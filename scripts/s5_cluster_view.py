"""K-means on train for K = 3..20 (DEV-10), one local HTML page per K.

Usage: uv run python scripts/s5_cluster_view.py   (resumable: a finished K is skipped)

Fits on train minus near-duplicates; val is only assigned, to show prompts per cluster. Test is
never used. Writes runs/cluster_view/
(index.html, k_XX.html; git-ignored, redacted train prompts), runs/s5/view/k_XX.npz and
results/wp08_full_data/clusters_by_k.json (numbers only).
"""

from __future__ import annotations

import html
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from metis.config import load_config
from metis.data.redact import redact

ROOT = Path(__file__).resolve().parents[1]
KS = range(3, 21)
N_SHOW = 12
SILHOUETTE_SAMPLE = 10_000
STYLE = (
    "<style>body{font-family:sans-serif;max-width:1000px;margin:2em auto;padding:0 16px}"
    "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px 8px;"
    "text-align:right}h2{background:#dae8fc;padding:.3em}li{margin:.5em 0;white-space:pre-wrap;"
    "border-bottom:1px solid #ddd;padding-bottom:.3em}.warn{background:#fff2cc;padding:.5em}</style>"
)


def load_vectors(out: Path) -> tuple[np.ndarray, np.ndarray]:
    ids, vecs = [], []
    for p in sorted(out.glob("part-*.npz")):
        with np.load(p) as z:
            ids.append(z["ids"])
            vecs.append(z["vecs"])
    return np.concatenate(ids), np.concatenate(vecs)


def page(
    k: int, df: pd.DataFrame, lab: np.ndarray, n_val: np.ndarray, sil: float, seed: int
) -> tuple[str, list]:
    rng = np.random.default_rng(seed + k)
    d = df.assign(cluster=lab)
    rows, body = [], []
    for c, g in d.groupby("cluster"):
        top = g["bot_id"].value_counts(normalize=True).iloc[0]
        row = {"cluster": int(c), "n": len(g), "share": len(g) / len(d), "n_val": int(n_val[c]),
               "median_chars": float(g["text_chars"].median()), "fa": float(g["lang"].eq("fa").mean()),
               "rag": float(g["uses_rag"].mean()), "top_bot_share": float(top)}  # fmt: skip
        rows.append(row)
        body.append(f"<h2>Cluster {c} (n = {len(g):,}, val = {row['n_val']})</h2><ol>")
        for i in rng.choice(g.index.to_numpy(), size=min(N_SHOW, len(g)), replace=False):
            txt, _ = redact(df.at[i, "embed_input"])
            body.append(f"<li dir='auto'>{html.escape(txt[:500])}</li>")
        body.append("</ol>")
    cells = "".join(
        f"<tr><td>{r['cluster']}</td><td>{r['n']:,}</td><td>{r['share']:.1%}</td><td>{r['n_val']}</td>"
        f"<td>{r['median_chars']:.0f}</td><td>{r['fa']:.0%}</td><td>{r['rag']:.0%}</td>"
        f"<td>{r['top_bot_share']:.0%}</td></tr>"
        for r in rows
    )
    warn = "" if k <= 8 else (
        "<p class='warn'>Above the paper's rule (K ≤ 8 for 400 val prompts); tested by owner "
        "decision DEV-10. Check the val column: scores rest on few prompts per cluster.</p>"
    )
    head = (
        f"<!doctype html><meta charset='utf-8'><title>K = {k}</title>{STYLE}"
        f"<p><a href='index.html'>All K</a></p><h1>K = {k} (silhouette {sil:.3f})</h1>{warn}"
        "<table><tr><th>cluster</th><th>train</th><th>share</th><th>val</th><th>median chars</th>"
        f"<th>Persian</th><th>RAG</th><th>top bot</th></tr>{cells}</table>"
    )
    return head + "\n".join(body), rows


def main() -> None:
    t0 = time.perf_counter()
    cfg = load_config("pipeline")
    seed, n_init = cfg["seed"], cfg["router"]["kmeans_n_init"]
    out = ROOT / "runs/s4/full" / cfg["s4"]["choice"]
    ids, vecs = load_vectors(out)
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet", columns=["prompt_id", "split"])
    dups = set(pd.read_parquet(out / "near_dups.parquet")["prompt_id"])
    train_ids = set(split.loc[split["split"] == "train", "prompt_id"]) - dups
    val_ids = set(split.loc[split["split"] == "val", "prompt_id"])
    tr = np.array([i in train_ids for i in ids])
    va = np.array([i in val_ids for i in ids])
    assert va.sum() == len(val_ids), "val vectors missing"
    x, xv = vecs[tr], vecs[va]
    cols = ["prompt_id", "bot_id", "lang", "uses_rag", "text_chars", "embed_input"]
    df = pd.read_parquet(ROOT / "runs/s1/prompts.parquet", columns=cols).set_index("prompt_id")
    df = df.loc[ids[tr]].reset_index()

    view, fits = ROOT / "runs/cluster_view", ROOT / "runs/s5/view"
    view.mkdir(parents=True, exist_ok=True)
    fits.mkdir(parents=True, exist_ok=True)
    res = ROOT / "results/wp08_full_data/clusters_by_k.json"
    done = json.loads(res.read_text(encoding="utf-8")) if res.exists() else {}
    for k in KS:
        name = f"k_{k:02d}"
        if name in done and (view / f"{name}.html").exists():
            continue
        km = KMeans(n_clusters=k, n_init=n_init, random_state=seed).fit(x)
        lab = km.labels_
        val_lab = km.predict(xv)  # same nearest-centroid rule as the fit
        sil = float(silhouette_score(x, lab, metric="cosine", sample_size=SILHOUETTE_SAMPLE,
                                     random_state=seed))  # fmt: skip
        text, rows = page(k, df, lab, np.bincount(val_lab, minlength=k), sil, seed)
        (view / f"{name}.html").write_text(text, encoding="utf-8")
        np.savez(fits / f"{name}.npz", centers=km.cluster_centers_, labels=lab)
        done[name] = {"k": k, "silhouette_cos": sil, "inertia": float(km.inertia_),
                      "n_train": len(x), "n_val": len(xv), "clusters": rows}  # fmt: skip
        res.write_text(json.dumps(done, indent=1) + "\n", encoding="utf-8")
        print(f"K {k}: silhouette {sil:.3f}  {(time.perf_counter() - t0) / 60:.1f} min", flush=True)

    links = "".join(
        f"<tr><td><a href='{n}.html'>K = {r['k']}</a></td><td>{r['silhouette_cos']:.3f}</td>"
        f"<td>{min(c['n_val'] for c in r['clusters'])}</td></tr>"
        for n, r in sorted(done.items())
    )
    (view / "index.html").write_text(
        f"<!doctype html><meta charset='utf-8'><title>Clusters by K</title>{STYLE}"
        f"<h1>Clusters by K</h1><p>Train prompts fitted: {len(x):,}. Paper rule: K ≤ 8; tested up to 20 (DEV-10).</p>"
        f"<table><tr><th>K</th><th>silhouette</th><th>smallest val count</th></tr>{links}</table>",
        encoding="utf-8",
    )
    print(f"wrote {view}/index.html")


if __name__ == "__main__":
    main()
