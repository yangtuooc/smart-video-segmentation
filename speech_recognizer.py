"""
语音识别模块
使用 Whisper 识别视频中的语音内容和时间戳
"""

from typing import List

import whisper

from models import SpeechSegment
from utils import extract_audio


class SpeechRecognizer:
    """语音识别器"""

    def __init__(self, model_size: str = "base", language: str = "zh"):
        """
        初始化语音识别器

        Args:
            model_size: Whisper 模型大小（tiny, base, small, medium, large）
            language: 语音语言代码
        """
        self._language = language
        print(f"正在加载 Whisper {model_size} 模型...")
        self._model = whisper.load_model(model_size)
        print("模型加载完成")

    def recognize(self, video_path: str) -> List[SpeechSegment]:
        """识别视频中的语音"""
        print("正在提取音频...")

        with extract_audio(video_path) as audio_path:
            print("正在识别语音...")
            result = self._model.transcribe(
                audio_path,
                language=self._language,
                word_timestamps=True,
                verbose=False
            )

            segments = [
                SpeechSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip()
                )
                for seg in result["segments"]
            ]

            return segments
