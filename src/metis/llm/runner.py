"""Resumable batch runner (WP-04 step 7, AGENTS.md §5, §7).

``fn(item)`` must go through ``get_or_call``, so finished items come back from the cache and a
rerun pays only for what is missing. Safe to kill. Prints counts and dollars only.
Budget refusals, key-guard refusals and crashes propagate and stop the batch at once.
An empty balance or dead key stops it cleanly: nothing is stored for that item, so a rerun resumes.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from metis.llm.callcache import ROOT, CallResult
from metis.llm.client import AccountBlocked
from metis.obs import tracking


@dataclass
class BatchReport:
    stage: str
    total: int
    done: int = 0
    new_calls: int = 0
    cache_hits: int = 0
    failed_new: int = 0
    failed_cached: int = 0
    truncated: int = 0
    tokens_out: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0
    stopped_reason: str | None = None

    @property
    def stopped(self) -> bool:
        return self.stopped_reason is not None


def _add(report: BatchReport, result: CallResult) -> None:
    report.done += 1
    if result.from_cache:
        report.cache_hits += 1
        report.failed_cached += result.status != "ok"
        return
    report.new_calls += 1
    report.cost_usd += result.cost_usd
    if result.status != "ok":
        report.failed_new += 1
        return
    resp = result.response
    report.truncated += resp.finish_reason == "length"
    report.tokens_out += resp.tokens_out
    report.reasoning_tokens += resp.reasoning_tokens or 0


def anomaly(report: BatchReport, limits: dict[str, Any], est_cost: float | None) -> str | None:
    """Reason to stop, judged on new calls only (cache hits say nothing about this run)."""
    n = report.new_calls
    if n < limits["min_calls"]:
        return None
    if report.failed_new / n > limits["max_failure_rate"]:
        return f"failures {report.failed_new}/{n}"
    if est_cost and report.cost_usd / n > limits["max_cost_ratio"] * est_cost:
        return f"cost per call {report.cost_usd / n:.6f} vs estimate {est_cost:.6f}"
    if report.truncated / n > limits["max_truncation_rate"]:
        return f"truncated {report.truncated}/{n}"
    out = report.tokens_out
    if out and report.reasoning_tokens / out > limits["max_reasoning_share"]:
        return f"reasoning tokens {report.reasoning_tokens}/{out}"
    return None


def _checkpoint(report: BatchReport) -> None:
    folder = Path(os.environ.get("METIS_RUNS_DIR", ROOT / "runs")) / "llm"
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f"{report.stage}.progress.json.tmp"
    tmp.write_text(json.dumps(asdict(report), indent=1), encoding="utf-8")
    tmp.replace(folder / f"{report.stage}.progress.json")


def _progress(report: BatchReport) -> None:
    print(
        f"[{report.stage}] {report.done}/{report.total} new={report.new_calls} "
        f"cached={report.cache_hits} failed={report.failed_new} ${report.cost_usd:.4f}",
        flush=True,
    )


async def _run(
    report: BatchReport,
    items: list[Any],
    fn: Callable[[Any], CallResult],
    concurrency: int,
    checkpoint_every: int,
    limits: dict[str, Any],
    est_cost: float | None,
) -> None:
    pending = iter(items)

    async def worker() -> None:
        while report.stopped_reason is None:
            item = next(pending, None)
            if item is None:
                return
            try:
                result = await asyncio.to_thread(fn, item)
            except AccountBlocked as exc:
                report.stopped_reason = report.stopped_reason or f"account: {exc.kind}"
                return
            _add(report, result)
            report.stopped_reason = report.stopped_reason or anomaly(report, limits, est_cost)
            if report.done % checkpoint_every == 0:
                _checkpoint(report)
                _progress(report)

    await asyncio.gather(*(worker() for _ in range(concurrency)))


def run_batch(
    stage: str,
    items: Iterable[Any],
    fn: Callable[[Any], CallResult],
    limits: dict[str, Any],
    concurrency: int = 4,
    checkpoint_every: int = 25,
    est_cost_per_call: float | None = None,
    params: dict[str, Any] | None = None,
) -> BatchReport:
    """Run ``fn`` over ``items``. Check ``report.stopped`` afterwards: a stop is not a success."""
    todo = [x for x in items if x is not None]
    report = BatchReport(stage=stage, total=len(todo))
    start = time.perf_counter()
    with tracking.batch_run(stage, params or {}) as log_metrics:
        try:
            asyncio.run(
                _run(report, todo, fn, concurrency, checkpoint_every, limits, est_cost_per_call)
            )
        finally:
            report.seconds = round(time.perf_counter() - start, 3)
            _checkpoint(report)
            log_metrics(
                {
                    "calls": report.new_calls,
                    "cache_hits": report.cache_hits,
                    "failures": report.failed_new + report.failed_cached,
                    "cost_usd": report.cost_usd,
                }
            )
    _progress(report)
    return report
