"""
说话人变化检测模块
使用 resemblyzer 预训练模型提取说话人嵌入向量进行聚类
"""

from typing import List, Tuple

import librosa
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from models import SpeechSegment
from utils import extract_audio

# 常量定义
MIN_AUDIO_DURATION = 0.3  # 最小音频时长（秒）
MIN_WAV_SAMPLES = 1600  # 最小采样点数
EMBEDDING_DIM = 256  # 嵌入向量维度
SAMPLE_RATE = 16000  # 采样率
MAX_SPEAKERS = 5  # 最大说话人数


class SpeakerChangeDetector:
    """说话人变化检测器（基于 resemblyzer）"""

    def __init__(self):
        print("正在加载说话人嵌入模型...")
        self._encoder = VoiceEncoder()
        print("说话人嵌入模型加载完成")

    def analyze_segments(
            self,
            video_path: str,
            speech_segments: List[SpeechSegment]
    ) -> List[Tuple[float, float]]:
        """
        分析语音片段，找出说话人变化的位置

        Args:
            video_path: 视频文件路径
            speech_segments: 语音片段列表

        Returns:
            说话人变化点列表 [(时间点, 变化程度), ...]
        """
        if len(speech_segments) < 2:
            return []

        print("正在提取说话人特征...")

        with extract_audio(video_path) as audio_path:
            embeddings = self._extract_all_embeddings(audio_path, speech_segments)
            labels = self._cluster_speakers(embeddings)
            self._print_analysis(speech_segments, labels)
            return self._generate_change_points(speech_segments, labels)

    def _extract_all_embeddings(
            self,
            audio_path: str,
            speech_segments: List[SpeechSegment]
    ) -> List[np.ndarray]:
        """为所有语音片段提取嵌入向量"""
        embeddings = []
        for i, seg in enumerate(speech_segments):
            emb = self._extract_embedding(audio_path, seg.start, seg.end)
            embeddings.append(emb)
            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{len(speech_segments)} 个片段")
        return embeddings

    def _extract_embedding(self, audio_path: str, start: float, end: float) -> np.ndarray:
        """提取指定时间段的说话人嵌入向量"""
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, offset=start, duration=end - start)

        if len(y) < sr * MIN_AUDIO_DURATION:
            return np.zeros(EMBEDDING_DIM)

        wav = preprocess_wav(y, source_sr=sr)
        if len(wav) < MIN_WAV_SAMPLES:
            return np.zeros(EMBEDDING_DIM)

        return self._encoder.embed_utterance(wav)

    def _cluster_speakers(self, embeddings: List[np.ndarray]) -> List[int]:
        """对说话人嵌入向量进行聚类"""
        # 过滤全零向量
        valid_indices = [i for i, emb in enumerate(embeddings) if np.any(emb != 0)]
        if len(valid_indices) < 2:
            return [0] * len(embeddings)

        valid_embeddings = np.array([embeddings[i] for i in valid_indices])

        # 自动聚类
        print("正在聚类识别说话人...")
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
        max_k = min(MAX_SPEAKERS, n_samples - 1)

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

        print(f"自动检测到 {best_n} 个说话人 (Silhouette Score: {best_score:.3f})")
        return best_labels, best_n

    @staticmethod
    def _print_analysis(speech_segments: List[SpeechSegment], labels: List[int]) -> None:
        """打印说话人分析结果"""
        print("\n语音片段说话人分析:")
        for i, (seg, label) in enumerate(zip(speech_segments, labels)):
            marker = " *** 说话人切换" if i > 0 and labels[i] != labels[i - 1] else ""
            text_preview = seg.text[:20] + "..." if len(seg.text) > 20 else seg.text
            print(f"  [{label}] {seg.start:.2f}s - {seg.end:.2f}s: \"{text_preview}\"{marker}")

    @staticmethod
    def _generate_change_points(
            speech_segments: List[SpeechSegment],
            labels: List[int]
    ) -> List[Tuple[float, float]]:
        """生成说话人切换点列表"""
        speaker_changes = []
        for i in range(1, len(labels)):
            change_time = speech_segments[i - 1].end
            change_score = 1.0 if labels[i] != labels[i - 1] else 0.0
            speaker_changes.append((change_time, change_score))
        return speaker_changes
