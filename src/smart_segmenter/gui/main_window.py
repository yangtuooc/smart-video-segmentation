"""
主窗口
整合所有组件，协调各模块交互

布局设计原则：
1. 视频预览为主焦点 - 占据最大空间
2. 时间轴紧邻预览 - 便于对照分析结果
3. 配置低频使用 - 可折叠，不占主要空间
4. 结果面板按需查看 - 右侧边栏
5. 操作按钮精简 - 顶部工具栏
"""

import json
from typing import List, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..models import SpeechSegment
from ..pipeline import PipelineConfig, PipelineResult
from .config_panel import ConfigPanel
from .segment_list import SegmentList
from .speech_panel import SpeechTextPanel
from .styles import get_primary_button_style
from .timeline_widget import TimelineWidget
from .video_player import VideoPlayer
from .worker import AnalyzeWorker, SplitWorker


class CollapsiblePanel(QWidget):
    """可折叠面板"""

    def __init__(self, title: str, widget: QWidget):
        super().__init__()
        self._widget = widget
        self._expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        self._header = QPushButton(f"- {title}")
        self._header.setFlat(True)
        self._header.setStyleSheet("text-align: left; padding: 4px 8px;")
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # 内容
        layout.addWidget(widget)
        self._title = title

    def _toggle(self):
        self._expanded = not self._expanded
        self._widget.setVisible(self._expanded)
        prefix = "-" if self._expanded else "+"
        self._header.setText(f"{prefix} {self._title}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._result: Optional[PipelineResult] = None
        self._worker: Optional[AnalyzeWorker] = None
        self._split_worker: Optional[SplitWorker] = None

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("Smart Video Segmenter")
        self.setMinimumSize(1280, 800)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(1)

        # 左侧主区域：视频 + 时间轴
        main_area = QWidget()
        main_layout_inner = QVBoxLayout(main_area)
        main_layout_inner.setContentsMargins(8, 8, 4, 8)
        main_layout_inner.setSpacing(8)

        # 视频播放器（主焦点）
        self._video_player = VideoPlayer()
        self._video_player.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout_inner.addWidget(self._video_player, 1)

        # 时间轴（紧邻视频）
        self._timeline = TimelineWidget()
        main_layout_inner.addWidget(self._timeline)

        content_splitter.addWidget(main_area)

        # 右侧边栏：完整工作流
        sidebar = self._create_sidebar()
        content_splitter.addWidget(sidebar)

        # 分割比例：视频区 70%, 侧边栏 30%
        content_splitter.setSizes([900, 380])
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)

        main_layout.addWidget(content_splitter, 1)

        # 底部状态栏
        statusbar = self._create_statusbar()
        main_layout.addWidget(statusbar)

    def _create_sidebar(self) -> QWidget:
        """创建右侧边栏 - 完整工作流"""
        sidebar = QWidget()
        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(420)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(4, 8, 8, 8)
        layout.setSpacing(12)

        # 1. 视频选择 + 参数配置
        self._config_panel = ConfigPanel()
        layout.addWidget(self._config_panel)

        # 分析按钮 - 主按钮样式
        self._analyze_btn = QPushButton("Analyze")
        self._analyze_btn.setMinimumHeight(36)
        self._analyze_btn.setToolTip("Run analysis (Ctrl+Enter)")
        self._analyze_btn.setStyleSheet(get_primary_button_style())
        self._analyze_btn.clicked.connect(self._trigger_analyze)
        self._analyze_btn.setEnabled(False)
        layout.addWidget(self._analyze_btn)

        # 进度区域
        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setVisible(False)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel()
        self._progress_label.setVisible(False)
        progress_layout.addWidget(self._progress_label)

        layout.addWidget(progress_widget)

        # 2. 结果面板
        # 片段列表
        self._segment_list = SegmentList()
        segments_section = CollapsiblePanel("Segments", self._segment_list)
        layout.addWidget(segments_section, 1)

        # 语音转录
        self._speech_panel = SpeechTextPanel()
        transcript_section = CollapsiblePanel("Transcript", self._speech_panel)
        layout.addWidget(transcript_section, 1)

        # 3. 导出操作
        export_widget = QWidget()
        export_layout = QHBoxLayout(export_widget)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.setSpacing(8)

        self._export_btn = QPushButton("Export JSON")
        self._export_btn.setToolTip("Export analysis results (Ctrl+E)")
        self._export_btn.clicked.connect(self._export_json)
        self._export_btn.setEnabled(False)
        export_layout.addWidget(self._export_btn)

        self._split_btn = QPushButton("Split Video")
        self._split_btn.setToolTip("Split into segments (Ctrl+Shift+S)")
        self._split_btn.clicked.connect(self._split_video)
        self._split_btn.setEnabled(False)
        export_layout.addWidget(self._split_btn)

        layout.addWidget(export_widget)

        return sidebar

    def _create_statusbar(self) -> QWidget:
        """创建底部状态栏"""
        statusbar = QWidget()
        layout = QHBoxLayout(statusbar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(16)

        self._status_label = QLabel("Ready")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 统计信息
        self._stats_label = QLabel()
        layout.addWidget(self._stats_label)

        return statusbar

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_video)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        export_action = QAction("Export JSON", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_json)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("Edit")

        analyze_action = QAction("Run Analysis", self)
        analyze_action.setShortcut(QKeySequence("Ctrl+Return"))
        analyze_action.triggered.connect(self._trigger_analyze)
        edit_menu.addAction(analyze_action)

        split_action = QAction("Split Video", self)
        split_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        split_action.triggered.connect(self._split_video)
        edit_menu.addAction(split_action)

        # 帮助菜单
        help_menu = menubar.addMenu("Help")

        shortcuts_action = QAction("Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """连接信号"""
        # 配置面板 -> 开始分析
        self._config_panel.analyze_requested.connect(self._start_analyze)
        # 配置面板 -> 视频加载
        self._config_panel.video_changed.connect(self._load_video)

        # 视频播放器 -> 时间轴 / 语音面板
        self._video_player.position_changed.connect(self._on_position_changed)
        self._video_player.duration_changed.connect(self._timeline.set_duration)

        # 时间轴 -> 视频播放器
        self._timeline.position_clicked.connect(self._video_player.seek)
        self._timeline.position_dragged.connect(self._video_player.seek)

        # 片段列表 -> 视频播放器
        self._segment_list.segment_selected.connect(self._video_player.seek)

    def _load_video(self, path: str):
        """加载视频到播放器"""
        self._video_player.load(path)
        self._analyze_btn.setEnabled(True)
        self._status_label.setText(f"Loaded: {path}")

    def _open_video(self):
        """打开视频文件"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv);;All Files (*)"
        )
        if path:
            self._config_panel._set_video_path(path)

    def _trigger_analyze(self):
        """触发分析（从菜单/工具栏）"""
        video_path = self._config_panel.get_video_path()
        if video_path:
            self._config_panel._start_analyze()

    @Slot(float)
    def _on_position_changed(self, position: float):
        """播放位置变化"""
        self._timeline.set_position(position)
        self._speech_panel.highlight_at_time(position)

    @Slot(str, PipelineConfig)
    def _start_analyze(self, video_path: str, config: PipelineConfig):
        """开始分析视频"""
        # 禁用控件
        self._set_controls_enabled(False)

        # 显示进度
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 4)
        self._progress_bar.setValue(0)
        self._progress_label.setVisible(True)
        self._stats_label.setText("")

        # 清空之前的结果
        self._timeline.clear()
        self._segment_list.clear()
        self._speech_panel.clear()
        self._result = None

        # 启动工作线程
        self._worker = AnalyzeWorker(video_path, config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_analyze_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self._status_label.setText("Analyzing...")

    def _set_controls_enabled(self, enabled: bool):
        """设置控件启用状态"""
        self._config_panel.set_enabled(enabled)
        self._analyze_btn.setEnabled(enabled and bool(self._config_panel.get_video_path()))
        self._export_btn.setEnabled(enabled and self._result is not None)
        has_splits = self._result and self._result.analysis_result.final_splits
        self._split_btn.setEnabled(enabled and bool(has_splits))

    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, message: str):
        """更新进度"""
        self._progress_bar.setValue(current)
        self._progress_label.setText(message)
        self._status_label.setText(f"Step {current}/{total}")

    @Slot(PipelineResult)
    def _on_analyze_finished(self, result: PipelineResult):
        """分析完成"""
        self._result = result
        self._worker = None

        # 更新时间轴
        self._timeline.set_duration(result.video_duration)
        self._timeline.set_shot_changes(result.shot_changes)
        self._timeline.set_speaker_changes(
            self._find_speaker_changes(result.speech_segments, result.speaker_labels)
        )
        self._timeline.set_split_points(result.analysis_result.final_splits)

        # 更新片段列表
        self._segment_list.set_segments(result.segments_info)

        # 更新语音文本
        self._speech_panel.set_data(result.speech_segments, result.speaker_labels)

        # 恢复控件状态
        self._set_controls_enabled(True)
        self._progress_bar.setVisible(False)
        self._progress_label.setVisible(False)

        # 统计信息
        shots = len(result.shot_changes)
        splits = len(result.analysis_result.final_splits)
        segments = len(result.segments_info)
        speakers = len(set(result.speaker_labels)) if result.speaker_labels else 0

        self._status_label.setText("Analysis complete")
        self._stats_label.setText(
            f"{segments} segments | {shots} shots | {speakers} speakers"
        )

    @Slot(str)
    def _on_error(self, message: str):
        """处理错误"""
        self._worker = None
        self._set_controls_enabled(True)
        self._progress_bar.setVisible(False)
        self._progress_label.setVisible(False)
        self._status_label.setText("Analysis failed")

        QMessageBox.critical(self, "Error", f"Analysis failed:\n{message}")

    def _export_json(self):
        """导出 JSON"""
        if not self._result:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "analysis.json", "JSON Files (*.json)"
        )
        if not path:
            return

        export_data = {
            "video": self._result.video_path,
            "duration": self._result.video_duration,
            "shot_changes": self._result.shot_changes,
            "speech_segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in self._result.speech_segments
            ],
            "speaker_labels": self._result.speaker_labels,
            "final_splits": [
                {
                    "timestamp": s.timestamp,
                    "reason": s.reason.value,
                    "confidence": s.confidence,
                }
                for s in self._result.analysis_result.final_splits
            ],
            "segments": [seg.to_dict() for seg in self._result.segments_info],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self._status_label.setText(f"Exported: {path}")

    def _split_video(self):
        """分割视频"""
        if not self._result or not self._result.analysis_result.final_splits:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return

        self._set_controls_enabled(False)
        self._status_label.setText("Splitting video...")

        self._split_worker = SplitWorker(self._result, output_dir)
        self._split_worker.finished.connect(self._on_split_finished)
        self._split_worker.error.connect(self._on_split_error)
        self._split_worker.start()

    @Slot(list)
    def _on_split_finished(self, output_files: List[str]):
        """分割完成"""
        self._split_worker = None
        self._set_controls_enabled(True)

        self._status_label.setText(f"Split complete - {len(output_files)} files created")
        QMessageBox.information(
            self, "Complete", f"Video split complete!\n\nCreated {len(output_files)} segments"
        )

    @Slot(str)
    def _on_split_error(self, message: str):
        """分割错误"""
        self._split_worker = None
        self._set_controls_enabled(True)
        self._status_label.setText("Split failed")

        QMessageBox.critical(self, "Error", f"Split failed:\n{message}")

    def _show_shortcuts(self):
        """显示快捷键帮助"""
        shortcuts = """
<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>Ctrl+O</b></td><td>Open video</td></tr>
<tr><td><b>Ctrl+Enter</b></td><td>Run analysis</td></tr>
<tr><td><b>Ctrl+E</b></td><td>Export JSON</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Split video</td></tr>
<tr><td colspan="2"><hr></td></tr>
<tr><td><b>Space</b></td><td>Play / Pause</td></tr>
<tr><td><b>Left / Right</b></td><td>Seek -5s / +5s</td></tr>
<tr><td><b>Up / Down</b></td><td>Volume +/- </td></tr>
<tr><td><b>M</b></td><td>Mute / Unmute</td></tr>
</table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "About",
            "<h3>Smart Video Segmenter</h3>"
            "<p>Intelligent video segmentation using shot detection and speaker diarization.</p>"
            "<p>Tech: TransNetV2, Whisper, Resemblyzer</p>"
        )

    @staticmethod
    def _find_speaker_changes(
        speech_segments: List[SpeechSegment], speaker_labels: List[int]
    ) -> List[float]:
        """根据说话人标签找出变化点时间"""
        if not speaker_labels or len(speaker_labels) < 2:
            return []

        change_times = []
        for i in range(1, len(speaker_labels)):
            if speaker_labels[i] != speaker_labels[i - 1]:
                change_times.append(speech_segments[i - 1].end)
        return change_times
