from pathlib import Path

import pytest

from app.filename_template import (
    DEFAULT_TEMPLATE,
    FALLBACK_NAME,
    MAX_STEM_LENGTH,
    render_filename,
    sanitize_filename,
    template_errors,
    unique_path,
)


def test_default_template_expansion(session):
    assert render_filename(DEFAULT_TEMPLATE, session) == "2026-10-03_14-30-00_en-tr"


def test_all_placeholders(session):
    name = render_filename("{date} {time} {languages} {duration} {session_id}", session)
    assert name == "2026-10-03 14-30-00 en-tr 00h05m24s abc12345"


def test_no_languages_uses_placeholder_word(empty_session):
    assert render_filename("{languages}", empty_session) == "none"


def test_literal_text_is_kept(session):
    assert render_filename("meeting-{date}", session) == "meeting-2026-10-03"


@pytest.mark.parametrize(
    "template, expected",
    [
        ("", ["empty"]),
        ("   ", ["empty"]),
        ("{date}_{nope}", ["unknown:nope"]),
        ("{date", ["unbalanced"]),
        ("date}", ["unbalanced"]),
        ("{}", ["unknown:"]),
        ("{date}_{time}", []),
    ],
)
def test_template_errors(template, expected):
    assert template_errors(template) == expected


def test_invalid_template_falls_back_to_default(session):
    assert render_filename("{unknown}", session) == render_filename(DEFAULT_TEMPLATE, session)


def test_template_cannot_reach_object_attributes(session):
    # str.format would evaluate this; the template engine must not.
    assert template_errors("{session_id.__class__}") == ["unknown:session_id.__class__"]


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('a<b>c:d"e/f\\g|h?i*j', "a_b_c_d_e_f_g_h_i_j"),
        ("..\\..\\Windows\\system32", "Windows_system32"),
        ("../../etc/passwd", "etc_passwd"),
        ("name. ", "name"),
        ("  spaced   out  ", "spaced out"),
        ("tab\tand\nnewline", "tab_and_newline"),
        ("", FALLBACK_NAME),
        ("...", FALLBACK_NAME),
        ("CON", "_CON"),
        ("nul.txt", "_nul.txt"),
        ("COM1", "_COM1"),
        ("Türkçe ığüşöç İ", "Türkçe ığüşöç İ"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitized_name_never_contains_separators(session):
    name = render_filename("../{date}/..\\{time}", session)
    assert "/" not in name and "\\" not in name
    assert not name.startswith(".")
    assert Path(name).name == name


def test_long_names_are_shortened():
    assert len(sanitize_filename("x" * 500)) == MAX_STEM_LENGTH


def test_unique_path_adds_numeric_suffix(tmp_path):
    first = unique_path(tmp_path, "note", "md")
    assert first == tmp_path / "note.md"
    first.write_text("1")
    second = unique_path(tmp_path, "note", ".md")
    assert second == tmp_path / "note_2.md"
    second.write_text("2")
    assert unique_path(tmp_path, "note", "md") == tmp_path / "note_3.md"
