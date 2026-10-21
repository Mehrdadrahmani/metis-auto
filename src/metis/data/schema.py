"""Typed objects for the session/message schema (WP-01).

Text fields (message content, instructions, RAG text, attachment content, widget text) are
excluded from ``repr`` so that printing or logging an object never shows content.
Unknown fields are kept in ``extra`` so the full dataset may add fields without breaking the loader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Attachment:
    content_type: str | None = None
    content: str | None = field(default=None, repr=False)  # usually a URL
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class InputWidget:
    type: str | None = None  # e.g. SINGLE_CHOICE
    name: str | None = field(default=None, repr=False)
    label: str | None = field(default=None, repr=False)
    choices: list[Any] = field(default_factory=list, repr=False)
    required: bool | None = None
    default: Any = field(default=None, repr=False)
    placeholder: str | None = field(default=None, repr=False)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class Rag:
    query: str | None = field(default=None, repr=False)
    context: list[Any] = field(default_factory=list, repr=False)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class Message:
    role: str
    content: str | None = field(default=None, repr=False)
    timestamp: Any = None
    # bot messages only
    model: str | None = None
    provider: str | None = None
    instructions: str | None = field(default=None, repr=False)
    rag: Rag | None = field(default=None, repr=False)
    input: list[InputWidget] = field(default_factory=list, repr=False)
    # user messages only
    attachments: list[Attachment] = field(default_factory=list, repr=False)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class Session:
    session_id: str
    category: str | None = None
    created_at: Any = None
    user_turns: int | None = None
    bot_turns: int | None = None
    session_len: int | None = None
    messages: list[Message] = field(default_factory=list, repr=False)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class Category:
    name: str | None
    sessions: list[Session] = field(default_factory=list, repr=False)
    extra: dict[str, Any] = field(default_factory=dict, repr=False)
