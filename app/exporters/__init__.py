"""Export formats.

To add a format, create an :class:`~app.exporters.base.Exporter` subclass
and add an instance to ``EXPORTERS``. Nothing in the recording or
transcription code needs to change.
"""

from __future__ import annotations

from app.exporters.base import Exporter, ExportOptions
from app.exporters.docx_exporter import DocxExporter
from app.exporters.json_exporter import JsonExporter
from app.exporters.markdown_exporter import MarkdownExporter
from app.exporters.pdf_exporter import PdfExporter
from app.exporters.text_exporter import TextExporter

EXPORTERS: dict[str, Exporter] = {
    exporter.format_id: exporter
    for exporter in (
        MarkdownExporter(),
        TextExporter(),
        JsonExporter(),
        DocxExporter(),
        PdfExporter(),
    )
}

__all__ = ["EXPORTERS", "Exporter", "ExportOptions"]
