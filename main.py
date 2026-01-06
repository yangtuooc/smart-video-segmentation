#!/usr/bin/env python3
"""
智能视频分割工具

结合镜头检测和语音识别，智能判断视频切分点。
核心逻辑：镜头切换 + 说话人变化 → 切分；镜头切换 + 同一人说话 → 不切分
"""

import argparse
import json
import os

from shot_detector import ShotDetector
from smart_segmenter import SmartSegmenter
from speaker_change_detector import SpeakerChangeDetector
from speech_recognizer import SpeechRecognizer
from utils import get_video_duration
from video_splitter import VideoSplitter


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="智能视频分割工具 - 结合镜头检测和语音识别"
    )
    parser.add_argument("video", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出目录（默认为视频同目录下的 segments 文件夹）")
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小（默认: base）"
    )
    parser.add_argument("--language", default="zh", help="语音语言代码（默认: zh 中文）")
    parser.add_argument("--shot-threshold", type=float, default=0.5, help="镜头检测阈值（默认: 0.5）")
    parser.add_argument("--min-segment", type=float, default=2.0, help="最小片段时长，秒（默认: 2.0）")
    parser.add_argument("--no-split", action="store_true", help="只分析不分割视频")
    parser.add_argument("--export-json", help="导出分析结果到 JSON 文件")

    return parser.parse_args()


def print_header(video_path: str) -> None:
    """打印程序头部信息"""
    print("=" * 60)
    print("智能视频分割工具")
    print("=" * 60)
    print(f"输入视频: {video_path}\n")


def print_section(step: int, total: int, title: str) -> None:
    """打印步骤标题"""
    print(f"[{step}/{total}] {title}")
    print("-" * 40)


def export_json(filepath: str, video_path: str, video_duration: float,
                shot_changes: list, speech_segments: list, result, segments_info: list) -> None:
    """导出分析结果到 JSON 文件"""
    export_data = {
        "video": video_path,
        "duration": video_duration,
        "shot_changes": shot_changes,
        "speech_segments": [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in speech_segments
        ],
        "final_splits": [
            {"timestamp": s.timestamp, "reason": s.reason.value, "confidence": s.confidence}
            for s in result.final_splits
        ],
        "segments": [seg.to_dict() for seg in segments_info]
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    print(f"\n分析结果已导出到: {filepath}")


def main():
    args = parse_args()

    if not os.path.exists(args.video):
        print(f"错误: 视频文件不存在: {args.video}")
        return 1

    print_header(args.video)

    # 1. 镜头检测
    print_section(1, 4, "镜头检测")
    shot_detector = ShotDetector(threshold=args.shot_threshold)
    shot_changes = shot_detector.detect(args.video)
    video_duration = get_video_duration(args.video)
    print(f"视频时长: {video_duration:.2f} 秒\n")

    # 2. 语音识别
    print_section(2, 4, "语音识别")
    speech_recognizer = SpeechRecognizer(model_size=args.whisper_model, language=args.language)
    speech_segments = speech_recognizer.recognize(args.video)
    print(f"识别到 {len(speech_segments)} 个语音片段\n")

    # 3. 说话人变化检测
    print_section(3, 4, "说话人变化检测")
    speaker_detector = SpeakerChangeDetector()
    speaker_changes = speaker_detector.analyze_segments(args.video, speech_segments)

    if speaker_changes:
        change_points = [(t, c) for t, c in speaker_changes if c > 0.5]
        print(f"检测到说话人切换点: {len(change_points)} 个")
        for t, _ in change_points:
            print(f"  - {t:.2f}s")
    print()

    # 4. 智能融合
    print_section(4, 4, "智能分析")
    segmenter = SmartSegmenter(min_segment_duration=args.min_segment)
    result = segmenter.analyze(shot_changes, speech_segments, video_duration, speaker_changes)

    # 打印分析结果
    print(f"\n原始镜头切换点: {len(result.shot_changes)} 个")
    print(f"最终切分点: {len(result.final_splits)} 个")
    print(f"被跳过的切换点: {len(result.skipped_shots)} 个")

    if result.skipped_shots:
        print("\n被跳过的镜头切换（因语音连续）:")
        for timestamp, reason in result.skipped_shots[:5]:
            print(f"  - {timestamp:.2f}s: {reason}")
        if len(result.skipped_shots) > 5:
            print(f"  ... 还有 {len(result.skipped_shots) - 5} 个")

    print("\n最终切分点:")
    for split in result.final_splits:
        print(f"  - {split.timestamp:.2f}s ({split.reason.value})")

    segments_info = SmartSegmenter.get_segments_info(result.final_splits, video_duration)
    print(f"\n分割后将产生 {len(segments_info)} 个片段:")
    for seg in segments_info:
        print(f"  片段 {seg.index}: {seg.start:.2f}s - {seg.end:.2f}s (时长: {seg.duration:.2f}s)")

    # 导出 JSON
    if args.export_json:
        export_json(
            args.export_json, args.video, video_duration,
            shot_changes, speech_segments, result, segments_info
        )

    # 分割视频
    if not args.no_split and result.final_splits:
        print("\n" + "=" * 60)
        print("开始分割视频")
        print("=" * 60)

        output_dir = args.output
        if not output_dir:
            video_dir = os.path.dirname(args.video) or "."
            output_dir = os.path.join(video_dir, "segments")

        splitter = VideoSplitter()
        splitter.split(args.video, output_dir, result.final_splits, video_duration)

    print("\n完成!")
    return 0


if __name__ == "__main__":
    exit(main())
