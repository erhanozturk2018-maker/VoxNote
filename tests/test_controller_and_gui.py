"""Controller and window tests that need neither a microphone nor the model.

Recognition results are injected through the same slot the transcription
worker uses, so the save, failure and recovery paths run for real.
"""

import json
from pathlib import Path

import pytest

from app import i18n, paths
from app.exporters import EXPORTERS
from app.recording_controller import AppState, RecordingController
from app.session_journal import SessionJournal, find_journals
from app.settings_manager import Settings, SettingsManager
from app.transcriber import DeviceInfo
from app.transcript_models import Session
from tests.conftest import wait_until


@pytest.fixture(autouse=True)
def english():
    i18n.set_language("en")
    yield
    i18n.set_language("en")


def make_controller(tmp_path, **overrides) -> RecordingController:
    settings = Settings(save_directory=str(tmp_path / "out"), **overrides)
    return RecordingController(settings)


def begin_fake_session(controller, session) -> None:
    """Put the controller where it is after the user pressed Stop."""
    controller.session = Session(session_id=session.session_id, started_at=session.started_at)
    controller._journal = SessionJournal(paths.journal_dir(), controller.session)
    controller._journal_path = controller._journal.path
    controller.state = AppState.PROCESSING
    controller._on_recognized(list(session.segments), ["en", "tr"])
    controller._on_capture_finished(int(session.duration_seconds * 16000))


def test_cannot_start_before_the_model_is_ready(qapp, tmp_path):
    controller = make_controller(tmp_path)
    assert controller.can_start is False
    assert controller.start() is False
    assert controller.stop() is False
    assert controller.state is AppState.READY


def test_invalid_state_transition_is_ignored(qapp, tmp_path):
    controller = make_controller(tmp_path)
    controller._set_state(AppState.PROCESSING)  # READY -> PROCESSING is not allowed
    assert controller.state is AppState.READY


def test_session_is_saved_automatically_and_journal_removed(qapp, tmp_path, session):
    controller = make_controller(tmp_path, export_format="json")
    saved = []
    controller.saved.connect(saved.append)
    begin_fake_session(controller, session)
    assert len(find_journals(paths.journal_dir())) == 1

    controller._on_transcription_finished()
    assert wait_until(lambda: controller.state is AppState.COMPLETED)
    path = Path(saved[0])
    assert path == controller.saved_path and path.parent == tmp_path / "out"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["session"]["languages"] == ["en", "tr"]
    assert document["session"]["duration_seconds"] == session.duration_seconds
    assert len(document["segments"]) == 3
    assert controller.has_unsaved_transcript is False
    assert find_journals(paths.journal_dir()) == []


def test_empty_session_creates_no_file(qapp, tmp_path, empty_session):
    controller = make_controller(tmp_path)
    notices = []
    controller.notice.connect(notices.append)
    controller.session = empty_session
    controller.state = AppState.PROCESSING
    controller._on_transcription_finished()
    assert controller.state is AppState.COMPLETED
    assert notices == ["no_speech"]
    assert not (tmp_path / "out").exists()


def test_failed_save_keeps_transcript_and_allows_saving_elsewhere(qapp, tmp_path, session):
    blocker = tmp_path / "blocked"
    blocker.write_text("this is a file, not a folder")
    controller = RecordingController(Settings(save_directory=str(blocker)))
    errors, saved = [], []
    controller.error.connect(lambda code, detail: errors.append(code))
    controller.saved.connect(saved.append)
    begin_fake_session(controller, session)

    controller._on_transcription_finished()
    assert wait_until(lambda: controller.state is AppState.ERROR)
    assert errors == ["directory_invalid"]
    assert saved == []
    # Nothing is lost: the transcript is in memory and in the journal.
    assert controller.has_unsaved_transcript
    assert len(controller.session.segments) == 3
    assert len(find_journals(paths.journal_dir())) == 1

    target = tmp_path / "elsewhere" / "rescued.txt"
    target.parent.mkdir()
    assert controller.save_as(target, "txt")
    assert wait_until(lambda: controller.state is AppState.COMPLETED)
    assert "Yesterday I went to the gym." in target.read_text(encoding="utf-8")
    assert controller.has_unsaved_transcript is False
    assert find_journals(paths.journal_dir()) == []


def test_recovery_after_crash(qapp, tmp_path, session):
    # A previous run wrote a journal and then died.
    journal = SessionJournal(paths.journal_dir(), session)
    for segment in session.segments:
        journal.append(segment, ["en", "tr"])
    journal.close()

    controller = make_controller(tmp_path, export_format="md")
    journals = controller.recoverable_journals()
    assert journals == [journal.path]
    controller.recover(journals)
    assert wait_until(lambda: controller.state is AppState.COMPLETED)
    text = controller.saved_path.read_text(encoding="utf-8")
    assert "Yesterday I went to the gym." in text and "English, Turkish" in text
    assert controller.recoverable_journals() == []


