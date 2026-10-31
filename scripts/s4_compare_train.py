"""S4 embedder choice on real data (WP-08 step 6, D-052): small vs nano on a TRAIN sample only.

Usage: uv run python scripts/s4_compare_train.py small   (or nano)

Prompts come from split.parquet rows with split == train, which holds no test rows by construction.
Writes results/wp08_full_data/embedder_compare_<model>.json (numbers only) and
runs/s4/cluster_samples_<model>.html (git-ignored, redacted prompts for the owner).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from s4_embed_bench import clusters, latency, log, persian_check, synth_text, write_html

from metis.config import load_config
from metis.embed.embedder import Embedder

ROOT = Path(__file__).resolve().parents[1]
N_SAMPLE = 10_000
N_LATENCY = 100


def train_sample(seed: int) -> pd.DataFrame:
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet", columns=["prompt_id", "split"])
    train = split.loc[split["split"] == "train", "prompt_id"]
    cols = ["prompt_id", "bot_id", "lang", "text_chars", "embed_input"]
    df = pd.read_parquet(ROOT / "runs/s1/prompts.parquet", columns=cols)
    df = df[df["prompt_id"].isin(set(train))].sort_values("prompt_id", ignore_index=True)
    df = df.sample(N_SAMPLE, random_state=seed).reset_index(drop=True)
    return df.assign(category="all")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model", choices=["small", "nano"])
    a = ap.parse_args()
    cfg = load_config("pipeline")
    s4, seed = cfg["s4"], cfg["seed"]
    cand = s4["candidates"][a.model]
    emb = Embedder(cand["name"], cand["revision"], device=s4["device"], path=str(ROOT / cand["path"]),
                   task=s4["task"], prompt_name=s4["prompt_name"],
                   merge_adapter=s4["merge_adapter"], max_tokens=s4["max_tokens"],
                   batch_size=s4["batch_size"], max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip
    df = train_sample(seed)
    texts = df["embed_input"].tolist()
    pairs = yaml.safe_load((ROOT / "scripts/data/persian_pairs.yaml").read_text(encoding="utf-8"))
    ntok = np.array(emb.count_tokens(texts))
    log(f"{a.model}: sample ready, max tokens {ntok.max()}")

    t0 = time.perf_counter()
    vecs = emb.encode(texts)
    secs = time.perf_counter() - t0
    log(f"{a.model}: embedded {len(texts)} in {secs:.0f} s")
    lat = {str(n): latency(emb, synth_text(emb, n, pairs), N_LATENCY) for n in (30, 200, 512)}
    persian = persian_check(emb, pairs)
    cl = clusters(vecs, df, {"all": "c1"}, ks=(4, 6, 8))
    path = ROOT / f"runs/s4/cluster_samples_{a.model}.html"
    write_html(path, a.model, df, cl, {"all": "c1"})

    bots = df["bot_id"].to_numpy()
    for r in cl.values():
        lab = np.array(r["labels"])
        r["largest_cluster_share"] = float(np.bincount(lab).max() / len(lab))
        r["bots_top1_share"] = [
            float(pd.Series(bots[lab == c]).value_counts(normalize=True).iloc[0])
            for c in range(lab.max() + 1)
        ]
    out = {
        "model": cand["name"], "embedder_id": emb.embedder_id, "n_train_sample": len(df), "seed": seed,
        "dim": int(vecs.shape[1]), "prompts_per_s": len(df) / secs, "embed_s": secs,
        "tokens": {"p50": float(np.median(ntok)), "p90": float(np.percentile(ntok, 90)),
                   "p99": float(np.percentile(ntok, 99)), "max": int(ntok.max())},
        "latency": lat, "persian": persian,
        "clusters": {k: {x: y for x, y in v.items() if x != "labels"} for k, v in cl.items()},
    }  # fmt: skip
    res = ROOT / f"results/wp08_full_data/embedder_compare_{a.model}.json"
    res.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(res)


if __name__ == "__main__":
    main()
