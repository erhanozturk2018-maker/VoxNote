"""Decoding options of the transcriber, checked with a stand-in model."""

from types import SimpleNamespace

import numpy as np

from app.language_tracker import LanguageTracker
from app.transcriber import CONTEXT_CHARACTERS, Transcriber


class FakeModel:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def detect_language(self, audio):
        return "en", 0.99, [("en", 0.99), ("tr", 0.01)]

    def transcribe(self, audio, **options):
        self.calls.append(options)
        return iter(self.outputs.pop(0)), None


def piece(text, no_speech=0.0, logprob=-0.2, ratio=1.2, start=0.0, end=1.0):
    return SimpleNamespace(
        text=text, no_speech_prob=no_speech, avg_logprob=logprob, compression_ratio=ratio, start=start, end=end
    )


def run(outputs, keep_uncertain=True, context=("", ""), vocabulary=""):
    transcriber = Transcriber("small", "cpu")
    transcriber._model = FakeModel(outputs)
    transcriber.keep_uncertain = keep_uncertain
    transcriber.vocabulary = vocabulary
    result = transcriber._recognize(np.zeros(32000, dtype=np.float32), LanguageTracker(), context)
    return result, transcriber._model.calls


UNSURE = piece(" vigidi vigidi", no_speech=0.9, logprob=-1.6)


def test_uncertain_speech_is_kept_by_default():
    result, calls = run([[piece(" Hello there."), UNSURE]])
    assert [p.text for p in result.pieces] == ["Hello there.", "vigidi vigidi"]
    assert calls[0]["no_speech_threshold"] is None  # the recogniser skips nothing either
    assert calls[0]["task"] == "transcribe" and calls[0]["temperature"] == 0.0


def test_uncertain_speech_is_dropped_in_strict_mode():
    result, calls = run([[piece(" Hello there."), UNSURE, piece(" la la la", ratio=3.0)]], keep_uncertain=False)
    assert [p.text for p in result.pieces] == ["Hello there."]
    assert calls[0]["no_speech_threshold"] == 0.6


def test_previous_utterance_is_passed_as_context_in_the_same_language():
    _, calls = run([[piece(" and then we left.")]], context=("en", "We waited for an hour"))
    assert calls[0]["initial_prompt"] == "We waited for an hour"
    assert calls[0]["condition_on_previous_text"] is False


def test_context_from_another_language_is_not_used():
    _, calls = run([[piece(" Hello.")]], context=("tr", "Sonra eve gittik"))
    assert calls[0]["initial_prompt"] is None


def test_context_is_limited_in_length():
    _, calls = run([[piece(" ok")]], context=("en", "x" * 1000))
    assert len(calls[0]["initial_prompt"]) == CONTEXT_CHARACTERS


def test_looping_result_is_decoded_again_without_context():
    looping = [piece(" again again again again", ratio=4.0)]
    clean = [piece(" Something else entirely.")]
    result, calls = run([looping, clean], context=("en", "again"))
    assert [p.text for p in result.pieces] == ["Something else entirely."]
    assert len(calls) == 2 and calls[1]["initial_prompt"] is None


def test_vocabulary_is_passed_as_punctuated_hint():
    _, calls = run([[piece(" ok")]], vocabulary=" Gesi ,Erhan.,, ")
    assert calls[0]["hotwords"] == "Gesi, Erhan."
    _, calls = run([[piece(" ok")]])
    assert calls[0]["hotwords"] is None
