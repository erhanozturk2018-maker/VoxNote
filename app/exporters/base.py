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


@dataclass(frozen=True)
class ExportOptions:
    # Prefix every transcript line with its start time.
    include_timestamps: bool = True


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

    def line(self, segment: TranscriptSegment) -> str:
        """Transcript line for a segment, with the timestamp if enabled."""
        if self.options.include_timestamps:
            return f"[{format_clock(segment.start)}] {segment.text}"
        return segment.text


def build_document(session: Session, options: ExportOptions | None = None) -> ExportDocument:
    options = options or ExportOptions()
    model = session.model or "unknown"
    metadata = (
        ("Date", session.started_at.strftime("%Y-%m-%d %H:%M:%S")),
        ("Languages", language_list(session.languages) or "None detected"),
        ("Duration", format_clock(session.duration_seconds)),
        ("Session ID", session.session_id),
        ("Model", f"Whisper {model} (faster-whisper)"),
    )

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
    return ExportDocument(TITLE, metadata, tuple(blocks), options)


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
