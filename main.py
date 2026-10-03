"""VoxNote entry point.

    python main.py
"""

from __future__ import annotations

import sys


def main() -> int:
    from app.logging_config import install_excepthook, setup_logging

    setup_logging()
    install_excepthook()

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from app import APP_NAME, APP_VERSION
    from app.i18n import set_language
    from app.main_window import MainWindow
    from app.recording_controller import RecordingController
    from app.resources import icon_path
    from app.settings_manager import SettingsManager
    from app.theme import apply_theme, set_mode

    if sys.platform == "win32":
        # Gives the window its own taskbar entry and icon when the
        # application is started through python.exe instead of VoxNote.exe.
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VoxNote.Desktop")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    icon = icon_path()
    if icon is not None:
        app.setWindowIcon(QIcon(str(icon)))
    # A second start (for example through the shortcut key of the desktop
    # icon) brings the running window to the front instead.
    from app.single_instance import InstanceServer, notify_running_instance

    if notify_running_instance():
        return 0
    instance_server = InstanceServer()

    settings_manager = SettingsManager()
    settings = settings_manager.load()
    set_language(settings.ui_language)
    set_mode(settings.theme)
    apply_theme(app)

    controller = RecordingController(settings)
    window = MainWindow(controller, settings_manager)
    window.show()
    instance_server.activation_requested.connect(window.bring_to_front)
    window.enable_desktop_integration()

    # Start slow work only after the window is visible.
    QTimer.singleShot(0, controller.load_model)
    QTimer.singleShot(200, window.check_recovery)
    QTimer.singleShot(400, window.show_first_run_help)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
