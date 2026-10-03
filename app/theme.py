"""Visual style shared by every window.

One small set of colour tokens is used for both the light and the dark
variant, so all controls stay visually consistent. The variant follows the
operating system setting.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QListView

from app.resources import assets_dir

LIGHT = {
    "window": "#f4f5f7",
    "card": "#ffffff",
    "border": "#d9dce1",
    "text": "#1c1f24",
    "muted": "#5b6470",
    "accent": "#6d3fd0",
    "accent_hover": "#5a31b3",
    "accent_text": "#ffffff",
    "record": "#c62828",
    "record_hover": "#a81f1f",
    "record_text": "#ffffff",
    "success": "#17703a",
    "success_bg": "#e6f4ea",
    "warning": "#8a5a00",
    "warning_bg": "#fff4d6",
    "error": "#b3261e",
    "error_bg": "#fdecea",
    "info_bg": "#f2edfc",
    "field": "#ffffff",
    "disabled_bg": "#e6e8ec",
    "disabled_text": "#8b929c",
}

DARK = {
    "window": "#1b1d21",
    "card": "#24272c",
    "border": "#3a3f47",
    "text": "#e8eaed",
    "muted": "#a2a9b3",
    "accent": "#a98bf5",
    "accent_hover": "#bda6f8",
    "accent_text": "#17121f",
    "record": "#ef5350",
    "record_hover": "#f27573",
    "record_text": "#1b1d21",
    "success": "#6fcf8b",
    "success_bg": "#1e3326",
    "warning": "#f0c060",
    "warning_bg": "#3a3018",
    "error": "#f28b82",
    "error_bg": "#301c1a",
    "info_bg": "#262036",
    "field": "#1f2226",
    "disabled_bg": "#2c3036",
    "disabled_text": "#6f7782",
}

_STYLE = """
QWidget {{ color: {text}; font-size: 10pt; }}
QMainWindow, QDialog {{ background: {window}; }}
QLabel#title {{ font-size: 18pt; font-weight: 600; }}
QLabel#version, QLabel#muted, QLabel#hint {{ color: {muted}; }}
QLabel#hint {{ font-size: 9pt; }}
QLabel#sectionTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#timer {{ font-size: 22pt; font-weight: 600; font-family: "Cascadia Mono", "Consolas", monospace; }}
QLabel#fieldError {{ color: {error}; font-size: 9pt; }}
QFrame#card {{ background: {card}; border: 1px solid {border}; border-radius: 8px; }}

QLabel#statusPill {{ border-radius: 11px; padding: 3px 12px; font-weight: 600;
    background: {disabled_bg}; color: {muted}; }}
QLabel#statusPill[state="ready"] {{ background: {info_bg}; color: {accent}; }}
QLabel#statusPill[state="recording"] {{ background: {error_bg}; color: {record}; }}
QLabel#statusPill[state="processing"], QLabel#statusPill[state="saving"] {{
    background: {warning_bg}; color: {warning}; }}
QLabel#statusPill[state="completed"] {{ background: {success_bg}; color: {success}; }}
QLabel#statusPill[state="error"] {{ background: {error_bg}; color: {error}; }}

QFrame#banner {{ border-radius: 6px; border: 1px solid {border}; background: {info_bg}; }}
QFrame#banner[kind="success"] {{ background: {success_bg}; border-color: {success}; }}
QFrame#banner[kind="warning"] {{ background: {warning_bg}; border-color: {warning}; }}
QFrame#banner[kind="error"] {{ background: {error_bg}; border-color: {error}; }}
QFrame#banner QLabel {{ background: transparent; }}

QPushButton {{ background: {card}; border: 1px solid {border}; border-radius: 6px;
    padding: 6px 14px; min-height: 20px; }}
QPushButton:hover {{ border-color: {accent}; }}
QPushButton:pressed {{ background: {info_bg}; }}
QPushButton:focus {{ border: 2px solid {accent}; padding: 5px 13px; }}
QPushButton:disabled {{ background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}
QPushButton#primary {{ background: {accent}; color: {accent_text}; border-color: {accent};
    font-weight: 600; padding: 8px 18px; }}
QPushButton#primary:hover {{ background: {accent_hover}; }}
QPushButton#record {{ background: {accent}; color: {accent_text}; border-color: {accent};
    font-weight: 600; padding: 8px 18px; }}
QPushButton#record:hover {{ background: {accent_hover}; }}
QPushButton#stop {{ background: {record}; color: {record_text}; border-color: {record};
    font-weight: 600; padding: 8px 18px; }}
QPushButton#stop:hover {{ background: {record_hover}; }}
QPushButton#primary:focus, QPushButton#record:focus, QPushButton#stop:focus {{
    border: 2px solid {text}; padding: 7px 17px; }}
QPushButton#primary:disabled, QPushButton#record:disabled, QPushButton#stop:disabled {{
    background: {disabled_bg}; color: {disabled_text}; border-color: {border}; }}
