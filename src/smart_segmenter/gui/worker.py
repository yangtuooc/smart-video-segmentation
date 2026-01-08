"""
后台工作线程
在独立线程中执行视频分析，避免阻塞 UI
"""

from PySide6.QtCore import QThread, Signal

from ..pipeline import PipelineConfig, PipelineResult, VideoPipeline


class AnalyzeWorker(QThread):
    """视频分析工作线程"""

    # 信号定义
    progress = Signal(int, int, str)  # (current, total, message)
    finished = Signal(PipelineResult)  # 分析结果
    error = Signal(str)  # 错误信息

    def __init__(self, video_path: str, config: PipelineConfig):
        super().__init__()
        self._video_path = video_path
        self._config = config

    def run(self):
        """执行分析任务"""
        try:
            pipeline = VideoPipeline(self._config)
            result = pipeline.analyze(
                self._video_path,
                on_progress=self._on_progress
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current: int, total: int, message: str):
        """进度回调"""
        self.progress.emit(current, total, message)


class SplitWorker(QThread):
    """视频分割工作线程"""

    finished = Signal(list)  # 输出文件列表
    error = Signal(str)

    def __init__(self, result: PipelineResult, output_dir: str):
        super().__init__()
        self._result = result
        self._output_dir = output_dir

    def run(self):
        """执行分割任务"""
        try:
            pipeline = VideoPipeline()
            output_files = pipeline.split_video(self._result, self._output_dir)
            self.finished.emit(output_files)
        except Exception as e:
            self.error.emit(str(e))
