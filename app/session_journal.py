"""Crash-safe journal of the session in progress.

While a session is recorded, every recognised segment is appended to a
small JSON Lines file in the application data directory. The journal is
deleted as soon as the transcript has been exported successfully. If the
application or the computer stops unexpectedly, the next launch finds the
journal and offers to recover the transcript.

The journal contains transcript text only, never audio.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from app.transcript_models import Session, TranscriptSegment

log = logging.getLogger(__name__)

JOURNAL_SUFFIX = ".jsonl"


class SessionJournal:
    def __init__(self, directory: Path, session: Session) -> None:
        self.path = directory / f"{session.session_id}{JOURNAL_SUFFIX}"
        self._file = None
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self._file = open(self.path, "w", encoding="utf-8")
            self._write(
                {
                    "type": "session",
                    "id": session.session_id,
                    "started_at": session.started_at.isoformat(),
                    "model": session.model,
                    "device": session.device,
                    "compute_type": session.compute_type,
                }
            )
        except OSError:
            # Recording must still work when the journal cannot be written.
            log.exception("Session journal could not be created")
            self._file = None

    def _write(self, record: dict) -> None:
        if self._file is None:
            return
        try:
            self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._file.flush()
            os.fsync(self._file.fileno())
        except OSError:
            log.exception("Session journal could not be written")
            self.close()

    def append(self, segment: TranscriptSegment, languages: list[str]) -> None:
        self._write(
            {
                "type": "segment",
                "start": segment.start,
                "end": segment.end,
                "language": segment.language,
                "language_probability": segment.language_probability,
                "text": segment.text,
                "languages": languages,
            }
        )

    def close(self) -> None:
        if self._file is not None:
            try:
                self._file.close()
            except OSError:
                pass
            self._file = None

    def delete(self) -> None:
        self.close()
        delete_journal(self.path)


def delete_journal(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        log.exception("Session journal could not be deleted")


def find_journals(directory: Path) -> list[Path]:
    try:
        return sorted(directory.glob(f"*{JOURNAL_SUFFIX}"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return []


def load_journal(path: Path) -> Session | None:
    """Rebuild a session from a journal. Damaged lines are skipped."""
    session: Session | None = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        try:
            record = json.loads(line)
            if record.get("type") == "session":
                session = Session(
                    session_id=str(record["id"]),
                    started_at=datetime.fromisoformat(record["started_at"]),
                    model=str(record.get("model", "")),
                    device=str(record.get("device", "")),
                    compute_type=str(record.get("compute_type", "")),
                )
            elif record.get("type") == "segment" and session is not None:
                session.segments.append(
                    TranscriptSegment(
                        start=float(record["start"]),
                        end=float(record["end"]),
                        language=str(record["language"]),
                        text=str(record["text"]),
                        language_probability=float(record.get("language_probability", 0.0)),
                    )
                )
                session.languages = [str(code) for code in record.get("languages", [])]
        except (ValueError, KeyError, TypeError):
            continue  # a line cut off by a crash
    if session is None:
        return None
    if session.segments:
        session.duration_seconds = max(segment.end for segment in session.segments)
    return session
