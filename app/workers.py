"""Background workers.

Everything that can block runs here, never on the GUI thread:

* :class:`ModelLoadWorker` downloads and initialises the speech model,
* :class:`CaptureWorker` turns raw microphone blocks into speech segments,
* :class:`TranscribeWorker` recognises the segments,
* :class:`ExportWorker` writes the transcript file.

Each worker is a ``QObject`` that lives in the GUI thread and runs its
``run`` method on a daemon thread. Results travel back as Qt signals, which
Qt delivers on the GUI thread, so no widget is ever touched from a worker.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
import wave
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, Signal

from app.audio_recorder import AudioRecorder, Resampler
from app.export_manager import ExportError, export_session, export_to_path
from app.exporters import ExportOptions
from app.language_tracker import LanguageTracker
from app.transcriber import Transcriber, TranscriberError
from app.transcript_models import Session, TranscriptSegment
from app.vad_processor import SAMPLE_RATE, SpeechSegment, VadConfig, VadProcessor, create_detector

log = logging.getLogger(__name__)

# Upper bound for speech that is waiting to be recognised. Recognition is
# normally faster than real time; on a slow CPU it may fall behind. When the
# backlog reaches this limit recording stops automatically, so memory stays
# bounded (20 min of 16 kHz float32 audio is about 77 MB) and nothing that
# was captured is thrown away.
MAX_BACKLOG_SECONDS = 20 * 60
# No audio for this long while the stream is open means the device is gone.
STALL_SECONDS = 3.0
LEVEL_INTERVAL = 0.066
SILENT_INPUT_SECONDS = 3.0


class Backlog:
    """Thread-safe counter of speech seconds waiting for recognition."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seconds = 0.0

    def add(self, seconds: float) -> float:
        with self._lock:
            self._seconds = max(0.0, self._seconds + seconds)
            return self._seconds

    @property
    def seconds(self) -> float:
        with self._lock:
            return self._seconds


