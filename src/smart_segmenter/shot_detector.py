"""
镜头检测模块
使用 TransNetV2 (PyTorch) 检测视频中的镜头切换点
"""

import logging
from typing import List

from transnetv2_pytorch import TransNetV2

logger = logging.getLogger(__name__)


class ShotDetector:
    """镜头检测器 (基于 TransNetV2 PyTorch)"""

    def __init__(self, threshold: float = 0.5, device: str = "auto"):
        """
        初始化镜头检测器

        Args:
            threshold: 镜头切换检测阈值（0-1）
            device: 运行设备（auto, cpu, cuda）
        """
        self._threshold = threshold
        logger.info("正在加载 TransNetV2 模型...")
        self._model = TransNetV2(device=device)
        logger.info("TransNetV2 模型加载完成")

    def detect(self, video_path: str) -> List[float]:
        """
        检测视频中的镜头切换点

        Args:
            video_path: 视频文件路径

        Returns:
            镜头切换点时间戳列表
        """
        logger.info("正在检测镜头切换...")
        scenes = self._model.detect_scenes(video_path, threshold=self._threshold)

        shot_timestamps = [float(scene['end_time']) for scene in scenes[:-1]]

        logger.info("检测到 %d 个镜头切换点", len(shot_timestamps))
        return shot_timestamps
