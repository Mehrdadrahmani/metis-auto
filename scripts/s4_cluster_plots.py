"""WP-03b: pictures of the Persian clustering test (no LLM calls).

1. results/wp03b_persian/figures/persian_k_curves.png: NMI, silhouette, small-cluster count and Khayyam difficulty
   gap vs K, both models, 95 % CI over the repeated splits (from results/wp03b_persian/persian_clustering_*.json).
2. results/wp03b_persian/figures/persian_map_<model>_<set>.png: UMAP of test prompts (split 1, K = 8, the paper's
   largest K for N_val = 400), left coloured by cluster, right by the known label. Dots only, no text.
3. runs/s4/persian_map_<model>.html (git-ignored, local only): the same maps, interactive; hover shows
   the label and the first 200 characters of the prompt, for the owner.

Usage: uv run python scripts/s4_cluster_plots.py [--models nano,small]
"""

from __future__ import annotations

import argparse
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import umap
from plotly.subplots import make_subplots
from s4_persian_cluster import (
    EXT,
    K_PAPER,
    ROOT,
    SEED,
    Store,
    assign,
    build_sets,
    load_all,
    log,
    split,
)
from sklearn.cluster import KMeans

FIG = ROOT / "results" / "wp03b_persian" / "figures"
COLORS = {"nano": "#6c8ebf", "small": "#d79b00"}
SETS = {"mix": "mix (EmbedLLM-like)", "khayyam": "Khayyam (38 categories)", "mmlu": "Global-MMLU",
        "one_topic": "one topic (Headlines-like)", "chat": "chat (no labels)"}  # fmt: skip
MAIN_LABEL = {
    "mix": "source",
    "khayyam": "label",
    "mmlu": "fine",
    "one_topic": "fine",
    "chat": "source",
}
MAP_SETS = ("mix", "khayyam", "chat")
MAX_POINTS = 6000


def curve(ax, res: dict, model: str, path: list[str], label: str | None = None) -> None:
    ks = sorted(int(k) for k in res["K"])
    m, h = [], []
    for k in ks:
        x = res["K"][str(k)]
        for p in path:
            x = x[p]
        m.append(x["mean"])
        h.append(x["ci95"] or 0)
    ax.errorbar(ks, m, yerr=h, color=COLORS[model], marker="o", ms=3, lw=1.2, capsize=2,
                label=label or model)  # fmt: skip


def k_curves(results: dict[str, dict]) -> None:
    rows = [
        ("nmi", "NMI vs known label (test)"),
        ("sil", "cosine silhouette (test)"),
        ("small", "val clusters with < 50 prompts"),
    ]
    fig, axes = plt.subplots(len(rows), len(SETS), figsize=(4 * len(SETS), 9), squeeze=False)
    for j, name in enumerate(SETS):
        for i, (kind, title) in enumerate(rows):
            ax = axes[i][j]
            for model, res in results.items():
                r = res["sets"].get(name)
                if r is None:
                    continue
                if kind == "nmi":
                    if name == "chat":
                        ax.text(0.5, 0.5, "no labels", ha="center", transform=ax.transAxes)
                        continue
                    curve(ax, r, model, [MAIN_LABEL[name], "nmi"])
                elif kind == "sil":
                    curve(ax, r, model, ["silhouette"])
                else:
                    curve(ax, r, model, ["val_small"])
            ax.axvspan(min(K_PAPER) - 0.5, max(K_PAPER) + 0.5, color="#fff2cc", zorder=0)
            ax.set_xscale("log", base=2)
            ax.set_xticks([3, 4, 6, 8, 16, 32, 64], ["3", "4", "6", "8", "16", "32", "64"])
            if i == 0:
                ax.set_title(f"{SETS[name]}\n" + (f"label = {MAIN_LABEL[name]}" if name != "chat" else ""),
                             fontsize=9)  # fmt: skip
            if j == 0:
                ax.set_ylabel(title, fontsize=9)
            if i == len(rows) - 1:
                ax.set_xlabel("K (yellow = paper range 3..N_val/50)", fontsize=8)
            ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "persian_k_curves.png", dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, name in zip(axes, ("khayyam", "one_topic")):
        for model, res in results.items():
            r = res["sets"].get(name)
            if r is None or "difficulty" not in r["K"]["3"]:
                continue
            curve(ax, r, model, ["difficulty", "val", "gap_reduction"], f"{model}: Ψ from val 400")
            ks = sorted(int(k) for k in r["K"])
            tr = [r["K"][str(k)]["difficulty"]["train"]["gap_reduction"]["mean"] for k in ks]
            ax.plot(
                ks,
                tr,
                color=COLORS[model],
                ls="--",
                lw=1,
                label=f"{model}: Ψ from train (no noise)",
            )
        ax.axhline(0, color="black", lw=0.6)
        ax.axvspan(min(K_PAPER) - 0.5, max(K_PAPER) + 0.5, color="#fff2cc", zorder=0)
        ax.set_xscale("log", base=2)
        ax.set_xticks([3, 4, 6, 8, 16, 32, 64], ["3", "4", "6", "8", "16", "32", "64"])
        ax.set_title(f"{SETS[name]}: human error gap shrink vs K = 1", fontsize=9)
        ax.set_xlabel("K")
        ax.set_ylabel("1 − E|e − Ψ_k| / E|e − ē|  (test)", fontsize=8)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "persian_difficulty_gap.png", dpi=130)
    plt.close(fig)


