"""WP-14: which prompt signals predict the winning model? Bot groups (D-078) and simple features.

Validation only, no paid calls, never a *.sealed* file. Every signal is scored the same held-out way as
S9. Many signals are tried on one set, so a small win here can be luck: read with the shuffle column.

Usage: uv run python scripts/s11_signal_tests.py
Writes results/signal_tests.md (aggregates only).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from router_check import SEED, cluster_labels, load_val, vectors

from metis.config import load_config
from metis.eval.baselines import ZeroRouter
from metis.eval.metrics import area, sweep
from metis.router.route import cluster_choices
from metis.router.select_k import halvings
from metis.router.select_lambda import lambda_grid

SHUFFLES = 100
CHEAP_LAMBDA = 0.1
DEEPSEEK = 0


def bot_groups(bot_ids: pd.Series) -> np.ndarray:
    """The 6 big bot clusters of k = 13, everything else in one group (D-078)."""
    bots = pd.read_parquet("runs/bot_clusters/bots.parquet", columns=["bot_id", "h"])
    with np.load("runs/bot_clusters/fits.npz") as z:
        by_hash = dict(zip(z["h"].tolist(), z["k_13"].tolist(), strict=True))
    cluster = bots.set_index("bot_id")["h"].map(by_hash)
    rows = json.loads(Path("experiments/bot_clusters/clusters_k13.json").read_text("utf-8"))
    big = [r["c"] for r in sorted((r for r in rows if r["c"] >= 0), key=lambda r: -r["n"])[:6]]
    mapped = bot_ids.map(cluster).to_numpy()
    return np.array([big.index(c) if c in big else 6 for c in mapped])


def table(losses: np.ndarray, labels: np.ndarray, fit: np.ndarray) -> np.ndarray:
    """Fail rate per group fitted on `fit`; a group not seen gets the overall rate."""
    overall = losses[fit].mean(0)
    out = np.tile(overall, (labels.max() + 1, 1))
    for g in np.unique(labels[fit]):
        out[g] = losses[fit][labels[fit] == g].mean(0)
    return out


def additive(losses, a, b, fit) -> np.ndarray:
    """D-078 per prompt: overall + (group a - overall) + (group b - overall)."""
    overall = losses[fit].mean(0)
    return np.clip(table(losses, a, fit)[a] + table(losses, b, fit)[b] - overall, 0, 1)


def scores(gamma_of, losses, c_hat, lams, splits) -> tuple[float, float]:
    """Held-out area, and pass rate minus DeepSeek at the cheap lambda."""
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    areas, gaps = [], []
    for a, b in splits:
        for fit, on in ((a, b), (b, a)):
            gamma = gamma_of(fit)[on]
            rows = np.arange(len(on))
            costs, q = sweep(rows, gamma, c_hat, lams, losses[on])
            areas.append(area(costs, q, c_min, c_max))
            pick = cluster_choices(gamma, c_hat, np.array([CHEAP_LAMBDA]))[0]
            gaps.append((1 - losses[on][rows, pick]).mean() - (1 - losses[on][:, DEEPSEEK]).mean())
    return float(np.mean(areas)), float(np.mean(gaps))


def main() -> None:
    cfg = load_config("pipeline")["router"]
    order, losses, groups, c_hat = load_val()
    msg = cluster_labels(vectors(order))
    p = pd.read_parquet(
        "runs/s1/prompts.parquet",
        columns=["prompt_id", "bot_id", "uses_rag", "lang", "instr_len_bucket", "text_chars", "est_tokens_in", "category"],
    ).set_index("prompt_id").loc[order]

    def codes(s: pd.Series) -> np.ndarray:
        return pd.factorize(s.astype(object).fillna("none").astype(str).astype(object), sort=True, use_na_sentinel=False)[0]

    bots = bot_groups(p["bot_id"])
    signals = {
        "No signal (K = 1)": np.zeros(len(order), int),
        "Message K = 8": msg[8],
        "Message K = 4": msg[4],
        "Bot groups": bots,
        "Single bot, top 20 + other": codes(p["bot_id"].where(p["bot_id"].isin(p["bot_id"].value_counts().index[:20]), "other")),
        "Bot category": codes(p["category"]),
        "Uses RAG": codes(p["uses_rag"]),
        "Language": codes(p["lang"]),
        "Instruction length": codes(p["instr_len_bucket"]),
        "Message length, 4 bands": np.searchsorted(np.quantile(p["text_chars"], [0.25, 0.5, 0.75]), p["text_chars"]),
        "Prompt tokens, 4 bands": np.searchsorted(np.quantile(p["est_tokens_in"], [0.25, 0.5, 0.75]), p["est_tokens_in"]),
    }
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
    splits = halvings(len(losses), cfg["select_k_repeats"], SEED, groups)
    few = splits[:5]
    rng = np.random.default_rng(SEED)

    zero = float(np.mean([
        area(*ZeroRouter(losses[f], c_hat).curve(None, None, losses[s]), float(c_hat.min()), float(c_hat.max()))
        for a, b in splits for f, s in ((a, b), (b, a))
    ]))
    lines = [
        "# Signal tests on validation", "",
        f"Measured, held out, n = {len(order)}, 40 halves. ZeroRouter area {zero:.4f}.",
        f"Cheap gap: pass rate minus always-DeepSeek at λ = {CHEAP_LAMBDA}. Shuffle: same groups in random order, {SHUFFLES} times, 95th percentile of area gain.",
        "Many signals were tried on one set, so a small win can be luck.", "",
        "| Signal | Groups | Area | Minus ZeroRouter | Shuffle 95% | Beats shuffle | Cheap gap |",
        "|---|---:|---:|---:|---:|---|---:|",
    ]

    def row(name, n, gamma_of, shuffle_of=None):
        a, gap = scores(gamma_of, losses, c_hat, lams, splits)
        limit, beats = "", ""
        if shuffle_of is not None:
            base = scores(lambda f: table(losses, np.zeros(len(order), int), f)[np.zeros(len(order), int)], losses, c_hat, lams, few)[0]
            null = []
            for _ in range(SHUFFLES):
                gamma = shuffle_of(rng.permutation(len(order)))
                null.append(scores(gamma, losses, c_hat, lams, few)[0] - base)
            limit = f"{np.percentile(null, 95):+.4f}"
            beats = "yes" if a - zero > np.percentile(null, 95) else "no"
        lines.append(f"| {name} | {n} | {a:.4f} | {a - zero:+.4f} | {limit} | {beats} | {gap:+.1%} |")

    for name, lab in signals.items():
        def gamma_of(fit, lab=lab):
            return table(losses, lab, fit)[lab]

        def shuffled(perm, lab=lab):
            s = lab[perm]
            return lambda fit: table(losses, s, fit)[s]

        row(name, len(np.unique(lab)), gamma_of, None if name.startswith("No signal") else shuffled)

    def both(perm, a_lab=msg[8], b_lab=bots):
        s = b_lab[perm]
        return lambda fit: additive(losses, a_lab, s, fit)

    row("Message K = 8 + bot groups (D-078)", 13, lambda f: additive(losses, msg[8], bots, f), both)
    row("Message K = 4 + bot groups (D-078)", 9, lambda f: additive(losses, msg[4], bots, f), lambda perm: both(perm, msg[4]))

    share = pd.Series(bots).value_counts(normalize=True).sort_index()
    lines += ["", "Bot group shares: " + ", ".join(f"{g}: {s:.0%}" for g, s in share.items()) + ".",
              f"Config hash: {hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]}."]
    Path("results/signal_tests.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
