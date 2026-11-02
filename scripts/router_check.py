"""Free early check (WP-14, D-114): does routing by cluster beat ignoring the prompt?

Validation only: reads runs/s7/labels_val.parquet, never a *.sealed* file. No paid calls.

Two held-out views, so nothing is scored on the prompts it was fitted on:
- halves: the S9 rule, 20 halvings both ways, normalized area for every K.
- folds: 10-fold, sessions kept whole, repeated 5 times. Each lambda gives a real router choice per
  prompt, compared with ZeroRouter at the same cost. 90% of val is fitted, close to the shipped case.
  No Pareto envelope here, so no credit for picking lucky lambdas after seeing the scores.

Usage: uv run python scripts/router_check.py
Writes results/router_check_val.md (aggregates only).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.eval.baselines import ZeroRouter
from metis.eval.metrics import area
from metis.llm.budget import call_cost
from metis.llm.client import load_models
from metis.router.route import cluster_choices, normalize_costs
from metis.router.select_k import fit_psi, halvings, select_k
from metis.router.select_lambda import lambda_grid

SEED = 20261020
MODELS = ["deepseek-v4-flash", "gpt-5.6-luna", "gemini-2.5-flash-lite", "claude-sonnet-5-5"]
KS = [1, *range(3, 21)]
FOLDS, FOLD_REPEATS, BOOT = 10, 5, 2000
OUT = Path("results/router_check_val.md")


def load_val() -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Prompt ids, losses (n, N), session group per prompt, normalized costs."""
    labels = pd.read_parquet("runs/s7/labels_val.parquet")
    losses = labels.pivot(index="prompt_id", columns="model_id", values="loss")[MODELS].dropna()
    order = sorted(losses.index)
    split = pd.read_parquet("runs/s2/split.parquet", columns=["prompt_id", "split", "session_id"])
    split = split[split["split"] == "val"].set_index("prompt_id")
    groups = np.unique(split.loc[order, "session_id"].to_numpy(), return_inverse=True)[1]

    columns = ["prompt_id", "model_id", "tokens_in", "tokens_out"]
    tokens = pd.concat(pd.read_parquet(f"runs/s6/responses_{s}.parquet", columns=columns) for s in ("pilot", "val"))
    tokens = tokens[tokens["prompt_id"].isin(order)].drop_duplicates(["prompt_id", "model_id"]).groupby("model_id")
    t_in, t_out = tokens["tokens_in"].mean(), tokens["tokens_out"].mean()
    known = load_models()
    c_hat = normalize_costs([call_cost(known[m], t_in[m], t_out[m]) for m in MODELS])
    return order, losses.loc[order].to_numpy(float), groups, c_hat


def vectors(order: list[str]) -> np.ndarray:
    choice = load_config("pipeline")["s4"]["choice"]
    ids, vecs = [], []
    for part in sorted(Path("runs/s4/full", choice).glob("part-*.npz")):
        with np.load(part) as z:
            keep = np.isin(z["ids"], order)
            ids.append(z["ids"][keep])
            vecs.append(z["vecs"][keep])
    all_ids, all_vecs = np.concatenate(ids), np.concatenate(vecs)
    return all_vecs[pd.Index(all_ids).get_indexer(order)]


def cluster_labels(vecs: np.ndarray) -> dict[int, np.ndarray]:
    out = {1: np.zeros(len(vecs), int)}
    for k in KS[1:]:
        with np.load(f"runs/s5/view/k_{k:02d}.npz") as z:
            c = z["centers"]
        out[k] = ((vecs[:, None, :] - c[None, :, :]) ** 2).sum(-1).argmin(1)
    return out


def zero_quality(fit_loss: np.ndarray, c_hat: np.ndarray, budget: float, score_loss: np.ndarray) -> np.ndarray:
    """Expected ZeroRouter quality per held-out prompt at this budget, hull taken from the fitted part."""
    m1, m2, p1 = ZeroRouter(fit_loss, c_hat).mix(budget)
    return 1 - (p1 * score_loss[:, m1] + (1 - p1) * score_loss[:, m2])


def zero_area(fit_loss, score_loss, c_hat, c_min, c_max) -> float:
    z = ZeroRouter(fit_loss, c_hat)
    return area(*z.curve(None, None, score_loss), c_min, c_max)


