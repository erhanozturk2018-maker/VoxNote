"""Makes sure only one VoxNote runs per user.

Starting VoxNote again, for example with the keyboard shortcut of its
desktop icon, does not open a second window: the new process asks the
running one to come to the front and exits.
"""

from __future__ import annotations

import getpass
import hashlib
import logging
import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from app.paths import ENV_HOME

log = logging.getLogger(__name__)


def _server_name() -> str:
    try:
        user = getpass.getuser()
    except Exception:
        user = "user"
    name = f"VoxNote-single-instance-{user}"
    # A separate data folder (portable installation, automated tests) is a
    # separate application as far as this guard is concerned.
    home = os.environ.get(ENV_HOME)
    if home:
        name += "-" + hashlib.sha1(home.encode("utf-8")).hexdigest()[:10]
    return name


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
