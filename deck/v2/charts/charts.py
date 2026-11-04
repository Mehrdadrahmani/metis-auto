"""Deck charts, dark style. Aggregates only, no prompt text. Run from repo root: uv run python charts.py <outdir>"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle

OUT = Path(sys.argv[1])
HERE = Path(__file__).parent
BG, CARD, INK, MUTED, GRID = "#ffffff", "#ffffff", "#17132b", "#514c6b", "#e8e6f2"
PURPLE, BLUE, GREEN, AMBER, PINK, TEAL = "#7a22e0", "#3366ff", "#0f9d6e", "#e08a00", "#e0336e", "#0e8088"
MC = {"DeepSeek": BLUE, "Luna": GREEN, "Gemini": AMBER, "Sonnet": PINK, "DeepSeek Pro": TEAL}
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID,
    "font.family": "DejaVu Sans", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def heat(ax, data, rows, cols, fmt, cmap, picks=None, vmin=None, vmax=None, best="min"):
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(cols)), cols, color=INK, fontsize=13)
    ax.set_yticks(range(len(rows)), rows, color=INK, fontsize=13)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = data[i, j]
            r, g, b_, _ = im.cmap(im.norm(v))
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b_
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=13, fontweight="bold",
                    color="#0f0c1d" if lum > 0.45 else "#ffffff")
        if picks is not None:
            ax.add_patch(Rectangle((picks[i] - 0.48, i - 0.46), 0.96, 0.92, fill=False, ec="#17132b", lw=3))
    return im


# 1. Iceberg -----------------------------------------------------------------------------
def iceberg():
    fig, ax = plt.subplots(figsize=(13, 7.2))
    ax.set_xlim(0, 13); ax.set_ylim(0, 7.2); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 13, 4.6, color="#13284a", zorder=0))
    ax.plot([0, 13], [4.6, 4.6], color=BLUE, lw=2, zorder=3)
    ax.add_patch(Polygon([[4.3, 4.6], [6.8, 6.75], [9.3, 4.6]], closed=True, fc="#e6f0ff", ec="#ffffff", zorder=2))
    ax.add_patch(Polygon([[4.3, 4.6], [9.3, 4.6], [12.9, 2.4], [11.9, 0.15], [1.1, 0.15], [0.1, 2.4]], closed=True,
                         fc="#3b6fb3", ec="#7fb0ff", alpha=0.55, zorder=1))
    top = [("ChatGPT", 90), ("Gemini", 83), ("Copilot", 66), ("Claude", 51)]
    for i, (m, p) in enumerate(top):
        ax.text(6.8, 5.75 - i * 0.33, f"{m}  {p}%", ha="center", va="center", fontsize=14, fontweight="bold", color="#14213d", zorder=4)
    ax.text(0.1, 6.9, "Famous: % of US adults who have heard of them", fontsize=14, color=INK, fontweight="bold")
    ax.text(0.1, 6.5, "Verasight survey, June 2026, n = 1,690", fontsize=12, color=MUTED)
    ax.text(0.1, 4.75, "500+ models on OpenRouter", ha="left", fontsize=14, color=BLUE, fontweight="bold")
    below = [
        ("DeepSeek", "heard of by only 31%, yet beat Sonnet on our Persian test: 68.6% vs 64.9% at 1/24 the price"),
        ("Kimi K2.6 · MiMo V2.5 Pro", "not even in the survey; score 54 on the Artificial Analysis index (Claude Opus 4.7: 57)"),
        ("Best open models", "within 3–6 points of the leaders at 1/2 to 1/6 of the price (Artificial Analysis, Apr 2026)"),
        ("…and hundreds more", "that most people never try"),
    ]
    for i, (h, t) in enumerate(below):
        y = 3.85 - i * 0.92
        ax.text(1.6, y, h, fontsize=15, fontweight="bold", color="#ffffff", zorder=4)
        ax.text(1.6, y - 0.36, t, fontsize=12.5, color="#dbe7ff", zorder=4)
    save(fig, "iceberg.png")


# 2. Why-now heat maps (chatbot K=4 fail rates, Khayyam per-subject accuracy) -------------
def whynow():
    fails = np.array([[22, 30, 40, 23], [45, 50, 66, 50], [31, 31, 34, 30], [36, 39, 43, 31]], float)
    rows = ["Everyday knowledge", "Short follow-ups", "Requests & support", "Personal chat"]
    kh = json.load(open("results/khayyam/khayyam_router.json"))
    km = ["gemini-2.5-flash-lite", "deepseek-v4-flash", "gpt-5.6-luna", "deepseek-v4-pro"]
    kc = [c for c in kh["clusters"] if not c["name_en"].startswith("Mixed")]
    acc = np.array([[c["test"][m] * 100 for m in km] for c in kc])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1, 1.05], "wspace": 0.55})
    heat(a1, fails, rows, ["DeepSeek", "Luna", "Gemini", "Sonnet"], lambda v: f"{v:.0f}%", "magma_r",
         picks=fails.argmin(1), vmin=15, vmax=70)
    a1.set_title("Chatbot messages: fail rate (lower is better)", color=INK, fontsize=14, loc="left", pad=12)
    heat(a2, acc, [c["name_en"] for c in kc], ["Gemini", "DeepSeek", "Luna", "DS Pro"], lambda v: f"{v:.0f}%",
         "viridis", picks=acc.argmax(1), vmin=30, vmax=75)
    a2.set_title("Khayyam exam: accuracy (higher is better)", color=INK, fontsize=14, loc="left", pad=12)
    fig.text(0.01, -0.04, "Black box = best model in that row.  Left: 798 validation prompts, AI judge.  "
             "Right: 1,100 Persian exam questions with true answers.", color=MUTED, fontsize=12)
    save(fig, "whynow_heat.png")


# 3. Market: monthly cost at 1M messages ------------------------------------------------
def market():
    names = ["Claude Sonnet", "GPT-5.6 Luna", "TakRouter\n+ 20% fee"]
    usd = [16320, 840, 828]
    pas = ["64.9%", "61.9%", "66.9%"]
    cols = [PINK, GREEN, PURPLE]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    bars = ax.barh(names[::-1], usd[::-1], color=cols[::-1], height=0.6)
    for b, u, p in zip(bars, usd[::-1], pas[::-1]):
        ax.text(b.get_width() + 200, b.get_y() + b.get_height() / 2, f"${u:,}  ·  pass {p}", va="center",
                fontsize=15, fontweight="bold", color=INK)
    ax.set_xlim(0, 22500); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=15, colors=INK, length=0)
    ax.set_title("Monthly cost for 1 million messages", color=INK, fontsize=16, loc="left", pad=10)
    save(fig, "market_bars.png")


# 4. Cluster sizes (validation counts of the shipped router) ------------------------------
def cluster_sizes():
    names = json.load(open("artifacts/router_v1/artifact.json"))["cluster_names"]
    counts = np.load("artifacts/router_v1/counts.npy")
    o = np.argsort(counts)
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.barh([names[i] for i in o], counts[o], color=PURPLE, height=0.65)
    for y, i in enumerate(o):
        ax.text(counts[i] + 3, y, f"{counts[i]}", va="center", fontsize=13, color=INK)
    ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=13, colors=INK, length=0)
    ax.set_title("Validation prompts per topic (n = 798)", color=INK, fontsize=14, loc="left")
    save(fig, "cluster_sizes.png")


# 5. Psi heat map with picks --------------------------------------------------------------
def psi_map():
    a = json.load(open("artifacts/router_v1/artifact.json"))
    psi = np.load("artifacts/router_v1/psi.npy")
    c = np.load("artifacts/router_v1/c_hat.npy")
    picks = (psi + a["lam"] * c[None, :]).argmin(1)
    fig, ax = plt.subplots(figsize=(9.5, 6.6))
    heat(ax, psi * 100, a["cluster_names"], ["DeepSeek", "Luna", "Gemini", "Sonnet"], lambda v: f"{v:.0f}%",
         "magma_r", picks=picks, vmin=15, vmax=70)
    ax.set_title("Error rate Ψ per topic (validation, n = 798) · black box = router's pick at λ = 0.515",
                 color=INK, fontsize=13, loc="left", pad=12)
    save(fig, "psi_heat.png")
    return {a["cluster_names"][i]: int(picks[i]) for i in range(len(picks))}, psi, c, a["lam"]


# 6. Validation deferral curves -----------------------------------------------------------
def curves():
    d = json.load(open(HERE / "val_curves.json"))
    ch = np.array(d["c_hat"])
    fig, ax = plt.subplots(figsize=(11, 6.2))
    style = {"UniRoute K = 8": (PURPLE, "-", 3.2), "UniRoute K = 4": ("#c084fc", "-", 2.4), "ZeroRouter": (MUTED, "--", 2),
             "K-NN k = 80": (TEAL, ":", 2.2), "Logistic": (AMBER, "-.", 2)}
    for name, v in d["curves"].items():
        col, ls, lw = style[name]
        ax.plot(v["cost"], np.array(v["quality"]) * 100, ls=ls, color=col, lw=lw,
                label=f"{name}  (area {d['areas'][name]:.3f})")
    for m, lab in zip(range(4), ["DeepSeek", "Luna", "Gemini", "Sonnet"]):
        ax.scatter(ch[m], d["single_quality"][m] * 100, s=140, color=MC[lab], zorder=5, edgecolor="#17132b", lw=1)
        ax.annotate(lab, (ch[m], d["single_quality"][m] * 100), xytext={"DeepSeek": (-40, 14), "Sonnet": (-30, 14), "Luna": (10, -22), "Gemini": (10, -22)}[lab],
                    textcoords="offset points", fontsize=13, color=MC[lab], fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlabel("Average cost per message, relative to always-Sonnet (log scale)", fontsize=13)
    ax.set_ylabel("Pass rate, %", fontsize=13)
    ax.grid(color=GRID, lw=0.8)
    ax.annotate("better ↖", xy=(0.03, 0.93), xycoords="axes fraction", fontsize=14, color=INK, fontweight="bold")
    ax.legend(frameon=False, fontsize=12, loc="lower right", labelcolor=INK)
    save(fig, "val_curves.png")


# 7. AUDC + QNC on sealed test ------------------------------------------------------------
def audc_qnc():
    f = json.load(open("results/final/final.json"))
    rows = [r for r in f["ladder"] if r["router"] != "Always-Sonnet"]
    names = [r["router"].replace("UniRoute ", "UniRoute\n") for r in rows]
    area_ = np.array([r["area"] for r in rows])
    k8 = rows[0]["area"]  # low/high are the CI of (router - K = 8), so the band is K8 + [low, high]
    lo = np.array([min(r["area"], k8 + r["low"]) for r in rows])
    hi = np.array([max(r["area"], k8 + r["high"]) for r in rows])
    qn = np.array([r["qnc"] for r in rows])
    cols = [PURPLE if "UniRoute" in r["router"] else ("#8a84a3" if "cheapest" in r["router"] else TEAL) for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.2), gridspec_kw={"wspace": 0.28})
    y = np.arange(len(rows))[::-1]
    a1.barh(y, area_, color=cols, height=0.62)
    a1.errorbar(area_, y, xerr=[area_ - lo, hi - area_], fmt="none", ecolor="#17132b", capsize=4, lw=1.4)
    for yi, v in zip(y, area_):
        a1.text(0.405, yi, f"{v:.3f}", va="center", ha="left", fontsize=13, color="#ffffff", fontweight="bold")
    a1.set_yticks(y, names, fontsize=12.5, color=INK); a1.set_xlim(0.4, 0.75)
    a1.set_title("AUDC: area under the deferral curve (higher is better)", color=INK, fontsize=14, loc="left")
    a1.set_xlabel("Bars: 95% CI of the difference from UniRoute K = 8, drawn around each value", fontsize=11)
    a1.tick_params(axis="y", length=0)
    rq = [(n, q, c) for n, q, c in zip(names, qn, cols) if q < 1]
    y2 = np.arange(len(rq))[::-1]
    a2.barh(y2, [q for _, q, _ in rq], color=[c for *_, c in rq], height=0.62)
    for yi, (_, q, _) in zip(y2, rq):
        a2.text(q + 0.0006, yi, f"{q:.3f}", va="center", fontsize=13, color=INK, fontweight="bold")
    a2.set_yticks(y2, [n for n, *_ in rq], fontsize=12.5, color=INK); a2.set_xlim(0, 0.05)
    a2.set_title("QNC: cost to match the best single model (lower is better)", color=INK, fontsize=14, loc="left")
    a2.set_xlabel("Share of the best single model's cost; always-cheapest never reaches it", fontsize=11)
    a2.tick_params(axis="y", length=0)
    save(fig, "audc_qnc.png")


# 8. Winner per cluster: Metis vs Khayyam -------------------------------------------------
def winners(psi_picks, psi=None, names=None):
    kh = json.load(open("results/khayyam/khayyam_router.json"))
    km = {"gemini-2.5-flash-lite": "Gemini", "deepseek-v4-flash": "DeepSeek", "gpt-5.6-luna": "Luna", "deepseek-v4-pro": "DeepSeek Pro"}
    mlab = ["DeepSeek", "Luna", "Gemini", "Sonnet"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"wspace": 0.75})
    for ax, title, items in (
        (a1, "Metis chatbot data: lowest error per topic (validation)",
         [(names[i], " = ".join(mlab[j] for j in range(4) if psi[i, j] <= psi[i].min() + 0.005)) for i in range(len(names))]),
        (a2, "Khayyam exam: most accurate model per subject (test)",
         [(c["name_en"].replace("Mixed (Maths and logic, Psychology)", "Mixed (maths, psychology)"),
           " = ".join(km[m] for m, v in c["test"].items() if v >= max(c["test"].values()) - 0.005)) for c in kh["clusters"]]),
    ):
        for i, (name, w) in enumerate(items):
            ax.add_patch(Rectangle((0, -i - 0.4), 1, 0.8, color=MC[w.split(" = ")[0]]))
            ax.text(0.5, -i, w + ("  (tie)" if " = " in w else ""), ha="center", va="center", fontsize=13, fontweight="bold", color="#ffffff")
            ax.text(-0.08, -i, name, ha="right", va="center", fontsize=13, color=INK)
        ax.set_xlim(0, 1); ax.set_ylim(-len(items) + 0.4, 0.6); ax.axis("off")
        ax.set_title(title, color=INK, fontsize=14, loc="right", pad=10)
    save(fig, "winners.png")


# 9. Khayyam deferral curve (backup) -------------------------------------------------------
def khayyam_curve():
    kh = json.load(open("results/khayyam/khayyam_router.json"))
    cv = kh["curve"]
    c = [p["cost"] for p in cv]; q = [p["acc"] * 100 for p in cv]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.plot(c, q, color=PURPLE, lw=3, label=f"UniRoute K = {kh['k_star']}  (area {kh['area_router']:.3f})")
    names = {"gemini-2.5-flash-lite": "Gemini", "deepseek-v4-flash": "DeepSeek", "gpt-5.6-luna": "Luna", "deepseek-v4-pro": "DeepSeek Pro"}
    pts = sorted((kh["c_hat"][i], kh["test_accuracy"][m] * 100, names[m]) for i, m in enumerate(kh["models"]))
    for x, yv, lab in pts:
        ax.scatter(x, yv, s=130, color=MC[lab], edgecolor="#ffffff", zorder=5)
        ax.annotate(lab, (x, yv), xytext=(8, -16), textcoords="offset points", color=MC[lab], fontsize=13, fontweight="bold")
    ax.set_xlabel("Relative cost"); ax.set_ylabel("Accuracy, %"); ax.grid(color=GRID)
    ax.set_title(f"Khayyam test (n = {kh['n_test']}): area gain over ZeroRouter +{kh['area_gain']:.3f}", color=INK, loc="left")
    ax.legend(frameon=False, labelcolor=INK, loc="lower right")
    save(fig, "khayyam_curve.png")


OUT.mkdir(parents=True, exist_ok=True)
whynow(); market(); cluster_sizes()
picks, psi, c, lam = psi_map()
curves(); audc_qnc(); winners(picks, psi, list(picks)); khayyam_curve()
print("picks", picks)
print("example cluster Health:", np.round(psi[7], 3), "lam*c", np.round(lam * c, 4), "score", np.round(psi[7] + lam * c, 3))
