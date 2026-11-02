"""WP-13 step 5: labels from the pointwise judge, and results/s7_stats.md (aggregates only).

Usage: uv run python scripts/s7_stats.py --set val
The test set writes labels_test.sealed.parquet and prints nothing about scores.
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
    ap.add_argument("--set", dest="which", choices=("val", "test"), default="val")
    ap.add_argument("--s7", type=Path, default=Path("runs/s7"))
    args = ap.parse_args()
    tau = yaml.safe_load(Path("configs/judge_choice.yaml").read_text(encoding="utf-8"))["tau"]
    tag = "test.sealed" if args.which == "test" else args.which
    d = pd.read_parquet(args.s7 / f"pointwise_jev_{tag}.parquet")
    kept = d[d["status"].isin(["ok", "failed_generation"])].copy()
    kept["loss"] = (kept["score"] < tau).astype(int)
    kept[["prompt_id", "model_id", "score", "loss", "status"]].to_parquet(
        args.s7 / f"labels_{tag}.parquet", index=False
    )
    if args.which == "test":
        print(f"sealed labels written: {len(kept)} of {len(d)} rows")
        return
    noise = json.loads((args.s7 / f"manifest_noise_{tag}.json").read_text())["summary"]
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
    Path("results/s7_stats.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
