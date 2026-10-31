"""WP-05 steps 5-6: curve metrics, K selection, lambda selection."""

import time

import numpy as np
import pytest

from metis.eval.metrics import (
    area,
    best_single,
    cost_quality,
    operating_point,
    pareto_envelope,
    qnc,
    sweep,
)
from metis.router.select_k import select_k
from metis.router.select_lambda import lambda_grid, select_lambda

SEED = 20261020
C_HAT = np.array([0.03, 0.05, 0.13, 1.0])


def planted(n=400, types=3, seed=SEED):
    """Cheap model fails often on type 2 only; the strong model is good everywhere."""
    rng = np.random.default_rng(seed)
    truth = rng.integers(types, size=n)
    rates = np.tile([0.05, 0.05, 0.05, 0.05], (types, 1))
    rates[types - 1, :3] = [0.7, 0.6, 0.5]
    return truth, (rng.random((n, 4)) < rates[truth]).astype(float)


def test_envelope_drops_dominated_points_and_sorts():
    c, q = pareto_envelope([0.5, 0.1, 0.3, 0.3, 0.9], [0.8, 0.5, 0.4, 0.7, 0.8])
    np.testing.assert_allclose(c, [0.1, 0.3, 0.5])
    np.testing.assert_allclose(q, [0.5, 0.7, 0.8])


def test_area_by_hand():
    # Quality rises from 0 to 1 over the whole range: a triangle.
    assert area([0, 1], [0, 1], 0, 1) == pytest.approx(0.5)
    # Flat after the best point: 0.5 * 0.5 + 0.5 * 1.
    assert area([0, 0.5], [0, 1], 0, 1) == pytest.approx(0.75)
    # Flat after a single point, and nothing below its cost.
    assert area([0.2], [0.6], 0, 1) == pytest.approx(0.48)
    assert area([1.0], [0.9], 0, 1) == pytest.approx(0.0)
    assert area([0.4], [0.6], 0.4, 0.4) == pytest.approx(0.6)


def test_qnc_by_hand():
    assert qnc([0.1, 0.5], [0.4, 0.8], q_best=0.6, c_best=1.0) == pytest.approx(0.3)
    assert qnc([0.1, 0.5], [0.4, 0.8], q_best=0.4, c_best=0.5) == pytest.approx(0.2)
    assert qnc([0.1, 0.5], [0.4, 0.8], q_best=0.9, c_best=1.0) == 1.0


