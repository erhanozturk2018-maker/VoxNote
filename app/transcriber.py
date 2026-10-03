"""Local speech recognition with faster-whisper.

The model is loaded once and reused for every utterance and every session.
Each utterance gets its own language detection, so a speaker can switch
languages between utterances. Recognition always runs with
``task="transcribe"``: the text is never translated or post-processed.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from app import DEFAULT_MODEL, MODELS
from app.language_tracker import LanguageDecision, LanguageTracker

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
# Free disk space required before a model download is attempted, on top of
# the size of the model itself. The margin covers temporary files.
FREE_SPACE_MARGIN_BYTES = 500_000_000

# A recognised piece is dropped only when the model itself reports that it
# probably heard no speech *and* is unsure about the text, or when the text
# is a degenerate repetition. These are Whisper's standard guard values.
NO_SPEECH_PROBABILITY = 0.6
LOW_CONFIDENCE_LOGPROB = -1.0
MAX_COMPRESSION_RATIO = 2.4


class TranscriberError(Exception):
    """A model problem. ``code`` selects the localized message."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class DeviceInfo:
    device: str  # "cuda" or "cpu"
    compute_type: str
    # Why the GPU is not used, as a machine-readable code, or "" if it is.
    fallback_reason: str = ""


@dataclass(frozen=True)
class RecognizedPiece:
    start: float  # seconds from the start of the utterance
    end: float
    text: str


@dataclass
class UtteranceResult:
    decision: LanguageDecision | None
    pieces: list[RecognizedPiece] = field(default_factory=list)
    seconds: float = 0.0  # time spent recognising


def register_nvidia_libraries() -> list[str]:
    """Make the cuBLAS/cuDNN DLLs from the NVIDIA pip wheels loadable.

    The wheels unpack their DLLs into ``site-packages/nvidia/*/bin``, which
    is not on the Windows DLL search path. Without this step CTranslate2
    cannot find them and GPU inference fails. The full CUDA Toolkit is not
    required.
    """
    if sys.platform != "win32":
        return []
    added: list[str] = []
    roots = [Path(entry) / "nvidia" for entry in sys.path if entry]
    # PyInstaller bundles place the DLLs next to the executable.
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        roots.append(Path(bundle) / "nvidia")
    for root in roots:
        if not root.is_dir():
            continue
        for bin_dir in root.glob("*/bin"):
            path = str(bin_dir)
            if path in added:
                continue
            try:
                os.add_dll_directory(path)
            except OSError:
                continue
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            added.append(path)
    return added


def import_engine() -> None:
    """Import the recognition engine, translating failures into error codes.

    Windows Smart App Control and similar application control policies can
    refuse to load unsigned native libraries. That surfaces as an
    ``ImportError`` and is reported separately because the remedy differs
    from a broken installation.
    """
    try:
        import ctranslate2  # noqa: F401
        import faster_whisper  # noqa: F401
    except Exception as exc:
        log.exception("Speech recognition engine could not be imported")
        # 4551 = ERROR_SYSTEM_INTEGRITY_POLICY_VIOLATION
        if getattr(exc, "winerror", None) == 4551:
            raise TranscriberError("engine_blocked_by_policy", str(exc)) from exc
        raise TranscriberError("engine_import_failed", str(exc)) from exc


def is_out_of_memory(error: BaseException) -> bool:
    text = str(error).lower()
    return "out of memory" in text or "cuda_error_out_of_memory" in text


