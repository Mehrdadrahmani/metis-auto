"""WP-05 steps 2-4: K-means, fingerprints, Bradley-Terry, routing."""

import inspect

import numpy as np
import pytest

from metis.config import load_config
from metis.router.bt import closed_form_psi, fit_bt
from metis.router.fingerprints import fingerprints
from metis.router.kmeans import assign, candidate_ks, cluster_counts, fit_all, fit_kmeans
from metis.router.route import (
    Router,
    cluster_choices,
    dev_pool,
    next_best,
    normalize_costs,
    rank_models,
    route,
)
from metis.router.select_k import halvings, select_k
from metis.router.select_lambda import lambda_grid

SEED = 20261020


def blobs(n=300, k=3, dim=8, seed=SEED):
    rng = np.random.default_rng(seed)
    centers = np.eye(dim)[:k] * 5
    truth = rng.integers(k, size=n)
    return centers[truth] + rng.normal(size=(n, dim)) * 0.2, truth


def test_candidates_follow_the_paper():
    assert candidate_ks(400) == [3, 4, 5, 6, 7, 8]
    assert candidate_ks(800)[-1] == 16
    assert candidate_ks(60) == []


def test_kmeans_recovers_blobs_and_is_repeatable():
    x, truth = blobs()
    a, b = fit_kmeans(x, 3, SEED), fit_kmeans(x, 3, SEED)
    np.testing.assert_array_equal(a.centroids, b.centroids)
    labels = assign(x, a.centroids)
    pairs = set(zip(truth.tolist(), labels.tolist(), strict=True))
    assert len(pairs) == 3


