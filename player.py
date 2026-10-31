from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QSplitter,
)


AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
VIDEO_EXT = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
MEDIA_EXT = AUDIO_EXT | VIDEO_EXT


def format_time(ms: int) -> str:
    total = max(0, ms // 1000)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class MediaPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медіаплеєр")
        self.resize(980, 620)
        self.setAcceptDrops(True)

        self._seeking = False
        self._loop = False
        self._muted = False

        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.8)

        self._build_ui()
        self._connect_signals()
        self._add_shortcuts()

    def _build_ui(self):
        self.video = QVideoWidget()
        self.video.setMinimumHeight(280)
        self.player.setVideoOutput(self.video)

        self.placeholder = QLabel("Відкрийте файл або URL")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #c9d1d9; font-size: 16px;")

        self.video_stack = QWidget()
        stack_layout = QVBoxLayout(self.video_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.addWidget(self.video)
        stack_layout.addWidget(self.placeholder)
        self.video.hide()

        self.playlist = QListWidget()
        self.playlist.setMinimumWidth(220)
        self.playlist.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        splitter = QSplitter()
        splitter.addWidget(self.video_stack)
        splitter.addWidget(self.playlist)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(110)

        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setToolTip("Play / Pause")

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.setToolTip("Stop")

        self.back_btn = QPushButton("−10 с")
        self.fwd_btn = QPushButton("+10 с")
        self.loop_btn = QPushButton("Повтор")
        self.loop_btn.setCheckable(True)

        self.speed_box = QComboBox()
        self.speed_box.addItems(["0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x"])
        self.speed_box.setCurrentText("1x")

        self.mute_btn = QPushButton()
        self.mute_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.mute_btn.setToolTip("Без звуку")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setMaximumWidth(140)

        open_file_btn = QPushButton("Відкрити файл")
        open_url_btn = QPushButton("Відкрити URL")

        controls = QHBoxLayout()
        controls.addWidget(self.back_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.fwd_btn)
        controls.addWidget(self.loop_btn)
        controls.addWidget(QLabel("Швидкість:"))
        controls.addWidget(self.speed_box)
        controls.addStretch()
        controls.addWidget(self.mute_btn)
        controls.addWidget(self.volume_slider)

        progress = QHBoxLayout()
        progress.addWidget(self.position_slider)
        progress.addWidget(self.time_label)

        top = QHBoxLayout()
        top.addWidget(open_file_btn)
        top.addWidget(open_url_btn)
        top.addStretch()

        root = QVBoxLayout()
        root.addLayout(top)
        root.addWidget(splitter, 1)
        root.addLayout(progress)
        root.addLayout(controls)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        for btn in (
            self.play_btn,
            self.stop_btn,
            self.back_btn,
            self.fwd_btn,
            self.loop_btn,
            self.mute_btn,
            open_file_btn,
            open_url_btn,
        ):
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        open_file_btn.clicked.connect(self.open_file)
        open_url_btn.clicked.connect(self.open_url)

        open_act = QAction("Відкрити файл", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self.open_file)
        url_act = QAction("Відкрити URL", self)
        url_act.setShortcut("Ctrl+U")
        url_act.triggered.connect(self.open_url)
        self.menuBar().addMenu("Файл").addActions([open_act, url_act])

        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #1e1e1e; color: #e6e6e6; }
            QPushButton {
                background: #2d2d2d; border: 1px solid #3d3d3d;
                padding: 6px 10px; border-radius: 6px;
            }
            QPushButton:hover { background: #3a3a3a; }
            QPushButton:checked { background: #0e639c; }
            QSlider::groove:horizontal { height: 6px; background: #3d3d3d; border-radius: 3px; }
            QSlider::handle:horizontal {
                width: 14px; margin: -5px 0; background: #61dafb; border-radius: 7px;
            }
            QListWidget { background: #252526; border: 1px solid #3d3d3d; }
            QComboBox { background: #2d2d2d; padding: 4px; }
            QMenuBar { background: #252526; }
            """
        )

    def _connect_signals(self):
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop)
        self.back_btn.clicked.connect(lambda _: self.skip(-10_000))
        self.fwd_btn.clicked.connect(lambda _: self.skip(10_000))
        self.loop_btn.toggled.connect(self._set_loop)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.speed_box.currentTextChanged.connect(self._set_speed)
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.playlist.itemDoubleClicked.connect(self._play_item)

        self.position_slider.sliderPressed.connect(self._begin_seek)
        self.position_slider.sliderReleased.connect(self._end_seek)
        self.position_slider.sliderMoved.connect(self._preview_time)

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_status)
        self.player.errorOccurred.connect(self._on_error)

    def _add_shortcuts(self):
        for key, handler in (
            (Qt.Key.Key_Space, self.toggle_play),
            (Qt.Key.Key_S, self.stop),
            (Qt.Key.Key_Left, lambda: self.skip(-10_000)),
            (Qt.Key.Key_Right, lambda: self.skip(10_000)),
            (Qt.Key.Key_M, self.toggle_mute),
            (Qt.Key.Key_Up, lambda: self._bump_volume(5)),
            (Qt.Key.Key_Down, lambda: self._bump_volume(-5)),
        ):
            act = QAction(self)
            act.setShortcut(QKeySequence(key))
            act.triggered.connect(lambda _, h=handler: h())
            self.addAction(act)

    def open_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Відкрити медіафайл",
            str(Path.home()),
            "Медіафайли (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.mp4 *.avi *.mkv *.mov *.webm);;"
            "Аудіо (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;"
            "Відео (*.mp4 *.avi *.mkv *.mov *.webm);;"
            "Усі файли (*)",
        )
        if files:
            self._add_files(files, play_first=True)

    def open_url(self):
        url, ok = QInputDialog.getText(self, "Відкрити URL", "Введіть посилання на медіа:")
        url = url.strip()
        if ok and url:
            self._add_url(url, play=True)

    def toggle_play(self):
        if not self.player.source().isValid():
            self.open_file()
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()

    def skip(self, delta_ms: int):
        duration = self.player.duration()
        pos = max(0, self.player.position() + delta_ms)
        if duration > 0:
            pos = min(pos, duration)
        self.player.setPosition(pos)

    def toggle_mute(self):
        self._muted = not self._muted
        self.audio.setMuted(self._muted)
        icon = (
            QStyle.StandardPixmap.SP_MediaVolumeMuted
            if self._muted
            else QStyle.StandardPixmap.SP_MediaVolume
        )
        self.mute_btn.setIcon(self.style().standardIcon(icon))

    def _set_loop(self, checked: bool):
        self._loop = checked

    def _set_speed(self, text: str):
        self.player.setPlaybackRate(float(text.replace("x", "")))

    def _set_volume(self, value: int):
        self.audio.setVolume(value / 100)
        if value > 0 and self._muted:
            self.toggle_mute()

    def _bump_volume(self, step: int):
        self.volume_slider.setValue(self.volume_slider.value() + step)

    def _begin_seek(self):
        self._seeking = True

    def _end_seek(self):
        self.player.setPosition(self.position_slider.value())
        self._seeking = False

    def _preview_time(self, value: int):
        self.time_label.setText(f"{format_time(value)} / {format_time(self.player.duration())}")

    def _on_position(self, pos: int):
        if not self._seeking:
            self.position_slider.setValue(pos)
            self.time_label.setText(f"{format_time(pos)} / {format_time(self.player.duration())}")

    def _on_duration(self, duration: int):
        self.position_slider.setRange(0, max(0, duration))
        self.time_label.setText(f"{format_time(self.player.position())} / {format_time(duration)}")

    def _on_state(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        icon = QStyle.StandardPixmap.SP_MediaPause if playing else QStyle.StandardPixmap.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))

    def _on_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._loop:
                self.player.setPosition(0)
                self.player.play()
            else:
                self._play_next()

    def _on_error(self, error, text=""):
        if error == QMediaPlayer.Error.NoError:
            return
        message = text or self.player.errorString() or "Не вдалося відтворити файл"
        QMessageBox.warning(self, "Помилка відтворення", message)

    def _add_files(self, files, play_first=False):
        first_item = None
        for path in files:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, QUrl.fromLocalFile(str(Path(path).resolve())))
            item.setToolTip(path)
            self.playlist.addItem(item)
            if first_item is None:
                first_item = item
        if play_first and first_item is not None:
            self._play_item(first_item)

    def _add_url(self, url: str, play=False):
        qurl = QUrl(url)
        if not qurl.isValid():
            QMessageBox.warning(self, "URL", "Некоректне посилання")
            return
        item = QListWidgetItem(url)
        item.setData(Qt.ItemDataRole.UserRole, qurl)
        self.playlist.addItem(item)
        if play:
            self._play_item(item)

    def _play_item(self, item: QListWidgetItem):
        url = item.data(Qt.ItemDataRole.UserRole)
        self.playlist.setCurrentItem(item)
        self.player.setSource(url)
        self._show_video_or_audio(url)
        self.statusBar().showMessage(url.toString())
        self.player.play()

    def _show_video_or_audio(self, url: QUrl):
        suffix = Path(url.toLocalFile() or url.path()).suffix.lower()
        is_video = suffix in VIDEO_EXT or not suffix
        if url.scheme() in {"http", "https"} and suffix not in AUDIO_EXT:
            is_video = True
        self.video.setVisible(is_video)
        self.placeholder.setVisible(not is_video)
        if not is_video:
            name = Path(url.toLocalFile() or url.path()).name or url.toString()
            self.placeholder.setText(f"Аудіо\n{name}")

    def _play_next(self):
        row = self.playlist.currentRow()
        if 0 <= row < self.playlist.count() - 1:
            self._play_item(self.playlist.item(row + 1))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and Path(path).suffix.lower() in MEDIA_EXT:
                files.append(path)
            elif url.scheme() in {"http", "https"}:
                self._add_url(url.toString(), play=not files)
        if files:
            self._add_files(files, play_first=True)
