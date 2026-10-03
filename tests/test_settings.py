import json
from dataclasses import asdict

from app import paths
from app.filename_template import DEFAULT_TEMPLATE
from app.settings_manager import LIMITS, SETTINGS_SCHEMA_VERSION, Settings, SettingsManager


def test_defaults_when_file_is_missing(tmp_path):
    settings = SettingsManager(tmp_path / "settings.json").load()
    assert settings == Settings()
    assert settings.ui_language == "en"
    assert settings.export_format == "md"
    assert settings.retain_audio is False


def test_round_trip(tmp_path):
    manager = SettingsManager(tmp_path / "nested" / "settings.json")
    original = Settings(
        ui_language="tr",
        save_directory=str(tmp_path / "Çıktı klasörü"),
        export_format="pdf",
        filename_template="{session_id}_{date}",
        include_timestamps=False,
        open_after_save=True,
        microphone="USB Mikrofon (Ğ)",
        vad_threshold=0.65,
        silence_ms=1200,
        device_preference="cpu",
        retain_audio=True,
    )
    manager.save(original)
    assert manager.load() == original


def test_file_is_utf8_json_with_schema_version(tmp_path):
    path = tmp_path / "settings.json"
    SettingsManager(path).save(Settings(microphone="Mikrofon ğüşiöç"))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == SETTINGS_SCHEMA_VERSION
    assert data["microphone"] == "Mikrofon ğüşiöç"
    assert set(data) == set(asdict(Settings()))


def test_no_temporary_file_is_left_behind(tmp_path):
    SettingsManager(tmp_path / "settings.json").save(Settings())
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_corrupt_file_falls_back_to_defaults_and_is_preserved(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ this is not json", encoding="utf-8")
    assert SettingsManager(path).load() == Settings()
    assert (tmp_path / "settings.json.corrupt").exists()


def test_non_object_json_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert SettingsManager(path).load() == Settings()


def test_unknown_keys_are_ignored_and_missing_keys_use_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"export_format": "docx", "future_option": 1}), encoding="utf-8")
    settings = SettingsManager(path).load()
    assert settings.export_format == "docx"
    assert settings.silence_ms == Settings().silence_ms


def test_invalid_values_are_normalised(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "ui_language": "xx",
                "export_format": "exe",
                "device_preference": "quantum",
                "filename_template": "{bad}",
                "vad_threshold": 7,
                "silence_ms": -5,
                "max_segment_s": "long",
                "retain_audio": "yes",
                "microphone": 42,
            }
        ),
        encoding="utf-8",
    )
    settings = SettingsManager(path).load()
    assert settings.ui_language == "en"
    assert settings.export_format == "md"
    assert settings.device_preference == "auto"
    assert settings.filename_template == DEFAULT_TEMPLATE
    assert settings.vad_threshold == LIMITS["vad_threshold"][1]
    assert settings.silence_ms == LIMITS["silence_ms"][0]
    assert settings.max_segment_s == Settings().max_segment_s
    assert settings.retain_audio is False
    assert settings.microphone == ""


def test_default_save_directory_is_inside_documents():
    settings = Settings()
    assert settings.resolved_save_directory() == paths.default_save_dir()
    assert settings.resolved_save_directory().name == "VoxNote"


def test_custom_save_directory(tmp_path):
    assert Settings(save_directory=str(tmp_path)).resolved_save_directory() == tmp_path


def test_application_data_respects_override(isolated_home):
    assert paths.settings_file() == isolated_home / "config" / "settings.json"
    assert paths.log_dir() == isolated_home / "data" / "logs"
    assert paths.journal_dir() == isolated_home / "data" / "sessions"
