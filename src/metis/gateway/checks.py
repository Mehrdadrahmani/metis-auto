"""G6: free code checks on an answer (PLAN E7). Each returns a reason code or None."""

from __future__ import annotations

import json
import re

from metis.data.lang import script_counts

REFUSALS = re.compile(
    r"(متأسفم[،,]?\s*(اما\s*)?نمی.?توانم|متاسفم[،,]?\s*(اما\s*)?نمی.?توانم|نمی.?توانم\s+(در\s+این\s+مورد\s+)?کمک|"
    r"I can(no|')t help|I cannot assist|I'm unable to help|I can(no|')t assist)", re.IGNORECASE)
HINTS = {
    "empty": "Give a complete answer.",
    "truncated": "Answer briefly and finish your answer.",
    "wrong_language": "Answer in Persian.",
    "bad_json": "Return valid JSON only.",
    "refusal": "Help with the request if it is allowed.",
}


def check_answer(text: str, finish_reason: str, user_lang: str, wants_json: bool = False, min_lang_chars: int = 20) -> str | None:
    if not text or not text.strip():
        return "empty"
    if finish_reason == "length":
        return "truncated"
    if wants_json:
        try:
            json.loads(text)
        except ValueError:
            return "bad_json"
        return None
    if user_lang == "fa" and len(text) >= min_lang_chars:
        arabic, latin, _ = script_counts(text)
        if arabic + latin and arabic / (arabic + latin) < 0.5:
            return "wrong_language"
    if len(text) < 400 and REFUSALS.search(text):
        return "refusal"
    return None
