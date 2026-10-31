"""Loader for the full dataset: the relational parquet dump (WP-08 step 2).

Tables are joined into the same ``Session``/``Message`` objects as the sample loader, one session
at a time, so the 710k messages never sit in memory together. Never prints or logs content.

Differences from the sample: no category (``Session.category`` is None), model, provider and
instructions come from the bot's **current** settings (not recorded per message), and ``rag`` is a
list of queries, each with its retrieved chunks.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb

from metis.data.load import LoadReport, SchemaError, _as_dict, _attachment, _list, _widget
from metis.data.schema import Attachment, InputWidget, Message, Rag, Session

ROLES = {"USER": "user", "AI": "bot", "SYSTEM": "system", "TOOL": "tool"}
_BATCH_ROWS = 2000
_EMPTY = ("", "[]", "{}", "null")


def is_parquet_dir(path: str | Path) -> bool:
    return Path(path, "chat_session.parquet").is_file()


def _json(text: str | None, path: str) -> Any:
    if text is None or text in _EMPTY:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SchemaError(f"{path}: not valid JSON") from e


def _rag(text: str | None) -> Rag | None:
    queries = _list(_json(text, "rag"), "rag")
    if not queries:
        return None
    context: list[Any] = []
    for raw in queries:
        q = _as_dict(raw, "rag[]")
        for chunk in _list(q.get("relevantChunks"), "rag[].relevantChunks"):
            context.append(_as_dict(chunk, "rag[].relevantChunks[]").get("content"))
    first = _as_dict(queries[0], "rag[]").get("query")
    return Rag(query=first, context=context, extra={"n_queries": len(queries)})


def _widgets(text: str | None, report: LoadReport) -> list[InputWidget]:
    inp = _json(text, "input")
    if inp is None:
        return []
    items = _list(_as_dict(inp, "input").get("items"), "input.items")
    return [_widget(w, report) for w in items]


def _attachments(text: str | None, report: LoadReport) -> list[Attachment]:
    return [_attachment(a, report) for a in _list(_json(text, "attachments"), "attachments")]


def _message(row: dict[str, Any], bot: dict[str, Any], report: LoadReport) -> Message:
    role = ROLES.get(row["type"])
    if role is None:
        raise SchemaError(f"message: unknown type {str(row['type'])[:20]!r}")
    is_bot = role == "bot"
    ts = row["timestamp"]
    return Message(
        role=role,
        content=row["content"],
        timestamp=ts.isoformat() if ts is not None else None,
        model=bot["provider_model"] if is_bot else None,
        provider=bot["provider_name"] if is_bot else None,
        instructions=bot["instructions"] if is_bot else None,
        rag=_rag(row["rag"]) if is_bot else None,
        input=_widgets(row["input"], report) if is_bot else [],
        attachments=_attachments(row["attachments"], report),
        extra={"message_id": row["message_id"], "finish_reason": row["finish_reason"]},
    )


def _session(
    sid: str,
    rows: list[dict[str, Any]],
    meta: dict[str, dict[str, Any]],
    bots: dict[str, dict[str, Any]],
    report: LoadReport,
    strict: bool,
) -> Session:
    info = meta.get(sid)
    if info is None or info["bot_id"] not in bots:
        raise SchemaError("session: message without a session or bot row")
    bot = bots[info["bot_id"]]
    messages = [_message(r, bot, report) for r in rows]
    declared = info["dialogue_length"]
    if declared is not None and declared != len(messages):
        report.mismatches["dialogue_length"] += 1
        if strict:
            raise SchemaError(f"session {sid}: dialogue_length {declared}, found {len(messages)}")
    report.n_sessions += 1
    report.n_messages += len(messages)
    return Session(
        session_id=sid,
        category=None,
        created_at=info["created_at"].isoformat() if info["created_at"] else None,
        user_turns=sum(m.role == "user" for m in messages),
        bot_turns=sum(m.role == "bot" for m in messages),
        session_len=len(messages),
        messages=messages,
        extra={"bot_id": info["bot_id"], "user_id": info["user_id"]},
    )


def connect(root: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    con.execute(f"SET temp_directory='{root / '.duckdb_tmp'}'")
    return con


def iter_sessions(
    path: str | Path,
    report: LoadReport | None = None,
    strict: bool = False,
    limit_sessions: int | None = None,
) -> Iterator[Session]:
    """Yield sessions in session-id order; messages in time order (user first on a tie)."""
    root = Path(path)
    report = report if report is not None else LoadReport()
    con = connect(root)
    bots = {
        r[0]: {"provider_model": r[1], "provider_name": r[2], "instructions": r[3]}
        for r in con.execute(
            "SELECT bot_id, provider_model, provider_name, instructions FROM read_parquet(?)",
            [str(root / "chat_bot.parquet")],
        ).fetchall()
    }
    meta = {
        r[0]: {"bot_id": r[1], "user_id": r[2], "created_at": r[3], "dialogue_length": r[4]}
        for r in con.execute(
            "SELECT session_id, bot_id, user_id, created_at, dialogue_length FROM read_parquet(?)",
            [str(root / "chat_session.parquet")],
        ).fetchall()
    }
    limit = "" if limit_sessions is None else f"LIMIT {int(limit_sessions)}"
    reader = con.sql(
        f"""
        WITH keep AS (SELECT session_id FROM read_parquet(?) ORDER BY session_id {limit})
        SELECT message_id, session_id, type, timestamp, content, finish_reason, attachments, rag,
               input
        FROM read_parquet(?, union_by_name = true) JOIN keep USING (session_id)
        ORDER BY session_id, timestamp NULLS LAST, type <> 'USER', message_id
        """,
        params=[str(root / "chat_session.parquet"), str(root / "chat_message-*.parquet")],
    ).to_arrow_reader(_BATCH_ROWS)
    current: str | None = None
    rows: list[dict[str, Any]] = []
    for batch in reader:
        for row in batch.to_pylist():
            if row["session_id"] != current:
                if rows:
                    yield _session(current, rows, meta, bots, report, strict)
                if current is not None and row["session_id"] < current:
                    raise SchemaError("messages out of session order")
                current, rows = row["session_id"], []
            rows.append(row)
    if rows:
        yield _session(current, rows, meta, bots, report, strict)
    con.close()


def message_types(path: str | Path) -> Counter:
    """Rows per message type (a cheap structure check)."""
    con = connect(Path(path))
    q = "SELECT type, count(*) FROM read_parquet(?, union_by_name = true) GROUP BY 1"
    out = Counter(dict(con.execute(q, [str(Path(path) / "chat_message-*.parquet")]).fetchall()))
    con.close()
    return out
