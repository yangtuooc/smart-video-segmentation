"""
说话人分离模块
使用 resemblyzer 预训练模型提取说话人嵌入向量进行聚类
"""

import logging
from typing import List, Tuple

import librosa
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from .models import SpeechSegment

logger = logging.getLogger(__name__)

# 常量定义
MIN_AUDIO_DURATION = 0.3  # 最小音频时长（秒）
MIN_WAV_SAMPLES = 1600  # 最小采样点数
EMBEDDING_DIM = 256  # 嵌入向量维度
SAMPLE_RATE = 16000  # 采样率
MAX_SPEAKERS = 10  # 最大说话人数量


class SpeakerDiarizer:
    """说话人分离器（基于 resemblyzer）"""

    def __init__(self):
        logger.info("正在加载说话人嵌入模型...")
        self._encoder = VoiceEncoder()
        logger.info("说话人嵌入模型加载完成")

    def diarize(
            self,
            audio_path: str,
            speech_segments: List[SpeechSegment]
    ) -> List[int]:
        """
        对语音片段进行说话人分离

        Args:
            audio_path: 音频文件路径（wav 格式）
            speech_segments: 语音片段列表

        Returns:
            每个片段对应的说话人标签 [0, 0, 1, 1, 0, ...]
        """
        if len(speech_segments) < 2:
            return [0] * len(speech_segments)

        logger.info("正在提取说话人特征...")
        full_audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE)

        embeddings = self._extract_embeddings(full_audio, sr, speech_segments)
        labels = self._cluster_speakers(embeddings)
        self._log_result(speech_segments, labels)
        return labels

    def _extract_embeddings(
            self,
            full_audio: np.ndarray,
            sr: int,
            speech_segments: List[SpeechSegment]
    ) -> List[np.ndarray]:
        """为所有语音片段提取嵌入向量"""
        embeddings = []
        for i, seg in enumerate(speech_segments):
            emb = self._extract_embedding(full_audio, sr, seg.start, seg.end)
            embeddings.append(emb)
            if (i + 1) % 10 == 0:
                logger.debug("已处理 %d/%d 个片段", i + 1, len(speech_segments))
        return embeddings

    def _extract_embedding(
            self,
            full_audio: np.ndarray,
            sr: int,
            start: float,
            end: float
    ) -> np.ndarray:
        """从音频数组中提取指定时间段的说话人嵌入向量"""
        start_sample = max(0, int(start * sr))
        end_sample = min(len(full_audio), int(end * sr))
        y = full_audio[start_sample:end_sample]

        if len(y) < sr * MIN_AUDIO_DURATION:
            return np.zeros(EMBEDDING_DIM)

        wav = preprocess_wav(y, source_sr=sr)
        if len(wav) < MIN_WAV_SAMPLES:
            return np.zeros(EMBEDDING_DIM)

        return self._encoder.embed_utterance(wav)

    def _cluster_speakers(self, embeddings: List[np.ndarray]) -> List[int]:
        """对说话人嵌入向量进行聚类"""
        valid_indices = [i for i, emb in enumerate(embeddings) if np.any(emb != 0)]
        if len(valid_indices) < 2:
            return [0] * len(embeddings)

        valid_embeddings = np.array([embeddings[i] for i in valid_indices])

        logger.info("正在聚类识别说话人...")
        cluster_labels, _ = self._find_optimal_clusters(valid_embeddings)

        # 映射回原始索引
        labels = [-1] * len(embeddings)
        for i, idx in enumerate(valid_indices):
            labels[idx] = cluster_labels[i]

        # 填充无效片段（使用前一个片段的标签）
        for i in range(len(labels)):
            if labels[i] == -1:
                labels[i] = labels[i - 1] if i > 0 else 0

        return labels

    def _find_optimal_clusters(self, embeddings: np.ndarray) -> Tuple[List[int], int]:
        """自动确定最佳聚类数并返回标签"""
        n_samples = len(embeddings)
        if n_samples < 2:
            return [0] * n_samples, 1

        best_score = -1
        best_labels = None
        best_n = 2
        max_k = min(n_samples - 1, MAX_SPEAKERS)

        for k in range(2, max_k + 1):
            try:
                clustering = AgglomerativeClustering(
                    n_clusters=k,
                    metric='cosine',
                    linkage='average'
                )
                labels = clustering.fit_predict(embeddings)
                score = silhouette_score(embeddings, labels, metric='cosine')

                if score > best_score:
                    best_score = score
                    best_labels = labels.tolist()
                    best_n = k
            except Exception:
                continue

        if best_labels is None:
            clustering = AgglomerativeClustering(
                n_clusters=2,
                metric='cosine',
                linkage='average'
            )
            best_labels = clustering.fit_predict(embeddings).tolist()
            best_n = 2

        logger.info("自动检测到 %d 个说话人 (Silhouette Score: %.3f)", best_n, best_score)
        return best_labels, best_n

    @staticmethod
    def _log_result(speech_segments: List[SpeechSegment], labels: List[int]) -> None:
        """记录分离结果"""
        logger.debug("说话人分离结果:")
        for i, (seg, label) in enumerate(zip(speech_segments, labels)):
            marker = " [切换]" if i > 0 and labels[i] != labels[i - 1] else ""
            text_preview = seg.text[:20] + "..." if len(seg.text) > 20 else seg.text
            logger.debug("  Speaker %d: %.2fs-%.2fs \"%s\"%s", label, seg.start, seg.end, text_preview, marker)