"""Routers compared in S11. All share one interface, so they are measured the same way:

    predict_loss(x_emb) -> (n, N) estimated loss per prompt and model
    choose(x_emb, lam)  -> (n,) chosen model index, by gamma + lambda * c_hat, ties to the cheaper
    curve(x_emb, lams, losses) -> (costs, qualities) from realized losses

Reported for comparison only: the gateway always ships UniRoute (PLAN M1).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from metis.eval.metrics import area, sweep
from metis.router.kmeans import assign
from metis.router.route import cluster_choices
from metis.router.select_k import halvings

KNN_CANDIDATES = (5, 10, 20, 40, 80)
LOGISTIC_CS = (0.01, 0.1, 1.0, 10.0, 100.0)


class LossRouter:
    """Base: anything that estimates a loss per (prompt, model)."""

    def __init__(self, c_hat: np.ndarray):
        self.c_hat = np.asarray(c_hat, dtype=float)

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def choose(self, x_emb: np.ndarray, lam: float) -> np.ndarray:
        return cluster_choices(self.predict_loss(x_emb), self.c_hat, np.array([lam]))[0]

    def curve(
        self, x_emb: np.ndarray, lams: np.ndarray, losses: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        gamma = self.predict_loss(x_emb)
        return sweep(np.arange(len(gamma)), gamma, self.c_hat, lams, losses)


class UniRoute(LossRouter):
    def __init__(self, centroids: np.ndarray, psi: np.ndarray, c_hat: np.ndarray):
        super().__init__(c_hat)
        self.centroids = centroids
        self.psi = psi

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        return self.psi[assign(x_emb, self.centroids)]


class AlwaysModel(LossRouter):
    """Always-best and always-cheapest: one model whatever the prompt or lambda."""

    def __init__(self, model: int, overall_loss: np.ndarray, c_hat: np.ndarray):
        super().__init__(c_hat)
        self.model = model
        self.overall = overall_loss

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        return np.tile(self.overall, (len(x_emb), 1))

    def choose(self, x_emb: np.ndarray, lam: float) -> np.ndarray:
        return np.full(len(x_emb), self.model)

    def curve(
        self, x_emb: np.ndarray, lams: np.ndarray, losses: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        return self.c_hat[[self.model]], 1 - losses[:, [self.model]].mean(axis=0)


def always_cheapest(val_losses: np.ndarray, c_hat: np.ndarray) -> AlwaysModel:
    return AlwaysModel(int(np.argmin(c_hat)), val_losses.mean(axis=0), c_hat)


def always_best(val_losses: np.ndarray, c_hat: np.ndarray) -> AlwaysModel:
    overall = val_losses.mean(axis=0)
    return AlwaysModel(int(np.lexsort((c_hat, np.round(overall, 12)))[0]), overall, c_hat)


def lower_hull(costs: np.ndarray, losses: np.ndarray) -> list[int]:
    """Models on the non-increasing lower convex hull of (cost, loss), cheapest first."""
    order = np.lexsort((losses, costs))
    hull: list[int] = []
    for i in order:
        if hull and costs[i] == costs[hull[-1]]:
            continue  # same cost, higher or equal loss
        while len(hull) >= 2:
            a, b = hull[-2], hull[-1]
            cross = (costs[b] - costs[a]) * (losses[i] - losses[a]) - (losses[b] - losses[a]) * (
                costs[i] - costs[a]
            )
            if cross > 0:
                break
            hull.pop()
        hull.append(int(i))
    return hull[: int(np.argmin(losses[hull])) + 1]


class ZeroRouter(LossRouter):
    """Paper App. D: ignores the prompt and mixes two neighbouring hull models."""

    def __init__(self, val_losses: np.ndarray, c_hat: np.ndarray):
        super().__init__(c_hat)
        self.overall = val_losses.mean(axis=0)
        self.hull = lower_hull(self.c_hat, self.overall)

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        return np.tile(self.overall, (len(x_emb), 1))

    def mix(self, budget: float) -> tuple[int, int, float]:
        """(m1, m2, p1): route to m1 with probability p1, else m2 (spec S11)."""
        costs = self.c_hat[self.hull]
        if budget <= costs[0]:
            return self.hull[0], self.hull[0], 1.0
        if budget >= costs[-1]:
            return self.hull[-1], self.hull[-1], 1.0
        i = int(np.searchsorted(costs, budget, side="right"))
        m1, m2 = self.hull[i - 1], self.hull[i]
        p1 = (self.c_hat[m2] - budget) / (self.c_hat[m2] - self.c_hat[m1])
        return m1, m2, float(p1)

    def choose_budget(self, n: int, budget: float, rng: np.random.Generator) -> np.ndarray:
        m1, m2, p1 = self.mix(budget)
        return np.where(rng.random(n) < p1, m1, m2)

    def curve(
        self, x_emb: np.ndarray, lams: np.ndarray, losses: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Hull models with realized quality; expected mixing is the line between them."""
        return self.c_hat[self.hull], 1 - losses[:, self.hull].mean(axis=0)


