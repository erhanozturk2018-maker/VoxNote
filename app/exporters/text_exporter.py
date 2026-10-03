"""Plain text export (UTF-8)."""

from __future__ import annotations

from pathlib import Path

from app.exporters.base import (
    EMPTY_NOTICE,
    TRANSCRIPT_HEADING,
    Exporter,
    ExportOptions,
    build_document,
)
from app.transcript_models import Session


class TextExporter(Exporter):
    format_id = "txt"
    extension = "txt"
    label = "Plain text (.txt)"

    def render(self, session: Session, options: ExportOptions) -> str:
        document = build_document(session, options)
        lines: list[str] = []
        if document.show_headings:
            lines += [document.title, "=" * len(document.title), ""]
        if document.metadata:
            lines += [f"{name}: {value}" for name, value in document.metadata]
            lines.append("")
        if document.show_headings:
            lines += [TRANSCRIPT_HEADING, "-" * len(TRANSCRIPT_HEADING), ""]
        if not document.blocks:
            lines += [EMPTY_NOTICE, ""]
        elif document.as_paragraph:
            lines += [document.paragraph, ""]
        for block in () if document.as_paragraph else document.blocks:
            if document.show_language_headings:
                lines.append(f"[{block.language_name}]")
            lines += [document.line(segment) for segment in block.segments]
            if document.show_language_headings:
                lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"

    def write(self, session: Session, path: Path, options: ExportOptions) -> None:
        path.write_text(self.render(session, options), encoding="utf-8", newline="\n")
