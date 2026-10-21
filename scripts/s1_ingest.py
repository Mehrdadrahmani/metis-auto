"""S1: build the prompts table (WP-02).

Usage: uv run python scripts/s1_ingest.py data/raw/sample.json runs/s1

Writes runs/s1/prompts.parquet (redacted text; git-ignored) and prompts.manifest.json (counts only).
Prints only the output paths.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from metis.config import load_config
from metis.data.inspect import _sha_file
from metis.data.load import load_with_report
from metis.data.prompts import build_prompts, exclusion_counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()

    t0 = time.perf_counter()
    cfg = load_config("pipeline")
    sessions, report = load_with_report(args.input)
    df, counts = build_prompts(sessions, cfg)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "prompts.parquet"
    df.to_parquet(out, index=False)
    manifest = {
        "stage": "s1_ingest",
        "input": str(args.input),
        "input_sha256": _sha_file(args.input),
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
