"""Pop-up panel that lets the user decide what a saved document contains.

It can be opened at any time, including while a recording is running; the
choices apply to the next save. Nothing here changes the recognised words,
only their arrangement and the extras written around them.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)

from app.exporters.base import METADATA_FIELDS
from app.i18n import tr
from app.settings_manager import Settings


class ContentPanel(QFrame):
    """Check boxes for layout, headings and metadata of exported documents."""

    changed = Signal()

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("popupPanel")
        self._settings = settings
        self._loading = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        def heading(key: str) -> QLabel:
            label = QLabel(tr(key))
            label.setObjectName("sectionTitle")
            return label

        layout.addWidget(heading("content.layout"))
        self.lines_radio = QRadioButton(tr("content.layout.lines"))
        self.paragraph_radio = QRadioButton(tr("content.layout.paragraph"))
        group = QButtonGroup(self)
        group.addButton(self.lines_radio)
        group.addButton(self.paragraph_radio)
        layout.addWidget(self.lines_radio)
        layout.addWidget(self.paragraph_radio)

        self.timestamps_check = QCheckBox(tr("content.timestamps"))
        self.language_check = QCheckBox(tr("content.language_headings"))
        layout.addSpacing(4)
        layout.addWidget(self.timestamps_check)
        layout.addWidget(self.language_check)

        layout.addSpacing(8)
        layout.addWidget(heading("content.include"))
        self.headings_check = QCheckBox(tr("content.headings"))
        layout.addWidget(self.headings_check)
        self.metadata_checks: dict[str, QCheckBox] = {}
        for field in METADATA_FIELDS:
            check = QCheckBox(tr(f"content.metadata.{field}"))
            self.metadata_checks[field] = check
            layout.addWidget(check)

        hint = QLabel(tr("content.hint"))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        hint.setMaximumWidth(300)
        layout.addSpacing(6)
        layout.addWidget(hint)

        self.load()
        for widget in (
            self.lines_radio,
            self.paragraph_radio,
            self.timestamps_check,
            self.language_check,
            self.headings_check,
            *self.metadata_checks.values(),
        ):
            widget.toggled.connect(self._store)

    def load(self) -> None:
        """Show the current settings."""
        self._loading = True
        s = self._settings
        self.paragraph_radio.setChecked(s.document_layout == "paragraph")
        self.lines_radio.setChecked(s.document_layout != "paragraph")
        self.timestamps_check.setChecked(s.include_timestamps)
        self.language_check.setChecked(s.language_headings)
        self.headings_check.setChecked(s.document_headings)
        for field, check in self.metadata_checks.items():
            check.setChecked(field in s.document_metadata)
        self._loading = False
        self._update_enabled()

    def _update_enabled(self) -> None:
        # Timestamps and language headings only exist in the line layout.
        lines = self.lines_radio.isChecked()
        self.timestamps_check.setEnabled(lines)
        self.language_check.setEnabled(lines)

    def _store(self) -> None:
        if self._loading:
            return
        s = self._settings
        s.document_layout = "paragraph" if self.paragraph_radio.isChecked() else "lines"
        s.include_timestamps = self.timestamps_check.isChecked()
        s.language_headings = self.language_check.isChecked()
        s.document_headings = self.headings_check.isChecked()
        s.document_metadata = [
            field for field, check in self.metadata_checks.items() if check.isChecked()
        ]
        self._update_enabled()
        self.changed.emit()
