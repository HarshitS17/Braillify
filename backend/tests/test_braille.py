"""
Tests for the Braille translation subsystem.

Validates:
  - Grade 1 English letter translation
  - Uppercase prefix insertion
  - Number indicator + digit translation
  - Punctuation mapping
  - Mixed text round-trip
  - Unknown character handling
  - translate_labels pipeline integration
"""

import pytest
from app.pipeline.braille.grade1_english import Grade1EnglishTranslator
from app.pipeline.braille_translation import translate_labels
from app.models.label import Label


@pytest.fixture
def translator():
    return Grade1EnglishTranslator()


# ── Single letters ──────────────────────────────────────────────────────────

def test_lowercase_letters(translator):
    result = translator.translate("abc")
    # a = ⠁  b = ⠃  c = ⠉
    assert result.braille_unicode == "⠁⠃⠉"
    assert result.language == "en"
    assert result.grade == 1


def test_uppercase_prefix(translator):
    result = translator.translate("A")
    # Capital prefix ⠠ + a ⠁
    assert result.braille_unicode == "⠠⠁"


def test_mixed_case(translator):
    result = translator.translate("Hi")
    # Cap prefix + h + i
    assert result.braille_unicode == "⠠⠓⠊"


# ── Digits ──────────────────────────────────────────────────────────────────

def test_single_digit(translator):
    result = translator.translate("5")
    # Number prefix ⠼ + e(5) ⠑
    assert result.braille_unicode == "⠼⠑"


def test_multi_digit(translator):
    result = translator.translate("42")
    # Number prefix once, then d(4) + b(2)
    assert result.braille_unicode == "⠼⠙⠃"


def test_number_indicator_resets_on_space(translator):
    result = translator.translate("1 2")
    # ⠼⠁ (space) ⠼⠃
    assert result.braille_unicode == "⠼⠁ ⠼⠃"


# ── Punctuation ─────────────────────────────────────────────────────────────

def test_period(translator):
    result = translator.translate("a.")
    # a ⠁ + period ⠲
    assert result.braille_unicode == "⠁⠲"


def test_comma(translator):
    result = translator.translate("a,b")
    assert result.braille_unicode == "⠁⠂⠃"


# ── Spaces ──────────────────────────────────────────────────────────────────

def test_space(translator):
    result = translator.translate("a b")
    assert result.braille_unicode == "⠁ ⠃"
    # dot notation for space should be "0"
    parts = result.braille_dots.split("-")
    assert "0" in parts


# ── Full word examples ──────────────────────────────────────────────────────

def test_word_nucleus(translator):
    result = translator.translate("Nucleus")
    # Should start with capital prefix
    assert result.braille_unicode.startswith("⠠")
    # Should have 8 cells: cap + n + u + c + l + e + u + s
    assert len(result.braille_unicode) == 8


# ── Unknown characters ─────────────────────────────────────────────────────

def test_unknown_chars_skipped(translator):
    result = translator.translate("a@b")
    # '@' is not in the table — silently skipped
    assert result.braille_unicode == "⠁⠃"


# ── Pipeline integration ───────────────────────────────────────────────────

def test_translate_labels_populates_braille():
    labels = [
        Label(diagram_id="d1", text="Hello"),
        Label(diagram_id="d1", text="World"),
    ]
    result = translate_labels(labels)

    for label in result:
        assert label.braille.braille_unicode != ""
        assert label.braille.grade == 1
        assert label.braille.language == "en"


def test_translate_labels_empty_text_unchanged():
    labels = [Label(diagram_id="d1", text="")]
    result = translate_labels(labels)
    assert result[0].braille.braille_unicode == ""
