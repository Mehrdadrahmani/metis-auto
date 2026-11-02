"""G7: one SQLite row per request. Ids and numbers only; no message text (PLAN E10)."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

COLUMNS = ("request_id", "ts", "session_id", "chatbot", "lang", "cluster", "scores", "chosen", "served_by", "tried",
           "escalations", "reasons", "cache", "tokens_in", "tokens_out", "cost_usd", "latency_ms", "stage_ms",
           "artifact", "status")


class TraceStore:
    def __init__(self, path: str | Path = ":memory:"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        self.db.execute(f"CREATE TABLE IF NOT EXISTS traces ({', '.join(COLUMNS)})")

    def add(self, row: dict[str, Any]) -> None:
        values = [json.dumps(row.get(c), ensure_ascii=False) if isinstance(row.get(c), dict | list) else row.get(c) for c in COLUMNS]
        with self.lock:
            self.db.execute(f"INSERT INTO traces VALUES ({','.join('?' * len(COLUMNS))})", values)
            self.db.commit()

    def rows(self, limit: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM traces ORDER BY ts DESC" + (f" LIMIT {int(limit)}" if limit else "")
        with self.lock:
            found = self.db.execute(sql).fetchall()
        out = []
        for values in found:
            row = dict(zip(COLUMNS, values, strict=True))
            for c in ("scores", "tried", "reasons", "stage_ms"):
                row[c] = json.loads(row[c]) if row[c] else ([] if c in ("tried", "reasons") else {})
            out.append(row)
        return out

    def summary(self) -> dict[str, Any]:
        rows = self.rows()
        served: dict[str, int] = {}
        for r in rows:
            if r["served_by"]:
                served[r["served_by"]] = served.get(r["served_by"], 0) + 1
        lat = sorted(r["latency_ms"] or 0 for r in rows)
        pick = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))] if lat else 0
        n = len(rows) or 1
        return {"requests": len(rows), "cost_usd": sum(r["cost_usd"] or 0 for r in rows), "routing": served,
                "cache_hits": sum(1 for r in rows if (r["cache"] or "").startswith("hit")) / n,
                "escalations": sum(r["escalations"] or 0 for r in rows) / n,
                "failures": sum(1 for r in rows if r["status"] != "ok") / n,
                "latency_p50": pick(0.5), "latency_p90": pick(0.9), "latency_p99": pick(0.99)}
