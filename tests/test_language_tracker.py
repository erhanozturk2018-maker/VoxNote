from app.language_names import language_list, language_name
from app.language_tracker import LanguageTracker


def decide_and_record(tracker, probabilities, duration=3.0):
    decision = tracker.decide(probabilities, duration)
    tracker.record(decision)
    return decision


def test_single_language():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("en", 0.98), ("tr", 0.01)])
    decide_and_record(tracker, [("en", 0.95), ("de", 0.02)])
    assert tracker.languages == ["en"]


def test_languages_are_deduplicated_and_ordered_by_first_occurrence():
    tracker = LanguageTracker()
    for top in ("en", "tr", "en", "tr", "de", "en"):
        decide_and_record(tracker, [(top, 0.97), ("xx", 0.01)])
    assert tracker.languages == ["en", "tr", "de"]


def test_unsorted_probabilities_are_handled():
    tracker = LanguageTracker()
    decision = tracker.decide([("tr", 0.02), ("en", 0.9), ("de", 0.05)], 3.0)
    assert (decision.language, decision.confident) == ("en", True)


def test_empty_probabilities():
    assert LanguageTracker().decide([], 3.0) is None


def test_decide_does_not_record():
    tracker = LanguageTracker()
    tracker.decide([("en", 0.99)], 3.0)
    assert tracker.languages == []


def test_low_confidence_sticks_to_known_plausible_language():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("en", 0.99)])
    # A new language barely ahead of the one already in use: no switch.
    decision = decide_and_record(tracker, [("cy", 0.40), ("en", 0.30)])
    assert decision.language == "en"
    assert decision.confident is False
    assert tracker.languages == ["en"]


def test_low_confidence_does_not_force_an_implausible_language():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("en", 0.99)])
    # English is not plausible here, so it must not be forced: decoding in
    # the wrong language would make the recogniser translate.
    decision = decide_and_record(tracker, [("tr", 0.60), ("en", 0.02)])
    assert decision.language == "tr"
    assert decision.confident is False


def test_short_utterance_needs_higher_probability():
    tracker = LanguageTracker()
    assert tracker.decide([("en", 0.80)], duration_seconds=0.8).confident is False
    assert tracker.decide([("en", 0.80)], duration_seconds=3.0).confident is True
    assert tracker.decide([("en", 0.95)], duration_seconds=0.8).confident is True


def test_confident_languages_come_before_tentative_ones():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("cy", 0.40), ("nn", 0.30)])  # tentative
    decide_and_record(tracker, [("en", 0.99)])  # confident
    assert tracker.languages == ["en", "cy"]


def test_tentative_language_is_promoted_on_first_confident_occurrence():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("tr", 0.50), ("az", 0.30)])
    decide_and_record(tracker, [("en", 0.99)])
    assert tracker.languages == ["en", "tr"]
    decide_and_record(tracker, [("tr", 0.99)])
    assert tracker.languages == ["en", "tr"]


def test_record_reports_changes():
    tracker = LanguageTracker()
    first = tracker.decide([("en", 0.99)], 3.0)
    assert tracker.record(first) is True
    assert tracker.record(first) is False


def test_reset():
    tracker = LanguageTracker()
    decide_and_record(tracker, [("en", 0.99)])
    tracker.reset()
    assert tracker.languages == []


def test_language_names():
    assert language_name("en") == "English"
    assert language_name("tr") == "Turkish"
    assert language_name("zz") == "zz"
    assert language_list(["en", "tr"]) == "English, Turkish"
    assert language_list([]) == ""
