"""Tests for the VAD state machine using a scripted detector.

The audio samples carry a marker value so the tests can tell exactly which
frames ended up in which segment.
"""

import numpy as np

from app.audio_recorder import Resampler
from app.vad_processor import FRAME_MS, FRAME_SAMPLES, SAMPLE_RATE, VadConfig, VadProcessor


class ScriptedDetector:
    """Returns a pre-defined probability for each successive frame."""

    def __init__(self, probabilities):
        self.probabilities = list(probabilities)
        self.calls = 0

    def __call__(self, frame):
        value = self.probabilities[self.calls] if self.calls < len(self.probabilities) else 0.0
        self.calls += 1
        return value


def frames_for(milliseconds):
    return int(round(milliseconds / FRAME_MS))


def run(pattern, config=None, block=FRAME_SAMPLES, flush=True):
    """``pattern`` is a list of (probability, frame_count) runs."""
    probabilities = [p for p, count in pattern for _ in range(count)]
    audio = np.repeat(np.arange(len(probabilities), dtype=np.float32), FRAME_SAMPLES)
    vad = VadProcessor(config or VadConfig(), ScriptedDetector(probabilities))
    segments = []
    for offset in range(0, len(audio), block):
        segments += vad.process(audio[offset : offset + block])
    if flush:
        segments += vad.flush()
    return segments, vad


def frame_indices(segment):
    return [int(value) for value in segment.audio[::FRAME_SAMPLES]]


CONFIG = VadConfig(
    threshold=0.5, min_speech_ms=96, silence_ms=320, max_segment_s=10, pre_roll_ms=64, post_roll_ms=64
)


def test_silence_produces_no_segments():
    segments, vad = run([(0.0, 200)], CONFIG)
    assert segments == []
    assert vad.samples_seen == 200 * FRAME_SAMPLES


def test_single_utterance_with_pre_and_post_roll():
    segments, _ = run([(0.0, 20), (0.9, 30), (0.0, 40)], CONFIG)
    assert len(segments) == 1
    indices = frame_indices(segments[0])
    # 2 frames of pre-roll, 30 frames of speech, 2 frames of post-roll.
    assert indices == list(range(18, 52))
    assert segments[0].start_sample == 18 * FRAME_SAMPLES
    assert segments[0].end_sample == 52 * FRAME_SAMPLES
    assert segments[0].start_seconds == 18 * FRAME_SAMPLES / SAMPLE_RATE


def test_short_pause_stays_inside_the_utterance():
    pause = frames_for(CONFIG.silence_ms) - 2
    segments, _ = run([(0.0, 10), (0.9, 20), (0.0, pause), (0.9, 20), (0.0, 40)], CONFIG)
    assert len(segments) == 1


def test_long_pause_splits_into_two_utterances():
    pause = frames_for(CONFIG.silence_ms) + 5
    segments, _ = run([(0.0, 10), (0.9, 20), (0.0, pause), (0.9, 20), (0.0, 40)], CONFIG)
    assert len(segments) == 2


def test_segments_never_overlap():
    pause = frames_for(CONFIG.silence_ms)
    segments, _ = run(
        [(0.0, 5), (0.9, 20), (0.0, pause), (0.9, 20), (0.0, pause), (0.9, 20), (0.0, 30)], CONFIG
    )
    assert len(segments) == 3
    seen = []
    for segment in segments:
        seen += frame_indices(segment)
    assert len(seen) == len(set(seen)), "a frame was emitted twice"
    assert seen == sorted(seen)
    for earlier, later in zip(segments, segments[1:]):
        assert earlier.end_sample <= later.start_sample


def test_too_short_sound_is_ignored():
    segments, _ = run([(0.0, 10), (0.9, 2), (0.0, 40)], CONFIG)
    assert segments == []


def test_intermediate_probability_does_not_start_speech():
    # Between the release threshold (0.35) and the threshold (0.5).
    segments, _ = run([(0.45, 100)], CONFIG)
    assert segments == []


def test_hysteresis_keeps_utterance_alive():
    # Probability dips below the threshold but not below the release level.
    segments, _ = run([(0.9, 10), (0.4, 60), (0.9, 10), (0.0, 30)], CONFIG)
    assert len(segments) == 1
    assert len(frame_indices(segments[0])) >= 80


def test_flush_returns_utterance_in_progress():
    segments, vad = run([(0.0, 5), (0.9, 30)], CONFIG, flush=False)
    assert segments == [] and vad.in_speech
    flushed = vad.flush()
    assert len(flushed) == 1
    assert frame_indices(flushed[0])[-1] == 34
    assert vad.flush() == []


def test_flush_processes_partial_final_frame():
    vad = VadProcessor(CONFIG, ScriptedDetector([0.9] * 50))
    audio = np.ones(10 * FRAME_SAMPLES + 100, dtype=np.float32)
    assert vad.process(audio) == []
    flushed = vad.flush()
    assert len(flushed) == 1
    assert len(flushed[0].audio) == 11 * FRAME_SAMPLES


def test_maximum_length_forces_a_cut_without_losing_audio():
    config = VadConfig(min_speech_ms=96, silence_ms=320, max_segment_s=2, pre_roll_ms=0, post_roll_ms=0)
    total = 200
    segments, _ = run([(0.9, total)], config)
    max_frames = int(2 * 1000 / FRAME_MS)
    assert all(len(frame_indices(s)) <= max_frames for s in segments)
    seen = [index for segment in segments for index in frame_indices(segment)]
    assert seen == list(range(total)), "continuous speech must be kept completely"


def test_long_utterance_is_cut_at_a_short_pause_near_the_limit():
    config = VadConfig(min_speech_ms=96, silence_ms=800, max_segment_s=4, pre_roll_ms=0, post_roll_ms=0)
    max_frames = int(4 * 1000 / FRAME_MS)
    soft = int(max_frames * 0.8)
    # A 256 ms pause (shorter than silence_ms) right after the soft limit.
    segments, _ = run([(0.9, soft + 2), (0.0, 8), (0.9, 20), (0.0, 40)], config)
    assert len(segments) == 2
    assert len(frame_indices(segments[0])) < max_frames


def test_block_size_does_not_change_the_result():
    pattern = [(0.0, 12), (0.9, 25), (0.0, 30), (0.9, 15), (0.0, 30)]
    reference, _ = run(pattern, CONFIG, block=FRAME_SAMPLES)
    for block in (160, 441, 1000, 4096):
        segments, _ = run(pattern, CONFIG, block=block)
        assert [(s.start_sample, s.end_sample) for s in segments] == [
            (s.start_sample, s.end_sample) for s in reference
        ]


def test_resampler_output_length_and_continuity():
    for rate in (44100, 48000, 22050, 8000):
        resampler = Resampler(rate)
        seconds = 2
        tone = np.sin(2 * np.pi * 440 * np.arange(rate * seconds) / rate).astype(np.float32)
        chunks = [resampler.process(tone[i : i + 1024]) for i in range(0, len(tone), 1024)]
        output = np.concatenate(chunks)
        assert abs(len(output) - SAMPLE_RATE * seconds) <= 2, rate
        assert output.dtype == np.float32
        # A 440 Hz tone must keep its level and have no clicks at block edges.
        steady = output[2000:-2000]
        assert 0.9 < np.max(np.abs(steady)) < 1.1
        assert np.max(np.abs(np.diff(steady))) < 0.25


def test_resampler_is_transparent_at_16_khz():
    block = np.random.default_rng(0).standard_normal(1000).astype(np.float32)
    assert Resampler(16000).process(block) is block
