# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

智能视频分割工具 - 结合镜头检测和语音识别，智能判断视频切分点。

核心逻辑：镜头切换 + 说话人变化 → 切分；镜头切换 + 同一人说话 → 不切分

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 基本使用
python main.py <视频路径>

# 指定输出目录
python main.py <视频路径> -o <输出目录>

# 只分析不分割
python main.py <视频路径> --no-split

# 导出分析结果到 JSON
python main.py <视频路径> --export-json result.json

# 完整参数示例
python main.py video.mp4 -o ./output --whisper-model small --language zh --shot-threshold 0.5 --min-segment 2.0
```

## 外部依赖

- FFmpeg: 用于音频提取和视频分割（需要系统安装）
- TransNetV2: 镜头检测模型
- Whisper: OpenAI 语音识别模型
- Resemblyzer: 说话人嵌入模型

## 架构

处理流水线：`main.py` 按顺序调用以下模块：

1. **ShotDetector** (`shot_detector.py`) - 使用 TransNetV2 检测镜头切换点
2. **SpeechRecognizer** (`speech_recognizer.py`) - 使用 Whisper 识别语音片段
3. **SpeakerChangeDetector** (`speaker_change_detector.py`) - 使用 Resemblyzer 提取说话人嵌入，通过聚类检测说话人变化
4. **SmartSegmenter** (`smart_segmenter.py`) - 融合镜头切换和说话人变化信息，决策最终切分点
5. **VideoSplitter** (`video_splitter.py`) - 使用 FFmpeg 执行视频分割

数据模型统一定义在 `models.py`，工具函数在 `utils.py`（音频提取、视频时长获取）。