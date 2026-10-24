"""WP-03b: the UniRoute paper's embedding + K-means procedure on public Persian data (no LLM calls).

Paper (§5.1, §6, App. G.1-G.3), with Jina v5 instead of Gecko:
  frozen embedder φ → random split train / val (N_val = 400) / test, repeated with recorded seeds →
  K-means (k-means++, 10 restarts) on the *train* part only → val and test assigned to the nearest
  centroid, k(x) = argmax φ(x)·μ_k (spec S5) → K grid 3 … N_val/50 (= 3..8), plus larger K for reference.
The paper picks K by routing area, which needs per-model correctness labels; we have none ($0), so we
measure (a) agreement of test clusters with known labels (NMI / ARI / purity), (b) cosine silhouette,
(c) spec check |C_k| ≥ 50 val prompts, (d) Khayyam only: human error rate per question (1 − share of
examinees choosing the key) used as one "model": Ψ_k = mean error of the val prompts in cluster k
(Eq. 12) and the test gap E|e(x) − Ψ_k(x)| that bounds the cluster-routing loss (Prop. 2, Remark C.1).

Sets: mix (EmbedLLM-like benchmark mix, ≤ 4,000 per source), khayyam (38 categories, 95 courses),
mmlu (Global-MMLU fa), one_topic (Khayyam's largest category; Headlines-like), chat (Persian chat
first user messages; no labels). Numbers only on stdout and in results/; texts only go to a local
HTML page for the owner. Embeddings: data/external/emb/<model>_<task>/store/ (keyed by text hash).

Usage: uv run python scripts/s4_persian_cluster.py nano [--task text-matching] [--embed-only]
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
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score

from metis.config import load_config
from metis.data.lang import lang_tag
from metis.embed.embedder import Embedder

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
KHAYYAM_RAW = EXT / "raw" / "raia-center__khayyam-challenge" / "default" / "train" / "0000.parquet"
SEED = load_config("pipeline")["seed"]
CHAT = ("arena", "wildchat", "lmsys_fa")
CAP = 4000
N_VAL, N_MIN = 400, 50  # paper / spec: validation 400, K ≤ N_val / 50
K_PAPER = tuple(range(3, N_VAL // N_MIN + 1))
K_EXTRA = (12, 16, 24, 32, 48, 64)
REPEATS, REPEATS_EXTRA = 10, 3
CHUNK = 1000


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def text_key(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:24]


def load_all() -> pd.DataFrame:
    parts = [pd.read_parquet(p) for p in sorted(EXT.glob("*.parquet"))]
    df = pd.concat(parts, ignore_index=True)
    df["text"] = df["text"].fillna("").str.strip()
    return df[df["text"].str.len() >= 2].drop_duplicates("text").reset_index(drop=True)


def khayyam_difficulty() -> pd.DataFrame:
    """Human error per question: 1 − share choosing the key (blank counts as wrong); numbers only."""
    d = pd.read_parquet(KHAYYAM_RAW, columns=["ID", "Key", "P0", "P1", "P2", "P3", "P4", "Level"])
    p = d[["P1", "P2", "P3", "P4"]].to_numpy()
    k = d["Key"].fillna(0).astype(int).to_numpy()
    ok = d["P0"].notna().to_numpy() & (k >= 1) & (k <= 4)
    err = np.full(len(d), np.nan)
    err[ok] = 1 - p[ok, k[ok] - 1] / 100
    return pd.DataFrame({"ext_id": d["ID"].astype(str), "err": err, "level": d["Level"]})


def build_sets(df: pd.DataFrame) -> dict[str, tuple[pd.DataFrame, list[str]]]:
    lab = df[~df["source"].isin(CHAT)]
    mix = lab.sample(frac=1.0, random_state=SEED).groupby("source").head(CAP).reset_index(drop=True)
    kh = df[df["source"] == "khayyam"].merge(khayyam_difficulty(), on="ext_id", how="left")
    top = kh["label"].value_counts().index[0]
    return {
        "mix": (mix, ["source", "label"]),
        "khayyam": (kh.reset_index(drop=True), ["label", "fine", "level"]),
        "mmlu": (df[df["source"] == "global_mmlu"].reset_index(drop=True), ["label", "fine"]),
        "one_topic": (kh[kh["label"] == top].reset_index(drop=True), ["fine", "level"]),
        "chat": (df[df["source"].isin(CHAT)].reset_index(drop=True), ["source"]),
    }


class Store:
    """Embedding store keyed by text hash; parts of ≤ CHUNK vectors (resumable, safe to kill)."""

    def __init__(self, root: Path) -> None:
        self.dir = root / "store"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vec: dict[str, np.ndarray] = {}
        for f in sorted(self.dir.glob("part_*.npz")):
            z = np.load(f)
            self.vec.update(zip(z["keys"].tolist(), z["vecs"]))

    def add(self, keys: list[str], vecs: np.ndarray) -> None:
        n = len(list(self.dir.glob("part_*.npz")))
        np.savez(self.dir / f"part_{n:05d}.npz", keys=np.array(keys), vecs=vecs)
        self.vec.update(zip(keys, vecs))

    def import_legacy(self, root: Path, old_texts: list[str]) -> int:
        """Old cache: chunk i = old_texts[i*CHUNK:(i+1)*CHUNK], file name carries the chunk hash."""
        got = 0
        for i in range(0, len(old_texts), CHUNK):
            chunk = old_texts[i : i + CHUNK]
            key = hashlib.sha256("\x1e".join(chunk).encode()).hexdigest()[:16]
            f = root / f"{i // CHUNK:04d}_{key}.npy"
            keys = [text_key(t) for t in chunk]
            if f.exists() and any(k not in self.vec for k in keys):
                v = np.load(f)
                if len(v) == len(chunk):
                    self.add(keys, v)
                    got += len(chunk)
        return got

    def embed(self, texts: list[str], emb: Embedder) -> None:
        todo = list(dict.fromkeys(t for t in texts if text_key(t) not in self.vec))
        n = -(-len(todo) // CHUNK)
        log(f"  {len(texts) - len(todo)} cached, {len(todo)} to embed ({n} chunks)")
        for j, i in enumerate(range(0, len(todo), CHUNK)):
            chunk = todo[i : i + CHUNK]
            t0 = time.perf_counter()
            self.add([text_key(t) for t in chunk], emb.encode(chunk))
            log(f"  chunk {j + 1}/{n}: {time.perf_counter() - t0:.0f} s")

    def get(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.vec[text_key(t)] for t in texts])


def legacy_texts() -> list[str]:
    """The text order of the first nano/small runs (before Khayyam, Arena and WildChat existed)."""
    files = [
        p for p in sorted(EXT.glob("*.parquet")) if p.stem not in ("khayyam", "arena", "wildchat")
    ]
    old = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
    old["text"] = old["text"].fillna("").str.strip()
    old = old[old["text"].str.len() >= 2].drop_duplicates("text").reset_index(drop=True)
    lab = old[~old["source"].isin(CHAT)]
    t1 = lab.sample(frac=1.0, random_state=SEED).groupby("source").head(CAP)
    t2 = old[old["source"] == "global_mmlu"]
    t3 = old[old["source"].isin(CHAT)]
    return pd.concat([t1, t2, t3]).drop_duplicates("text")["text"].tolist()


def purity(y: np.ndarray, c: np.ndarray) -> float:
    return float(sum(pd.Series(y[c == k]).value_counts().iloc[0] for k in np.unique(c)) / len(y))


def assign(x: np.ndarray, mu: np.ndarray) -> np.ndarray:
    return np.argmax(x @ mu.T, axis=1)  # spec S5: k(x) = argmax φ(x)·μ_k


def split(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Paper-style random split: val = N_VAL, train = 60 %, test = the rest."""
    p = np.random.default_rng(seed).permutation(n)
    n_tr = int(0.6 * n)
    return p[:n_tr], p[n_tr : n_tr + N_VAL], p[n_tr + N_VAL :]


