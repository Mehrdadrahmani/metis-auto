"""Pilot 100 against the 300 new validation prompts, and all 400. Validation only, no paid calls.

Usage: uv run python scripts/val_vs_pilot.py
Writes results/val_vs_pilot.md (aggregates only). Pass mark and separability as in pilot_decision.py.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.eval.stats import fingerprint_stability, separability, wilson_ci
from metis.router.select_k import fit_psi

SEED = 20261020
ANCHOR = "claude-sonnet-5-5"
MODELS = ["deepseek-v4-flash", "gpt-5.6-luna", "gemini-2.5-flash-lite", ANCHOR]
TAU = 7


def centers(path: Path) -> np.ndarray:
    with np.load(path) as z:
        return z["centers"]


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


def rate(k: int, n: int) -> str:
    low, high = wilson_ci(k, n)
    return f"{k / n:.1%} ({low:.0%} to {high:.0%})"


def main() -> None:
    labels = pd.read_parquet("runs/s7/labels_val.parquet")
    split = pd.read_parquet("runs/s2/split.parquet", columns=["prompt_id", "split", "in_pilot", "session_id"])
    split = split[split["split"] == "val"].set_index("prompt_id")
    scores = labels.pivot(index="prompt_id", columns="model_id", values="score")[MODELS].dropna()
    order = sorted(scores.index)
    scores = scores.loc[order]
    pilot = split.loc[order, "in_pilot"].to_numpy(bool)
    groups = {"Pilot": pilot, "New": ~pilot, "All": np.ones(len(order), bool)}
    fails = (scores.to_numpy() < TAU).astype(float)

    lines = [
        "# Validation against pilot", "",
        f"Measured, pointwise jev, pass mark {TAU}. Same judge, same answers for pilot prompts.",
        f"Pilot n = {pilot.sum()}, new n = {(~pilot).sum()}, all n = {len(order)}.",
        "Rates show a 95% Wilson interval.", "",
        "## Pass rate", "",
        "| Model | Pilot | New | All | New minus pilot (95% CI) |", "|---|---:|---:|---:|---:|",
    ]
    for j, m in enumerate(MODELS):
        ok = 1 - fails[:, j]
        cells = [rate(int(ok[g].sum()), int(g.sum())) for g in groups.values()]
        a, b = ok[pilot], ok[~pilot]
        gap = b.mean() - a.mean()
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        lines.append(f"| {m} | {' | '.join(cells)} | {gap:+.1%} ({gap - 1.96 * se:+.1%} to {gap + 1.96 * se:+.1%}) |")

    lines += ["", "## Mean score", "", "| Model | Pilot | New | All |", "|---|---:|---:|---:|"]
    for m in MODELS:
        s = scores[m].to_numpy()
        lines.append(f"| {m} | {s[pilot].mean():.2f} | {s[~pilot].mean():.2f} | {s.mean():.2f} |")

    lines += ["", "## Patterns", "", "| Share of prompts | Pilot | New | All |", "|---|---:|---:|---:|"]
    sonnet, deep = MODELS.index(ANCHOR), 0
    measures = {
        "All 4 pass": (fails.sum(1) == 0),
        "All 4 fail": (fails.sum(1) == 4),
        "At least one passes (ceiling)": (fails.sum(1) < 4),
        "DeepSeek passes, Sonnet fails": (fails[:, deep] == 0) & (fails[:, sonnet] == 1),
        "Sonnet passes, DeepSeek fails": (fails[:, deep] == 1) & (fails[:, sonnet] == 0),
    }
    for name, hit in measures.items():
        lines.append(f"| {name} | " + " | ".join(f"{hit[g].mean():.1%}" for g in groups.values()) + " |")

    vecs = vectors(order)
    sess = np.unique(split.loc[order, "session_id"].to_numpy(), return_inverse=True)[1]
    lines += ["", "## Separability and stability", "",
              "| Set | n | D, K = 1 | D, K = 3 | D, K = 8 | C, K = 3 | C, K = 8 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    cuts = {k: centers(Path(f"runs/s5/view/k_{k:02d}.npz")) for k in (3, 8)}
    assign = {k: ((vecs[:, None, :] - c[None, :, :]) ** 2).sum(-1).argmin(1) for k, c in cuts.items()}
    assign[1] = np.zeros(len(order), int)
    for name, g in groups.items():
        cells, stab = [], []
        for k in (1, 3, 8):
            lab = assign[k][g]
            psi = fit_psi(fails[g], lab, k, "pt", anchor=sonnet)
            cells.append(f"{separability(psi, np.bincount(lab, minlength=k)):.3f}")
            if k > 1:
                c = fingerprint_stability(fails[g], lab, k, SEED, repeats=5, groups=sess[g], method="pt", anchor=sonnet)
                stab.append(f"{c:.3f}")
        lines.append(f"| {name} | {g.sum()} | {' | '.join(cells)} | {' | '.join(stab)} |")

    for k in (3, 8):
        lab = assign[k]
        lines += ["", f"## Pass rate by cluster, K = {k}, all validation", "",
                  "| Cluster | n | pilot n | all fail | " + " | ".join(MODELS) + " |",
                  "|---:|---:|---:|---:|" + "---:|" * len(MODELS)]
        for c in range(k):
            g = lab == c
            cells = " | ".join(f"{1 - fails[g, j].mean():.1%}" for j in range(4))
            lines.append(f"| {c} | {g.sum()} | {(g & pilot).sum()} | {(fails[g].sum(1) == 4).mean():.1%} | {cells} |")
    Path("results/val_vs_pilot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
