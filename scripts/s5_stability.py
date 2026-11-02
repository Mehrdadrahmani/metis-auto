"""K-means stability and val-train gap per K, no labels needed (WP-08, warning sign only; never
chooses K, D-064).

Usage: uv run python scripts/s5_stability.py   (resumable; run after s5_cluster_view.py)

Refits train with two other seeds and compares labels with the saved fit by Adjusted Rand Index
(1 = same clusters). Gap = total variation between the val and train cluster shares (0 = same).
Writes results/wp08_full_data/cluster_stability.json (numbers only).
"""

from __future__ import annotations

import json
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

from metis.config import load_config

ROOT = Path(__file__).resolve().parents[1]
KS = range(3, 21)
EXTRA_SEEDS = (1, 2)


def gap(n_val: np.ndarray, n_train: np.ndarray) -> float:
    return float(0.5 * np.abs(n_val / n_val.sum() - n_train / n_train.sum()).sum())


def main() -> None:
    t0 = time.perf_counter()
    cfg = load_config("pipeline")
    seed, n_init = cfg["seed"], cfg["router"]["kmeans_n_init"]
    out = ROOT / "runs/s4/full" / cfg["s4"]["choice"]
    ids, vecs = [], []
    for p in sorted(out.glob("part-*.npz")):
        with np.load(p) as z:
            ids.append(z["ids"])
            vecs.append(z["vecs"])
    ids, vecs = np.concatenate(ids), np.concatenate(vecs)
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet", columns=["prompt_id", "split"])
    train = set(split.loc[split["split"] == "train", "prompt_id"])
    x = vecs[np.array([i in train for i in ids])]
    by_k = json.loads((ROOT / "results/wp08_full_data/clusters_by_k.json").read_text("utf-8"))
    res = ROOT / "results/wp08_full_data/cluster_stability.json"
    done = json.loads(res.read_text("utf-8")) if res.exists() else {}
    for k in KS:
        name = f"k_{k:02d}"
        if name in done:
            continue
        with np.load(ROOT / f"runs/s5/view/{name}.npz") as z:
            fits = [z["labels"]]
        assert len(fits[0]) == len(x), "saved fit does not match train"
        for extra in EXTRA_SEEDS:
            fits.append(KMeans(n_clusters=k, n_init=n_init, random_state=seed + extra).fit(x).labels_)
        aris = [float(adjusted_rand_score(a, b)) for a, b in combinations(fits, 2)]
        rows = by_k[name]["clusters"]
        n_val = np.array([r["n_val"] for r in rows], float)
        n_train = np.array([r["n"] for r in rows], float)
        done[name] = {"k": k, "ari_mean": float(np.mean(aris)), "ari_min": min(aris),
                      "gap_val_train": gap(n_val, n_train), "min_val": int(n_val.min()),
                      "empty_val_clusters": int((n_val == 0).sum())}  # fmt: skip
        res.write_text(json.dumps(done, indent=1) + "\n", encoding="utf-8")
        print(name, done[name], f"{(time.perf_counter() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
