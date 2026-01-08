"""
时间轴组件
可视化显示镜头切换、说话人变化和切分点
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QToolTip, QWidget

from ..models import SplitPoint


@dataclass
class TrackConfig:
    """轨道配置"""
    name: str
    color: QColor
    times: List[float]


class TimelineWidget(QWidget):
    """时间轴组件"""

    # 信号
    position_clicked = Signal(float)  # 点击时间位置（秒）
    position_dragged = Signal(float)  # 拖拽时间位置（秒）

    # 颜色定义
    COLOR_SHOT = QColor(66, 133, 244)      # 蓝色 - 镜头切换
    COLOR_SPEAKER = QColor(52, 168, 83)    # 绿色 - 说话人变化
    COLOR_SPLIT = QColor(234, 67, 53)      # 红色 - 切分点
    COLOR_POSITION = QColor(255, 152, 0)   # 橙色 - 当前位置
    COLOR_BG = QColor(38, 38, 38)          # 背景色
    COLOR_TRACK = QColor(60, 60, 60)       # 轨道色
    COLOR_TICK = QColor(100, 100, 100)     # 刻度色
    COLOR_TEXT = QColor(200, 200, 200)     # 文本色

    # 布局常量
    MARGIN_LEFT = 60   # 左边距（用于标签）
    MARGIN_RIGHT = 10  # 右边距
    MARGIN_TOP = 25    # 顶部边距（用于时间刻度）
    MARGIN_BOTTOM = 25 # 底部边距（用于图例）
    TRACK_HEIGHT = 14  # 轨道高度
    TRACK_GAP = 6      # 轨道间距
    MARKER_WIDTH = 3   # 标记宽度

    def __init__(self):
        super().__init__()
        self._duration = 0.0
        self._position = 0.0
        self._shot_changes: List[float] = []
        self._speaker_changes: List[float] = []
        self._split_points: List[SplitPoint] = []
        self._is_dragging = False
        self._hover_time: Optional[float] = None

        self.setMinimumHeight(100)
        self.setMaximumHeight(120)
        self.setMouseTracking(True)  # 启用鼠标追踪

    def set_duration(self, duration: float):
        """设置视频总时长"""
        self._duration = duration
        self.update()

    def set_position(self, position: float):
        """设置当前播放位置"""
        self._position = position
        self.update()

    def set_shot_changes(self, times: List[float]):
        """设置镜头切换点"""
        self._shot_changes = times
        self.update()

    def set_speaker_changes(self, times: List[float]):
        """设置说话人变化点"""
        self._speaker_changes = times
        self.update()

    def set_split_points(self, splits: List[SplitPoint]):
        """设置切分点"""
        self._split_points = splits
        self.update()

    def clear(self):
        """清空所有数据"""
        self._duration = 0.0
        self._position = 0.0
        self._shot_changes = []
        self._speaker_changes = []
        self._split_points = []
        self.update()

    def paintEvent(self, event):
        """绘制时间轴"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), self.COLOR_BG)

        if self._duration <= 0:
            painter.setPen(self.COLOR_TEXT)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a video to show timeline")
            return

        track_rect = self._get_track_rect()

        # 绘制时间刻度
        self._draw_time_ticks(painter, track_rect)

        # 绘制轨道
        tracks = [
            TrackConfig("Shots", self.COLOR_SHOT, self._shot_changes),
            TrackConfig("Speaker", self.COLOR_SPEAKER, self._speaker_changes),
            TrackConfig("Splits", self.COLOR_SPLIT, [s.timestamp for s in self._split_points]),
        ]
        self._draw_tracks(painter, track_rect, tracks)

        # 绘制当前位置指示器
        self._draw_position_indicator(painter, track_rect)

        # 绘制底部图例和时间信息
        self._draw_footer(painter, tracks)

    def _get_track_rect(self) -> QRectF:
        """获取轨道绘制区域"""
        return QRectF(
            self.MARGIN_LEFT,
            self.MARGIN_TOP,
            self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.height() - self.MARGIN_TOP - self.MARGIN_BOTTOM
        )

    def _time_to_x(self, time: float, track_rect: QRectF) -> float:
        """时间转换为 X 坐标"""
        if self._duration <= 0:
            return track_rect.left()
        return track_rect.left() + (time / self._duration) * track_rect.width()

    def _x_to_time(self, x: float, track_rect: QRectF) -> float:
        """X 坐标转换为时间"""
        if track_rect.width() <= 0:
            return 0.0
        ratio = (x - track_rect.left()) / track_rect.width()
        return max(0.0, min(self._duration, ratio * self._duration))

    def _draw_time_ticks(self, painter: QPainter, track_rect: QRectF):
        """绘制时间刻度"""
        painter.setPen(QPen(self.COLOR_TICK, 1))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # 计算合适的刻度间隔
        tick_interval = self._calculate_tick_interval()
        if tick_interval <= 0:
            return

        time = 0.0
        while time <= self._duration:
            x = self._time_to_x(time, track_rect)

            # 刻度线
            painter.drawLine(QPointF(x, track_rect.top() - 5), QPointF(x, track_rect.top()))

            # 时间标签
            label = self._format_time(time)
            label_width = fm.horizontalAdvance(label)
            painter.setPen(self.COLOR_TEXT)
            painter.drawText(QPointF(x - label_width / 2, track_rect.top() - 8), label)
            painter.setPen(QPen(self.COLOR_TICK, 1))

            time += tick_interval

    def _calculate_tick_interval(self) -> float:
        """计算合适的刻度间隔"""
        if self._duration <= 0:
            return 0.0

        # 目标：大约 5-8 个刻度
        target_ticks = 6
        raw_interval = self._duration / target_ticks

        # 选择合适的间隔（1, 2, 5, 10, 15, 30, 60, 120...）
        nice_intervals = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600]
        for interval in nice_intervals:
            if interval >= raw_interval:
                return float(interval)
        return raw_interval

    def _draw_tracks(self, painter: QPainter, track_rect: QRectF, tracks: List[TrackConfig]):
        """绘制轨道"""
        track_count = len(tracks)
        total_track_height = track_count * self.TRACK_HEIGHT + (track_count - 1) * self.TRACK_GAP
        start_y = track_rect.top() + (track_rect.height() - total_track_height) / 2

        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        for i, track in enumerate(tracks):
            y = start_y + i * (self.TRACK_HEIGHT + self.TRACK_GAP)

            # 轨道标签
            painter.setPen(self.COLOR_TEXT)
            painter.drawText(
                QRectF(5, y, self.MARGIN_LEFT - 10, self.TRACK_HEIGHT),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                track.name
            )

            # 轨道背景
            track_bg_rect = QRectF(track_rect.left(), y, track_rect.width(), self.TRACK_HEIGHT)
            painter.fillRect(track_bg_rect, self.COLOR_TRACK)

            # 标记点
            for time in track.times:
                x = self._time_to_x(time, track_rect)
                marker_rect = QRectF(
                    x - self.MARKER_WIDTH / 2, y,
                    self.MARKER_WIDTH, self.TRACK_HEIGHT
                )
                painter.fillRect(marker_rect, track.color)

    def _draw_position_indicator(self, painter: QPainter, track_rect: QRectF):
        """绘制当前位置指示器"""
        x = self._time_to_x(self._position, track_rect)

        # 指示线
        painter.setPen(QPen(self.COLOR_POSITION, 2))
        painter.drawLine(
            QPointF(x, track_rect.top() - 3),
            QPointF(x, track_rect.bottom() + 3)
        )

        # 顶部三角形
        triangle = QPainterPath()
        triangle.moveTo(x, track_rect.top() - 3)
        triangle.lineTo(x - 5, track_rect.top() - 10)
        triangle.lineTo(x + 5, track_rect.top() - 10)
        triangle.closeSubpath()
        painter.fillPath(triangle, QBrush(self.COLOR_POSITION))

    def _draw_footer(self, painter: QPainter, tracks: List[TrackConfig]):
        """绘制底部图例和时间信息"""
        y = self.height() - self.MARGIN_BOTTOM + 8
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # 当前时间 / 总时长
        time_text = f"{self._format_time(self._position)} / {self._format_time(self._duration)}"
        painter.setPen(self.COLOR_TEXT)
        painter.drawText(QPointF(self.MARGIN_LEFT, y + 4), time_text)

        # 图例（右对齐）
        x = self.width() - self.MARGIN_RIGHT
        for track in reversed(tracks):
            label = f" {track.name}"
            label_width = fm.horizontalAdvance(label)
            x -= label_width
            painter.setPen(self.COLOR_TEXT)
            painter.drawText(QPointF(x, y + 4), label)

            # 颜色块
            x -= 12
            painter.fillRect(QRectF(x, y - 4, 10, 10), track.color)
            x -= 15

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton and self._duration > 0:
            track_rect = self._get_track_rect()
            if track_rect.left() <= event.position().x() <= track_rect.right():
                self._is_dragging = True
                time = self._x_to_time(event.position().x(), track_rect)
                self.position_clicked.emit(time)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        if self._duration <= 0:
            return

        track_rect = self._get_track_rect()

        # 拖拽更新位置
        if self._is_dragging:
            time = self._x_to_time(event.position().x(), track_rect)
            self.position_dragged.emit(time)
            return

        # 悬停提示
        if track_rect.contains(event.position()):
            time = self._x_to_time(event.position().x(), track_rect)
            self._hover_time = time

            # 查找附近的标记点
            tooltip_lines = [f"Time: {self._format_time(time)}"]
            tolerance = self._duration * 0.01  # 1% 容差

            for t in self._shot_changes:
                if abs(t - time) < tolerance:
                    tooltip_lines.append(f"Shot change: {self._format_time(t)}")
                    break

            for t in self._speaker_changes:
                if abs(t - time) < tolerance:
                    tooltip_lines.append(f"Speaker change: {self._format_time(t)}")
                    break

            for sp in self._split_points:
                if abs(sp.timestamp - time) < tolerance:
                    tooltip_lines.append(f"Split point: {self._format_time(sp.timestamp)}")
                    tooltip_lines.append(f"  Reason: {sp.reason.value}")
                    break

            QToolTip.showText(event.globalPosition().toPoint(), "\n".join(tooltip_lines), self)
        else:
            self._hover_time = None
            QToolTip.hideText()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hover_time = None
        QToolTip.hideText()

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间 (M:SS.s)"""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:05.2f}"
