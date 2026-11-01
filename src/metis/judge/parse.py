"""Read judge output (WP-06 step 5). Every parser returns None on anything invalid."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE = re.compile(r"```[a-zA-Z]*")
JEV_MAX_LEVEL = 4  # five score bands, levels 0..4


def first_object(text: str) -> dict[str, Any] | None:
    """The first balanced ``{...}`` that is valid JSON. Braces inside strings do not count."""
    text = _FENCE.sub("", text or "")
    for start, char in enumerate(text):
        if char != "{":
            continue
        found = _object_at(text, start)
        if found is not None:
            return found
    return None


def _object_at(text: str, start: int) -> dict[str, Any] | None:
    depth, in_string, escaped = 0, False, False
    for end in range(start, len(text)):
        c = text[end]
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    found = json.loads(text[start : end + 1])
                except ValueError:
                    return None
                return found if isinstance(found, dict) else None
    return None


def parse_point(text: str) -> dict[str, Any] | None:
    found = first_object(text)
    score = found.get("score") if found else None
    if isinstance(score, bool) or not isinstance(score, int | float) or score != int(score):
        return None
    if not 1 <= score <= 10:
        return None
    return {"score": float(score), "reason": str(found.get("reason", ""))}


def parse_pair(text: str) -> dict[str, Any] | None:
    found = first_object(text)
    verdict = found.get("verdict") if found else None
    if not isinstance(verdict, str):
        return None
    verdict = {"a": "A", "b": "B", "tie": "tie"}.get(verdict.strip().lower())
    return {"verdict": verdict, "reason": str(found.get("reason", ""))} if verdict else None


def _jev_answer(text: str) -> dict[str, Any] | None:
    found = first_object(text)
    answer = found.get("verdict") if found else None
    return answer if isinstance(answer, dict) else None


def parse_jev_point(text: str) -> dict[str, Any] | None:
    """Jev's level 0..4 mapped to 1..10, not rounded: ``1 + 2.25 * level``."""
    answer = _jev_answer(text)
    level = answer.get("score") if answer else None
    if isinstance(level, bool) or not isinstance(level, int | float):
        return None
    if not 0 <= level <= JEV_MAX_LEVEL:
        return None
    score = 1 + 9 * level / JEV_MAX_LEVEL
    return {"score": float(score), "reason": "", "confidence": answer.get("confidence")}


def parse_jev_pair(text: str) -> dict[str, Any] | None:
    answer = _jev_answer(text)
    verdict = answer.get("choice") if answer else None
    if verdict not in ("A", "B", "tie"):
        return None
    return {"verdict": verdict, "reason": "", "confidence": answer.get("confidence")}
