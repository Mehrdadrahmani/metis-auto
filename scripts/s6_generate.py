"""S6: generate answers (WP-06 step 6, spec S6, PLAN M6, P3).

Usage: METIS_MOCK=1 uv run python scripts/s6_generate.py --set pilot --stage pilot
A real run needs an approved stage in configs/budget.yaml. Prints counts and dollars only.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from metis.config import load_config
from metis.llm import stage as st
from metis.llm.budget import Budget, call_cost
from metis.llm.callcache import CallCache, get_or_call
from metis.llm.client import complete, is_mock
from metis.llm.messages import build_messages, gen_params
from metis.llm.runner import run_batch


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="which", choices=st.SETS, required=True)
    ap.add_argument("--stage", choices=("pilot", "gen_main"), required=True)
    ap.add_argument("--prompts", type=Path, default=Path("runs/s1/prompts.parquet"))
    ap.add_argument("--split", type=Path, default=Path("runs/s2/split.parquet"))
    ap.add_argument("--out", type=Path, default=Path("runs/s6"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    start = time.perf_counter()
    cfg = load_config("gen_config")
    cache = CallCache()
    budget = Budget(cache)
    limits = budget.config["anomalies"]
    ids = st.select_ids(args.split, args.which, args.limit)
    rows = st.load_rows(args.prompts, ids)
    t_in = sum(r["est_tokens_in"] for r in rows.values()) / len(rows)

    wanted = [
        m for m, spec in budget.models.items()
        if spec["role"] == "candidate" or (spec["role"] == "pilot_option" and args.stage == "pilot")
    ]
    order = st.cheapest_first(budget.models, wanted)
    costs = {m: call_cost(budget.models[m], t_in, st.T_OUT) for m in order}
    if not is_mock():
        budget.check(args.stage, sum(costs.values()) * len(ids))

    records, reports = [], {}
    for model_id in order:
        params = gen_params(model_id, cfg)

        def one(pid: str, model_id=model_id, params=params):
            r = rows[pid]
            messages = build_messages(r["instructions"], r["text"], r["history"], r["rag_context"])
            result = get_or_call(
                cache, budget, args.stage, model_id, messages, params, cfg["_id"],
                costs[model_id], complete, prompt_id=pid,
            )
            resp = result.response
            ok = result.status == "ok" and bool(resp and resp.text.strip())
            records.append({
                "prompt_id": pid, "model_id": model_id, "gen_config_id": cfg["_id"],
                "text": resp.text if ok else None,
                "tokens_in": resp.tokens_in if resp else 0,
                "tokens_out": resp.tokens_out if resp else 0,
                "latency_ms": resp.latency_ms if resp else None,
                "finish_reason": resp.finish_reason if resp else None,
                "status": "ok" if ok else "failed",
            })
            return result

        report = run_batch(
            f"{args.stage}_gen_{model_id}", ids, one, limits, args.concurrency,
            est_cost_per_call=costs[model_id], params={"gen_config_id": cfg["_id"]},
        )
        reports[model_id] = report
        if report.stopped:
            print(f"STOPPED {model_id}: {report.stopped_reason}")
            break

    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_parquet(args.out / f"responses_{args.which}.parquet", index=False)
    st.write_manifest(args.out / f"manifest_{args.which}.json", ids, {
        "stage": args.stage, "gen_config_id": cfg["_id"], "mock": is_mock(),
        "models": order, "records": len(records),
        "new_calls": sum(r.new_calls for r in reports.values()),
        "cost_usd": sum(r.cost_usd for r in reports.values()),
        "seconds": round(time.perf_counter() - start, 2),
    })
    cache.close()
    return 1 if any(r.stopped for r in reports.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
