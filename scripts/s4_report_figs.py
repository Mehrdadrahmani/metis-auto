"""WP-03b report figures (numbers only, no text): data overview, model comparison, cluster composition.

Writes to report/persian_clustering/figures/:
  data_overview.png       rows per source, length (chars) per source, language mix
  model_compare.png       NMI at K = 8 per set and adapter; silhouette; run time
  composition_<set>.png   share of each known label inside each cluster (nano, K = 8, split 1, test part)

Usage: uv run python scripts/s4_report_figs.py
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from s4_persian_cluster import (
    CHAT,
    EXT,
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

from metis.data.lang import lang_tag

OUT = ROOT / "report" / "persian_clustering" / "figures"
BLUE, ORANGE, GREEN, GREY = "#6c8ebf", "#d79b00", "#82b366", "#999999"
RUNS = {
    "small": "small (clustering)",
    "nano": "nano (clustering)",
    "nano_text-matching": "nano (text-matching)",
}
RUN_COL = {"small": ORANGE, "nano": BLUE, "nano_text-matching": GREEN}
SETS = {"mix": ("mix", "source"), "khayyam": ("Khayyam", "label"), "mmlu": ("Global-MMLU", "fine"),
        "one_topic": ("one topic", "fine")}  # fmt: skip


def data_overview(df: pd.DataFrame) -> None:
    df = df.assign(chars=df["text"].str.len(), lang=df["text"].map(lang_tag))
    order = df["source"].value_counts().index.tolist()
    col = [GREEN if s in CHAT else BLUE for s in order]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1, 1.2, 1]})
    n = df["source"].value_counts()[order]
    axes[0].barh(order, n.values, color=col)
    for i, v in enumerate(n.values):
        axes[0].text(v, i, f" {v:,}", va="center", fontsize=8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("unique texts")
    axes[0].set_title("rows per source (blue = benchmark, green = chat)", fontsize=10)
    data = [np.log10(df.loc[df["source"] == s, "chars"].clip(lower=1)) for s in order]
    bp = axes[1].boxplot(
        data, orientation="horizontal", tick_labels=order, showfliers=False, patch_artist=True
    )
    for patch, c in zip(bp["boxes"], col):
        patch.set_facecolor(c)
        patch.set_alpha(0.5)
    axes[1].invert_yaxis()
    axes[1].set_xticks([1, 2, 3, 4], ["10", "100", "1,000", "10,000"])
    axes[1].set_xlabel("length in characters (log scale; box = middle 50 %)")
    axes[1].set_title("text length per source", fontsize=10)
    langs = ["fa", "mixed", "en", "other"]
    share = (pd.crosstab(df["source"], df["lang"], normalize="index").reindex(order).reindex(columns=langs)
             .fillna(0))  # fmt: skip
    left = np.zeros(len(order))
    for lg, c in zip(langs, [BLUE, ORANGE, GREEN, GREY]):
        axes[2].barh(order, share[lg].values, left=left, color=c, label=lg)
        left += share[lg].values
    axes[2].invert_yaxis()
    axes[2].set_xlim(0.8, 1.0)
    axes[2].set_xlabel("share of texts (axis starts at 80 %)")
    axes[2].set_title("language", fontsize=10)
    axes[2].legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "data_overview.png", dpi=130)
    plt.close(fig)


def model_compare() -> None:
    res = {
        r: json.loads(
            (ROOT / "results" / "wp03b_persian" / f"persian_clustering_{r}.json").read_text()
        )
        for r in RUNS
    }
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), gridspec_kw={"width_ratios": [2, 1.4, 0.8]})
    w = 0.26
    x = np.arange(len(SETS))
    for i, r in enumerate(RUNS):
        m = [res[r]["sets"][s]["K"]["8"][lb]["nmi"]["mean"] for s, (_, lb) in SETS.items()]
        h = [res[r]["sets"][s]["K"]["8"][lb]["nmi"]["ci95"] for s, (_, lb) in SETS.items()]
        axes[0].bar(x + (i - 1) * w, m, w, yerr=h, color=RUN_COL[r], label=RUNS[r], capsize=2)
    axes[0].set_xticks(x, [f"{t}\n(vs {lb})" for t, lb in SETS.values()], fontsize=8)
    axes[0].set_ylabel("NMI vs known label (test)")
    axes[0].set_title("match with known topics, K = 8 (higher = better)", fontsize=10)
    axes[0].legend(fontsize=8)
    sets2 = ["mix", "khayyam", "mmlu", "one_topic", "chat"]
    x2 = np.arange(len(sets2))
    for i, r in enumerate(RUNS):
        m = [res[r]["sets"][s]["K"]["8"]["silhouette"]["mean"] for s in sets2]
        axes[1].bar(x2 + (i - 1) * w, m, w, color=RUN_COL[r])
    axes[1].set_xticks(x2, ["mix", "Khayyam", "MMLU", "one topic", "chat"], fontsize=8)
    axes[1].set_ylabel("cosine silhouette (test)")
    axes[1].set_title("how well separated, K = 8", fontsize=10)
    t = [res[r]["duration_s"] / 60 for r in RUNS]
    axes[2].bar(range(len(RUNS)), t, color=[RUN_COL[r] for r in RUNS])
    axes[2].set_xticks(range(len(RUNS)), ["small", "nano", "nano\ntext-m."], fontsize=8)
    axes[2].set_ylabel("minutes")
    axes[2].set_title("run time (incl. new embeddings)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "model_compare.png", dpi=130)
    plt.close(fig)


def composition(sets: dict, store: Store) -> None:
    for name, col, top_n in (("mix", "source", 9), ("khayyam", "label", 12)):
        d, _ = sets[name]
        d = d.reset_index(drop=True)
        v = store.get(d["text"].tolist())
        tr, _, te = split(len(d), SEED)
        c = assign(
            v, KMeans(n_clusters=8, n_init=10, random_state=SEED).fit(v[tr]).cluster_centers_
        )
        lab = d[col].astype(str).to_numpy()
        top = list(pd.Series(lab).value_counts().index[:top_n])
        lab = np.where(np.isin(lab, top), lab, "other")
        tab = pd.crosstab(c[te], lab[te], normalize="index")
        tab = tab.reindex(columns=top + (["other"] if "other" in tab.columns else []))
        sizes = np.bincount(c[te], minlength=8)
        names = top if name == "mix" else [f"cat {i + 1}" for i in range(len(top))]
        names = names + (["other"] if "other" in tab.columns else [])
        fig, ax = plt.subplots(figsize=(1.0 + 0.75 * len(names), 4.6))
        im = ax.imshow(tab.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i in range(tab.shape[0]):
            for j in range(tab.shape[1]):
                val = tab.values[i, j]
                if val >= 0.05:
                    ax.text(j, i, f"{val:.0%}", ha="center", va="center", fontsize=7,
                            color="white" if val > 0.6 else "black")  # fmt: skip
        ax.set_xticks(range(len(names)), names, rotation=40, ha="right", fontsize=8)
        ax.set_yticks(range(8), [f"cluster {k} (n={sizes[k]})" for k in range(8)], fontsize=8)
        ax.set_xlabel(
            f"known {col}" + (" (names: khayyam_legend.json)" if name == "khayyam" else "")
        )
        fig.colorbar(im, ax=ax, fraction=0.03, label="share of the cluster")
        fig.tight_layout()
        fig.savefig(OUT / f"composition_{name}.png", dpi=130)
        plt.close(fig)
        if name == "khayyam":
            (OUT / "khayyam_legend.json").write_text(
                json.dumps(
                    {f"cat {i + 1}": lb for i, lb in enumerate(top)}, ensure_ascii=False, indent=1
                )
            )
        log(f"  composition {name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_all()
    data_overview(df)
    log("data overview")
    model_compare()
    log("model compare")
    composition(build_sets(df), Store(EXT / "emb" / "nano_clustering"))
    log(f"done: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
