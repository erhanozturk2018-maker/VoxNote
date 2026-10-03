"""Settings dialog.

Nothing is applied until the user confirms with *Save*; *Cancel* leaves
every setting untouched, and *Restore defaults* only fills the form, so it
can still be cancelled.

The microphone is chosen in the main window and is therefore not repeated
here.
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import MODELS, paths
from app.export_manager import ExportError, check_directory
from app.exporters import EXPORTERS
from app.filename_template import PLACEHOLDERS, render_filename, template_errors
from app.i18n import available_languages, has, tr
from app.icons import set_button_icon
from app.language_names import LANGUAGE_NAMES, language_list
from app.recording_controller import RecordingController
from app.settings_manager import LIMITS, THEMES, Settings
from app.theme import polish_combos, refresh_style
from app.workers import _directory_bytes

# Shown first in the language chooser; the rest follows alphabetically.
_COMMON_LANGUAGES = ("en", "tr", "de", "fr", "es", "it", "ru", "pt", "ar", "zh", "ja")


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
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return holder


def _row(*widgets: QWidget, stretch_first: bool = True) -> QWidget:
    holder = QWidget()
    layout = QHBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for index, widget in enumerate(widgets):
        layout.addWidget(widget, 1 if stretch_first and index == 0 else 0)
    if not stretch_first:
        layout.addStretch(1)
    return holder


class LanguageChooser(QDialog):
    """Lets the user tick the languages they speak."""

    def __init__(self, selected: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.languages.title"))
        self.setModal(True)
        self.resize(380, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(_hint(tr("dialog.languages.text")))

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(tr("dialog.languages.filter"))
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_edit)

        self.list = QListWidget()
        codes = [code for code in _COMMON_LANGUAGES if code in LANGUAGE_NAMES]
        codes += sorted(
            (code for code in LANGUAGE_NAMES if code not in codes), key=LANGUAGE_NAMES.get
        )
        for code in codes:
            item = QListWidgetItem(LANGUAGE_NAMES[code])
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if code in selected else Qt.CheckState.Unchecked
            )
            self.list.addItem(item)
        layout.addWidget(self.list, 1)

        buttons = QDialogButtonBox()
        ok = buttons.addButton(tr("dialog.ok"), QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setObjectName("primary")
        ok.setDefault(True)
        buttons.addButton(tr("settings.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        clear = buttons.addButton(tr("dialog.languages.clear"), QDialogButtonBox.ButtonRole.ResetRole)
        clear.clicked.connect(self._clear)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(bool(needle) and needle not in item.text().lower())

    def _clear(self) -> None:
        for index in range(self.list.count()):
            self.list.item(index).setCheckState(Qt.CheckState.Unchecked)

    def selected(self) -> list[str]:
        return [
            self.list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.list.count())
            if self.list.item(index).checkState() == Qt.CheckState.Checked
        ]


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, controller: RecordingController, parent=None) -> None:
        super().__init__(parent)
        self._original = settings
        self._controller = controller
        self._spoken: list[str] = list(settings.spoken_languages)
        self._directory: Path | None = None
        self._ready = False
        self.setWindowTitle(tr("settings.title"))
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general(), tr("settings.tab.general"))
        self.tabs.addTab(self._build_recognition(), tr("settings.tab.recognition"))
        self.tabs.addTab(self._build_recording(), tr("settings.tab.recording"))
        self.tabs.currentChanged.connect(self._fit_to_tab)
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

        polish_combos(self)
        self._load(settings)
        self._ready = True
        self._validate()
        self.setFixedWidth(640)
        self._fit_to_tab()

    def _fit_to_tab(self, _index: int = 0) -> None:
        """Make the dialog exactly as tall as the visible tab needs.

        A tab widget is normally as tall as its tallest page, which leaves
        short pages with a large empty area.
        """
        if not self._ready:
            return
        form = self.tabs.currentWidget().layout()
        form.invalidate()
        margins = self.layout().contentsMargins()
        page_width = self.width() - margins.left() - margins.right() - 2
        if form.hasHeightForWidth():
            page_height = form.totalHeightForWidth(page_width)
        else:
            page_height = form.totalSizeHint().height()
        self.tabs.setFixedHeight(page_height + self.tabs.tabBar().sizeHint().height() + 4)
        self.layout().invalidate()
        self.setFixedHeight(self.layout().totalSizeHint().height())

    # -- pages -----------------------------------------------------------

    def _form(self) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(18, 18, 18, 18)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)
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

        self.theme_combo = QComboBox()
        for name in THEMES:
            self.theme_combo.addItem(tr(f"theme.{name}"), name)
        form.addRow(tr("settings.theme"), self.theme_combo)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText(str(paths.default_save_dir()))
        self.folder_browse = QPushButton(tr("settings.browse"))
        set_button_icon(self.folder_browse, "folder")
        self.folder_browse.clicked.connect(self._browse_folder)
        self.folder_error = _error_label()
        form.addRow(
            tr("settings.folder"),
            _column(
                _row(self.folder_edit, self.folder_browse),
                self.folder_error,
                _hint(tr("settings.folder.hint")),
            ),
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

    def _build_recognition(self) -> QWidget:
        from app.main_window import device_text

        page, form = self._form()
        transcriber = self._controller.transcriber

        self.model_combo = QComboBox()
        for name in MODELS:
            self.model_combo.addItem(tr(f"settings.model.option.{name}"), name)
        self.model_status = _hint("")
        self.model_combo.currentIndexChanged.connect(self._update_model_status)
        form.addRow(
            tr("settings.model"),
            _column(self.model_combo, self.model_status, _hint(tr("settings.model.hint"))),
        )

        self.spoken_label = QLabel()
        self.spoken_label.setWordWrap(True)
        self.spoken_button = QPushButton(tr("settings.spoken.choose"))
        set_button_icon(self.spoken_button, "languages")
        self.spoken_button.clicked.connect(self._choose_languages)
        form.addRow(
            tr("settings.spoken"),
            _column(
                _row(self.spoken_label, self.spoken_button),
                _hint(tr("settings.spoken.hint")),
            ),
        )

        self.vocabulary_edit = QLineEdit()
        self.vocabulary_edit.setPlaceholderText(tr("settings.vocabulary.placeholder"))
        self.vocabulary_edit.setMaxLength(500)
        form.addRow(
            tr("settings.vocabulary"),
            _column(self.vocabulary_edit, _hint(tr("settings.vocabulary.hint"))),
        )

        self.device_combo = QComboBox()
        for code in ("auto", "cuda", "cpu"):
            self.device_combo.addItem(tr(f"settings.device.{code}"), code)
        info = transcriber.device_info
        if info is not None:
            in_use = tr("settings.device.in_use", device=device_text(info))
            if info.fallback_reason and has(f"device.reason.{info.fallback_reason}"):
                in_use += " " + tr(f"device.reason.{info.fallback_reason}")
        else:
            in_use = tr(f"model.{self._controller.model_state}")
        form.addRow(tr("settings.device"), _column(self.device_combo, _hint(in_use)))

        model_button = QPushButton(tr("settings.model.open"))
        set_button_icon(model_button, "folder-open")
        model_button.clicked.connect(self._open_model_folder)
        log_button = QPushButton(tr("settings.logs.open"))
        set_button_icon(log_button, "folder-open")
        log_button.clicked.connect(lambda: self._open_directory(paths.log_dir()))
        form.addRow(
            tr("settings.folders"),
            _column(
                _row(model_button, log_button, stretch_first=False),
                _hint(tr("settings.logs.hint")),
            ),
        )
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
        self._recording_form = form
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

        self.retain_check = QCheckBox(tr("settings.retain_audio"))
        audio_button = QPushButton(tr("settings.open_audio_folder"))
        set_button_icon(audio_button, "folder-open")
        audio_button.clicked.connect(lambda: self._open_directory(paths.audio_dir()))
        form.addRow(
            tr("settings.debugging"),
            _column(
                _row(self.retain_check, audio_button),
                _hint(tr("settings.retain_audio.hint")),
            ),
        )

        # Rarely needed options stay out of the way until asked for.
        self.advanced_toggle = QPushButton(tr("settings.advanced"))
        self.advanced_toggle.setObjectName("flat")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        form.addRow(_row(self.advanced_toggle, stretch_first=False))

        self.min_speech_spin = self._spin("min_speech_ms", ms, 50)
        self.max_segment_spin = self._spin("max_segment_s", " " + tr("unit.s"), 1)
        self.pre_roll_spin = self._spin("pre_roll_ms", ms, 50)
        self.post_roll_spin = self._spin("post_roll_ms", ms, 50)
        self._advanced_rows = []
        for label, spin, hint in (
            ("settings.min_speech", self.min_speech_spin, "settings.min_speech.hint"),
            ("settings.max_segment", self.max_segment_spin, "settings.max_segment.hint"),
            ("settings.pre_roll", self.pre_roll_spin, "settings.pre_roll.hint"),
            ("settings.post_roll", self.post_roll_spin, "settings.post_roll.hint"),
        ):
            field = _column(spin, _hint(tr(hint)))
            form.addRow(tr(label), field)
            self._advanced_rows.append(field)
        self._toggle_advanced(False)
        return page

    # -- behaviour -------------------------------------------------------

    def _toggle_advanced(self, shown: bool) -> None:
        set_button_icon(self.advanced_toggle, "chevron-down" if shown else "chevron-right")
        for field in self._advanced_rows:
            self._recording_form.setRowVisible(field, shown)
        self._fit_to_tab()

    def _update_model_status(self) -> None:
        name = self.model_combo.currentData()
        transcriber = self._controller.transcriber
        if name == transcriber.model_name:
            path = transcriber.model_path or transcriber.cached_model_path()
        else:
            from app.transcriber import Transcriber

            path = Transcriber(name).cached_model_path()
        if path is not None:
            megabytes = _directory_bytes(Path(path), follow_links=True) / 1_000_000
            text = tr("settings.model.status.cached", megabytes=f"{megabytes:.0f}")
        else:
            text = tr("settings.model.status.missing", megabytes=str(MODELS[name]))
        self.model_status.setText(text)

    def _open_model_folder(self) -> None:
        transcriber = self._controller.transcriber
        path = transcriber.model_path or transcriber.cached_model_path()
        if path is None:
            from huggingface_hub.constants import HF_HUB_CACHE

            path = Path(HF_HUB_CACHE)
        self._open_directory(Path(path))

    def _choose_languages(self) -> None:
        dialog = LanguageChooser(self._spoken, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._spoken = dialog.selected()
            self._update_spoken_label()
            self._fit_to_tab()

    def _update_spoken_label(self) -> None:
        self.spoken_label.setText(language_list(self._spoken) or tr("settings.spoken.all"))

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
        select(self.theme_combo, settings.theme)
        self.folder_edit.setText(str(settings.resolved_save_directory()))
        select(self.format_combo, settings.export_format)
        self.template_edit.setText(settings.filename_template)
        self.timestamps_check.setChecked(settings.include_timestamps)
        self.open_after_check.setChecked(settings.open_after_save)
        select(self.model_combo, settings.model)
        self._spoken = list(settings.spoken_languages)
        self._update_spoken_label()
        self.vocabulary_edit.setText(settings.vocabulary)
        select(self.device_combo, settings.device_preference)
        self.silence_spin.setValue(settings.silence_ms)
        self.threshold_spin.setValue(settings.vad_threshold)
        self.min_speech_spin.setValue(settings.min_speech_ms)
        self.max_segment_spin.setValue(settings.max_segment_s)
        self.pre_roll_spin.setValue(settings.pre_roll_ms)
        self.post_roll_spin.setValue(settings.post_roll_ms)
        self.retain_check.setChecked(settings.retain_audio)
        self._update_model_status()

    def _restore_defaults(self) -> None:
        # Fills the form only. The interface language is kept, because
        # switching it back would be surprising.
        self._load(
            replace(
                Settings(),
                ui_language=self.language_combo.currentData(),
                tutorial_seen=self._original.tutorial_seen,
            )
        )
        self._validate()
        self._fit_to_tab()

    def _browse_folder(self) -> None:
        start = Path(self.folder_edit.text().strip() or paths.default_save_dir())
        while not start.exists() and start != start.parent:
            start = start.parent
        chosen = QFileDialog.getExistingDirectory(self, tr("main.folder.dialog"), str(start))
        if chosen:
            self.folder_edit.setText(chosen)
            self._set_error(self.folder_edit, self.folder_error, "")

    def _set_error(self, field: QLineEdit, label: QLabel, text: str) -> None:
        changed = label.isHidden() == bool(text)
        label.setText(text)
        label.setVisible(bool(text))
        field.setProperty("invalid", "true" if text else "false")
        refresh_style(field)
        if changed:
            self._fit_to_tab()

    def _validate(self) -> None:
        if not self._ready:
            return
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
        directory = self._directory
        default = paths.default_save_dir()
        return replace(
            self._original,
            ui_language=self.language_combo.currentData(),
            theme=self.theme_combo.currentData(),
            # The default folder is stored as "" so it keeps following the
            # user's Documents folder if that is moved.
            save_directory="" if directory is None or directory == default else str(directory),
            export_format=self.format_combo.currentData(),
            filename_template=self.template_edit.text().strip(),
            include_timestamps=self.timestamps_check.isChecked(),
            open_after_save=self.open_after_check.isChecked(),
            model=self.model_combo.currentData(),
            spoken_languages=list(self._spoken),
            vocabulary=self.vocabulary_edit.text(),
            device_preference=self.device_combo.currentData(),
            silence_ms=self.silence_spin.value(),
            vad_threshold=round(self.threshold_spin.value(), 2),
            min_speech_ms=self.min_speech_spin.value(),
            max_segment_s=self.max_segment_spin.value(),
            pre_roll_ms=self.pre_roll_spin.value(),
            post_roll_ms=self.post_roll_spin.value(),
            retain_audio=self.retain_check.isChecked(),
        ).normalized()
