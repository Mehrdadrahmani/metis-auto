"""Synthetic test bed (WP-05 step 9): prompt types and model fail rates are planted, so the right
answer is known. Each cheap model is weak on one type; the strong model is good on all of them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

COSTS = np.array([0.03, 0.05, 0.13, 1.0])
MODELS = ("cheap-a", "cheap-b", "mid", "strong")
DIM = 64
# rows = types, columns = models
STRUCTURED = np.array(
    [
        [0.05, 0.05, 0.60, 0.05],
        [0.05, 0.60, 0.05, 0.05],
        [0.60, 0.05, 0.05, 0.05],
    ]
)
# Same overall rate per model as STRUCTURED, in every type.
FLAT = np.tile(STRUCTURED.mean(axis=0), (3, 1))


@dataclass(frozen=True)
class SplitData:
    emb: np.ndarray
    types: np.ndarray
    losses: np.ndarray
    sessions: np.ndarray


@dataclass(frozen=True)
class Bed:
    train: SplitData
    val: SplitData
    test: SplitData
    rates: np.ndarray


def _split(
    n: int, centers: np.ndarray, rates: np.ndarray, rng: np.random.Generator, spread: float
) -> SplitData:
    types = rng.integers(len(centers), size=n)
    emb = centers[types] + rng.normal(size=(n, centers.shape[1])) * spread
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    losses = (rng.random((n, rates.shape[1])) < rates[types]).astype(float)
    return SplitData(emb, types, losses, rng.integers(n // 2, size=n))


def make_bed(
    seed: int,
    rates: np.ndarray = STRUCTURED,
    n_train: int = 5000,
    n_val: int = 400,
    n_test: int = 300,
    spread: float = 0.05,
) -> Bed:
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(len(rates), DIM))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    return Bed(
        _split(n_train, centers, rates, rng, spread),
        _split(n_val, centers, rates, rng, spread),
        _split(n_test, centers, rates, rng, spread),
        rates,
    )
