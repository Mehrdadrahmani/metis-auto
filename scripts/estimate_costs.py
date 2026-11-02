"""Per-stage calls and dollars (WP-06 step 10, PLAN 7.1). Prices from configs/models.yaml.

Usage: uv run python scripts/estimate_costs.py
T_in comes from the eligible prompts if runs/s1/prompts.parquet exists, else PLAN's 1,640.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from metis.llm.budget import call_cost
from metis.llm.client import load_models

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/cost_estimate_v1.md"
T_OUT, J_T_OUT, TEMPLATE = 300, 150, 500
N_VAL, N_TEST, N_PILOT, J = 400, 300, 100, 2


def mean_t_in() -> tuple[float, str]:
    path = ROOT / "runs/s1/prompts.parquet"
    if not path.exists():
        return 1640.0, "PLAN 7.2"
    df = pd.read_parquet(path, columns=["est_tokens_in", "eligible_labeled"])
    return float(df.loc[df["eligible_labeled"], "est_tokens_in"].mean()), "eligible prompts (chars / 3)"


def main() -> None:
    models = load_models()
    t_in, source = mean_t_in()
    candidates = [m for m, s in models.items() if s["role"] == "candidate"]
    pilot_gen = [*candidates, "deepseek-v4-pro"]
    non_anchor = [m for m in pilot_gen if not models[m]["is_anchor"]]
    main_new = N_VAL + N_TEST - N_PILOT
    judge_in = {1: t_in + TEMPLATE + T_OUT, 2: t_in + TEMPLATE + 2 * T_OUT}

    def judge_cost(judge: str, answers: int) -> float:
        return call_cost(models[judge], judge_in[answers], J_T_OUT)

    rows = []
    for m in pilot_gen:
        rows.append((f"Pilot generation: {m}", N_PILOT, N_PILOT * call_cost(models[m], t_in, T_OUT)))
    for judge in ("judge", "jev"):
        n = len(pilot_gen) * N_PILOT
        rows.append((f"Pilot pointwise: {judge}", n, n * judge_cost(judge, 1)))
        n = len(non_anchor) * N_PILOT * J
        if judge == "jev":  # D-093: terra judges the pilot pointwise only
            rows.append((f"Pilot pairwise: {judge}", n, n * judge_cost(judge, 2)))
    pilot = sum(r[2] for r in rows)
    for m in candidates:
        rows.append((f"Main generation: {m}", main_new, main_new * call_cost(models[m], t_in, T_OUT)))
    n_point = len(candidates) * main_new
    n_pair = (len(candidates) - 1) * main_new * J
    point, pair = n_point * judge_cost("judge", 1), n_pair * judge_cost("judge", 2)
    gen_main = sum(r[2] for r in rows if r[0].startswith("Main"))
    rejudge = int(0.05 * n_point) * judge_cost("judge", 1)

    lines = [
        "# Cost estimate v1 (WP-06 step 10)",
        "",
        (
            f"Assumptions: T_in = {t_in:.0f} ({source}), T_out = {T_OUT}, judge output = {J_T_OUT}, "
            f"template = {TEMPLATE} tokens. Metis prices, no prompt-cache discount. "
            "Instructions are not cut to 6,000 tokens here, so judge cost leans high. "
            "deepseek-v4-flash costs double in peak hours: not included. "
            "Prices are from `configs/models.yaml`; simulated from formulas, nothing measured yet."
        ),
        "",
        "| Item | Calls | USD |",
        "|---|---:|---:|",
    ]
    lines += [f"| {name} | {calls} | {usd:.2f} |" for name, calls, usd in rows]
    lines += [
        f"| Main judging, pointwise (gpt-5.6-terra) | {n_point} | {point:.2f} |",
        f"| Main judging, pairwise (gpt-5.6-terra) | {n_pair} | {pair:.2f} |",
        f"| Re-judge 5% | {int(0.05 * n_point)} | {rejudge:.2f} |",
        "",
        f"**Pilot (terra pointwise, jev both): ${pilot:.2f}.** Main generation: ${gen_main:.2f}.",
        "",
        (
            f"Total, pointwise path: ${pilot + gen_main + point + rejudge:.2f}. "
            f"Total, pairwise path: ${pilot + gen_main + pair + rejudge:.2f}. Cap: $60."
        ),
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-3:]))


if __name__ == "__main__":
    main()
