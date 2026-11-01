"""Budget guard and ledger (WP-04 step 6, PLAN E12).

``guard`` compares ledger spend + money reserved by calls in flight + the new estimate with the
hard cap and the stage approval, and returns the ``Permit`` a real call needs. Reservations live
in this object, so run only one paid process at a time. Missing prices refuse rather than guess.
"""

from __future__ import annotations

import threading
from typing import Any

from metis.config import load_config
from metis.llm.callcache import CallCache
from metis.llm.client import ModelNotReadyError, Permit, is_mock, load_models


class BudgetRefused(RuntimeError):
    """The spend is outside the hard cap or the stage approval."""


def call_cost(model: dict[str, Any], tokens_in: int, tokens_out: int) -> float:
    """USD for one call at list input price (any prompt-cache discount is ignored)."""
    if model.get("price_in") is None or model.get("price_out") is None:
        raise ModelNotReadyError(f"no price for {model.get('id')}")
    return (tokens_in * model["price_in"] + tokens_out * model["price_out"]) / 1e6


class Budget:
    def __init__(
        self,
        cache: CallCache,
        config: dict[str, Any] | None = None,
        models: dict[str, dict[str, Any]] | None = None,
    ):
        self.cache = cache
        self.config = config or load_config("budget")
        self.models = models or load_models()
        self._lock = threading.Lock()
        self._reserved: dict[str, float] = {}

    def estimate(self, stage: str, plan: list[dict[str, Any]]) -> float:
        """Plan rows: ``{model_id, calls, tokens_in, tokens_out}`` (tokens are per-call means)."""
        self._check_stage(stage)
        return sum(
            r["calls"] * call_cost(self.models[r["model_id"]], r["tokens_in"], r["tokens_out"])
            for r in plan
        )

    def _check_stage(self, stage: str) -> None:
        if stage not in self.config["approved_usd"]:
            raise BudgetRefused(f"unknown stage {stage}")

    def check(self, stage: str, estimate_usd: float) -> None:
        """Refuse without reserving anything. Use before a batch with its whole estimate."""
        self._check_stage(stage)
        with self._lock:
            self._check_locked(stage, estimate_usd)

    def _check_locked(self, stage: str, estimate_usd: float) -> None:
        total = self.cache.spent_usd() + sum(self._reserved.values()) + estimate_usd
        if total > self.config["hard_cap_usd"]:
            raise BudgetRefused(f"hard cap: {total:.4f} > {self.config['hard_cap_usd']}")
        in_stage = self.cache.spent_usd(stage) + self._reserved.get(stage, 0.0) + estimate_usd
        approved = self.config["approved_usd"][stage]
        if in_stage > approved:
            raise BudgetRefused(f"stage {stage}: {in_stage:.4f} > approved {approved}")

    def guard(self, stage: str, estimate_usd: float) -> Permit:
        """Reserve ``estimate_usd`` for one call and return its Permit, or refuse."""
        if is_mock():
            return Permit(stage, 0.0)
        if estimate_usd <= 0:
            raise BudgetRefused("a real call needs a positive estimate")
        self._check_stage(stage)
        with self._lock:
            self._check_locked(stage, estimate_usd)
            self._reserved[stage] = self._reserved.get(stage, 0.0) + estimate_usd
        return Permit(stage, estimate_usd)

    def release(self, permit: Permit) -> None:
        with self._lock:
            left = self._reserved.get(permit.stage, 0.0) - permit.reserved_usd
            self._reserved[permit.stage] = max(0.0, left)

    def ledger_report(self) -> str:
        """Markdown for MASTER_LOG.md §Budget (real spend, or mock spend in the mock store)."""
        lines = [
            "| Stage | Calls | Failed | Tokens in | Tokens out | USD |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        rows = self.cache.ledger_rows()
        for r in rows:
            lines.append(
                f"| {r['stage']} | {r['calls']} | {r['failed']} | {r['tokens_in']} "
                f"| {r['tokens_out']} | {r['usd']:.4f} |"
            )
        spent = sum(r["usd"] for r in rows)
        lines.append(f"\nSpent ${spent:.4f} of cap ${self.config['hard_cap_usd']:.2f}.")
        return "\n".join(lines)
