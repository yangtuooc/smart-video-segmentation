"""
视频播放器组件
支持播放控制、音量调节、快进快退、键盘快捷键
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class VideoPlayer(QWidget):
    """视频播放器"""

    # 信号
    position_changed = Signal(float)  # 时间位置（秒）
    duration_changed = Signal(float)  # 视频时长（秒）

    # 常量
    SEEK_STEP = 5.0  # 快进/快退步长（秒）
    SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

    def __init__(self):
        super().__init__()
        self._duration = 0.0
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 视频显示区域
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumSize(480, 270)
        layout.addWidget(self._video_widget, 1)

        # 播放器
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._audio.setVolume(0.8)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video_widget)

        # 连接信号
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

        # 进度条
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 1000)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.sliderMoved.connect(self._on_slider_moved)
        layout.addWidget(self._slider)

        # 控制栏
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.setSpacing(8)

        # 播放控制按钮
        self._back_btn = QPushButton("-5s")
        self._back_btn.setToolTip("Seek backward 5s (Left)")
        self._back_btn.setFixedWidth(40)
        self._back_btn.clicked.connect(self._seek_backward)
        controls_layout.addWidget(self._back_btn)

        self._play_btn = QPushButton("Play")
        self._play_btn.setToolTip("Play/Pause (Space)")
        self._play_btn.setFixedWidth(50)
        self._play_btn.clicked.connect(self._toggle_play)
        controls_layout.addWidget(self._play_btn)

        self._forward_btn = QPushButton("+5s")
        self._forward_btn.setToolTip("Seek forward 5s (Right)")
        self._forward_btn.setFixedWidth(40)
        self._forward_btn.clicked.connect(self._seek_forward)
        controls_layout.addWidget(self._forward_btn)

        # 时间标签
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setMinimumWidth(110)
        controls_layout.addWidget(self._time_label)

        controls_layout.addStretch()

        # 播放速度
        speed_label = QLabel("Speed")
        controls_layout.addWidget(speed_label)

        self._speed_combo = QComboBox()
        self._speed_combo.setFixedWidth(70)
        for speed in self.SPEED_OPTIONS:
            self._speed_combo.addItem(f"{speed}x", speed)
        self._speed_combo.setCurrentIndex(self.SPEED_OPTIONS.index(1.0))
        self._speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        controls_layout.addWidget(self._speed_combo)

        # 音量控制
        self._volume_btn = QPushButton("Vol")
        self._volume_btn.setToolTip("Mute/Unmute (M)")
        self._volume_btn.setFixedWidth(40)
        self._volume_btn.clicked.connect(self._toggle_mute)
        controls_layout.addWidget(self._volume_btn)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(80)
        self._volume_slider.setToolTip("Volume (Up/Down)")
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_layout.addWidget(self._volume_slider)

        layout.addWidget(controls)

        # 状态
        self._is_slider_pressed = False
        self._was_playing = False
        self._is_muted = False
        self._last_volume = 80

    def _setup_shortcuts(self):
        """设置焦点策略以接收键盘事件"""
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event: QKeyEvent):
        """键盘快捷键处理"""
        key = event.key()

        if key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Left:
            self._seek_backward()
        elif key == Qt.Key.Key_Right:
            self._seek_forward()
        elif key == Qt.Key.Key_Up:
            self._adjust_volume(10)
        elif key == Qt.Key.Key_Down:
            self._adjust_volume(-10)
        elif key == Qt.Key.Key_M:
            self._toggle_mute()
        else:
            super().keyPressEvent(event)

    def load(self, path: str):
        """加载视频文件"""
        from PySide6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(path))
        self.setFocus()

    def play(self):
        """播放"""
        self._player.play()

    def pause(self):
        """暂停"""
        self._player.pause()

    def stop(self):
        """停止"""
        self._player.stop()

    def seek(self, position: float):
        """跳转到指定时间（秒）"""
        position = max(0.0, min(position, self._duration))
        self._player.setPosition(int(position * 1000))

    def get_duration(self) -> float:
        """获取视频时长（秒）"""
        return self._duration

    def get_position(self) -> float:
        """获取当前位置（秒）"""
        return self._player.position() / 1000.0

    def _toggle_play(self):
        """切换播放/暂停"""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def _seek_forward(self):
        """快进"""
        self.seek(self.get_position() + self.SEEK_STEP)

    def _seek_backward(self):
        """快退"""
        self.seek(self.get_position() - self.SEEK_STEP)

    def _on_slider_pressed(self):
        """进度条按下"""
        self._is_slider_pressed = True
        self._was_playing = self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if self._was_playing:
            self._player.pause()

    def _on_slider_released(self):
        """进度条释放"""
        self._is_slider_pressed = False
        if self._was_playing:
            self._player.play()

    def _on_slider_moved(self, value: int):
        """进度条拖动"""
        if self._duration > 0:
            position = value / 1000 * self._duration
            self._player.setPosition(int(position * 1000))

    def _on_speed_changed(self, index: int):
        """播放速度变化"""
        speed = self._speed_combo.itemData(index)
        self._player.setPlaybackRate(speed)

    def _on_volume_changed(self, value: int):
        """音量变化"""
        self._audio.setVolume(value / 100.0)
        self._update_volume_icon()

    def _toggle_mute(self):
        """切换静音"""
        if self._is_muted:
            self._volume_slider.setValue(self._last_volume)
            self._is_muted = False
        else:
            self._last_volume = self._volume_slider.value()
            self._volume_slider.setValue(0)
            self._is_muted = True
        self._update_volume_icon()

    def _adjust_volume(self, delta: int):
        """调整音量"""
        new_value = max(0, min(100, self._volume_slider.value() + delta))
        self._volume_slider.setValue(new_value)

    def _update_volume_icon(self):
        """更新音量图标"""
        volume = self._volume_slider.value()
        if volume == 0:
            self._volume_btn.setText("Mute")
        else:
            self._volume_btn.setText("Vol")

    @Slot(int)
    def _on_position_changed(self, ms: int):
        """播放位置变化"""
        position = ms / 1000.0
        self.position_changed.emit(position)

        # 更新进度条（非拖动时）
        if not self._is_slider_pressed and self._duration > 0:
            self._slider.blockSignals(True)
            self._slider.setValue(int(position / self._duration * 1000))
            self._slider.blockSignals(False)

        # 更新时间标签
        self._time_label.setText(
            f"{self._format_time(position)} / {self._format_time(self._duration)}"
        )

    @Slot(int)
    def _on_duration_changed(self, ms: int):
        """视频时长变化"""
        self._duration = ms / 1000.0
        self.duration_changed.emit(self._duration)

    @Slot(QMediaPlayer.PlaybackState)
    def _on_state_changed(self, state: QMediaPlayer.PlaybackState):
        """播放状态变化"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("Pause")
            self._play_btn.setToolTip("Pause (Space)")
        else:
            self._play_btn.setText("Play")
            self._play_btn.setToolTip("Play (Space)")

    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间"""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
