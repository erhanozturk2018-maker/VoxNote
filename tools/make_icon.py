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
VIOLET = "#7b4fe0"
VIOLET_DARK = "#4f2aa6"

# The logo shows what the application does: sound (a waveform, left) becomes
# writing (lines of text, right). Each tuple is (x, height) of a waveform bar
# or (y, length) of a text line on a 256 unit grid.
WAVE_BARS = ((48, 44), (74, 104), (100, 68), (126, 128))
TEXT_LINES = ((92, 58), (128, 58), (164, 36))
# Simplified drawing for very small icon sizes.
WAVE_BARS_SMALL = ((46, 64), (82, 124), (118, 84))
TEXT_LINES_SMALL = ((104, 62), (152, 40))


def paint_logo(painter: QPainter, size: float, tile: bool = True) -> None:
    """Draw the logo into a ``size`` x ``size`` square.

    The drawing is defined on a 256 unit grid and scaled, so every icon
    size is rendered from the vector description instead of being resized.
    """
    painter.save()
    painter.scale(size / 256, size / 256)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    if tile:
        gradient = QLinearGradient(0, 8, 0, 248)
        gradient.setColorAt(0.0, QColor(VIOLET))
        gradient.setColorAt(1.0, QColor(VIOLET_DARK))
        painter.setBrush(gradient)
        painter.drawRoundedRect(QRectF(8, 8, 240, 240), 54, 54)

    painter.setBrush(QColor("#ffffff"))
    small = size < 40
    bars, lines = (WAVE_BARS_SMALL, TEXT_LINES_SMALL) if small else (WAVE_BARS, TEXT_LINES)
    bar_width, line_height, text_x = (24, 26, 150) if small else (16, 18, 154)
    for x, height in bars:
        painter.drawRoundedRect(
            QRectF(x, 128 - height / 2, bar_width, height), bar_width / 2, bar_width / 2
        )
    for y, length in lines:
        painter.drawRoundedRect(
            QRectF(text_x, y - line_height / 2, length, line_height),
            line_height / 2,
            line_height / 2,
        )
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
    gradient.setColorAt(0.0, QColor(VIOLET))
    gradient.setColorAt(1.0, QColor(VIOLET_DARK))
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
    painter.setPen(QColor("#e6dcff"))
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
