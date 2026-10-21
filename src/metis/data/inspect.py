"""Structure-only data card (WP-01). Reports key paths, types, counts, length percentiles,
value sets of short categorical fields and redaction hits. Never outputs message text."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metis.data.load import load_with_report
from metis.data.redact import redact_counts, redact_message

# Only these fields have their values listed (all others: counts and lengths only).
CATEGORICAL_PATHS = {
    "[].category",
    "[].sessions[].messages[].role",
    "[].sessions[].messages[].model",
    "[].sessions[].messages[].provider",
    "[].sessions[].messages[].input.items[].type",
    "[].sessions[].messages[].attachments[].contentType",
}
_MAX_VALUE_LEN = 60
_MAX_VALUES = 60
_SAFE_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,40}")
LONG_PROMPT_CHARS = 20_000


@dataclass
class _PathStats:
    count: int = 0
    types: Counter = field(default_factory=Counter)
    lengths: list[int] = field(default_factory=list)  # str length or list length
    values: Counter = field(default_factory=Counter)  # categorical paths only


def _walk(obj: Any, path: str, stats: dict[str, _PathStats]) -> None:
    st = stats[path]
    st.count += 1
    st.types[type(obj).__name__] += 1
    if isinstance(obj, str):
        st.lengths.append(len(obj))
        if path in CATEGORICAL_PATHS:
            st.values[obj if len(obj) <= _MAX_VALUE_LEN else "<long value>"] += 1
    elif isinstance(obj, list):
        st.lengths.append(len(obj))
        for x in obj:
            _walk(x, path + "[]", stats)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            key = k if _SAFE_KEY.fullmatch(k) else "<key>"
            _walk(v, f"{path}.{key}", stats)
    elif path in CATEGORICAL_PATHS:
        st.values[repr(obj)] += 1


def percentiles(xs: list[int], qs=(0, 50, 90, 99, 100)) -> list[int]:
    if not xs:
        return []
    s = sorted(xs)
    return [s[min(len(s) - 1, round(q / 100 * (len(s) - 1)))] for q in qs]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_card(path: str | Path) -> dict[str, Any]:
    """Compute the data card as a dict of aggregates (no content)."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    stats: dict[str, _PathStats] = defaultdict(_PathStats)
    _walk(raw, "", stats)

    sessions, report = load_with_report(path)
    msgs = [m for s in sessions for m in s.messages]
    instr = [m.instructions for m in msgs if m.instructions]
    hits_by_field: Counter = Counter()
    rescan_by_field: Counter = Counter()
    msgs_with_hits = 0
    sessions_with_hits = 0
    for s in sessions:
        session_hit = False
        for m in s.messages:
            red, hits = redact_message(m)
            hits_by_field.update(hits)
            if any(hits.values()):
                msgs_with_hits += 1
                session_hit = True
            rescan_by_field.update(redact_message(red)[1])
        sessions_with_hits += session_hit

    hits_by_kind: Counter = Counter()
    for m in msgs:
        for text in _texts(m):
            hits_by_kind.update(redact_counts(text)[1])

    return {
        "input_sha256": _sha_file(path),
        "categories": report.n_categories,
        "sessions": report.n_sessions,
        "messages": report.n_messages,
        "roles": dict(Counter(m.role for m in msgs)),
        "models": dict(Counter(m.model for m in msgs if m.model)),
        "providers": dict(Counter(m.provider for m in msgs if m.provider)),
        "sessions_per_category": dict(Counter(s.category for s in sessions)),
        "attachment_messages": sum(bool(m.attachments) for m in msgs),
        "attachments": sum(len(m.attachments) for m in msgs),
        "widget_messages": sum(bool(m.input) for m in msgs),
        "widgets": sum(len(m.input) for m in msgs),
        "rag_messages": sum(m.rag is not None for m in msgs),
        "rag_nonempty_context_messages": sum(bool(m.rag and m.rag.context) for m in msgs),
        "instructions_nonempty": len(instr),
        "instructions_distinct": len({_sha(t) for t in instr}),
        "instructions_over_20k": sum(len(t) > LONG_PROMPT_CHARS for t in instr),
        "instructions_over_20k_distinct": len(
            {_sha(t) for t in instr if len(t) > LONG_PROMPT_CHARS}
        ),
        "turn_count_mismatches": dict(report.mismatches),
        "extra_fields": dict(report.extra_fields),
        "redaction_hits_by_field": dict(hits_by_field),
        "redaction_hits_by_kind": dict(hits_by_kind),
        "messages_with_hits": msgs_with_hits,
        "sessions_with_hits": sessions_with_hits,
        "rescan_hits_by_field": dict(rescan_by_field),
        "paths": {
            p: {
                "count": st.count,
                "types": dict(st.types),
                "length_p0_50_90_99_100": percentiles(st.lengths),
                **({"values": _cap(st.values)} if st.values else {}),
            }
            for p, st in sorted(stats.items())
        },
    }


