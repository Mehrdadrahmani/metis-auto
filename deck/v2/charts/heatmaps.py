"""Heat maps for the deck in soft good/bad colours (green = good, coral = bad). Aggregates only.
Run from repo root: uv run python deck/v2/charts/heatmaps.py deck/v2/img"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

OUT = Path(sys.argv[1])
INK = "#17132b"
GOOD_BAD = LinearSegmentedColormap.from_list("goodbad", ["#cdebd9", "#fff4cc", "#f9c9b6", "#ee9a8a"])
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})


def draw(data, rows, cols, fmt, cmap, boxes, title, name, top=False, size=(10, 6.4), fs=15):
    fig, ax = plt.subplots(figsize=size, facecolor="#ffffff")
    ax.imshow(data, cmap=cmap, aspect="auto", vmin=data.min(), vmax=data.max())
    ax.set_xticks(range(len(cols)), cols, fontsize=fs, color=INK)
    ax.set_yticks(range(len(rows)), rows, fontsize=fs, color=INK)
    ax.tick_params(length=0)
    if top:
        ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows)), minor=True)
    ax.grid(which="minor", color="#ffffff", linewidth=3)
    ax.tick_params(which="minor", length=0)
    for i in range(len(rows)):
        for j in range(len(cols)):
            ax.text(j, i, fmt(data[i, j]), ha="center", va="center", fontsize=fs + 1, fontweight="bold", color=INK)
        for j in boxes[i]:
            ax.add_patch(Rectangle((j - 0.46, i - 0.44), 0.92, 0.88, fill=False, ec=INK, lw=3))
    if title:
        ax.set_title(title, color=INK, fontsize=13, loc="left", pad=12)
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


# Psi: error per topic (lower = better = green); box = router's pick
a = json.load(open("artifacts/router_v1/artifact.json"))
psi = np.load("artifacts/router_v1/psi.npy")
c = np.load("artifacts/router_v1/c_hat.npy")
picks = (psi + a["lam"] * c[None, :]).argmin(1)
draw(psi * 100, a["cluster_names"], ["DeepSeek", "Luna", "Gemini", "Sonnet"], lambda v: f"{v:.0f}%", GOOD_BAD,
     [[p] for p in picks], "Error rate Ψ per topic (validation, n = 798) · box = router's pick at λ = 0.515", "psi_heat.png",
     size=(9.5, 6.6), fs=13)

# Khayyam: accuracy per subject (higher = better = green); box = best
kh = json.load(open("results/khayyam/khayyam_router.json"))
km = ["deepseek-v4-flash", "gpt-5.6-luna", "gemini-2.5-flash-lite", "deepseek-v4-pro"]
cl = [x for x in kh["clusters"] if not x["name_en"].startswith("Mixed")]
acc = np.array([[x["test"][m] * 100 for m in km] for x in cl])
draw(acc, [x["name_en"] for x in cl], ["DeepSeek", "Luna", "Gemini", "DeepSeek Pro"], lambda v: f"{v:.0f}%", GOOD_BAD.reversed(),
     [[j for j in range(4) if acc[i, j] >= acc[i].max() - 0.5] for i in range(len(cl))], None, "khayyam_heat.png", top=True)
print("ok", picks)
