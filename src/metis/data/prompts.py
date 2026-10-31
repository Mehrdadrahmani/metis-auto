"""S1: build the `prompts` table from sessions (WP-02 step 4, spec S1, PLAN M5–M7, E6).

One row per user message that is directly followed by a bot reply. All text columns are redacted.
Embedding input = the whole current user message, normalized (D-045, D-047); no context turns
(D-046). Generation context = the reply's system prompt, RAG context and earlier history (M6).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pandas as pd

from metis.data.lang import lang_tag
from metis.data.normalize import match_key, normalize
from metis.data.redact import redact_message
from metis.data.rules import (
    estimate_tokens,
    is_image_generation,
    is_widget_click_msg,
    is_workflow_turn_msg,
    needs_vision_msg,
    widget_choices,
)
from metis.data.schema import Message, Session

# Exclusion reasons for the labeled sets (val/test); each is counted separately.
# Long per-prompt context, stored apart from the main table on the full data.
CONTEXT_COLUMNS = ("instructions", "history", "rag_context", "prod_answer")

REASONS_LABELED = (
    "reply_workflow",
    "reply_image",
    "reply_no_model",
    "widget_click",
    "has_image",
    "huge_prompt",
    "too_short",
    "junk",
    "dup_exact",
)
# Train (unlabeled, clustering only) keeps images, huge prompts and no-model replies: only the
# user text is used, and the gateway routes such messages too.
REASONS_TRAIN = (
    "reply_workflow",
    "reply_image",
    "widget_click",
    "too_short",
    "junk",
    "dup_exact_train",
)


def prompt_id(session_id: str, index: int) -> str:
    return hashlib.sha256(f"{session_id}:{index}".encode()).hexdigest()[:16]


def text_hash(text: str | None) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else None


def _parse_ts(ts: Any) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _is_junk(text_norm: str) -> bool:
    """No letter and no digit at all (only punctuation, symbols, emoji)."""
    return bool(text_norm) and not any(c.isalnum() for c in text_norm)


def _instr_bucket(n: int) -> str:
    if n <= 1000:
        return "<=1k"
    if n <= 5000:
        return "1-5k"
    if n <= 20000:
        return "5-20k"
    return ">20k"


def _history(
    msgs: list[Message], max_turns: int, max_tokens: int, cpt: float
) -> list[dict[str, str]]:
    """Earlier messages as chat turns (oldest first): last `max_turns`, at most `max_tokens`."""
    turns = [
        {"role": "user" if m.role == "user" else "assistant", "content": m.content or ""}
        for m in msgs
        if m.role in ("user", "bot")
    ][-max_turns:]
    while turns and sum(estimate_tokens(t["content"], cpt) for t in turns) > max_tokens:
        turns.pop(0)
    return turns


def build_rows(
    sessions: Iterable[Session], cfg: dict[str, Any], counts: Counter
) -> list[dict[str, Any]]:
    """One row per user message with a reply, before duplicates are marked (`finish_prompts`)."""
    s1 = cfg["s1"]
    huge, min_chars = s1["huge_prompt_chars"], s1["min_text_chars"]
    cpt = s1["chars_per_token"]
    rows: list[dict[str, Any]] = []
    for s in sessions:
        red = [redact_message(m)[0] for m in s.messages]
        for i, (raw, m) in enumerate(zip(s.messages, red, strict=True)):
            if m.role != "user":
                continue
            counts["user_messages"] += 1
            reply = red[i + 1] if i + 1 < len(red) and red[i + 1].role == "bot" else None
            if reply is None:
                counts["user_without_reply"] += 1
                continue
            prev_bot = s.messages[i - 1] if i > 0 and s.messages[i - 1].role == "bot" else None
            text = m.content or ""
            text_norm = normalize(text)
            instr = reply.instructions or ""
            rag_context = [c for c in (reply.rag.context if reply.rag else []) if c]
            history = _history(red[:i], s1["history_max_turns"], s1["history_max_tokens"], cpt)
            t_user, t_reply = _parse_ts(m.timestamp), _parse_ts(reply.timestamp)
            flags = {
                "reply_workflow": is_workflow_turn_msg(reply),
                "reply_image": is_image_generation(reply.model, reply.provider),
                "reply_no_model": reply.model is None,
                "widget_click": is_widget_click_msg(prev_bot, raw),
                "has_image": needs_vision_msg(m),
                "huge_prompt": len(instr) > huge,
                "too_short": len(text_norm) < min_chars,
                "junk": _is_junk(text_norm),
            }
            rows.append(
                {
                    "prompt_id": prompt_id(s.session_id, i),
                    "session_id": s.session_id,
                    "msg_index": i,
                    "category": s.category,
                    "bot_id": s.extra.get("bot_id") or s.category,
                    "session_created_at": s.created_at,
                    "timestamp": m.timestamp,
                    "text": text,
                    "text_norm": text_norm,
                    "embed_input": text_norm,
                    "match_key": match_key(text),
                    "lang": lang_tag(text_norm),
                    "system_prompt_id": text_hash(instr),
                    "instructions": instr,
                    "history": history,
                    "rag_context": rag_context,
                    "prod_model": reply.model,
                    "prod_provider": reply.provider,
                    "prod_answer": reply.content or "",
                    "prod_latency_s": (t_reply - t_user).total_seconds()
                    if t_user and t_reply
                    else None,
                    **flags,
                    "prev_bot_widget": bool(widget_choices(prev_bot)),
                    "widget_click_exact": (raw.content or "").strip()
                    in {c.strip() for c in widget_choices(prev_bot) if isinstance(c, str)},
                    "instr_chars": len(instr),
                    "text_chars": len(text),
                    "est_tokens_in": estimate_tokens(instr, cpt)
                    + sum(estimate_tokens(c, cpt) for c in rag_context)
                    + sum(estimate_tokens(t["content"], cpt) for t in history)
                    + estimate_tokens(text, cpt),
                    "uses_rag": bool(rag_context),
                    "demands_json": "json" in instr.casefold(),
                    "instr_len_bucket": _instr_bucket(len(instr)),
                }
            )
    return rows


def finish_prompts(df: pd.DataFrame) -> pd.DataFrame:
    """Mark duplicates and eligibility (needs the whole table: repeats cross session batches)."""
    other_l = [r for r in REASONS_LABELED if r != "dup_exact"]
    other_t = [r for r in REASONS_TRAIN if r != "dup_exact_train"]
    df["dup_exact"], df["dup_of"] = duplicates_within(df, ~df[other_l].any(axis=1))
    df["dup_exact_train"], _ = duplicates_within(df, ~df[other_t].any(axis=1))
    df["eligible_labeled"] = ~df[list(REASONS_LABELED)].any(axis=1)
    df["eligible_train"] = ~df[list(REASONS_TRAIN)].any(axis=1)
    return df


def build_prompts(sessions: list[Session], cfg: dict[str, Any]) -> tuple[pd.DataFrame, Counter]:
    """Return the prompts table and structural counts (no content)."""
    counts: Counter = Counter()
    df = pd.DataFrame(build_rows(sessions, cfg, counts))
    counts["prompt_rows"] = len(df)
    return (df if df.empty else finish_prompts(df)), counts


def duplicates_within(df: pd.DataFrame, base: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Exact duplicates (WP-02 step 6) = same normalized text within the same chatbot (`bot_id`),
    among the rows in `base` only (so an excluded row never removes a usable one). The earliest
    occurrence is kept; returns (is_duplicate, prompt_id of the kept row)."""
    sub = df[base].sort_values(["timestamp", "prompt_id"], kind="stable")
    key = sub["bot_id"].astype(str) + "\x00" + sub["match_key"]
    first = sub.groupby(key, sort=False)["prompt_id"].transform("first")
    dup = (first != sub["prompt_id"]) & (sub["match_key"] != "")
    is_dup = pd.Series(False, index=df.index)
    is_dup.loc[dup.index] = dup
    dup_of = pd.Series(None, index=df.index, dtype=object)
    dup_of.loc[dup[dup].index] = first[dup]
    return is_dup, dup_of


def exclusion_counts(df: pd.DataFrame) -> dict[str, int]:
    """Rows flagged by each reason (a row may have several) + first-reason waterfall."""
    out = {f"flag_{r}": int(df[r].sum()) for r in REASONS_LABELED}
    remaining = pd.Series(True, index=df.index)
    for r in REASONS_LABELED:
        hit = remaining & df[r]
        out[f"waterfall_{r}"] = int(hit.sum())
        remaining &= ~df[r]
    out["eligible_labeled"] = int(df["eligible_labeled"].sum())
    out["eligible_train"] = int(df["eligible_train"].sum())
    return out
