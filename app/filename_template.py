"""File name templates: expansion, validation and sanitisation.

Templates use ``{placeholder}`` substitutions. Substitution is done with a
regular expression rather than ``str.format`` so a template can never reach
object attributes, and the result is always reduced to a single safe file
name that cannot escape the chosen directory.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from app.transcript_models import Session

DEFAULT_TEMPLATE = "{date}_{time}_{languages}"
PLACEHOLDERS = ("date", "time", "languages", "duration", "session_id")
FALLBACK_NAME = "session"
MAX_STEM_LENGTH = 120

_PLACEHOLDER_RE = re.compile(r"\{([^{}]*)\}")
_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}  # fmt: skip


def template_errors(template: str) -> list[str]:
    """Return problems with a template as machine-readable codes.

    Codes: ``empty``, ``unbalanced`` and ``unknown:<name>``.
    """
    errors: list[str] = []
    if not template.strip():
        return ["empty"]
    for name in _PLACEHOLDER_RE.findall(template):
        if name not in PLACEHOLDERS:
            errors.append(f"unknown:{name}")
    remainder = _PLACEHOLDER_RE.sub("", template)
    if "{" in remainder or "}" in remainder:
        errors.append("unbalanced")
    return errors


def template_values(session: Session) -> dict[str, str]:
    """Substitution values for a session."""
    total = max(0, int(round(session.duration_seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {
        "date": session.started_at.strftime("%Y-%m-%d"),
        "time": session.started_at.strftime("%H-%M-%S"),
        "languages": "-".join(session.languages) if session.languages else "none",
        "duration": f"{hours:02d}h{minutes:02d}m{seconds:02d}s",
        "session_id": session.session_id,
    }


def sanitize_filename(name: str) -> str:
    """Turn arbitrary text into a file name that is valid on Windows,
    macOS and Linux. Path separators are removed, so the result can never
    point outside the target directory."""
    name = unicodedata.normalize("NFC", name)
    name = _INVALID_CHARS_RE.sub("_", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"_{2,}", "_", name)
    # Windows silently drops trailing dots and spaces; leading dots would
    # create hidden files or ".." style names.
    name = name.strip(" ._")
    if len(name) > MAX_STEM_LENGTH:
        name = name[:MAX_STEM_LENGTH].rstrip(" ._")
    if not name:
        return FALLBACK_NAME
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = f"_{name}"
    return name


def render_filename(template: str, session: Session) -> str:
    """Expand a template for a session and return a safe file name stem."""
    values = template_values(session)

    def substitute(match: re.Match[str]) -> str:
        return values.get(match.group(1), "")

    if template_errors(template):
        template = DEFAULT_TEMPLATE
    return sanitize_filename(_PLACEHOLDER_RE.sub(substitute, template))


def candidate_paths(directory: Path, stem: str, extension: str):
    """Yield ``stem.ext``, ``stem_2.ext``, ``stem_3.ext`` ... in order."""
    extension = extension.lstrip(".")
    yield directory / f"{stem}.{extension}"
    counter = 2
    while True:
        yield directory / f"{stem}_{counter}.{extension}"
        counter += 1


def unique_path(directory: Path, stem: str, extension: str) -> Path:
    """Return the first path for ``stem`` that does not exist yet."""
    for candidate in candidate_paths(directory, stem, extension):
        if not candidate.exists():
            return candidate
    raise AssertionError("unreachable")
