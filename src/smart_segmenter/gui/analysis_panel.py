"""
AI 分析结果面板
展示智能分割的分析统计信息
"""

from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ..models import SplitPoint, SplitReason


class StatBar(QWidget):
    """统计条组件"""

    def __init__(self, label: str, color: str):
        super().__init__()
        self._label = label
        self._color = color
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # 颜色指示器
        indicator = QFrame()
        indicator.setFixedSize(12, 12)
        indicator.setStyleSheet(f"background-color: {self._color}; border-radius: 2px;")
        layout.addWidget(indicator)

        # 标签
        self._name_label = QLabel(self._label)
        self._name_label.setFixedWidth(80)
        self._name_label.setStyleSheet("color: #DFE1E5;")
        layout.addWidget(self._name_label)

        # 进度条
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #393B40;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self._bar, 1)

        # 数值
        self._value_label = QLabel("0")
        self._value_label.setFixedWidth(40)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._value_label.setStyleSheet("color: #6F737A;")
        layout.addWidget(self._value_label)

        # 百分比
        self._percent_label = QLabel("0%")
        self._percent_label.setFixedWidth(40)
        self._percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._percent_label.setStyleSheet("color: #6F737A;")
        layout.addWidget(self._percent_label)

    def set_value(self, count: int, total: int):
        """设置值"""
        percent = int(count / total * 100) if total > 0 else 0
        self._bar.setValue(percent)
        self._value_label.setText(str(count))
        self._percent_label.setText(f"{percent}%")


class AnalysisPanel(QWidget):
    """AI 分析结果面板"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 标题
        title = QLabel("🤖 AI 分析结果")
        title.setStyleSheet("color: #DFE1E5; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        # 分割点统计
        split_section = QWidget()
        split_layout = QVBoxLayout(split_section)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(4)

        self._total_label = QLabel("检测到 0 个分割点")
        self._total_label.setStyleSheet("color: #6F737A; font-size: 12px;")
        split_layout.addWidget(self._total_label)

        # 分割依据分布
        reason_title = QLabel("分割依据")
        reason_title.setStyleSheet("color: #9DA0A8; font-size: 11px; margin-top: 8px;")
        split_layout.addWidget(reason_title)

        self._shot_bar = StatBar("镜头切换", "#548AF7")
        split_layout.addWidget(self._shot_bar)

        self._speaker_bar = StatBar("说话人切换", "#5FAD65")
        split_layout.addWidget(self._speaker_bar)

        self._both_bar = StatBar("镜头+说话人", "#955AE0")
        split_layout.addWidget(self._both_bar)

        self._silence_bar = StatBar("静音/停顿", "#F2C55C")
        split_layout.addWidget(self._silence_bar)

        layout.addWidget(split_section)

        # 置信度分布
        conf_section = QWidget()
        conf_layout = QVBoxLayout(conf_section)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        conf_layout.setSpacing(4)

        conf_title = QLabel("置信度分布")
        conf_title.setStyleSheet("color: #9DA0A8; font-size: 11px; margin-top: 8px;")
        conf_layout.addWidget(conf_title)

        self._high_conf_bar = StatBar("高 (≥80%)", "#5FAD65")
        conf_layout.addWidget(self._high_conf_bar)

        self._mid_conf_bar = StatBar("中 (60-80%)", "#F2C55C")
        conf_layout.addWidget(self._mid_conf_bar)

        self._low_conf_bar = StatBar("低 (<60%)", "#DB5C5C")
        conf_layout.addWidget(self._low_conf_bar)

        layout.addWidget(conf_section)

        # 视频信息
        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        info_title = QLabel("视频信息")
        info_title.setStyleSheet("color: #9DA0A8; font-size: 11px; margin-top: 8px;")
        info_layout.addWidget(info_title)

        self._duration_label = QLabel("时长: --")
        self._duration_label.setStyleSheet("color: #6F737A; font-size: 12px;")
        info_layout.addWidget(self._duration_label)

        self._segments_label = QLabel("片段数: --")
        self._segments_label.setStyleSheet("color: #6F737A; font-size: 12px;")
        info_layout.addWidget(self._segments_label)

        self._avg_duration_label = QLabel("平均时长: --")
        self._avg_duration_label.setStyleSheet("color: #6F737A; font-size: 12px;")
        info_layout.addWidget(self._avg_duration_label)

        layout.addWidget(info_section)
        layout.addStretch()

    def update_stats(
        self,
        split_points: List[SplitPoint],
        video_duration: float,
        num_segments: int
    ):
        """更新统计信息"""
        total = len(split_points)
        self._total_label.setText(f"检测到 {total} 个分割点")

        # 统计分割依据
        reason_counts: Dict[str, int] = {
            "shot_change": 0,
            "speaker_change": 0,
            "both": 0,
            "silence": 0,
        }
        conf_counts = {"high": 0, "mid": 0, "low": 0}

        for sp in split_points:
            reason_str = sp.reason.value if hasattr(sp.reason, 'value') else str(sp.reason)
            if reason_str in reason_counts:
                reason_counts[reason_str] += 1

            # 置信度分布
            if sp.confidence >= 0.8:
                conf_counts["high"] += 1
            elif sp.confidence >= 0.6:
                conf_counts["mid"] += 1
            else:
                conf_counts["low"] += 1

        # 更新分割依据条
        self._shot_bar.set_value(reason_counts["shot_change"], total)
        self._speaker_bar.set_value(reason_counts["speaker_change"], total)
        self._both_bar.set_value(reason_counts["both"], total)
        self._silence_bar.set_value(reason_counts["silence"], total)

        # 更新置信度条
        self._high_conf_bar.set_value(conf_counts["high"], total)
        self._mid_conf_bar.set_value(conf_counts["mid"], total)
        self._low_conf_bar.set_value(conf_counts["low"], total)

        # 更新视频信息
        self._duration_label.setText(f"时长: {self._format_duration(video_duration)}")
        self._segments_label.setText(f"片段数: {num_segments}")
        if num_segments > 0:
            avg = video_duration / num_segments
            self._avg_duration_label.setText(f"平均时长: {avg:.1f}秒")
        else:
            self._avg_duration_label.setText("平均时长: --")

    def clear(self):
        """清空统计"""
        self._total_label.setText("检测到 0 个分割点")
        self._shot_bar.set_value(0, 1)
        self._speaker_bar.set_value(0, 1)
        self._both_bar.set_value(0, 1)
        self._silence_bar.set_value(0, 1)
        self._high_conf_bar.set_value(0, 1)
        self._mid_conf_bar.set_value(0, 1)
        self._low_conf_bar.set_value(0, 1)
        self._duration_label.setText("时长: --")
        self._segments_label.setText("片段数: --")
        self._avg_duration_label.setText("平均时长: --")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes < 60:
            return f"{minutes}分{secs}秒"
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}时{minutes}分{secs}秒"
