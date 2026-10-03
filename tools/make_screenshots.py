"""Render the screenshots used in the documentation (docs/images/*.png).

    python tools/make_screenshots.py

The real application windows are created and painted into image files. The
speech model is not loaded and the microphone is not opened; the transcript
shown is fixed sample text, inserted through the same code path that live
recognition results use. Settings are read from and written to a temporary
folder, so your own configuration is not touched.
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["VOXNOTE_HOME"] = tempfile.mkdtemp(prefix="voxnote-shots-")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.i18n import set_language  # noqa: E402
from app.main_window import MainWindow  # noqa: E402
from app.recording_controller import AppState, RecordingController  # noqa: E402
from app.settings_dialog import SettingsDialog  # noqa: E402
from app.settings_manager import Settings, SettingsManager  # noqa: E402
from app.theme import apply_theme  # noqa: E402
from app.transcriber import DeviceInfo  # noqa: E402
from app.transcript_models import Session, TranscriptSegment  # noqa: E402

OUTPUT = ROOT / "docs" / "images"

SAMPLE = [
    (2.0, 5.4, "en", "Yesterday I went to the gym and trained for about one hour."),
    (6.1, 9.0, "en", "After that I was really tired."),
    (10.2, 13.6, "tr", "Sonra arkadaşımı gördüm ve birlikte kahve içmeye gittik."),
    (14.4, 16.9, "tr", "Çok güzel bir gündü."),
    (18.0, 20.1, "en", "We talked for a while."),
]


def sample_session() -> Session:
    session = Session(
        session_id="3f9a1c2e",
        started_at=datetime(2026, 10, 3, 14, 30, 0).astimezone(),
        duration_seconds=24.0,
        model="small",
        device="cuda",
        compute_type="float16",
    )
    return session


def grab(widget, name: str) -> None:
    QApplication.processEvents()
    path = OUTPUT / name
    widget.grab().save(str(path), "PNG")
    print("Wrote", path)


def main() -> int:
    app = QApplication(sys.argv)
    apply_theme(app)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    documents = Path("C:/Users/Alex/Documents/VoxNote")
    for language in ("en", "tr", "de"):
        set_language(language)
        settings = Settings(ui_language=language, save_directory=str(documents))
        controller = RecordingController(settings)
        # Present the model as loaded without loading it.
        controller.transcriber.device_info = DeviceInfo("cuda", "float16")
        controller.model_ready = True
        controller.model_state = "ready"
        window = MainWindow(controller, SettingsManager())
        window.resize(900, 760)
        window.show()
        window._update_model_label()
        suffix = "" if language == "en" else f"-{language}"

        if language == "en":
            grab(window, "main-ready.png")

        # Recording
        controller.session = sample_session()
        controller.state = AppState.RECORDING
        controller.session_reset.emit()
        segments = [TranscriptSegment(a, b, code, text, 0.98) for a, b, code, text in SAMPLE]
        controller._on_recognized(segments[:3], ["en", "tr"])
        window._on_state_changed(AppState.RECORDING)
        window._timer.stop()
        window.timer_label.setText("00:00:14")
        window._on_speech_active(True)
        window._on_level(0.22)
        if language == "en":
            grab(window, "main-recording.png")

        # Completed
        controller._on_recognized(segments[3:], ["en", "tr"])
        window._on_speech_active(False)
        window._on_level(0.0)
        controller.state = AppState.COMPLETED
        controller._unsaved = False
        controller.saved_path = documents / "2026-10-03_14-30-00_en-tr.md"
        window._on_state_changed(AppState.COMPLETED)
        window._show_result("success", "result.saved", {"path": str(controller.saved_path)})
        grab(window, f"main-completed{suffix}.png")

        if language == "en":
            dialog = SettingsDialog(settings, controller, window)
            dialog.show()
            for index, name in enumerate(("general", "recording", "system")):
                dialog.tabs.setCurrentIndex(index)
                grab(dialog, f"settings-{name}.png")
            dialog.close()
        controller.discard_session()
        controller.state = AppState.READY
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
