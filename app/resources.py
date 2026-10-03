"""Locations of files shipped with the application."""

from __future__ import annotations

import sys
from pathlib import Path


def assets_dir() -> Path:
    # PyInstaller unpacks bundled data below ``sys._MEIPASS``.
    bundle = getattr(sys, "_MEIPASS", None)
    base = Path(bundle) if bundle else Path(__file__).resolve().parent.parent
    return base / "assets"


def icon_path() -> Path | None:
    for name in ("voxnote.ico", "voxnote.png"):
        path = assets_dir() / name
        if path.is_file():
            return path
    return None
