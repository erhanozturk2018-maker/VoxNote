"""Help window: frequently asked questions and information about the
application."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app import APP_NAME, APP_VERSION, paths
from app.i18n import has, tr
from app.icons import set_button_icon
from app.resources import assets_dir
from app.theme import tokens

PROJECT_URL = "https://github.com/erhanozturk2018-maker/VoxNote"


# (key sequence, translation key) of every keyboard shortcut, in the order
# they are listed in the introduction.
SHORTCUTS = (
    ("Ctrl+R", "shortcut.start"),
    ("Ctrl+E", "shortcut.stop"),
    ("Ctrl+Alt+R", "shortcut.global"),
    ("Ctrl+Shift+C", "shortcut.copy"),
    ("Ctrl+Shift+S", "shortcut.save_as"),
    ("Ctrl+O", "shortcut.open_folder"),
    ("Ctrl+T", "shortcut.theme"),
    ("Ctrl+,", "shortcut.settings"),
    ("F1", "shortcut.help"),
)


def tutorial_steps() -> list[tuple[str, str]]:
    """Title and text of each step of the introduction."""
    steps = []
    number = 1
    while has(f"tutorial.{number}.title"):
        steps.append((tr(f"tutorial.{number}.title"), tr(f"tutorial.{number}.text")))
        number += 1
    return steps


def faq_entries() -> list[tuple[str, str]]:
    """Question and answer pairs in the current language."""
    entries = []
    number = 1
    while has(f"faq.{number}.q"):
        entries.append((tr(f"faq.{number}.q"), tr(f"faq.{number}.a")))
        number += 1
    return entries


class HelpDialog(QDialog):
    def __init__(self, parent=None, start_tab: int = 0) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("help.title"))
        self.setModal(True)
        self.resize(620, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tutorial(), tr("help.tab.start"))
        self.tabs.addTab(self._build_faq(), tr("help.tab.faq"))
        self.tabs.addTab(self._build_about(), tr("help.tab.about"))
        self.tabs.setCurrentIndex(max(0, min(start_tab, self.tabs.count() - 1)))
        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox()
        close = buttons.addButton(tr("help.close"), QDialogButtonBox.ButtonRole.RejectRole)
        close.setDefault(True)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_tutorial(self) -> QWidget:
        colors = tokens()
        parts = [
            f'<p style="margin:12px 0 6px 0; color:{colors["muted"]};">'
            f'{html.escape(tr("tutorial.intro"))}</p>'
        ]
        for number, (title, text) in enumerate(tutorial_steps(), start=1):
            parts.append(
                '<table cellspacing="0" cellpadding="0" style="margin-top:12px;"><tr>'
                f'<td width="34" valign="top" style="font-size:15pt; font-weight:600; '
                f'color:{colors["accent"]};">{number}</td>'
                f'<td><span style="font-weight:600; color:{colors["text"]};">'
                f"{html.escape(title)}</span><br>"
                f'<span style="color:{colors["muted"]};">{html.escape(text)}</span></td>'
                "</tr></table>"
            )
        parts.append(
            f'<p style="margin:20px 0 6px 0; font-weight:600; color:{colors["text"]};">'
            f'{html.escape(tr("tutorial.shortcuts"))}</p>'
            '<table cellspacing="0" cellpadding="3">'
        )
        for keys, key in SHORTCUTS:
            parts.append(
                f'<tr><td width="130" style="font-family:Consolas, monospace; '
                f'color:{colors["accent"]};">{html.escape(keys)}</td>'
                f'<td style="color:{colors["muted"]};">{html.escape(tr(key))}</td></tr>'
            )
        parts.append("</table>")
        self.tutorial_view = QTextBrowser()
        self.tutorial_view.setObjectName("help")
        self.tutorial_view.setOpenLinks(False)
        self.tutorial_view.setHtml("".join(parts))
        self.tutorial_view.setAccessibleName(tr("help.tab.start"))
        return self.tutorial_view

    def _build_faq(self) -> QWidget:
        colors = tokens()
        parts = []
        for question, answer in faq_entries():
            parts.append(
                f'<p style="margin:14px 0 4px 0; font-weight:600; color:{colors["text"]};">'
                f"{html.escape(question)}</p>"
                f'<p style="margin:0; color:{colors["muted"]};">{html.escape(answer)}</p>'
            )
        self.faq_view = QTextBrowser()
        self.faq_view.setObjectName("help")
        self.faq_view.setOpenLinks(False)
        self.faq_view.setHtml("".join(parts))
        self.faq_view.setAccessibleName(tr("help.tab.faq"))
        return self.faq_view

    def _build_about(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(14)
        logo = QLabel()
        image = QPixmap(str(assets_dir() / "voxnote.png"))
        if not image.isNull():
            logo.setPixmap(
                image.scaled(
                    128,
                    128,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setFixedSize(64, 64)
            logo.setScaledContents(True)
        names = QVBoxLayout()
        names.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        version = QLabel(tr("app.version", version=APP_VERSION))
        version.setObjectName("muted")
        names.addWidget(title)
        names.addWidget(version)
        header.addWidget(logo)
        header.addLayout(names)
        header.addStretch(1)
        layout.addLayout(header)

        def paragraph(key: str, object_name: str = "") -> QLabel:
            label = QLabel(tr(key))
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if object_name:
                label.setObjectName(object_name)
            return label

        layout.addWidget(paragraph("about.description"))
        layout.addWidget(paragraph("about.privacy.title", "sectionTitle"))
        layout.addWidget(paragraph("about.privacy.text"))
        layout.addWidget(paragraph("about.credits.title", "sectionTitle"))
        layout.addWidget(paragraph("about.credits.text"))
        layout.addWidget(paragraph("about.license", "hint"))
        layout.addStretch(1)

        row = QHBoxLayout()
        website = QPushButton(tr("about.website"))
        website.setToolTip(PROJECT_URL)
        website.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
        logs = QPushButton(tr("settings.logs.open"))
        logs.clicked.connect(self._open_logs)
        set_button_icon(website, "info")
        set_button_icon(logs, "folder-open")
        for button in (website, logs):
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        return page

    def _open_logs(self) -> None:
        directory = paths.log_dir()
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))
