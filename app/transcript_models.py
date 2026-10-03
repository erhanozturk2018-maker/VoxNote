"""Plain data objects shared by the recognition engine, the GUI and exporters."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TranscriptSegment:
    """One recognised piece of speech.

    ``start`` and ``end`` are seconds from the beginning of the recording.
    ``text`` is exactly what the recogniser returned, apart from surrounding
    whitespace being stripped.
    """

    start: float
    end: float
    language: str
    text: str
    language_probability: float = 0.0


@dataclass
class Session:
    """A single recording session and its transcript."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    started_at: datetime = field(default_factory=lambda: datetime.now().astimezone())
    duration_seconds: float = 0.0
    segments: list[TranscriptSegment] = field(default_factory=list)
    # ISO 639-1 style codes as used by Whisper, ordered by first confident use.
    languages: list[str] = field(default_factory=list)
    model: str = ""
    device: str = ""
    compute_type: str = ""

    @property
    def is_empty(self) -> bool:
        return not any(segment.text.strip() for segment in self.segments)


def format_clock(seconds: float) -> str:
    """Format a duration as ``HH:MM:SS``."""
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
