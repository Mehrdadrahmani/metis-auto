"""WP-14 steps 2 to 4: fingerprints for K 3..20, choice of K, baselines. Validation only, no paid calls.

Reads the same files as router_check.py, never a *.sealed* file.

Usage: uv run python scripts/s9_router_val.py
Writes results/{fingerprints,select_k,ladder_val}.md, results/select_k.png, runs/s8/psi_k*.npy and
MLflow runs in experiment `router-selection`. Aggregates only.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from router_check import KS, MODELS, SEED, cluster_labels, load_val, vectors

from metis.config import load_config
from metis.eval.baselines import KNN_CANDIDATES, LogisticRouter, ZeroRouter, tune_knn_k
from metis.eval.metrics import area, best_single, qnc, sweep
from metis.eval.stats import wilson_ci
from metis.obs import tracking
from metis.router.fingerprints import fingerprints
from metis.router.select_k import fit_psi, halvings, select_k
from metis.router.select_lambda import lambda_grid

ROBUST_SEEDS = (1, 2, 3, 4)
LOGISTIC_HALVINGS = 5
WITHIN = 0.01  # QNC within 1 point, reported beside exact (WP-05 note)


def fingerprint_report(losses, labels, k_star, ship_max) -> str:
    names = yaml.safe_load(Path("configs/cluster_names.yaml").read_text("utf-8")).get(f"k_{k_star}", {})
    f = fingerprints(losses, labels[k_star], k_star)
    smooth = fingerprints(losses, labels[k_star], k_star, alpha=2.0)
    n = len(losses)
    lines = [
        "# Fingerprints", "",
        f"Measured on validation, n = {n}. Pointwise jev, pass mark 7, Eq. 12, α = 0. Fail rate per cluster with 95% Wilson interval.",
        "Names are drafts from configs/cluster_names.yaml. Ceiling means every model fails under 5% in the cluster.", "",
        f"## K* = {k_star}", "",
        "| Cluster | Name | n | " + " | ".join(MODELS) + " |", "|---:|---|---:|" + "---:|" * len(MODELS),
    ]
    for c in range(k_star):
        cells = []
        for j in range(len(MODELS)):
            fails = round(f.psi[c, j] * f.counts[c])
            low, high = wilson_ci(fails, int(f.counts[c]))
            cells.append(f"{f.psi[c, j]:.0%} ({low:.0%} to {high:.0%})")
        lines.append(f"| {c} | {names.get(c, '')} | {f.counts[c]} | " + " | ".join(cells) + " |")
    lines += [
        "", f"Largest change from α = 2 smoothing: {np.abs(f.psi - smooth.psi).max():.3f}.", "",
        "## Every K", "", "| K | Smallest cluster | Median cluster | Empty | Ceiling clusters | Can ship |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for k in KS[1:]:
        g = fingerprints(losses, labels[k], k)
        ship = "yes" if k <= ship_max else "no"
        lines.append(f"| {k} | {g.counts.min()} | {np.median(g.counts):.0f} | {len(g.empty_clusters)} | {len(g.ceiling_clusters)} | {ship} |")
    return "\n".join(lines) + "\n"


def plot(sel, zero_area_mean, k_star, ship_max) -> None:
    ks = sorted(sel.mean_area)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(ks, [sel.mean_area[k] for k in ks], "o-", color="#6c8ebf", label="UniRoute")
    ax.axhline(zero_area_mean, color="#666666", ls="--", label="ZeroRouter")
    ax.axvline(ship_max + 0.5, color="#d6b656", ls=":", label="K limit")
    ax.scatter([k_star], [sel.mean_area[k_star]], color="#d79b00", zorder=3, label="K*")
    ax.set_xlabel("K")
    ax.set_ylabel("Held-out normalized area")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("results/select_k.png", dpi=150)


def score_all(x, losses, labels, c_hat, lams, groups, repeats, k_star):
    """Held-out area and QNC per router on the same halves; logistic on the first few only."""
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    unit = x / np.linalg.norm(x, axis=1, keepdims=True)
    order = np.argsort(-(unit @ unit.T), axis=1, kind="stable")
    knn_k, knn_means = tune_knn_k(order, losses, c_hat, lams, SEED, repeats, groups)

    names = [f"UniRoute K = {k_star}", "UniRoute K = 1", "ZeroRouter", f"K-NN k = {knn_k}", "Logistic", "Always-cheapest", "Always-best"]
    rows = {n: {"area": [], "qnc": [], "qnc1": []} for n in names}

    def add(name, costs, qualities, q_best, c_best):
        rows[name]["area"].append(area(costs, qualities, c_min, c_max))
        rows[name]["qnc"].append(qnc(costs, qualities, q_best, c_best))
        rows[name]["qnc1"].append(qnc(costs, qualities, q_best - WITHIN, c_best))

    for h, (a, b) in enumerate(halvings(len(losses), repeats, SEED, groups)):
        for fit, score in ((a, b), (b, a)):
            loss_s = losses[score]
            best = best_single(losses[fit], c_hat)
            q_best, c_best = 1 - loss_s[:, best].mean(), c_hat[best]
            for name, k in ((names[0], k_star), (names[1], 1)):
                psi = fit_psi(losses[fit], labels[k][fit], k)
                add(name, *sweep(labels[k][score], psi, c_hat, lams, loss_s), q_best, c_best)
            add("ZeroRouter", *ZeroRouter(losses[fit], c_hat).curve(None, None, loss_s), q_best, c_best)

            in_fit = np.zeros(len(losses), bool)
            in_fit[fit] = True
            near = order[score]
            near = near[in_fit[near]].reshape(len(score), len(fit))[:, :knn_k]
            add(names[3], *sweep(np.arange(len(score)), losses[near].mean(1), c_hat, lams, loss_s), q_best, c_best)

            if h < LOGISTIC_HALVINGS:
                gamma = LogisticRouter(x[fit], losses[fit], c_hat, SEED, groups[fit]).predict_loss(x[score])
                add("Logistic", *sweep(np.arange(len(score)), gamma, c_hat, lams, loss_s), q_best, c_best)

            cheap = int(np.argmin(c_hat))
            add("Always-cheapest", c_hat[[cheap]], 1 - loss_s[:, [cheap]].mean(0), q_best, c_best)
            add("Always-best", c_hat[[best]], 1 - loss_s[:, [best]].mean(0), q_best, c_best)
    return names, rows, knn_means


def log_mlflow(sel, rows, config_id: str) -> None:
    if not tracking.enabled():
        return
    mlflow = tracking._mlflow()
    mlflow.set_experiment("router-selection")
    for k, score in sel.mean_area.items():
        with mlflow.start_run(run_name=f"uniroute-k{k}"):
            mlflow.log_params({"method": "pointwise", "K": k, "alpha": 0, "tau": 7, "config": config_id, "set": "val"})
            mlflow.log_metric("area", score)
    for name, r in rows.items():
        with mlflow.start_run(run_name=name):
            mlflow.log_params({"method": name, "alpha": 0, "tau": 7, "config": config_id, "set": "val"})
            mlflow.log_metrics({"area": float(np.mean(r["area"])), "qnc": float(np.mean(r["qnc"]))})
    with mlflow.start_run(run_name="select-k-plot"):
        mlflow.log_artifact("results/select_k.png")


def main() -> None:
    cfg = load_config("pipeline")["router"]
    order, losses, groups, c_hat = load_val()
    x = vectors(order)
    labels = cluster_labels(x)
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
    repeats, ship_max = cfg["select_k_repeats"], cfg["k_ship_max"]

    comparison = [k for k in KS if k == 1 or k > ship_max]
    sel = select_k(labels, losses, c_hat, lams, SEED, repeats, groups, comparison=comparison)
    k_star = sel.k_star
    other = {s: select_k(labels, losses, c_hat, lams, s, repeats, groups, comparison=comparison) for s in ROBUST_SEEDS}
    smooth = select_k(labels, losses, c_hat, lams, SEED, repeats, groups, comparison=comparison, alpha=2.0)

    names, rows, knn_means = score_all(x, losses, labels, c_hat, lams, groups, repeats, k_star)
    zero_mean = float(np.mean(rows["ZeroRouter"]["area"]))

    Path("runs/s8").mkdir(parents=True, exist_ok=True)
    for k in KS[1:]:
        np.save(f"runs/s8/psi_k{k}.npy", fit_psi(losses, labels[k], k))
    Path("results/fingerprints.md").write_text(fingerprint_report(losses, labels, k_star, ship_max), encoding="utf-8")
    plot(sel, zero_mean, k_star, ship_max)

    ship = [k for k in KS[1:] if k <= ship_max]
    lines = [
        "# Choice of K", "",
        f"Split-validation (D-061), 20 halvings both ways, sessions whole, n = {len(losses)}. Measured, held out.",
        f"K* = {k_star}: highest mean area among K ≤ {ship_max} (D-064, D-089). Figure: results/select_k.png.",
        "K* is not a count of real topics.", "",
        "| K | Mean area | α = 2 | " + " | ".join(f"Seed {s}" for s in ROBUST_SEEDS) + " |", "|---:|---:|---:|" + "---:|" * len(ROBUST_SEEDS),
    ]
    for k in KS:
        cells = " | ".join(f"{other[s].mean_area[k]:.4f}" for s in ROBUST_SEEDS)
        lines.append(f"| {k} | {sel.mean_area[k]:.4f} | {smooth.mean_area[k]:.4f} | {cells} |")
    wins = {s: o.k_star for s, o in other.items()}
    lines += [
        "", f"Winner with α = 2: K = {smooth.k_star}. Winner per other seed: {json.dumps(wins)}.",
        f"Empty clusters met while fitting halves: {sel.empty_events}, filled with the overall rate (D-054, Q-028).",
        f"Scored K ≤ {ship_max}: {', '.join(map(str, ship))}.",
    ]
    Path("results/select_k.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    star = np.array(rows[names[0]]["area"])
    lines = [
        "# Router ladder on validation", "",
        f"Measured, held out, n = {len(losses)}, 40 halves ({2 * LOGISTIC_HALVINGS} for logistic). Comparison only: UniRoute ships (M1).",
        "QNC: cheapest budget reaching the best single model on the held-out half, as a share of its cost. 1.000 can mean never reached.",
        "Read QNC with care: the best single model flips between DeepSeek and Sonnet across halves, and their costs differ 24 times.",
        "Spread is across halves that share data, not a confidence interval.", "",
        "| Router | Area | Minus UniRoute K* | QNC exact | QNC within 1 point |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in names:
        r = rows[name]
        a = np.array(r["area"])
        gap = (a - star[: len(a)]).mean()
        lines.append(
            f"| {name} | {a.mean():.4f} | {gap:+.4f} | {np.mean(r['qnc']):.3f} | {np.mean(r['qnc1']):.3f} |"
        )
    lines += ["", f"K-NN k tuned on {list(KNN_CANDIDATES)}: " + json.dumps({k: round(v, 4) for k, v in knn_means.items()}) + "."]
    Path("results/ladder_val.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    log_mlflow(sel, rows, "s9-val")


if __name__ == "__main__":
    main()
