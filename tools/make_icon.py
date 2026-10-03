"""Generate the application icon and small interface images in assets/.

    python tools/make_icon.py

The icon is drawn with Qt, so no image editor or third-party artwork is
needed. Run it again after changing the drawing code below.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SIZE = 256


def draw() -> QImage:
    image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded blue tile
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#2563eb"))
    painter.drawRoundedRect(QRectF(8, 8, SIZE - 16, SIZE - 16), 52, 52)

    white = QColor("#ffffff")
    # Microphone capsule
    painter.setBrush(white)
    painter.drawRoundedRect(QRectF(100, 48, 56, 100), 28, 28)

    # Cradle and stand
    pen = QPen(white, 12)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(76, 72, 104, 104), 180 * 16, 180 * 16)
    painter.drawLine(QPointF(128, 176), QPointF(128, 204))
    painter.drawLine(QPointF(98, 208), QPointF(158, 208))
    painter.end()
    return image


def draw_arrow(color: str) -> QImage:
    """Small chevron used as the drop-down indicator of combo boxes."""
    image = QImage(24, 24, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.drawPolyline([QPointF(5, 9), QPointF(12, 16), QPointF(19, 9)])
    painter.end()
    return image


def main() -> int:
    app = QGuiApplication(sys.argv)  # noqa: F841 - required for painting
    ASSETS.mkdir(exist_ok=True)
    image = draw()
    png = ASSETS / "voxnote.png"
    ico = ASSETS / "voxnote.ico"
    if not image.save(str(png), "PNG"):
        print("Could not write", png)
        return 1
    if not image.save(str(ico), "ICO"):
        print("Could not write", ico, "(Qt ICO plugin missing)")
        return 1
    draw_arrow("#5b6470").save(str(ASSETS / "arrow-light.png"), "PNG")
    draw_arrow("#a2a9b3").save(str(ASSETS / "arrow-dark.png"), "PNG")
    print("Wrote", png, "and", ico)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
