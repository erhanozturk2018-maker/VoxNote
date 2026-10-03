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
    from app.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    icon = icon_path()
    if icon is not None:
        app.setWindowIcon(QIcon(str(icon)))
    apply_theme(app)

    settings_manager = SettingsManager()
    settings = settings_manager.load()
    set_language(settings.ui_language)

    controller = RecordingController(settings)
    window = MainWindow(controller, settings_manager)
    window.show()

    # Start slow work only after the window is visible.
    QTimer.singleShot(0, controller.load_model)
    QTimer.singleShot(200, window.check_recovery)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