def _texts(m) -> list[str]:
    """All string fields of a message that redaction covers (for per-kind counts)."""
    out: list[str] = []

    def add(x: Any) -> None:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, list):
            for y in x:
                add(y)
        elif isinstance(x, dict):
            for y in x.values():
                add(y)

    add(m.content)
    add(m.instructions)
    if m.rag:
        add(m.rag.query)
        add(m.rag.context)
        add(m.rag.extra)
    for a in m.attachments:
        add(a.content)
        add(a.extra)
    for w in m.input:
        add([w.name, w.label, w.choices, w.default, w.placeholder, w.extra])
    add(m.extra)
    return out


def _cap(values: Counter) -> dict[str, int]:
    items = values.most_common(_MAX_VALUES)
    out = dict(items)
    rest = sum(values.values()) - sum(n for _, n in items)
    if rest:
        out["<other>"] = rest
    return out


def _sha_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _table(d: dict[str, Any], key: str = "value", val: str = "count") -> str:
    rows = [f"| {key} | {val} |", "|---|---|"]
    rows += [f"| `{k}` | {v} |" for k, v in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))]
    return "\n".join(rows)


def render_markdown(card: dict[str, Any], source_name: str) -> str:
    c = card
    lines = [
        f"# Data card: `{source_name}` (structure only)",
        "",
        (
            "Generated by `scripts/data_card.py` (WP-01). Aggregates only: no message text, "
            "instructions, RAG text or attachment content."
        ),
        "",
        f"Input sha256: {c['input_sha256']}",
        "",
        "## Counts",
        "",
        "| item | n |",
        "|---|---|",
    ]
    for k in [
        "categories", "sessions", "messages", "attachment_messages", "attachments",
        "widget_messages", "widgets", "rag_messages", "rag_nonempty_context_messages",
        "instructions_nonempty", "instructions_distinct", "instructions_over_20k",
        "instructions_over_20k_distinct", "messages_with_hits", "sessions_with_hits",
    ]:  # fmt: skip
        lines.append(f"| {k} | {c[k]} |")
    lines += [
        f"| distinct models | {len(c['models'])} |",
        f"| distinct providers | {len(c['providers'])} |",
        "",
        "## Roles",
        "",
        _table(c["roles"]),
        "",
        "## Models (bot messages)",
        "",
        _table(c["models"]),
        "",
        "## Providers",
        "",
        _table(c["providers"]),
        "",
        "## Sessions per category",
        "",
        _table(c["sessions_per_category"]),
        "",
        "## Redaction hits",
        "",
        "By field:",
        "",
        _table(c["redaction_hits_by_field"], "field", "hits"),
        "",
        "By kind:",
        "",
        _table(c["redaction_hits_by_kind"] or {"(none)": 0}, "kind", "hits"),
        "",
        f"Re-scan after redaction: **{sum(c['rescan_hits_by_field'].values())} hits**.",
        "",
        "## Schema checks",
        "",
        f"- Turn-count mismatches (sessions): {c['turn_count_mismatches'] or 'none'}",
        f"- Unknown fields: {c['extra_fields'] or 'none'}",
        "",
        "## Key paths",
        "",
        "Length = string length or list length; percentiles p0 / p50 / p90 / p99 / max.",
        "",
        "| path | count | types | length p0/50/90/99/max |",
        "|---|---|---|---|",
    ]
    for p, st in c["paths"].items():
        types = ", ".join(f"{t}:{n}" for t, n in st["types"].items())
        lens = " / ".join(map(str, st["length_p0_50_90_99_100"])) or "–"
        lines.append(f"| `{p or '(root)'}` | {st['count']} | {types} | {lens} |")
    lines += ["", "## Categorical value sets", ""]
    for p, st in c["paths"].items():
        if "values" in st:
            lines += [f"`{p}`", "", _table(st["values"]), ""]
    return "\n".join(lines) + "\n"
