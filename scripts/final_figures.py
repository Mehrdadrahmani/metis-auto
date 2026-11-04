"""Figures for the report from results/final/final.json. Palette checked with the dataviz validator."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

d = json.loads(Path("results/final/final.json").read_text(encoding="utf-8"))
Path("results/final/figures").mkdir(exist_ok=True)
names = {"deepseek-v4-flash": ("DeepSeek", "#1e88e5"), "gpt-5.6-luna": ("Luna", "#0f9d8a"), "gemini-2.5-flash-lite": ("Gemini", "#c98500"), "claude-sonnet-5-5": ("Sonnet", "#e0245e"), "K = 8": ("TakRouter K = 8", "#7a22e0"), "K = 4": ("TakRouter K = 4", "#7a22e0")}
n = d["n"]
fig, ax = plt.subplots(figsize=(7, 4))
for k, (label, c) in names.items():
    q, usd = d["pass_rates"][k], d["usd_1k"][k]
    se = 1.96 * (q * (1 - q) / n) ** 0.5
    ax.errorbar(usd, q * 100, yerr=se * 100, fmt="o", color=c, ms=8, capsize=0, lw=2)
    dx, dy, ha = {"K = 8": (10, 3, "left"), "deepseek-v4-flash": (-10, 3, "right"), "gpt-5.6-luna": (10, -12, "left")}.get(k, (0, 12, "center"))
    ax.annotate(label, (usd, q * 100), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=9)
ax.set_xscale("log")
ax.set_xlabel("Dollars per 1,000 messages (log scale)")
ax.set_ylabel("Pass rate, % (bars: normal 95% CI)")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#e8e6f2")
fig.tight_layout()
fig.savefig("results/final/figures/cost_quality.png", dpi=170)
