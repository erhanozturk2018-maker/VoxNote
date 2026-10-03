"""Generate the application icon and the other image files in assets/.

    python tools/make_icon.py

Everything is drawn with Qt, so no image editor or third-party artwork is
needed. Run it again after changing the drawing code below.

Output:
    assets/voxnote.png            256 px application icon
    assets/voxnote.ico            Windows icon with 16 to 256 px images
    assets/arrow-light.png        drop-down arrow, light theme
    assets/arrow-dark.png         drop-down arrow, dark theme
    assets/installer-side.bmp     side picture of the setup wizard
    assets/installer-small.bmp    corner picture of the setup wizard
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
BLUE = "#2563eb"
BLUE_DARK = "#1b3fa8"


def paint_logo(painter: QPainter, size: float, tile: bool = True) -> None:
    """Draw the microphone logo into a ``size`` x ``size`` square.

    The drawing is defined on a 256 unit grid and scaled, so every icon
    size is rendered from the vector description instead of being resized.
    """
    painter.save()
    painter.scale(size / 256, size / 256)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if tile:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BLUE))
        painter.drawRoundedRect(QRectF(8, 8, 240, 240), 52, 52)

    white = QColor("#ffffff")
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(white)
    painter.drawRoundedRect(QRectF(100, 48, 56, 100), 28, 28)  # capsule

    # Thin strokes disappear in very small icons, so they are thickened.
    pen = QPen(white, 12 if size >= 48 else 18)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(76, 72, 104, 104), 180 * 16, 180 * 16)  # cradle
    painter.drawLine(QPointF(128, 176), QPointF(128, 204))  # stand
    painter.drawLine(QPointF(98, 208), QPointF(158, 208))
    painter.restore()


def logo(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    paint_logo(painter, size)
    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def write_ico(path: Path, sizes=ICON_SIZES) -> None:
    """Write a multi-size .ico file with PNG-compressed images."""
    images = [(size, png_bytes(logo(size))) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    directory = b""
    for size, data in images:
        dimension = 0 if size >= 256 else size  # 0 means 256
        directory += struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    path.write_bytes(header + directory + b"".join(data for _, data in images))


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


def installer_side(width: int = 328, height: int = 628) -> QImage:
    """Tall picture shown on the first and last page of the setup wizard."""
    image = QImage(width, height, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    gradient = QLinearGradient(0, 0, 0, height)
    gradient.setColorAt(0.0, QColor(BLUE))
    gradient.setColorAt(1.0, QColor(BLUE_DARK))
    painter.fillRect(0, 0, width, height, gradient)

    logo_size = 150
    painter.translate((width - logo_size) / 2, 150)
    paint_logo(painter, logo_size, tile=False)
    painter.resetTransform()

    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setPen(QColor("#ffffff"))
    title = QFont("Segoe UI", 30)
    title.setWeight(QFont.Weight.DemiBold)
    painter.setFont(title)
    painter.drawText(QRectF(0, 330, width, 70), Qt.AlignmentFlag.AlignHCenter, "VoxNote")
    painter.setFont(QFont("Segoe UI", 12))
    painter.setPen(QColor("#dbe6ff"))
    painter.drawText(
        QRectF(20, 400, width - 40, 80),
        Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
        "Speech to text,\non your own computer",
    )
    painter.end()
    return image


def installer_small(size: int = 110) -> QImage:
    """Square picture shown in the corner of the other wizard pages."""
    image = QImage(size, size, QImage.Format.Format_RGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    paint_logo(painter, size)
    painter.end()
    return image


def main() -> int:
    app = QGuiApplication(sys.argv)  # noqa: F841 - required for painting
    ASSETS.mkdir(exist_ok=True)
    outputs = {
        "voxnote.png": lambda p: logo(256).save(str(p), "PNG"),
        "voxnote.ico": lambda p: (write_ico(p), True)[1],
        "arrow-light.png": lambda p: draw_arrow("#5b6470").save(str(p), "PNG"),
        "arrow-dark.png": lambda p: draw_arrow("#a2a9b3").save(str(p), "PNG"),
        "installer-side.bmp": lambda p: installer_side().save(str(p), "BMP"),
        "installer-small.bmp": lambda p: installer_small().save(str(p), "BMP"),
    }
    for name, write in outputs.items():
        path = ASSETS / name
        if not write(path):
            print("Could not write", path)
            return 1
        print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
