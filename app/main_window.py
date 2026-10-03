"""Main application window."""

from __future__ import annotations

import html
import logging
import math
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import (
    QDesktopServices,
    QFontMetrics,
    QGuiApplication,
    QKeySequence,
    QPixmap,
    QShortcut,
    QTextBlockFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app import APP_NAME, APP_VERSION
from app.audio_recorder import AudioError, list_input_devices
from app.export_manager import ExportError, check_directory
from app.exporters import EXPORTERS
from app.filename_template import render_filename
from app.i18n import has, set_language, tr
from app.icons import clear_cache, icon, icon_size, pixmap, set_button_icon
from app.language_names import language_list, language_name
from app.logging_config import log_file
from app.recording_controller import AppState, RecordingController
from app.resources import assets_dir
from app.settings_manager import Settings, SettingsManager
from app.theme import THEME_MODES, apply_theme, refresh_style, set_mode, tokens
from app.transcript_models import format_clock

log = logging.getLogger(__name__)

# The content never grows wider than this, however large the window is. On a
# maximised window the controls would otherwise drift far apart and lines of
# text would become too long to read comfortably. See docs/DESIGN_RATIONALE.md.
MAX_CONTENT_WIDTH = 960

# Icon and text colour token for each kind of inline message.
_BANNER_ICONS = {
    "info": ("info", "accent"),
    "success": ("success", "success"),
    "warning": ("warning", "warning"),
    "error": ("error", "error"),
}


def error_text(code: str, detail: str = "") -> str:
    """Localized, user-facing message for an error code."""
    key = f"error.{code}"
    if not has(key):
        key = "error.unknown"
    return tr(key, detail=detail, log=str(log_file()))


def reveal_in_file_manager(path: Path) -> None:
    """Open the folder containing ``path`` and select the file if possible."""
    if sys.platform == "win32" and path.is_file():
        try:
            subprocess.Popen(["explorer", "/select,", str(path)])
            return
        except OSError:
            pass
    folder = path if path.is_dir() else path.parent
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))


def device_text(info) -> str:
    """Short description of the device used for recognition."""
    if info.device == "cuda":
        return tr("device.gpu", compute_type=info.compute_type)
    return tr("device.cpu", compute_type=info.compute_type)


class ElidedLabel(QLabel):
    """A label that shortens long paths in the middle and shows the full
    text as a tooltip."""

    def __init__(self) -> None:
        super().__init__()
        self._full = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setMinimumWidth(80)

    def set_full_text(self, text: str) -> None:
        self._full = text
        self.setToolTip(text)
        self._update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update()

    def _update(self) -> None:
        metrics = QFontMetrics(self.font())
        self.setText(
            metrics.elidedText(self._full, Qt.TextElideMode.ElideMiddle, max(self.width() - 4, 40))
        )


class TranscriptView(QTextEdit):
    """Read-only transcript whose lines never become longer than a
    comfortable reading measure, however wide the window is."""

    MAX_LINE_CHARACTERS = 80

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        limit = self.fontMetrics().averageCharWidth() * self.MAX_LINE_CHARACTERS
        if self.viewport().width() > limit:
            self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
            self.setLineWrapColumnOrWidth(limit)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)


class Banner(QFrame):
    """Inline message with an icon and optional actions. Used instead of
    modal dialogs so information never blocks the user."""

    def __init__(self, closable: bool = True) -> None:
        super().__init__()
        self.setObjectName("banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(6)
        self.buttons: list[QPushButton] = []
        self.close_button = QPushButton()
        self.close_button.setObjectName("flat")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setVisible(closable)
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.label, 1)
        layout.addLayout(self._actions)
        layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        self.hide()

    def show_message(self, text: str, kind: str = "info", actions=()) -> None:
        """``actions`` is a sequence of ``(label, icon name, callback)``."""
        colors = tokens()
        icon_name, color_token = _BANNER_ICONS.get(kind, _BANNER_ICONS["info"])
        self.icon_label.setPixmap(pixmap(icon_name, colors[color_token], 20))
        self.close_button.setIcon(icon("close"))
        self.label.setText(text)
        self.setProperty("kind", kind)
        refresh_style(self)

        for button in self.buttons:
            self._actions.removeWidget(button)
            button.deleteLater()
        self.buttons = []
        for label, icon_name, callback in actions:
            button = QPushButton(label)
            if icon_name:
                set_button_icon(button, icon_name)
            button.clicked.connect(callback)
            self._actions.addWidget(button)
            self.buttons.append(button)
        self.setAccessibleName(text)
        self.show()


