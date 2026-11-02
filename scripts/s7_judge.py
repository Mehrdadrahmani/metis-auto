"""S7: judge the answers, pointwise and/or pairwise (WP-06 step 6, spec S7-PT, S7-PW).

Usage: METIS_MOCK=1 uv run python scripts/s7_judge.py --set pilot --stage pilot --judge judge
A real run needs an approved stage in configs/budget.yaml. Prints counts and dollars only.
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
from metis.llm.client import is_mock
from metis.llm.runner import run_batch

JUDGE_T_OUT = 150      # reason + verdict, capped at 400
TEMPLATE_TOKENS = 500  # the template's own text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", choices=st.SETS, required=True)
    ap.add_argument("--stage", choices=("pilot", "judge_main"), required=True)
    ap.add_argument("--judge", choices=("judge", "jev"), required=True)
    ap.add_argument("--method", choices=("pointwise", "pairwise", "both"), default="both")
    ap.add_argument("--prompts", type=Path, default=Path("runs/s1/prompts.parquet"))
    ap.add_argument("--s6", type=Path, default=Path("runs/s6"))
    ap.add_argument("--out", type=Path, default=Path("runs/s7"))
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--retry-failed", action="store_true", help="retry calls stored as failed")
    args = ap.parse_args()

    if args.which == "test" and (args.stage != "judge_main" or args.method != "pointwise"):
        ap.error("the test set takes --stage judge_main --method pointwise only")
    tag = st.file_tag(args.which)
    start = time.perf_counter()
    cfg = render.judge_config()
    cache = CallCache()
    budget = Budget(cache)
    limits = budget.config["anomalies"]
    answers = pd.read_parquet(args.s6 / f"responses_{tag}.parquet")
    ids = sorted(answers["prompt_id"].unique())
    rows = st.load_rows(args.prompts, ids)
    # A failed generation has no text; parquet may hand it back as NaN, which is truthy.
    text = {(a.prompt_id, a.model_id): a.text if isinstance(a.text, str) else None
            for a in answers.itertuples()}
    t_in = sum(r["est_tokens_in"] for r in rows.values()) / len(rows)
    models = st.cheapest_first(budget.models, sorted(answers["model_id"].unique()))
    anchor = cfg["anchor"]

    def price(n_answers: int) -> float:
        tokens = t_in + TEMPLATE_TOKENS + n_answers * st.T_OUT
        return call_cost(budget.models[args.judge], tokens, JUDGE_T_OUT)

    tasks = []
    if args.method in ("pointwise", "both"):
        tasks.append(("pointwise", [(p, m) for m in models for p in ids], price(1)))
    if args.method in ("pairwise", "both"):
        items = [(p, m, o) for m in models if m != anchor for p in ids for o in pairwise.ORDERS]
        random.Random(cfg["seed"]).shuffle(items)
        tasks.append(("pairwise", items, price(2)))
    if not is_mock():
        # Cached items are free: the pre-check prices only what is left. Each call is still guarded.
        count = sum(len(items) for _, items, _ in tasks)
        left = max(0, count - cache.ok_calls(args.stage, args.judge)) / count
        budget.check(args.stage, left * sum(len(items) * cost for _, items, cost in tasks))

    args.out.mkdir(parents=True, exist_ok=True)
    stopped, summary = False, {}
    for method, items, cost in tasks:
        run = JudgeRun(cache, budget, args.stage, args.judge, cfg, cost, args.retry_failed)
        records = []

        def one(item, method=method, run=run, records=records):
            if method == "pointwise":
                pid, model_id = item
                result, record = pointwise.judge(run, rows[pid], model_id, text.get(item))
            else:
                pid, model_id, order = item
                result, record = pairwise.judge(
                    run, rows[pid], model_id, order, text.get((pid, model_id)), text.get((pid, anchor))
                )
            records.append(record)
            return result

        report = run_batch(
            f"{args.stage}_{method}_{args.judge}", items, one, limits, args.concurrency,
            est_cost_per_call=cost, params={"judge_config_id": cfg["judge_config_id"]},
        )
        name = f"{method}_{args.judge}_{tag}"
        keys = [c for c in ("prompt_id", "model_id", "order") if records and c in records[0]]
        table = pd.DataFrame(records).sort_values(keys, ignore_index=True)  # threads race
        # A stopped run never writes the table later stages read. Rerun the command to resume.
        table.to_parquet(args.out / f"{name}{'.partial' if report.stopped else ''}.parquet", index=False)
        if not report.stopped:
            (args.out / f"{name}.partial.parquet").unlink(missing_ok=True)
        by_status = pd.Series([r["status"] for r in records]).value_counts().to_dict()
        summary[method] = {"records": len(records), "status": by_status,
                           "new_calls": report.new_calls, "cost_usd": report.cost_usd}
        if method == "pairwise":
            summary[method]["outcomes"] = len(pairwise.outcomes(records))
        print(method, summary[method])
        if report.stopped:
            print(f"STOPPED {method}: {report.stopped_reason}")
            stopped = True
            break

    st.write_manifest(args.out / f"manifest_{args.judge}_{tag}.json", ids, {
        "stage": args.stage, "judge": args.judge, "mock": is_mock(), "complete": not stopped,
        "judge_config_id": cfg["judge_config_id"], "seed": cfg["seed"], "summary": summary,
        "seconds": round(time.perf_counter() - start, 2),
    })
    cache.close()
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
