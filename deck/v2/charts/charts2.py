"""Cluster map (validation embeddings, no text), Khayyam heat map, typeset formulas. Run from repo root."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from router_check import load_val, vectors
from sklearn.manifold import TSNE

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID = "#17132b", "#514c6b", "#e8e6f2"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "mathtext.fontset": "cm"})
PAL = ["#3366ff", "#0f9d6e", "#e08a00", "#9933ff", "#e0336e", "#0e8088", "#8a6d3b", "#c2185b"]

# 1. Cluster map: validation prompts in 2-D (PCA of embeddings), coloured by the shipped router's topic
art = json.load(open("artifacts/router_v1/artifact.json"))
cent = np.load("artifacts/router_v1/centroids.npy")
order, losses, groups, c_hat = load_val()
x = vectors(order)
xn = x / np.linalg.norm(x, axis=1, keepdims=True)
cn = cent / np.linalg.norm(cent, axis=1, keepdims=True)
lab = np.argmax(xn @ cn.T, axis=1)
p = TSNE(n_components=2, perplexity=45, init="pca", random_state=20261020).fit_transform(xn)
c2 = np.array([np.median(p[lab == k], axis=0) for k in range(len(cn))])
fig, ax = plt.subplots(figsize=(13, 7.4), facecolor="#ffffff")
for k in range(len(cn)):
    m = lab == k
    ax.scatter(p[m, 0], p[m, 1], s=26, color=PAL[k], alpha=0.55, lw=0)
for k in range(len(cn)):
    ax.scatter(*c2[k], s=420, marker="o", color="#ffffff", edgecolor=PAL[k], lw=3.5, zorder=4)
    ax.annotate(art["cluster_names"][k], c2[k], xytext=(0, -40 if k == 3 else 22), textcoords="offset points", fontsize=14, ha="center",
                fontweight="bold", color=PAL[k], zorder=5,
                bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=PAL[k], lw=1.2, alpha=0.95))
# a new message: a point near cluster 7 (health), arrow to its centre
k0 = 7
span = p.max(0) - p.min(0)
new = c2[k0] + np.array([0.10, -0.12]) * span
ax.scatter(*new, s=520, marker="*", color="#17132b", zorder=6)
ax.annotate("", xy=c2[k0], xytext=new, arrowprops=dict(arrowstyle="->", lw=2.2, color="#17132b"), zorder=6)
ax.annotate("new message → nearest centre", new, xytext=(16, -30), textcoords="offset points", fontsize=15, color=INK, fontweight="bold", bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec="#17132b", lw=1))
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
fig.savefig(OUT / "cluster_map.png", dpi=200, bbox_inches="tight", pad_inches=0.2)
plt.close(fig)
print("cluster sizes", np.bincount(lab, minlength=8))

# 2. Khayyam heat map (test accuracy per subject), best boxed
kh = json.load(open("results/khayyam/khayyam_router.json"))
km = ["deepseek-v4-flash", "gpt-5.6-luna", "gemini-2.5-flash-lite", "deepseek-v4-pro"]
names = ["DeepSeek", "Luna", "Gemini", "DeepSeek Pro"]
cl = [c for c in kh["clusters"] if not c["name_en"].startswith("Mixed")]
acc = np.array([[c["test"][m] * 100 for m in km] for c in cl])
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor="#ffffff")
im = ax.imshow(acc, cmap="Purples", vmin=20, vmax=75, aspect="auto")
ax.set_xticks(range(4), names, fontsize=15, color=INK)
ax.set_yticks(range(len(cl)), [c["name_en"] for c in cl], fontsize=15, color=INK)
ax.tick_params(length=0); ax.xaxis.tick_top()
for s in ax.spines.values():
    s.set_visible(False)
for i in range(len(cl)):
    best = acc[i].max()
    for j in range(4):
        v = acc[i, j]
        ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=16, fontweight="bold",
                color="#ffffff" if v > 52 else INK)
        if v >= best - 0.5:
            ax.add_patch(plt.Rectangle((j - 0.47, i - 0.45), 0.94, 0.9, fill=False, ec="#e0336e", lw=3.5))
fig.savefig(OUT / "khayyam_heat.png", dpi=200, bbox_inches="tight", pad_inches=0.15)
plt.close(fig)


# 3. Formulas
def formula(tex, name, size=34):
    fig = plt.figure(figsize=(0.01, 0.01), facecolor="#ffffff")
    fig.text(0, 0, tex, fontsize=size, color=INK)
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight", pad_inches=0.12, facecolor="#ffffff")
    plt.close(fig)


formula(r"$\Psi_k(h)=\dfrac{1}{|V_k|}\sum_{x\in V_k}\ell(x,h)$", "f_psi.png")
formula(r"$h^{*}(x)=\arg\min_{h\in\mathcal{H}}\;\Psi_{k(x)}(h)+\lambda\,\hat{c}(h)$", "f_route.png")
formula(r"$k(x)=\arg\min_{k}\;\Vert\phi(x)-\mu_k\Vert$", "f_cluster.png", 30)
formula(r"$\mathrm{AUDC}=\dfrac{1}{c_{\max}-c_{\min}}\int_{c_{\min}}^{c_{\max}}\tilde{Q}(b)\,db$", "f_audc.png")
formula(r"$\mathrm{QNC}=\dfrac{\min\{\,b:\tilde{Q}(b)\geq Q(h^{\dagger})\,\}}{c(h^{\dagger})}$", "f_qnc.png")
print("ok")
