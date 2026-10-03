"""Document layout and content options, the content panel, the edge bar and
the single-instance guard."""

import json

import pytest

from app.export_manager import export_session
from app.exporters import ExportOptions
from app.exporters.base import METADATA_FIELDS, build_document
from app.filename_template import DEFAULT_TEMPLATE
from app.recording_controller import AppState, RecordingController
from app.settings_manager import Settings, SettingsManager
from tests.conftest import TURKISH_TEXT, wait_until
from tests.test_exporters import read_export

DOCUMENT_FORMATS = ["md", "txt", "docx", "pdf"]
PARAGRAPH = f"Yesterday I went to the gym. {TURKISH_TEXT} We talked for a while."


def test_paragraph_joins_all_segments_in_order(session):
    document = build_document(session, ExportOptions(layout="paragraph"))
    assert document.paragraph == PARAGRAPH
    assert document.as_paragraph


@pytest.mark.parametrize("format_id", DOCUMENT_FORMATS)
def test_paragraph_layout(session, tmp_path, format_id):
    options = ExportOptions(layout="paragraph")
    text = read_export(export_session(session, tmp_path, DEFAULT_TEMPLATE, format_id, options))
    flat = " ".join(text.split())
    assert "Yesterday I went to the gym. Sonra arkadaşımı gördüm." in flat
    assert "ığdır. We talked for a while." in flat
    # No per-line timestamps and no language headings inside the paragraph.
    assert "[00:00" not in text
    assert "### English" not in text and "[English]" not in text
    assert "Speaking Session" in text  # headings and metadata are still there
    assert "English, Turkish" in text


@pytest.mark.parametrize("format_id", DOCUMENT_FORMATS)
def test_only_the_paragraph(session, tmp_path, format_id):
    options = ExportOptions(layout="paragraph", headings=False, metadata=())
    text = read_export(export_session(session, tmp_path, DEFAULT_TEMPLATE, format_id, options))
    assert " ".join(text.split()) == PARAGRAPH


def test_plain_text_paragraph_file_is_exactly_the_paragraph(session, tmp_path):
    options = ExportOptions(layout="paragraph", headings=False, metadata=())
    path = export_session(session, tmp_path, DEFAULT_TEMPLATE, "txt", options)
    assert path.read_text(encoding="utf-8") == PARAGRAPH + "\n"


@pytest.mark.parametrize("format_id", DOCUMENT_FORMATS)
def test_metadata_rows_can_be_left_out(session, tmp_path, format_id):
    options = ExportOptions(metadata=("date", "duration"))
    text = read_export(export_session(session, tmp_path, DEFAULT_TEMPLATE, format_id, options))
    assert "2026-10-03 14:30:00" in text and "00:05:24" in text
    assert "abc12345" not in text  # session id
    assert "Session ID" not in text and "Model" not in text
    assert "Languages:" not in text


@pytest.mark.parametrize("format_id", DOCUMENT_FORMATS)
def test_headings_can_be_left_out(session, tmp_path, format_id):
    options = ExportOptions(headings=False, language_headings=False, include_timestamps=False)
    text = read_export(export_session(session, tmp_path, DEFAULT_TEMPLATE, format_id, options))
    assert "Speaking Session" not in text
    assert "Transcript" not in text
    assert "### English" not in text and "[English]" not in text
    assert "Yesterday I went to the gym." in text
    assert "Session ID" in text  # metadata was not switched off


def test_metadata_order_is_fixed(session):
    document = build_document(session, ExportOptions(metadata=("model", "date")))
    assert [name for name, _ in document.metadata] == ["Date", "Model"]
    assert len(build_document(session).metadata) == len(METADATA_FIELDS)


def test_json_is_not_affected_by_document_options(session, tmp_path):
    options = ExportOptions(layout="paragraph", headings=False, metadata=())
    data = json.loads(export_session(session, tmp_path, DEFAULT_TEMPLATE, "json", options).read_text("utf-8"))
    assert len(data["segments"]) == 3 and data["session"]["id"] == "abc12345"


def test_settings_for_document_content_are_normalised(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "document_layout": "newspaper",
                "document_metadata": ["model", "bogus", "date", "date"],
                "dock_edge": "top",
                "global_hotkeys": "yes",
            }
        ),
        encoding="utf-8",
    )
    settings = SettingsManager(path).load()
    assert settings.document_layout == "lines"
    assert settings.document_metadata == ["date", "model"]
    assert settings.dock_edge == "right"
    assert settings.global_hotkeys is True


