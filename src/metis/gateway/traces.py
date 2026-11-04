"""G7: one SQLite row per request. Ids and numbers only; no message text (PLAN E10)."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

COLUMNS = ("request_id", "ts", "session_id", "chatbot", "lang", "cluster", "scores", "chosen", "served_by", "tried",
           "escalations", "reasons", "cache", "tokens_in", "tokens_out", "cost_usd", "latency_ms", "stage_ms",
           "artifact", "status", "user_id", "billing")  # billing: service | own_key (the user's own provider key)


class TraceStore:
    def __init__(self, path: str | Path = ":memory:"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        self.db.execute(f"CREATE TABLE IF NOT EXISTS traces ({', '.join(COLUMNS)})")
        have = {r[1] for r in self.db.execute("PRAGMA table_info(traces)")}
        for col in COLUMNS:  # older files: add the new columns
            if col not in have:
                self.db.execute(f"ALTER TABLE traces ADD COLUMN {col}")
        self.db.commit()

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

    def usage(self, prices: dict[str, dict[str, float]], premium: str, user_id: int | None = None,
              since: float = 0.0) -> dict[str, Any]:
        """Per-day totals and the model mix, for the dashboard. ``premium`` prices what sending
        every request to that model would have cost (same tokens), so the saving is a comparison."""
        sql = "SELECT ts, served_by, cost_usd, tokens_in, tokens_out, latency_ms, cache, status FROM traces WHERE ts >= ?"
        args: tuple = (since,)
        if user_id is not None:
            sql, args = sql + " AND user_id = ?", (since, user_id)
        with self.lock:
            found = self.db.execute(sql, args).fetchall()
        p = prices.get(premium, {})
        days: dict[str, dict[str, float]] = {}
        mix: dict[str, int] = {}
        lat = []
        totals = {"requests": 0, "cost_usd": 0.0, "premium_usd": 0.0, "cache_hits": 0, "failures": 0}
        for ts, served, cost, t_in, t_out, latency, cache, status in found:
            day = time.strftime("%Y-%m-%d", time.localtime(ts or 0))
            d = days.setdefault(day, {"requests": 0, "cost_usd": 0.0, "premium_usd": 0.0})
            prem = ((t_in or 0) * p.get("price_in", 0) + (t_out or 0) * p.get("price_out", 0)) / 1e6
            hit = str(cache or "").startswith("hit")
            if hit:
                prem = 0.0  # a cache hit would also be free in front of the premium model
            for bucket in (d, totals):
                bucket["requests"] += 1
                bucket["cost_usd"] += cost or 0.0
                bucket["premium_usd"] += prem
            totals["cache_hits"] += hit
            totals["failures"] += status != "ok"
            if served:
                mix[served] = mix.get(served, 0) + 1
            if latency:
                lat.append(latency)
        lat.sort()
        q = lambda f: round(lat[min(len(lat) - 1, int(f * len(lat)))], 1) if lat else None
        return {**totals, "days": [{"day": k, **v} for k, v in sorted(days.items())], "mix": mix,
                "latency_p50_ms": q(0.5), "latency_p90_ms": q(0.9)}

    def spent(self, user_id: int) -> float:
        with self.lock:
            return float(self.db.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM traces WHERE user_id = ? "
                                         "AND COALESCE(billing, 'service') != 'own_key'", (user_id,)).fetchone()[0])

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
