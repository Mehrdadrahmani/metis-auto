"""WP-05 steps 7, 8, 10: baselines, statistics, artifact."""

import numpy as np
import pytest

from metis.embed.store import VectorStore
from metis.eval.baselines import (
    AlwaysModel,
    KNNRouter,
    LogisticRouter,
    UniRoute,
    ZeroRouter,
    always_best,
    always_cheapest,
    lower_hull,
    neighbor_order,
    tune_knn_k,
)
from metis.eval.metrics import area
from metis.eval.stats import (
    balanced_accuracy,
    bootstrap,
    cohen_kappa,
    fingerprint_stability,
    mcnemar_exact,
    separability,
    session_resample,
    spearman,
    wilson_ci,
)
from metis.router.artifact import Meta, RouterArtifact, load_artifact, save_artifact
from metis.router.route import route
from metis.router.select_lambda import lambda_grid

SEED = 20261020
C_HAT = np.array([0.03, 0.05, 0.13, 1.0])


def test_hull_drops_dominated_and_not_convex_models():
    costs = np.array([0.1, 0.2, 0.3, 1.0])
    # Model 1 sits above the line from 0 to 2; model 3 costs more without being better.
    assert lower_hull(costs, np.array([0.5, 0.45, 0.2, 0.25])) == [0, 2]
    assert lower_hull(costs, np.array([0.5, 0.3, 0.2, 0.1])) == [0, 1, 2, 3]


def test_zero_router_mix_follows_the_spec_formula():
    losses = np.column_stack([np.ones(10) * 0.5, np.ones(10) * 0.1])
    zero = ZeroRouter(losses, np.array([0.2, 1.0]))
    m1, m2, p1 = zero.mix(0.4)
    assert (m1, m2) == (0, 1)
    assert p1 == pytest.approx((1.0 - 0.4) / (1.0 - 0.2))
    assert zero.mix(0.1) == (0, 0, 1.0)
    assert zero.mix(2.0) == (1, 1, 1.0)
    chosen = zero.choose_budget(100_000, 0.4, np.random.default_rng(SEED))
    assert zero.c_hat[chosen].mean() == pytest.approx(0.4, abs=0.01)


def test_always_routers():
    losses = np.array([[1.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 0.0]])
    assert always_cheapest(losses, C_HAT).model == 0
    assert always_best(losses, C_HAT).model == 1  # ties with model 3, which costs more
    router = AlwaysModel(2, losses.mean(axis=0), C_HAT)
    np.testing.assert_array_equal(router.choose(np.zeros((3, 2)), 5.0), [2, 2, 2])
    costs, qualities = router.curve(np.zeros((2, 2)), lambda_grid(), losses)
    assert costs.tolist() == [0.13] and qualities.tolist() == [0.0]


def test_uniroute_interface_matches_route():
    centroids = np.eye(2)
    psi = np.array([[0.1, 0.1, 0.1, 0.1], [0.9, 0.5, 0.4, 0.1]])
    router = UniRoute(centroids, psi, C_HAT)
    x = np.array([[1.0, 0], [0, 1.0]])
    assert router.choose(x, 0.2).tolist() == [0, 3]
    np.testing.assert_array_equal(router.predict_loss(x), psi)


def knn_setup(n=120):
    rng = np.random.default_rng(SEED)
    types = rng.integers(2, size=n)
    emb = np.eye(8)[types] + rng.normal(size=(n, 8)) * 0.1
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    ids = [f"p{i}" for i in range(n)]
    losses = np.column_stack([types, 1 - types, np.zeros(n), np.zeros(n)]).astype(float)
    store = VectorStore("test", 8, path=None)
    store.upsert(ids, emb)
    return store, ids, emb, losses


def test_knn_matches_numpy_and_recovers_types():
    store, ids, emb, losses = knn_setup()
    order = neighbor_order(store, ids, emb)
    brute = np.argsort(-(emb @ emb.T), axis=1, kind="stable")
    assert (order[:, :10] == brute[:, :10]).mean() > 0.99
    k, means = tune_knn_k(order, losses, C_HAT, lambda_grid(), seed=SEED, repeats=3)
    assert k in means and set(means) == {5, 10, 20, 40}  # 80 is above N_val / 3
    router = KNNRouter(store, ids, losses, C_HAT, k)
    gamma = router.predict_loss(emb[:3])
    assert gamma.shape == (3, 4)
    np.testing.assert_allclose(gamma[0], losses[order[0, :k]].mean(axis=0))
    store.close()


def test_logistic_learns_the_type_and_handles_a_constant_model():
    _, _, emb, losses = knn_setup()
    router = LogisticRouter(emb, losses, C_HAT, seed=SEED)
    gamma = router.predict_loss(emb)
    assert ((gamma[:, 0] > 0.5) == (losses[:, 0] == 1)).mean() > 0.95
    np.testing.assert_array_equal(gamma[:, 3], 0.0)
    with pytest.raises(ValueError):
        LogisticRouter(emb, losses * 0.5, C_HAT, seed=SEED)


def test_session_resample_keeps_sessions_whole():
    groups = np.repeat(np.arange(20), 3)
    draw = session_resample(groups, SEED)
    for _ in range(5):
        idx = draw()
        assert len(idx) == 60
        counts = np.bincount(groups[idx], minlength=20)
        assert set(counts % 3) == {0}


def test_session_bootstrap_widens_on_correlated_sessions():
    rng = np.random.default_rng(SEED)
    groups = np.repeat(np.arange(100), 3)
    values = np.repeat(rng.normal(size=100), 3) + rng.normal(size=300) * 0.1
    whole = bootstrap(lambda i: float(values[i].mean()), groups, n_boot=2000)
    single = bootstrap(lambda i: float(values[i].mean()), np.arange(300), n_boot=2000)
    assert (whole.high - whole.low) > 1.4 * (single.high - single.low)


