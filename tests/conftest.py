"""Shared test fixtures.

Tests never touch the real user profile: all application data is redirected
to a temporary folder, and Qt runs without a display.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.transcript_models import Session, TranscriptSegment  # noqa: E402

TURKISH_TEXT = "Sonra arkadaşımı gördüm. Çığlık, öğün, şişe, İstanbul, ILIK ığdır."


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXNOTE_HOME", str(tmp_path / "home"))
    yield tmp_path / "home"


@pytest.fixture
def session() -> Session:
    return Session(
        session_id="abc12345",
        started_at=datetime(2026, 10, 3, 14, 30, 0, tzinfo=timezone(timedelta(hours=3))),
        duration_seconds=324.0,
        languages=["en", "tr"],
        model="small",
        device="cpu",
        compute_type="int8",
        segments=[
            TranscriptSegment(0.0, 2.5, "en", "Yesterday I went to the gym.", 0.98),
            TranscriptSegment(2.5, 4.0, "tr", TURKISH_TEXT, 0.97),
            TranscriptSegment(4.0, 5.5, "en", "We talked for a while.", 0.99),
        ],
    )


@pytest.fixture
def empty_session() -> Session:
    return Session(
        session_id="empty000",
        started_at=datetime(2026, 10, 3, 9, 0, 0, tzinfo=timezone.utc),
        duration_seconds=12.0,
        model="small",
    )


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def wait_until(condition, timeout: float = 10.0) -> bool:
    """Process Qt events until ``condition()`` is true or time runs out."""
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False
