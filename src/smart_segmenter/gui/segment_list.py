"""
片段列表组件
显示视频切分后的片段信息，支持缩略图、置信度、类型标签
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..models import SegmentInfo


class SegmentItemWidget(QWidget):
    """片段列表项组件"""

    def __init__(self, segment: SegmentInfo, index: int):
        super().__init__()
        self._segment = segment
        self._index = index
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # 选择框
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(True)
        layout.addWidget(self._checkbox)

        # 序号
        index_label = QLabel(f"{self._index}")
        index_label.setFixedWidth(24)
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setStyleSheet("color: #6F737A; font-weight: bold;")
        layout.addWidget(index_label)

        # 时间信息
        time_layout = QVBoxLayout()
        time_layout.setSpacing(2)

        time_range = QLabel(f"{self._format_time(self._segment.start)} - {self._format_time(self._segment.end)}")
        time_range.setStyleSheet("color: #DFE1E5; font-size: 13px;")
        time_layout.addWidget(time_range)

        duration = QLabel(f"时长: {self._segment.duration:.1f}秒")
        duration.setStyleSheet("color: #6F737A; font-size: 11px;")
        time_layout.addWidget(duration)

        layout.addLayout(time_layout)
        layout.addStretch()

        # 置信度（如果有）
        if hasattr(self._segment, 'confidence') and self._segment.confidence:
            confidence = int(self._segment.confidence * 100)
            conf_widget = QWidget()
            conf_layout = QVBoxLayout(conf_widget)
            conf_layout.setContentsMargins(0, 0, 0, 0)
            conf_layout.setSpacing(2)

            conf_label = QLabel(f"{confidence}%")
            conf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            conf_label.setStyleSheet("color: #DFE1E5; font-size: 11px;")
            conf_layout.addWidget(conf_label)

            # 置信度条
            conf_bar = QProgressBar()
            conf_bar.setRange(0, 100)
            conf_bar.setValue(confidence)
            conf_bar.setTextVisible(False)
            conf_bar.setFixedSize(50, 4)
            conf_bar.setStyleSheet(self._get_confidence_style(confidence))
            conf_layout.addWidget(conf_bar)

            layout.addWidget(conf_widget)

        # 类型标签（如果有）
        if hasattr(self._segment, 'reason') and self._segment.reason:
            reason_label = QLabel(self._get_reason_text(self._segment.reason))
            reason_label.setStyleSheet(self._get_reason_style(self._segment.reason))
            reason_label.setFixedHeight(20)
            layout.addWidget(reason_label)

    def _get_confidence_style(self, confidence: int) -> str:
        """根据置信度返回样式"""
        if confidence >= 80:
            color = "#5FAD65"  # 绿色
        elif confidence >= 60:
            color = "#F2C55C"  # 黄色
        else:
            color = "#DB5C5C"  # 红色
        return f"""
            QProgressBar {{
                background-color: #393B40;
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """

    def _get_reason_text(self, reason) -> str:
        """获取原因文本"""
        reason_map = {
            "shot_change": "镜头",
            "speaker_change": "说话人",
            "silence": "静音",
            "both": "镜头+说话人",
        }
        reason_str = reason.value if hasattr(reason, 'value') else str(reason)
        return reason_map.get(reason_str, reason_str)

    def _get_reason_style(self, reason) -> str:
        """获取原因标签样式"""
        reason_str = reason.value if hasattr(reason, 'value') else str(reason)
        color_map = {
            "shot_change": "#548AF7",  # 蓝色
            "speaker_change": "#5FAD65",  # 绿色
            "silence": "#F2C55C",  # 黄色
            "both": "#955AE0",  # 紫色
        }
        color = color_map.get(reason_str, "#6F737A")
        return f"""
            background-color: {color}30;
            color: {color};
            border: 1px solid {color}50;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
        """

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def is_selected(self) -> bool:
        """是否选中"""
        return self._checkbox.isChecked()

    def set_selected(self, selected: bool):
        """设置选中状态"""
        self._checkbox.setChecked(selected)


class SegmentList(QWidget):
    """片段列表"""

    # 信号
    segment_selected = Signal(float)  # 开始时间
    selection_changed = Signal(list)  # 选中的片段索引列表

    def __init__(self):
        super().__init__()
        self._segments: List[SegmentInfo] = []
        self._item_widgets: List[SegmentItemWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(8)

        self._select_all_btn = QPushButton("全选")
        self._select_all_btn.setFlat(True)
        self._select_all_btn.clicked.connect(self._select_all)
        toolbar_layout.addWidget(self._select_all_btn)

        self._select_none_btn = QPushButton("取消")
        self._select_none_btn.setFlat(True)
        self._select_none_btn.clicked.connect(self._select_none)
        toolbar_layout.addWidget(self._select_none_btn)

        toolbar_layout.addStretch()

        self._count_label = QLabel()
        self._count_label.setStyleSheet("color: #6F737A;")
        toolbar_layout.addWidget(self._count_label)

        layout.addWidget(toolbar)

        # 列表
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setSpacing(2)
        self._list.setStyleSheet("""
            QListWidget {
                background-color: #1E1F22;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #2B2D30;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #2E436E;
            }
            QListWidget::item:hover {
                background-color: #393B40;
            }
        """)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list, 1)

        # 底部信息栏
        self._info_label = QLabel("无片段")
        self._info_label.setContentsMargins(8, 4, 8, 4)
        self._info_label.setStyleSheet("color: #6F737A;")
        layout.addWidget(self._info_label)

    def set_segments(self, segments: List[SegmentInfo]):
        """设置片段列表"""
        self._segments = segments
        self._item_widgets.clear()
        self._list.clear()

        if not segments:
            self._info_label.setText("无片段")
            self._count_label.setText("")
            return

        # 计算统计信息
        total_duration = sum(seg.duration for seg in segments)
        self._info_label.setText(f"总时长: {self._format_duration(total_duration)}")
        self._count_label.setText(f"{len(segments)} 个片段")

        for i, seg in enumerate(segments):
            item = QListWidgetItem(self._list)
            widget = SegmentItemWidget(seg, i + 1)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)
            self._item_widgets.append(widget)

    def clear(self):
        """清空列表"""
        self._segments = []
        self._item_widgets.clear()
        self._list.clear()
        self._info_label.setText("无片段")
        self._count_label.setText("")

    def get_selected_indices(self) -> List[int]:
        """获取选中的片段索引"""
        return [i for i, w in enumerate(self._item_widgets) if w.is_selected()]

    def highlight_segment(self, index: int):
        """高亮指定片段"""
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)
            self._list.scrollToItem(self._list.item(index))

    def _select_all(self):
        """全选"""
        for widget in self._item_widgets:
            widget.set_selected(True)
        self.selection_changed.emit(self.get_selected_indices())

    def _select_none(self):
        """取消全选"""
        for widget in self._item_widgets:
            widget.set_selected(False)
        self.selection_changed.emit(self.get_selected_indices())

    def _on_item_clicked(self, item: QListWidgetItem):
        """单击项"""
        row = self._list.row(item)
        if 0 <= row < len(self._segments):
            self.segment_selected.emit(self._segments[row].start)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """双击项 - 跳转到片段"""
        row = self._list.row(item)
        if 0 <= row < len(self._segments):
            self.segment_selected.emit(self._segments[row].start)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
