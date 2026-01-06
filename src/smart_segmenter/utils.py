"""
公共工具函数
提供音频提取、视频信息获取等功能
"""

import os
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Generator

import cv2


def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）"""
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        return frame_count / fps if fps > 0 else 0.0
    finally:
        cap.release()


@contextmanager
def extract_audio(video_path: str) -> Generator[str, None, None]:
    """
    从视频中提取音频的上下文管理器
    使用完毕后自动清理临时文件

    Usage:
        with extract_audio(video_path) as audio_path:
            # 使用 audio_path
    """
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio.close()

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        temp_audio.name
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    try:
        yield temp_audio.name
    finally:
        if os.path.exists(temp_audio.name):
            os.unlink(temp_audio.name)
