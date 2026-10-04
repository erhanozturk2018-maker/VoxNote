"""Streaming voice activity detection.

Audio arrives in arbitrary block sizes. It is cut into fixed 32 ms frames,
each frame gets a speech probability from a detector, and a small state
machine groups frames into utterances:

* speech starts when the probability reaches the threshold; a short
  *pre-roll* of earlier audio is prepended so the first syllable survives,
* pauses shorter than the configured silence duration stay inside the
  utterance,
* the utterance ends after enough silence, keeping a short *post-roll*,
* utterances with too little speech are dropped,
* an utterance that approaches the maximum length is cut at the next short
  pause, or hard-cut at the maximum.

Emitted segments never overlap, so no audio is transcribed twice.

Only the active utterance and the pre-roll are kept in memory; silence is
discarded as it arrives.
"""

from __future__ import annotations

import glob
import logging
import os
from collections import deque
from dataclasses import dataclass
from typing import Callable

import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512  # 32 ms, the window size Silero VAD expects at 16 kHz
FRAME_MS = FRAME_SAMPLES * 1000 / SAMPLE_RATE
# Past this share of the maximum length the segment ends at any short pause.
SOFT_LIMIT_RATIO = 0.8
SOFT_LIMIT_SILENCE_MS = 200


@dataclass(frozen=True)
class VadConfig:
    threshold: float = 0.5
    min_speech_ms: int = 250
    silence_ms: int = 1200
    max_segment_s: float = 28.0
    pre_roll_ms: int = 300
    post_roll_ms: int = 300

    @property
    def release_threshold(self) -> float:
        """Probability below which a frame counts as silence (hysteresis)."""
        return max(self.threshold - 0.15, 0.01)


@dataclass(frozen=True)
class SpeechSegment:
    """A detected utterance. Sample positions are absolute within the session."""

    audio: np.ndarray
    start_sample: int
    end_sample: int

    @property
    def start_seconds(self) -> float:
        return self.start_sample / SAMPLE_RATE

    @property
    def duration_seconds(self) -> float:
        return (self.end_sample - self.start_sample) / SAMPLE_RATE


class SileroDetector:
    """Frame-by-frame speech probability from the Silero VAD ONNX model.

    The model file ships with faster-whisper and runs on the CPU through
    onnxruntime, so no additional download or PyTorch installation is needed.
    """

    CONTEXT_SAMPLES = 64

    def __init__(self) -> None:
        import importlib.util

        import onnxruntime

        # Locate the package without importing it: importing faster_whisper
        # pulls in the recognition engine, which the VAD does not need.
        spec = importlib.util.find_spec("faster_whisper")
        locations = list(spec.submodule_search_locations or []) if spec else []
        candidates = sorted(
            path
            for location in locations
            for path in glob.glob(os.path.join(location, "assets", "silero_vad*.onnx"))
        )
        if not candidates:
            raise FileNotFoundError("Silero VAD model not found in faster-whisper assets")

        options = onnxruntime.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        options.log_severity_level = 4
        self._session = onnxruntime.InferenceSession(
            candidates[-1], providers=["CPUExecutionProvider"], sess_options=options
        )
        names = {item.name for item in self._session.get_inputs()}
        if not {"input", "h", "c"} <= names:
            raise RuntimeError(f"Unsupported Silero VAD model inputs: {sorted(names)}")
        self.reset()

    def reset(self) -> None:
        self._h = np.zeros((1, 1, 128), dtype=np.float32)
        self._c = np.zeros((1, 1, 128), dtype=np.float32)
        self._context = np.zeros(self.CONTEXT_SAMPLES, dtype=np.float32)

    def __call__(self, frame: np.ndarray) -> float:
        window = np.concatenate((self._context, frame)).astype(np.float32, copy=False)
        output, self._h, self._c = self._session.run(
            None, {"input": window[np.newaxis, :], "h": self._h, "c": self._c}
        )
        self._context = frame[-self.CONTEXT_SAMPLES :].copy()
        return float(np.asarray(output).reshape(-1)[-1])