def test_empty_metadata_selection_is_kept(tmp_path):
    manager = SettingsManager(tmp_path / "settings.json")
    manager.save(Settings(document_metadata=[], document_layout="paragraph"))
    loaded = manager.load()
    assert loaded.document_metadata == [] and loaded.document_layout == "paragraph"


def test_controller_passes_document_options(qapp, tmp_path):
    settings = Settings(
        document_layout="paragraph",
        document_headings=False,
        language_headings=False,
        include_timestamps=False,
        document_metadata=["date"],
    )
    options = RecordingController(settings)._options()
    assert options == ExportOptions(
        include_timestamps=False,
        layout="paragraph",
        language_headings=False,
        headings=False,
        metadata=("date",),
    )


def test_content_panel_changes_settings_immediately(qapp, tmp_path, session):
    from app.main_window import MainWindow

    controller = RecordingController(Settings(save_directory=str(tmp_path)))
    window = MainWindow(controller, SettingsManager(tmp_path / "settings.json"))
    try:
        controller._on_recognized(list(session.segments), ["en", "tr"])
        assert "[00:00:00]" in window.transcript_view.toPlainText()
        window.show_content_panel()
        panel = window.content_panel
        assert panel.timestamps_check.isEnabled()

        panel.timestamps_check.setChecked(False)
        assert controller.settings.include_timestamps is False
        assert "[00:00:00]" not in window.transcript_view.toPlainText()  # preview follows

        panel.metadata_checks["session_id"].setChecked(False)
        panel.headings_check.setChecked(False)
        panel.paragraph_radio.setChecked(True)
        assert not panel.timestamps_check.isEnabled()  # meaningless in a paragraph
        assert not panel.language_check.isEnabled()

        saved = SettingsManager(tmp_path / "settings.json").load()
        assert saved.document_layout == "paragraph"
        assert saved.document_headings is False
        assert "session_id" not in saved.document_metadata
        panel.hide()
    finally:
        controller.discard_session()
        window.close()


def test_edge_bar_hides_at_the_edge_and_reports_clicks(qapp, tmp_path):
    from PySide6.QtGui import QGuiApplication

    from app.dock import STRIP, WIDTH, EdgeDock

    controller = RecordingController(Settings(save_directory=str(tmp_path)))
    screen = QGuiApplication.primaryScreen().availableGeometry()
    dock = EdgeDock(controller, "right")
    try:
        assert dock._position(expanded=False).x() == screen.right() + 1 - STRIP
        assert dock._position(expanded=True).x() == screen.right() + 1 - WIDTH
        dock.set_edge("left")
        assert dock._position(expanded=False).x() == screen.left() - (WIDTH - STRIP)
        assert dock._position(expanded=True).x() == screen.left()

        requests = []
        dock.start_requested.connect(lambda: requests.append("start"))
        dock.stop_requested.connect(lambda: requests.append("stop"))
        dock._toggle_recording()  # model not ready: nothing may happen
        controller.model_ready = True
        dock._toggle_recording()
        controller.state = AppState.RECORDING
        dock._on_state_changed(AppState.RECORDING)
        assert dock.state_label.text() == "Recording"
        dock._toggle_recording()
        assert requests == ["start", "stop"]
    finally:
        dock._clock.stop()
        controller.state = AppState.READY
        dock.close()


def test_toggle_recording_stops_when_recording(qapp, tmp_path, monkeypatch):
    from app.main_window import MainWindow

    controller = RecordingController(Settings(save_directory=str(tmp_path)))
    window = MainWindow(controller, SettingsManager(tmp_path / "settings.json"))
    calls = []
    monkeypatch.setattr(window, "start_recording", lambda: calls.append("start"))
    monkeypatch.setattr(window, "stop_recording", lambda: calls.append("stop"))
    try:
        window.toggle_recording()
        controller.state = AppState.RECORDING
        window.toggle_recording()
        assert calls == ["start", "stop"]
    finally:
        controller.state = AppState.READY
        window.close()


def test_second_instance_activates_the_first(qapp):
    from app.single_instance import InstanceServer, notify_running_instance

    server = InstanceServer()
    activations = []
    server.activation_requested.connect(lambda: activations.append(1))
    assert notify_running_instance() is True
    assert wait_until(lambda: activations == [1], timeout=3)
    server._server.close()
    assert notify_running_instance(timeout_ms=200) is False
