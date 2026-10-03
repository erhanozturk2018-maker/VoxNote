"""Settings dialog.

Nothing is applied until the user confirms with *Save*; *Cancel* leaves
every setting untouched, and *Restore defaults* only fills the form, so it
can still be cancelled.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import MODEL_NAME, paths
from app.audio_recorder import AudioError, list_input_devices
from app.export_manager import ExportError, check_directory
from app.exporters import EXPORTERS
from app.filename_template import PLACEHOLDERS, render_filename, template_errors
from app.i18n import available_languages, has, tr
from app.recording_controller import RecordingController
from app.settings_manager import LIMITS, Settings
from app.theme import refresh_style
from app.workers import _directory_bytes


def _hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("hint")
    label.setWordWrap(True)
    return label


def _error_label() -> QLabel:
    label = QLabel()
    label.setObjectName("fieldError")
    label.setWordWrap(True)
    label.hide()
    return label


def _column(*widgets: QWidget) -> QWidget:
    holder = QWidget()
    layout = QVBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    for widget in widgets:
        layout.addWidget(widget)
    return holder


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, controller: RecordingController, parent=None) -> None:
        super().__init__(parent)
        self._original = settings
        self._controller = controller
        self.setWindowTitle(tr("settings.title"))
        self.setModal(True)
        self.setMinimumWidth(640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general(), tr("settings.tab.general"))
        self.tabs.addTab(self._build_recording(), tr("settings.tab.recording"))
        self.tabs.addTab(self._build_system(), tr("settings.tab.system"))
        layout.addWidget(self.tabs)

        self.buttons = QDialogButtonBox()
        self.save_button = self.buttons.addButton(
            tr("settings.save"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.save_button.setObjectName("primary")
        self.save_button.setDefault(True)
        self.buttons.addButton(tr("settings.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        self.defaults_button = self.buttons.addButton(
            tr("settings.defaults"), QDialogButtonBox.ButtonRole.ResetRole
        )
        self.defaults_button.setToolTip(tr("settings.defaults.tip"))
        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self.reject)
        self.defaults_button.clicked.connect(self._restore_defaults)
        layout.addWidget(self.buttons)

        self._load(settings)
        self._validate()

    # -- pages -----------------------------------------------------------

    def _form(self) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        return page, form

    def _build_general(self) -> QWidget:
        page, form = self._form()

        self.language_combo = QComboBox()
        for code, name in available_languages().items():
            self.language_combo.addItem(name, code)
        form.addRow(
            tr("settings.ui_language"),
            _column(self.language_combo, _hint(tr("settings.ui_language.hint"))),
        )

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText(str(paths.default_save_dir()))
        self.folder_browse = QPushButton(tr("settings.browse"))
        self.folder_browse.clicked.connect(self._browse_folder)
        self.folder_error = _error_label()
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.folder_edit, 1)
        row_layout.addWidget(self.folder_browse)
        form.addRow(
            tr("settings.folder"),
            _column(row, self.folder_error, _hint(tr("settings.folder.hint"))),
        )

        self.format_combo = QComboBox()
        for format_id, exporter in EXPORTERS.items():
            self.format_combo.addItem(exporter.label, format_id)
        self.format_combo.currentIndexChanged.connect(self._validate)
        form.addRow(tr("settings.format"), self.format_combo)

        self.template_edit = QLineEdit()
        self.template_edit.textChanged.connect(self._validate)
        self.template_error = _error_label()
        self.template_preview = QLabel()
        self.template_preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        placeholders = "  ".join("{" + name + "}" for name in PLACEHOLDERS)
        form.addRow(
            tr("settings.template"),
            _column(
                self.template_edit,
                self.template_error,
                self.template_preview,
                _hint(tr("settings.template.hint", placeholders=placeholders)),
            ),
        )

        self.timestamps_check = QCheckBox(tr("settings.timestamps"))
        self.open_after_check = QCheckBox(tr("settings.open_after_save"))
        form.addRow(tr("settings.documents"), _column(self.timestamps_check, self.open_after_check))
        return page

    def _spin(self, key: str, suffix: str, step: int) -> QSpinBox:
        low, high = LIMITS[key]
        spin = QSpinBox()
        spin.setRange(int(low), int(high))
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        return spin

    def _build_recording(self) -> QWidget:
        page, form = self._form()

        self.mic_combo = QComboBox()
        self.mic_combo.addItem(tr("main.microphone.default"), "")
        try:
            for device in list_input_devices():
                self.mic_combo.addItem(device.name, device.name)
        except AudioError:
            pass
        form.addRow(tr("settings.microphone"), self.mic_combo)

        ms = " " + tr("unit.ms")
        self.silence_spin = self._spin("silence_ms", ms, 50)
        form.addRow(
            tr("settings.silence"),
            _column(self.silence_spin, _hint(tr("settings.silence.hint"))),
        )

        low, high = LIMITS["vad_threshold"]
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(low, high)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setDecimals(2)
        form.addRow(
            tr("settings.threshold"),
            _column(self.threshold_spin, _hint(tr("settings.threshold.hint"))),
        )

        self.min_speech_spin = self._spin("min_speech_ms", ms, 50)
        form.addRow(
            tr("settings.min_speech"),
            _column(self.min_speech_spin, _hint(tr("settings.min_speech.hint"))),
        )

        self.max_segment_spin = self._spin("max_segment_s", " " + tr("unit.s"), 1)
        form.addRow(
            tr("settings.max_segment"),
            _column(self.max_segment_spin, _hint(tr("settings.max_segment.hint"))),
        )

        self.pre_roll_spin = self._spin("pre_roll_ms", ms, 50)
        self.post_roll_spin = self._spin("post_roll_ms", ms, 50)
        form.addRow(
            tr("settings.pre_roll"),
            _column(self.pre_roll_spin, _hint(tr("settings.pre_roll.hint"))),
        )
        form.addRow(
            tr("settings.post_roll"),
            _column(self.post_roll_spin, _hint(tr("settings.post_roll.hint"))),
        )

        self.retain_check = QCheckBox(tr("settings.retain_audio"))
        audio_button = QPushButton(tr("settings.open_audio_folder"))
        audio_button.clicked.connect(lambda: self._open_directory(paths.audio_dir()))
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.retain_check, 1)
        row_layout.addWidget(audio_button)
        form.addRow(
            tr("settings.debugging"),
            _column(row, _hint(tr("settings.retain_audio.hint"))),
        )
        return page

    def _build_system(self) -> QWidget:
        from app.main_window import device_text

        page, form = self._form()
        transcriber = self._controller.transcriber

        self.device_combo = QComboBox()
        for code in ("auto", "cuda", "cpu"):
            self.device_combo.addItem(tr(f"settings.device.{code}"), code)
        form.addRow(
            tr("settings.device"),
            _column(self.device_combo, _hint(tr("settings.device.hint"))),
        )

        info = transcriber.device_info
        if info is not None:
            in_use = device_text(info)
            if info.fallback_reason and has(f"device.reason.{info.fallback_reason}"):
                in_use += "\n" + tr(f"device.reason.{info.fallback_reason}")
        else:
            in_use = tr(f"model.{self._controller.model_state}")
        in_use_label = QLabel(in_use)
        in_use_label.setWordWrap(True)
        form.addRow(tr("settings.device.in_use"), in_use_label)

        model_path = transcriber.model_path or transcriber.cached_model_path()
        self._model_path = model_path
        if model_path is not None:
            megabytes = _directory_bytes(Path(model_path), follow_links=True) / 1_000_000
            status = tr("settings.model.cached", model=MODEL_NAME, megabytes=f"{megabytes:.0f}")
        else:
            status = tr("settings.model.missing", model=MODEL_NAME)
        status_label = QLabel(status)
        status_label.setWordWrap(True)
        location = QLabel(str(model_path) if model_path else "—")
        location.setWordWrap(True)
        location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        model_button = QPushButton(tr("settings.model.open"))
        model_button.setEnabled(model_path is not None)
        model_button.clicked.connect(lambda: self._open_directory(self._model_path))
        form.addRow(tr("settings.model"), status_label)
        form.addRow(tr("settings.model.location"), _column(location, model_button))

        log_button = QPushButton(tr("settings.logs.open"))
        log_button.clicked.connect(lambda: self._open_directory(paths.log_dir()))
        form.addRow(tr("settings.logs"), _column(log_button, _hint(tr("settings.logs.hint"))))

        form.addRow(tr("settings.privacy"), _hint(tr("settings.privacy.text")))
        for button in (model_button, log_button):
            button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        return page

    # -- behaviour -------------------------------------------------------

    def _open_directory(self, directory: Path | None) -> None:
        if directory is None:
            return
        directory = Path(directory)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def _load(self, settings: Settings) -> None:
        def select(combo: QComboBox, value) -> None:
            combo.setCurrentIndex(max(combo.findData(value), 0))

        select(self.language_combo, settings.ui_language)
        self.folder_edit.setText(str(settings.resolved_save_directory()))
        select(self.format_combo, settings.export_format)
        self.template_edit.setText(settings.filename_template)
        self.timestamps_check.setChecked(settings.include_timestamps)
        self.open_after_check.setChecked(settings.open_after_save)
        select(self.mic_combo, settings.microphone)
        self.silence_spin.setValue(settings.silence_ms)
        self.threshold_spin.setValue(settings.vad_threshold)
        self.min_speech_spin.setValue(settings.min_speech_ms)
        self.max_segment_spin.setValue(settings.max_segment_s)
        self.pre_roll_spin.setValue(settings.pre_roll_ms)
        self.post_roll_spin.setValue(settings.post_roll_ms)
        self.retain_check.setChecked(settings.retain_audio)
        select(self.device_combo, settings.device_preference)

    def _restore_defaults(self) -> None:
        # Fills the form only. The interface language is kept, because
        # switching it back would be surprising.
        self._load(replace(Settings(), ui_language=self.language_combo.currentData()))
        self._validate()

    def _browse_folder(self) -> None:
        start = Path(self.folder_edit.text().strip() or paths.default_save_dir())
        while not start.exists() and start != start.parent:
            start = start.parent
        chosen = QFileDialog.getExistingDirectory(self, tr("main.folder.dialog"), str(start))
        if chosen:
            self.folder_edit.setText(chosen)
            self._set_error(self.folder_edit, self.folder_error, "")

    def _set_error(self, field: QLineEdit, label: QLabel, text: str) -> None:
        label.setText(text)
        label.setVisible(bool(text))
        field.setProperty("invalid", "true" if text else "false")
        refresh_style(field)

    def _validate(self) -> None:
        template = self.template_edit.text()
        errors = template_errors(template)
        if errors:
            code = errors[0]
            if code.startswith("unknown:"):
                message = tr("settings.template.error.unknown", name="{" + code[8:] + "}")
            else:
                message = tr(f"settings.template.error.{code}")
            self.template_preview.setText("")
        else:
            message = ""
            stem = render_filename(template, self._controller.session)
            extension = EXPORTERS[self.format_combo.currentData()].extension
            self.template_preview.setText(tr("settings.template.preview", name=f"{stem}.{extension}"))
        self._set_error(self.template_edit, self.template_error, message)
        self.save_button.setEnabled(not errors)

    def _accept(self) -> None:
        if template_errors(self.template_edit.text()):
            self.tabs.setCurrentIndex(0)
            return
        text = self.folder_edit.text().strip()
        directory = Path(text).expanduser() if text else paths.default_save_dir()
        if not directory.is_absolute():
            self.tabs.setCurrentIndex(0)
            self._set_error(self.folder_edit, self.folder_error, tr("settings.folder.error.relative"))
            return
        create = False
        if not directory.exists():
            answer = QMessageBox.question(
                self,
                tr("settings.folder.create.title"),
                tr("settings.folder.create.text", path=str(directory)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.tabs.setCurrentIndex(0)
                self.folder_edit.setFocus()
                return
            create = True
        try:
            check_directory(directory, create=create)
        except ExportError as exc:
            from app.main_window import error_text

            self.tabs.setCurrentIndex(0)
            self._set_error(self.folder_edit, self.folder_error, error_text(exc.code, exc.detail))
            self.folder_edit.setFocus()
            return
        self._directory = directory
        self.accept()

    def result_settings(self) -> Settings:
        directory = getattr(self, "_directory", None)
        default = paths.default_save_dir()
        return replace(
            self._original,
            ui_language=self.language_combo.currentData(),
            # The default folder is stored as "" so it keeps following the
            # user's Documents folder if that is moved.
            save_directory="" if directory is None or directory == default else str(directory),
            export_format=self.format_combo.currentData(),
            filename_template=self.template_edit.text().strip(),
            include_timestamps=self.timestamps_check.isChecked(),
            open_after_save=self.open_after_check.isChecked(),
            microphone=self.mic_combo.currentData() or "",
            silence_ms=self.silence_spin.value(),
            vad_threshold=round(self.threshold_spin.value(), 2),
            min_speech_ms=self.min_speech_spin.value(),
            max_segment_s=self.max_segment_spin.value(),
            pre_roll_ms=self.pre_roll_spin.value(),
            post_roll_ms=self.post_roll_spin.value(),
            retain_audio=self.retain_check.isChecked(),
            device_preference=self.device_combo.currentData(),
        ).normalized()
