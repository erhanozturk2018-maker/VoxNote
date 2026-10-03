"""System-wide keyboard shortcuts (Windows).

A global hotkey works while another application has the focus. Windows
delivers it as a ``WM_HOTKEY`` message to the thread that registered it;
Qt passes every native message through installed native event filters,
which is where it is picked up.

On other platforms, or when the key combination is already taken by another
program, registration simply fails and the application works without it.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

log = logging.getLogger(__name__)

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000

# Ctrl+Alt+R starts and stops recording.
TOGGLE_RECORDING = (1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("R"), "Ctrl+Alt+R")


class _Filter(QAbstractNativeEventFilter):
    def __init__(self, callback) -> None:
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self._callback(int(msg.wParam))
                return True, 0
        return False, 0


class GlobalHotkeys(QObject):
    """Registers the application's global hotkeys and reports presses."""

    toggle_recording = Signal()

    def __init__(self, app) -> None:
        super().__init__()
        self._app = app
        self._filter = _Filter(self._on_hotkey)
        self._registered: list[int] = []
        self.active = False

    def enable(self) -> bool:
        """Register the hotkeys. Returns ``False`` if that was not possible."""
        if self.active:
            return True
        if sys.platform != "win32":
            return False
        hotkey_id, modifiers, key, name = TOGGLE_RECORDING
        if not ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, key):
            log.warning("Global hotkey %s is not available (used by another program?)", name)
            return False
        self._registered.append(hotkey_id)
        self._app.installNativeEventFilter(self._filter)
        self.active = True
        log.info("Global hotkey %s registered", name)
        return True

    def disable(self) -> None:
        if not self.active:
            return
        for hotkey_id in self._registered:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
        self._registered.clear()
        self._app.removeNativeEventFilter(self._filter)
        self.active = False

    def _on_hotkey(self, hotkey_id: int) -> None:
        if hotkey_id == TOGGLE_RECORDING[0]:
            self.toggle_recording.emit()
