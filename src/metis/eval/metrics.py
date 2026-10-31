"""Evaluation definitions (spec section 7): deferral curve, Pareto envelope, area, QNC.

`quality` is 1 - loss, which is the pass rate for pointwise labels and the win rate against the
anchor for pairwise labels (the anchor scores 0.5).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from metis.router.route import cluster_choices

EPS = 1e-12


@dataclass(frozen=True)
class OperatingPoint:
    cost: float
    quality: float
    shares: np.ndarray  # (N,) share of prompts sent to each model


def cost_quality(chosen: np.ndarray, c_hat: np.ndarray, losses: np.ndarray) -> OperatingPoint:
    """Measure any router from its choice per prompt, using realized losses."""
    rows = np.arange(len(chosen))
    return OperatingPoint(
        cost=float(c_hat[chosen].mean()),
        quality=float(1 - losses[rows, chosen].mean()),
        shares=np.bincount(chosen, minlength=len(c_hat)) / len(chosen),
    )


def operating_point(
    lam: float, labels: np.ndarray, psi: np.ndarray, c_hat: np.ndarray, losses: np.ndarray
) -> OperatingPoint:
    """UniRoute at one lambda."""
    chosen = cluster_choices(psi, c_hat, np.array([lam]))[0][labels]
    return cost_quality(chosen, c_hat, losses)


def sweep(
    labels: np.ndarray, psi: np.ndarray, c_hat: np.ndarray, lams: np.ndarray, losses: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Cost(lambda) and Quality(lambda) of UniRoute over a grid."""
    chosen = cluster_choices(psi, c_hat, lams)[:, labels]  # (L, n)
    costs = c_hat[chosen].mean(axis=1)
    qualities = 1 - losses[np.arange(len(labels)), chosen].mean(axis=1)
    return costs, qualities


def pareto_envelope(costs: np.ndarray, qualities: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The undominated points, cost and quality both strictly increasing."""
    costs, qualities = np.asarray(costs, float), np.asarray(qualities, float)
    order = np.lexsort((-qualities, costs))
    keep = []
    best = -np.inf
    for i in order:
        if qualities[i] > best + EPS:
            keep.append(i)
            best = qualities[i]
    return costs[keep], qualities[keep]


def envelope_quality(budget, env_costs: np.ndarray, env_qualities: np.ndarray):
    """Q~(b): linear between envelope points, flat outside them."""
    return np.interp(budget, env_costs, env_qualities)


def area(costs: np.ndarray, qualities: np.ndarray, c_min: float, c_max: float) -> float:
    """Normalized area under the envelope over the pool's cost range.

    A budget below the curve's cheapest point buys nothing, so it adds no area. Without this, one
    expensive model would get credit at budgets it cannot be run on.
    """
    env_c, env_q = pareto_envelope(costs, qualities)
    if c_max <= c_min:
        return float(envelope_quality(c_min, env_c, env_q))
    start = max(c_min, float(env_c[0]))
    inside = env_c[(env_c > start) & (env_c < c_max)]
    grid = np.concatenate(([start], inside, [c_max]))
    return float(np.trapezoid(envelope_quality(grid, env_c, env_q), grid) / (c_max - c_min))


def best_single(losses: np.ndarray, c_hat: np.ndarray) -> int:
    """h-dagger: lowest overall loss, ties to the cheaper model."""
    mean_loss = np.round(losses.mean(axis=0), 12)
    return int(np.lexsort((c_hat, mean_loss))[0])


def qnc(costs: np.ndarray, qualities: np.ndarray, q_best: float, c_best: float) -> float:
    """Cheapest budget reaching q_best, as a share of h-dagger's cost; 1.0 if never reached."""
    env_c, env_q = pareto_envelope(costs, qualities)
    reached = np.flatnonzero(env_q >= q_best - EPS)
    if len(reached) == 0:
        return 1.0
    i = int(reached[0])
    if i == 0:
        return float(env_c[0] / c_best)
    share = (q_best - env_q[i - 1]) / (env_q[i] - env_q[i - 1])
    return float((env_c[i - 1] + share * (env_c[i] - env_c[i - 1])) / c_best)
