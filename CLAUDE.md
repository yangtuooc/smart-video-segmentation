# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 开发原则

优先搜索并遵守业界最佳实践规范，遵守软件设计原则：

- **SOLID**: 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置
- **KISS**: 保持简单
- **DRY**: 不要重复自己
- **关注点分离**: CLI 只负责参数解析和输出，业务逻辑放在独立模块

## 项目概述

智能视频分割工具 - 结合镜头检测和语音识别，智能判断视频切分点。

## 常用命令

```bash
# 安装（开发模式）
pip install -e .

# 基本使用
sseg <视频路径>

# 指定输出目录
sseg <视频路径> -o <输出目录>

# 只分析不分割
sseg <视频路径> -n

# 导出分析结果到 JSON
sseg <视频路径> -e result.json

# 查看帮助
sseg -h

# 完整参数示例
sseg video.mp4 -o ./output -m small -l zh -t 0.5 -s 2.0
```

## 外部依赖

- FFmpeg: 用于音频提取和视频分割（需要系统安装）
- TransNetV2: 镜头检测模型
- Whisper: OpenAI 语音识别模型
- Resemblyzer: 说话人嵌入模型

## 项目结构

采用 **src 布局**（Python 打包最佳实践）：

```
smart-video-segmentation/
├── src/
│   └── smart_segmenter/      # 包目录
│       ├── __init__.py
│       ├── cli.py            # CLI 层：参数解析、输出格式化
│       ├── pipeline.py       # 视频流程处理
│       ├── shot_detector.py  # 镜头检测 (TransNetV2)
│       ├── speech_recognizer.py  # 语音识别 (Whisper)
│       ├── speaker_diarizer.py   # 说话人分离 (Resemblyzer)
│       ├── smart_segmenter.py    # 智能融合决策
│       ├── video_splitter.py     # 视频分割 (FFmpeg)
│       ├── models.py         # 数据模型
│       └── utils.py          # 工具函数
├── tests/
├── pyproject.toml            # 项目配置（依赖、构建、脚本）
├── README.md
└── CLAUDE.md
```

