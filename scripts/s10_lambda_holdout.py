"""WP-14 steps 6 and 7 for two candidates, K = 8 (owner, D-117) and K = 4 (rule, D-064). Validation only.

Usage: uv run python scripts/s10_lambda_holdout.py
Writes results/lambda_val.md and results/holdout_demo.md (aggregates only). No paid calls.
In-sample lambda points are the spec's S10. Out-of-fold points show what they are worth on unseen prompts.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from router_check import (
    FOLD_REPEATS,
    FOLDS,
    MODELS,
    SEED,
    cluster_labels,
    load_val,
    session_folds,
    vectors,
)

from metis.config import load_config
from metis.eval.metrics import area, best_single, operating_point, sweep
from metis.router.route import cluster_choices
from metis.router.select_k import fit_psi, halvings
from metis.router.select_lambda import lambda_grid, select_lambda

CANDIDATES = (8, 4)
GEMINI = MODELS.index("gemini-2.5-flash-lite")
HOLDOUT_LAMBDA = 0.1  # the quality target is met at every lambda without Gemini, so it picks the top of the grid
SHORT = [m.split("-")[0] for m in MODELS]


def out_of_fold(k, labels, losses, groups, c_hat, lam):
    """Mean cost, pass rate and shares on unseen folds, with Psi fitted on the other folds."""
    costs, quality, shares = [], [], []
    rows = np.arange(len(losses))
    for repeat in range(FOLD_REPEATS):
        fold = session_folds(groups, np.random.default_rng(SEED + repeat))
        chosen = np.zeros(len(losses), int)
        for f in range(FOLDS):
            on = fold == f
            psi = fit_psi(losses[~on], labels[~on], k)
            chosen[on] = cluster_choices(psi, c_hat, np.array([lam]))[0][labels[on]]
        costs.append(c_hat[chosen].mean())
        quality.append(1 - losses[rows, chosen].mean())
        shares.append(np.bincount(chosen, minlength=len(c_hat)) / len(chosen))
    return float(np.mean(costs)), float(np.mean(quality)), np.mean(shares, axis=0)


def halves_area(k, labels, losses, c_hat, lams, groups, repeats, pool):
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    scores = []
    for a, b in halvings(len(losses), repeats, SEED, groups):
        for fit, score in ((a, b), (b, a)):
            psi = fit_psi(losses[fit][:, pool], labels[fit], k)
            costs, q = sweep(labels[score], psi, c_hat[pool], lams, losses[score][:, pool])
            scores.append(area(costs, q, c_min, c_max))
    return float(np.mean(scores))


def main() -> None:
    cfg = load_config("pipeline")["router"]
    order, losses, groups, c_hat = load_val()
    labels = cluster_labels(vectors(order))
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
    best = best_single(losses, c_hat)
    q_target = 1 - losses[:, best].mean() - 0.02
    c_target = 0.5 * c_hat[best]

    lines = [
        "# Lambda on validation", "",
        f"Measured, n = {len(losses)}. Always-best = {MODELS[best]}, pass {1 - losses[:, best].mean():.1%}, cost {c_hat[best]:.3f}.",
        f"Quality mode target {q_target:.1%} (always-best minus 2 points, primary). Budget mode target cost {c_target:.3f}.",
        "In-sample is S10 on all validation. Unseen is out of fold, the fairer figure.", "",
        "| K | Mode | λ | In-sample cost | In-sample pass | Unseen cost | Unseen pass | Unseen shares |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for k in CANDIDATES:
        psi = fit_psi(losses, labels[k], k)
        costs, q = sweep(labels[k], psi, c_hat, lams, losses)
        for mode, target in (("quality", q_target), ("budget", c_target)):
            c = select_lambda(lams, costs, q, mode, target)
            uc, uq, us = out_of_fold(k, labels[k], losses, groups, c_hat, c.lam)
            share = ", ".join(f"{n} {s:.0%}" for n, s in zip(SHORT, us, strict=True))
            flag = "" if c.feasible else " (target not met)"
            lines.append(f"| {k} | {mode}{flag} | {c.lam:.4g} | {c.cost:.3f} | {c.quality:.1%} | {uc:.3f} | {uq:.1%} | {share} |")
    Path("results/lambda_val.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dev = np.array([i for i in range(len(MODELS)) if i != GEMINI])
    full = np.arange(len(MODELS))
    lines = [
        "# Holdout demo", "",
        f"Measured, n = {len(losses)}, validation only. Gemini hidden, then added back from its validation row alone.",
        "K is fixed per candidate, so this shows the add-a-model step, not a fresh K choice.", "",
        "| K | Area without Gemini | Area with Gemini | Change | λ | Gemini share, unseen |", "|---:|---:|---:|---:|---:|---:|",
    ]
    for k in CANDIDATES:
        before = halves_area(k, labels[k], losses, c_hat, lams, groups, cfg["select_k_repeats"], dev)
        after = halves_area(k, labels[k], losses, c_hat, lams, groups, cfg["select_k_repeats"], full)
        lam = HOLDOUT_LAMBDA
        _, _, shares = out_of_fold(k, labels[k], losses, groups, c_hat, lam)
        full_psi = fit_psi(losses, labels[k], k)
        point = operating_point(lam, labels[k], full_psi, c_hat, losses)
        lines.append(f"| {k} | {before:.4f} | {after:.4f} | {after - before:+.4f} | {lam:.4g} | {shares[GEMINI]:.1%} (in-sample {point.shares[GEMINI]:.1%}) |")
    Path("results/holdout_demo.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