class Transcriber:
    """Owns the Whisper model."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device_preference: str = "auto") -> None:
        self.model_name = model_name
        # Optional names and terms that recognition should favour. Passed to
        # the decoder as a hint; the transcript is never edited afterwards.
        self.vocabulary = ""
        self.device_preference = device_preference
        self.device_info: DeviceInfo | None = None
        self.model_path: Path | None = None
        self._model = None
        self._lock = threading.Lock()
        # Called with the new DeviceInfo when a GPU failure forces the CPU.
        self.on_device_changed: Callable[[DeviceInfo], None] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    # -- loading ---------------------------------------------------------

    def cached_model_path(self) -> Path | None:
        """Return the local model folder without touching the network."""
        try:
            from faster_whisper.utils import download_model

            return Path(download_model(self.model_name, local_files_only=True))
        except Exception:
            return None

    def load(self, status: Callable[[str], None] | None = None) -> DeviceInfo:
        """Download (first run only) and initialise the model.

        ``status`` receives ``"checking"``, ``"downloading"`` and
        ``"initializing"``. Raises :class:`TranscriberError` on failure.
        """
        notify = status or (lambda _code: None)
        with self._lock:
            if self._model is not None and self.device_info is not None:
                return self.device_info

            # No telemetry is sent by the model hub client.
            os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
            started = time.perf_counter()
            notify("checking")
            # Must happen before the engine is imported so its GPU libraries
            # are found.
            register_nvidia_libraries()
            import_engine()
            path = self.cached_model_path()
            if path is None:
                notify("downloading")
                path = self._download()
            self.model_path = path

            notify("initializing")
            self._model, self.device_info = self._create_model(self.device_preference)
            log.info(
                "Model '%s' ready on %s (%s) after %.1f s",
                self.model_name,
                self.device_info.device,
                self.device_info.compute_type,
                time.perf_counter() - started,
            )
            return self.device_info

    def _download(self) -> Path:
        from faster_whisper.utils import download_model
        from huggingface_hub.constants import HF_HUB_CACHE

        cache = Path(HF_HUB_CACHE)
        try:
            cache.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(cache).free
        except OSError as exc:
            raise TranscriberError("model_cache_unwritable", str(exc)) from exc
        required = MODELS.get(self.model_name, 2000) * 1_000_000 + FREE_SPACE_MARGIN_BYTES
        if free < required:
            raise TranscriberError("no_disk_space", f"{free // 1_000_000} MB free in {cache}")

        log.info("Downloading model '%s' to %s", self.model_name, cache)
        try:
            return Path(download_model(self.model_name))
        except OSError as exc:
            if getattr(exc, "errno", None) == 28:  # ENOSPC
                raise TranscriberError("no_disk_space", str(exc)) from exc
            log.exception("Model download failed")
            raise TranscriberError("model_download_failed", str(exc)) from exc
        except Exception as exc:
            log.exception("Model download failed")
            raise TranscriberError("model_download_failed", str(exc)) from exc

    def _candidates(self, preference: str) -> tuple[list[tuple[str, str]], str]:
        """Return (device, compute type) pairs to try, best first."""
        import ctranslate2

        candidates: list[tuple[str, str]] = []
        reason = ""
        if preference in ("auto", "cuda"):
            try:
                gpu_count = ctranslate2.get_cuda_device_count()
            except Exception:
                gpu_count = 0
            if gpu_count > 0:
                supported = ctranslate2.get_supported_compute_types("cuda")
                for compute_type in ("float16", "int8_float16", "float32"):
                    if compute_type in supported:
                        candidates.append(("cuda", compute_type))
                if not candidates:
                    reason = "cuda_unsupported_compute_type"
            else:
                reason = "cuda_unavailable"
        else:
            reason = "cpu_selected"

        cpu_supported = ctranslate2.get_supported_compute_types("cpu")
        for compute_type in ("int8", "float32"):
            if compute_type in cpu_supported:
                candidates.append(("cpu", compute_type))
                break
        else:
            candidates.append(("cpu", "default"))
        return candidates, reason

    def _create_model(self, preference: str):
        from faster_whisper import WhisperModel

        candidates, reason = self._candidates(preference)
        last_error: Exception | None = None
        for device, compute_type in candidates:
            try:
                model = WhisperModel(str(self.model_path), device=device, compute_type=compute_type)
                # A model can load although the GPU libraries are missing;
                # the failure only shows on first use. Run one tiny inference
                # so problems surface here, where falling back is possible.
                silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
                segments, _ = model.transcribe(silence, language="en", beam_size=1)
                list(segments)
            except Exception as exc:
                last_error = exc
                log.warning("Model init failed on %s/%s: %s", device, compute_type, exc)
                if device == "cuda":
                    reason = "cuda_out_of_memory" if is_out_of_memory(exc) else "cuda_init_failed"
                continue
            return model, DeviceInfo(device, compute_type, "" if device == "cuda" else reason)
        raise TranscriberError("model_load_failed", str(last_error))

    def unload(self) -> None:
        with self._lock:
            self._model = None
            self.device_info = None
            self.model_path = None

    # -- recognition -----------------------------------------------------

    def transcribe(self, audio: np.ndarray, tracker: LanguageTracker) -> UtteranceResult:
        """Recognise one utterance of 16 kHz mono float32 audio.

        The tracker decides the language but is not updated here; the caller
        records the decision once it knows the utterance produced text.
        """
        with self._lock:
            if self._model is None:
                raise TranscriberError("model_not_loaded")
            started = time.perf_counter()
            try:
                result = self._recognize(audio, tracker)
            except RuntimeError as exc:
                if self.device_info is None or self.device_info.device != "cuda":
                    raise
                # GPU failure in the middle of a session (typically another
                # program took the VRAM). Continue on the CPU and retry.
                reason = "cuda_out_of_memory" if is_out_of_memory(exc) else "cuda_runtime_error"
                log.warning("GPU inference failed (%s), switching to CPU: %s", reason, exc)
                self._model = None
                model, info = self._create_model("cpu")
                self._model = model
                self.device_info = DeviceInfo(info.device, info.compute_type, reason)
                if self.on_device_changed:
                    self.on_device_changed(self.device_info)
                result = self._recognize(audio, tracker)
            result.seconds = time.perf_counter() - started
            return result

    def _recognize(self, audio: np.ndarray, tracker: LanguageTracker) -> UtteranceResult:
        model = self._model
        duration = len(audio) / SAMPLE_RATE
        _, _, probabilities = model.detect_language(audio)
        decision = tracker.decide(probabilities or [], duration)
        if decision is None:
            return UtteranceResult(None)

        segments, _info = model.transcribe(
            audio,
            language=decision.language,
            task="transcribe",
            beam_size=5,
            # Each utterance is decoded on its own. Feeding earlier text back
            # in is what makes Whisper repeat itself and drift between
            # languages, and it would bias the next utterance's language.
            condition_on_previous_text=False,
            # Speech was already isolated by the streaming VAD.
            vad_filter=False,
            no_speech_threshold=NO_SPEECH_PROBABILITY,
            log_prob_threshold=LOW_CONFIDENCE_LOGPROB,
            compression_ratio_threshold=MAX_COMPRESSION_RATIO,
            hotwords=self.vocabulary.strip() or None,
        )

        result = UtteranceResult(decision)
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            if (
                segment.no_speech_prob > NO_SPEECH_PROBABILITY
                and segment.avg_logprob < LOW_CONFIDENCE_LOGPROB
            ):
                continue
            if segment.compression_ratio > MAX_COMPRESSION_RATIO:
                continue
            start = min(max(float(segment.start), 0.0), duration)
            end = min(max(float(segment.end), start), duration)
            result.pieces.append(RecognizedPiece(start, end, text))
        return result
