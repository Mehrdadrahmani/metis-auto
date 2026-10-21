"""Tests for Persian normalization and language tags (synthetic examples)."""

import pytest

from metis.data.lang import lang_tag
from metis.data.normalize import match_key, normalize


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("علي", "علی"),  # Arabic yeh
        ("كتاب", "کتاب"),  # Arabic kaf
        ("مدرسة", "مدرسه"),  # teh marbuta
        ("۱۲۳۴", "1234"),  # Persian digits
        ("٤٥٦", "456"),  # Arabic-Indic digits
        ("س\u0640\u0640\u0640لام", "سلام"),  # tatweel
        ("مُحَمَّد", "محمد"),  # diacritics
        ("می\u200c\u200cخواهم", "می\u200cخواهم"),  # repeated ZWNJ
        ("می\u200c خواهم", "می خواهم"),  # ZWNJ next to a space
        ("  سلام   \n\t دنیا  ", "سلام دنیا"),  # whitespace
        ("\ufeffسلام\u200f", "سلام"),  # BOM, RLM
        ("ﻼ", "لا"),  # presentation form (NFKC)
        ("Hello  World", "Hello World"),  # Latin unchanged except spaces
        ("", ""),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def test_normalize_none_and_idempotent():
    assert normalize(None) == ""
    s = "  علي  ۱۲ كتاب\u200c\u200cها "
    assert normalize(normalize(s)) == normalize(s)


def test_match_key_casefold():
    assert match_key("  Yes ") == match_key("yes")
    assert match_key("بلي") == match_key("بلی")


@pytest.mark.parametrize(
    "text, tag",
    [
        ("سلام، حالت چطوره؟", "fa"),
        ("How do I reset my password?", "en"),
        ("سلام، لطفا این کد python رو debug کن", "mixed"),
        ("12345 !!!", "other"),
        ("😀😀", "other"),
        ("Привет как дела", "other"),
        ("سلام سلام سلام سلام ok", "fa"),
        ("", "other"),
        ("سلام کلید من [REDACTED:openai] است", "fa"),
    ],
)
def test_lang_tag(text, tag):
    assert lang_tag(text) == tag
