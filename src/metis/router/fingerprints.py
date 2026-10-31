"""S8-PT: per-cluster fail rates. Default alpha = 0 is exactly paper Eq. 12 (DEV-7, D-054).

All tables are (K, N): rows are clusters, columns are models.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

CEILING = 0.05  # spec S8-PT: every model below this in a cluster means no room to route


@dataclass(frozen=True)
class Fingerprints:
    psi: np.ndarray  # (K, N)
    counts: np.ndarray  # (K,)
    se: np.ndarray  # (K, N); NaN for an empty cluster
    overall: np.ndarray  # (N,) the model's fail rate on the whole set
    empty_clusters: tuple[int, ...]  # filled with `overall`, to be logged by the caller
    ceiling_clusters: tuple[int, ...]


def check_inputs(losses: np.ndarray, labels: np.ndarray, k: int) -> None:
    if losses.ndim != 2 or len(losses) != len(labels):
        raise ValueError(f"losses {losses.shape} do not match labels {labels.shape}")
    if not np.isfinite(losses).all() or losses.min() < 0 or losses.max() > 1:
        raise ValueError("losses must be finite and in [0, 1]")
    if len(labels) and (labels.min() < 0 or labels.max() >= k):
        raise ValueError(f"labels outside 0..{k - 1}")


def cluster_sums(losses: np.ndarray, labels: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Sum of losses per (cluster, model), and the prompts per cluster."""
    sums = np.zeros((k, losses.shape[1]))
    np.add.at(sums, labels, losses)
    return sums, np.bincount(labels, minlength=k)


def fail_rates(losses: np.ndarray, labels: np.ndarray, k: int, alpha: float = 0.0) -> np.ndarray:
    """The Psi table alone. An empty cluster gets the model's overall rate."""
    sums, counts = cluster_sums(losses, labels, k)
    overall = losses.mean(axis=0)
    psi = np.tile(overall, (k, 1))
    filled = counts + alpha > 0
    psi[filled] = (sums[filled] + alpha * overall) / (counts[filled, None] + alpha)
    return psi


def fingerprints(
    losses: np.ndarray, labels: np.ndarray, k: int, alpha: float = 0.0
) -> Fingerprints:
    """Psi with counts, standard errors and flags. `losses` is (n, N), 1 = fail."""
    losses = np.asarray(losses, dtype=float)
    labels = np.asarray(labels)
    check_inputs(losses, labels, k)
    psi = fail_rates(losses, labels, k, alpha)
    counts = np.bincount(labels, minlength=k)
    with np.errstate(divide="ignore", invalid="ignore"):
        se = np.sqrt(psi * (1 - psi) / (counts[:, None] + alpha))
    se[counts == 0] = np.nan
    return Fingerprints(
        psi=psi,
        counts=counts,
        se=se,
        overall=losses.mean(axis=0),
        empty_clusters=tuple(int(c) for c in np.flatnonzero(counts == 0)),
        ceiling_clusters=tuple(int(c) for c in np.flatnonzero((psi < CEILING).all(axis=1))),
    )
