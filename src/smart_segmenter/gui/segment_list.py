"""
片段列表组件
显示视频切分后的片段信息
"""

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models import SegmentInfo


class SegmentList(QWidget):
    """片段列表"""

    # 信号：选中片段
    segment_selected = Signal(float)  # 开始时间

    def __init__(self):
        super().__init__()
        self._segments: List[SegmentInfo] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 表格
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["#", "Time", "Duration"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)

        # 列宽配置
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(2, 70)

        # 隐藏垂直表头
        self._table.verticalHeader().setVisible(False)

        # 点击跳转
        self._table.cellClicked.connect(self._on_click)

        layout.addWidget(self._table, 1)

        # 底部信息栏
        self._info_label = QLabel("No segments")
        self._info_label.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self._info_label)

    def set_segments(self, segments: List[SegmentInfo]):
        """设置片段列表"""
        self._segments = segments
        self._table.setRowCount(len(segments))

        if not segments:
            self._info_label.setText("No segments")
            return

        # 计算统计信息
        total_duration = sum(seg.duration for seg in segments)
        self._info_label.setText(
            f"{len(segments)} segments | Total: {self._format_duration(total_duration)}"
        )

        for row, seg in enumerate(segments):
            # 序号
            index_item = QTableWidgetItem(str(seg.index))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, index_item)

            # 时间范围
            time_range = f"{self._format_time(seg.start)} - {self._format_time(seg.end)}"
            time_item = QTableWidgetItem(time_range)
            self._table.setItem(row, 1, time_item)

            # 时长
            duration_item = QTableWidgetItem(f"{seg.duration:.1f}s")
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, duration_item)

    def clear(self):
        """清空列表"""
        self._segments = []
        self._table.setRowCount(0)
        self._info_label.setText("No segments")

    def highlight_segment(self, index: int):
        """高亮指定片段"""
        if 0 <= index < len(self._segments):
            self._table.selectRow(index)
            self._table.scrollTo(self._table.model().index(index, 0))

    def _on_click(self, row: int, _col: int):
        """单击跳转到片段"""
        if 0 <= row < len(self._segments):
            self.segment_selected.emit(self._segments[row].start)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间 (M:SS)"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