class EnergyDetector:
    """Fallback detector based on signal energy over an adaptive noise floor.

    Only used when the Silero model cannot be loaded. It is far less accurate
    in noisy rooms.
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._noise = 1e-4

    def __call__(self, frame: np.ndarray) -> float:
        rms = float(np.sqrt(np.mean(np.square(frame)))) if frame.size else 0.0
        if rms < self._noise * 2:
            self._noise = 0.95 * self._noise + 0.05 * max(rms, 1e-5)
        ratio = rms / max(self._noise * 4.0, 2e-3)
        return float(min(1.0, ratio / 2.0))


def create_detector() -> Callable[[np.ndarray], float]:
    try:
        return SileroDetector()
    except Exception:
        log.exception("Silero VAD unavailable, using the energy-based fallback")
        return EnergyDetector()


class VadProcessor:
    """Groups a stream of 16 kHz mono samples into speech segments."""

    def __init__(self, config: VadConfig, detector: Callable[[np.ndarray], float]) -> None:
        self.config = config
        self._detector = detector
        self._silence_frames = _frames(config.silence_ms, minimum=1)
        self._soft_silence_frames = min(
            self._silence_frames, _frames(SOFT_LIMIT_SILENCE_MS, minimum=1)
        )
        self._post_roll_frames = _frames(config.post_roll_ms)
        self._max_frames = max(1, int(config.max_segment_s * 1000 / FRAME_MS))
        self._soft_frames = int(self._max_frames * SOFT_LIMIT_RATIO)
        self._pre_roll: deque[tuple[int, np.ndarray]] = deque(maxlen=_frames(config.pre_roll_ms))
        self._pending = np.zeros(0, dtype=np.float32)
        self._position = 0  # absolute sample index of the next frame
        self._last_end = 0  # end of the last emitted segment
        self._frames: list[np.ndarray] = []
        self._segment_start = 0
        self._speech_frames = 0
        self._silence_run = 0
        self._triggered = False

    @property
    def in_speech(self) -> bool:
        return self._triggered

    @property
    def samples_seen(self) -> int:
        return self._position + len(self._pending)

    def process(self, samples: np.ndarray) -> list[SpeechSegment]:
        """Feed samples and return the segments completed by them."""
        if self._pending.size:
            samples = np.concatenate((self._pending, samples))
        usable = len(samples) - len(samples) % FRAME_SAMPLES
        self._pending = samples[usable:].copy()

        segments: list[SpeechSegment] = []
        for offset in range(0, usable, FRAME_SAMPLES):
            segment = self._process_frame(samples[offset : offset + FRAME_SAMPLES])
            if segment is not None:
                segments.append(segment)
        return segments

    def flush(self) -> list[SpeechSegment]:
        """Finish the stream: return the utterance in progress, if any."""
        segments: list[SpeechSegment] = []
        if self._pending.size:
            padded = np.zeros(FRAME_SAMPLES, dtype=np.float32)
            padded[: len(self._pending)] = self._pending
            self._pending = np.zeros(0, dtype=np.float32)
            segment = self._process_frame(padded)
            if segment is not None:
                segments.append(segment)
        if self._triggered:
            segment = self._finish(keep_frames=len(self._frames))
            if segment is not None:
                segments.append(segment)
        return segments

    def _process_frame(self, frame: np.ndarray) -> SpeechSegment | None:
        frame = np.ascontiguousarray(frame, dtype=np.float32)
        probability = self._detector(frame)
        start = self._position
        self._position += FRAME_SAMPLES

        if not self._triggered:
            if probability < self.config.threshold:
                if self._pre_roll.maxlen:
                    self._pre_roll.append((start, frame))
                return None
            self._triggered = True
            # Pre-roll never reaches back into audio that was already emitted.
            lead = [(pos, data) for pos, data in self._pre_roll if pos >= self._last_end]
            self._pre_roll.clear()
            self._segment_start = lead[0][0] if lead else start
            self._frames = [data for _, data in lead] + [frame]
            self._speech_frames = 1
            self._silence_run = 0
            return None

        self._frames.append(frame)
        if probability >= self.config.threshold:
            self._speech_frames += 1
            self._silence_run = 0
        elif probability < self.config.release_threshold or self._silence_run:
            self._silence_run += 1

        needed = (
            self._soft_silence_frames
            if len(self._frames) >= self._soft_frames
            else self._silence_frames
        )
        if self._silence_run >= needed:
            trailing = self._silence_run - min(self._silence_run, self._post_roll_frames)
            return self._finish(keep_frames=len(self._frames) - trailing)
        if len(self._frames) >= self._max_frames:
            return self._finish(keep_frames=len(self._frames))
        return None

    def _finish(self, keep_frames: int) -> SpeechSegment | None:
        frames = self._frames
        kept, dropped = frames[:keep_frames], frames[keep_frames:]
        enough_speech = self._speech_frames * FRAME_MS >= self.config.min_speech_ms
        start = self._segment_start
        end = start + len(kept) * FRAME_SAMPLES

        self._frames = []
        self._triggered = False
        self._speech_frames = 0
        self._silence_run = 0

        if not enough_speech or not kept:
            return None

        self._last_end = end
        # Trailing silence that was cut off may serve as pre-roll for the
        # next utterance; it lies after ``_last_end`` so nothing overlaps.
        if self._pre_roll.maxlen:
            for index, data in enumerate(dropped):
                self._pre_roll.append((end + index * FRAME_SAMPLES, data))
        return SpeechSegment(np.concatenate(kept), start, end)


def _frames(milliseconds: float, minimum: int = 0) -> int:
    return max(minimum, int(round(milliseconds / FRAME_MS)))