def difficulty(err: np.ndarray, c: np.ndarray, k: int, tr, va, te) -> dict:
    """Ψ_k from val (paper setting) and from train (noise-free); test gap E|e − Ψ_k(x)| vs K = 1."""
    out = {}
    e_te, c_te = err[te], c[te]
    m = ~np.isnan(e_te)
    e_te, c_te = e_te[m], c_te[m]
    for src, idx in (("val", va), ("train", tr)):
        e, cc = err[idx], c[idx]
        ok = ~np.isnan(e)
        mean_all = float(e[ok].mean())
        psi = np.array([e[ok & (cc == j)].mean() if (ok & (cc == j)).any() else mean_all
                        for j in range(k)])  # fmt: skip
        gap = float(np.abs(e_te - psi[c_te]).mean())
        g1 = float(np.abs(e_te - mean_all).mean())
        r2 = 1 - float(((e_te - psi[c_te]) ** 2).sum() / ((e_te - mean_all) ** 2).sum())
        out[src] = {"gap": gap, "gap_k1": g1, "gap_reduction": 1 - gap / g1, "r2": r2,
                    "psi_spread": float(psi.max() - psi.min())}  # fmt: skip
    return out


def run_set(name: str, df: pd.DataFrame, v: np.ndarray, labels: list[str], ks: list[int]) -> dict:
    res: dict = {"n": len(df), "labels": {lb: int(df[lb].nunique()) for lb in labels}, "K": {}}
    err = df["err"].to_numpy(float) if "err" in df else None
    keep: dict[int, np.ndarray] = {}
    for k in ks:
        reps = REPEATS if k in K_PAPER else REPEATS_EXTRA
        rows = []
        for r in range(reps):
            tr, va, te = split(len(df), SEED + r)
            if k >= len(tr):
                continue
            km = KMeans(n_clusters=k, n_init=10, random_state=SEED + r).fit(v[tr])
            c = assign(v, km.cluster_centers_)
            rng = np.random.default_rng(SEED + r)
            s = rng.choice(te, size=min(3000, len(te)), replace=False)
            sz = np.bincount(c[va], minlength=k)
            row = {"silhouette": float(silhouette_score(v[s], c[s], metric="cosine")),
                   "val_min": int(sz.min()), "val_small": int((sz < N_MIN).sum()),
                   "test_max_share": float(np.bincount(c[te], minlength=k).max() / len(te))}  # fmt: skip
            for lb in labels:
                y = df[lb].astype(str).to_numpy()[te]
                row[lb] = {"nmi": float(normalized_mutual_info_score(y, c[te])),
                           "ari": float(adjusted_rand_score(y, c[te])), "purity": purity(y, c[te])}  # fmt: skip
            if err is not None:
                row["difficulty"] = difficulty(err, c, k, tr, va, te)
            rows.append(row)
            if r == 0:
                keep[k] = c
        res["K"][str(k)] = summarize(rows)
        msg = ", ".join(f"{lb} NMI {res['K'][str(k)][lb]['nmi']['mean']:.3f}" for lb in labels)
        log(f"  {name} K={k} ({len(rows)} splits): {msg}, "
            f"sil {res['K'][str(k)]['silhouette']['mean']:.3f}")  # fmt: skip
    res["_keep"] = keep
    return res


