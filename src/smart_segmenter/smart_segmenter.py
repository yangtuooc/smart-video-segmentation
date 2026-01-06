"""
智能融合决策模块
结合镜头检测和说话人标签，智能决定最终的切分点
"""

from typing import List, Tuple

from .models import (
    AnalysisResult,
    SegmentInfo,
    SpeechSegment,
    SplitPoint,
    SplitReason,
)

# 常量定义
SHOT_SPEAKER_TIME_TOLERANCE = 1.0  # 镜头切换与说话人变化的时间容差（秒）
SHOT_SPEAKER_CONFIDENCE = 0.9  # 镜头切换+说话人变化的置信度


class SmartSegmenter:
    """智能分割器"""

    def __init__(self, min_segment_duration: float = 2.0):
        """
        初始化智能分割器

        Args:
            min_segment_duration: 最小片段时长（秒），避免切出太短的片段
        """
        self._min_segment_duration = min_segment_duration

    def analyze(
            self,
            shot_changes: List[float],
            speech_segments: List[SpeechSegment],
            video_duration: float,
            speaker_labels: List[int] = None
    ) -> AnalysisResult:
        """
        分析并决定最终切分点

        Args:
            shot_changes: 镜头切换点时间戳列表
            speech_segments: 语音片段列表
            video_duration: 视频总时长
            speaker_labels: 每个语音片段的说话人标签

        Returns:
            分析结果
        """
        # 根据说话人标签计算变化点
        speaker_change_times = self._find_speaker_changes(speech_segments, speaker_labels)

        final_splits, skipped_shots = self._process_shot_changes(
            shot_changes, speaker_change_times
        )

        final_splits.sort(key=lambda x: x.timestamp)
        final_splits = self._filter_close_splits(final_splits)

        return AnalysisResult(
            shot_changes=shot_changes,
            speech_segments=speech_segments,
            final_splits=final_splits,
            skipped_shots=skipped_shots
        )

    @staticmethod
    def _find_speaker_changes(
            speech_segments: List[SpeechSegment],
            speaker_labels: List[int] = None
    ) -> List[float]:
        """根据说话人标签找出变化点时间"""
        if not speaker_labels or len(speaker_labels) < 2:
            return []

        change_times = []
        for i in range(1, len(speaker_labels)):
            if speaker_labels[i] != speaker_labels[i - 1]:
                # 变化点在前一个片段结束时
                change_times.append(speech_segments[i - 1].end)
        return change_times

    def _process_shot_changes(
            self,
            shot_changes: List[float],
            speaker_change_times: List[float]
    ) -> Tuple[List[SplitPoint], List[Tuple[float, str]]]:
        """处理镜头切换点，结合说话人变化决定是否切分"""
        final_splits = []
        skipped_shots = []
        last_split_time = 0.0

        for shot_time in shot_changes:
            if shot_time - last_split_time < self._min_segment_duration:
                skipped_shots.append((shot_time, "片段太短"))
                continue

            if self._has_speaker_change_near(shot_time, speaker_change_times):
                split = SplitPoint(
                    timestamp=shot_time,
                    reason=SplitReason.SHOT_CHANGE_AND_SPEAKER_CHANGE,
                    confidence=SHOT_SPEAKER_CONFIDENCE
                )
                final_splits.append(split)
                last_split_time = shot_time
            else:
                skipped_shots.append((shot_time, "语音连续，不切分"))

        return final_splits, skipped_shots

    @staticmethod
    def _has_speaker_change_near(shot_time: float, speaker_change_times: List[float]) -> bool:
        """检查指定时间点附近是否有说话人变化"""
        for change_time in speaker_change_times:
            if abs(change_time - shot_time) < SHOT_SPEAKER_TIME_TOLERANCE:
                return True
        return False

    def _filter_close_splits(self, splits: List[SplitPoint]) -> List[SplitPoint]:
        """过滤掉间距太近的切分点，保留置信度更高的"""
        if len(splits) <= 1:
            return splits

        filtered = [splits[0]]
        for split in splits[1:]:
            if split.timestamp - filtered[-1].timestamp >= self._min_segment_duration:
                filtered.append(split)
            elif split.confidence > filtered[-1].confidence:
                filtered[-1] = split

        return filtered

    @staticmethod
    def get_segments_info(splits: List[SplitPoint], video_duration: float) -> List[SegmentInfo]:
        """获取分割后的片段信息"""
        timestamps = [0.0] + [s.timestamp for s in splits] + [video_duration]

        return [
            SegmentInfo(
                index=i,
                start=timestamps[i],
                end=timestamps[i + 1],
                duration=timestamps[i + 1] - timestamps[i]
            )
            for i in range(len(timestamps) - 1)
        ]