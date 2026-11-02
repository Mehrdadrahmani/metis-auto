"""WP-08 step 9: budget memo for Gate 1, from real token statistics and Metis prices.

Usage: uv run python scripts/budget_memo.py     (no paid call; writes results/budget_memo.md)
Simulated from formulas. Test tokens are not opened: all eligible prompts stand in for them.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from metis.llm.budget import call_cost
from metis.llm.client import load_models

ROOT = Path(__file__).resolve().parents[1]
T_OUT_MEAN, T_OUT_LOW, T_IN_HIGH = 300, 129, 4439  # planning; median and billing mean, WP-08 part A
J_OUT, TEMPLATE, MAIN = 150, 500, 600  # 400 val + 300 test - 100 pilot (reused)
CACHE_LABELS = (0.0, 1.0, 1.8)  # PLAN 7.2, low/mid/high
LIVE = (0.8, 1.5, 2.5)
RUBRIC = (0.0, 0.0, 2.5)


def costs(models: dict, t_gen: float, t_judge: float, t_out: float, pilot_v4pro: bool = True) -> dict:
    cand = [m for m, s in models.items() if s["role"] == "candidate"]
    pilot = [*cand, "deepseek-v4-pro"] if pilot_v4pro else cand
    others = sum(not models[m]["is_anchor"] for m in pilot)

    def gen(m: str) -> float:
        return call_cost(models[m], t_gen, t_out)

    def judge(j: str, answers: int) -> float:
        return call_cost(models[j], t_judge + TEMPLATE + answers * t_out, J_OUT)

    # D-093: terra judges the pilot pointwise only; jev does both methods.
    pilot_all = sum(100 * gen(m) for m in pilot) + len(pilot) * 100 * judge("judge", 1)
    pilot_all += len(pilot) * 100 * judge("jev", 1) + others * 200 * judge("jev", 2)
    return {
        "pilot": pilot_all, "gen": sum(MAIN * gen(m) for m in cand),
        "point": 4 * MAIN * judge("judge", 1), "pair": 6 * MAIN * judge("judge", 2),
        "rejudge": 120 * judge("judge", 1), "jev_point": 4 * MAIN * judge("jev", 1),
        "jev_pair": 6 * MAIN * judge("jev", 2),
    }  # fmt: skip


def main() -> None:
    models = load_models()
    df = pd.read_parquet(ROOT / "runs/s1/prompts.parquet", columns=["est_tokens_in", "eligible_labeled"])
    tokens = df.loc[df["eligible_labeled"], "est_tokens_in"]
    mean = float(tokens.mean())
    capped = {cap: float(tokens.clip(upper=cap).mean()) for cap in (4000, 2500)}
    share = {cap: float((tokens > cap).mean()) for cap in capped}
    low, mid, high = (costs(models, mean, mean, T_OUT_LOW), costs(models, mean, mean, T_OUT_MEAN),
                      costs(models, T_IN_HIGH, T_IN_HIGH, T_OUT_MEAN))  # fmt: skip
    cases = (low, mid, high)

    def row(name: str, key: str) -> str:
        return f"| {name} | " + " | ".join(f"${c[key]:.2f}" for c in cases) + " |"

    def total(key: str, i: int) -> float:
        c = cases[i]
        return c["pilot"] + c["gen"] + c[key] + c["rejudge"] + CACHE_LABELS[i] + LIVE[i] + RUBRIC[i]

    base = total("point", 1)
    pair = total("pair", 1)
    no_pro = costs(models, mean, mean, T_OUT_MEAN, pilot_v4pro=False)
    cut = {cap: costs(models, mean, t, T_OUT_MEAN) for cap, t in capped.items()}
    jev_path = mid["pilot"] + mid["gen"] + mid["jev_point"] + mid["rejudge"] + 2.5
    lines = [
        "# Budget memo for Gate 1", "",
        ("Simulated from formulas and measured token statistics; no paid call yet. Metis prices of "
         "2026-11-01, no prompt-cache discount, DeepSeek peak-hour doubling not included. Sizes: val 400, "
         f"test 300, pilot 100. Mean input {mean:,.0f} tokens (chars / 3, n = {len(tokens):,} eligible prompts)."), "",
        f"**Mid total: pointwise ${base:.2f}, pairwise ${pair:.2f}. Cap $60. Line for action $45 (PLAN section 6).**",
        "These include cache labels and the live run, which `results/cost_estimate_v1.md` leaves out.", "",
        "## Cost per stage", "",
        "Low: median answer 129 tokens. Mid: 300 tokens. High: input 4,439 tokens (billing mean, all traffic).", "",
        "| Stage | Low | Mid | High |", "|---|---:|---:|---:|",
        row("Pilot: 5 models; terra pointwise, jev both (D-093)", "pilot"), row("Main generation (600 prompts)", "gen"),
        row("Main judging, pointwise (terra)", "point"), row("Main judging, pairwise (terra)", "pair"),
        row("Re-judge 5%", "rejudge"),
        "| Cache labels (WP-17, planning) | $0.00 | $1.00 | $1.80 |", "| Live run (WP-19, planning) | $0.80 | $1.50 | $2.50 |",
        "| Rubric revision (only if Gate 2 fails) | $0.00 | $0.00 | $2.50 |",
        f"| **Total, pointwise** | **${total('point', 0):.2f}** | **${base:.2f}** | **${total('point', 2):.2f}** |",
        f"| **Total, pairwise** | **${total('pair', 0):.2f}** | **${pair:.2f}** | **${total('pair', 2):.2f}** |", "",
        ("PLAN section 7 high: pointwise $39, pairwise $54. The mid case is above both. The main reason is the "
         f"judge: mean input is {mean:,.0f} tokens against 1,640 planned, at $2.20 / $13.20 per million."), "",
        "## Ways to cut (mid case)", "", "| Option | Saves | Cost to the project |", "|---|---:|---|",
        f"| jev-latest passes the pilot and judges the main run, pointwise | ${mid['point'] - mid['jev_point']:.2f} | None if it agrees with the owner; known only at Gate 2 |",
        f"| Leave deepseek-v4-pro out of the pilot | ${mid['pilot'] - no_pro['pilot']:.2f} | That option (D-083) is not tested |",
        f"| Drop the 5% re-judge | ${mid['rejudge']:.2f} | No judge noise check (PLAN section 6 allows it) |",
        f"| Cap judge input at 4,000 tokens (cuts {share[4000]:.0%} of prompts) | ${mid['point'] - cut[4000]['point'] + mid['pilot'] - cut[4000]['pilot']:.2f} | Judge sees less context on those prompts |",
        f"| Cap judge input at 2,500 tokens (cuts {share[2500]:.0%} of prompts) | ${mid['point'] - cut[2500]['point'] + mid['pilot'] - cut[2500]['pilot']:.2f} | Same, on many more prompts |", "",
        (f"With jev as main judge: about ${jev_path:.2f} in total, pointwise. Instructions alone do not drive cost: "
         "the 6,000-token cut on them saves $0."), "",
        "## Recommendation", "",
        "1. Keep the pointwise path as the plan. Pairwise with terra can be added to the pilot later for about $8.57 (answers are cached).",
        f"2. **Approve only the pilot now, with a $10 limit** (mid ${mid['pilot']:.2f}, high ${high['pilot']:.2f}). It buys the real prices, token counts and the judge answer.",
        "3. Keep gen_main, judge_main, cache_labels and live at $0 until Gate 2, then set them from measured costs.",
        "4. If the first 20 real pilot calls cost over twice the estimate, the run stops by itself.",
        (f"5. Even if the pilot uses the whole limit, $50 is left. The rest of the pointwise path with terra needs about "
         f"${mid['gen'] + mid['point'] + mid['rejudge'] + 2.5:.2f}, and pairwise with terra about "
         f"${mid['gen'] + mid['pair'] + mid['rejudge'] + 2.5:.2f}, which fits but was never tested with terra (D-093)."), "",
    ]  # fmt: skip
    (ROOT / "results/budget_memo.md").write_text("\n".join(lines), "utf-8")
    print("\n".join(lines[3:6] + lines[9:35]))


if __name__ == "__main__":
    main()
