"""Persistent user settings stored as a small JSON file."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from app import paths
from app.filename_template import DEFAULT_TEMPLATE, template_errors

log = logging.getLogger(__name__)

SETTINGS_SCHEMA_VERSION = 1
EXPORT_FORMATS = ("md", "txt", "json", "docx", "pdf")
UI_LANGUAGES = ("en", "tr", "de", "ru", "it", "fr")
DEVICE_PREFERENCES = ("auto", "cuda", "cpu")

# (minimum, maximum) for every numeric option; values outside are clamped.
LIMITS: dict[str, tuple[float, float]] = {
    "vad_threshold": (0.10, 0.95),
    "min_speech_ms": (50, 2000),
    "silence_ms": (200, 5000),
    "max_segment_s": (5, 30),
    "pre_roll_ms": (0, 1000),
    "post_roll_ms": (0, 1000),
}


@dataclass
class Settings:
    schema_version: int = SETTINGS_SCHEMA_VERSION
    # Interface language. Independent of the spoken language.
    ui_language: str = "en"
    # Empty means "use the default folder inside Documents".
    save_directory: str = ""
    export_format: str = "md"
    filename_template: str = DEFAULT_TEMPLATE
    include_timestamps: bool = True
    open_after_save: bool = False
    # Empty means "system default input device".
    microphone: str = ""
    # Speech probability above which a frame counts as speech.
    vad_threshold: float = 0.5
    # Segments containing less speech than this are discarded.
    min_speech_ms: int = 250
    # Silence that ends a segment. Shorter pauses stay inside the utterance.
    silence_ms: int = 800
    # A segment is cut when it reaches this length (Whisper window is 30 s).
    max_segment_s: int = 28
    # Audio kept before detected speech so the first syllable is not lost.
    pre_roll_ms: int = 300
    # Audio kept after detected speech so the last syllable is not lost.
    post_roll_ms: int = 300
    # "auto" uses the GPU when it works and falls back to the CPU.
    device_preference: str = "auto"
    # Debug option: keep the raw microphone audio of each session.
    retain_audio: bool = False

    def resolved_save_directory(self) -> Path:
        if self.save_directory.strip():
            return Path(self.save_directory).expanduser()
        return paths.default_save_dir()

    def normalized(self) -> "Settings":
        """Return a copy with every value forced into its valid range."""
        data = asdict(self)
        defaults = asdict(Settings())

        for key, default in defaults.items():
            value = data.get(key)
            if isinstance(default, bool):
                if not isinstance(value, bool):
                    data[key] = default
            elif isinstance(default, int):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    data[key] = default
                else:
                    data[key] = int(value)
            elif isinstance(default, float):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    data[key] = default
                else:
                    data[key] = float(value)
            elif not isinstance(value, str):
                data[key] = default

        for key, (low, high) in LIMITS.items():
            kind = type(defaults[key])
            data[key] = kind(min(max(data[key], low), high))

        if data["ui_language"] not in UI_LANGUAGES:
            data["ui_language"] = defaults["ui_language"]
        if data["export_format"] not in EXPORT_FORMATS:
            data["export_format"] = defaults["export_format"]
        if data["device_preference"] not in DEVICE_PREFERENCES:
            data["device_preference"] = defaults["device_preference"]
        if template_errors(data["filename_template"]):
            data["filename_template"] = defaults["filename_template"]
        data["schema_version"] = SETTINGS_SCHEMA_VERSION
        return Settings(**data)


class SettingsManager:
    """Loads and saves :class:`Settings`.

    A missing, unreadable or corrupt file never stops the application: the
    defaults are used and a corrupt file is kept next to the new one with a
    ``.corrupt`` suffix so nothing is destroyed silently.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or paths.settings_file()

    def load(self) -> Settings:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return Settings()
        except OSError as exc:
            log.warning("Settings file could not be read: %s", exc)
            return Settings()

        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("settings root is not an object")
        except ValueError as exc:
            log.warning("Settings file is corrupt, using defaults: %s", exc)
            self._preserve_corrupt_file()
            return Settings()

        known = {item.name for item in fields(Settings)}
        return Settings(**{k: v for k, v in data.items() if k in known}).normalized()

    def save(self, settings: Settings) -> None:
        """Write settings atomically. Raises ``OSError`` on failure."""
        settings = settings.normalized()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def _preserve_corrupt_file(self) -> None:
        try:
            os.replace(self.path, self.path.with_name(self.path.name + ".corrupt"))
        except OSError:
            pass
