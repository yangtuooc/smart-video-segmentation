"""
视频处理流水线模块
协调各模块执行完整的视频分析和分割流程
"""

import os
from dataclasses import dataclass
from typing import Callable, List, Optional

from .models import AnalysisResult, SegmentInfo, SpeechSegment
from .shot_detector import ShotDetector
from .smart_segmenter import SmartSegmenter
from .speaker_diarizer import SpeakerDiarizer
from .speech_recognizer import SpeechRecognizer
from .utils import extract_audio, get_video_duration
from .video_splitter import VideoSplitter


@dataclass
class PipelineConfig:
    """流水线配置"""
    whisper_model: str = "base"
    language: str = "zh"
    shot_threshold: float = 0.5
    min_segment_duration: float = 2.0


@dataclass
class PipelineResult:
    """流水线执行结果"""
    video_path: str
    video_duration: float
    shot_changes: List[float]
    speech_segments: List[SpeechSegment]
    speaker_labels: List[int]
    analysis_result: AnalysisResult
    segments_info: List[SegmentInfo]


# 进度回调函数类型
ProgressCallback = Callable[[int, int, str], None]


class VideoPipeline:
    """视频处理流水线"""

    def __init__(self, config: PipelineConfig = None):
        self._config = config or PipelineConfig()

    def analyze(
        self,
        video_path: str,
        on_progress: ProgressCallback = None
    ) -> PipelineResult:
        """
        分析视频，返回分析结果

        Args:
            video_path: 视频文件路径
            on_progress: 进度回调函数 (step, total, message)

        Returns:
            PipelineResult: 分析结果
        """
        def report(step: int, total: int, msg: str):
            if on_progress:
                on_progress(step, total, msg)

        with extract_audio(video_path) as audio_path:
            report(1, 4, "镜头检测")
            shot_detector = ShotDetector(threshold=self._config.shot_threshold)
            shot_changes = shot_detector.detect(video_path)
            video_duration = get_video_duration(video_path)

            report(2, 4, "语音识别")
            speech_recognizer = SpeechRecognizer(
                model_size=self._config.whisper_model,
                language=self._config.language
            )
            speech_segments = speech_recognizer.recognize(audio_path)

            report(3, 4, "说话人分离")
            diarizer = SpeakerDiarizer()
            speaker_labels = diarizer.diarize(audio_path, speech_segments)

            report(4, 4, "智能分析")
            segmenter = SmartSegmenter(min_segment_duration=self._config.min_segment_duration)
            analysis_result = segmenter.analyze(
                shot_changes, speech_segments, video_duration, speaker_labels
            )

        segments_info = SmartSegmenter.get_segments_info(
            analysis_result.final_splits, video_duration
        )

        return PipelineResult(
            video_path=video_path,
            video_duration=video_duration,
            shot_changes=shot_changes,
            speech_segments=speech_segments,
            speaker_labels=speaker_labels,
            analysis_result=analysis_result,
            segments_info=segments_info,
        )

    def split_video(
        self,
        result: PipelineResult,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        根据分析结果分割视频

        Args:
            result: 分析结果
            output_dir: 输出目录，默认为视频所在目录下的 segments 文件夹

        Returns:
            输出文件路径列表
        """
        if not result.analysis_result.final_splits:
            return []

        if not output_dir:
            video_dir = os.path.dirname(result.video_path) or "."
            output_dir = os.path.join(video_dir, "segments")

        splitter = VideoSplitter()
        return splitter.split(
            result.video_path,
            output_dir,
            result.analysis_result.final_splits,
            result.video_duration
        )