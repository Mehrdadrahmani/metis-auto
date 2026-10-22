"""S4 embedder benchmark (WP-03 step 5). Numbers only; prompt texts go only to a local HTML file.

Per model: load time, RAM, single-message latency (synthetic Persian, 30/200/512 tokens + the
longest sample message) on CPU and MPS, batch-64 throughput, determinism, Persian paraphrase
sanity (AUC), token counts vs the model limit, K-means K = 4 / 6 on the sample (sizes, category /
language mix, mean length, silhouette), Qdrant exact search == numpy on the real vectors.

Usage: uv run python scripts/s4_embed_bench.py small   (or nano)
Writes results/embedder_benchmark_<model>.json, runs/s4/emb_<model>.npy,
runs/s4/cluster_samples_<model>.html (git-ignored, for the owner).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import torch
import yaml
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score, silhouette_score

from metis.config import load_config
from metis.data.redact import redact
from metis.embed.embedder import Embedder
from metis.embed.store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "small": ("jinaai/jina-embeddings-v5-text-small", "dd76d535f5447ca3897a9c893fb1e612ead98192"),
    "nano": ("jinaai/jina-embeddings-v5-text-nano", "8a7f00aac812071b69403df470f1038ec85f8925"),
}
LENGTHS = (30, 200, 512)
N_CALLS = 200
SEED = load_config("pipeline")["seed"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / 1e6


def synth_text(emb: Embedder, n_tokens: int, pairs: dict) -> str:
    """Synthetic Persian text of ~n_tokens tokens (special tokens included)."""
    base = " ".join(a + " " + b for a, b in pairs["paraphrase"] + pairs["close"])
    tok = emb.model.tokenizer
    ids = tok(base * 20, add_special_tokens=False)["input_ids"]
    special = emb.count_tokens([""])[0]
    return tok.decode(ids[: max(1, n_tokens - special)])


def latency(emb: Embedder, text: str, n: int) -> dict:
    for _ in range(10):
        emb.encode([text])
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        emb.encode([text])
        ts.append((time.perf_counter() - t0) * 1000)
    a = np.array(ts)
    return {"n": n, "p50_ms": float(np.percentile(a, 50)), "p95_ms": float(np.percentile(a, 95))}


def sample_table() -> pd.DataFrame:
    df = pd.read_parquet(
        ROOT / "runs/s1/prompts.parquet",
        columns=["prompt_id", "category", "lang", "text_chars", "embed_input",
                 "eligible_labeled", "eligible_train"],
    )  # fmt: skip
    return df[df["eligible_labeled"] | df["eligible_train"]].reset_index(drop=True)


def persian_check(emb: Embedder, pairs: dict) -> dict:
    out = {}
    for g in ("paraphrase", "close"):
        a = emb.encode([p[0] for p in pairs[g]])
        b = emb.encode([p[1] for p in pairs[g]])
        out[g] = (a * b).sum(1)
    y = np.r_[np.ones(len(out["paraphrase"])), np.zeros(len(out["close"]))]
    s = np.r_[out["paraphrase"], out["close"]]
    return {
        "n_pairs": [len(out["paraphrase"]), len(out["close"])],
        "mean_cos_paraphrase": float(out["paraphrase"].mean()),
        "mean_cos_close": float(out["close"].mean()),
        "gap": float(out["paraphrase"].mean() - out["close"].mean()),
        "auc": float(roc_auc_score(y, s)),
    }


def clusters(vecs: np.ndarray, df: pd.DataFrame, cat_code: dict, ks=(4, 6)) -> dict:
    res = {}
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(vecs)
        lab = km.labels_
        d = df.assign(cluster=lab, cat=df["category"].map(cat_code))
        per = []
        for c in range(k):
            g = d[d["cluster"] == c]
            per.append({
                "cluster": c, "n": len(g),
                "categories": g["cat"].value_counts().sort_index().to_dict(),
                "lang": g["lang"].value_counts().to_dict(),
                "mean_chars": float(g["text_chars"].mean()),
            })  # fmt: skip
        res[str(k)] = {
            "silhouette_cos": float(silhouette_score(vecs, lab, metric="cosine")),
            "inertia": float(km.inertia_),
            "clusters": per,
            "labels": lab.tolist(),
        }
    return res


def write_html(path: Path, model: str, df: pd.DataFrame, cl: dict, cat_code: dict) -> None:
    rng = np.random.default_rng(SEED)
    parts = [
        "<!doctype html><meta charset='utf-8'><title>Cluster samples</title>",
        (
            "<style>body{font-family:sans-serif;max-width:1000px;margin:2em auto;padding:0 16px}"
            "li{margin:.6em 0;white-space:pre-wrap;border-bottom:1px solid #ddd;padding-bottom:.4em}"
            "h2{background:#dae8fc;padding:.3em}</style>"
        ),
        f"<h1>Cluster samples: {html.escape(model)} (8 random redacted prompts per cluster)</h1>",
        "<p>For each K: do the clusters make sense? (yes / partly / no). Category codes: "
        + ", ".join(f"{v} = {html.escape(str(k))}" for k, v in cat_code.items())
        + "</p>",
    ]
    for k, r in cl.items():
        parts.append(f"<h1>K = {k} (silhouette {r['silhouette_cos']:.3f})</h1>")
        lab = np.array(r["labels"])
        for c in range(int(k)):
            idx = np.flatnonzero(lab == c)
            pick = rng.choice(idx, size=min(8, len(idx)), replace=False)
            parts.append(f"<h2>Cluster {c} (n = {len(idx)})</h2><ol>")
            for i in pick:
                txt, _ = redact(df.at[i, "embed_input"])
                parts.append(f"<li dir='auto'>[{cat_code[df.at[i, 'category']]}] "
                             f"{html.escape(txt[:1500])}</li>")  # fmt: skip
            parts.append("</ol>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model", choices=list(MODELS))
    ap.add_argument("--devices", default="cpu,mps")
    a = ap.parse_args()
    name, rev = MODELS[a.model]
    pairs = yaml.safe_load((ROOT / "scripts/data/persian_pairs.yaml").read_text(encoding="utf-8"))
    df = sample_table()
    texts = df["embed_input"].tolist()
    out: dict = {"model": name, "revision": rev, "torch_threads": torch.get_num_threads(),
                 "torch": torch.__version__, "n_sample": len(df), "devices": {}}  # fmt: skip

    vecs_by_dev = {}
    for dev in a.devices.split(","):
        if dev == "mps" and not torch.backends.mps.is_available():
            out["devices"][dev] = {"available": False}
            continue
        r0 = rss_mb()
        t0 = time.perf_counter()
        local = (
            ROOT
            / "models"
            / f"{name.split('/')[-1].replace('jina-embeddings-', 'jina_').replace('-', '_')}_{rev[:12]}"
        )
        emb = Embedder(name, rev, device=dev, path=str(local) if local.exists() else None)
        r: dict = {"load_s": time.perf_counter() - t0, "rss_mb_after_load": rss_mb(),
                   "rss_mb_delta": rss_mb() - r0, "embedder_id": emb.embedder_id}  # fmt: skip
        log(f"{dev}: loaded in {r['load_s']:.0f} s")
        r["latency"] = {}
        for n in LENGTHS:
            r["latency"][str(n)] = latency(emb, synth_text(emb, n, pairs), N_CALLS)
            log(f"{dev}: latency {n} tok p95 {r['latency'][str(n)]['p95_ms']:.0f} ms")
        ntok = np.array(emb.count_tokens(texts))
        longest = texts[int(ntok.argmax())]
        r["latency"]["longest_sample"] = {**latency(emb, longest, 20), "tokens": int(ntok.max())}
        log(f"{dev}: longest sample done")
        synth = [synth_text(emb, 200, pairs)] * 256
        budget, emb.max_batch_tokens = emb.max_batch_tokens, None  # true batch 64
        t0 = time.perf_counter()
        emb.encode(synth, batch_size=64)
        emb.max_batch_tokens = budget
        r["batch64_200tok_prompts_per_s"] = len(synth) / (time.perf_counter() - t0)
        t0 = time.perf_counter()
        v = emb.encode(texts, batch_size=64)  # token-budget batches
        r["sample_prompts_per_s"] = len(texts) / (time.perf_counter() - t0)
        r["max_batch_tokens"] = emb.max_batch_tokens
        r["rss_mb_peak_so_far"] = rss_mb()
        log(f"{dev}: sample embedded")
        d1, d2 = emb.encode(texts[:16]), emb.encode(texts[:16])
        r["determinism_max_abs_diff"] = float(np.abs(d1 - d2).max())
        r["batching_max_abs_diff"] = float(np.abs(v[:16] - d1).max())  # other batch mates
        r["persian"] = persian_check(emb, pairs)
        if dev == "mps":
            r["mps_alloc_mb"] = torch.mps.current_allocated_memory() / 1e6
        r["tokens"] = {"mean": float(ntok.mean()), "p50": float(np.median(ntok)),
                       "p90": float(np.percentile(ntok, 90)), "max": int(ntok.max()),
                       "n_over_512": int((ntok > 512).sum()),
                       "n_over_limit": int((ntok > emb.max_tokens).sum())}  # fmt: skip
        out["devices"][dev] = r
        vecs_by_dev[dev] = v
        del emb
        if dev == "mps":
            torch.mps.empty_cache()

    if {"cpu", "mps"} <= vecs_by_dev.keys():
        d = vecs_by_dev["cpu"] - vecs_by_dev["mps"]
        out["cpu_vs_mps"] = {"max_abs_diff": float(np.abs(d).max()),
                             "min_cos": float((vecs_by_dev["cpu"] * vecs_by_dev["mps"]).sum(1).min())}  # fmt: skip

    vecs = vecs_by_dev.get("cpu", next(iter(vecs_by_dev.values())))
    (ROOT / "runs/s4").mkdir(parents=True, exist_ok=True)
    np.save(ROOT / f"runs/s4/emb_{a.model}.npy", vecs)
    cats = sorted(df["category"].unique())
    cat_code = {c: f"c{i + 1}" for i, c in enumerate(cats)}
    cl = clusters(vecs, df, cat_code)
    write_html(ROOT / f"runs/s4/cluster_samples_{a.model}.html", a.model, df, cl, cat_code)
    out["clusters"] = {k: {kk: vv for kk, vv in v.items() if kk != "labels"} for k, v in cl.items()}

    # Qdrant exact search must equal numpy brute force on the real vectors
    st = VectorStore(f"bench-{a.model}", vecs.shape[1], path=None)
    st.upsert(df["prompt_id"].tolist(), vecs, [{"lang": x} for x in df["lang"]])
    ok = 0
    for q in range(20):
        want = df["prompt_id"].to_numpy()[np.argsort(-(vecs @ vecs[q]), kind="stable")[:10]]
        ok += [p for p, _ in st.search(vecs[q], 10, exact=True)] == list(want)
    out["qdrant_equals_numpy"] = f"{ok}/20"
    st.close()

    path = ROOT / f"results/embedder_benchmark_{a.model}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(path)


if __name__ == "__main__":
    main()
