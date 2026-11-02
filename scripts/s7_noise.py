"""WP-09 step 5: test-retest. Re-judge a seeded sample with a salted cache key (a true repeat).

Usage: uv run python scripts/s7_noise.py --set pilot --stage pilot
Pointwise: 20 items for terra and jev. Pairwise: 20 items for jev (D-093). Prints aggregates only.
Compares with the first judgments in runs/s7; writes runs/pilot/noise_*.parquet and a manifest.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import pandas as pd

from metis.judge import pairwise, pointwise, render
from metis.judge.common import JudgeRun
from metis.llm import stage as st
from metis.llm.budget import Budget, call_cost
from metis.llm.callcache import CallCache
from metis.llm.runner import run_batch

SALT = "-noise1"
N = 20
JOBS = (("pointwise", "judge"), ("pointwise", "jev"), ("pairwise", "jev"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", choices=st.SETS, required=True)
    ap.add_argument("--stage", choices=("pilot",), required=True)
    ap.add_argument("--prompts", type=Path, default=Path("runs/s1/prompts.parquet"))
    ap.add_argument("--s6", type=Path, default=Path("runs/s6"))
    ap.add_argument("--s7", type=Path, default=Path("runs/s7"))
    ap.add_argument("--out", type=Path, default=Path("runs/pilot"))
    args = ap.parse_args()

    start = time.perf_counter()
    base = render.judge_config()
    cfg = {**base, "judge_config_id": base["judge_config_id"] + SALT}
    cache = CallCache()
    budget = Budget(cache)
    answers = pd.read_parquet(args.s6 / f"responses_{args.which}.parquet")
    text = {(a.prompt_id, a.model_id): a.text for a in answers.itertuples()}
    rows = st.load_rows(args.prompts, sorted(answers["prompt_id"].unique()))
    rng = random.Random(base["seed"])
    summary, stopped = {}, False

    for method, judge in JOBS:
        first = pd.read_parquet(args.s7 / f"{method}_{judge}_{args.which}.parquet")
        first = first[first["status"] == "ok"]
        keys = ["prompt_id", "model_id"] + (["order"] if method == "pairwise" else [])
        items = sorted(first[keys].itertuples(index=False, name=None))
        items = rng.sample(items, N)
        cost = call_cost(budget.models[judge], 4000, 150)
        run = JudgeRun(cache, budget, args.stage, judge, cfg, cost)
        records = []

        def one(item, method=method, run=run, records=records):
            if method == "pointwise":
                result, record = pointwise.judge(run, rows[item[0]], item[1], text.get(item))
            else:
                pid, model_id, order = item
                result, record = pairwise.judge(
                    run, rows[pid], model_id, order, text.get((pid, model_id)),
                    text.get((pid, base["anchor"])),
                )
            records.append(record)
            return result

        report = run_batch(
            f"{args.stage}_noise_{method}_{judge}", items, one, budget.config["anomalies"], 2,
            est_cost_per_call=cost, params={"judge_config_id": cfg["judge_config_id"]},
        )
        table = pd.DataFrame(records).sort_values(keys, ignore_index=True)
        table.to_parquet(args.out / f"noise_{method}_{judge}_{args.which}.parquet", index=False)
        both = table[table["status"] == "ok"].merge(first, on=keys, suffixes=("_2", "_1"))
        if method == "pointwise":
            gap = (both["score_1"] - both["score_2"]).abs()
            agree = {"exact": float((gap == 0).mean()), "within_1": float((gap <= 1).mean()),
                     "mean_abs_gap": float(gap.mean())}
        else:
            agree = {"same_verdict": float((both["verdict_1"] == both["verdict_2"]).mean())}
        name = f"{method}_{judge}"
        summary[name] = {"n": len(both), **agree, "new_calls": report.new_calls,
                         "cost_usd": report.cost_usd}
        print(name, summary[name])
        if report.stopped:
            print(f"STOPPED {name}: {report.stopped_reason}")
            stopped = True
            break

    st.write_manifest(args.out / f"manifest_noise_{args.which}.json",
                      sorted(answers["prompt_id"].unique()), {
        "stage": args.stage, "judge_config_id": cfg["judge_config_id"], "seed": base["seed"],
        "summary": summary, "seconds": round(time.perf_counter() - start, 2),
    })
    cache.close()
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
