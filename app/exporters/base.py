"""Shared building blocks for all export formats.

Every exporter renders the same :class:`ExportDocument`, which guarantees
that all formats carry equivalent metadata and transcript content.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.language_names import language_list, language_name
from app.transcript_models import Session, TranscriptSegment, format_clock

TITLE = "Speaking Session"
TRANSCRIPT_HEADING = "Transcript"
EMPTY_NOTICE = "No speech was detected in this session."

# Characters that cannot be stored in XML based formats (DOCX) or rendered
# in a PDF. Tabs and line breaks are kept.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ExportError(Exception):
    """An export problem. ``code`` selects the localized message."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


# Metadata rows a document can contain, in display order.
METADATA_FIELDS = ("date", "languages", "duration", "session_id", "model")
LAYOUTS = ("lines", "paragraph")


@dataclass(frozen=True)
class ExportOptions:
    """What a saved document contains. The words of the transcript are never
    affected; only how they are arranged and which extras accompany them."""

    # Prefix every transcript line with its start time ("lines" layout only).
    include_timestamps: bool = True
    # "lines": one entry per recognised sentence, grouped by language.
    # "paragraph": the whole transcript as one continuous paragraph.
    layout: str = "lines"
    # Show a heading whenever the language changes ("lines" layout only).
    language_headings: bool = True
    # Show the document title and the "Transcript" heading.
    headings: bool = True
    # Metadata rows to include; a subset of METADATA_FIELDS.
    metadata: tuple[str, ...] = METADATA_FIELDS


@dataclass(frozen=True)
class LanguageBlock:
    """Consecutive segments spoken in the same language."""

    language: str
    language_name: str
    segments: tuple[TranscriptSegment, ...]


@dataclass(frozen=True)
class ExportDocument:
    """Format-independent view of a session."""

    title: str
    metadata: tuple[tuple[str, str], ...]
    blocks: tuple[LanguageBlock, ...]
    options: ExportOptions
    # The whole transcript as a single paragraph, in spoken order.
    paragraph: str = ""

    @property
    def as_paragraph(self) -> bool:
        return self.options.layout == "paragraph"

    @property
    def show_headings(self) -> bool:
        return self.options.headings

    @property
    def show_language_headings(self) -> bool:
        return self.options.language_headings

    def line(self, segment: TranscriptSegment) -> str:
        """Transcript line for a segment, with the timestamp if enabled."""
        if self.options.include_timestamps:
            return f"[{format_clock(segment.start)}] {segment.text}"
        return segment.text


def build_document(session: Session, options: ExportOptions | None = None) -> ExportDocument:
    options = options or ExportOptions()
    model = session.model or "unknown"
    rows = {
        "date": ("Date", session.started_at.strftime("%Y-%m-%d %H:%M:%S")),
        "languages": ("Languages", language_list(session.languages) or "None detected"),
        "duration": ("Duration", format_clock(session.duration_seconds)),
        "session_id": ("Session ID", session.session_id),
        "model": ("Model", f"Whisper {model} (faster-whisper)"),
    }
    metadata = tuple(rows[key] for key in METADATA_FIELDS if key in options.metadata)

    blocks: list[LanguageBlock] = []
    current: list[TranscriptSegment] = []
    for segment in session.segments:
        if not segment.text.strip():
            continue
        if current and current[0].language != segment.language:
            blocks.append(_block(current))
            current = []
        current.append(segment)
    if current:
        blocks.append(_block(current))
    paragraph = " ".join(
        segment.text.strip() for block in blocks for segment in block.segments
    )
    return ExportDocument(TITLE, metadata, tuple(blocks), options, paragraph)


def _block(segments: list[TranscriptSegment]) -> LanguageBlock:
    code = segments[0].language
    return LanguageBlock(code, language_name(code), tuple(segments))


def printable(text: str) -> str:
    """Remove control characters that document formats cannot represent."""
    return _CONTROL_CHARS_RE.sub("", text)


class Exporter(ABC):
    """One output format. Implementations write the complete file."""

    format_id: str
    extension: str
    label: str

    @abstractmethod
    def write(self, session: Session, path: Path, options: ExportOptions) -> None:
        """Write ``session`` to ``path``. May raise ``OSError`` or
        :class:`ExportError`."""