class Worker(QObject):
    """Runs :meth:`run` on a daemon thread."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._guarded, name=self._name, daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    def _guarded(self) -> None:
        try:
            self.run()
        except Exception:
            log.exception("Worker %s crashed", self._name)
            self.crashed()

    def run(self) -> None:
        raise NotImplementedError

    def crashed(self) -> None:
        """Called when ``run`` raised; subclasses emit their failure signal."""


class ModelLoadWorker(Worker):
    status = Signal(str)  # "checking", "downloading", "initializing"
    download_progress = Signal(int)  # megabytes on disk so far
    loaded = Signal(object)  # DeviceInfo
    failed = Signal(str, str)  # error code, technical detail

    def __init__(self, transcriber: Transcriber) -> None:
        super().__init__("model-loader")
        self._transcriber = transcriber
        self._downloading = threading.Event()
        self.detector = None

    def run(self) -> None:
        try:
            info = self._transcriber.load(self._on_status)
        except TranscriberError as exc:
            self._downloading.clear()
            self.failed.emit(exc.code, exc.detail)
            return
        # Load the VAD model here as well so the first recording starts
        # without a delay.
        self.detector = create_detector()
        self.loaded.emit(info)

    def crashed(self) -> None:
        self._downloading.clear()
        self.failed.emit("model_load_failed", "")

    def _on_status(self, code: str) -> None:
        self.status.emit(code)
        if code == "downloading":
            self._downloading.set()
            threading.Thread(target=self._watch_download, daemon=True).start()
        else:
            self._downloading.clear()

    def _watch_download(self) -> None:
        """Report how much of the model has arrived on disk."""
        try:
            from huggingface_hub.constants import HF_HUB_CACHE
        except Exception:
            return
        cache = Path(HF_HUB_CACHE)
        baseline = _directory_bytes(cache)
        while self._downloading.is_set():
            time.sleep(1.0)
            done = max(0, _directory_bytes(cache) - baseline)
            self.download_progress.emit(int(done / 1_000_000))


def _directory_bytes(directory: Path, follow_links: bool = False) -> int:
    """Total size of the files below ``directory``.

    The model hub cache stores each file once and links to it; links are
    skipped unless ``follow_links`` is set so nothing is counted twice.
    """
    total = 0
    try:
        for path in directory.rglob("*"):
            try:
                if path.is_file() and (follow_links or not path.is_symlink()):
                    total += path.stat().st_size
            except OSError:
                continue
    except OSError:
        pass
    return total


class CaptureWorker(Worker):
    """Consumes microphone blocks and produces speech segments."""

    level = Signal(float)  # peak amplitude 0..1 of the latest audio
    speech_active = Signal(bool)
    notice = Signal(str)  # "silent_input", "audio_dropped"
    stalled = Signal()  # the microphone stopped delivering audio
    overloaded = Signal()  # recognition backlog limit reached
    finished = Signal(int)  # total number of 16 kHz samples captured

    def __init__(
        self,
        recorder: AudioRecorder,
        blocks: "queue.Queue[np.ndarray]",
        segments: "queue.Queue[SpeechSegment | None]",
        config: VadConfig,
        backlog: Backlog,
        detector=None,
        audio_path: Path | None = None,
    ) -> None:
        super().__init__("capture")
        self._recorder = recorder
        self._blocks = blocks
        self._segments = segments
        self._config = config
        self._backlog = backlog
        self._detector = detector
        self._audio_path = audio_path
        self._stop = threading.Event()
        self._samples = 0
        self._done = False

    def request_stop(self) -> None:
        """Finish after the audio that is already queued has been processed."""
        self._stop.set()

    def crashed(self) -> None:
        self._finish()

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        # ``finished`` is emitted before the end marker is queued so the GUI
        # learns the duration before the transcription worker can finish.
        self.finished.emit(self._samples)
        self._segments.put(None)

    def run(self) -> None:
        detector = self._detector or create_detector()
        if hasattr(detector, "reset"):
            detector.reset()
        vad = VadProcessor(self._config, detector)
        resampler = Resampler(self._recorder.sample_rate)
        writer = self._open_writer()

        last_block = time.monotonic()
        last_level = 0.0
        peak_since_start = 0.0
        was_speaking = False
        warned_silent = warned_dropped = reported_stall = reported_overload = False

        try:
            while True:
                try:
                    block = self._blocks.get(timeout=0.1)
                except queue.Empty:
                    if self._stop.is_set():
                        break
                    gone = self._recorder.aborted.is_set()
                    if not reported_stall and (
                        gone or time.monotonic() - last_block > STALL_SECONDS
                    ):
                        reported_stall = True
                        log.warning("Microphone stopped delivering audio")
                        self.stalled.emit()
                    continue

                now = time.monotonic()
                last_block = now
                samples = resampler.process(block)
                if samples.size == 0:
                    continue
                self._samples += len(samples)
                if writer is not None:
                    pcm = np.clip(samples, -1.0, 1.0) * 32767.0
                    writer.writeframes(pcm.astype("<i2").tobytes())

                peak = float(np.max(np.abs(samples)))
                peak_since_start = max(peak_since_start, peak)
                if now - last_level >= LEVEL_INTERVAL:
                    last_level = now
                    self.level.emit(min(1.0, peak))

                if (
                    not warned_silent
                    and peak_since_start == 0.0
                    and self._samples > SILENT_INPUT_SECONDS * SAMPLE_RATE
                ):
                    warned_silent = True
                    self.notice.emit("silent_input")
                if not warned_dropped and self._recorder.dropped_blocks:
                    warned_dropped = True
                    log.warning("Audio blocks were dropped because the capture queue was full")
                    self.notice.emit("audio_dropped")

                for segment in vad.process(samples):
                    waiting = self._push(segment)
                    if waiting > MAX_BACKLOG_SECONDS and not reported_overload:
                        reported_overload = True
                        log.warning("Recognition backlog limit reached (%.0f s)", waiting)
                        self.overloaded.emit()
                if vad.in_speech != was_speaking:
                    was_speaking = vad.in_speech
                    self.speech_active.emit(was_speaking)

            # Recording stopped: the utterance in progress is still valid.
            for segment in vad.flush():
                self._push(segment)
        finally:
            if writer is not None:
                try:
                    writer.close()
                except Exception:
                    log.exception("Closing the debug audio file failed")
            self.level.emit(0.0)
            self.speech_active.emit(False)
            log.info("Capture finished: %.1f s of audio", self._samples / SAMPLE_RATE)
            self._finish()

    def _push(self, segment: SpeechSegment) -> float:
        waiting = self._backlog.add(segment.duration_seconds)
        self._segments.put(segment)
        return waiting

    def _open_writer(self):
        if self._audio_path is None:
            return None
        try:
            self._audio_path.parent.mkdir(parents=True, exist_ok=True)
            writer = wave.open(str(self._audio_path), "wb")
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(SAMPLE_RATE)
            return writer
        except Exception:
            log.exception("Debug audio file could not be created")
            return None


class TranscribeWorker(Worker):
    """Recognises speech segments in the order they were spoken."""

    # (list[TranscriptSegment], list[str]) - new segments and all languages
    recognized = Signal(list, list)
    pending = Signal(float)  # seconds of speech still waiting
    problem = Signal(str, str)  # error code, technical detail
    finished = Signal()

    def __init__(
        self,
        transcriber: Transcriber,
        segments: "queue.Queue[SpeechSegment | None]",
        tracker: LanguageTracker,
        backlog: Backlog,
    ) -> None:
        super().__init__("transcribe")
        self._transcriber = transcriber
        self._segments = segments
        self._tracker = tracker
        self._backlog = backlog

    def crashed(self) -> None:
        self.finished.emit()

    def run(self) -> None:
        audio_total = 0.0
        work_total = 0.0
        count = 0
        reported_problem = False
        # Language and text of the previous utterance, passed on as context.
        context = ("", "")
        while True:
            segment = self._segments.get()
            if segment is None:
                break
            try:
                result = self._transcriber.transcribe(segment.audio, self._tracker, context)
            except Exception as exc:
                # One bad utterance must not end the session.
                log.exception("Transcription of one segment failed")
                if not reported_problem:
                    reported_problem = True
                    code = exc.code if isinstance(exc, TranscriberError) else "transcription_failed"
                    self.problem.emit(code, str(exc))
                self.pending.emit(self._backlog.add(-segment.duration_seconds))
                continue

            count += 1
            audio_total += segment.duration_seconds
            work_total += result.seconds
            log.info(
                "Segment %d: %.2f s of audio recognised in %.2f s (%d piece(s))",
                count,
                segment.duration_seconds,
                result.seconds,
                len(result.pieces),
            )
            self.pending.emit(self._backlog.add(-segment.duration_seconds))
            if result.decision is None or not result.pieces:
                continue

            self._tracker.record(result.decision)
            context = (result.decision.language, " ".join(p.text for p in result.pieces))
            offset = segment.start_seconds
            new_segments = [
                TranscriptSegment(
                    start=offset + piece.start,
                    end=offset + piece.end,
                    language=result.decision.language,
                    text=piece.text,
                    language_probability=result.decision.probability,
                )
                for piece in result.pieces
            ]
            self.recognized.emit(new_segments, list(self._tracker.languages))

        if work_total > 0:
            log.info(
                "Session recognition: %d segment(s), %.1f s of speech in %.1f s "
                "(real-time factor %.2f)",
                count,
                audio_total,
                work_total,
                work_total / max(audio_total, 1e-6),
            )
        self.finished.emit()


class ExportWorker(Worker):
    done = Signal(str)  # path of the written file
    failed = Signal(str, str)  # error code, technical detail

    def __init__(
        self,
        session: Session,
        format_id: str,
        options: ExportOptions,
        directory: Path | None = None,
        template: str = "",
        target: Path | None = None,
    ) -> None:
        super().__init__("export")
        self._session = session
        self._format_id = format_id
        self._options = options
        self._directory = directory
        self._template = template
        self._target = target

    def crashed(self) -> None:
        self.failed.emit("export_failed", "")

    def run(self) -> None:
        try:
            if self._target is not None:
                path = export_to_path(self._session, self._target, self._format_id, self._options)
            else:
                path = export_session(
                    self._session,
                    self._directory,
                    self._template,
                    self._format_id,
                    self._options,
                )
        except ExportError as exc:
            self.failed.emit(exc.code, exc.detail)
            return
        self.done.emit(str(path))
