"""Safe loader for the session/message dataset (WP-01).

Never prints or logs content. Problems are reported as counts in ``LoadReport``.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metis.data.schema import Attachment, Category, InputWidget, Message, Rag, Session

_ATTACHMENT_KEYS = {"contentType", "content"}
_WIDGET_KEYS = {"type", "name", "label", "choices", "required", "default", "placeholder"}
_RAG_KEYS = {"query", "context"}
_INPUT_KEYS = {"items"}
_MESSAGE_KEYS = {
    "role",
    "content",
    "timestamp",
    "model",
    "provider",
    "instructions",
    "rag",
    "input",
    "attachments",
}
_SESSION_KEYS = {"session_id", "created_at", "user_turns", "bot_turns", "session_len", "messages"}
_CATEGORY_KEYS = {"category", "sessions"}


class SchemaError(ValueError):
    """The data does not have the expected structure (message names the path, never content)."""


@dataclass
class LoadReport:
    n_categories: int = 0
    n_sessions: int = 0
    n_messages: int = 0
    extra_fields: Counter = field(default_factory=Counter)  # "path.key" -> occurrences
    mismatches: Counter = field(default_factory=Counter)  # "user_turns" etc. -> sessions


def _extra(obj: dict[str, Any], known: set[str], path: str, report: LoadReport) -> dict[str, Any]:
    extra = {k: v for k, v in obj.items() if k not in known}
    for k in extra:
        report.extra_fields[f"{path}.{k}"] += 1
    return extra


def _as_dict(obj: Any, path: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise SchemaError(f"{path}: expected object, got {type(obj).__name__}")
    return obj


def _list(obj: Any, path: str) -> list[Any]:
    if obj is None:
        return []
    if not isinstance(obj, list):
        raise SchemaError(f"{path}: expected list, got {type(obj).__name__}")
    return obj


def _attachment(raw: Any, report: LoadReport) -> Attachment:
    d = _as_dict(raw, "attachment")
    return Attachment(
        content_type=d.get("contentType"),
        content=d.get("content"),
        extra=_extra(d, _ATTACHMENT_KEYS, "attachment", report),
    )


def _widget(raw: Any, report: LoadReport) -> InputWidget:
    d = _as_dict(raw, "input.items[]")
    return InputWidget(
        type=d.get("type"),
        name=d.get("name"),
        label=d.get("label"),
        choices=_list(d.get("choices"), "input.items[].choices"),
        required=d.get("required"),
        default=d.get("default"),
        placeholder=d.get("placeholder"),
        extra=_extra(d, _WIDGET_KEYS, "input.items[]", report),
    )


def _rag(raw: Any, report: LoadReport) -> Rag | None:
    if raw is None:
        return None
    d = _as_dict(raw, "rag")
    return Rag(
        query=d.get("query"),
        context=_list(d.get("context"), "rag.context"),
        extra=_extra(d, _RAG_KEYS, "rag", report),
    )


def _message(raw: Any, report: LoadReport) -> Message:
    d = _as_dict(raw, "message")
    extra = _extra(d, _MESSAGE_KEYS, "message", report)
    widgets: list[InputWidget] = []
    inp = d.get("input")
    if inp is not None:
        inp = _as_dict(inp, "input")
        widgets = [_widget(w, report) for w in _list(inp.get("items"), "input.items")]
        input_extra = _extra(inp, _INPUT_KEYS, "input", report)
        if input_extra:
            extra["input"] = input_extra
    return Message(
        role=d.get("role"),
        content=d.get("content"),
        timestamp=d.get("timestamp"),
        model=d.get("model"),
        provider=d.get("provider"),
        instructions=d.get("instructions"),
        rag=_rag(d.get("rag"), report),
        input=widgets,
        attachments=[_attachment(a, report) for a in _list(d.get("attachments"), "attachments")],
        extra=extra,
    )


def _session(raw: Any, category: str | None, report: LoadReport, strict: bool) -> Session:
    d = _as_dict(raw, "session")
    messages = [_message(m, report) for m in _list(d.get("messages"), "session.messages")]
    s = Session(
        session_id=d.get("session_id"),
        category=category,
        created_at=d.get("created_at"),
        user_turns=d.get("user_turns"),
        bot_turns=d.get("bot_turns"),
        session_len=d.get("session_len"),
        messages=messages,
        extra=_extra(d, _SESSION_KEYS, "session", report),
    )
    actual = {
        "user_turns": sum(m.role == "user" for m in messages),
        "bot_turns": sum(m.role == "bot" for m in messages),
        "session_len": len(messages),
    }
    for key, n in actual.items():
        declared = getattr(s, key)
        if declared is not None and declared != n:
            report.mismatches[key] += 1
            if strict:
                raise SchemaError(f"session {s.session_id}: {key} declared {declared}, found {n}")
    return s


def load_categories(path: str | Path, strict: bool = False) -> tuple[list[Category], LoadReport]:
    """Load the dataset as categories with their sessions, plus a structure-only report."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    report = LoadReport()
    cats = []
    for c in _list(raw, "top level"):
        c = _as_dict(c, "category")
        name = c.get("category")
        sessions = [_session(s, name, report, strict) for s in _list(c.get("sessions"), "sessions")]
        cats.append(
            Category(
                name=name, sessions=sessions, extra=_extra(c, _CATEGORY_KEYS, "category", report)
            )
        )
    report.n_categories = len(cats)
    report.n_sessions = sum(len(c.sessions) for c in cats)
    report.n_messages = sum(len(s.messages) for c in cats for s in c.sessions)
    return cats, report


def load_with_report(path: str | Path, strict: bool = False) -> tuple[list[Session], LoadReport]:
    from metis.data.load_parquet import is_parquet_dir, iter_sessions

    if is_parquet_dir(path):
        report = LoadReport()
        return list(iter_sessions(path, report, strict=strict)), report
    cats, report = load_categories(path, strict=strict)
    return [s for c in cats for s in c.sessions], report


def load_dataset(path: str | Path, strict: bool = False) -> list[Session]:
    """All sessions (category attached to each). Content is never printed."""
    return load_with_report(path, strict=strict)[0]
