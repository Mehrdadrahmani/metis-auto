"""S2: split by session (WP-02).

Usage: uv run python scripts/s2_split.py runs/s1/prompts.parquet runs/s2 results/split_manifest.json
       [--sizes sample_dry_run]

Writes split.parquet (no test rows), test_ids.sealed and a manifest (counts + hashes only).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.data.split import make_splits, split_manifest, write_split

ROOT = Path(__file__).resolve().parents[1]


def smd(a: pd.Series, b: pd.Series) -> float:
    """Standardized difference (pooled SD); 0 if both have no spread."""
    sd = np.sqrt((a.var() + b.var()) / 2)
    return 0.0 if sd == 0 else round(float(abs(a.mean() - b.mean()) / sd), 3)


def similarity(prompts: pd.DataFrame, table: pd.DataFrame, purpose: pd.DataFrame | None) -> dict:
    """Val vs test vs all eligible on language, length, RAG, bot purpose: aggregates only."""
    keep = ["prompt_id", "bot_id", "eligible_labeled", "uses_rag", "lang"]
    d = prompts[keep].copy()
    d["log_len"] = np.log1p(prompts["text_chars"])
    d["is_fa"] = d["lang"].eq("fa").astype(float)
    d["rag"] = d["uses_rag"].astype(float)
    columns = ["is_fa", "log_len", "rag"]
    if purpose is not None:
        d = d.merge(purpose, on="bot_id", how="left")
        d["cat"] = d["cat"].fillna("none")
        for c in sorted(d["cat"].unique()):
            d[f"bot_{c}"] = d["cat"].eq(c).astype(float)
            columns.append(f"bot_{c}")
    d = d.merge(table[["prompt_id", "split"]], on="prompt_id")
    groups = {
        "val": d[d["split"] == "val"],
        "test": d[d["split"] == "test"],
        "train": d[d["split"] == "train"],
        "eligible": d[d["eligible_labeled"]],
    }
    out = {}
    for x, y in (("val", "test"), ("val", "eligible"), ("test", "eligible"), ("val", "train")):
        out[f"{x}_vs_{y}"] = {c: smd(groups[x][c], groups[y][c]) for c in columns}
    out["means"] = {g: {c: round(float(f[c].mean()), 3) for c in columns}
                    for g, f in groups.items()}  # fmt: skip
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prompts", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--sizes", default=None, help="config section overriding n_val/n_test/n_pilot")
    args = ap.parse_args()

    t0 = time.perf_counter()
    cfg = load_config("pipeline")
    s2 = dict(cfg["s2"])
    if args.sizes:
        s2.update(cfg[args.sizes])
    balance = s2.get("balance_field")
    cols = ["prompt_id", "session_id", "bot_id", "lang", "msg_index", "text_chars", "uses_rag",
            "eligible_labeled", "eligible_train"] + ([balance] if balance else [])  # fmt: skip
    cols = list(dict.fromkeys(cols))
    prompts = pd.read_parquet(args.prompts, columns=cols)
    res = make_splits(
        prompts,
        n_val=s2["n_val"],
        n_test=s2["n_test"],
        n_pilot=s2["n_pilot"],
        max_per_session=s2["max_per_session"],
        cal_models=s2["cal_models"],
        seed=cfg["seed"],
        balance=balance,
    )
    t = res.table
    a, b = (set(t.loc[t["split"] == s, "session_id"]) for s in ("val", "test"))
    train = set(t.loc[t["split"] == "train", "session_id"])
    assert not (a & b or a & train or b & train), "a session is in two splits"
    manifest = split_manifest(res, {"pipeline": cfg["_id"]})
    purpose_path = ROOT / "runs/bots/purpose.parquet"
    purpose = pd.read_parquet(purpose_path) if purpose_path.exists() else None
    manifest["similarity"] = similarity(prompts, t, purpose)
    manifest.update({"sizes_section": args.sizes or "s2", "input": str(args.prompts),
                     "duration_s": round(time.perf_counter() - t0, 2), "cost_usd": 0.0})  # fmt: skip
    write_split(res, args.out_dir, manifest)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out_dir}/split.parquet, test_ids.sealed and {args.manifest}")


if __name__ == "__main__":
    main()
