"""WP-13 step 5: labels from the pointwise judge, and results/s7_stats.md (aggregates only).

Usage: uv run python scripts/s7_stats.py --set val
Validation only for now. A test run must write labels_test.sealed.parquet and no stats.
Loss = 1 when score < tau. Failed generations keep the worst score; dropped judgments have no label.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", choices=("val",), default="val")
    args = ap.parse_args()
    tau = yaml.safe_load(Path("configs/judge_choice.yaml").read_text(encoding="utf-8"))["tau"]
    d = pd.read_parquet(f"runs/s7/pointwise_jev_{args.which}.parquet")
    kept = d[d["status"].isin(["ok", "failed_generation"])].copy()
    kept["loss"] = (kept["score"] < tau).astype(int)
    kept[["prompt_id", "model_id", "score", "loss", "status"]].to_parquet(
        f"runs/s7/labels_{args.which}.parquet", index=False
    )
    noise = json.loads(Path(f"runs/s7/manifest_noise_{args.which}.json").read_text())["summary"]
    repeat = noise["pointwise_jev"]
    lines = [
        f"# S7 stats: {args.which}", "",
        f"Measured, pointwise jev, tau = {tau}, n = {d['prompt_id'].nunique()} prompts per model.", "",
        "| Model | judged | failed answer | dropped | mean score | median | pass rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model_id, g in d.groupby("model_id"):
        counts = g["status"].value_counts()
        scored = g[g["status"] == "ok"]["score"]
        rows = kept[kept["model_id"] == model_id]
        lines.append(
            f"| {model_id} | {counts.get('ok', 0)} | {counts.get('failed_generation', 0)} "
            f"| {counts.get('dropped', 0)} | {scored.mean():.2f} | {scored.median():.2f} "
            f"| {1 - rows['loss'].mean():.3f} |"
        )
    lines += [
        "",
        "Pass rate counts a failed answer as a fail.",
        f"Repeat check n = {repeat['n']}: mean gap {repeat['mean_abs_gap']:.3f}, "
        + f"within 1 point {repeat['within_1']:.3f}.",
    ]
    Path(f"results/s7_stats{'' if args.which == 'val' else '_' + args.which}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
