"""Write results/s6_stats.md: counts, tokens, dollars and latency per model. No text.

Usage: uv run python scripts/s6_stats.py --set val
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", default="val")
    args = ap.parse_args()
    d = pd.read_parquet(f"runs/s6/responses_{args.which}.parquet")
    db = sqlite3.connect("cache/llm_calls.sqlite")
    usd = dict(db.execute(
        "SELECT model_id, SUM(cost_usd) FROM ledger WHERE stage = 'gen_main' GROUP BY model_id"
    ).fetchall())
    lines = [
        f"# S6 stats: {args.which}", "",
        f"Measured, n = {d.prompt_id.nunique()} prompts per model, pilot answers reused.",
        "Dollars are new gen_main calls only, by ledger.", "",
        "| Model | ok | failed | retried for length | mean in | mean out | p50 ms | p90 ms | new $ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    base = d.gen_config_id.mode()[0]
    for model_id, g in d.groupby("model_id"):
        ok = g[g.status == "ok"]
        lines.append(
            f"| {model_id} | {len(ok)} | {len(g) - len(ok)} | {(ok.gen_config_id != base).sum()} "
            f"| {ok.tokens_in.mean():.0f} | {ok.tokens_out.mean():.0f} "
            f"| {ok.latency_ms.median():.0f} | {ok.latency_ms.quantile(0.9):.0f} "
            f"| {usd.get(model_id, 0):.4f} |"
        )
    lines += ["", f"Total new: ${sum(usd.values()):.4f}."]
    Path("results/s6_stats.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
