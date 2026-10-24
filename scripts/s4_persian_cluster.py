"""WP-03b steps 2-5: embed public Persian data and test K-means clusters against known labels.

Sets (from `data/external/*.parquet`, `scripts/ext_download.py`):
  T1 mix   labelled benchmarks, ≤ 4,000 per source; label = source (like EmbedLLM's benchmark mix)
  T2 mmlu  Global-MMLU fa alone; labels = subject category (6) and subject (57)
  T3 chat  Persian chat prompts (Arena, WildChat, lmsys); no labels
As the paper (§5.1): K-means (k-means++, 10 restarts) on a 60 % split, held-out 40 % assigned to the
nearest centroid (argmax φ·μ, spec S5); NMI / ARI / purity on the 40 %, cosine silhouette.
Numbers only on stdout and in results/; texts only go to a local HTML page for the owner.
Embeddings are cached in data/external/emb/ (resumable, chunks of 1,000).

Usage: uv run python scripts/s4_persian_cluster.py nano   (or small; --task text-matching)
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score

from metis.config import load_config
from metis.data.lang import lang_tag
from metis.embed.embedder import Embedder

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
SEED = load_config("pipeline")["seed"]
CHAT = ("arena", "wildchat", "lmsys_fa")
CAP = 4000
KS = (3, 4, 6, 8, 12, 16, 24, 32, 48, 64)
CHUNK = 1000


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def load_sets() -> dict[str, pd.DataFrame]:
    parts = [pd.read_parquet(p) for p in sorted(EXT.glob("*.parquet"))]
    df = pd.concat(parts, ignore_index=True)
    df["text"] = df["text"].fillna("").str.strip()
    df = df[df["text"].str.len() >= 2].drop_duplicates("text").reset_index(drop=True)
    lab = df[~df["source"].isin(CHAT)]
    t1 = lab.sample(frac=1.0, random_state=SEED).groupby("source").head(CAP).reset_index(drop=True)
    t2 = df[df["source"] == "global_mmlu"].reset_index(drop=True)
    t3 = df[df["source"].isin(CHAT)].reset_index(drop=True)
    return {"T1_mix": t1, "T2_mmlu": t2, "T3_chat": t3}


def embed_all(texts: list[str], emb: Embedder, cache: Path) -> np.ndarray:
    """Embed in chunks of CHUNK texts; each chunk file is keyed by the hash of its texts."""
    cache.mkdir(parents=True, exist_ok=True)
    out = []
    for i in range(0, len(texts), CHUNK):
        chunk = texts[i : i + CHUNK]
        key = hashlib.sha256("\x1e".join(chunk).encode()).hexdigest()[:16]
        f = cache / f"{i // CHUNK:04d}_{key}.npy"
        if not f.exists():
            t0 = time.perf_counter()
            np.save(f, emb.encode(chunk))
            log(
                f"  chunk {i // CHUNK + 1}/{-(-len(texts) // CHUNK)}: {time.perf_counter() - t0:.0f} s"
            )
        out.append(np.load(f))
    return np.concatenate(out)


def purity(y: np.ndarray, c: np.ndarray) -> float:
    return float(sum(pd.Series(y[c == k]).value_counts().iloc[0] for k in np.unique(c)) / len(y))


def assign(x: np.ndarray, mu: np.ndarray) -> np.ndarray:
    return np.argmax(x @ mu.T, axis=1)  # spec S5: k(x) = argmax φ(x)·μ_k


def analyse(name: str, df: pd.DataFrame, v: np.ndarray, labels: list[str], ks) -> dict:
    rng = np.random.default_rng(SEED)
    fit = np.zeros(len(df), bool)
    fit[rng.permutation(len(df))[: int(0.6 * len(df))]] = True
    held = ~fit
    sil_idx = rng.choice(np.flatnonzero(held), size=min(5000, held.sum()), replace=False)
    res: dict = {"n": len(df), "n_fit": int(fit.sum()), "n_held": int(held.sum()),
                 "label_counts": {lb: int(df[lb].nunique()) for lb in labels}, "K": {}}  # fmt: skip
    for k in ks:
        if k >= fit.sum():
            continue
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(v[fit])
        c = assign(v, km.cluster_centers_)
        r = {"silhouette_cos": float(silhouette_score(v[sil_idx], c[sil_idx], metric="cosine"))
             if len(np.unique(c[sil_idx])) > 1 else None,
             "sizes_held": np.bincount(c[held], minlength=k).tolist()}  # fmt: skip
        for lb in labels:
            y = df[lb].astype(str).to_numpy()
            r[lb] = {"nmi": float(normalized_mutual_info_score(y[held], c[held])),
                     "ari": float(adjusted_rand_score(y[held], c[held])),
                     "purity": purity(y[held], c[held])}  # fmt: skip
        res["K"][str(k)] = r
        res["K"][str(k)]["_labels"] = c  # dropped before saving; used for tables and HTML
        log(f"  {name} K={k}: " + ", ".join(f"{lb} NMI {r[lb]['nmi']:.3f}" for lb in labels)
            + (f", sil {r['silhouette_cos']:.3f}" if r["silhouette_cos"] is not None else ""))  # fmt: skip
    return res


def crosstab(df: pd.DataFrame, c: np.ndarray, col: str) -> list[dict]:
    rows = []
    for k in np.unique(c):
        g = df[c == k]
        rows.append({"cluster": int(k), "n": len(g), col: g[col].value_counts().head(4).to_dict(),
                     "mean_chars": round(float(g["text"].str.len().mean()), 1),
                     "lang": g["lang"].value_counts().to_dict()})  # fmt: skip
    return rows


def write_html(
    path: Path, title: str, sections: list[tuple[str, pd.DataFrame, np.ndarray, str]]
) -> None:
    rng = np.random.default_rng(SEED)
    parts = [
        f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title>",
        (
            "<style>body{font-family:sans-serif;max-width:1000px;margin:2em auto;padding:0 16px}"
            "li{margin:.6em 0;white-space:pre-wrap;border-bottom:1px solid #ddd;padding-bottom:.4em}"
            "h2{background:#dae8fc;padding:.3em}</style>"
        ),
        f"<h1>{html.escape(title)}</h1><p>8 random items per cluster; [label] = known source/topic.</p>",
    ]
    for head, df, c, col in sections:
        parts.append(f"<h1>{html.escape(head)}</h1>")
        for k in np.unique(c):
            idx = np.flatnonzero(c == k)
            top = df.iloc[idx][col].value_counts().head(3)
            mix = ", ".join(f"{html.escape(str(a))} {b}" for a, b in top.items())
            parts.append(f"<h2>Cluster {k} (n = {len(idx)}; {mix})</h2><ol>")
            for i in rng.choice(idx, size=min(8, len(idx)), replace=False):
                parts.append(f"<li dir='auto'>[{html.escape(str(df.iat[i, df.columns.get_loc(col)]))}] "
                             f"{html.escape(df.iat[i, df.columns.get_loc('text')][:800])}</li>")  # fmt: skip
            parts.append("</ol>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model", choices=["small", "nano"])
    ap.add_argument("--task", default=None, help="adapter (default: configs/pipeline.yaml s4.task)")
    ap.add_argument(
        "--max-tokens", type=int, default=2048, help="external test only; truncated count reported"
    )
    a = ap.parse_args()
    s4 = load_config("pipeline")["s4"]
    cand = s4["candidates"][a.model]
    task = a.task or s4["task"]
    emb = Embedder(cand["name"], cand["revision"], device=s4["device"], path=str(ROOT / cand["path"]),
                   task=task, prompt_name=s4["prompt_name"], merge_adapter=s4["merge_adapter"],
                   max_tokens=a.max_tokens, batch_size=s4["batch_size"],
                   max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip
    sets = load_sets()
    allt = pd.concat(sets.values()).drop_duplicates("text")["text"].tolist()
    ntok = np.array(emb.count_tokens(allt))
    log(f"{a.model}/{task}: {len(allt)} unique texts, tokens p50 {np.median(ntok):.0f}, "
        f"max {ntok.max()}, over {a.max_tokens}: {(ntok > a.max_tokens).sum()}")  # fmt: skip
    vecs = embed_all(allt, emb, EXT / "emb" / f"{a.model}_{task}")
    pos = {t: i for i, t in enumerate(allt)}

    out: dict = {"model": cand["name"], "revision": cand["revision"], "task": task,
                 "embedder_id": emb.embedder_id, "seed": SEED, "max_tokens": a.max_tokens,
                 "n_unique": len(allt), "tokens": {"p50": float(np.median(ntok)), "p90": float(np.percentile(ntok, 90)),
                 "max": int(ntok.max()), "n_over_max": int((ntok > a.max_tokens).sum())}, "sets": {}}  # fmt: skip
    html_sections = []
    for name, df in sets.items():
        if df.empty:
            continue
        df = df.assign(lang=df["text"].map(lang_tag)).reset_index(drop=True)
        v = vecs[[pos[t] for t in df["text"]]]
        labels = {
            "T1_mix": ["source", "label"],
            "T2_mmlu": ["label", "fine"],
            "T3_chat": ["source"],
        }[name]
        extra = {"T1_mix": [df["source"].nunique()], "T2_mmlu": [6, 57], "T3_chat": []}[name]
        ks = sorted(set(KS) | set(extra))
        r = analyse(name, df, v, labels, ks)
        r["source_counts"] = df["source"].value_counts().to_dict()
        show_k = {"T1_mix": df["source"].nunique(), "T2_mmlu": 6, "T3_chat": 8}[name]
        c = r["K"][str(show_k)]["_labels"]
        r["table_K"] = show_k
        r["table"] = crosstab(df, c, "source" if name != "T2_mmlu" else "label")
        if name != "T2_mmlu":
            html_sections.append(
                (f"{name}, K = {show_k}", df, c, "source" if name == "T3_chat" else "label")
            )
        for kk in r["K"].values():
            kk.pop("_labels")
        out["sets"][name] = r
    tag = a.model if task == s4["task"] else f"{a.model}_{task}"
    (ROOT / "results" / f"persian_clustering_{tag}.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False)
    )
    write_html(
        ROOT / "runs" / "s4" / f"persian_clusters_{tag}.html",
        f"Persian clusters: {tag}",
        html_sections,
    )
    log(f"done: results/persian_clustering_{tag}.json, runs/s4/persian_clusters_{tag}.html")


if __name__ == "__main__":
    main()
