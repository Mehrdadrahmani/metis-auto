"""Structure-only data card (WP-01).

Usage: uv run python scripts/data_card.py data/raw/sample.json results/wp01_data/data_card_sample.md

Writes the markdown card and a manifest next to it. Prints only the output paths.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from metis.data.inspect import build_card, render_markdown


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    t0 = time.perf_counter()
    card = build_card(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(card, args.input.name), encoding="utf-8")
    manifest = {
        "stage": "data_card",
        "input": str(args.input),
        "input_sha256": card["input_sha256"],
        "config_hash": None,
        "seed": None,
        "counts": {k: card[k] for k in ("categories", "sessions", "messages")},
        "rescan_hits": sum(card["rescan_hits_by_field"].values()),
        "duration_s": round(time.perf_counter() - t0, 2),
        "cost_usd": 0.0,
    }
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} and {manifest_path}")


if __name__ == "__main__":
    main()
