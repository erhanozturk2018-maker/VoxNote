"""Markdown export."""

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


class MarkdownExporter(Exporter):
    format_id = "md"
    extension = "md"
    label = "Markdown (.md)"

    def render(self, session: Session, options: ExportOptions) -> str:
        document = build_document(session, options)
        lines: list[str] = []
        if document.show_headings:
            lines += [f"# {document.title}", ""]
        if document.metadata:
            lines += [f"- {name}: {value}" for name, value in document.metadata]
            lines.append("")
        if document.show_headings:
            lines += [f"## {TRANSCRIPT_HEADING}", ""]
        if not document.blocks:
            lines += [f"_{EMPTY_NOTICE}_", ""]
        elif document.as_paragraph:
            lines += [document.paragraph, ""]
        for block in () if document.as_paragraph else document.blocks:
            if document.show_language_headings:
                lines += [f"### {block.language_name}", ""]
            for segment in block.segments:
                # A blank line between entries keeps each one on its own
                # line in rendered Markdown without altering the text.
                lines += [document.line(segment), ""]
        return "\n".join(lines).rstrip("\n") + "\n"

    def write(self, session: Session, path: Path, options: ExportOptions) -> None:
        path.write_text(self.render(session, options), encoding="utf-8", newline="\n")
