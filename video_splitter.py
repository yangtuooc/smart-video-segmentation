"""
视频分割模块
根据切分点将视频分割为多个片段
"""

import os
import subprocess
from typing import List

from models import SplitPoint


class VideoSplitter:
    """视频分割器"""

    def __init__(self, preset: str = "fast", crf: int = 23):
        """
        初始化视频分割器

        Args:
            preset: FFmpeg 编码预设（ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow）
            crf: 视频质量（0-51，越小质量越高，23为默认）
        """
        self.preset = preset
        self.crf = crf

    def split(
            self,
            input_path: str,
            output_dir: str,
            splits: List[SplitPoint],
            video_duration: float
    ) -> List[str]:
        """
        根据切分点分割视频

        Args:
            input_path: 输入视频路径
            output_dir: 输出目录
            splits: 切分点列表
            video_duration: 视频总时长

        Returns:
            输出文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)

        timestamps = [0.0] + [s.timestamp for s in splits] + [video_duration]
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_paths = []

        for i in range(len(timestamps) - 1):
            start = timestamps[i]
            end = timestamps[i + 1]
            duration = end - start
            output_path = os.path.join(output_dir, f"{base_name}_segment_{i:03d}.mp4")

            self._export_segment(input_path, output_path, start, duration)
            output_paths.append(output_path)

            print(f"已导出片段 {i}: {start:.2f}s - {end:.2f}s")

        print(f"\n视频分割完成，共 {len(output_paths)} 个片段")
        print(f"输出目录: {output_dir}")

        return output_paths

    def _export_segment(
            self,
            input_path: str,
            output_path: str,
            start: float,
            duration: float
    ) -> None:
        """导出单个视频片段"""
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", self.preset,
            "-crf", str(self.crf),
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
