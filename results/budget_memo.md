# Budget memo for Gate 1

Simulated from formulas and measured token statistics; no paid call yet. Metis prices of 2026-11-01, no prompt-cache discount, DeepSeek peak-hour doubling not included. Sizes: val 400, test 300, pilot 100. Mean input 2,871 tokens (chars / 3, n = 206,729 eligible prompts).

**Mid total: pointwise $41.61, pairwise $56.05. Cap $60. Line for action $45 (PLAN section 6).**
These include cache labels and the live run, which `results/cost_estimate_v1.md` leaves out.

## Cost per stage

Low: median answer 129 tokens. Mid: 300 tokens. High: input 4,439 tokens (billing mean, all traffic).

| Stage | Low | Mid | High |
|---|---:|---:|---:|
| Pilot: 5 models; terra pointwise, jev both (D-093) | $6.24 | $6.71 | $9.07 |
| Main generation (600 prompts) | $5.68 | $7.06 | $9.59 |
| Main judging, pointwise (terra) | $23.23 | $24.13 | $32.41 |
| Main judging, pairwise (terra) | $35.87 | $38.58 | $51.00 |
| Re-judge 5% | $1.16 | $1.21 | $1.62 |
| Cache labels (WP-17, planning) | $0.00 | $1.00 | $1.80 |
| Live run (WP-19, planning) | $0.80 | $1.50 | $2.50 |
| Rubric revision (only if Gate 2 fails) | $0.00 | $0.00 | $2.50 |
| **Total, pointwise** | **$37.11** | **$41.61** | **$59.49** |
| **Total, pairwise** | **$49.75** | **$56.05** | **$78.08** |

PLAN section 7 high: pointwise $39, pairwise $54. The mid case is above both. The main reason is the judge: mean input is 2,871 tokens against 1,640 planned, at $2.20 / $13.20 per million.

## Ways to cut (mid case)

| Option | Saves | Cost to the project |
|---|---:|---|
| jev-latest passes the pilot and judges the main run, pointwise | $23.73 | None if it agrees with the owner; known only at Gate 2 |
| Leave deepseek-v4-pro out of the pilot | $1.33 | That option (D-083) is not tested |
| Drop the 5% re-judge | $1.21 | No judge noise check (PLAN section 6 allows it) |
| Cap judge input at 4,000 tokens (cuts 18% of prompts) | $6.67 | Judge sees less context on those prompts |
| Cap judge input at 2,500 tokens (cuts 27% of prompts) | $8.72 | Same, on many more prompts |

With jev as main judge: about $17.88 in total, pointwise. Instructions alone do not drive cost: the 6,000-token cut on them saves $0.

## Recommendation

1. Keep the pointwise path as the plan. Pairwise with terra can be added to the pilot later for about $8.57 (answers are cached).
2. **Approve only the pilot now, with a $10 limit** (mid $6.71, high $9.07). It buys the real prices, token counts and the judge answer.
3. Keep gen_main, judge_main, cache_labels and live at $0 until Gate 2, then set them from measured costs.
4. If the first 20 real pilot calls cost over twice the estimate, the run stops by itself.
5. Even if the pilot uses the whole limit, $50 is left. The rest of the pointwise path with terra needs about $34.90, and pairwise with terra about $49.34, which fits but was never tested with terra (D-093).
