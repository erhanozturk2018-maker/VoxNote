"""Interface translations.

Each language is a plain Python dictionary in its own module below
``app/i18n/locales``. English is the reference: a key missing from another
language falls back to English, so a partial translation never shows a
blank label.

To add a language, copy ``locales/en.py``, translate the values, and register the
module in ``_MODULES`` below and in ``UI_LANGUAGES`` in
``app/settings_manager.py``.

The interface language is independent of the language being spoken.
"""

from __future__ import annotations

import logging
from importlib import import_module

log = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en"

# code -> (module name, name of the language in that language)
# The modules live in the ``locales`` sub-package on purpose: a module named
# ``app.i18n.tr`` (Turkish) would replace the ``tr`` function of this package.
_MODULES: dict[str, tuple[str, str]] = {
    "en": ("app.i18n.locales.en", "English"),
    "tr": ("app.i18n.locales.tr", "Türkçe"),
    "de": ("app.i18n.locales.de", "Deutsch"),
    "fr": ("app.i18n.locales.fr", "Français"),
    "it": ("app.i18n.locales.it", "Italiano"),
    "ru": ("app.i18n.locales.ru", "Русский"),
}

_tables: dict[str, dict[str, str]] = {}
_current = DEFAULT_LANGUAGE


def available_languages() -> dict[str, str]:
    """Language codes and their native names, in display order."""
    return {code: name for code, (_, name) in _MODULES.items()}


def table(code: str) -> dict[str, str]:
    if code not in _tables:
        module_name = _MODULES[code][0]
        _tables[code] = dict(import_module(module_name).STRINGS)
    return _tables[code]


def set_language(code: str) -> str:
    """Select the interface language. Unknown codes select English."""
    global _current
    _current = code if code in _MODULES else DEFAULT_LANGUAGE
    return _current


def current_language() -> str:
    return _current


def has(key: str) -> bool:
    return key in table(DEFAULT_LANGUAGE)


def tr(key: str, **values) -> str:
    """Return the text for ``key`` in the current language."""
    text = table(_current).get(key)
    if text is None:
        text = table(DEFAULT_LANGUAGE).get(key)
    if text is None:
        log.warning("Missing translation key: %s", key)
        return key
    if values:
        try:
            return text.format(**values)
        except (KeyError, IndexError, ValueError):
            log.warning("Bad placeholders in translation '%s' (%s)", key, _current)
            return text
    return text
