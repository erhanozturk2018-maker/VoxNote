"""Persistent user settings stored as a small JSON file."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from app import DEFAULT_MODEL, MODELS, paths
from app.language_names import LANGUAGE_NAMES
from app.filename_template import DEFAULT_TEMPLATE, template_errors

log = logging.getLogger(__name__)

SETTINGS_SCHEMA_VERSION = 1
EXPORT_FORMATS = ("md", "txt", "json", "docx", "pdf")
UI_LANGUAGES = ("en", "tr", "de", "ru", "it", "fr")
DEVICE_PREFERENCES = ("auto", "cuda", "cpu")
THEMES = ("system", "light", "dark")
DOCK_EDGES = ("off", "left", "right")

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
    # Appearance: follow the operating system, or force light or dark.
    theme: str = "system"
    # Whether the short introduction was shown on first start.
    tutorial_seen: bool = False
    # Empty means "use the default folder inside Documents".
    save_directory: str = ""
    export_format: str = "md"
    filename_template: str = DEFAULT_TEMPLATE
    include_timestamps: bool = True
    # "lines" (one entry per sentence) or "paragraph" (one continuous text).
    document_layout: str = "lines"
    # Language headings between sentences of different languages.
    language_headings: bool = True
    # Document title and "Transcript" heading.
    document_headings: bool = True
    # Metadata rows written into documents.
    document_metadata: list[str] = field(
        default_factory=lambda: ["date", "languages", "duration", "session_id", "model"]
    )
    # Floating bar at the screen edge: "off", "left" or "right".
    dock_edge: str = "right"
    # Ctrl+Alt+R starts and stops recording from any application.
    global_hotkeys: bool = True
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
    # Whisper model used for recognition; one of ``app.MODELS``.
    model: str = DEFAULT_MODEL
    # Languages recognition is limited to. Empty means every language.
    spoken_languages: list[str] = field(default_factory=list)
    # Comma separated names and terms recognition should favour.
    vocabulary: str = ""
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
            if isinstance(default, list):
                items = value if isinstance(value, list) else default
                data[key] = list(dict.fromkeys(item for item in items if isinstance(item, str)))
            elif isinstance(default, bool):
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
        if data["document_layout"] not in ("lines", "paragraph"):
            data["document_layout"] = defaults["document_layout"]
        allowed_fields = ("date", "languages", "duration", "session_id", "model")
        data["document_metadata"] = [f for f in allowed_fields if f in data["document_metadata"]]
        if data["dock_edge"] not in DOCK_EDGES:
            data["dock_edge"] = defaults["dock_edge"]
        if data["theme"] not in THEMES:
            data["theme"] = defaults["theme"]
        if data["model"] not in MODELS:
            data["model"] = defaults["model"]
        data["spoken_languages"] = [c for c in data["spoken_languages"] if c in LANGUAGE_NAMES]
        data["vocabulary"] = " ".join(data["vocabulary"].split())[:500]
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
