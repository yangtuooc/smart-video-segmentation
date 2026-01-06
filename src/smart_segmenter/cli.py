"""
命令行接口模块
只负责参数解析和输出格式化，业务逻辑委托给 pipeline
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="sseg",
    help="智能视频分割工具 - 结合镜头检测和语音识别",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def setup_logging(verbose: bool = False) -> None:
    """配置日志输出"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )


class WhisperModel(str, Enum):
    """Whisper 模型大小"""
    tiny = "tiny"
    base = "base"
    small = "small"
    medium = "medium"
    large = "large"


def print_header(video_path: str) -> None:
    """打印程序头部信息"""
    print("智能视频分割工具")
    print(f"输入: {video_path}")
    print()


def print_progress(step: int, total: int, title: str) -> None:
    """打印进度信息"""
    print(f"[{step}/{total}] {title}")


def print_result(result) -> None:
    """打印分析结果"""
    analysis = result.analysis_result
    print()
    print(f"镜头切换: {len(analysis.shot_changes)} | 切分点: {len(analysis.final_splits)} | 跳过: {len(analysis.skipped_shots)}")

    if analysis.final_splits:
        print()
        print("切分点:")
        for split in analysis.final_splits:
            print(f"  {split.timestamp:.2f}s - {split.reason.value}")

    print()
    print(f"片段 ({len(result.segments_info)}):")
    for seg in result.segments_info:
        print(f"  #{seg.index}: {seg.start:.2f}s ~ {seg.end:.2f}s ({seg.duration:.2f}s)")


def export_to_json(filepath: str, result) -> None:
    """导出分析结果到 JSON 文件"""
    export_data = {
        "video": result.video_path,
        "duration": result.video_duration,
        "shot_changes": result.shot_changes,
        "speech_segments": [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in result.speech_segments
        ],
        "final_splits": [
            {"timestamp": s.timestamp, "reason": s.reason.value, "confidence": s.confidence}
            for s in result.analysis_result.final_splits
        ],
        "segments": [seg.to_dict() for seg in result.segments_info],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    print(f"导出: {filepath}")


@app.command()
def main(
    video: Path = typer.Argument(..., help="输入视频文件路径", exists=True),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="输出目录"),
    whisper_model: WhisperModel = typer.Option(
        WhisperModel.base, "-m", "--model", help="Whisper 模型大小"
    ),
    language: str = typer.Option("zh", "-l", "--lang", help="语音语言代码"),
    shot_threshold: float = typer.Option(0.5, "-t", "--threshold", help="镜头检测阈值"),
    min_segment: float = typer.Option(2.0, "-s", "--min-seg", help="最小片段时长（秒）"),
    no_split: bool = typer.Option(False, "-n", "--no-split", help="只分析不分割"),
    export_json: Optional[Path] = typer.Option(None, "-e", "--export", help="导出 JSON"),
    verbose: bool = typer.Option(False, "--verbose", help="显示详细日志"),
) -> None:
    """
    智能视频分割工具

    结合镜头检测和说话人变化检测，智能判断视频切分点。
    """
    setup_logging(verbose)

    # 延迟导入避免启动时加载模型
    from .pipeline import PipelineConfig, VideoPipeline

    video_path = str(video)
    print_header(video_path)

    # 配置并执行流水线
    config = PipelineConfig(
        whisper_model=whisper_model.value,
        language=language,
        shot_threshold=shot_threshold,
        min_segment_duration=min_segment,
    )
    pipeline = VideoPipeline(config)
    result = pipeline.analyze(video_path, on_progress=print_progress)

    # 输出结果
    print_result(result)

    # 导出 JSON
    if export_json:
        export_to_json(str(export_json), result)

    # 分割视频
    if not no_split and result.analysis_result.final_splits:
        print()
        print("分割视频...")
        output_dir = str(output) if output else None
        pipeline.split_video(result, output_dir)

    print()
    print("完成")


if __name__ == "__main__":
    app()