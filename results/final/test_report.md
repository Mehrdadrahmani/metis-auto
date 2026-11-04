# Final test report (WP-19)

Opened once through `scripts/eval_test.py`, after tag `pre-test`. The frozen artifact and protocol were unchanged. n = 299 of 300 (1 prompt refused by Jev, left out). Full numbers: `results/final/final.json`.

## Primary
| Comparison (measured, session bootstrap 10,000) | Pass difference (95% CI) | Cost ratio | McNemar p |
|---|---:|---:|---:|
| K = 8 vs always-Sonnet | +2.0 points (-3.0 to +7.1) | 0.042 | 0.50 |
| K = 8 vs always-DeepSeek | -1.7 points (-3.8 to +0.3) | 1.02 | 0.23 |
| K = 4 vs always-Sonnet | +5.4 points (+1.4 to +9.4) | 0.34 | 0.014 |
| K = 4 vs always-DeepSeek | +1.7 points (-1.3 to +4.7) | 8.2 | 0.36 |

**Verdict, K = 8 (the shipped router):** criterion 1 met (95.8% cheaper than Sonnet). Criterion 2 met (lower bound -3.0 vs limit -5). Criterion 3 met (simulated p90 4.4 s vs 8.8 s). **Does not add value over always-DeepSeek.** 89% of its traffic goes to DeepSeek and the rest to Luna, which is weaker here.

Plain reading: routing away from Sonnet saves about 96%, but nearly all of that saving comes from using DeepSeek. On this data the K = 8 router alone did not beat DeepSeek. K = 4 scored the highest pass rate, at about 8 times DeepSeek's cost, and its gain over DeepSeek is inside the noise.

## Pass rates and cost (measured, n = 299)
DeepSeek 68.6% at $0.68 per 1k, Luna 61.9% at $0.84, Gemini 51.8% at $0.41, Sonnet 64.9% at $16.32, K = 8 66.9% at $0.69, K = 4 70.2% at $5.55.

## Secondary
- Area, K = 8 0.686; K = 4 0.697; K = 1 and ZeroRouter 0.684; K-NN 0.681; logistic 0.678. All differences from K = 8 include 0.
- α = 2: no change in choices at this λ. Holdout: adding Gemini from its validation row moved area from 0.680 to 0.686.
- Budget λ points: K = 8 68.6% at $6.11, K = 4 70.2% at $5.55.
- Length terciles: all routers weakest on medium prompts; K = 8 follows DeepSeek. Short: 76.3% vs Sonnet 63.9%. Long: 63.4% vs 67.3%.
- Repeats, n = 60: mean score gap 0.137, 5% flipped pass or fail.
- Production: 52% of prompts ran a model with a list price here, about $0.30 per 1k at DeepSeek token counts. Cosine to production answers: K = 8 0.887, Sonnet 0.872. Similarity is not quality (M15).

## Replay on test (simulated)
With cache and checks: pass 66.9%, $0.72 per 1k, 0 cache hits in 299 sampled prompts, 0.3% escalated. 10-minute DeepSeek outage: 0 failed requests, 21 failovers, pass 65.2%, $0.74 per 1k.

## Deviations
- Area CIs for K-NN, logistic, K = 1 and fixed rows used 2,000 draws, not 10,000; K = 4 and ZeroRouter used 10,000. Primary results used 10,000.
- `category` is empty in the data, so per-category tables were not possible. Per-cluster tables are in the JSON.
- The script's `refused` field prints 0 because the refused prompt has no label rows; n = 299 is correct.
- Always-Sonnet shows area 0 because its only point sits at the top of the cost range; it is not comparable.
- A ruff cleanup of the script does not change numbers.