QPushButton#flat {{ background: transparent; border: 1px solid transparent; padding: 5px 8px; }}
QPushButton#flat:hover {{ background: {info_bg}; border-color: {border}; }}
QPushButton#flat:focus {{ border: 2px solid {accent}; padding: 4px 7px; }}
QPushButton#flat:disabled {{ background: transparent; border-color: transparent; }}

QFrame#popupPanel {{ background: {card}; border: 1px solid {border}; border-radius: 8px; }}
QFrame#popupPanel QLabel {{ background: transparent; }}
QRadioButton {{ spacing: 8px; }}

QListWidget, QTextBrowser#help {{ background: {field}; border: 1px solid {border};
    border-radius: 6px; padding: 6px; }}
QTextBrowser#help {{ padding: 4px 14px 14px 14px; font-size: 10.5pt; }}
QListWidget::item {{ padding: 4px 2px; }}
QListWidget::item:selected {{ background: {info_bg}; color: {text}; }}

QComboBox, QLineEdit {{ background: {field};
    border: 1px solid {border}; border-radius: 6px; padding: 5px 8px; min-height: 20px; }}
QComboBox:focus, QLineEdit:focus {{ border: 2px solid {accent}; padding: 4px 7px; }}
QComboBox:disabled, QLineEdit:disabled {{ background: {disabled_bg}; color: {disabled_text}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: url("{arrow}"); width: 12px; height: 12px; }}
QSpinBox, QDoubleSpinBox {{ min-height: 26px; padding-left: 4px; }}
QComboBox {{ combobox-popup: 0; }}
QComboBox QAbstractItemView {{ background: {field}; border: 1px solid {border};
    border-radius: 6px; padding: 4px; outline: none;
    selection-background-color: {accent}; selection-color: {accent_text}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 2px 10px; border-radius: 4px; }}
QComboBox QAbstractItemView::item:hover {{ background: {info_bg}; color: {text}; }}
QComboBox QAbstractItemView::item:selected {{ background: {accent}; color: {accent_text}; }}
QLineEdit[invalid="true"] {{ border: 2px solid {error}; padding: 4px 7px; }}

QTextEdit#transcript {{ background: {field}; border: 1px solid {border}; border-radius: 6px;
    padding: 8px; font-size: 11pt; }}
QProgressBar {{ background: {disabled_bg}; border: none; border-radius: 4px; max-height: 8px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 4px; }}
QProgressBar#level[speech="true"]::chunk {{ background: {success}; }}

QTabWidget::pane {{ border: 1px solid {border}; border-radius: 6px; background: {card}; top: -1px; }}
QTabBar::tab {{ padding: 7px 16px; border: 1px solid transparent; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px; color: {muted}; }}
QTabBar::tab:selected {{ background: {card}; border-color: {border}; color: {text}; font-weight: 600; }}
QTabBar::tab:focus {{ color: {accent}; }}
QToolTip {{ background: {card}; color: {text}; border: 1px solid {border}; padding: 4px; }}
QCheckBox {{ spacing: 8px; }}
"""


THEME_MODES = ("system", "light", "dark")
_mode = "system"


def set_mode(mode: str) -> None:
    """Choose the appearance: ``system``, ``light`` or ``dark``."""
    global _mode
    _mode = mode if mode in THEME_MODES else "system"


def mode() -> str:
    return _mode


def is_dark() -> bool:
    """Whether the dark variant applies.

    The mode chosen by the user decides; ``system`` follows the operating
    system. The ``VOXNOTE_THEME`` environment variable (``light`` or
    ``dark``) overrides both and is meant for testing.
    """
    forced = os.environ.get("VOXNOTE_THEME", "").lower()
    if forced in ("light", "dark"):
        return forced == "dark"
    if _mode in ("light", "dark"):
        return _mode == "dark"
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def tokens() -> dict[str, str]:
    return DARK if is_dark() else LIGHT


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    colors = tokens()
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["field"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["card"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["card"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["accent_text"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["card"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors["muted"]))
    app.setPalette(palette)
    arrow = assets_dir() / ("arrow-dark.png" if is_dark() else "arrow-light.png")
    app.setStyleSheet(_STYLE.format(arrow=arrow.as_posix(), **colors))


def polish_combos(parent) -> None:
    """Give every combo box below ``parent`` a roomy drop-down list.

    By default the Fusion style opens the list on top of the box, as tall as
    a couple of items and with scroll arrows. With a list view and the style
    sheet above, the list opens below the box, shows up to twelve items at a
    comfortable height and scrolls with a normal scroll bar beyond that.
    """
    for combo in parent.findChildren(QComboBox):
        view = QListView(combo)
        view.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        combo.setView(view)
        combo.setMaxVisibleItems(12)


def refresh_style(widget) -> None:
    """Re-evaluate the style sheet after a dynamic property changed."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
