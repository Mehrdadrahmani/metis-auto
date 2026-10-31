"""Structure-only data card and secret scan of the full parquet dataset (WP-08 step 2).

Usage: uv run python scripts/data_card_full.py data/raw/metis/data results/wp08_full_data

Writes data_card_full.md and a manifest. Counts, lengths and shares only; no text is printed.
The scan redacts every text column and redacts the result again, which must find nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

from metis.data.load_parquet import connect
from metis.data.redact import redact_counts

SCAN = {
    "chat_bot.parquet": [
        "instructions",
        "description",
        "provider_args",
        "summarizer_provider_args",
        "functions",
        "async_webhook",
    ],
    "chat_session.parquet": ["headline"],
    "chat_message-*.parquet": [
        "content",
        "attachments",
        "citations",
        "tool_calls",
        "rag",
        "input",
        "google_search_query",
    ],
    "derived/chat_message_input.parquet": ["items"],
    "derived/chat_message_tool_calls.parquet": [
        "call.parameters.query",
        "result.outputs",
        "result.outputs.body",
    ],
    "derived/chat_message_rag.parquet": ["query"],
}


def _files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.parquet") if ".duckdb_tmp" not in p.parts)


def scan(root: Path) -> tuple[dict[str, Counter], Counter, Counter]:
    """Hits per kind for each column, rows with a hit, and hits left after redaction."""
    hits: dict[str, Counter] = defaultdict(Counter)
    rows_hit: Counter = Counter()
    left: Counter = Counter()
    for pattern, columns in SCAN.items():
        for path in sorted(root.glob(pattern)):
            cols = [c for c in columns if c in pq.read_schema(path).names]
            for batch in pq.ParquetFile(path).iter_batches(batch_size=2000, columns=cols):
                for col in cols:
                    key = f"{path.name.split('-')[0].removesuffix('.parquet')}.{col}"
                    for text in batch.column(col).to_pylist():
                        if not text:
                            continue
                        red, c = redact_counts(text)
                        if c:
                            hits[key].update(c)
                            rows_hit[key] += 1
                            left[key] += sum(redact_counts(red)[1].values())
    return hits, rows_hit, left


def table(rows: list[tuple], head: list[str]) -> list[str]:
    def cell(x):
        return f"{x:,.1f}" if isinstance(x, float) else f"{x:,}" if isinstance(x, int) else str(x)

    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return out + ["| " + " | ".join(cell(x) for x in r) + " |" for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    t0 = time.perf_counter()
    root, B = args.input, str(args.input) + "/"
    con = connect(root)
    for name, p in {
        "b": "chat_bot.parquet",
        "s": "chat_session.parquet",
        "m": "chat_message-*.parquet",
        "bill": "derived/chat_message_billing.parquet",
    }.items():
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{B}{p}')")
    q = lambda sql: con.execute(sql).fetchall()

    tables = [
        (
            p.relative_to(root).as_posix(),
            pq.read_metadata(p).num_rows,
            pq.read_metadata(p).num_columns,
        )
        for p in _files(root)
    ]
    types = q(
        "SELECT type, count(*), quantile_cont(length(content), 0.5)::INT, "
        "quantile_cont(length(content), 0.99)::INT, max(length(content)), "
        "sum((content IS NULL OR content = '')::INT)::INT FROM m GROUP BY 1 ORDER BY 2 DESC"
    )
    months = q(
        "SELECT coalesce(strftime(timestamp, '%Y-%m'), 'no timestamp'), count(*), "
        "count(DISTINCT session_id) FROM m GROUP BY 1 ORDER BY 1"
    )
    finish = q("SELECT coalesce(finish_reason, 'none'), count(*) FROM m GROUP BY 1 ORDER BY 2 DESC")
    models = q(
        "SELECT b.provider_name, b.provider_model, count(*), "
        "round(100.0 * count(*) / sum(count(*)) OVER (), 1)::DOUBLE, "
        "count(DISTINCT b.bot_id), count(DISTINCT s.user_id) "
        "FROM m JOIN s USING (session_id) JOIN b USING (bot_id) WHERE m.type = 'USER' "
        "GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 15"
    )
    integrity = q(
        "SELECT (SELECT count(*) FROM m WHERE session_id NOT IN (SELECT session_id FROM s)), "
        "(SELECT count(*) FROM s WHERE bot_id NOT IN (SELECT bot_id FROM b)), "
        "(SELECT count(*) - count(DISTINCT message_id) FROM m), "
        "(SELECT count(*) FROM s WHERE session_id NOT IN (SELECT session_id FROM m))"
    )[0]
    bill = q(
        "SELECT count(*), round(sum(totalCost), 2), sum(inputTokens)::BIGINT, "
        "sum(outputTokens)::BIGINT FROM bill"
    )[0]
    con.close()

    hits, rows_hit, left = scan(root)
    kinds = sorted({k for c in hits.values() for k in c})
    scan_rows = [
        (col, rows_hit[col], *[c.get(k, 0) for k in kinds], left[col])
        for col, c in sorted(hits.items())
    ]

    lines = [
        "# Data card: full dataset (structure only)",
        "",
        "Measured. Counts, lengths and shares only; no message text.",
        "",
        "## Tables",
        "",
        *table(tables, ["file", "rows", "columns"]),
        "",
        "## Message types (length in characters)",
        "",
        *table(types, ["type", "rows", "p50", "p99", "max", "empty"]),
        "",
        "## Messages per month",
        "",
        *table(months, ["month", "messages", "sessions"]),
        "",
        "## Finish reasons",
        "",
        *table(finish, ["reason", "rows"]),
        "",
        "## User messages by the bot's current model (top 15)",
        "",
        *table(models, ["provider", "model", "user messages", "share %", "bots", "users"]),
        "",
        "## Integrity",
        "",
        *table([integrity], ["orphan messages", "orphan sessions", "dup ids", "empty sessions"]),
        "",
        "## Billing (currency not stated)",
        "",
        *table([bill], ["rows", "total cost", "input tokens", "output tokens"]),
        "",
        "## Secret scan (`metis.data.redact`, may include false positives)",
        "",
        *table(scan_rows or [("none",)], ["column", "rows hit", *kinds, "left after redaction"]),
        "",
    ]
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output / "data_card_full.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    sizes = "".join(f"{p.name}:{p.stat().st_size}\n" for p in _files(root))
    manifest = {
        "stage": "data_card_full",
        "input": str(root),
        "input_sizes_sha256": hashlib.sha256(sizes.encode()).hexdigest(),
        "config_hash": None,
        "seed": None,
        "counts": {t[0]: t[1] for t in tables},
        "scan_rows_hit": sum(rows_hit.values()),
        "scan_left_after_redaction": sum(left.values()),
        "duration_s": round(time.perf_counter() - t0, 2),
        "cost_usd": 0.0,
    }
    path = args.output / "data_card_full.manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} and {path}")


if __name__ == "__main__":
    main()