def test_best_single_prefers_cheaper_on_ties():
    losses = np.array([[0.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
    assert best_single(losses, np.array([1.0, 0.5, 0.1])) == 2
    assert best_single(np.zeros((2, 2)), np.array([1.0, 0.5])) == 1


def test_sweep_matches_operating_point_and_any_router_measure():
    labels, losses = planted()
    psi = np.array([losses[labels == k].mean(axis=0) for k in range(3)])
    lams = lambda_grid()
    costs, qualities = sweep(labels, psi, C_HAT, lams, losses)
    for i in (0, 20, 40, 60):
        p = operating_point(float(lams[i]), labels, psi, C_HAT, losses)
        assert (p.cost, p.quality) == pytest.approx((costs[i], qualities[i]))
        assert p.shares.sum() == pytest.approx(1)
    always = cost_quality(np.full(len(labels), 3), C_HAT, losses)
    assert always.cost == 1.0
    assert always.quality == pytest.approx(1 - losses[:, 3].mean())
    # Extreme lambdas reach the two ends of the pool.
    assert costs[-1] == pytest.approx(C_HAT[0])
    assert costs[0] > costs[-1]


def test_routing_beats_a_single_cluster_on_planted_data():
    labels, losses = planted()
    lams = lambda_grid()
    selection = select_k(
        {1: np.zeros(400, dtype=int), 3: labels, 4: labels}, losses, C_HAT, lams, seed=SEED
    )
    assert selection.mean_area[3] > selection.mean_area[1]
    # K = 4 uses identical clusters here, so it ties and the smaller K wins.
    assert selection.k_star == 3
    assert selection.areas[3].shape == (40,)
    assert selection.empty_events >= 40  # K = 4 always has an empty cluster


def test_k1_cannot_win_even_when_it_scores_best():
    rng = np.random.default_rng(2)  # a dataset where K = 1 does score best
    losses = (rng.random((400, 4)) < np.array([0.4, 0.4, 0.4, 0.1])).astype(float)
    noise = rng.integers(3, size=400)  # same rates in every "cluster"
    selection = select_k(
        {1: np.zeros(400, dtype=int), 3: noise}, losses, C_HAT, lambda_grid(), seed=SEED
    )
    assert selection.mean_area[1] > selection.mean_area[3]
    assert selection.k_star == 3
    with pytest.raises(ValueError):
        select_k({1: noise * 0}, losses, C_HAT, lambda_grid(), seed=SEED)


def test_select_k_is_repeatable_and_respects_the_pool_and_sessions():
    labels, losses = planted()
    lams = lambda_grid()
    runs = [
        select_k({3: labels}, losses, C_HAT, lams, seed=SEED, repeats=3, pool=[1, 2, 3])
        for _ in range(2)
    ]
    np.testing.assert_array_equal(runs[0].areas[3], runs[1].areas[3])
    full = select_k({3: labels}, losses, C_HAT, lams, seed=SEED, repeats=3)
    assert not np.array_equal(runs[0].areas[3], full.areas[3])
    grouped = select_k(
        {3: labels}, losses, C_HAT, lams, seed=SEED, repeats=3, groups=np.arange(400) // 3
    )
    assert np.isfinite(grouped.areas[3]).all()


def test_select_k_pairwise_uses_the_anchor():
    labels, losses = planted()
    selection = select_k(
        {3: labels},
        losses,
        C_HAT,
        lambda_grid(),
        seed=SEED,
        repeats=2,
        method="pw",
        anchor=3,
        pool=[0, 3],
    )
    assert selection.k_star == 3
    with pytest.raises(ValueError):
        select_k({3: labels}, losses, C_HAT, lambda_grid(), seed=SEED, method="pw")


def test_lambda_grid_shape():
    grid = lambda_grid()
    assert len(grid) == 61 and grid[0] == 0
    assert grid[1] == pytest.approx(1e-3) and grid[-1] == pytest.approx(1e2)


def test_select_lambda_modes():
    lams = np.array([0.0, 0.1, 1.0, 10.0])
    costs = np.array([1.0, 0.6, 0.2, 0.1])
    quality = np.array([0.9, 0.85, 0.7, 0.5])
    budget = select_lambda(lams, costs, quality, "budget", 0.6)
    assert (budget.lam, budget.feasible) == (0.1, True)
    target = select_lambda(lams, costs, quality, "quality", 0.7)
    assert (target.lam, target.quality, target.feasible) == (1.0, 0.7, True)


def test_select_lambda_reports_an_unreachable_target():
    lams = np.array([0.0, 1.0])
    costs = np.array([1.0, 0.2])
    quality = np.array([0.9, 0.5])
    budget = select_lambda(lams, costs, quality, "budget", 0.1)
    assert (budget.lam, budget.feasible) == (1.0, False)
    target = select_lambda(lams, costs, quality, "quality", 0.95)
    assert (target.lam, target.feasible) == (0.0, False)
    with pytest.raises(ValueError):
        select_lambda(lams, costs, quality, "other", 0.5)


def test_s9_runtime_under_two_minutes():
    _, losses = planted()
    rng = np.random.default_rng(SEED)
    val_labels = {k: rng.integers(k, size=400) for k in range(3, 9)}
    val_labels[1] = np.zeros(400, dtype=int)
    start = time.perf_counter()
    select_k(val_labels, losses, C_HAT, lambda_grid(), seed=SEED)
    assert time.perf_counter() - start < 120
