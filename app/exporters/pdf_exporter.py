"""PDF export using ReportLab.

The PDF standard fonts cannot display characters such as ``ğ``, ``ş`` or
``İ``, so a Unicode TrueType font from the operating system is embedded
instead. Each paragraph uses the first available font that contains all of
its characters, which lets a single document mix, for example, Latin and
CJK text. If no usable Unicode font exists the export fails with a clear
error rather than producing a document with corrupted characters.

Set the ``VOXNOTE_PDF_FONT`` environment variable to the path of a ``.ttf``
file to force a specific font.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from xml.sax.saxutils import escape

from app.exporters.base import (
    EMPTY_NOTICE,
    TRANSCRIPT_HEADING,
    Exporter,
    ExportError,
    ExportOptions,
    build_document,
    printable,
)
from app.transcript_models import Session

log = logging.getLogger(__name__)

ENV_FONT = "VOXNOTE_PDF_FONT"

# (file name, index inside a .ttc collection). Earlier entries are preferred.
_WINDOWS_FONTS = [
    ("segoeui.ttf", 0),
    ("arial.ttf", 0),
    ("tahoma.ttf", 0),
    ("msyh.ttc", 0),  # Chinese
    ("YuGothR.ttc", 0),  # Japanese
    ("msgothic.ttc", 0),
    ("malgun.ttf", 0),  # Korean
    ("Nirmala.ttc", 0),  # Indic scripts
    ("Nirmala.ttf", 0),
    ("LeelawUI.ttf", 0),  # Thai, Lao, Khmer
    ("ebrima.ttf", 0),  # Ethiopic and other African scripts
    ("seguisym.ttf", 0),
]
_UNIX_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def font_candidates() -> list[tuple[Path, int]]:
    """Font files to consider, in order of preference."""
    candidates: list[tuple[Path, int]] = []
    forced = os.environ.get(ENV_FONT)
    if forced:
        candidates.append((Path(forced), 0))
    if sys.platform == "win32":
        fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates += [(fonts / name, index) for name, index in _WINDOWS_FONTS]
    else:
        candidates += [(Path(name), 0) for name in _UNIX_FONTS]
    return [(path, index) for path, index in candidates if path.is_file()]


class _FontLibrary:
    """Registers fonts with ReportLab on demand and picks one per text."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._candidates: list[tuple[Path, int]] | None = None
        self._loaded: list[tuple[str, frozenset[int]]] = []
        self._next = 0

    def _load_next(self) -> bool:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        if self._candidates is None:
            self._candidates = font_candidates()
        while self._next < len(self._candidates):
            path, index = self._candidates[self._next]
            self._next += 1
            name = f"VoxNote-{path.stem}-{index}"
            try:
                font = TTFont(name, str(path), subfontIndex=index)
                pdfmetrics.registerFont(font)
            except Exception as exc:  # e.g. PostScript-flavoured OpenType
                log.info("PDF font %s is not usable: %s", path.name, exc)
                continue
            self._loaded.append((name, frozenset(font.face.charToGlyph)))
            return True
        return False

    def font_for(self, text: str) -> str:
        """Return the name of the best font for ``text``."""
        needed = {ord(char) for char in text if not char.isspace()}
        with self._lock:
            position = 0
            while True:
                if position >= len(self._loaded) and not self._load_next():
                    break
                name, coverage = self._loaded[position]
                if needed <= coverage:
                    return name
                position += 1
            if not self._loaded:
                raise ExportError("pdf_font_missing")
            # No single font has every character; use the closest match.
            return max(self._loaded, key=lambda item: len(needed & item[1]))[0]


_fonts = _FontLibrary()


class PdfExporter(Exporter):
    format_id = "pdf"
    extension = "pdf"
    label = "PDF (.pdf)"

    def write(self, session: Session, path: Path, options: ExportOptions) -> None:
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        document = build_document(session, options)
        base_font = _fonts.font_for(document.title + TRANSCRIPT_HEADING + EMPTY_NOTICE)

        def style(name: str, size: float, text: str = "", **extra) -> ParagraphStyle:
            return ParagraphStyle(
                name,
                fontName=_fonts.font_for(text) if text else base_font,
                fontSize=size,
                leading=size * 1.4,
                alignment=TA_LEFT,
                **extra,
            )

        def paragraph(text: str, name: str, size: float, **extra) -> Paragraph:
            text = printable(text)
            return Paragraph(escape(text), style(name, size, text, **extra))

        story = [paragraph(document.title, "Title", 20, spaceAfter=10)]
        for name, value in document.metadata:
            story.append(paragraph(f"{name}: {value}", "Meta", 10.5, textColor=HexColor("#333333")))
        story.append(Spacer(1, 8))
        story.append(paragraph(TRANSCRIPT_HEADING, "Heading", 15, spaceBefore=8, spaceAfter=6))
        if not document.blocks:
            story.append(paragraph(EMPTY_NOTICE, "Empty", 11, textColor=HexColor("#555555")))
        for block in document.blocks:
            story.append(
                paragraph(
                    block.language_name,
                    "Language",
                    12,
                    spaceBefore=10,
                    spaceAfter=4,
                    textColor=HexColor("#1f4e8c"),
                )
            )
            for segment in block.segments:
                story.append(paragraph(document.line(segment), "Body", 11, spaceAfter=4))

        output = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=document.title,
            author="",
            creator="",
        )
        output.build(story)
