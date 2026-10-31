"""WP-05 step 9 report: UniRoute and the baselines on planted synthetic data. No real data, $0.

Usage: uv run python scripts/synthetic_validation.py
Writes results/wp05_router/synthetic_validation.md and manifest.json.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from metis.config import load_config
from metis.embed.store import VectorStore
from metis.eval.baselines import (
    KNNRouter,
    LogisticRouter,
    UniRoute,
    ZeroRouter,
    always_best,
    always_cheapest,
    neighbor_order,
    tune_knn_k,
)
from metis.eval.metrics import area, best_single, qnc, sweep
from metis.eval.stats import bootstrap, separability
from metis.router.fingerprints import fail_rates, fingerprints
from metis.router.kmeans import assign, fit_all
from metis.router.route import normalize_costs
from metis.router.select_k import select_k
from metis.router.select_lambda import lambda_grid
from synthetic import COSTS, DIM, FLAT, MODELS, STRUCTURED, make_bed

OUT = ROOT / "results" / "wp05_router"
C_HAT = normalize_costs(COSTS)
LAMS = lambda_grid()
KS = [3, 4, 5, 6, 7, 8]
RUNS = 100


def rule_picks(selection) -> dict[str, int]:
    """Spec argmax, against the smallest K within one spread of the best (Q-025)."""
    means = selection.mean_area
    best = max(KS, key=lambda k: means[k])
    spread = float(selection.areas[best].std())
    return {
        "highest score (spec)": best,
        "smallest K within one spread": next(k for k in KS if means[k] >= means[best] - spread),
    }


def fit_bed(bed, seed):
    fitted = fit_all(bed.train.emb, [1, *KS], seed, n_init=3)
    labels = {k: assign(bed.val.emb, m.centroids) for k, m in fitted.items()}
    selection = select_k(labels, bed.val.losses, C_HAT, LAMS, seed=seed, groups=bed.val.sessions)
    return fitted, labels, selection


def rule_study(rates) -> tuple[dict, dict]:
    picks: dict[str, Counter] = {}
    gain: dict[str, list[float]] = {}
    for seed in range(RUNS):
        bed = make_bed(seed, rates)
        fitted, labels, selection = fit_bed(bed, seed)
        test_area = {}
        for k in KS:
            psi = fail_rates(bed.val.losses, labels[k], k)
            test_labels = assign(bed.test.emb, fitted[k].centroids)
            costs, qualities = sweep(test_labels, psi, C_HAT, LAMS, bed.test.losses)
            test_area[k] = area(costs, qualities, C_HAT.min(), C_HAT.max())
        for rule, k in rule_picks(selection).items():
            picks.setdefault(rule, Counter())[k] += 1
            gain.setdefault(rule, []).append(test_area[k] - test_area[3])
    return picks, gain


def ladder(bed, seed, k):
    """Every router on one bed, at K clusters; areas and QNC on the synthetic test split."""
    fitted = fit_all(bed.train.emb, [k], seed, n_init=10)[k]
    val_labels = assign(bed.val.emb, fitted.centroids)
    fp = fingerprints(bed.val.losses, val_labels, k)
    ids = [f"v{i}" for i in range(len(bed.val.emb))]
    store = VectorStore("synthetic", DIM, path=None)
    store.upsert(ids, bed.val.emb)
    order = neighbor_order(store, ids, bed.val.emb)
    best_k, _ = tune_knn_k(order, bed.val.losses, C_HAT, LAMS, seed=seed, groups=bed.val.sessions)
    routers = {
        "UniRoute": UniRoute(fitted.centroids, fp.psi, C_HAT),
        "ZeroRouter": ZeroRouter(bed.val.losses, C_HAT),
        f"K-NN (k = {best_k})": KNNRouter(store, ids, bed.val.losses, C_HAT, best_k),
        "Logistic": LogisticRouter(
            bed.val.emb, bed.val.losses, C_HAT, seed, groups=bed.val.sessions
        ),
        "Always-best": always_best(bed.val.losses, C_HAT),
        "Always-cheapest": always_cheapest(bed.val.losses, C_HAT),
    }
    h = best_single(bed.val.losses, C_HAT)
    q_best = 1 - bed.test.losses[:, h].mean()
    rows = {}
    singles = {}
    for name, router in routers.items():
        costs, qualities = router.curve(bed.test.emb, LAMS, bed.test.losses)
        if name.startswith("Always"):
            singles[name] = (float(costs[0]), float(qualities[0]))
            continue
        rows[name] = (
            area(costs, qualities, C_HAT.min(), C_HAT.max()),
            qnc(costs, qualities, q_best, C_HAT[h]),
            qnc(costs, qualities, q_best - 0.01, C_HAT[h]),
        )
    store.close()
    test_labels = assign(bed.test.emb, fitted.centroids)
    zero = routers["ZeroRouter"]

    def difference(idx):
        costs, qualities = sweep(test_labels[idx], fp.psi, C_HAT, LAMS, bed.test.losses[idx])
        z_c, z_q = zero.curve(bed.test.emb[idx], LAMS, bed.test.losses[idx])
        return area(costs, qualities, C_HAT.min(), C_HAT.max()) - area(
            z_c, z_q, C_HAT.min(), C_HAT.max()
        )

    boot = bootstrap(difference, bed.test.sessions, n_boot=10_000, seed=seed)
    curve = sweep(test_labels, fp.psi, C_HAT, LAMS, bed.test.losses)
    return rows, singles, boot, fp, curve


def main() -> None:
    start = time.perf_counter()
    seed = load_config("pipeline")["seed"]
    lines = [
        "# Synthetic validation of the router (WP-05 step 9)",
        "",
        ("Simulated data with a planted answer: 3 prompt types in 64 dimensions, 4 models, "
        "5,000 train / 400 val / 300 test, whole sessions resampled. No real data."),
        "",
    ]
    report = {}
    for name, rates in (("Planted structure", STRUCTURED), ("No structure", FLAT)):
        rows, singles, boot, fp, curve = ladder(make_bed(seed, rates), seed, 3)
        report[name] = {"estimate": boot.estimate, "low": boot.low, "high": boot.high}
        lines += [
            f"## {name}: routers at K = 3 (simulated, n_test = 300, one dataset)",
            "",
            "| Router | Area | QNC | QNC within 1 point |",
            "|---|---:|---:|---:|",
            *[f"| {r} | {a:.4f} | {q:.3f} | {q1:.3f} |" for r, (a, q, q1) in rows.items()],
            "",
            "Single models (no curve): "
            + "; ".join(f"{r} cost {c:.2f}, quality {q:.4f}" for r, (c, q) in singles.items())
            + ". QNC 1.000 means the exact quality of the best model was never reached.",
            "",
            (f"UniRoute minus ZeroRouter area: **{boot.estimate:+.4f}**, 95% CI "
            f"[{boot.low:+.4f}, {boot.high:+.4f}] (10,000 session resamples)."),
            f"Separability (criterion D): {separability(fp.psi, fp.counts):.2f}.",
            "",
        ]
        if name == "Planted structure":
            points = sorted(set(zip(np.round(curve[0], 3), np.round(curve[1], 3), strict=True)))
            lines += [
                "UniRoute deferral curve, distinct points (cost, quality): "
                + ", ".join(f"({c:.3f}, {q:.3f})" for c, q in points),
                "",
            ]
    lines += [
        f"## Choosing K: which rule finds the truth? ({RUNS} simulated datasets each)",
        "",
        "The planted answer is K = 3. Area change = test area at the picked K minus at K = 3.",
        "",
        "| Data | Rule | K = 3 picked | Other picks | Area change, mean | worst |",
        "|---|---|---:|---|---:|---:|",
    ]
    study = {}
    for name, rates in (("Planted structure", STRUCTURED), ("No structure", FLAT)):
        picks, gain = rule_study(rates)
        study[name] = {r: {str(k): v for k, v in sorted(c.items())} for r, c in picks.items()}
        for rule, counts in picks.items():
            others = ", ".join(f"K{k}: {n}" for k, n in sorted(counts.items()) if k != 3)
            lines.append(
                f"| {name} | {rule} | {counts[3]} | {others} | "
                f"{np.mean(gain[rule]):+.4f} | {np.min(gain[rule]):+.4f} |"
            )
    lines += [
        "",
        "Models: " + ", ".join(f"{m} ({c})" for m, c in zip(MODELS, COSTS, strict=True)) + ".",
        "",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "synthetic_validation.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "stage": "WP-05 synthetic validation",
        "seed": seed,
        "config_id": load_config("pipeline")["_id"],
        "runs": RUNS,
        "difference": report,
        "picks": study,
        "duration_s": round(time.perf_counter() - start, 1),
        "cost_usd": 0.0,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
