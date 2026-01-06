"""
数据模型定义
所有数据类和枚举定义集中管理
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


@dataclass
class SpeechSegment:
    """语音片段"""
    start: float
    end: float
    text: str


class SplitReason(Enum):
    """切分原因"""
    SHOT_CHANGE_AND_SPEAKER_CHANGE = "镜头切换且说话人变化"


@dataclass
class SplitPoint:
    """切分点"""
    timestamp: float
    reason: SplitReason
    confidence: float


@dataclass
class AnalysisResult:
    """分析结果"""
    shot_changes: List[float]
    speech_segments: List[SpeechSegment]
    final_splits: List[SplitPoint]
    skipped_shots: List[Tuple[float, str]]


@dataclass
class SegmentInfo:
    """片段信息"""
    index: int
    start: float
    end: float
    duration: float

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "index": self.index,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.duration, 2)
        }
