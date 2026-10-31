"""S10: choose lambda on validation, for a budget or for a quality target."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LambdaChoice:
    lam: float
    cost: float
    quality: float
    mode: str  # "budget" | "quality"
    target: float
    feasible: bool  # False: nothing met the target, so this is the closest point


def lambda_grid(n: int = 60, low: float = 1e-3, high: float = 1e2) -> np.ndarray:
    """{0} plus `n` log-spaced values, ascending."""
    return np.concatenate(([0.0], np.logspace(np.log10(low), np.log10(high), n)))


def select_lambda(
    lams: np.ndarray, costs: np.ndarray, qualities: np.ndarray, mode: str, target: float
) -> LambdaChoice:
    """Budget: smallest lambda with Cost <= target. Quality: largest with Quality >= target."""
    lams = np.asarray(lams, dtype=float)
    if np.any(np.diff(lams) <= 0):
        raise ValueError("lambda grid must be strictly increasing")
    if mode == "budget":
        ok = np.flatnonzero(costs <= target)
        feasible = len(ok) > 0
        # Without a feasible point: the lowest cost, and the largest lambda among equals.
        i = int(ok[0]) if feasible else len(lams) - 1 - int(np.argmin(costs[::-1]))
    elif mode == "quality":
        ok = np.flatnonzero(qualities >= target)
        feasible = len(ok) > 0
        i = int(ok[-1]) if feasible else len(lams) - 1 - int(np.argmax(qualities[::-1]))
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return LambdaChoice(
        float(lams[i]), float(costs[i]), float(qualities[i]), mode, target, feasible
    )
