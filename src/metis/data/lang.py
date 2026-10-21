"""Language tag by letter-script ratios (WP-02 step 3)."""

from __future__ import annotations

import re

FA_THRESHOLD = 0.7
EN_THRESHOLD = 0.7
MIXED_THRESHOLD = 0.2
_REDACTED = re.compile(r"\[REDACTED:[a-z_]+\]")  # markers from metis.data.redact


def _is_arabic_script(c: str) -> bool:
    o = ord(c)
    return (
        0x0600 <= o <= 0x06FF
        or 0x0750 <= o <= 0x077F
        or 0x08A0 <= o <= 0x08FF
        or 0xFB50 <= o <= 0xFDFF
        or 0xFE70 <= o <= 0xFEFF
    )


def _is_latin(c: str) -> bool:
    return c.isascii() or 0x00C0 <= ord(c) <= 0x024F


def script_counts(text: str | None) -> tuple[int, int, int]:
    """(Arabic-script letters, Latin letters, other letters)."""
    fa = en = other = 0
    for c in _REDACTED.sub(" ", text or ""):
        if not c.isalpha():
            continue
        if _is_arabic_script(c):
            fa += 1
        elif _is_latin(c):
            en += 1
        else:
            other += 1
    return fa, en, other


def lang_tag(text: str | None) -> str:
    """'fa', 'en', 'mixed' or 'other' (no letters, or another script)."""
    fa, en, other = script_counts(text)
    total = fa + en + other
    if total == 0:
        return "other"
    if fa / total >= FA_THRESHOLD:
        return "fa"
    if en / total >= EN_THRESHOLD:
        return "en"
    if fa / total >= MIXED_THRESHOLD and en / total >= MIXED_THRESHOLD:
        return "mixed"
    return "other"
