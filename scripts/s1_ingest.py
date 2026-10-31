"""S1: build the prompts table (WP-02, WP-08).

Usage: uv run python scripts/s1_ingest.py <data.json | parquet folder> runs/s1

JSON sample: everything in prompts.parquet. Parquet folder (full data): sessions are streamed;
long per-prompt context goes to context/part-*.parquet, joined by prompt_id when needed.
Writes prompts.manifest.json (counts only). Prints counts and paths, never content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from collections import Counter
from itertools import islice
from pathlib import Path

import pandas as pd

from metis.config import load_config
from metis.data.inspect import _sha_file
from metis.data.load import LoadReport, load_with_report
from metis.data.load_parquet import is_parquet_dir, iter_sessions
from metis.data.prompts import (
    CONTEXT_COLUMNS,
    build_prompts,
    build_rows,
    exclusion_counts,
    finish_prompts,
)

BATCH_SESSIONS = 2000


def input_hash(path: Path) -> str:
    if path.is_file():
        return _sha_file(path)
    h = hashlib.sha256()  # folder: names and sizes (1 GB of parquet need not be read twice)
    for f in sorted(p for p in path.rglob("*.parquet")):
        h.update(f"{f.relative_to(path)}:{f.stat().st_size}\n".encode())
    return h.hexdigest()


def build_streaming(root: Path, out_dir: Path, cfg: dict) -> tuple[pd.DataFrame, Counter, LoadReport]:
    report = LoadReport()
    counts: Counter = Counter()
    ctx_dir = out_dir / "context"
    shutil.rmtree(ctx_dir, ignore_errors=True)
    ctx_dir.mkdir(parents=True)
    sessions = iter_sessions(root, report)
    light: list[pd.DataFrame] = []
    part = 0
    while batch := list(islice(sessions, BATCH_SESSIONS)):
        df = pd.DataFrame(build_rows(batch, cfg, counts))
        if not df.empty:
            ctx = ["prompt_id", *CONTEXT_COLUMNS]
            df[ctx].to_parquet(ctx_dir / f"part-{part:05d}.parquet", index=False)
            light.append(df.drop(columns=list(CONTEXT_COLUMNS)))
        part += 1
        print(f"sessions {report.n_sessions:,}  rows {counts['user_messages']:,}", flush=True)
    full = pd.concat(light, ignore_index=True)
    counts["prompt_rows"] = len(full)
    return finish_prompts(full), counts, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()

    t0 = time.perf_counter()
    cfg = load_config("pipeline")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if is_parquet_dir(args.input):
        df, counts, report = build_streaming(args.input, args.out_dir, cfg)
    else:
        sessions, report = load_with_report(args.input)
        df, counts = build_prompts(sessions, cfg)
    out = args.out_dir / "prompts.parquet"
    df.to_parquet(out, index=False)
    manifest = {
        "stage": "s1_ingest",
        "input": str(args.input),
        "input_sha256": input_hash(args.input),
        "config_id": cfg["_id"],
        "seed": cfg["seed"],
        "counts": {
            "sessions": report.n_sessions,
            "messages": report.n_messages,
            **dict(counts),
            **exclusion_counts(df),
        },
        "duration_s": round(time.perf_counter() - t0, 2),
        "cost_usd": 0.0,
    }
    man = args.out_dir / "prompts.manifest.json"
    man.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} and {man}")


if __name__ == "__main__":
    main()
