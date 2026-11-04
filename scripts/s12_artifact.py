"""WP-14 steps 6 and 8: lambda by D-118 and artifact v1. Validation only, no paid calls.

Main router K = 8 (owner, D-117); K = 4 (D-064 rule) is frozen next to it as the comparison.
Lambda: the largest on the grid whose out-of-fold pass rate is not below always-DeepSeek (DEV-16).
Usage: uv run python scripts/s12_artifact.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import numpy as np
from router_check import MODELS, cluster_labels, load_val, vectors
from s10_lambda_holdout import out_of_fold

from metis.config import load_config
from metis.llm.client import load_models
from metis.router.artifact import Meta, RouterArtifact, load_artifact, save_artifact
from metis.router.select_k import fit_psi
from metis.router.select_lambda import lambda_grid

JUDGE_ID = "356e63e52245"
GEN_ID = "fca2b649cc8d"


def out_of_fold_lambda(k, labels, losses, groups, c_hat, lams, target):
    rows = [(float(lam), *out_of_fold(k, labels, losses, groups, c_hat, float(lam))) for lam in lams]
    ok = [r for r in rows if r[2] >= target]
    return (ok[-1] if ok else max(rows, key=lambda r: r[2])), bool(ok), rows


def main() -> None:
    cfg = load_config("pipeline")["router"]
    names = load_config("cluster_names")
    order, losses, groups, c_hat = load_val()
    labels = cluster_labels(vectors(order))
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
    deepseek = 1 - losses[:, 0].mean()
    known = load_models()
    prices = {m: {"in": known[m]["price_in"], "out": known[m]["price_out"]} for m in MODELS}
    val_hash = hashlib.sha256("\n".join(order).encode()).hexdigest()[:12]

    lines = ["# Frozen lambda (D-118, DEV-16)", "",
             f"Measured on validation, out of fold, n = {len(order)}. Target: always-DeepSeek pass {deepseek:.1%}.", "",
             "| K | λ | Unseen cost | Unseen pass | Target met | Shares (DeepSeek, Luna, Gemini, Sonnet) |", "|---:|---:|---:|---:|---|---|"]
    for k, folder in ((8, "artifacts/router_v1"), (4, "artifacts/router_v1_k4")):
        (lam, cost, quality, shares), met, rows = out_of_fold_lambda(k, labels[k], losses, groups, c_hat, lams, deepseek)
        share = ", ".join(f"{s:.0%}" for s in shares)
        lines.append(f"| {k} | {lam:.4g} | {cost:.3f} | {quality:.1%} | {'yes' if met else 'no'} | {share} |")
        with np.load(f"runs/s5/view/k_{k:02d}.npz") as z:
            centers = z["centers"]
        psi = fit_psi(losses, labels[k], k)
        counts = np.bincount(labels[k], minlength=k)
        own = names.get(f"k_{k}", {})
        cluster_names = tuple(own[i] if k == 8 else f"Cluster {i}" for i in range(k))  # k_4 names are stale, D-088
        meta = Meta(method="point", embedder_id=load_config("pipeline")["s4"]["choice"], k_star=k,
                    cluster_names=cluster_names, models=tuple(MODELS), prices=prices, lam=lam,
                    lambda_mode="quality-out-of-fold", lambda_target=float(deepseek), router_type="uniroute",
                    hashes={"val_set": val_hash, "gen_config": GEN_ID, "judge_config": JUDGE_ID},
                    build_date=str(date(2026, 11, 3)), tau=7.0)
        art = RouterArtifact(meta=meta, centroids=centers.astype(float), psi=psi.astype(float), counts=counts.astype(int), c_hat=c_hat)
        if Path(folder).exists():
            shutil.rmtree(folder)  # nothing is frozen until the pre-test tag
        save_artifact(art, folder)
        load_artifact(folder)
        Path(folder, "lambda_curve.json").write_text(json.dumps([{"lam": r[0], "cost": r[1], "pass": r[2]} for r in rows]), encoding="utf-8")
    Path("results/lambda_frozen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
