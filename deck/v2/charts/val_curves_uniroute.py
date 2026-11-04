"""Slide 24 plot: validation deferral curves for UniRoute K = 8 and K = 4 only, plus single models.
Aggregates only. Run from repo root: uv run python deck/v2/charts/val_curves_uniroute.py deck/v2/img"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE, OUT = Path(__file__).parent, Path(sys.argv[1])
INK, MUTED, GRID = "#17132b", "#514c6b", "#e8e6f2"
MC = {"DeepSeek": "#3366ff", "Luna": "#0f9d6e", "Gemini": "#e08a00", "Sonnet": "#e0336e"}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRID, "xtick.color": MUTED, "ytick.color": MUTED})
d = json.load(open(HERE / "val_curves.json"))
ch = np.array(d["c_hat"])
fig, ax = plt.subplots(figsize=(11, 6.2), facecolor="#ffffff")
for name, col, lw in (("UniRoute K = 8", "#7a22e0", 3.4), ("UniRoute K = 4", "#c084fc", 3.0)):
    v = d["curves"][name]
    ax.plot(v["cost"], np.array(v["quality"]) * 100, color=col, lw=lw, label=f"{name}  (area {d['areas'][name]:.3f})")
for m, lab in enumerate(["DeepSeek", "Luna", "Gemini", "Sonnet"]):
    q = d["single_quality"][m] * 100
    ax.scatter(ch[m], q, s=150, color=MC[lab], zorder=5, edgecolor=INK, lw=1)
    ax.annotate(lab, (ch[m], q), xytext={"DeepSeek": (-40, 14), "Sonnet": (-30, 14), "Luna": (10, -22), "Gemini": (10, -22)}[lab],
                textcoords="offset points", fontsize=14, color=MC[lab], fontweight="bold")
ax.set_xscale("log")
ax.set_xlabel("Cost per message, relative to always-Sonnet (log scale)", fontsize=14, color=MUTED)
ax.set_ylabel("Pass rate, %", fontsize=14, color=MUTED)
ax.grid(color=GRID, lw=0.8)
ax.annotate("better ↖", xy=(0.03, 0.93), xycoords="axes fraction", fontsize=15, color=INK, fontweight="bold")
ax.legend(frameon=False, fontsize=13, loc="lower right", labelcolor=INK)
fig.savefig(OUT / "val_curves_uniroute.png", dpi=200, bbox_inches="tight", pad_inches=0.15)
print({k: round(d["areas"][k], 3) for k in ("UniRoute K = 8", "UniRoute K = 4")})