def session_folds(groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    fold_of_group = rng.permutation(groups.max() + 1) % FOLDS
    return fold_of_group[groups]


def out_of_fold(k, labels, losses, groups, c_hat, lams):
    """Router cost and quality minus ZeroRouter at the same cost; (L, repeats) points + (L, n) gaps."""
    gaps = np.zeros((len(lams), len(losses)))
    costs = np.zeros(len(lams))
    quality = np.zeros(len(lams))
    for repeat in range(FOLD_REPEATS):
        fold = session_folds(groups, np.random.default_rng(SEED + repeat))
        for f in range(FOLDS):
            on = fold == f
            psi = fit_psi(losses[~on], labels[~on], k, "pt")
            picks = cluster_choices(psi, c_hat, lams)[:, labels[on]]  # (L, n_on)
            rows = np.arange(on.sum())
            for i in range(len(lams)):
                q = 1 - losses[on][rows, picks[i]]
                z = zero_quality(losses[~on], c_hat, float(c_hat[picks[i]].mean()), losses[on])
                gaps[i, on] += (q - z) / FOLD_REPEATS
                costs[i] += c_hat[picks[i]].sum() / (FOLD_REPEATS * len(losses))
                quality[i] += q.sum() / (FOLD_REPEATS * len(losses))
    return costs, quality, gaps


def boot_ci(gap: np.ndarray, groups: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """95% interval, resampling whole sessions."""
    sums = np.bincount(groups, gap)
    sizes = np.bincount(groups)
    draws = rng.integers(0, len(sizes), (BOOT, len(sizes)))
    means = sums[draws].sum(1) / sizes[draws].sum(1)
    return tuple(np.percentile(means, [2.5, 97.5]))


def main() -> None:
    cfg = load_config("pipeline")["router"]
    order, losses, groups, c_hat = load_val()
    labels = cluster_labels(vectors(order))
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
    c_min, c_max = float(c_hat.min()), float(c_hat.max())

    comparison = [k for k in KS if k == 1 or k > cfg["k_ship_max"]]
    sel = select_k(labels, losses, c_hat, lams, SEED, cfg["select_k_repeats"], groups, comparison=comparison)

    zero = []
    for a, b in halvings(len(losses), cfg["select_k_repeats"], SEED, groups):
        for fit_on, score_on in ((a, b), (b, a)):
            zero.append(zero_area(losses[fit_on], losses[score_on], c_hat, c_min, c_max))
    zero = np.array(zero)

    lines = [
        "# Router check on validation", "",
        "Measured, held out, validation only. Pointwise jev, pass mark 7.",
        f"n = {len(order)} prompts in {groups.max() + 1} sessions. Sealed files not opened.", "",
        "## Models", "", "| Model | Cost share of Sonnet | Pass rate |", "|---|---:|---:|",
    ]
    for j in np.argsort(c_hat):
        lines.append(f"| {MODELS[j]} | {c_hat[j]:.3f} | {1 - losses[:, j].mean():.1%} |")
    lines += [
        "", f"Best possible (a perfect router): {1 - losses.min(axis=1).mean():.1%}. Hull used by ZeroRouter on all val: "
        + ", ".join(MODELS[i] for i in ZeroRouter(losses, c_hat).hull) + ".",
        "", "## S9 score by K", "",
        (f"Mean normalized area, 40 held-out halves. ZeroRouter on the same halves: {zero.mean():.4f}. "
        f"K limit {cfg['k_ship_max']}, K* = {sel.k_star}."),
        "The spread is of halves that share data, so it is too narrow to be a confidence interval.", "",
        "| K | Area | Minus K = 1 | Minus ZeroRouter | Share of halves above ZeroRouter |", "|---:|---:|---:|---:|---:|",
    ]
    for k in KS:
        a = sel.areas[k]
        lines.append(
            f"| {k} | {a.mean():.4f} | {(a - sel.areas[1]).mean():+.4f} | {(a - zero).mean():+.4f} | {(a > zero).mean():.0%} |"
        )

    picks = {"K = 1": 1, "K = 3": 3, "K = 8": 8, f"K* = {sel.k_star}": sel.k_star}
    wanted = (0.0, 0.01, 0.03, 0.1, 0.3, 1.0)
    grid = np.array(wanted)
    rng = np.random.default_rng(SEED)
    lines += [
        "", "## Router against ZeroRouter at the same cost", "",
        f"Out of fold: {FOLDS} folds, {FOLD_REPEATS} repeats, sessions whole. Interval: 95% bootstrap over sessions.",
        "Gap in points of pass rate. Zero inside the interval means no measured gain.", "",
        "| Router | λ | Cost | Pass rate | Gap to ZeroRouter (95% CI) |", "|---|---:|---:|---:|---:|",
    ]
    for name, k in picks.items():
        costs, quality, gaps = out_of_fold(k, labels[k], losses, groups, c_hat, grid)
        for i, lam in enumerate(grid):
            low, high = boot_ci(gaps[i], groups, rng)
            lines.append(
                f"| {name} | {lam:g} | {costs[i]:.3f} | {quality[i]:.1%} | "
                f"{gaps[i].mean():+.1%} ({low:+.1%} to {high:+.1%}) |"
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
