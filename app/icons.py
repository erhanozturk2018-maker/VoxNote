"""Interface icons.

Icons are small vector drawings defined here and rendered at runtime in the
colour of the current theme, so they stay sharp on high-resolution screens
and match both the light and the dark variant. No image files or icon fonts
are needed.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.theme import tokens

# Bodies of 24 x 24 SVG drawings. ``currentColor`` is replaced when rendering.
_SHAPES: dict[str, str] = {
    "microphone": (
        '<rect x="9" y="3" width="6" height="11" rx="3"/>'
        '<path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3"/><path d="M8.5 21h7"/>'
    ),
    "stop": '<rect x="6.5" y="6.5" width="11" height="11" rx="2" fill="currentColor"/>',
    "settings": (
        '<path d="M4 7h9"/><path d="M19 7h1"/><circle cx="16" cy="7" r="2.5"/>'
        '<path d="M4 17h3"/><path d="M13 17h7"/><circle cx="10" cy="17" r="2.5"/>'
    ),
    "help": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M9.6 9.4a2.5 2.5 0 1 1 3.6 2.3c-.8.5-1.2 1-1.2 1.9"/>'
        '<circle cx="12" cy="16.9" r="0.7" fill="currentColor"/>'
    ),
    "refresh": '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4.5v5h-5"/>',
    "folder": (
        '<path d="M3 7.5a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H5'
        'a2 2 0 0 1-2-2z"/>'
    ),
    "folder-open": (
        '<path d="M3 17V7.5a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2V10"/>'
        '<path d="M3 17l2.2-5.6a1 1 0 0 1 .9-.6H21l-2.4 6.3a1.4 1.4 0 0 1-1.3.9H4'
        'a1 1 0 0 1-1-1z"/>'
    ),
    "file": (
        '<path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
        '<path d="M14 3v5h5"/><path d="M9 13h6"/><path d="M9 17h6"/>'
    ),
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    "save": '<path d="M12 4v11"/><path d="M7.5 10.5L12 15l4.5-4.5"/><path d="M5 20h14"/>',
    "success": '<circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.8 2.8L16 9.6"/>',
    "info": (
        '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/>'
        '<circle cx="12" cy="7.8" r="0.7" fill="currentColor"/>'
    ),
    "warning": (
        '<path d="M12 4l9 16H3z"/><path d="M12 10v4.5"/>'
        '<circle cx="12" cy="17.2" r="0.7" fill="currentColor"/>'
    ),
    "error": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6"/><path d="M15 9l-6 6"/>',
    "close": '<path d="M6.5 6.5l11 11"/><path d="M17.5 6.5l-11 11"/>',
    "languages": (
        '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
        '<path d="M12 3c2.6 2.5 3.8 5.5 3.8 9s-1.2 6.5-3.8 9c-2.6-2.5-3.8-5.5-3.8-9S9.400 5.500 12 3z"/>'
    ),
    "chevron-right": '<path d="M9.5 6l6 6-6 6"/>',
    "chevron-down": '<path d="M6 9.5l6 6 6-6"/>',
    "chip": (
        '<rect x="7" y="7" width="10" height="10" rx="1.5"/>'
        '<path d="M10 3.5V7M14 3.5V7M10 17v3.500M14 17v3.500M3.500 10H7M3.500 14H7M17 10h3.500M17 14h3.500"/>'
    ),
}

_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    "{body}</svg>"
)

ICON_SIZE = 18
_cache: dict[tuple[str, str, int], QPixmap] = {}


def pixmap(name: str, color: str | None = None, size: int = ICON_SIZE) -> QPixmap:
    """Render an icon. ``color`` defaults to the theme's text colour."""
    color = color or tokens()["text"]
    key = (name, color, size)
    if key not in _cache:
        svg = _TEMPLATE.format(color=color, body=_SHAPES[name].replace("currentColor", color))
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        scale = 3  # render larger than shown so it stays crisp when scaled
        image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        result = QPixmap.fromImage(image)
        result.setDevicePixelRatio(scale)
        _cache[key] = result
    return _cache[key]


def icon(name: str, color: str | None = None, size: int = ICON_SIZE) -> QIcon:
    """An icon with a dimmed variant for disabled controls."""
    colors = tokens()
    result = QIcon()
    result.addPixmap(pixmap(name, color or colors["text"], size), QIcon.Mode.Normal)
    result.addPixmap(pixmap(name, colors["disabled_text"], size), QIcon.Mode.Disabled)
    return result


def set_button_icon(button, name: str, color: str | None = None) -> None:
    """Give a button an icon, with a little room between icon and label."""
    button.setIcon(icon(name, color))
    button.setIconSize(icon_size())
    text = button.text()
    if text and not text.startswith(" "):
        button.setText(" " + text)


def icon_size(size: int = ICON_SIZE) -> QSize:
    return QSize(size, size)


def clear_cache() -> None:
    _cache.clear()
