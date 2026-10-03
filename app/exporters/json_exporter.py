"""JSON export.

The schema is documented in ``docs/EXPORT_FORMATS.md``. Any change that
removes or renames a field, or changes its meaning, must increase
``JSON_SCHEMA_VERSION``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app import APP_NAME, APP_VERSION
from app.exporters.base import Exporter, ExportOptions
from app.language_names import language_name
from app.transcript_models import Session

JSON_SCHEMA_VERSION = 1


def build_json_document(session: Session) -> dict[str, Any]:
    segments = [segment for segment in session.segments if segment.text.strip()]
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "application": {"name": APP_NAME, "version": APP_VERSION},
        "session": {
            "id": session.session_id,
            "started_at": session.started_at.isoformat(timespec="seconds"),
            "duration_seconds": round(session.duration_seconds, 2),
            "languages": list(session.languages),
            "language_names": [language_name(code) for code in session.languages],
            "model": session.model,
            "device": session.device,
            "compute_type": session.compute_type,
        },
        "segments": [
            {
                "index": index,
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "language": segment.language,
                "language_probability": round(segment.language_probability, 4),
                "text": segment.text,
            }
            for index, segment in enumerate(segments)
        ],
    }


def validate_json_document(document: Any) -> list[str]:
    """Check a document against schema version 1.

    Returns a list of problems; an empty list means the document is valid.
    """
    problems: list[str] = []

    def require(container: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
        if not isinstance(container, dict) or key not in container:
            problems.append(f"{where}.{key} is missing")
            return None
        value = container[key]
        if isinstance(value, bool) or not isinstance(value, kinds):
            problems.append(f"{where}.{key} has the wrong type")
            return None
        return value

    if not isinstance(document, dict):
        return ["document is not an object"]
    if document.get("schema_version") != JSON_SCHEMA_VERSION:
        problems.append("schema_version is not supported")

    application = require(document, "application", dict, "document")
    if application is not None:
        require(application, "name", str, "application")
        require(application, "version", str, "application")

    session = require(document, "session", dict, "document")
    if session is not None:
        require(session, "id", str, "session")
        require(session, "started_at", str, "session")
        duration = require(session, "duration_seconds", (int, float), "session")
        if duration is not None and duration < 0:
            problems.append("session.duration_seconds is negative")
        for key in ("languages", "language_names"):
            values = require(session, key, list, "session")
            if values is not None and not all(isinstance(item, str) for item in values):
                problems.append(f"session.{key} must contain only strings")
        for key in ("model", "device", "compute_type"):
            require(session, key, str, "session")

    segments = require(document, "segments", list, "document")
    previous_start = 0.0
    for position, segment in enumerate(segments or []):
        where = f"segments[{position}]"
        index = require(segment, "index", int, where)
        if index is not None and index != position:
            problems.append(f"{where}.index is out of order")
        start = require(segment, "start", (int, float), where)
        end = require(segment, "end", (int, float), where)
        if start is not None and end is not None:
            if end < start:
                problems.append(f"{where} ends before it starts")
            if start < previous_start:
                problems.append(f"{where} is not in chronological order")
            previous_start = start
        require(segment, "language", str, where)
        probability = require(segment, "language_probability", (int, float), where)
        if probability is not None and not 0 <= probability <= 1:
            problems.append(f"{where}.language_probability is outside 0..1")
        text = require(segment, "text", str, where)
        if text is not None and not text.strip():
            problems.append(f"{where}.text is empty")
    return problems


class JsonExporter(Exporter):
    format_id = "json"
    extension = "json"
    label = "JSON (.json)"

    def render(self, session: Session, options: ExportOptions) -> str:
        return json.dumps(build_json_document(session), indent=2, ensure_ascii=False) + "\n"

    def write(self, session: Session, path: Path, options: ExportOptions) -> None:
        path.write_text(self.render(session, options), encoding="utf-8", newline="\n")