def neighbor_order(
    store: Any,
    prompt_ids: Sequence[str],
    queries: np.ndarray,
    filter: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """(n_queries, n_val): every validation index for each query, nearest first."""
    index = {p: i for i, p in enumerate(prompt_ids)}
    rows = []
    for q in queries:
        hits = store.search(q, len(prompt_ids), filter=dict(filter or {}), exact=True)
        rows.append([index[p] for p, _ in hits])
    return np.array(rows)


def tune_knn_k(
    order: np.ndarray,
    val_losses: np.ndarray,
    c_hat: np.ndarray,
    lams: np.ndarray,
    seed: int,
    repeats: int = 20,
    groups: np.ndarray | None = None,
    candidates: Sequence[int] = KNN_CANDIDATES,
) -> tuple[int, dict[int, float]]:
    """k by split-validation, capped at N_val/3; ties to the smaller k. `order` is val on val."""
    n = len(val_losses)
    usable = [k for k in candidates if k <= n / 3]
    if not usable:
        raise ValueError(f"no candidate k fits N_val = {n}")
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    scores: dict[int, list[float]] = {k: [] for k in usable}
    for part_a, part_b in halvings(n, repeats, seed, groups):
        for fit_on, score_on in ((part_a, part_b), (part_b, part_a)):
            in_fit = np.zeros(n, dtype=bool)
            in_fit[fit_on] = True
            rows = order[score_on]
            nearest = rows[in_fit[rows]].reshape(len(score_on), len(fit_on))
            for k in usable:
                top = min(k, len(fit_on))
                gamma = val_losses[nearest[:, :top]].mean(axis=1)
                costs, qualities = sweep(
                    np.arange(len(score_on)), gamma, c_hat, lams, val_losses[score_on]
                )
                scores[k].append(area(costs, qualities, c_min, c_max))
    means = {k: float(np.mean(v)) for k, v in scores.items()}
    best = max(means.values())
    return next(k for k in usable if means[k] >= best - 1e-12), means


class KNNRouter(LossRouter):
    """Paper Eq. 4: mean loss of the k nearest validation prompts (exact Qdrant search, D-048)."""

    def __init__(
        self,
        store: Any,
        prompt_ids: Sequence[str],
        val_losses: np.ndarray,
        c_hat: np.ndarray,
        k: int,
        filter: Mapping[str, Any] | None = None,
    ):
        super().__init__(c_hat)
        self.store = store
        self.index = {p: i for i, p in enumerate(prompt_ids)}
        self.val_losses = val_losses
        self.k = k
        self.filter = dict(filter or {})

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        rows = []
        for x in x_emb:
            hits = self.store.search(x, self.k, filter=self.filter, exact=True)
            rows.append(self.val_losses[[self.index[p] for p, _ in hits]].mean(axis=0))
        return np.array(rows)


class LogisticRouter(LossRouter):
    """One logistic model per LLM on the embeddings; C by 5-fold CV on val, sessions kept whole.

    Pointwise labels only: pairwise ties (0.5) are not binary.
    """

    def __init__(
        self,
        val_emb: np.ndarray,
        val_losses: np.ndarray,
        c_hat: np.ndarray,
        seed: int,
        groups: np.ndarray | None = None,
        cs: Sequence[float] = LOGISTIC_CS,
    ):
        from sklearn.linear_model import LogisticRegressionCV
        from sklearn.model_selection import StratifiedGroupKFold

        super().__init__(c_hat)
        if not np.isin(val_losses, (0.0, 1.0)).all():
            raise ValueError("logistic baseline needs binary pointwise labels")
        ids = np.arange(len(val_losses)) if groups is None else groups
        self.models: list[Any] = []
        for h in range(val_losses.shape[1]):
            y = val_losses[:, h]
            if len(np.unique(y)) == 1:  # every answer passed or failed
                self.models.append(float(y[0]))
                continue
            folds = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
            model = LogisticRegressionCV(
                Cs=list(cs),
                cv=list(folds.split(val_emb, y, ids)),
                l1_ratios=(0,),
                scoring="neg_log_loss",
                max_iter=2000,
                use_legacy_attributes=False,
            )
            self.models.append(model.fit(val_emb, y))

    def predict_loss(self, x_emb: np.ndarray) -> np.ndarray:
        columns = [
            np.full(len(x_emb), m) if isinstance(m, float) else m.predict_proba(x_emb)[:, 1]
            for m in self.models
        ]
        return np.column_stack(columns)
