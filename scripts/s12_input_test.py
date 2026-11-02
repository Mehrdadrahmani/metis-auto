"""WP-14 (D-069): does the previous user message help routing? Validation only, local, no paid calls.

Inputs: A current message (shipped), T = 2 previous + current, hybrid previous + current only for
short follow-ups (shortest 21.8% of val, the eligible share in D-069). Same centroids for all, so
this tests the assignment, not a re-clustering on the new input.

Usage: uv run python scripts/s12_input_test.py [--device cpu]
Writes results/representation_test.md (aggregates only).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from router_check import SEED, cluster_labels, load_val, vectors
from s4_embed_full import embedder
from s11_signal_tests import scores, table

from metis.config import load_config
from metis.router.select_k import halvings
from metis.router.select_lambda import lambda_grid

SHORT_SHARE = 0.218


def labels_for(vecs: np.ndarray, k: int) -> np.ndarray:
    with np.load(f"runs/s5/view/k_{k:02d}.npz") as z:
        c = z["centers"]
    return ((vecs[:, None, :] - c[None, :, :]) ** 2).sum(-1).argmin(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    cfg = load_config("pipeline")
    order, losses, groups, c_hat = load_val()
    p = pd.read_parquet("runs/s1/prompts.parquet", columns=["prompt_id", "session_id", "msg_index", "embed_input", "text_chars"])
    p = p.sort_values(["session_id", "msg_index"])
    p["prev"] = p.groupby("session_id")["embed_input"].shift(1)
    p = p.set_index("prompt_id").loc[order]
    has_prev = p["prev"].notna().to_numpy()
    cut = np.quantile(p["text_chars"], SHORT_SHARE)
    short = (p["text_chars"] <= cut).to_numpy()

    joined = (p["prev"].fillna("") + "\n" + p["embed_input"]).str.strip().tolist()
    model = embedder(cfg, args.device)
    t2 = np.asarray(model.encode(joined))
    a = vectors(order)
    hybrid = np.where((short & has_prev)[:, None], t2, a)

    r = cfg["router"]
    lams = lambda_grid(r["lambda_n"], r["lambda_low"], r["lambda_high"])
    splits = halvings(len(losses), r["select_k_repeats"], SEED, groups)
    base = cluster_labels(a)
    lines = [
        "# Representation test on validation", "",
        f"Measured, held out, n = {len(order)}, 40 halves. {has_prev.mean():.0%} of prompts have a previous message; short means {cut:.0f} chars or fewer.",
        "Same centroids throughout. Cheap gap: pass rate minus always-DeepSeek at λ = 0.1.", "",
        "| Input | K | Area | Cheap gap | Prompts moved to another cluster |", "|---|---:|---:|---:|---:|",
    ]
    for name, vecs in (("A current message", a), ("T = 2", t2), ("Hybrid", hybrid)):
        for k in (8, 4):
            lab = labels_for(vecs, k)
            ar, gap = scores(lambda fit, lab=lab: table(losses, lab, fit)[lab], losses, c_hat, lams, splits)
            lines.append(f"| {name} | {k} | {ar:.4f} | {gap:+.1%} | {(lab != base[k]).mean():.0%} |")
    Path("results/representation_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
