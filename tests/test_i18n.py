import re

import pytest

from app import i18n
from app.settings_manager import UI_LANGUAGES

PLACEHOLDER = re.compile(r"\{(\w+)\}")
LANGUAGES = list(i18n.available_languages())


@pytest.fixture(autouse=True)
def restore_language():
    yield
    i18n.set_language("en")


def test_languages_match_settings():
    assert set(LANGUAGES) == set(UI_LANGUAGES)
    assert LANGUAGES[:3] == ["en", "tr", "de"]


@pytest.mark.parametrize("code", LANGUAGES)
def test_translation_is_complete(code):
    reference = i18n.table("en")
    table = i18n.table(code)
    assert set(table) == set(reference), (
        f"missing: {sorted(set(reference) - set(table))}, "
        f"extra: {sorted(set(table) - set(reference))}"
    )


@pytest.mark.parametrize("code", LANGUAGES)
def test_placeholders_match_english(code):
    reference = i18n.table("en")
    for key, text in i18n.table(code).items():
        assert text.strip(), key
        assert set(PLACEHOLDER.findall(text)) == set(PLACEHOLDER.findall(reference[key])), key


@pytest.mark.parametrize("code", [c for c in LANGUAGES if c != "en"])
def test_translation_differs_from_english(code):
    reference = i18n.table("en")
    table = i18n.table(code)
    same = [key for key in table if table[key] == reference[key]]
    # Product names, units and a few technical labels are legitimately equal.
    assert len(same) < len(table) * 0.1, same


def test_tr_formats_values():
    i18n.set_language("en")
    assert i18n.tr("result.saved", path="C:/x.md") == "Saved: C:/x.md"
    i18n.set_language("tr")
    assert i18n.tr("result.saved", path="C:/x.md") == "Kaydedildi: C:/x.md"
    i18n.set_language("de")
    assert i18n.tr("state.ready") == "Bereit"


def test_unknown_language_falls_back_to_english():
    assert i18n.set_language("xx") == "en"
    assert i18n.tr("state.ready") == "Ready"


def test_unknown_key_returns_key():
    assert i18n.tr("no.such.key") == "no.such.key"
    assert not i18n.has("no.such.key")