def test_session_bootstrap_covers_the_truth_on_correlated_sessions():
    covered = []
    groups = np.repeat(np.arange(50), 3)
    for seed in range(200):
        rng = np.random.default_rng(seed)
        values = np.repeat(rng.normal(size=50), 3) + rng.normal(size=150) * 0.1
        result = bootstrap(lambda i, v=values: float(v[i].mean()), groups, n_boot=300, seed=seed)
        covered.append(result.low <= 0 <= result.high)
    assert 0.88 <= np.mean(covered) <= 0.99


def test_bootstrap_is_seeded_and_reports_a_paired_difference():
    a = np.arange(100.0)
    run = [bootstrap(lambda i: float((a[i] + 1 - a[i]).mean()), np.arange(100), 100) for _ in "ab"]
    assert run[0] == run[1]
    assert run[0].estimate == pytest.approx(1) and run[0].low == pytest.approx(1)
    assert run[0].excludes_zero()


def test_mcnemar_exact_by_hand():
    a = np.array([1, 1, 1, 1, 1, 0, 1, 0], bool)
    b = np.array([0, 0, 0, 0, 0, 1, 1, 0], bool)
    only_a, only_b, p = mcnemar_exact(a, b)
    assert (only_a, only_b) == (5, 1)
    assert p == pytest.approx(2 * (1 + 6) / 64)
    assert mcnemar_exact(a, a) == (0, 0, 1.0)


def test_wilson_kappa_accuracy_spearman():
    low, high = wilson_ci(8, 10)
    assert (low, high) == pytest.approx((0.4902, 0.9433), abs=1e-3)
    assert wilson_ci(0, 0) == (0.0, 1.0)
    truth = np.array([1, 1, 1, 1, 0, 0])
    guess = np.array([1, 1, 1, 0, 0, 1])
    assert balanced_accuracy(truth, np.ones(6)) == 0.5
    assert balanced_accuracy(truth, guess) == pytest.approx((0.75 + 0.5) / 2)
    assert cohen_kappa(truth, truth) == 1
    assert cohen_kappa(truth, guess) == pytest.approx((4 / 6 - 5 / 9) / (1 - 5 / 9))
    assert spearman(np.arange(5), np.arange(5) ** 3) == pytest.approx(1)


def test_criteria_c_and_d():
    rng = np.random.default_rng(SEED)
    labels = rng.integers(3, size=600)
    rates = np.array([[0.1, 0.9], [0.5, 0.5], [0.9, 0.1]])
    losses = (rng.random((600, 2)) < rates[labels]).astype(float)
    assert fingerprint_stability(losses, labels, 3, seed=SEED) > 0.9
    psi = np.array([[0.1, 0.9], [0.5, 0.5], [0.9, 0.1]])
    assert separability(psi, np.array([200, 200, 200])) == pytest.approx(2 / 3)
    assert separability(psi, np.array([200, 0, 200])) == 1.0


def meta(**changes):
    values = {
        "method": "point",
        "embedder_id": "jina-test",
        "k_star": 2,
        "cluster_names": ("a", "b"),
        "models": ("m0", "m1"),
        "prices": {"m0": 0.1, "m1": 1.0},
        "lam": 0.3,
        "lambda_mode": "budget",
        "lambda_target": 0.5,
        "router_type": "uniroute",
        "hashes": {"val_set": "x", "gen_config": "y", "judge_config": "z"},
        "build_date": "2026-10-31",
        "tau": 7.0,
    }
    return Meta(**{**values, **changes})


def artifact(**changes):
    return RouterArtifact(
        meta=meta(**changes),
        centroids=np.eye(2),
        psi=np.array([[0.1, 0.2], [0.9, 0.2]]),
        counts=np.array([10, 20]),
        c_hat=np.array([0.1, 1.0]),
    )


def test_artifact_round_trip_routes_the_same(tmp_path):
    original = artifact()
    folder = save_artifact(original, tmp_path / "v1")
    loaded = load_artifact(folder)
    assert loaded.meta == original.meta
    for name in ("centroids", "psi", "counts", "c_hat"):
        np.testing.assert_array_equal(getattr(loaded, name), getattr(original, name))
    x = np.array([0.0, 1.0])
    assert route(x, ["m0", "m1"], loaded.router(), 0.3) == route(
        x, ["m0", "m1"], original.router(), 0.3
    )


def test_artifact_refuses_tampering_and_overwriting(tmp_path):
    folder = save_artifact(artifact(), tmp_path / "v1")
    with pytest.raises(FileExistsError):
        save_artifact(artifact(), folder)
    np.save(folder / "psi.npy", np.zeros((2, 2)))
    with pytest.raises(ValueError, match="hash"):
        load_artifact(folder)


def test_artifact_checks_its_fields():
    with pytest.raises(ValueError):
        artifact(tau=None)
    with pytest.raises(ValueError):
        artifact(method="pair", anchor="other")
    with pytest.raises(ValueError):
        artifact(cluster_names=("only-one",))
    with pytest.raises(ValueError):
        artifact(router_type="unknown")
    assert artifact(method="pair", anchor="m1", tau=None).meta.anchor == "m1"


def test_area_of_baselines_is_comparable():
    losses = np.random.default_rng(SEED).integers(2, size=(50, 4)).astype(float)
    zero = ZeroRouter(losses, C_HAT)
    costs, qualities = zero.curve(np.zeros((50, 2)), lambda_grid(), losses)
    assert 0 <= area(costs, qualities, C_HAT.min(), C_HAT.max()) <= 1
