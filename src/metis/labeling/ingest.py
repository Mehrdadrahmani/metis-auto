"""Read the tool's CSV into ``human_labels`` (WP-06 step 7, spec section 3).

Usage: uv run python -m metis.labeling.ingest labels.csv runs/labeling/cal_x.key.json runs/labeling/human_labels.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PREF = {("left", "h"): "h", ("left", "anchor"): "anchor",
        ("right", "h"): "anchor", ("right", "anchor"): "h"}
PASS = {"yes": True, "no": False}


def ingest(csv_path: Path, key: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Unblinds the labels. Rows without both answers are left out, and an unknown id is an error."""
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    rows = []
    for r in df.to_dict("records"):
        k = key[r["item_id"]]
        if r["pass"] not in PASS or r["pref"] not in ("left", "right", "tie"):
            continue
        rows.append({
            "prompt_id": k["prompt_id"],
            "model_id": k["model_id"],
            "human_pass": PASS[r["pass"]],
            "human_pref": "tie" if r["pref"] == "tie" else PREF[(r["pref"], k["left"])],
            "note": r.get("note", ""),
            "mode": r.get("mode", ""),
        })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("key", type=Path)
    ap.add_argument("out", type=Path)
    args = ap.parse_args()
    labels = ingest(args.csv, json.loads(args.key.read_text(encoding="utf-8")))
    labels.to_parquet(args.out, index=False)
    print(f"{len(labels)} labels written")


if __name__ == "__main__":
    main()
