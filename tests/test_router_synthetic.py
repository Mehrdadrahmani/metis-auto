"""WP-05 step 9: the whole method on data with a planted answer."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))

from metis.eval.baselines import ZeroRouter
from metis.eval.metrics import area, best_single, qnc, sweep
from metis.eval.stats import bootstrap
from metis.router.fingerprints import fingerprints
from metis.router.kmeans import assign, candidate_ks, fit_all
from metis.router.route import dev_pool, normalize_costs
from metis.router.select_k import select_k
from metis.router.select_lambda import lambda_grid, select_lambda
from synthetic import COSTS, FLAT, MODELS, make_bed

SEED = 20261020
C_HAT = normalize_costs(COSTS)
LAMS = lambda_grid()


def build(bed):
    ks = [1, *candidate_ks(len(bed.val.emb))]
    fitted = fit_all(bed.train.emb, ks, SEED, n_init=3)
    labels = {k: assign(bed.val.emb, m.centroids) for k, m in fitted.items()}
    choice = select_k(labels, bed.val.losses, C_HAT, LAMS, seed=SEED, groups=bed.val.sessions)
    # K = 3 is the planted answer. The tests below check the fit and routing at the true K; the
    # choice of K has its own tests (open rule question, Q-025).
    return choice, fitted[3], fingerprints(bed.val.losses, labels[3], 3)


def area_difference(bed, fitted, fp):
    """Bootstrap of (UniRoute - ZeroRouter) area on test, sessions resampled, Psi held fixed."""
    test_labels = assign(bed.test.emb, fitted.centroids)
    zero = ZeroRouter(bed.val.losses, C_HAT)
    c_min, c_max = C_HAT.min(), C_HAT.max()

    def statistic(idx):
        costs, qualities = sweep(test_labels[idx], fp.psi, C_HAT, LAMS, bed.test.losses[idx])
        z_costs, z_qualities = zero.curve(bed.test.emb[idx], LAMS, bed.test.losses[idx])
        return area(costs, qualities, c_min, c_max) - area(z_costs, z_qualities, c_min, c_max)

    return bootstrap(statistic, bed.test.sessions, n_boot=2000, seed=SEED)


@pytest.fixture(scope="module")
def structured():
    bed = make_bed(SEED)
    return bed, *build(bed)


@pytest.mark.xfail(
    strict=True, reason="Q-025: the spec's argmax rule finds K = 3 in 12 of 100 runs"
)
def test_k_star_is_the_planted_three(structured):
    _, choice, _, _ = structured
    assert choice.k_star == 3


def test_k_above_one_helps_and_extra_clusters_add_nothing_real(structured):
    _, choice, _, _ = structured
    assert choice.mean_area[3] > choice.mean_area[1] + 0.05
    spread = choice.areas[3].std()
    assert all(abs(choice.mean_area[k] - choice.mean_area[3]) < spread for k in range(4, 9))


def test_fingerprints_recover_the_planted_rates(structured):
    bed, _, fitted, fp = structured
    train_labels = assign(bed.train.emb, fitted.centroids)
    # Name each cluster by the true type most of its prompts have.
    planted = np.array([np.bincount(bed.train.types[train_labels == k]).argmax() for k in range(3)])
    assert sorted(planted.tolist()) == [0, 1, 2]
    truth = bed.rates[planted]
    true_se = np.sqrt(truth * (1 - truth) / fp.counts[:, None])
    z = np.abs(fp.psi - truth) / true_se
    # 12 cells: one beyond 2 SE is expected by chance, so "all of them" would be the wrong test.
    assert (z <= 2).mean() >= 0.75
    assert (z <= 3).all()


def test_uniroute_beats_zerorouter_on_structure(structured):
    bed, _, fitted, fp = structured
    result = area_difference(bed, fitted, fp)
    assert result.estimate > 0
    assert result.excludes_zero()


def test_uniroute_reaches_best_quality_for_less(structured):
    bed, _, fitted, fp = structured
    labels = assign(bed.test.emb, fitted.centroids)
    costs, qualities = sweep(labels, fp.psi, C_HAT, LAMS, bed.test.losses)
    best = best_single(bed.val.losses, C_HAT)
    assert MODELS[best] == "strong"
    q_best = 1 - bed.test.losses[:, best].mean()
    # Within 1 point: the strong model's true rate is matched, and exact QNC can miss by one
    # prompt in 300, so it reports "never reached" (see the WP-05 report).
    assert qnc(costs, qualities, q_best - 0.01, C_HAT[best]) < 0.1


def test_no_structure_gives_no_gain():
    bed = make_bed(SEED, rates=FLAT)
    _, fitted, fp = build(bed)
    result = area_difference(bed, fitted, fp)
    assert result.low <= 0 <= result.high


def test_new_model_changes_only_its_row_and_lambda(structured):
    bed, _choice, fitted, fp = structured
    labels = assign(bed.val.emb, fitted.centroids)
    pool = dev_pool(MODELS, {"mid": "holdout"})
    k = fp.psi.shape[0]
    hidden = fingerprints(bed.val.losses[:, pool], labels, k)
    np.testing.assert_array_equal(hidden.psi, fp.psi[:, pool])
    target = 0.3
    before = select_lambda(
        LAMS,
        *sweep(labels, hidden.psi, C_HAT[pool], LAMS, bed.val.losses[:, pool]),
        "budget",
        target,
    )
    after = select_lambda(
        LAMS, *sweep(labels, fp.psi, C_HAT, LAMS, bed.val.losses), "budget", target
    )
    assert before.feasible and after.feasible
    assert after.quality >= before.quality - 0.03


def test_dev_pool_is_respected_when_choosing_k(structured):
    bed, _, fitted, _ = structured
    labels = {3: assign(bed.val.emb, fitted.centroids)}
    pool = dev_pool(MODELS, {"mid": "holdout"})
    hidden = bed.val.losses.copy()
    hidden[:, 2] = 1 - hidden[:, 2]  # a change in the hidden model must not matter
    a = select_k(labels, bed.val.losses, C_HAT, LAMS, seed=SEED, repeats=3, pool=pool)
    b = select_k(labels, hidden, C_HAT, LAMS, seed=SEED, repeats=3, pool=pool)
    np.testing.assert_array_equal(a.areas[3], b.areas[3])
