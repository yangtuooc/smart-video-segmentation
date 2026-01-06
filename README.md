# Smart Video Segmentation

Intelligent video segmentation tool based on deep learning.

## Overview

This tool combines **shot detection** and **speaker recognition** to intelligently determine optimal video split points. Suitable for ad material segmentation, video editing preprocessing, etc.

## Features

- 🎬 **Shot Boundary Detection** - TransNetV2 deep learning model
- 🎤 **Speech Recognition** - OpenAI Whisper with multi-language support
- 👥 **Speaker Recognition** - Resemblyzer embeddings + automatic clustering
- 🧠 **Smart Decision** - Multi-signal fusion for split point determination
- ✂️ **Video Export** - FFmpeg lossless splitting

## Requirements

- Python 3.8+
- FFmpeg (must be installed and added to PATH)

## Installation

```bash
# Clone the project
git clone <repository-url>
cd smart-video-segmentation

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Analyze and split video
python main.py input.mp4

# Analyze only, no splitting
python main.py input.mp4 --no-split

# Specify output directory
python main.py input.mp4 -o ./output

# Export analysis results to JSON
python main.py input.mp4 --export-json result.json --no-split
```

## Usage

### Command Line Arguments

```
python main.py <video> [options]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `video` | str | required | Input video file path |
| `-o, --output` | str | `./segments` | Output directory |
| `--whisper-model` | str | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `--language` | str | `zh` | Speech language code |
| `--shot-threshold` | float | `0.5` | Shot detection threshold (0-1) |
| `--min-segment` | float | `2.0` | Minimum segment duration (seconds) |
| `--no-split` | flag | - | Analyze only, don't split video |
| `--export-json` | str | - | Export analysis results to JSON |

### Output Example

```
============================================================
Smart Video Segmentation Tool
============================================================
Input video: example.mp4

[1/4] Shot Detection
----------------------------------------
Loading TransNetV2 model...
Detected 8 shot changes
Video duration: 139.60 seconds

[2/4] Speech Recognition
----------------------------------------
Recognized 52 speech segments

[3/4] Speaker Change Detection
----------------------------------------
Auto-detected 4 speakers (Silhouette Score: 0.365)
Detected 3 speaker change points

[4/4] Smart Analysis
----------------------------------------
Final split points: 2
  - 37.97s (shot change with speaker change)
  - 101.60s (shot change with speaker change)

Will produce 3 segments:
  Segment 0: 0.00s - 37.97s (duration: 37.97s)
  Segment 1: 37.97s - 101.60s (duration: 63.63s)
  Segment 2: 101.60s - 139.60s (duration: 38.00s)
```

### JSON Output Format

```json
{
  "video": "example.mp4",
  "duration": 139.60,
  "shot_changes": [5.93, 37.97, ...],
  "speech_segments": [
    {"start": 0.00, "end": 7.72, "text": "..."}
  ],
  "final_splits": [
    {"timestamp": 37.97, "reason": "shot change with speaker change", "confidence": 0.9}
  ],
  "segments": [
    {"index": 0, "start": 0.0, "end": 37.97, "duration": 37.97}
  ]
}
```

## Architecture

```
smart-video-segmentation/
├── main.py                    # Entry point, argument parsing, workflow orchestration
├── models.py                  # Data models (SpeechSegment, SplitPoint, etc.)
├── utils.py                   # Utilities (audio extraction, video duration)
├── shot_detector.py           # Shot detection (TransNetV2)
├── speech_recognizer.py       # Speech recognition (Whisper)
├── speaker_change_detector.py # Speaker detection (Resemblyzer + Clustering)
├── smart_segmenter.py         # Smart fusion decision
├── video_splitter.py          # Video splitting (FFmpeg)
└── requirements.txt
```
