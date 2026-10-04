"""Per-utterance language decisions and the session language list.

Whisper reports a probability for every language it knows. For long, clear
utterances the top candidate is reliable. For very short or ambiguous audio
it is not, and blindly following it makes a transcript flip between
languages. The tracker therefore separates two questions:

* *Which language should this utterance be decoded in?* (``decide``)
* *Which languages were spoken in this session?* (``record`` / ``languages``)

The tracker never forces a language that the recogniser considers
implausible, because decoding speech in the wrong language makes Whisper
translate or invent text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class LanguageDecision:
    language: str
    probability: float
    confident: bool


class LanguageTracker:
    """Chooses a language per utterance and remembers what was spoken."""

    def __init__(
        self,
        confident_probability: float = 0.70,
        short_utterance_seconds: float = 1.5,
        short_utterance_probability: float = 0.90,
        sticky_ratio: float = 0.5,
        override_probability: float = 0.90,
    ) -> None:
        # Minimum probability for a decision to count as confident.
        self.confident_probability = confident_probability
        # Utterances shorter than this need the stricter probability below.
        self.short_utterance_seconds = short_utterance_seconds
        self.short_utterance_probability = short_utterance_probability
        # An already used language is preferred over an unconfident new one
        # when its probability is at least ``sticky_ratio`` times the top one.
        self.sticky_ratio = sticky_ratio
        # A language outside ``allowed`` is still accepted when the recogniser
        # is at least this sure about it and the utterance is not short.
        self.override_probability = override_probability
        self._confident: list[str] = []
        self._tentative: list[str] = []
        # Languages the user said they speak. Empty means "any language".
        # They settle short and unclear utterances; clearly spoken speech in
        # another language is still recognised as what it is, because forcing
        # it into an allowed language would label it wrongly.
        self.allowed: frozenset[str] = frozenset()

    def _restrict(self, ranked: list[tuple[str, float]]) -> list[tuple[str, float]]:
        """Keep only allowed languages and rescale their probabilities.

        Choosing between two or three languages is far more reliable than
        choosing between a hundred, which is what makes short utterances
        land in the right language.
        """
        if not self.allowed:
            return ranked
        kept = [(code, prob) for code, prob in ranked if code in self.allowed]
        if not kept:
            # The recogniser does not know any of the allowed codes.
            return ranked
        total = sum(prob for _, prob in kept)
        if total <= 0:
            return [(code, 1.0 / len(kept)) for code, _ in kept]
        return [(code, prob / total) for code, prob in kept]

    def reset(self) -> None:
        self._confident.clear()
        self._tentative.clear()

    def decide(
        self, probabilities: Iterable[tuple[str, float]], duration_seconds: float
    ) -> LanguageDecision | None:
        """Pick the language for one utterance without recording it.

        ``probabilities`` is the list of ``(language_code, probability)``
        pairs reported by the recogniser. Returns ``None`` when it is empty.
        """
        raw = sorted(
            ((code, float(prob)) for code, prob in probabilities),
            key=lambda item: item[1],
            reverse=True,
        )
        if not raw:
            return None
        if (
            self.allowed
            and raw[0][0] not in self.allowed
            and raw[0][1] >= self.override_probability
            and duration_seconds >= self.short_utterance_seconds
        ):
            return LanguageDecision(raw[0][0], raw[0][1], True)
        ranked: Sequence[tuple[str, float]] = self._restrict(raw)

        top_language, top_probability = ranked[0]
        required = (
            self.short_utterance_probability
            if duration_seconds < self.short_utterance_seconds
            else self.confident_probability
        )
        if top_probability >= required:
            return LanguageDecision(top_language, top_probability, True)

        # Not confident. Avoid an unnecessary switch: prefer a language that
        # was already used in this session if it is still plausible.
        known = self._confident + self._tentative
        if top_language not in known:
            lookup = dict(ranked)
            best_known = max(known, key=lambda code: lookup.get(code, 0.0), default=None)
            if best_known is not None:
                known_probability = lookup.get(best_known, 0.0)
                if known_probability >= self.sticky_ratio * top_probability:
                    return LanguageDecision(best_known, known_probability, False)
        return LanguageDecision(top_language, top_probability, False)

    def record(self, decision: LanguageDecision) -> bool:
        """Remember a decision that produced transcript text.

        Returns ``True`` when the session language list changed.
        """
        before = self.languages
        if decision.confident:
            if decision.language not in self._confident:
                self._confident.append(decision.language)
            if decision.language in self._tentative:
                self._tentative.remove(decision.language)
        elif (
            decision.language not in self._confident
            and decision.language not in self._tentative
        ):
            self._tentative.append(decision.language)
        return self.languages != before

    @property
    def languages(self) -> list[str]:
        """Distinct session languages.

        Languages are ordered by their first confident occurrence. Languages
        that were only ever detected with low confidence follow, so that the
        list always covers every language label used in the transcript.
        """
        return self._confident + self._tentative
