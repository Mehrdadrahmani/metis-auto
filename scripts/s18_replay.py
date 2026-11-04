"""WP-18 runs on validation. $0, simulated from stored answers. Usage: uv run python scripts/s18_replay.py"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from router_check import MODELS, load_val, vectors

from metis.eval.report import metrics
from metis.router.artifact import load_artifact
from metis.router.route import route
from metis.sim.replay import Settings, Traffic, load_answers, run


def traffic() -> tuple[Traffic, dict]:
    order, losses, groups, _ = load_val()
    vecs = vectors(order)
    cols = ["prompt_id", "session_id", "msg_index", "bot_id", "system_prompt_id", "text_norm", "demands_json", "uses_rag", "has_image", "timestamp"]
    meta = pd.read_parquet("runs/s1/prompts.parquet", columns=cols, filters=[("prompt_id", "in", order)]).set_index("prompt_id")
    rank = meta.loc[order].assign(i=np.arange(len(order))).sort_values(["timestamp", "msg_index"]).i.to_numpy()
    ids = [order[i] for i in rank]
    frame = pd.concat(pd.read_parquet(f"runs/s6/responses_{s}.parquet") for s in ("pilot", "val"))
    frame = frame[frame.prompt_id.isin(order)].drop_duplicates(["prompt_id", "model_id"])
    return Traffic(ids, vecs[rank], meta, pd.DataFrame(losses, index=order, columns=MODELS), groups[rank]), load_answers(frame)


def main() -> None:
    tr, answers = traffic()
    art = load_artifact("artifacts/router_v1")
    k4 = load_artifact("artifacts/router_v1_k4")
    main_model = "deepseek-v4-flash"
    runs = [(Settings("TakRouter K = 8, plain"), art), (Settings("TakRouter K = 4, plain"), k4),
            (Settings("Always Sonnet", fixed_model="claude-sonnet-5-5"), art), (Settings("Always DeepSeek", fixed_model=main_model), art),
            (Settings("Always Gemini", fixed_model="gemini-2.5-flash-lite"), art),
            (Settings("K = 8 + checks", checks=True), art), (Settings("K = 8 + cache", cache=True), art),
            (Settings("K = 8 + cache + checks", cache=True, checks=True), art),
            (Settings("K = 4 + cache + checks", cache=True, checks=True), k4),
            (Settings("K = 8 + all, 10-min outage", cache=True, checks=True, outage=(200, 300), outage_model=main_model), art)]
    runs += [(Settings(f"K = 8 + sticky δ {d}", stick_delta=d), art) for d in (0.02, 0.05, 0.1)]
    out, store = {}, {}
    for s, a in runs:
        rows = run(tr, answers, a, s)
        out[s.name] = metrics(rows, tr.groups)
        store[s.name] = rows
    plain = store["TakRouter K = 8, plain"]
    offline = 1 - np.mean([tr.losses.loc[p, route(v, MODELS, art.router(), art.meta.lam).model] for p, v in zip(tr.ids, tr.vectors, strict=True)])
    assert abs(plain.passed.mean() - offline) < 1e-9, "replay differs from offline"
    lines = ["# Replay on validation", "",
             f"Simulated cost and latency from stored calls, pass from stored labels, n = {len(tr.ids)}. In-sample for the router, so its pass is a little optimistic: see `results/lambda_frozen.md` for unseen figures.",
             f"Replay of K = 8 plain equals the offline router: {offline:.4f}. Cached answers have no stored label, so pass excludes them.", "",
             "| Setup | Pass (95% CI) | $ per 1k | p50 s | p90 s | Cache hits | Escalated | Failed | Failovers |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, m in out.items():
        lines.append(f"| {name} | {m['pass']:.1%} ({m['pass_low']:.1%} to {m['pass_high']:.1%}) | {m['cost_1k']:.3f} | {m['p50'] / 1000:.2f} | {m['p90'] / 1000:.2f} | {m['cache_rate']:.1%} | {m['escalation_rate']:.1%} | {m['failed']:.1%} | {m['failovers']} |")
    Path("results/replay_val.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("results/replay_val.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
