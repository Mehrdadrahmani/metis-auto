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

import pandas as pd

from metis.config import load_config
from metis.data.split import make_splits, split_manifest, write_split


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
    cols = ["prompt_id", "session_id", "category", "lang", "session_created_at",
            "eligible_labeled", "eligible_train"]  # fmt: skip
    prompts = pd.read_parquet(args.prompts, columns=cols)
    res = make_splits(
        prompts,
        n_val=s2["n_val"],
        n_test=s2["n_test"],
        n_pilot=s2["n_pilot"],
        pool_factor=s2["recent_pool_factor"],
        max_per_session=s2["max_per_session"],
        cal_models=s2["cal_models"],
        seed=cfg["seed"],
    )
    manifest = split_manifest(res, {"pipeline": cfg["_id"]})
    manifest.update({"sizes_section": args.sizes or "s2", "input": str(args.prompts),
                     "duration_s": round(time.perf_counter() - t0, 2), "cost_usd": 0.0})  # fmt: skip
    write_split(res, args.out_dir, manifest)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out_dir}/split.parquet, test_ids.sealed and {args.manifest}")


if __name__ == "__main__":
    main()
