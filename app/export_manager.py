"""Writes a session to disk in the selected format.

The manager owns everything that is the same for all formats: checking the
target directory, building the file name, avoiding collisions and making
sure a failed export never leaves a damaged file behind.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path

from app.exporters import EXPORTERS, ExportOptions
from app.exporters.base import ExportError
from app.filename_template import candidate_paths, render_filename
from app.transcript_models import Session

log = logging.getLogger(__name__)


__all__ = ["ExportError", "check_directory", "export_session", "export_to_path"]


def check_directory(directory: Path, create: bool = False) -> None:
    """Verify that ``directory`` exists and can be written to.

    Raises :class:`ExportError` with one of the codes ``directory_missing``,
    ``directory_invalid`` or ``directory_not_writable``.
    """
    if not directory.exists():
        if not create:
            raise ExportError("directory_missing", str(directory))
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExportError("directory_not_writable", str(exc)) from exc
    if not directory.is_dir():
        raise ExportError("directory_invalid", str(directory))
    probe = directory / f".voxnote-{uuid.uuid4().hex}.tmp"
    try:
        with open(probe, "xb"):
            pass
        probe.unlink()
    except OSError as exc:
        raise ExportError("directory_not_writable", str(exc)) from exc


def _reserve(directory: Path, stem: str, extension: str) -> Path:
    """Atomically claim the first free file name for ``stem``."""
    for candidate in candidate_paths(directory, stem, extension):
        try:
            with open(candidate, "xb"):
                return candidate
        except FileExistsError:
            continue
    raise AssertionError("unreachable")


def _write(session: Session, target: Path, format_id: str, options: ExportOptions) -> None:
    """Render into a temporary file and move it into place when complete."""
    exporter = EXPORTERS[format_id]
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex[:8]}.part")
    try:
        exporter.write(session, temporary, options)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ExportError("export_failed", "the exporter produced no data")
        os.replace(temporary, target)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def export_session(
    session: Session,
    directory: Path,
    template: str,
    format_id: str,
    options: ExportOptions | None = None,
) -> Path:
    """Save ``session`` into ``directory`` and return the new file's path.

    An existing file is never overwritten: a numeric suffix is added
    instead. Raises :class:`ExportError`; when it does, no file is left
    behind.
    """
    if format_id not in EXPORTERS:
        raise ExportError("unknown_format", format_id)
    options = options or ExportOptions()
    started = time.perf_counter()
    check_directory(directory, create=True)

    stem = render_filename(template, session)
    try:
        target = _reserve(directory, stem, EXPORTERS[format_id].extension)
    except OSError as exc:
        raise ExportError("export_failed", str(exc)) from exc

    try:
        _write(session, target, format_id, options)
    except BaseException as exc:
        try:
            target.unlink(missing_ok=True)  # remove the empty placeholder
        except OSError:
            pass
        if isinstance(exc, ExportError):
            raise
        if isinstance(exc, Exception):
            log.exception("Export to %s failed", format_id)
            raise ExportError("export_failed", str(exc)) from exc
        raise
    log.info(
        "Exported %d segment(s) as %s in %.2f s",
        len(session.segments),
        format_id,
        time.perf_counter() - started,
    )
    return target


def export_to_path(
    session: Session, target: Path, format_id: str, options: ExportOptions | None = None
) -> Path:
    """Save ``session`` to an explicit path chosen by the user ("Save As").

    The caller is responsible for confirming an overwrite; the operating
    system's save dialog does that. An existing file is replaced only after
    the new content was written completely.
    """
    if format_id not in EXPORTERS:
        raise ExportError("unknown_format", format_id)
    check_directory(target.parent, create=False)
    try:
        _write(session, target, format_id, options or ExportOptions())
    except ExportError:
        raise
    except Exception as exc:
        log.exception("Export to %s failed", format_id)
        raise ExportError("export_failed", str(exc)) from exc
    return target
