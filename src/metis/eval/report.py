"""Metrics from replay rows (WP-18). Pure functions, tested on a tiny example."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def session_ci(values: np.ndarray, groups: np.ndarray, seed: int = 20261020, draws: int = 2000) -> tuple[float, float, float]:
    """Mean and 95% interval, whole sessions resampled. NaN values are left out."""
    keep = ~np.isnan(values)
    values, groups = values[keep], np.unique(groups[keep], return_inverse=True)[1]
    sums, sizes = np.bincount(groups, values), np.bincount(groups)
    picks = np.random.default_rng(seed).integers(0, len(sizes), (draws, len(sizes)))
    means = sums[picks].sum(1) / sizes[picks].sum(1)
    return float(values.mean()), *np.percentile(means, [2.5, 97.5])


def metrics(rows: pd.DataFrame, groups: np.ndarray) -> dict[str, Any]:
    mean, low, high = session_ci(rows.passed.to_numpy(float), groups)
    return {"n": len(rows), "pass": mean, "pass_low": low, "pass_high": high, "cost_1k": rows.cost.mean() * 1000,
            "p50": float(rows.latency.quantile(0.5)), "p90": float(rows.latency.quantile(0.9)), "p99": float(rows.latency.quantile(0.99)),
            "cache_rate": float(rows.cached.mean()), "escalation_rate": float((rows.escalations > 0).mean()),
            "failed": float((rows.status != "ok").mean()), "failovers": int(((rows.tried > 1) & (rows.escalations == 0) & (rows.reasons == 0)).sum()),
            "shares": rows.model.value_counts(normalize=True).to_dict()}
