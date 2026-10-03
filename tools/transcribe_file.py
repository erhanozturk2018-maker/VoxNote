"""Run a WAV file through the same pipeline the application uses.

This is a diagnostic tool for developers. It feeds the file through the
resampler, the streaming VAD, the language tracker and the recogniser in
small blocks, exactly as microphone audio would arrive, and prints the
resulting segments with timing information.

    python tools/transcribe_file.py path/to/audio.wav [--device auto|cuda|cpu]

Only uncompressed 16-bit PCM WAV files are supported.
"""

from __future__ import annotations

import argparse
import sys
import time
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import MODEL_NAME  # noqa: E402
from app.audio_recorder import Resampler  # noqa: E402
from app.language_names import language_list, language_name  # noqa: E402
from app.language_tracker import LanguageTracker  # noqa: E402
from app.transcriber import Transcriber  # noqa: E402
from app.transcript_models import format_clock  # noqa: E402
from app.vad_processor import VadConfig, VadProcessor, create_detector  # noqa: E402


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        if handle.getsampwidth() != 2:
            raise SystemExit("Only 16-bit PCM WAV files are supported.")
        rate = handle.getframerate()
        channels = handle.getnchannels()
        data = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16)
    audio = data.astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio, rate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("wav", type=Path)
    parser.add_argument("--device", default="auto", choices=("auto", "cuda", "cpu"))
    parser.add_argument("--silence-ms", type=int, default=VadConfig.silence_ms)
    args = parser.parse_args()

    audio, rate = read_wav(args.wav)
    print(f"Input: {len(audio) / rate:.1f} s at {rate} Hz")

    transcriber = Transcriber(MODEL_NAME, args.device)
    started = time.perf_counter()
    info = transcriber.load(lambda code: print(f"Model: {code}"))
    print(
        f"Model ready in {time.perf_counter() - started:.1f} s on "
        f"{info.device} ({info.compute_type}) {info.fallback_reason}"
    )

    resampler = Resampler(rate)
    vad = VadProcessor(VadConfig(silence_ms=args.silence_ms), create_detector())
    tracker = LanguageTracker()
    block = max(1, rate // 20)
    segments = []
    for offset in range(0, len(audio), block):
        segments.extend(vad.process(resampler.process(audio[offset : offset + block])))
    segments.extend(vad.flush())
    print(f"VAD found {len(segments)} speech segment(s)")

    for segment in segments:
        result = transcriber.transcribe(segment.audio, tracker)
        if result.decision is None or not result.pieces:
            print(f"[{format_clock(segment.start_seconds)}] (no text, {result.seconds:.2f} s)")
            continue
        tracker.record(result.decision)
        text = " ".join(piece.text for piece in result.pieces)
        print(
            f"[{format_clock(segment.start_seconds)}] "
            f"{language_name(result.decision.language)} "
            f"p={result.decision.probability:.2f} "
            f"{'confident' if result.decision.confident else 'tentative'} "
            f"audio={segment.duration_seconds:.1f}s took={result.seconds:.2f}s: {text}"
        )
    print(f"Languages: {language_list(tracker.languages) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
