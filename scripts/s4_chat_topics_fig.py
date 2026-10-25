"""WP-03b: heatmap of nearest-topic shares per cluster (from results/wp03b_persian/persian_cluster_topics.json)."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

root = str(__import__("pathlib").Path(__file__).resolve().parents[1]) + "/"
r = json.loads(
    __import__("pathlib")
    .Path(root + "results/wp03b_persian/persian_cluster_topics.json")
    .read_text()
)
topics = list(r["topics"])
names = {
    "khayyam": [
        "0 humanities mix",
        "1 math",
        "2 Persian literature",
        "3 religion & philosophy",
        "4 chemistry",
        "5 history & society",
        "6 biology & geography",
        "7 physics",
    ],
    "chat": [
        "0 general / poetry",
        "1 general, writing, personal",
        "2 short general questions",
        "3 health",
        "4 science",
        "5 business & money",
        "6 history & society",
        "7 coding & tech",
    ],
}
fig, axes = plt.subplots(1, 2, figsize=(16, 4.8))
for ax, s in zip(axes, ("khayyam", "chat")):
    m = np.zeros((8, len(topics)))
    for c in r["sets"][s]["clusters"]:
        # full topic shares are not stored beyond top 4; show the top 4 (rest left blank)
        for t, v in c["topics"].items():
            m[c["cluster"], topics.index(t)] = v
    ax.imshow(m, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(8):
        for j in range(len(topics)):
            if m[i, j] >= 0.05:
                ax.text(
                    j,
                    i,
                    f"{m[i, j]:.0%}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if m[i, j] > 0.6 else "black",
                )
    ns = {c["cluster"]: c["n"] for c in r["sets"][s]["clusters"]}
    ax.set_yticks(range(8), [f"{names[s][i]} (n={ns[i]})" for i in range(8)], fontsize=8)
    ax.set_xticks(
        range(len(topics)),
        [t.replace("_", " ") for t in topics],
        rotation=40,
        ha="right",
        fontsize=8,
    )
    ax.set_title(
        f"{'Khayyam (check: subjects known)' if s == 'khayyam' else 'chat (no labels)'}: nearest topic per prompt, by cluster",
        fontsize=10,
    )
fig.tight_layout()
fig.savefig(root + "report/persian_clustering/figures/cluster_topics.png", dpi=130)
