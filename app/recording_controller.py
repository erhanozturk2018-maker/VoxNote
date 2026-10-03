"""Application logic between the GUI and the engine.

The controller owns the state machine, the speech model and the current
session. It is the only place where recording, recognition and export are
started or stopped, which is what prevents duplicate sessions and invalid
state transitions.
"""

from __future__ import annotations

import logging
import queue
import time
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from app import paths
from app.audio_recorder import CAPTURE_QUEUE_BLOCKS, AudioError, AudioRecorder
from app.exporters import ExportOptions
from app.language_tracker import LanguageTracker
from app.session_journal import SessionJournal, delete_journal, find_journals, load_journal
from app.settings_manager import Settings
from app.transcriber import DeviceInfo, Transcriber
from app.transcript_models import Session
from app.vad_processor import SAMPLE_RATE, VadConfig
from app.workers import Backlog, CaptureWorker, ExportWorker, ModelLoadWorker, TranscribeWorker

log = logging.getLogger(__name__)


class AppState(Enum):
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"
    SAVING = "saving"
    COMPLETED = "completed"
    ERROR = "error"


# States in which no work is in progress.
IDLE_STATES = (AppState.READY, AppState.COMPLETED, AppState.ERROR)

_TRANSITIONS = {
    AppState.READY: {AppState.RECORDING, AppState.SAVING, AppState.ERROR},
    AppState.RECORDING: {AppState.PROCESSING, AppState.ERROR},
    AppState.PROCESSING: {AppState.SAVING, AppState.COMPLETED, AppState.ERROR},
    AppState.SAVING: {AppState.COMPLETED, AppState.ERROR},
    AppState.COMPLETED: {AppState.RECORDING, AppState.SAVING, AppState.READY, AppState.ERROR},
    AppState.ERROR: {AppState.RECORDING, AppState.SAVING, AppState.READY, AppState.ERROR},
}


