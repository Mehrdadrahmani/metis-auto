"""Bot clusters experiment. Usage: run.py embed [--device cpu] | run.py cluster

embed: redacted description + instructions, first MAX_CHARS characters; identical texts once.
cluster: K-means for K = 2..60 on unique texts, elbow by largest distance from the end-to-end line
(on inertia), plus silhouette and stability (ARI over seeds) as checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from metis.config import load_config
from metis.data.redact import redact
from metis.embed.embedder import Embedder

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/bot_clusters"
HERE = Path(__file__).resolve().parent
MAX_CHARS = 6000
KS = list(range(2, 61))
CHECK_KS = (5, 8, 10, 12, 15, 20, 25, 30, 40)


def elbow(ks: list[int], inertia: list[float]) -> int:
    x = (np.array(ks) - ks[0]) / (ks[-1] - ks[0])
    y = (np.array(inertia) - inertia[-1]) / (inertia[0] - inertia[-1])
    return ks[int(np.argmax((1 - x) - y))]


def bot_table() -> pd.DataFrame:
    b = pd.read_parquet(ROOT / "data/raw/metis/data/chat_bot.parquet",
                        columns=["bot_id", "description", "instructions"])  # fmt: skip
    def text(r) -> str:
        parts = [str(r[c]).strip() for c in ("description", "instructions") if isinstance(r[c], str)]
        return redact("\n".join(p for p in parts if p))[0][:MAX_CHARS]
    b["text"] = b.apply(text, axis=1)
    b["h"] = b["text"].map(lambda t: hashlib.sha256(t.encode()).hexdigest()[:16])
    return b[["bot_id", "text", "h"]]


def run_embed(device: str | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config("pipeline")
    s4 = cfg["s4"]
    cand = s4["candidates"][s4["choice"]]
    b = bot_table()
    b.to_parquet(OUT / "bots.parquet", index=False)
    u = b[b["text"].str.len() > 0].drop_duplicates("h")
    print(f"bots {len(b)}, empty {(b['text'].str.len() == 0).sum()}, unique texts {len(u)}", flush=True)
    emb = Embedder(cand["name"], cand["revision"], device=device or s4["device"],
                   path=str(ROOT / cand["path"]), task=s4["task"], prompt_name=s4["prompt_name"],
                   merge_adapter=s4["merge_adapter"], max_tokens=s4["max_tokens"],
                   batch_size=s4["batch_size"], max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip
    u = u.assign(n=u["text"].str.len()).sort_values("n")
    vecs = []
    for i in range(0, len(u), 100):
        vecs.append(emb.encode(u["text"].iloc[i : i + 100].tolist()))
        print(i + 100, flush=True)
    np.savez(OUT / "vectors.npz", h=u["h"].to_numpy(str), vecs=np.concatenate(vecs))


def run_cluster() -> None:
    cfg = load_config("pipeline")
    seed, n_init = cfg["seed"], cfg["router"]["kmeans_n_init"]
    with np.load(OUT / "vectors.npz") as z:
        h, x = z["h"], z["vecs"]
    fits = {}
    rows = []
    for k in KS:
        km = KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(x)
        fits[k] = km.labels_
        rows.append({"k": k, "inertia": float(km.inertia_),
                     "silhouette": float(silhouette_score(x, km.labels_, metric="cosine"))})  # fmt: skip
    best = elbow(KS, [r["inertia"] for r in rows])
    ari = {}
    for k in sorted({*CHECK_KS, best}):
        labels = [fits[k]] + [KMeans(n_clusters=k, n_init=n_init, random_state=seed + s).fit(x).labels_
                              for s in (1, 2)]  # fmt: skip
        ari[k] = float(np.mean([adjusted_rand_score(a, b) for a, b in combinations(labels, 2)]))
    np.savez(OUT / "fits.npz", h=h, **{f"k_{k}": v for k, v in fits.items()})
    res = {"unique_texts": len(x), "elbow_k": best, "by_k": rows, "ari": ari}
    (HERE / "results.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print("elbow", best, "ari", ari)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["embed", "cluster"])
    ap.add_argument("--device")
    a = ap.parse_args()
    run_embed(a.device) if a.step == "embed" else run_cluster()


if __name__ == "__main__":
    main()