def summarize(rows: list[dict]) -> dict:
    """Mean and 95 % t-interval over the repeated splits, for every numeric leaf."""

    def walk(vals: list):
        if isinstance(vals[0], dict):
            return {key: walk([x[key] for x in vals]) for key in vals[0]}
        a = np.array(vals, float)
        half = (
            float(stats.t.ppf(0.975, len(a) - 1) * a.std(ddof=1) / np.sqrt(len(a)))
            if len(a) > 1
            else None
        )
        return {"mean": float(a.mean()), "ci95": half, "n_splits": len(a)}

    return walk(rows)


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
    ap.add_argument("--embed-only", action="store_true")
    ap.add_argument("--sets", default="", help="comma list (default: all)")
    a = ap.parse_args()
    s4 = load_config("pipeline")["s4"]
    cand = s4["candidates"][a.model]
    task = a.task or s4["task"]
    emb = Embedder(cand["name"], cand["revision"], device=s4["device"], path=str(ROOT / cand["path"]),
                   task=task, prompt_name=s4["prompt_name"], merge_adapter=s4["merge_adapter"],
                   max_tokens=a.max_tokens, batch_size=s4["batch_size"],
                   max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip
    t_start = time.time()
    df = load_all()
    sets = build_sets(df)
    if a.sets:
        sets = {k: v for k, v in sets.items() if k in a.sets.split(",")}
    allt = pd.concat([d for d, _ in sets.values()]).drop_duplicates("text")["text"].tolist()
    ntok = np.array(emb.count_tokens(allt))
    log(f"{a.model}/{task}: {len(allt)} unique texts, tokens p50 {np.median(ntok):.0f}, "
        f"max {ntok.max()}, over {a.max_tokens}: {(ntok > a.max_tokens).sum()}")  # fmt: skip
    root = EXT / "emb" / f"{a.model}_{task}"
    store = Store(root)
    log(f"  legacy cache imported: {store.import_legacy(root, legacy_texts())} vectors")
    store.embed(allt, emb)
    if a.embed_only:
        return

    tag = a.model if task == s4["task"] else f"{a.model}_{task}"
    out_path = ROOT / "results" / f"persian_clustering_{tag}.json"
    out: dict = json.loads(out_path.read_text()) if a.sets and out_path.exists() else {"sets": {}}
    out.update({"model": cand["name"], "revision": cand["revision"], "task": task,
                "embedder_id": emb.embedder_id, "seed": SEED, "max_tokens": a.max_tokens,
                "protocol": {"split": "train 60 % / val 400 / test rest", "repeats": REPEATS,
                             "repeats_extra_K": REPEATS_EXTRA, "K_paper": list(K_PAPER),
                             "K_extra": list(K_EXTRA), "kmeans": "k-means++, n_init 10, fit on train",
                             "assign": "argmax dot product", "n_min": N_MIN},
                "n_unique": len(allt), "tokens": {"p50": float(np.median(ntok)), "p90": float(np.percentile(ntok, 90)),
                "max": int(ntok.max()), "n_over_max": int((ntok > a.max_tokens).sum())}})  # fmt: skip
    html_sections = []
    for name, (d, labels) in sets.items():
        if d.empty:
            continue
        d = d.assign(lang=d["text"].map(lang_tag)).reset_index(drop=True)
        v = store.get(d["text"].tolist())
        extra = [d[lb].nunique() for lb in labels if 3 <= d[lb].nunique() <= 128 and name != "chat"]
        ks = sorted(set(K_PAPER) | set(K_EXTRA) | set(extra))
        log(f"{name}: n = {len(d)}, K = {ks}")
        r = run_set(name, d, v, labels, ks)
        keep = r.pop("_keep")
        r["source_counts"] = d["source"].value_counts().to_dict()
        if "err" in d:
            r["err_known"] = int(d["err"].notna().sum())
        col = "source" if name in ("mix", "chat") else labels[0]
        r["table_K"] = 8
        r["table"] = crosstab(d, keep[8], col)
        if name in ("mix", "khayyam", "chat"):
            html_sections.append((f"{name}, K = 8 (split 1)", d, keep[8], col))
        out["sets"][name] = r
    out["duration_s"] = round(time.time() - t_start)
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    write_html(
        ROOT / "runs" / "s4" / f"persian_clusters_{tag}.html",
        f"Persian clusters: {tag}",
        html_sections,
    )
    log(f"done: {out_path.relative_to(ROOT)}, runs/s4/persian_clusters_{tag}.html")


if __name__ == "__main__":
    main()