class RecordingController(QObject):
    state_changed = Signal(object)  # AppState
    model_status = Signal(str)  # checking, downloading, initializing, ready, failed
    model_download_progress = Signal(int)  # megabytes
    model_failed = Signal(str, str)  # error code, detail
    device_changed = Signal(object)  # DeviceInfo
    segments_added = Signal(list)  # list[TranscriptSegment]
    languages_changed = Signal(list)  # list[str]
    session_reset = Signal()  # a new, empty session replaced the old one
    level = Signal(float)
    speech_active = Signal(bool)
    pending_changed = Signal(float)  # seconds of speech waiting for recognition
    notice = Signal(str)  # informational message code
    saved = Signal(str)  # path of the file that was written
    error = Signal(str, str)  # error code, technical detail

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.state = AppState.READY
        self.session = Session()
        self.saved_path: Path | None = None
        self.model_ready = False
        self.model_state = "idle"
        self.transcriber = Transcriber(settings.model, settings.device_preference)
        self.transcriber.on_device_changed = self._on_device_fallback
        self.started_monotonic = 0.0

        self._tracker = LanguageTracker()
        self._detector = None
        self._recorder: AudioRecorder | None = None
        self._capture: CaptureWorker | None = None
        self._transcribe: TranscribeWorker | None = None
        self._export: ExportWorker | None = None
        self._loader: ModelLoadWorker | None = None
        self._journal: SessionJournal | None = None
        self._journal_path: Path | None = None
        self._unsaved = False
        self._recovery_queue: list[Path] = []

    # -- state -----------------------------------------------------------

    @property
    def device_info(self) -> DeviceInfo | None:
        return self.transcriber.device_info

    @property
    def can_start(self) -> bool:
        return self.model_ready and self.state in IDLE_STATES

    @property
    def can_stop(self) -> bool:
        return self.state is AppState.RECORDING

    @property
    def is_busy(self) -> bool:
        return self.state not in IDLE_STATES

    @property
    def has_transcript(self) -> bool:
        return not self.session.is_empty

    @property
    def has_unsaved_transcript(self) -> bool:
        return self._unsaved and self.has_transcript

    def _set_state(self, state: AppState) -> None:
        if state is self.state:
            return
        if state not in _TRANSITIONS[self.state]:
            log.error("Invalid state transition %s -> %s ignored", self.state, state)
            return
        log.info("State: %s -> %s", self.state.value, state.value)
        self.state = state
        self.state_changed.emit(state)

    # -- model -----------------------------------------------------------

    def load_model(self) -> None:
        """Start loading the speech model in the background."""
        if self.model_ready or (self._loader and self._loader.is_running()):
            return
        self.model_state = "checking"
        loader = ModelLoadWorker(self.transcriber)
        loader.status.connect(self._on_model_status)
        loader.download_progress.connect(self.model_download_progress)
        loader.loaded.connect(self._on_model_loaded)
        loader.failed.connect(self._on_model_failed)
        self._loader = loader
        loader.start()

    def _on_model_status(self, code: str) -> None:
        self.model_state = code
        self.model_status.emit(code)

    def _on_model_loaded(self, info: DeviceInfo) -> None:
        if self._loader is not None and self._loader.detector is not None:
            self._detector = self._loader.detector
        self.model_ready = True
        self.model_state = "ready"
        self.model_status.emit("ready")
        self.device_changed.emit(info)
        self.state_changed.emit(self.state)

    def _on_model_failed(self, code: str, detail: str) -> None:
        self.model_ready = False
        self.model_state = "failed"
        self.model_status.emit("failed")
        self.model_failed.emit(code, detail)
        self.state_changed.emit(self.state)

    def _on_device_fallback(self, info: DeviceInfo) -> None:
        # Called from the transcription thread; signals cross threads safely.
        self.device_changed.emit(info)
        self.notice.emit("gpu_fallback")

    def apply_settings(self, settings: Settings) -> None:
        """Adopt new settings. Takes effect for the next recording."""
        reload_needed = (
            settings.device_preference != self.settings.device_preference
            or settings.model != self.settings.model
        )
        self.settings = settings
        if reload_needed and not self.is_busy:
            if self._loader and self._loader.is_running():
                return  # the running load finishes first; restart to apply
            self.transcriber.unload()
            self.transcriber.device_preference = settings.device_preference
            self.transcriber.model_name = settings.model
            self.model_state = "checking"
            self.model_ready = False
            self.state_changed.emit(self.state)
            self.load_model()

    # -- recording -------------------------------------------------------

    def start(self) -> bool:
        """Begin a new recording session. Returns ``False`` if not allowed."""
        if not self.can_start:
            log.info("Start ignored in state %s", self.state.value)
            return False

        self.discard_session()
        info = self.transcriber.device_info
        session = Session(
            model=self.transcriber.model_name,
            device=info.device if info else "",
            compute_type=info.compute_type if info else "",
        )
        self.session = session
        self.saved_path = None
        self._unsaved = False
        self._tracker.reset()
        self._tracker.allowed = frozenset(self.settings.spoken_languages)
        self.transcriber.vocabulary = self.settings.vocabulary
        self.session_reset.emit()

        blocks: queue.Queue = queue.Queue(maxsize=CAPTURE_QUEUE_BLOCKS)
        segments: queue.Queue = queue.Queue()
        backlog = Backlog()
        recorder = AudioRecorder(self.settings.microphone, blocks)
        try:
            recorder.start()
        except AudioError as exc:
            log.warning("Recording could not start: %s", exc)
            recorder.stop()
            self._set_state(AppState.ERROR)
            self.error.emit(exc.code, exc.detail)
            return False

        self._journal = SessionJournal(paths.journal_dir(), session)
        self._journal_path = self._journal.path

        audio_path = None
        if self.settings.retain_audio:
            stamp = session.started_at.strftime("%Y-%m-%d_%H-%M-%S")
            audio_path = paths.audio_dir() / f"{stamp}_{session.session_id}.wav"

        s = self.settings
        config = VadConfig(
            threshold=s.vad_threshold,
            min_speech_ms=s.min_speech_ms,
            silence_ms=s.silence_ms,
            max_segment_s=s.max_segment_s,
            pre_roll_ms=s.pre_roll_ms,
            post_roll_ms=s.post_roll_ms,
        )
        capture = CaptureWorker(
            recorder, blocks, segments, config, backlog, self._detector, audio_path
        )
        capture.level.connect(self.level)
        capture.speech_active.connect(self.speech_active)
        capture.notice.connect(self.notice)
        capture.stalled.connect(self._on_capture_stalled)
        capture.overloaded.connect(self._on_overloaded)
        capture.finished.connect(self._on_capture_finished)

        transcribe = TranscribeWorker(self.transcriber, segments, self._tracker, backlog)
        transcribe.recognized.connect(self._on_recognized)
        transcribe.pending.connect(self.pending_changed)
        transcribe.problem.connect(self._on_transcription_problem)
        transcribe.finished.connect(self._on_transcription_finished)

        self._recorder, self._capture, self._transcribe = recorder, capture, transcribe
        self.started_monotonic = time.monotonic()
        transcribe.start()
        capture.start()
        self._set_state(AppState.RECORDING)
        return True

    def stop(self) -> bool:
        """Stop capturing. Speech that is already buffered is still
        recognised and saved. Returns ``False`` if nothing was recording."""
        if not self.can_stop:
            log.info("Stop ignored in state %s", self.state.value)
            return False
        self._set_state(AppState.PROCESSING)
        if self._recorder is not None:
            self._recorder.stop()
        if self._capture is not None:
            self._capture.request_stop()
        return True

    def _on_capture_stalled(self) -> None:
        if self.state is AppState.RECORDING:
            self.notice.emit("microphone_disconnected")
            self.stop()

    def _on_overloaded(self) -> None:
        if self.state is AppState.RECORDING:
            self.notice.emit("backlog_limit")
            self.stop()

    def _on_capture_finished(self, samples: int) -> None:
        self.session.duration_seconds = samples / SAMPLE_RATE

    def _on_recognized(self, new_segments: list, languages: list) -> None:
        self.session.segments.extend(new_segments)
        self._unsaved = True
        if self._journal is not None:
            for segment in new_segments:
                self._journal.append(segment, languages)
        self.segments_added.emit(new_segments)
        if languages != self.session.languages:
            self.session.languages = list(languages)
            self.languages_changed.emit(list(languages))

    def _on_transcription_problem(self, code: str, detail: str) -> None:
        self.notice.emit("transcription_failed")

    def _on_transcription_finished(self) -> None:
        if self.state is AppState.RECORDING:
            # The worker ended on its own (it crashed); stop cleanly.
            self.stop()
        self._recorder = self._capture = self._transcribe = None
        if self._journal is not None:
            self._journal.close()
        if self.state is not AppState.PROCESSING:
            return
        if self.session.is_empty:
            self.discard_session()
            self._set_state(AppState.COMPLETED)
            self.notice.emit("no_speech")
            return
        self.save()

    # -- saving ----------------------------------------------------------

    def _options(self) -> ExportOptions:
        return ExportOptions(include_timestamps=self.settings.include_timestamps)

    def save(self) -> bool:
        """Export the current transcript using the configured folder,
        file name template and format."""
        if self.state in (AppState.RECORDING, AppState.SAVING) or not self.has_transcript:
            return False
        worker = ExportWorker(
            self.session,
            self.settings.export_format,
            self._options(),
            directory=self.settings.resolved_save_directory(),
            template=self.settings.filename_template,
        )
        return self._run_export(worker)

    def save_as(self, target: Path, format_id: str) -> bool:
        """Export the current transcript to an explicit file."""
        if self.is_busy or not self.has_transcript:
            return False
        return self._run_export(ExportWorker(self.session, format_id, self._options(), target=target))

    def _run_export(self, worker: ExportWorker) -> bool:
        worker.done.connect(self._on_saved)
        worker.failed.connect(self._on_save_failed)
        self._export = worker
        self._set_state(AppState.SAVING)
        worker.start()
        return True

    def _on_saved(self, path: str) -> None:
        self._export = None
        self.saved_path = Path(path)
        self._unsaved = False
        # The transcript is safely on disk; the recovery copy is obsolete.
        if self._journal_path is not None:
            delete_journal(self._journal_path)
            self._journal_path = None
        self._journal = None
        self._set_state(AppState.COMPLETED)
        self.saved.emit(path)
        self._recover_next()

    def _on_save_failed(self, code: str, detail: str) -> None:
        # The transcript stays in memory (and in the journal) so the user
        # can save it somewhere else.
        self._export = None
        self._recovery_queue.clear()
        log.warning("Saving failed: %s %s", code, detail)
        self._set_state(AppState.ERROR)
        self.error.emit(code, detail)

    def discard_session(self) -> None:
        """Forget the current transcript and its recovery journal."""
        if self._journal is not None:
            self._journal.close()
            self._journal = None
        if self._journal_path is not None:
            delete_journal(self._journal_path)
            self._journal_path = None
        self._unsaved = False

    # -- crash recovery --------------------------------------------------

    def recoverable_journals(self) -> list[Path]:
        """Journals left behind by sessions that were never exported."""
        if self.is_busy:
            return []
        return [path for path in find_journals(paths.journal_dir()) if path != self._journal_path]

    def recover(self, journals: list[Path]) -> None:
        """Load unsaved sessions one after another and export each."""
        self._recovery_queue = list(journals)
        self._recover_next()

    def discard_journals(self, journals: list[Path]) -> None:
        for path in journals:
            delete_journal(path)

    def _recover_next(self) -> None:
        while self._recovery_queue and not self.is_busy:
            path = self._recovery_queue.pop(0)
            session = load_journal(path)
            if session is None or session.is_empty:
                delete_journal(path)
                continue
            self.session = session
            self.saved_path = None
            self._journal = None
            self._journal_path = path
            self._unsaved = True
            self.session_reset.emit()
            self.segments_added.emit(list(session.segments))
            self.languages_changed.emit(list(session.languages))
            self.notice.emit("session_recovered")
            self.save()
            return

    # -- shutdown --------------------------------------------------------

    def shutdown(self) -> None:
        """Release the microphone. Called when the application exits."""
        if self._recorder is not None:
            self._recorder.stop()
        if self._capture is not None:
            self._capture.request_stop()
        if self._journal is not None:
            self._journal.close()
