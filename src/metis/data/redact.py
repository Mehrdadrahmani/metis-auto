"""Secret redaction (WP-01, AGENTS.md §4, PLAN.md E13).

``redact(text) -> (text, n_hits)`` replaces key-like strings with ``[REDACTED:<kind>]``.
It is idempotent: redacting redacted text changes nothing and reports 0 hits.
"""

from __future__ import annotations

import dataclasses
import re
from collections import Counter
from typing import Any

from metis.data.schema import Message

_NOT_DONE = r"(?!\[REDACTED:)"  # never re-match an earlier replacement
_KEY_CHARS = r"[A-Za-z0-9._~+/=-]"

# (kind, pattern). Order matters: specific token formats before generic ones.
# Generic patterns keep the name (group 1) and replace only the value.
_NAME_START = r"(?<![A-Za-z])"  # allows OPENAI_API_KEY, DB_PASSWORD
_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic", re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}")),
    ("openai", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{10,}")),
    ("google", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("metis", re.compile(r"tpsg-[A-Za-z0-9_-]{10,}")),
    ("github", re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("slack", re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")),
    ("aws", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_-]+)?")),
    ("bearer", re.compile(r"(?i)(\bBearer\s+)" + _NOT_DONE + _KEY_CHARS + "{10,}")),
    (
        "url_param",
        re.compile(
            r"(?i)([?&](?:key|api_?key|token|access_token|auth|sig|signature|secret"
            r"|x-amz-signature|x-amz-credential|x-amz-security-token)=)"
            + _NOT_DONE
            + r"[^&\s\"'<>]+"
        ),
    ),
    (
        "api_key",
        re.compile(
            r"(?i)("
            + _NAME_START
            + r"api[_-]?key[\"']?\s*[:=]\s*[\"']?)"
            + _NOT_DONE
            + r"[^\s\"',;}]+"
        ),
    ),
    (
        "password",
        re.compile(
            r"(?i)("
            + _NAME_START
            + r"pass(?:word|wd)[\"']?\s*[:=]\s*[\"']?)"
            + _NOT_DONE
            + r"[^\s\"',;}]+"
        ),
    ),
    (
        "credential",
        re.compile(
            r"(?i)(" + _NAME_START + r"(?:access[_-]?token|auth[_-]?token|refresh[_-]?token"
            r"|secret[_-]?key|client[_-]?secret|token|secret)[\"']?\s*[:=]\s*[\"']?)"
            + _NOT_DONE
            + _KEY_CHARS
            + "{16,}"
        ),
    ),
]

_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_QUOTED_RUN = re.compile(r"([\"'`])([A-Za-z0-9+/_=-]{32,})\1")
# Unknown key formats: a long letters+digits value right after ":" or "=" (WP-01 residual scan).
_ASSIGNED_RUN = re.compile(r"([:=]\s*)([A-Za-z0-9]{24,})(?![A-Za-z0-9_-])")


def _replace(kind: str, counter: Counter) -> Any:
    def sub(m: re.Match[str]) -> str:
        counter[kind] += 1
        prefix = m.group(1) if m.re.groups and m.group(1) else ""
        return f"{prefix}[REDACTED:{kind}]"

    return sub


def _run(kind: str, counter: Counter, closing_quote: bool) -> Any:
    """Redact a long run only if it mixes letters and digits and is not a UUID."""

    def sub(m: re.Match[str]) -> str:
        head, run = m.group(1), m.group(2)
        has_letter = any(c.isalpha() for c in run)
        has_digit = any(c.isdigit() for c in run)
        if not (has_letter and has_digit) or _UUID.fullmatch(run):
            return m.group(0)
        counter[kind] += 1
        return f"{head}[REDACTED:{kind}]{head if closing_quote else ''}"

    return sub


def redact_counts(text: str) -> tuple[str, Counter]:
    """Redact ``text``; return the new text and hits per kind."""
    counter: Counter = Counter()
    if not text:
        return text, counter
    for kind, pattern in _RULES:
        text = pattern.sub(_replace(kind, counter), text)
    text = _QUOTED_RUN.sub(_run("long_token", counter, closing_quote=True), text)
    text = _ASSIGNED_RUN.sub(_run("opaque_value", counter, closing_quote=False), text)
    return text, counter


def redact(text: str) -> tuple[str, int]:
    """Redact ``text``; return the new text and the number of hits."""
    text, counter = redact_counts(text)
    return text, sum(counter.values())


def redact_obj(obj: Any, counter: Counter | None = None) -> tuple[Any, Counter]:
    """Redact every string inside a JSON-like object (str, list, dict; keys are kept)."""
    counter = Counter() if counter is None else counter
    if isinstance(obj, str):
        text, c = redact_counts(obj)
        counter.update(c)
        return text, counter
    if isinstance(obj, list):
        return [redact_obj(x, counter)[0] for x in obj], counter
    if isinstance(obj, dict):
        return {k: redact_obj(v, counter)[0] for k, v in obj.items()}, counter
    return obj, counter


def _redact_dc(obj: Any, counter: Counter) -> Any:
    """Redact all string values of a dataclass instance (recursively); returns a copy."""
    changes = {}
    for f in dataclasses.fields(obj):
        value = getattr(obj, f.name)
        if dataclasses.is_dataclass(value):
            changes[f.name] = _redact_dc(value, counter)
        elif isinstance(value, list) and value and dataclasses.is_dataclass(value[0]):
            changes[f.name] = [_redact_dc(v, counter) for v in value]
        else:
            changes[f.name] = redact_obj(value, counter)[0]
    return dataclasses.replace(obj, **changes)


# Message fields reported separately in the hit counts.
MESSAGE_FIELDS = ("content", "instructions", "rag", "attachments", "input", "extra")


def redact_message(m: Message) -> tuple[Message, dict[str, int]]:
    """Redact every text field of a message (content, instructions, rag.query, rag.context[],
    attachment content, widget text, unknown extra fields). Returns a copy and hits per field
    (``rag`` is split into ``rag.query`` and ``rag.context``)."""
    hits: dict[str, int] = {}
    changes: dict[str, Any] = {}
    for name in MESSAGE_FIELDS:
        value = getattr(m, name)
        if name == "rag" and value is not None:
            cq, cc, ce = Counter(), Counter(), Counter()
            query = redact_obj(value.query, cq)[0]
            context = redact_obj(value.context, cc)[0]
            extra = redact_obj(value.extra, ce)[0]
            changes[name] = dataclasses.replace(value, query=query, context=context, extra=extra)
            hits["rag.query"] = sum(cq.values())
            hits["rag.context"] = sum(cc.values()) + sum(ce.values())
            continue
        c: Counter = Counter()
        if isinstance(value, list) and value and dataclasses.is_dataclass(value[0]):
            changes[name] = [_redact_dc(v, c) for v in value]
        else:
            changes[name] = redact_obj(value, c)[0]
        hits[name] = sum(c.values())
    return dataclasses.replace(m, **changes), hits