class MainWindow(QMainWindow):
    def __init__(self, controller: RecordingController, settings_manager: SettingsManager) -> None:
        super().__init__()
        self.controller = controller
        self.settings_manager = settings_manager
        self._close_when_idle = False
        self._last_language: str | None = None
        self._speech = False
        self._pending_seconds = 0.0
        # Messages are stored as (kind, key, values, actions) so they can be
        # re-rendered when the interface language changes.
        self._banner_state: tuple | None = None
        self._result_state: tuple | None = None

        self._build_ui()
        self._connect()
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._update_timer)

        self.retranslate()
        self.refresh_devices()
        self._update_controls()
        self.resize(920, 740)
        self.setMinimumSize(720, 580)

    @property
    def settings(self) -> Settings:
        return self.controller.settings

    # -- construction ----------------------------------------------------

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        return card, layout

    def _icon_button(self, name: str, object_name: str = "") -> QPushButton:
        button = QPushButton()
        button.setProperty("iconName", name)
        button.setIconSize(icon_size())
        if object_name:
            button.setObjectName(object_name)
        return button

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(20, 16, 20, 10)
        column = QWidget()
        column.setMaximumWidth(MAX_CONTENT_WIDTH)
        outer.addStretch(1)
        outer.addWidget(column, 100)
        outer.addStretch(1)
        root = QVBoxLayout(column)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        self.setCentralWidget(central)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        self.logo_label = QLabel()
        logo = QPixmap(str(assets_dir() / "voxnote.png"))
        if not logo.isNull():
            self.logo_label.setPixmap(
                logo.scaled(
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.logo_label.setFixedSize(32, 32)
            self.logo_label.setScaledContents(True)
        self.title_label = QLabel(APP_NAME)
        self.title_label.setObjectName("title")
        self.version_label = QLabel()
        self.version_label.setObjectName("version")
        self.theme_button = self._icon_button("theme-system", "flat")
        self.theme_button.setFixedSize(36, 36)
        self.help_button = self._icon_button("help")
        self.settings_button = self._icon_button("settings")
        header.addWidget(self.logo_label)
        header.addWidget(self.title_label)
        header.addWidget(self.version_label, 0, Qt.AlignmentFlag.AlignBottom)
        header.addStretch(1)
        header.addWidget(self.theme_button)
        header.addWidget(self.help_button)
        header.addWidget(self.settings_button)
        root.addLayout(header)

        self.banner = Banner()
        root.addWidget(self.banner)

        # Recorder
        card, layout = self._card()
        row = QHBoxLayout()
        row.setSpacing(10)
        self.start_button = self._icon_button("microphone", "record")
        self.stop_button = self._icon_button("stop", "stop")
        self.status_pill = QLabel()
        self.status_pill.setObjectName("statusPill")
        self.status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setObjectName("timer")
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        row.addStretch(1)
        row.addWidget(self.status_pill)
        row.addSpacing(8)
        row.addWidget(self.timer_label)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.mic_label = QLabel()
        self.mic_combo = QComboBox()
        self.mic_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.mic_combo.setMinimumContentsLength(18)
        self.mic_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mic_label.setBuddy(self.mic_combo)
        self.mic_refresh = self._icon_button("refresh", "flat")
        self.mic_refresh.setFixedSize(34, 34)
        self.level_bar = QProgressBar()
        self.level_bar.setObjectName("level")
        self.level_bar.setRange(0, 100)
        self.level_bar.setTextVisible(False)
        self.level_bar.setFixedWidth(170)
        row.addWidget(self.mic_label)
        row.addWidget(self.mic_combo, 1)
        row.addWidget(self.mic_refresh)
        row.addSpacing(6)
        row.addWidget(self.level_bar)
        layout.addLayout(row)
        root.addWidget(card)

        # Transcript
        card, layout = self._card()
        row = QHBoxLayout()
        row.setSpacing(8)
        self.transcript_title = QLabel()
        self.transcript_title.setObjectName("sectionTitle")
        self.languages_icon = QLabel()
        self.languages_icon.setFixedSize(16, 16)
        self.languages_label = QLabel()
        self.languages_label.setObjectName("muted")
        self.languages_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.restriction_label = QLabel()
        self.restriction_label.setObjectName("hint")
        self.copy_button = self._icon_button("copy")
        self.save_button = self._icon_button("save", "primary")
        self.save_as_button = self._icon_button("save")
        row.addWidget(self.transcript_title)
        row.addSpacing(10)
        row.addWidget(self.languages_icon)
        row.addWidget(self.languages_label)
        row.addWidget(self.restriction_label)
        row.addStretch(1)
        row.addWidget(self.copy_button)
        row.addWidget(self.save_as_button)
        row.addWidget(self.save_button)
        layout.addLayout(row)
        self.transcript_view = TranscriptView()
        self.transcript_view.setObjectName("transcript")
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setMinimumHeight(150)
        layout.addWidget(self.transcript_view, 1)
        root.addWidget(card, 1)

        # Output
        card, layout = self._card()
        row = QHBoxLayout()
        row.setSpacing(10)
        self.folder_label = QLabel()
        self.folder_value = ElidedLabel()
        self.open_folder_button = self._icon_button("folder-open", "flat")
        self.open_folder_button.setFixedSize(34, 34)
        self.folder_button = QPushButton()
        self.format_label = QLabel()
        self.format_combo = QComboBox()
        for format_id, exporter in EXPORTERS.items():
            self.format_combo.addItem(exporter.label, format_id)
        self.format_label.setBuddy(self.format_combo)
        row.addWidget(self.folder_label)
        row.addWidget(self.folder_value, 1)
        row.addWidget(self.open_folder_button)
        row.addWidget(self.folder_button)
        row.addSpacing(10)
        row.addWidget(self.format_label)
        row.addWidget(self.format_combo)
        layout.addLayout(row)
        self.filename_hint = QLabel()
        self.filename_hint.setObjectName("hint")
        layout.addWidget(self.filename_hint)
        self.result_banner = Banner(closable=False)
        layout.addWidget(self.result_banner)
        root.addWidget(card)

        # Footer: short confirmations on the left, the speech model on the
        # right. It is part of the centred column so that it stays close to
        # the content instead of sitting in the far corner of a large window.
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 0, 2, 0)
        footer.setSpacing(8)
        self.status_message = QLabel()
        self.status_message.setObjectName("hint")
        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self.status_message.clear)
        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 0)
        self.model_progress.setFixedWidth(110)
        self.model_progress.setTextVisible(False)
        self.model_icon = QLabel()
        self.model_icon.setFixedSize(16, 16)
        self.model_label = QLabel()
        self.model_label.setObjectName("hint")
        footer.addWidget(self.status_message, 1)
        footer.addWidget(self.model_progress)
        footer.addWidget(self.model_icon)
        footer.addWidget(self.model_label)
        root.addLayout(footer)

        self.setTabOrder(self.start_button, self.stop_button)
        self.setTabOrder(self.stop_button, self.mic_combo)

    def _connect(self) -> None:
        c = self.controller
        c.state_changed.connect(self._on_state_changed)
        c.model_status.connect(self._on_model_status)
        c.model_download_progress.connect(self._on_model_download_progress)
        c.model_failed.connect(self._on_model_failed)
        c.device_changed.connect(lambda _info: self._update_model_label())
        c.segments_added.connect(self._on_segments_added)
        c.languages_changed.connect(self._on_languages_changed)
        c.session_reset.connect(self._on_session_reset)
        c.level.connect(self._on_level)
        c.speech_active.connect(self._on_speech_active)
        c.pending_changed.connect(self._on_pending_changed)
        c.notice.connect(self._on_notice)
        c.saved.connect(self._on_saved)
        c.error.connect(self._on_error)

        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.settings_button.clicked.connect(self.open_settings)
        self.help_button.clicked.connect(self.open_help)
        self.theme_button.clicked.connect(self.cycle_theme)
        # In "system" mode, follow the operating system while running.
        try:
            QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_system_scheme_changed)
        except AttributeError:
            pass  # older Qt versions have no such signal
        self.mic_refresh.clicked.connect(lambda: self.refresh_devices(rescan=True))
        self.mic_combo.activated.connect(self._on_mic_selected)
        self.format_combo.activated.connect(self._on_format_selected)
        self.folder_button.clicked.connect(self.choose_folder)
        self.copy_button.clicked.connect(self.copy_transcript)
        self.open_folder_button.clicked.connect(self.open_folder)
        self.save_button.clicked.connect(self.save_now)
        self.save_as_button.clicked.connect(self.save_as)

        # Shortcuts for frequent users; each one is also shown in a tooltip.
        for sequence, slot in (
            ("Ctrl+R", self.start_recording),
            ("Ctrl+E", self.stop_recording),
            ("Ctrl+,", self.open_settings),
            ("F1", self.open_help),
            ("Ctrl+T", self.cycle_theme),
            ("Ctrl+Shift+S", self.save_as),
            ("Ctrl+Shift+C", self.copy_transcript),
            ("Ctrl+O", self.open_folder),
        ):
            QShortcut(QKeySequence(sequence), self, activated=slot)

    # -- texts and icons -------------------------------------------------

    def _apply_icons(self) -> None:
        colors = tokens()
        special = {"record": colors["record_text"], "primary": colors["accent_text"]}
        self.theme_button.setProperty("iconName", f"theme-{self.settings.theme}")
        for button in self.findChildren(QPushButton):
            name = button.property("iconName")
            if name:
                set_button_icon(button, name, special.get(button.objectName()))
        self.languages_icon.setPixmap(pixmap("languages", colors["muted"], 16))
        self.model_icon.setPixmap(pixmap("chip", colors["muted"], 16))

    def retranslate(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.version_label.setText(tr("app.version", version=APP_VERSION))
        self.settings_button.setText(tr("main.settings"))
        self.settings_button.setToolTip(tr("main.settings.tip", shortcut="Ctrl+,"))
        self.help_button.setText(tr("main.help"))
        self.help_button.setToolTip(tr("main.help.tip", shortcut="F1"))
        theme_name = tr(f"theme.{self.settings.theme}")
        self.theme_button.setToolTip(tr("main.theme.tip", mode=theme_name, shortcut="Ctrl+T"))
        self.theme_button.setAccessibleName(tr("main.theme.tip", mode=theme_name, shortcut="Ctrl+T"))
        self.start_button.setText(tr("main.start"))
        self.stop_button.setText(tr("main.stop"))
        self.stop_button.setToolTip(tr("main.stop.tip", shortcut="Ctrl+E"))
        self.mic_label.setText(tr("main.microphone"))
        self.mic_refresh.setToolTip(tr("main.refresh.tip"))
        self.mic_refresh.setAccessibleName(tr("main.refresh"))
        self.level_bar.setToolTip(tr("main.level"))
        self.level_bar.setAccessibleName(tr("main.level"))
        self.transcript_title.setText(tr("main.transcript"))
        self.transcript_view.setPlaceholderText(tr("main.transcript.placeholder"))
        self.transcript_view.setAccessibleName(tr("main.transcript"))
        self.copy_button.setText(tr("main.copy"))
        self.copy_button.setToolTip(tr("main.copy.tip", shortcut="Ctrl+Shift+C"))
        self.folder_label.setText(tr("main.folder"))
        self.folder_button.setText(tr("main.folder.change"))
        self.folder_button.setToolTip(tr("main.folder.change.tip"))
        self.format_label.setText(tr("main.format"))
        self.open_folder_button.setToolTip(tr("main.open_folder.tip", shortcut="Ctrl+O"))
        self.open_folder_button.setAccessibleName(tr("main.open_folder"))
        self.save_button.setText(tr("main.save"))
        self.save_button.setToolTip(tr("main.save.tip"))
        self.save_as_button.setText(tr("main.save_as"))
        self.save_as_button.setToolTip(tr("main.save_as.tip", shortcut="Ctrl+Shift+S"))
        self.banner.close_button.setToolTip(tr("main.dismiss"))
        self.banner.close_button.setAccessibleName(tr("main.dismiss"))
        self.timer_label.setAccessibleName(tr("main.elapsed"))
        self.timer_label.setToolTip(tr("main.elapsed"))
        self._apply_icons()
        self._refresh_default_device_text()
        self._update_output_fields()
        self._update_languages()
        self._update_model_label()
        self._update_controls()
        if self._banner_state:
            self._show_banner(*self._banner_state)
        if self._result_state:
            self._show_result(*self._result_state)

    def _flash(self, text: str, milliseconds: int = 4000) -> None:
        """Show a short confirmation in the footer."""
        self.status_message.setText(text)
        self._message_timer.stop()
        if milliseconds:
            self._message_timer.start(milliseconds)

    def _render(self, key: str, values: dict) -> str:
        if key in ("@error", "@model"):
            return error_text(values["code"], values.get("detail", ""))
        return tr(key, **values)

    def _actions(self, specs) -> list:
        """Turn ``(label key, icon name, callback)`` into translated actions."""
        return [(tr(label_key), icon_name, callback) for label_key, icon_name, callback in specs]

    def _show_banner(self, kind: str, key: str, values: dict, actions=()) -> None:
        self._banner_state = (kind, key, values, actions)
        self.banner.show_message(self._render(key, values), kind, self._actions(actions))

    def _show_result(self, kind: str, key: str, values: dict, actions=()) -> None:
        self._result_state = (kind, key, values, actions)
        self.result_banner.show_message(self._render(key, values), kind, self._actions(actions))

    def _clear_result(self) -> None:
        self._result_state = None
        self.result_banner.hide()

    def _clear_banner(self) -> None:
        self._banner_state = None
        self.banner.hide()

    # -- devices and output fields ---------------------------------------

    def _refresh_default_device_text(self) -> None:
        if self.mic_combo.count():
            self.mic_combo.setItemText(0, tr("main.microphone.default"))

    def refresh_devices(self, rescan: bool = False) -> None:
        if self.controller.is_busy:
            return
        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()
        self.mic_combo.addItem(tr("main.microphone.default"), "")
        try:
            devices = list_input_devices(refresh=rescan)
        except AudioError as exc:
            devices = []
            self._show_banner("error", "@error", {"code": exc.code, "detail": exc.detail})
        for device in devices:
            self.mic_combo.addItem(device.name, device.name)
        index = self.mic_combo.findData(self.settings.microphone)
        self.mic_combo.setCurrentIndex(max(index, 0))
        self.mic_combo.blockSignals(False)
        if not devices and not self._banner_state:
            self._show_banner("warning", "@error", {"code": "no_microphone"})
        elif devices and self._banner_state and self._banner_state[2].get("code") == "no_microphone":
            self._clear_banner()
        if rescan and devices:
            self._flash(tr("main.refresh.done", count=len(devices)), 4000)

    def _update_output_fields(self) -> None:
        self.folder_value.set_full_text(str(self.settings.resolved_save_directory()))
        index = self.format_combo.findData(self.settings.export_format)
        self.format_combo.setCurrentIndex(max(index, 0))
        example = render_filename(self.settings.filename_template, self.controller.session)
        extension = EXPORTERS[self.settings.export_format].extension
        # Before anything was recorded the name is only an example.
        in_session = self.controller.is_busy or self.controller.has_transcript
        key = "main.filename_hint" if in_session else "main.filename_example"
        self.filename_hint.setText(tr(key, name=f"{example}.{extension}"))

    def _persist(self) -> None:
        try:
            self.settings_manager.save(self.settings)
        except OSError as exc:
            log.exception("Settings could not be saved")
            self._show_banner("warning", "error.settings_save_failed", {"detail": str(exc)})

    def _on_mic_selected(self, index: int) -> None:
        self.settings.microphone = self.mic_combo.itemData(index) or ""
        self._persist()

    def _on_format_selected(self, index: int) -> None:
        self.settings.export_format = self.format_combo.itemData(index)
        self._persist()
        self._update_output_fields()

    def choose_folder(self) -> None:
        if self.controller.state is AppState.SAVING:
            return
        start = self.settings.resolved_save_directory()
        while not start.exists() and start != start.parent:
            start = start.parent
        chosen = QFileDialog.getExistingDirectory(self, tr("main.folder.dialog"), str(start))
        if not chosen:
            return
        try:
            check_directory(Path(chosen))
        except ExportError as exc:
            self._show_result("error", "@error", {"code": exc.code, "detail": exc.detail})
            return
        self.settings.save_directory = chosen
        self._persist()
        self._update_output_fields()
        self._flash(tr("main.folder.changed"), 4000)

    # -- recording -------------------------------------------------------

    def start_recording(self) -> None:
        if not self.controller.can_start:
            return
        if self.controller.has_unsaved_transcript:
            answer = QMessageBox.question(
                self,
                tr("dialog.unsaved.title"),
                tr("dialog.unsaved.text"),
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Discard:
                return
        # Find out about an unusable folder before the user speaks, not after.
        try:
            check_directory(self.settings.resolved_save_directory(), create=True)
        except ExportError as exc:
            self._show_banner(
                "error",
                "@error",
                {"code": exc.code, "detail": exc.detail},
                (("main.folder.change", "folder", self.choose_folder),),
            )
            return
        self._clear_banner()
        self._clear_result()
        self.controller.start()

    def stop_recording(self) -> None:
        self.controller.stop()

    def _on_state_changed(self, state: AppState) -> None:
        if state is AppState.RECORDING:
            self._timer.start()
        else:
            self._timer.stop()
            if state is AppState.PROCESSING:
                self._update_timer()
        if state in (AppState.COMPLETED, AppState.ERROR) and self.controller.session.duration_seconds:
            self.timer_label.setText(format_clock(self.controller.session.duration_seconds))
        self._update_controls()
        self._update_output_fields()
        if self._close_when_idle and not self.controller.is_busy:
            if state is AppState.COMPLETED:
                self.close()
            else:
                self._close_when_idle = False  # saving failed; keep the window open

    def _update_timer(self) -> None:
        elapsed = time.monotonic() - self.controller.started_monotonic
        self.timer_label.setText(format_clock(elapsed))

    def _update_controls(self) -> None:
        c = self.controller
        state = c.state
        idle = not c.is_busy
        self.start_button.setEnabled(c.can_start)
        self.stop_button.setEnabled(c.can_stop)
        if c.can_start:
            self.start_button.setToolTip(tr("main.start.tip", shortcut="Ctrl+R"))
        elif not c.model_ready and idle:
            self.start_button.setToolTip(tr("main.start.tip.model"))
        else:
            self.start_button.setToolTip(tr("main.start.tip.busy"))

        self.mic_combo.setEnabled(idle)
        self.mic_refresh.setEnabled(idle)
        self.format_combo.setEnabled(state is not AppState.SAVING)
        self.folder_button.setEnabled(state is not AppState.SAVING)
        self.settings_button.setEnabled(idle)
        self.copy_button.setEnabled(c.has_transcript)
        self.save_as_button.setEnabled(idle and c.has_transcript)
        # "Save" is only offered when the automatic save did not happen.
        self.save_button.setVisible(idle and c.has_unsaved_transcript)

        text = tr(f"state.{state.value}")
        if state is AppState.RECORDING and self._speech:
            text = tr("state.recording.speech")
        elif state is AppState.PROCESSING and self._pending_seconds >= 1:
            text = tr("state.processing.pending", seconds=int(self._pending_seconds))
        self.status_pill.setText(text)
        self.status_pill.setAccessibleName(tr("main.status", status=text))
        if self.status_pill.property("state") != state.value:
            self.status_pill.setProperty("state", state.value)
            refresh_style(self.status_pill)

    def _on_level(self, peak: float) -> None:
        # Map -50 dB .. 0 dB to the meter range.
        value = 0 if peak <= 0 else int(max(0.0, min(1.0, (20 * math.log10(peak) + 50) / 50)) * 100)
        self.level_bar.setValue(value)

    def _on_speech_active(self, active: bool) -> None:
        self._speech = active
        self.level_bar.setProperty("speech", "true" if active else "false")
        refresh_style(self.level_bar)
        self._update_controls()

    def _on_pending_changed(self, seconds: float) -> None:
        self._pending_seconds = seconds
        if self.controller.state is AppState.PROCESSING:
            self._update_controls()

    # -- appearance ------------------------------------------------------

    def apply_appearance(self) -> None:
        """Re-style everything for the current theme mode."""
        set_mode(self.settings.theme)
        apply_theme(QApplication.instance())
        clear_cache()
        self.retranslate()
        # The transcript carries its colours inline, so it is rendered again.
        self.transcript_view.clear()
        self._last_language = None
        if self.controller.session.segments:
            self._on_segments_added(list(self.controller.session.segments))

    def cycle_theme(self) -> None:
        """Switch between system, light and dark appearance."""
        current = THEME_MODES.index(self.settings.theme) if self.settings.theme in THEME_MODES else 0
        self.settings.theme = THEME_MODES[(current + 1) % len(THEME_MODES)]
        self._persist()
        self.apply_appearance()
        self._flash(tr("main.theme.changed", mode=tr(f"theme.{self.settings.theme}")))

    def _on_system_scheme_changed(self, *_args) -> None:
        if self.settings.theme == "system":
            self.apply_appearance()

    # -- transcript ------------------------------------------------------

    def _on_session_reset(self) -> None:
        self.transcript_view.clear()
        self._last_language = None
        self._pending_seconds = 0.0
        self.timer_label.setText("00:00:00")
        self._update_languages()
        self._update_output_fields()

    def _on_segments_added(self, segments: list) -> None:
        view = self.transcript_view
        bar = view.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        colors = tokens()
        cursor = view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        def add_line(markup: str, top_margin: int) -> None:
            # Every line is its own block, so lines never run together.
            block_format = QTextBlockFormat()
            block_format.setTopMargin(top_margin)
            block_format.setBottomMargin(2)
            if view.document().isEmpty():
                cursor.setBlockFormat(block_format)
            else:
                cursor.insertBlock(block_format)
            cursor.insertHtml(markup)

        for segment in segments:
            if segment.language != self._last_language:
                first = self._last_language is None
                self._last_language = segment.language
                add_line(
                    f'<span style="color:{colors["accent"]}; font-weight:600;">'
                    f"{html.escape(language_name(segment.language))}</span>",
                    0 if first else 10,
                )
            stamp = ""
            if self.settings.include_timestamps:
                stamp = (
                    f'<span style="color:{colors["muted"]};">'
                    f"[{format_clock(segment.start)}]</span> "
                )
            add_line(
                f'{stamp}<span style="color:{colors["text"]}; font-weight:400;">'
                f"{html.escape(segment.text)}</span>",
                0,
            )
        if at_bottom:
            bar.setValue(bar.maximum())
        self._update_controls()

    def _on_languages_changed(self, _codes: list) -> None:
        self._update_languages()
        self._update_output_fields()

    def _update_languages(self) -> None:
        names = language_list(self.controller.session.languages)
        self.languages_label.setText(names or tr("main.languages.none"))
        self.languages_label.setToolTip(tr("main.languages.tip"))
        self.languages_label.setAccessibleName(
            tr("main.languages", languages=names or tr("main.languages.none"))
        )
        # Remind the user when recognition is limited to certain languages;
        # anything else they say is written in one of those.
        allowed = language_list(self.settings.spoken_languages)
        self.restriction_label.setVisible(bool(allowed))
        self.restriction_label.setText(tr("main.languages.limited", languages=allowed))
        self.restriction_label.setToolTip(tr("main.languages.limited.tip"))

    def copy_transcript(self) -> None:
        if not self.controller.has_transcript:
            return
        text = "\n".join(s.text for s in self.controller.session.segments if s.text.strip())
        QGuiApplication.clipboard().setText(text)
        self._flash(tr("main.copy.done"), 4000)

    # -- saving ----------------------------------------------------------

    def _on_saved(self, path: str) -> None:
        self._show_result(
            "success",
            "result.saved",
            {"path": path},
            (
                ("main.open_file", "file", self.open_saved_file),
                ("main.open_folder", "folder-open", self.open_folder),
            ),
        )
        self._update_controls()
        if self.settings.open_after_save and not self._close_when_idle:
            self.open_saved_file()

    def _on_error(self, code: str, detail: str) -> None:
        if code in ("no_microphone", "microphone_open_failed", "audio_backend_unavailable"):
            self._show_banner("error", "@error", {"code": code, "detail": detail})
        else:
            self._show_result("error", "@error", {"code": code, "detail": detail})
        self._update_controls()

    def _on_notice(self, code: str) -> None:
        if code == "no_speech":
            self._show_result("info", "notice.no_speech", {})
        elif code == "session_recovered":
            self._flash(tr("notice.session_recovered"), 6000)
        else:
            self._show_banner("warning", f"notice.{code}", {})

    def save_now(self) -> None:
        self._clear_result()
        self.controller.save()

    def save_as(self) -> None:
        c = self.controller
        if c.is_busy or not c.has_transcript:
            return
        filters = {exporter.label: fid for fid, exporter in EXPORTERS.items()}
        current = EXPORTERS[self.settings.export_format]
        stem = render_filename(self.settings.filename_template, c.session)
        start = self.settings.resolved_save_directory()
        if not start.exists():
            start = Path.home()
        chosen, selected = QFileDialog.getSaveFileName(
            self,
            tr("main.save_as.dialog"),
            str(start / f"{stem}.{current.extension}"),
            ";;".join(f"{label} (*.{EXPORTERS[fid].extension})" for label, fid in filters.items()),
            f"{current.label} (*.{current.extension})",
        )
        if not chosen:
            return
        format_id = next(
            (fid for label, fid in filters.items() if selected.startswith(label)),
            self.settings.export_format,
        )
        target = Path(chosen)
        extension = EXPORTERS[format_id].extension
        if target.suffix.lower() != f".{extension}":
            target = target.with_name(f"{target.name}.{extension}")
        self._clear_result()
        c.save_as(target, format_id)

    def open_saved_file(self) -> None:
        path = self.controller.saved_path
        if path is None or not path.exists():
            self._show_result("warning", "result.file_missing", {})
            self._update_controls()
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            self._show_result("warning", "result.open_failed", {"path": str(path)})

    def open_folder(self) -> None:
        path = self.controller.saved_path
        if path is not None and path.exists():
            reveal_in_file_manager(path)
            return
        folder = self.settings.resolved_save_directory()
        if not folder.is_dir():
            self._show_result("warning", "@error", {"code": "directory_missing", "detail": str(folder)})
            return
        reveal_in_file_manager(folder)

    # -- model -----------------------------------------------------------

    def _on_model_status(self, code: str) -> None:
        self._update_model_label()
        self._update_controls()
        if code == "ready" and self._banner_state and self._banner_state[1] == "@model":
            self._clear_banner()

    def _on_model_download_progress(self, megabytes: int) -> None:
        if self.controller.model_state == "downloading":
            self.model_label.setText(tr("model.downloading.progress", megabytes=megabytes))

    def _on_model_failed(self, code: str, detail: str) -> None:
        self._show_banner(
            "error",
            "@model",
            {"code": code, "detail": detail},
            (("model.retry", "refresh", self.controller.load_model),),
        )

    def _update_model_label(self) -> None:
        c = self.controller
        state = c.model_state
        info = c.device_info
        self.model_progress.setVisible(state in ("checking", "downloading", "initializing"))
        tooltip = tr("model.tip")
        if state == "ready" and info is not None:
            text = tr("model.ready", model=c.transcriber.model_name, device=device_text(info))
            if info.fallback_reason and has(f"device.reason.{info.fallback_reason}"):
                tooltip = tr(f"device.reason.{info.fallback_reason}")
        elif state == "idle":
            text = tr("model.idle")
        else:
            text = tr(f"model.{state}")
        self.model_label.setText(text)
        self.model_label.setToolTip(tooltip)

    # -- dialogs and lifecycle -------------------------------------------

    def open_settings(self) -> None:
        if self.controller.is_busy:
            return
        from app.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.settings, self.controller, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        new_settings = dialog.result_settings()
        language_changed = new_settings.ui_language != self.settings.ui_language
        theme_changed = new_settings.theme != self.settings.theme
        self.controller.apply_settings(new_settings)
        self._persist()
        if language_changed:
            set_language(new_settings.ui_language)
        if theme_changed:
            self.apply_appearance()
        else:
            self.retranslate()
        self._flash(tr("settings.saved"), 4000)

    def open_help(self, tab: int = 0) -> None:
        from app.help_dialog import HelpDialog

        HelpDialog(self, start_tab=tab if isinstance(tab, int) else 0).exec()

    def show_first_run_help(self) -> None:
        """Show the short introduction once, on the first start."""
        if self.settings.tutorial_seen:
            return
        self.settings.tutorial_seen = True
        self._persist()
        self.open_help(0)

    def check_recovery(self) -> None:
        """Offer to restore transcripts that were never saved (after a crash)."""
        journals = self.controller.recoverable_journals()
        if not journals:
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(tr("dialog.recover.title"))
        box.setText(tr("dialog.recover.text", count=len(journals)))
        recover = box.addButton(tr("dialog.recover.recover"), QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton(tr("dialog.recover.discard"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(tr("dialog.recover.later"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(recover)
        box.exec()
        if box.clickedButton() is recover:
            self.controller.recover(journals)
        elif box.clickedButton() is discard:
            self.controller.discard_journals(journals)

    def closeEvent(self, event) -> None:
        c = self.controller
        if c.state is AppState.RECORDING:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(tr("dialog.close.title"))
            box.setText(tr("dialog.close.recording"))
            stop = box.addButton(tr("dialog.close.stop_save"), QMessageBox.ButtonRole.AcceptRole)
            box.addButton(tr("dialog.close.keep"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(stop)
            box.exec()
            if box.clickedButton() is stop:
                self._close_when_idle = True
                c.stop()
            event.ignore()
            return
        if c.is_busy:
            # Speech is still being recognised or the file is being written.
            self._close_when_idle = True
            self._flash(tr("dialog.close.wait"), 0)
            event.ignore()
            return
        if c.has_unsaved_transcript:
            answer = QMessageBox.question(
                self,
                tr("dialog.unsaved.title"),
                tr("dialog.close.unsaved"),
                QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Close:
                event.ignore()
                return
        c.shutdown()
        event.accept()
