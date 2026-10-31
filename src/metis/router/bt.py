"""S8-PW: per-cluster Bradley-Terry strengths against the anchor, with alpha virtual ties.

Only the anchor design is judged, so the fit has a closed form. `closed_form_psi` is the check on
the optimizer (spec S8-PW), and the cheap path used inside the K search. Tables are (K, N).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from metis.router.fingerprints import check_inputs, cluster_sums


@dataclass(frozen=True)
class BTFit:
    beta: np.ndarray  # (K, N); the anchor column is 0
    psi: np.ndarray  # (K, N); 1 - sigma(beta), the anchor column is 0.5
    counts: np.ndarray  # (K,)
    empty_clusters: tuple[int, ...]  # filled with the overall rate (D-054), not fitted


def _prepare(outcomes: np.ndarray, labels: np.ndarray, k: int, alpha: float):
    outcomes = np.asarray(outcomes, dtype=float)
    labels = np.asarray(labels)
    check_inputs(outcomes, labels, k)
    if alpha <= 0:
        raise ValueError("Bradley-Terry needs alpha > 0: an all-wins cluster has no finite fit")
    return outcomes, labels


def closed_form_psi(
    outcomes: np.ndarray, labels: np.ndarray, k: int, anchor: int, alpha: float = 2.0
) -> np.ndarray:
    """Psi_k(h) = 1 - (sum o + alpha/2) / (|C_k| + alpha); anchor = 0.5; empty cluster = overall."""
    outcomes, labels = _prepare(outcomes, labels, k, alpha)
    sums, counts = cluster_sums(outcomes, labels, k)
    psi = 1 - (sums + 0.5 * alpha) / (counts[:, None] + alpha)
    psi[counts == 0] = 1 - outcomes.mean(axis=0)
    psi[:, anchor] = 0.5
    return psi


def _objective(beta: np.ndarray, wins: np.ndarray, total: np.ndarray) -> tuple[float, np.ndarray]:
    """Mean negative log-likelihood and gradient; log sigma(b) = -log(1 + e^-b)."""
    nll = wins * np.logaddexp(0, -beta) + (total - wins) * np.logaddexp(0, beta)
    grad = total * expit(beta) - wins
    return float(nll.sum() / total.sum()), grad / total.sum()


def fit_bt(
    outcomes: np.ndarray, labels: np.ndarray, k: int, anchor: int, alpha: float = 2.0
) -> BTFit:
    """L-BFGS per cluster. `outcomes` is (n, N): 1 = h beats the anchor, 0.5 tie, 0 anchor wins."""
    outcomes, labels = _prepare(outcomes, labels, k, alpha)
    sums, counts = cluster_sums(outcomes, labels, k)
    n_models = outcomes.shape[1]
    others = np.delete(np.arange(n_models), anchor)
    beta = np.zeros((k, n_models))
    for c in np.flatnonzero(counts):
        wins = sums[c, others] + 0.5 * alpha
        total = np.full(len(others), counts[c] + alpha, dtype=float)
        res = minimize(
            _objective,
            np.zeros(len(others)),
            args=(wins, total),
            jac=True,
            method="L-BFGS-B",
            options={"ftol": 1e-15, "gtol": 1e-10, "maxiter": 500},
        )
        if not res.success:
            raise RuntimeError(f"Bradley-Terry fit failed in cluster {c}: {res.message}")
        beta[c, others] = res.x

    psi = 1 - expit(beta)
    empty = np.flatnonzero(counts == 0)
    if len(empty):
        overall = np.clip(1 - outcomes.mean(axis=0), 1e-9, 1 - 1e-9)
        psi[empty] = overall
        beta[empty] = np.log((1 - overall) / overall)
    psi[:, anchor] = 0.5
    beta[:, anchor] = 0.0
    return BTFit(beta, psi, counts, tuple(int(c) for c in empty))
