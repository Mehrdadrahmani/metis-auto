"""Grow validation with prompts from train sessions (owner, 2026-11-03; D-115, DEV-15). No paid calls.

Train sessions can never hold a test prompt (make_splits keeps labeled sessions out of train), so
this needs no sealed file. The other pool, split "none", is mostly leftovers of test sessions.
The old 400 and the pilot stay as they are. Chosen prompts become val; the rest of each moved session
becomes "none", so train stays unlabeled and a session is never in two sets. Centroids are not refit.

Usage: uv run python scripts/s2_grow_val.py --add 400
Keeps the old table as runs/s2/split_val400.parquet. Refuses to run twice.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.data.split import _draw, ids_sha256

SEED = 20261103
SPLIT = Path("runs/s2/split.parquet")
BACKUP = Path("runs/s2/split_val400.parquet")
MANIFEST = Path("results/split_grow_manifest.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", type=int, required=True)
    args = ap.parse_args()
    if BACKUP.exists():
        raise SystemExit(f"{BACKUP} exists: validation was already grown")

    start = time.perf_counter()
    table = pd.read_parquet(SPLIT)
    eligible = pd.read_parquet("runs/s1/prompts.parquet", columns=["prompt_id", "eligible_labeled"])
    elig_ids = set(eligible.loc[eligible["eligible_labeled"], "prompt_id"])
    train = table[(table["split"] == "train") & table["prompt_id"].isin(elig_ids)]
    pool = train[["prompt_id", "session_id"]].assign(stratum="all")
    cap = load_config("pipeline")["s2"]["max_per_session"]
    chosen, sessions, shortfall = _draw(pool, args.add, cap, np.random.default_rng(SEED))

    old_val = table.loc[table["split"] == "val", "prompt_id"]
    moved = table["session_id"].isin(sessions)
    if table.loc[moved, "split"].eq("val").any():
        raise SystemExit("a chosen session already holds validation prompts")
    if len(chosen) != args.add:
        raise SystemExit(f"short draw: {shortfall}")

    shutil.copy2(SPLIT, BACKUP)
    new = table.copy()
    new.loc[moved & new["split"].eq("train"), "split"] = "none"
    new.loc[new["prompt_id"].isin(chosen), "split"] = "val"
    new.to_parquet(SPLIT, index=False)

    MANIFEST.write_text(json.dumps({
        "stage": "s2_grow_val", "decision": "D-115", "deviation": "DEV-15", "seed": SEED,
        "added": len(chosen), "sessions_moved": len(sessions), "max_per_session": cap,
        "train_prompts_left_train": int((moved & table["split"].eq("train")).sum()),
        "old_val_sha256": ids_sha256(old_val), "new_prompts_sha256": ids_sha256(chosen),
        "val_sha256": ids_sha256(new.loc[new["split"] == "val", "prompt_id"]),
        "counts_by_split": new["split"].value_counts().to_dict(),
        "centroids_refit": False, "sealed_files_opened": False,
        "seconds": round(time.perf_counter() - start, 2),
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
