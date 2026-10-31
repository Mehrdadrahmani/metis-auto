"""S9: choose K by split-validation (Q-020) with R = 20 halvings (DEV-6).

Every K is scored on the same halvings, so differences between K are not halving noise. With
session ids, a session stays on one side: otherwise a session in both halves would leak (D-060).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from metis.eval.metrics import area, sweep
from metis.router.bt import closed_form_psi
from metis.router.fingerprints import fail_rates

TIE = 1e-12


@dataclass(frozen=True)
class KSelection:
    k_star: int
    mean_area: dict[int, float]  # every K scored, comparison Ks included
    areas: dict[int, np.ndarray]  # (2R,) one area per direction, for the stability check
    empty_events: int  # clusters with no prompts in a fitting half, filled with the overall rate


def halvings(
    n: int, repeats: int, seed: int, groups: np.ndarray | None = None
) -> list[tuple[np.ndarray, np.ndarray]]:
    """`repeats` random splits into two halves, as pairs of index arrays."""
    rng = np.random.default_rng(seed)
    group_ids = np.arange(n) if groups is None else np.unique(groups, return_inverse=True)[1]
    sizes = np.bincount(group_ids)
    out = []
    for _ in range(repeats):
        order = rng.permutation(len(sizes))
        in_a = np.zeros(len(sizes), dtype=bool)
        in_a[order[np.cumsum(sizes[order]) <= n / 2]] = True
        mask = in_a[group_ids]
        out.append((np.flatnonzero(mask), np.flatnonzero(~mask)))
    return out


def fit_psi(
    losses: np.ndarray,
    labels: np.ndarray,
    k: int,
    method: str = "pt",
    alpha: float | None = None,
    anchor: int | None = None,
) -> np.ndarray:
    """Psi of the active method; alpha defaults to 0 for pointwise and 2 for pairwise (spec)."""
    if method == "pt":
        return fail_rates(losses, labels, k, 0.0 if alpha is None else alpha)
    if method == "pw":
        if anchor is None:
            raise ValueError("pairwise needs the anchor")
        return closed_form_psi(1 - losses, labels, k, anchor, 2.0 if alpha is None else alpha)
    raise ValueError(f"unknown method {method!r}")


def select_k(
    val_labels: Mapping[int, np.ndarray],
    losses: np.ndarray,
    c_hat: np.ndarray,
    lams: np.ndarray,
    seed: int,
    repeats: int = 20,
    groups: np.ndarray | None = None,
    pool: Sequence[int] | None = None,
    comparison: Sequence[int] = (1,),
    method: str = "pt",
    alpha: float | None = None,
    anchor: int | None = None,
) -> KSelection:
    """K* = argmax of the mean area, ties to the smaller K.

    `val_labels` maps K to the cluster of each validation prompt. `pool` limits routing to some
    models (the `dev` models in experiment mode); `anchor` is an index into the full model list.
    Ks in `comparison` are scored but cannot win (K = 1, PLAN M14).
    """
    pool = np.arange(losses.shape[1]) if pool is None else np.asarray(pool)
    pool_losses = losses[:, pool]
    pool_cost = c_hat[pool]
    c_min, c_max = float(pool_cost.min()), float(pool_cost.max())
    pool_anchor = None if anchor is None else int(np.flatnonzero(pool == anchor)[0])

    splits = halvings(len(losses), repeats, seed, groups)
    areas: dict[int, np.ndarray] = {}
    empty = 0
    for k, labels in val_labels.items():
        scores = []
        for part_a, part_b in splits:
            for fit_on, score_on in ((part_a, part_b), (part_b, part_a)):
                psi = fit_psi(pool_losses[fit_on], labels[fit_on], k, method, alpha, pool_anchor)
                empty += k - len(np.unique(labels[fit_on]))
                costs, qualities = sweep(
                    labels[score_on], psi, pool_cost, lams, pool_losses[score_on]
                )
                scores.append(area(costs, qualities, c_min, c_max))
        areas[k] = np.array(scores)

    mean_area = {k: float(a.mean()) for k, a in areas.items()}
    eligible = sorted(k for k in val_labels if k not in comparison)
    if not eligible:
        raise ValueError("no K can be selected")
    best = max(mean_area[k] for k in eligible)
    k_star = next(k for k in eligible if mean_area[k] >= best - TIE)
    return KSelection(k_star, mean_area, areas, empty)
