"""Build one generation request (WP-06 step 3, PLAN M6).

Same shape for every model: one system message (the chatbot's instructions, then the retrieved
context), the earlier turns, then the user message. Everything is redacted here, so ``complete()``
sees clean text and its check stays a last line of defence.

Instructions and context share one system message: wrappers differ in how they treat a second
system message, and a dropped one would fail silently.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from metis.llm.client import redact_messages

HUGE_PROMPT_CHARS = 20_000  # PLAN M7; such prompts are excluded from the labeled sets


def build_messages(
    instructions: str | None,
    user_text: str,
    history: Iterable[dict[str, str]] = (),
    rag_context: Iterable[Any] = (),
) -> list[dict[str, Any]]:
    """Return the redacted chat messages for one prompt. Raises on input S1 should have excluded."""
    instructions = instructions or ""
    if len(instructions) > HUGE_PROMPT_CHARS:
        raise ValueError("instructions over the size limit reached the request builder")
    if not user_text.strip():
        raise ValueError("empty user message")

    system = instructions.strip()
    context = "\n\n".join(str(c) for c in rag_context if c)
    if context:
        system = f"{system}\n\nRetrieved context:\n{context}".strip()

    # Some providers reject empty turns or a conversation that opens with the assistant. S1 can
    # leave both (a bot greeting, or a cut at the turn limit), so drop them for all models alike.
    turns = [{"role": t["role"], "content": t["content"]} for t in history if t.get("content")]
    while turns and turns[0]["role"] != "user":
        turns.pop(0)

    messages: list[dict[str, Any]] = [{"role": "system", "content": system}] if system else []
    return redact_messages([*messages, *turns, {"role": "user", "content": user_text}])


def gen_params(model_id: str, cfg: dict[str, Any], max_tokens: int | None = None) -> dict[str, Any]:
    """Provider parameters for one model from ``configs/gen_config.yaml``.

    ``max_tokens`` overrides the common limit, for the second pass on cut answers.
    """
    rule = cfg["models"][model_id]  # KeyError on purpose: every model must be listed
    params = dict(cfg["common"])
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    for old, new in rule.get("rename", {}).items():
        params[new] = params.pop(old)
    return {**params, **rule.get("add", {})}