def test_discarding_recovery_journals(qapp, tmp_path, session):
    journal = SessionJournal(paths.journal_dir(), session)
    journal.append(session.segments[0], ["en"])
    journal.close()
    controller = make_controller(tmp_path)
    controller.discard_journals(controller.recoverable_journals())
    assert controller.recoverable_journals() == []


def make_window(controller, tmp_path):
    from app.main_window import MainWindow

    return MainWindow(controller, SettingsManager(tmp_path / "settings.json"))


def test_main_window_controls_follow_state(qapp, tmp_path, session):
    controller = make_controller(tmp_path)
    window = make_window(controller, tmp_path)
    try:
        # Model not loaded: recording cannot start.
        assert not window.start_button.isEnabled()
        assert not window.stop_button.isEnabled()
        assert not window.save_as_button.isEnabled()
        assert not window.copy_button.isEnabled()
        assert window.status_pill.text() == "Ready"

        controller.transcriber.device_info = DeviceInfo("cpu", "int8", "cuda_unavailable")
        controller._on_model_loaded(controller.transcriber.device_info)
        assert window.start_button.isEnabled()
        assert "CPU (int8)" in window.model_label.text()

        controller.state = AppState.RECORDING
        controller.state_changed.emit(AppState.RECORDING)
        assert not window.start_button.isEnabled()
        assert window.stop_button.isEnabled()
        assert not window.mic_combo.isEnabled()
        assert not window.settings_button.isEnabled()
        assert window.status_pill.text() == "Recording"
        window._timer.stop()

        controller._on_recognized(list(session.segments), ["en", "tr"])
        text = window.transcript_view.toPlainText()
        assert "Yesterday I went to the gym." in text and "arkadaşımı" in text
        assert text.count("English") == 2 and text.count("Turkish") == 1
        assert window.languages_label.text() == "English, Turkish"
        assert "en-tr" in window.filename_hint.text()

        controller.state = AppState.ERROR
        controller.state_changed.emit(AppState.ERROR)
        assert window.save_button.isVisibleTo(window) and window.save_as_button.isEnabled()
        assert not window.result_banner.buttons
        assert window.copy_button.isEnabled()
    finally:
        controller.discard_session()
        controller.state = AppState.READY
        window.close()


def test_main_window_retranslates(qapp, tmp_path):
    controller = make_controller(tmp_path)
    window = make_window(controller, tmp_path)
    try:
        assert "Start Recording" in window.start_button.text()
        i18n.set_language("tr")
        window.retranslate()
        assert "Kaydı Başlat" in window.start_button.text()
        assert window.status_pill.text() == "Hazır"
        i18n.set_language("de")
        window.retranslate()
        assert "Aufnahme starten" in window.start_button.text()
    finally:
        window.close()


def test_main_window_persists_quick_changes(qapp, tmp_path):
    controller = make_controller(tmp_path)
    window = make_window(controller, tmp_path)
    try:
        index = window.format_combo.findData("pdf")
        window.format_combo.setCurrentIndex(index)
        window._on_format_selected(index)
        assert SettingsManager(tmp_path / "settings.json").load().export_format == "pdf"
        assert window.filename_hint.text().endswith(".pdf")
    finally:
        window.close()


def test_format_combo_lists_every_exporter(qapp, tmp_path):
    window = make_window(make_controller(tmp_path), tmp_path)
    try:
        listed = [window.format_combo.itemData(i) for i in range(window.format_combo.count())]
        assert listed == list(EXPORTERS)
    finally:
        window.close()


def test_settings_dialog_round_trip_and_validation(qapp, tmp_path):
    from app.settings_dialog import SettingsDialog

    controller = make_controller(tmp_path)
    (tmp_path / "out").mkdir()
    dialog = SettingsDialog(controller.settings, controller)
    try:
        assert dialog.save_button.isEnabled()
        assert dialog.template_preview.text().endswith(".md")

        dialog.template_edit.setText("{nope}")
        assert not dialog.save_button.isEnabled()
        assert "Unknown placeholder" in dialog.template_error.text()

        dialog.template_edit.setText("talk_{session_id}")
        assert dialog.save_button.isEnabled()
        dialog.format_combo.setCurrentIndex(dialog.format_combo.findData("docx"))
        assert dialog.template_preview.text().endswith(".docx")
        dialog.silence_spin.setValue(1500)
        dialog.language_combo.setCurrentIndex(dialog.language_combo.findData("de"))
        dialog.model_combo.setCurrentIndex(dialog.model_combo.findData("small"))
        dialog._spoken = ["en", "tr"]
        dialog.vocabulary_edit.setText("  Gesi,   Erhan ")
        dialog.retain_check.setChecked(True)
        dialog._accept()

        result = dialog.result_settings()
        assert result.filename_template == "talk_{session_id}"
        assert result.export_format == "docx"
        assert result.silence_ms == 1500
        assert result.ui_language == "de"
        assert result.model == "small"
        assert result.spoken_languages == ["en", "tr"]
        assert result.vocabulary == "Gesi, Erhan"
        assert result.retain_audio is True
        assert result.save_directory == str(tmp_path / "out")
        # The dialog does not modify the live settings object.
        assert controller.settings.export_format == "md"
    finally:
        dialog.close()


