"""WP-03b: do the clusters mean something? Label make-up of every cluster (numbers only, no text).

nano, clustering adapter, K = 8, split 1 (seed 20261020), test part. For labelled sets: top labels per
cluster (share of the cluster) and, per label, the share that lands in its main cluster; NMI against a
shuffled-label baseline. For chat (no labels): counted text features per cluster (length, script,
code / math / question markers, source). Writes results/persian_cluster_meaning.json.

Usage: uv run python scripts/s4_cluster_meaning.py [--model nano] [--k 8]
"""

from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd
from s4_persian_cluster import EXT, ROOT, SEED, Store, assign, build_sets, load_all, log, split
from sklearn.cluster import KMeans
from sklearn.metrics import normalized_mutual_info_score

from metis.data.lang import lang_tag

LATIN = re.compile(r"[A-Za-z]")
ARABIC = re.compile(r"[؀-ۿ]")
CODE = re.compile(
    r"```|\bdef |\bimport |\bclass |#include|\bfunction\b|</?\w+>|;\s*$|\{\s*$|=>|\bSELECT\b",
    re.MULTILINE,
)
MATH = re.compile(r"[=+×÷^√∫∑]|\d\s*[-*/]\s*\d")
QUEST = re.compile(r"[?؟]")
CHAT_FEATURES = ("chars_p50", "latin_share", "code", "math", "question", "lang_fa", "lang_mixed_en")


def features(texts: pd.Series) -> dict:
    lat = texts.map(
        lambda t: len(LATIN.findall(t)) / max(1, len(LATIN.findall(t)) + len(ARABIC.findall(t)))
    )
    lang = texts.map(lang_tag)
    return {"chars_p50": float(texts.str.len().median()), "latin_share": float(lat.mean()),
            "code": float(texts.map(lambda t: bool(CODE.search(t))).mean()),
            "math": float(texts.map(lambda t: bool(MATH.search(t))).mean()),
            "question": float(texts.map(lambda t: bool(QUEST.search(t))).mean()),
            "lang_fa": float((lang == "fa").mean()), "lang_mixed_en": float(lang.isin(["mixed", "en"]).mean())}  # fmt: skip


def labelled(d: pd.DataFrame, c: np.ndarray, te: np.ndarray, col: str, k: int) -> dict:
    y = d[col].fillna("(none)").astype(str).to_numpy()[te]
    ct = c[te]
    rng = np.random.default_rng(SEED)
    out = {"nmi": float(normalized_mutual_info_score(y, ct)),
           "nmi_shuffled": float(normalized_mutual_info_score(rng.permutation(y), ct)), "clusters": [], "labels": {}}  # fmt: skip
    for j in range(k):
        m = ct == j
        vc = pd.Series(y[m]).value_counts(normalize=True)
        row = {
            "cluster": j,
            "n": int(m.sum()),
            "top": {a: round(float(b), 3) for a, b in vc.head(5).items()},
        }
        if "err" in d:
            e = d["err"].to_numpy(float)[te][m]
            row["human_error"] = round(float(np.nanmean(e)), 3) if np.isfinite(e).any() else None
        out["clusters"].append(row)
    for lb in pd.Series(y).value_counts().index:
        m = y == lb
        cc = pd.Series(ct[m]).value_counts(normalize=True)
        out["labels"][lb] = {
            "n": int(m.sum()),
            "main_cluster": int(cc.index[0]),
            "share_in_main": round(float(cc.iloc[0]), 3),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default="nano")
    ap.add_argument("--k", type=int, default=8)
    a = ap.parse_args()
    store = Store(EXT / "emb" / f"{a.model}_clustering")
    sets = build_sets(load_all())
    res: dict = {"model": a.model, "K": a.k, "seed": SEED, "split": "1 (test part)", "sets": {}}
    for name, cols in (
        ("mix", ["source", "fine"]),
        ("khayyam", ["label", "level"]),
        ("mmlu", ["fine", "label"]),
        ("chat", ["source"]),
    ):
        d, _ = sets[name]
        d = d.reset_index(drop=True)
        v = store.get(d["text"].tolist())
        tr, _, te = split(len(d), SEED)
        c = assign(
            v, KMeans(n_clusters=a.k, n_init=10, random_state=SEED).fit(v[tr]).cluster_centers_
        )
        r = {col: labelled(d, c, te, col, a.k) for col in cols}
        if name in ("chat", "mix"):
            r["features"] = [
                {"cluster": j, **features(d["text"].iloc[te][c[te] == j])} for j in range(a.k)
            ]
            r["features_all"] = features(d["text"].iloc[te])
        res["sets"][name] = r
        log(
            f"{name}: "
            + ", ".join(
                f"{col} NMI {r[col]['nmi']:.3f} (shuffled {r[col]['nmi_shuffled']:.3f})"
                for col in cols
            )
        )
    (ROOT / "results" / "persian_cluster_meaning.json").write_text(
        json.dumps(res, indent=1, ensure_ascii=False)
    )
    log("done: results/persian_cluster_meaning.json")


if __name__ == "__main__":
    main()
