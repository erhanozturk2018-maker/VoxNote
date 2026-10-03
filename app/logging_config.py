"""Application logging.

Logs are diagnostic only. Transcript text and microphone audio are never
written to the log; modules log durations, counts and error details instead.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app import APP_NAME, APP_VERSION
from app import paths

LOG_FILE_NAME = "voxnote.log"
_FORMAT = "%(asctime)s %(levelname)-7s %(name)s [%(threadName)s] %(message)s"


def log_file() -> Path:
    return paths.log_dir() / LOG_FILE_NAME


def setup_logging(level: int = logging.INFO) -> Path | None:
    """Configure the root logger. Returns the log file path if it is usable."""
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(_FORMAT)
    target: Path | None = log_file()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            target, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # A read-only profile must not prevent the application from starting.
        target = None

    if sys.stderr is not None:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        root.addHandler(console)

    # Third-party libraries are noisy at INFO level.
    for name in ("faster_whisper", "httpx", "httpcore", "huggingface_hub", "PIL"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "%s %s starting (Python %s, %s)",
        APP_NAME,
        APP_VERSION,
        sys.version.split()[0],
        sys.platform,
    )
    return target


def install_excepthook() -> None:
    """Send uncaught exceptions to the log instead of losing them."""
    log = logging.getLogger("app.unhandled")

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("Unhandled exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = hook
