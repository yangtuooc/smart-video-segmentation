"""
语音文本面板组件
显示语音识别文本和说话人标签
"""

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import SpeechSegment


# 说话人颜色
SPEAKER_COLORS = [
    QColor(66, 133, 244),   # 蓝色
    QColor(52, 168, 83),    # 绿色
    QColor(251, 188, 4),    # 黄色
    QColor(234, 67, 53),    # 红色
    QColor(171, 71, 188),   # 紫色
    QColor(0, 172, 193),    # 青色
    QColor(255, 112, 67),   # 橙色
    QColor(124, 179, 66),   # 草绿
]


class SpeechTextPanel(QWidget):
    """语音文本面板"""

    # 信号：点击片段
    segment_clicked = Signal(float)  # 开始时间

    def __init__(self):
        super().__init__()
        self._segments: List[SpeechSegment] = []
        self._labels: List[int] = []
        self._current_index = -1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 文本显示区域
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("", 11))
        layout.addWidget(self._text_edit, 1)

        # 底部信息栏
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)
        footer_layout.setSpacing(12)

        # 说话人图例
        self._legend_labels: List[QLabel] = []
        for i in range(4):
            color_label = QLabel(f"[{i}]")
            color_label.setStyleSheet(f"color: {SPEAKER_COLORS[i % len(SPEAKER_COLORS)].name()};")
            color_label.setVisible(False)
            footer_layout.addWidget(color_label)
            self._legend_labels.append(color_label)

        footer_layout.addStretch()

        self._info_label = QLabel()
        footer_layout.addWidget(self._info_label)

        layout.addWidget(footer)

    def set_data(self, segments: List[SpeechSegment], labels: List[int]):
        """设置语音片段和说话人标签"""
        self._segments = segments
        self._labels = labels
        self._current_index = -1
        self._update_display()

    def clear(self):
        """清空数据"""
        self._segments = []
        self._labels = []
        self._current_index = -1
        self._text_edit.clear()
        self._info_label.setText("")
        for label in self._legend_labels:
            label.setVisible(False)

    def highlight_at_time(self, time: float):
        """高亮当前时间对应的片段"""
        if not self._segments:
            return

        # 查找当前片段
        new_index = -1
        for i, seg in enumerate(self._segments):
            if seg.start <= time <= seg.end:
                new_index = i
                break

        if new_index != self._current_index:
            self._current_index = new_index
            self._highlight_segment(new_index)

    def _update_display(self):
        """更新文本显示"""
        self._text_edit.clear()

        if not self._segments:
            self._info_label.setText("")
            return

        # 统计说话人数量
        unique_speakers = set(self._labels) if self._labels else {0}
        num_speakers = len(unique_speakers)
        self._info_label.setText(f"{len(self._segments)} segments, {num_speakers} speakers")

        # 更新图例
        for i, label in enumerate(self._legend_labels):
            if i < num_speakers:
                label.setVisible(True)
                color = SPEAKER_COLORS[i % len(SPEAKER_COLORS)]
                label.setStyleSheet(f"color: {color.name()};")
            else:
                label.setVisible(False)

        # 构建富文本
        cursor = self._text_edit.textCursor()
        for i, seg in enumerate(self._segments):
            # 说话人标签颜色
            speaker = self._labels[i] if i < len(self._labels) else 0
            color = SPEAKER_COLORS[speaker % len(SPEAKER_COLORS)]

            # 时间标签格式
            time_format = QTextCharFormat()
            time_format.setForeground(QColor(136, 136, 136))

            # 说话人标签格式
            speaker_format = QTextCharFormat()
            speaker_format.setForeground(color)
            speaker_format.setFontWeight(QFont.Weight.Bold)

            # 文本格式
            text_format = QTextCharFormat()

            # 插入内容
            cursor.insertText(f"[{self._format_time(seg.start)}] ", time_format)
            cursor.insertText(f"[{speaker}] ", speaker_format)
            cursor.insertText(f"{seg.text}\n\n", text_format)

    def _highlight_segment(self, index: int):
        """高亮指定片段"""
        if index < 0 or index >= len(self._segments):
            return

        # 滚动到指定位置
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        # 移动到指定行
        for _ in range(index * 2):
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:05.2f}"
