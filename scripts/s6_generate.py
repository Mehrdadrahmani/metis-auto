"""S6: generate answers (WP-06 step 6, spec S6, PLAN M6, P3).

Usage: METIS_MOCK=1 uv run python scripts/s6_generate.py --set pilot --stage pilot
A real run needs an approved stage in configs/budget.yaml. Prints counts and dollars only.

Every answer is saved to the call cache as it arrives. After any stop, run the same command again:
saved answers come back free. Add --retry-failed to also retry calls stored as failed.
A stopped run writes responses_<set>.partial.parquet and resume_<set>.json, never the final table.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

from metis.config import load_config
from metis.llm import stage as st
from metis.llm.budget import Budget, call_cost
from metis.llm.callcache import CallCache, cache_key, get_or_call
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
    ap.add_argument("--retry-failed", action="store_true", help="retry calls stored as failed")
    ap.add_argument("--est-usd", action="append", default=[], metavar="MODEL=USD",
                    help="measured cost per call, replaces the token-based estimate for that model")
    ap.add_argument("--estimate-only", action="store_true", help="print calls left and $, send nothing")
    args = ap.parse_args()

    start = time.perf_counter()
    cfg = load_config("gen_config")
    retries = [load_config("gen_retry"), load_config("gen_retry_2")]  # rising limits, cut answers only
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
    for pair in args.est_usd:
        model_id, usd = pair.split("=")
        if model_id not in costs:
            raise ValueError(f"unknown model {model_id}")
        costs[model_id] = float(usd)
    def messages_for(pid: str) -> list[dict]:
        r = rows[pid]
        return build_messages(r["instructions"], r["text"], r["history"], r["rag_context"])

    def calls_left(model_id: str) -> int:
        """Cached answers are free: the pre-check prices only what is left (D-097)."""
        spec, params = budget.models[model_id], gen_params(model_id, cfg)
        keys = (cache_key(model_id, spec.get("api_name"), messages_for(p), params, cfg["_id"]) for p in ids)
        found = [cache.get(k) for k in keys]
        return sum(f is None or (args.retry_failed and f.status != "ok") for f in found)

    left = {m: calls_left(m) for m in order}
    to_pay = sum(costs[m] * n for m, n in left.items())
    print(f"calls left {sum(left.values())} of {len(ids) * len(order)}: {left}; "
          f"token-based estimate ${to_pay:.2f}", flush=True)
    if args.estimate_only:
        cache.close()
        return 0
    if not is_mock():
        budget.check(args.stage, to_pay)

    records, reports = [], {}
    for model_id in order:
        params = gen_params(model_id, cfg)

        def one(pid: str, model_id=model_id, params=params):
            messages = messages_for(pid)
            result = get_or_call(
                cache, budget, args.stage, model_id, messages, params, cfg["_id"],
                costs[model_id], complete, retry_failed=args.retry_failed, prompt_id=pid,
            )
            config_id = cfg["_id"]
            for retry in retries:  # same limits for all models
                if not (result.status == "ok" and result.response
                        and result.response.finish_reason == "length"):
                    break
                config_id = retry["_id"]
                result = get_or_call(
                    cache, budget, args.stage, model_id, messages,
                    gen_params(model_id, cfg, retry["max_tokens"]), config_id,
                    costs[model_id] * 3, complete, retry_failed=args.retry_failed, prompt_id=pid,
                )
            resp = result.response
            ok = result.status == "ok" and bool(resp and resp.text.strip())
            records.append({
                "prompt_id": pid, "model_id": model_id, "gen_config_id": config_id,
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

    stopped = next(((m, r) for m, r in reports.items() if r.stopped), None)
    args.out.mkdir(parents=True, exist_ok=True)
    tag = st.file_tag(args.which)
    final = args.out / f"responses_{tag}.parquet"
    partial = args.out / f"responses_{tag}.partial.parquet"
    resume = args.out / f"resume_{tag}.json"
    # Sorted because threads race. A stopped run never writes the table S7 reads.
    columns = ["prompt_id", "model_id"]
    table = pd.DataFrame(records, columns=None if records else columns).sort_values(columns, ignore_index=True)
    table.to_parquet(partial if stopped else final, index=False)
    if stopped:
        resume.write_text(json.dumps({
            "stopped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": stopped[0], "reason": stopped[1].stopped_reason,
            "answers_saved_this_run": sum(r["status"] == "ok" for r in records),
            "done_per_model": {m: r.done for m, r in reports.items()},
            "resume_with": f"uv run python scripts/s6_generate.py --set {args.which} "
                           f"--stage {args.stage} --retry-failed "
                           f"{' '.join(f'--est-usd {e}' for e in args.est_usd)}".strip(),
        }, indent=2) + "\n", encoding="utf-8")
        print(f"Saved. To resume: see {resume}")
    else:
        partial.unlink(missing_ok=True)
        resume.unlink(missing_ok=True)
    st.write_manifest(args.out / f"manifest_{tag}.json", ids, {
        "stage": args.stage, "gen_config_id": cfg["_id"], "mock": is_mock(),
        "complete": stopped is None,
        "models": order, "records": len(records),
        "new_calls": sum(r.new_calls for r in reports.values()),
        "cost_usd": sum(r.cost_usd for r in reports.values()),
        "seconds": round(time.perf_counter() - start, 2),
    })
    cache.close()
    return 1 if any(r.stopped for r in reports.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
