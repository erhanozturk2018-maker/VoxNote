"""Locations of user-writable application directories.

Nothing in this module assumes a fixed absolute path. Every location is
derived from the operating system at runtime. Setting the ``VOXNOTE_HOME``
environment variable redirects all application data into a single folder,
which is used by the test suite and can be used for portable installations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app import APP_NAME

ENV_HOME = "VOXNOTE_HOME"


def _override() -> Path | None:
    value = os.environ.get(ENV_HOME)
    return Path(value) if value else None


def config_dir() -> Path:
    """Directory holding ``settings.json``."""
    override = _override()
    if override:
        return override / "config"
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / APP_NAME


def data_dir() -> Path:
    """Directory holding logs, session journals and optional debug audio."""
    override = _override()
    if override:
        return override / "data"
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME")
    return (Path(base) if base else Path.home() / ".local" / "share") / APP_NAME


def log_dir() -> Path:
    return data_dir() / "logs"


def journal_dir() -> Path:
    """Crash-recovery journals of sessions that have not been exported yet."""
    return data_dir() / "sessions"


def audio_dir() -> Path:
    """Debug audio recordings. Only used when the user enables retention."""
    return data_dir() / "audio"


def settings_file() -> Path:
    return config_dir() / "settings.json"


def documents_dir() -> Path:
    """Return the user's Documents folder without assuming where it lives.

    On Windows the folder can be relocated (for example into OneDrive), so the
    shell is asked for the real location.
    """
    if sys.platform == "win32":
        found = _windows_documents_dir()
        if found:
            return found
    elif sys.platform not in ("darwin",):
        xdg = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg:
            return Path(xdg)
    return Path.home() / "Documents"


def _windows_documents_dir() -> Path | None:
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        # FOLDERID_Documents {FDD39AD0-238F-46AF-ADB4-6C85480369C7}
        folder_id = GUID(
            0xFDD39AD0,
            0x238F,
            0x46AF,
            (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7),
        )
        buffer = ctypes.c_wchar_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id), 0, None, ctypes.byref(buffer)
        )
        if result != 0 or not buffer.value:
            return None
        path = Path(buffer.value)
        ctypes.windll.ole32.CoTaskMemFree(buffer)
        return path
    except Exception:
        return None


def default_save_dir() -> Path:
    """Default export folder used on first launch."""
    return documents_dir() / APP_NAME
