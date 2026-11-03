"""SQLite call cache and ledger (WP-04 step 5, spec golden rule 2, PLAN E11).

A call is paid for at most once. Response and ledger row are written in one transaction, so the
cache and the money record cannot disagree. Mock answers live in a separate file and use separate
keys, so a fake answer can never be served to a real run.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from metis.llm.client import CallFailed, Response, is_mock

ROOT = Path(__file__).resolve().parents[3]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
  key TEXT PRIMARY KEY, status TEXT NOT NULL, stage TEXT NOT NULL, model_id TEXT NOT NULL,
  response TEXT, error_kind TEXT, cost_usd REAL NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, stage TEXT NOT NULL,
  model_id TEXT NOT NULL, key TEXT NOT NULL, status TEXT NOT NULL,
  tokens_in INTEGER NOT NULL, tokens_out INTEGER NOT NULL, cost_usd REAL NOT NULL
);
"""


def default_path() -> Path:
    if is_mock() and os.environ.get("METIS_MOCK_CACHE"):  # dry run: its own cache, never the paid one
        return Path(os.environ["METIS_MOCK_CACHE"])
    return ROOT / "cache" / ("llm_calls.mock.sqlite" if is_mock() else "llm_calls.sqlite")


def cache_key(
    model_id: str,
    api_name: str | None,
    messages: list[dict[str, Any]],
    gen_params: dict[str, Any],
    config_id: str,
) -> str:
    """sha256 of canonical JSON; prices and stage are not part of the request, so not of the key."""
    payload = {
        "model_id": model_id,
        "api_name": api_name,
        "messages": messages,
        "gen_params": gen_params,
        "config_id": config_id,
    }
    if is_mock():
        payload["mock"] = True
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


@dataclass
class CallResult:
    key: str
    status: str  # "ok" or "failed"
    from_cache: bool
    response: Response | None
    error_kind: str | None
    cost_usd: float


class CallCache:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(_SCHEMA)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def get(self, key: str) -> CallResult | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM calls WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        resp = Response(**json.loads(row["response"])) if row["response"] else None
        return CallResult(key, row["status"], True, resp, row["error_kind"], 0.0)

    def put(
        self,
        key: str,
        stage: str,
        model_id: str,
        status: str,
        response: Response | None,
        error_kind: str | None,
        cost_usd: float,
    ) -> None:
        now = time.time()
        body = json.dumps(response.to_dict(), ensure_ascii=False) if response else None
        tokens_in = response.tokens_in if response else 0
        tokens_out = response.tokens_out if response else 0
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?)",
                (key, status, stage, model_id, body, error_kind, cost_usd, now),
            )
            self._db.execute(
                "INSERT INTO ledger (ts, stage, model_id, key, status, tokens_in, tokens_out,"
                " cost_usd) VALUES (?,?,?,?,?,?,?,?)",
                (now, stage, model_id, key, status, tokens_in, tokens_out, cost_usd),
            )

    def spent_usd(self, stage: str | None = None) -> float:
        sql, args = "SELECT COALESCE(SUM(cost_usd), 0) FROM ledger", ()
        if stage is not None:
            sql, args = sql + " WHERE stage = ?", (stage,)
        with self._lock:
            return float(self._db.execute(sql, args).fetchone()[0])

    def ok_calls(self, stage: str, model_id: str) -> int:
        sql = "SELECT COUNT(*) FROM ledger WHERE stage = ? AND model_id = ? AND status = 'ok'"
        with self._lock:
            return int(self._db.execute(sql, (stage, model_id)).fetchone()[0])

    def ledger_rows(self) -> list[dict[str, Any]]:
        sql = (
            "SELECT stage, COUNT(*) calls, SUM(status != 'ok') failed, SUM(tokens_in) tokens_in,"
            " SUM(tokens_out) tokens_out, SUM(cost_usd) usd FROM ledger GROUP BY stage ORDER BY stage"
        )
        with self._lock:
            return [dict(r) for r in self._db.execute(sql).fetchall()]


class NewCallRefused(RuntimeError):
    """A paid call was needed while replay-only mode (METIS_ASSERT_NO_NEW_CALLS=1) is on."""


def get_or_call(
    cache: CallCache,
    budget: Any,
    stage: str,
    model_id: str,
    messages: list[dict[str, Any]],
    gen_params: dict[str, Any],
    config_id: str,
    estimate_usd: float,
    send: Callable[..., Response],
    retry_failed: bool = False,
    prompt_id: str | None = None,
) -> CallResult:
    """Return the stored result, or pay for one call through the budget guard and store it.

    Failed calls are stored and returned as they are until ``retry_failed=True``. A failed call
    costs $0 in the ledger: a provider may still bill a timed-out call, so check its invoice.
    """
    from metis.llm.budget import call_cost  # budget imports this module

    model = budget.models[model_id]
    key = cache_key(model_id, model.get("api_name"), messages, gen_params, config_id)
    found = cache.get(key)
    if found is not None and (found.status == "ok" or not retry_failed):
        return found

    if os.environ.get("METIS_ASSERT_NO_NEW_CALLS") == "1":  # WP-21 replay: every answer must come from the cache
        raise NewCallRefused(f"cache miss for {model_id} (stage {stage}) while METIS_ASSERT_NO_NEW_CALLS=1")
    permit = budget.guard(stage, estimate_usd)
    try:
        try:
            response = send(model_id, messages, gen_params, permit=permit, prompt_id=prompt_id)
        except CallFailed as exc:
            cache.put(key, stage, model_id, "failed", None, exc.kind, 0.0)
            return CallResult(key, "failed", False, None, exc.kind, 0.0)
        if is_mock():
            priced = {"price_in": model.get("price_in") or 0, "price_out": model.get("price_out") or 0}
            cost = call_cost(priced, response.tokens_in, response.tokens_out)
        elif response.usage_reported:
            cost = call_cost(model, response.tokens_in, response.tokens_out)
        else:
            cost = estimate_usd  # no usage from the provider: book the estimate, not zero
        cache.put(key, stage, model_id, "ok", response, None, cost)
        return CallResult(key, "ok", False, response, None, cost)
    finally:
        budget.release(permit)