def test_settings_dialog_restore_defaults_only_fills_the_form(qapp, tmp_path):
    from app.settings_dialog import SettingsDialog

    controller = make_controller(tmp_path, silence_ms=2000, export_format="pdf")
    dialog = SettingsDialog(controller.settings, controller)
    try:
        dialog._restore_defaults()
        assert dialog.silence_spin.value() == Settings().silence_ms
        assert dialog.format_combo.currentData() == "md"
        dialog.reject()
        assert controller.settings.silence_ms == 2000
        assert controller.settings.export_format == "pdf"
    finally:
        dialog.close()


def test_settings_dialog_rejects_unwritable_folder(qapp, tmp_path):
    from app.settings_dialog import SettingsDialog

    blocker = tmp_path / "file.txt"
    blocker.write_text("x")
    controller = make_controller(tmp_path)
    dialog = SettingsDialog(controller.settings, controller)
    try:
        dialog.folder_edit.setText(str(blocker))
        dialog._accept()
        assert dialog.result() != SettingsDialog.DialogCode.Accepted
        assert dialog.folder_error.text()
    finally:
        dialog.close()


def test_saved_message_offers_to_open_the_file(qapp, tmp_path, session):
    controller = make_controller(tmp_path)
    window = make_window(controller, tmp_path)
    try:
        window._on_saved(str(tmp_path / "x.md"))
        assert [button.text().strip() for button in window.result_banner.buttons] == [
            "Open File",
            "Open Folder",
        ]
        # The actions follow the interface language.
        i18n.set_language("de")
        window.retranslate()
        assert window.result_banner.buttons[0].text().strip() == "Datei öffnen"
    finally:
        window.close()


def test_settings_dialog_height_follows_the_visible_tab(qapp, tmp_path):
    from app.settings_dialog import SettingsDialog

    dialog = SettingsDialog(Settings(save_directory=str(tmp_path)), make_controller(tmp_path))
    try:
        dialog.tabs.setCurrentIndex(2)
        collapsed = dialog.height()
        dialog.advanced_toggle.setChecked(True)
        assert dialog.height() > collapsed
        dialog.advanced_toggle.setChecked(False)
        assert dialog.height() == collapsed
    finally:
        dialog.close()


def test_language_chooser(qapp):
    from PySide6.QtCore import Qt

    from app.settings_dialog import LanguageChooser

    chooser = LanguageChooser(["tr", "en"])
    try:
        assert chooser.selected() == ["en", "tr"]
        assert chooser.list.item(0).text() == "English"
        chooser.filter_edit.setText("germ")
        visible = [
            chooser.list.item(i).text()
            for i in range(chooser.list.count())
            if not chooser.list.item(i).isHidden()
        ]
        assert visible == ["German"]
        chooser.list.item(2).setCheckState(Qt.CheckState.Checked)
        assert chooser.selected() == ["en", "tr", "de"]
        chooser._clear()
        assert chooser.selected() == []
    finally:
        chooser.close()


def test_help_dialog_shows_questions_and_about(qapp):
    from app import APP_VERSION
    from app.help_dialog import HelpDialog, faq_entries

    assert len(faq_entries()) >= 8
    dialog = HelpDialog()
    try:
        text = dialog.faq_view.toPlainText()
        assert "Do I need an internet connection?" in text
        assert dialog.tabs.count() == 2
        about = dialog.tabs.widget(1)
        from PySide6.QtWidgets import QLabel

        labels = " ".join(label.text() for label in about.findChildren(QLabel))
        assert APP_VERSION in labels and "MIT" in labels
    finally:
        dialog.close()


def test_every_icon_renders(qapp):
    from app.icons import _SHAPES, pixmap

    for name in _SHAPES:
        image = pixmap(name, "#000000", 18).toImage()
        assert not image.isNull()
        assert any(
            image.pixelColor(x, y).alpha() > 0
            for x in range(0, image.width(), 3)
            for y in range(0, image.height(), 3)
        ), name