def maps(model: str, task: str) -> None:
    store = Store(EXT / "emb" / f"{model}_{task}")
    sets = build_sets(load_all())
    fig_html = make_subplots(rows=len(MAP_SETS), cols=2, vertical_spacing=0.05,
                             subplot_titles=[f"{SETS[s]}: {t}" for s in MAP_SETS for t in ("K-means cluster (K = 8)", "known label")])  # fmt: skip
    for row, name in enumerate(MAP_SETS, start=1):
        d, _ = sets[name]
        if d.empty:
            continue
        d = d.reset_index(drop=True)
        v = store.get(d["text"].tolist())
        tr, _, te = split(len(d), SEED)
        c = assign(
            v, KMeans(n_clusters=8, n_init=10, random_state=SEED).fit(v[tr]).cluster_centers_
        )
        te = np.random.default_rng(SEED).choice(te, size=min(MAX_POINTS, len(te)), replace=False)
        xy = umap.UMAP(
            n_neighbors=30, min_dist=0.1, metric="cosine", random_state=SEED
        ).fit_transform(v[te])
        lab = d[MAIN_LABEL[name]].astype(str).to_numpy()[te]
        top = list(d[MAIN_LABEL[name]].astype(str).value_counts().index[:10])
        lab_plot = np.where(np.isin(lab, top), lab, "other")
        if name == "khayyam":  # numbered in the PNG legend; names (dataset metadata) in a side file
            (FIG / "persian_map_khayyam_legend.json").write_text(
                json.dumps(
                    {f"category {i + 1}": lb for i, lb in enumerate(top)}, ensure_ascii=False
                )
            )
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
        cmap = plt.get_cmap("tab10")
        for k in range(8):
            m = c[te] == k
            axes[0].scatter(
                xy[m, 0], xy[m, 1], s=3, color=cmap(k % 10), label=f"cluster {k}", alpha=0.6
            )
        cats = top + (["other"] if (lab_plot == "other").any() else [])
        m = lab_plot == "other"  # drawn first, light grey, so the named labels stay visible
        axes[1].scatter(xy[m, 0], xy[m, 1], s=2, color="#d0d0d0", label="other", alpha=0.5)
        for i, lb in enumerate(top):
            m = lab_plot == lb
            # Khayyam category names are Persian; matplotlib can't shape them, so use numbers there
            name_lb = lb if name != "khayyam" else f"category {i + 1}"
            axes[1].scatter(xy[m, 0], xy[m, 1], s=3, color=cmap(i % 10), label=name_lb, alpha=0.7)
        for ax, t in zip(
            axes, ("K-means cluster (K = 8, fit on train)", f"known {MAIN_LABEL[name]}")
        ):
            ax.set_title(t, fontsize=10)
            lo, hi = np.percentile(xy, [0.5, 99.5], axis=0)  # a few far outliers squash the view
            pad = 0.05 * (hi - lo)
            ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0])
            ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
            ax.set_xticks([])
            ax.set_yticks([])
            ax.legend(fontsize=6, markerscale=3, loc="best", ncol=2)
        fig.suptitle(f"{model}: {SETS[name]}, {len(te)} test prompts, UMAP (cosine)", fontsize=11)
        fig.tight_layout()
        fig.savefig(FIG / f"persian_map_{model}_{name}.png", dpi=120)
        plt.close(fig)
        hover = [f"{a} | cluster {b}<br>{t[:200]}" for a, b, t in
                 zip(lab, c[te], d["text"].to_numpy()[te])]  # fmt: skip
        for col, colour in ((1, c[te]), (2, None)):
            if colour is not None:
                fig_html.add_trace(go.Scattergl(x=xy[:, 0], y=xy[:, 1], mode="markers", text=hover, hoverinfo="text",
                                                marker={"size": 3, "color": colour, "colorscale": "Turbo"},
                                                showlegend=False), row=row, col=col)  # fmt: skip
            else:
                for lb in cats:
                    m = lab_plot == lb
                    fig_html.add_trace(go.Scattergl(x=xy[m, 0], y=xy[m, 1], mode="markers", name=f"{name}: {lb}",
                                                    text=[hover[i] for i in np.flatnonzero(m)], hoverinfo="text",
                                                    marker={"size": 3}), row=row, col=col)  # fmt: skip
        log(f"  map {model}/{name}: {len(te)} points")
    fig_html.update_layout(
        height=650 * len(MAP_SETS), width=1300, title=f"Persian clusters map: {model}"
    )
    fig_html.write_html(ROOT / "runs" / "s4" / f"persian_map_{model}.html", include_plotlyjs="cdn")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", default="nano,small")
    ap.add_argument("--no-maps", action="store_true")
    a = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)
    results = {}
    for m in a.models.split(","):
        p = ROOT / "results" / "wp03b_persian" / f"persian_clustering_{m}.json"
        if p.exists():
            results[m] = json.loads(p.read_text())
    if not results:
        sys.exit("no results/wp03b_persian/persian_clustering_*.json yet")
    k_curves(results)
    log("curves: results/wp03b_persian/figures/persian_k_curves.png, persian_difficulty_gap.png")
    if not a.no_maps:
        for m, res in results.items():
            maps(m, res["task"])
    log("done")


if __name__ == "__main__":
    main()
