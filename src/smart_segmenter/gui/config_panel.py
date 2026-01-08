"""
配置面板组件
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..pipeline import PipelineConfig


class ConfigPanel(QWidget):
    """配置面板"""

    # 信号：请求开始分析
    analyze_requested = Signal(str, PipelineConfig)  # (video_path, config)
    # 信号：视频路径改变
    video_changed = Signal(str)  # video_path

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 视频选择
        video_group = QGroupBox("Video")
        video_layout = QVBoxLayout(video_group)
        video_layout.setContentsMargins(12, 12, 12, 12)
        video_layout.setSpacing(8)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self._video_path = QLineEdit()
        self._video_path.setPlaceholderText("No file selected")
        self._video_path.setReadOnly(True)
        path_row.addWidget(self._video_path)

        self._browse_btn = QPushButton("...")
        self._browse_btn.setFixedWidth(32)
        self._browse_btn.setToolTip("Browse files")
        self._browse_btn.clicked.connect(self._browse_video)
        path_row.addWidget(self._browse_btn)

        video_layout.addLayout(path_row)
        layout.addWidget(video_group)

        # 参数配置
        config_group = QGroupBox("Settings")
        config_layout = QFormLayout(config_group)
        config_layout.setContentsMargins(12, 12, 12, 12)
        config_layout.setSpacing(8)
        config_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Whisper 模型
        self._model_combo = QComboBox()
        self._model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self._model_combo.setCurrentText("base")
        config_layout.addRow("Model", self._model_combo)

        # 语言
        self._language = QLineEdit("zh")
        self._language.setMaximumWidth(60)
        config_layout.addRow("Language", self._language)

        # 镜头阈值
        self._threshold = QDoubleSpinBox()
        self._threshold.setRange(0.1, 1.0)
        self._threshold.setSingleStep(0.1)
        self._threshold.setValue(0.5)
        config_layout.addRow("Threshold", self._threshold)

        # 最小片段时长
        self._min_segment = QDoubleSpinBox()
        self._min_segment.setRange(0.5, 30.0)
        self._min_segment.setSingleStep(0.5)
        self._min_segment.setValue(2.0)
        self._min_segment.setSuffix(" s")
        config_layout.addRow("Min Duration", self._min_segment)

        layout.addWidget(config_group)
        layout.addStretch()

        # 启用拖拽
        self.setAcceptDrops(True)

    def _browse_video(self):
        """选择视频文件"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv);;All Files (*)"
        )
        if path:
            self._set_video_path(path)

    def _set_video_path(self, path: str):
        """设置视频路径"""
        self._video_path.setText(path)
        if Path(path).exists():
            self.video_changed.emit(path)

    def _start_analyze(self):
        """开始分析"""
        video_path = self._video_path.text()
        if not video_path:
            return

        config = PipelineConfig(
            whisper_model=self._model_combo.currentText(),
            language=self._language.text(),
            shot_threshold=self._threshold.value(),
            min_segment_duration=self._min_segment.value(),
        )
        self.analyze_requested.emit(video_path, config)

    def set_enabled(self, enabled: bool):
        """设置控件启用状态"""
        self._browse_btn.setEnabled(enabled)
        self._model_combo.setEnabled(enabled)
        self._language.setEnabled(enabled)
        self._threshold.setEnabled(enabled)
        self._min_segment.setEnabled(enabled)

    def get_video_path(self) -> str:
        """获取当前视频路径"""
        return self._video_path.text()

    # 拖拽支持
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).suffix.lower() in {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"}:
                self._set_video_path(path)
