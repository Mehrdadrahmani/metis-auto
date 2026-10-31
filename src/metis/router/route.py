"""Online routing rule (spec section 5, paper Eq. 8/11): s(h) = Psi_k(h) + lambda * c_hat(h)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from metis.router.kmeans import assign

TIE_DECIMALS = 12  # scores this close are a tie, and the cheaper model wins


@dataclass(frozen=True)
class Router:
    """The part of the artifact that routing needs."""

    models: tuple[str, ...]
    centroids: np.ndarray  # (K, D)
    psi: np.ndarray  # (K, N)
    c_hat: np.ndarray  # (N,)

    def __post_init__(self) -> None:
        expected = (len(self.centroids), len(self.models))
        if self.psi.shape != expected or len(self.c_hat) != len(self.models):
            raise ValueError(f"psi {self.psi.shape} or c_hat do not match {expected}")


@dataclass(frozen=True)
class RouteDecision:
    model: str
    cluster: int
    scores: dict[str, float]
    ranking: tuple[str, ...]  # best first, the failover and escalation order


def normalize_costs(costs: Sequence[float]) -> np.ndarray:
    """c_hat(h) = c(h) / max c."""
    costs = np.asarray(costs, dtype=float)
    return costs / costs.max()


def rank_models(scores: np.ndarray, c_hat: np.ndarray) -> np.ndarray:
    """Model indices, best first; ties go to the cheaper model, then to the lower index."""
    by_cost = np.argsort(c_hat, kind="stable")
    return by_cost[np.argsort(np.round(scores[by_cost], TIE_DECIMALS), kind="stable")]


def cluster_choices(psi: np.ndarray, c_hat: np.ndarray, lams: np.ndarray) -> np.ndarray:
    """Best model for every (lambda, cluster), same rule as `rank_models`; shape (L, K)."""
    by_cost = np.argsort(c_hat, kind="stable")
    lams = np.asarray(lams, dtype=float)[:, None, None]
    scores = psi[None, :, by_cost] + lams * c_hat[by_cost]
    return by_cost[np.round(scores, TIE_DECIMALS).argmin(axis=2)]  # argmin keeps the first


def route(x_emb: np.ndarray, available: Iterable[str], router: Router, lam: float) -> RouteDecision:
    """Pick the model for one embedded prompt; models without a fingerprint are skipped."""
    allowed = set(available)
    pool = np.array([i for i, m in enumerate(router.models) if m in allowed], dtype=int)
    if len(pool) == 0:
        raise ValueError("no available model has a fingerprint")
    k = int(assign(np.asarray(x_emb)[None, :], router.centroids)[0])
    scores = router.psi[k, pool] + lam * router.c_hat[pool]
    order = pool[rank_models(scores, router.c_hat[pool])]
    return RouteDecision(
        model=router.models[order[0]],
        cluster=k,
        scores={router.models[i]: float(s) for i, s in zip(pool, scores, strict=True)},
        ranking=tuple(router.models[i] for i in order),
    )


def next_best(decision: RouteDecision, tried: Iterable[str]) -> str | None:
    """Next model after failures or an escalation; None when every model was tried."""
    used = set(tried)
    return next((m for m in decision.ranking if m not in used), None)


def dev_pool(models: Sequence[str], exp_roles: Mapping[str, str]) -> np.ndarray:
    """Indices of the models that may be used to choose K and lambda (holdout demo, PLAN M4)."""
    return np.array([i for i, m in enumerate(models) if exp_roles.get(m) != "holdout"], dtype=int)
