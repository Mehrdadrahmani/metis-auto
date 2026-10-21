"""Persian text normalization for matching and embedding (WP-02 step 2).

Only used for `text_norm` / `embed_input`, widget matching and duplicate detection. The original
text is kept unchanged for generation and judging.
"""

from __future__ import annotations

import re
import unicodedata

_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh -> Persian yeh
        "ى": "ی",  # alef maksura -> Persian yeh
        "ك": "ک",  # Arabic kaf -> Persian keheh
        "ة": "ه",  # teh marbuta -> heh (matching only)
        **{chr(0x06F0 + i): str(i) for i in range(10)},  # Persian digits
        **{chr(0x0660 + i): str(i) for i in range(10)},  # Arabic-Indic digits
        "\u0640": None,  # tatweel
        "\u200b": None,  # zero-width space
        "\u200d": None,  # zero-width joiner
        "\u200e": None,  # LRM
        "\u200f": None,  # RLM
        "\ufeff": None,  # BOM
    }
)
# Arabic diacritics (harakat, tanween, shadda, sukun, superscript alef, Quranic marks)
_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed]")
_ZWNJ_RUN = re.compile("\u200c{2,}")
_ZWNJ_SPACE = re.compile(r"\s*\u200c\s*(?=\s)|(?<=\s)\u200c|\u200c(?=\s)")
_SPACE = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    """Normalize Persian/Arabic variants, digits, ZWNJ and whitespace (meaning unchanged)."""
    if not text:
        return ""
    # NFKC folds Arabic presentation forms (U+FB50–U+FEFF) and full-width characters.
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_CHAR_MAP)
    text = _DIACRITICS.sub("", text)
    text = _ZWNJ_RUN.sub("\u200c", text)
    text = _ZWNJ_SPACE.sub("", text)
    text = _SPACE.sub(" ", text).strip()
    return text.strip("\u200c")


def match_key(text: str | None) -> str:
    """Key for equality checks (widget clicks, exact duplicates): normalized and case-folded."""
    return normalize(text).casefold()