def test_assign_is_nearest_centroid():
    x, _ = blobs()
    centroids = fit_kmeans(x, 4, SEED).centroids
    brute = ((x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
    np.testing.assert_array_equal(assign(x, centroids), brute)


def test_k1_is_the_mean_and_counts_keep_empty_clusters():
    x, _ = blobs()
    models = fit_all(x, [1, 3], SEED)
    np.testing.assert_allclose(models[1].centroids[0], x.mean(axis=0))
    assert models[1].inertia > models[3].inertia
    np.testing.assert_array_equal(cluster_counts(np.array([0, 0, 2]), 4), [2, 0, 1, 0])


def test_alpha_zero_is_paper_eq12_exactly():
    rng = np.random.default_rng(SEED)
    losses = rng.integers(2, size=(200, 4)).astype(float)
    labels = rng.integers(3, size=200)
    fp = fingerprints(losses, labels, 3)
    for k in range(3):
        np.testing.assert_array_equal(fp.psi[k], losses[labels == k].mean(axis=0))
    np.testing.assert_array_equal(fp.counts, np.bincount(labels, minlength=3))


def test_empty_cluster_gets_overall_rate_and_is_reported():
    losses = np.array([[1.0, 0.0], [0.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    labels = np.array([0, 0, 2, 2])
    fp = fingerprints(losses, labels, 3)
    assert fp.empty_clusters == (1,)
    np.testing.assert_array_equal(fp.psi[1], [0.5, 0.0])
    assert np.isnan(fp.se[1]).all()


def test_smoothing_is_only_an_option_and_shrinks_to_overall():
    losses = np.array([[1.0], [1.0], [0.0], [0.0], [0.0], [0.0]])
    labels = np.array([0, 0, 1, 1, 1, 1])
    psi = fingerprints(losses, labels, 2, alpha=2).psi[:, 0]
    overall = 2 / 6
    np.testing.assert_allclose(psi, [(2 + 2 * overall) / 4, (0 + 2 * overall) / 6])


def test_ceiling_flag_and_range():
    losses = np.zeros((10, 3))
    losses[5:, 1] = 1
    fp = fingerprints(losses, np.array([0] * 5 + [1] * 5), 2)
    assert fp.ceiling_clusters == (0,)
    assert fp.psi.min() >= 0 and fp.psi.max() <= 1
    with pytest.raises(ValueError):
        fingerprints(losses + 2, np.zeros(10, dtype=int), 1)


def test_bt_fit_equals_closed_form_and_anchor_row():
    rng = np.random.default_rng(SEED)
    outcomes = rng.choice([0.0, 0.5, 1.0], size=(400, 4), p=[0.5, 0.1, 0.4])
    labels = rng.integers(4, size=400)
    fit = fit_bt(outcomes, labels, 4, anchor=3)
    closed = closed_form_psi(outcomes, labels, 4, anchor=3)
    assert np.abs(fit.psi - closed).max() < 1e-6
    np.testing.assert_array_equal(fit.psi[:, 3], 0.5)
    np.testing.assert_array_equal(fit.beta[:, 3], 0.0)
    assert fit.psi.min() > 0 and fit.psi.max() < 1


def test_bt_handles_all_wins_and_empty_clusters():
    outcomes = np.ones((20, 3))
    labels = np.array([0] * 10 + [2] * 10)
    fit = fit_bt(outcomes, labels, 3, anchor=0)
    closed = closed_form_psi(outcomes, labels, 3, anchor=0)
    assert fit.empty_clusters == (1,)
    assert np.abs(fit.psi - closed).max() < 1e-6
    with pytest.raises(ValueError):
        fit_bt(outcomes, labels, 3, anchor=0, alpha=0)


def app_b_router():
    return Router(
        models=("S", "M", "C"),
        centroids=np.eye(3),  # coding, literature, chat
        psi=np.array([[0.50, 0.62, 0.85], [0.50, 0.80, 0.92], [0.50, 0.52, 0.55]]),
        c_hat=np.array([1.0, 0.30, 0.05]),
    )


def test_spec_appendix_b_worked_example():
    router = app_b_router()
    chat = route(np.array([0, 0, 1.0]), ["S", "M", "C"], router, 0.4)
    assert chat.model == "C" and chat.cluster == 2
    assert chat.scores == pytest.approx({"S": 0.90, "M": 0.64, "C": 0.57})
    lit = route(np.array([0, 1.0, 0]), ["S", "M", "C"], router, 0.4)
    assert lit.model == "S"
    assert lit.scores == pytest.approx({"S": 0.90, "M": 0.92, "C": 0.94})


def test_failover_order_and_availability():
    router = app_b_router()
    d = route(np.array([0, 0, 1.0]), ["S", "M", "C", "unknown"], router, 0.4)
    assert d.ranking == ("C", "M", "S")
    assert next_best(d, ["C"]) == "M"
    assert next_best(d, ["C", "M", "S"]) is None
    assert route(np.array([0, 0, 1.0]), ["S", "M"], router, 0.4).model == "M"
    with pytest.raises(ValueError):
        route(np.array([0, 0, 1.0]), ["unknown"], router, 0.4)


def test_ties_go_to_the_cheaper_model():
    c_hat = np.array([1.0, 0.2, 0.5])
    psi = np.array([[0.3, 0.3, 0.3]])
    router = Router(("A", "B", "C"), np.ones((1, 1)), psi, c_hat)
    assert route(np.array([1.0]), "ABC", router, 0).model == "B"
    # 0.1 + 0.2 and 0.3 differ only by rounding error.
    scores = np.array([0.1 + 0.2, 0.3])
    assert rank_models(scores, np.array([0.5, 0.1]))[0] == 1


def test_batch_and_single_routing_agree():
    router = app_b_router()
    lams = lambda_grid()
    choices = cluster_choices(router.psi, router.c_hat, lams)
    for li, lam in enumerate(lams):
        for k in range(3):
            d = route(np.eye(3)[k], router.models, router, float(lam))
            assert router.models[choices[li, k]] == d.model


def test_new_model_changes_only_its_own_column():
    rng = np.random.default_rng(SEED)
    losses = rng.integers(2, size=(120, 3)).astype(float)
    labels = rng.integers(3, size=120)
    old = fingerprints(losses, labels, 3).psi
    extended = np.column_stack([losses, rng.integers(2, size=120)])
    new = fingerprints(extended, labels, 3).psi
    np.testing.assert_array_equal(new[:, :3], old)


def test_helpers():
    np.testing.assert_allclose(normalize_costs([1.0, 2.0, 4.0]), [0.25, 0.5, 1.0])
    pool = dev_pool(["a", "b", "c"], {"b": "holdout"})
    np.testing.assert_array_equal(pool, [0, 2])


def test_halvings_keep_sessions_whole():
    groups = np.repeat(np.arange(50), 3)
    for a, b in halvings(150, 5, SEED, groups):
        assert not set(groups[a]) & set(groups[b])
        assert sorted(a.tolist() + b.tolist()) == list(range(150))
        assert abs(len(a) - len(b)) <= 6


def test_code_defaults_match_the_config():
    r = load_config("pipeline")["router"]
    assert r["select_k_repeats"] == inspect.signature(select_k).parameters["repeats"].default
    grid = lambda_grid(r["lambda_n"], r["lambda_low"], r["lambda_high"])
    np.testing.assert_array_equal(grid, lambda_grid())
