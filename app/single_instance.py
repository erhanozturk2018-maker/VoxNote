"""Makes sure only one VoxNote runs per user.

Starting VoxNote again, for example with the keyboard shortcut of its
desktop icon, does not open a second window: the new process asks the
running one to come to the front and exits.
"""

from __future__ import annotations

import getpass
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger(__name__)


def _server_name() -> str:
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    return f"VoxNote-single-instance-{user}"


def notify_running_instance(timeout_ms: int = 400) -> bool:
    """Ask an already running VoxNote to show its window.

    Returns ``True`` if another instance answered.
    """
    socket = QLocalSocket()
    socket.connectToServer(_server_name())
    if not socket.waitForConnected(timeout_ms):
        return False
    socket.write(b"show")
    socket.waitForBytesWritten(timeout_ms)
    socket.disconnectFromServer()
    return True


class InstanceServer(QObject):
    """Listens for later launches of the application."""

    activation_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._server = QLocalServer(self)
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        # A stale name can be left behind by a crashed process.
        QLocalServer.removeServer(_server_name())
        if not self._server.listen(_server_name()):
            log.warning("Single-instance server could not start: %s", self._server.errorString())
        self._server.newConnection.connect(self._on_connection)

    def _on_connection(self) -> None:
        connection = self._server.nextPendingConnection()
        if connection is not None:
            connection.disconnectFromServer()
        self.activation_requested.emit()
