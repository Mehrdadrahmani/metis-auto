"""S5: K-means on the train embeddings, nearest-centroid assignment (paper section 5.1, DEV-7)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class KMeansModel:
    k: int
    centroids: np.ndarray  # (K, D)
    inertia: float


def candidate_ks(n_val: int) -> list[int]:
    """Paper App. G.2: {3, ..., floor(N_val / 50)}. K = 1 is a comparison only (PLAN M14)."""
    return list(range(3, n_val // 50 + 1))


def fit_kmeans(train_emb: np.ndarray, k: int, seed: int, n_init: int = 10) -> KMeansModel:
    """k-means++ with `n_init` restarts; K = 1 is the mean, no search needed."""
    train_emb = np.asarray(train_emb)
    if train_emb.ndim != 2 or len(train_emb) < k or k < 1:
        raise ValueError(f"need a 2-d array with at least k={k} rows, got {train_emb.shape}")
    if k == 1:
        mean = train_emb.mean(axis=0, keepdims=True)
        return KMeansModel(1, mean, float(((train_emb - mean) ** 2).sum()))

    from sklearn.cluster import KMeans  # not needed online, so not loaded by the gateway

    km = KMeans(n_clusters=k, init="k-means++", n_init=n_init, random_state=seed)
    km.fit(train_emb)
    return KMeansModel(k, km.cluster_centers_, float(km.inertia_))


def fit_all(
    train_emb: np.ndarray, ks: Iterable[int], seed: int, n_init: int = 10
) -> dict[int, KMeansModel]:
    return {k: fit_kmeans(train_emb, k, seed, n_init) for k in ks}


def assign(emb: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """Nearest centroid in Euclidean distance. Expands the square, so it needs no n x K x D array."""
    emb = np.asarray(emb)
    centroids = np.asarray(centroids)
    dist2 = (emb**2).sum(axis=1, keepdims=True) - 2 * emb @ centroids.T + (centroids**2).sum(axis=1)
    return dist2.argmin(axis=1)


def cluster_counts(labels: np.ndarray, k: int) -> np.ndarray:
    """Prompts per cluster; zeros are allowed (no K is dropped, D-054)."""
    return np.bincount(np.asarray(labels), minlength=k)
