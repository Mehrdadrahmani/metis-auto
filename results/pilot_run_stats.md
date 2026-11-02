# Pilot run stats (WP-09)

Measured on 2026-11-02, n = 100 pilot prompts. No text. Confidence intervals and judge decisions: WP-11.

## Calls and spend

Total $5.87 of the $10 pilot limit, 2,361 paid calls, 0 failed calls. Includes the route check.

| Model or judge | Calls | Tokens in | Tokens out | Cost |
|---|---:|---:|---:|---:|
| claude-sonnet-5-5 | 110 | 497,219 | 59,313 | $1.75 |
| deepseek-v4-pro | 103 | 286,847 | 32,156 | $0.28 |
| gpt-5.6-luna | 101 | 245,961 | 21,393 | $0.08 |
| deepseek-v4-flash | 102 | 285,381 | 27,965 | $0.07 |
| gemini-2.5-flash-lite | 104 | 247,926 | 33,043 | $0.04 |
| gpt-5.6-terra (judge) | 514 | 1,162,259 | 65,477 | $3.42 |
| jev-latest (returned jev-1.14.0) | 1,327 | 5,076,321 | 40,980 | $0.23 |

## Answers

500 of 500 ok. Passes: 482 ended under 1,024 tokens, 16 under 2,048, 2 under 4,096. None cut in the end.

| Model | Cut at 1,024 | Mean tokens out | Chars per token out |
|---|---:|---:|---:|
| claude-sonnet-5-5 | 9 | 480 | 1.48 |
| deepseek-v4-pro | 3 | 291 | 2.46 |
| gemini-2.5-flash-lite | 3 | 279 | 2.97 |
| deepseek-v4-flash | 2 | 259 | 2.39 |
| gpt-5.6-luna | 1 | 204 | 2.91 |

Chars per token are from the first pass. Only gpt-5.6-luna and terra report reasoning tokens (0). The others do not report them.

## Judgments

| Run | Records | ok | Mean score | SD |
|---|---:|---:|---:|---:|
| terra pointwise | 500 | 499 | 6.90 | 2.01 |
| jev pointwise | 500 | 500 | 6.81 | 1.71 |
| jev pairwise | 800 | 800 | | |

One terra item failed parsing twice and was dropped (0.2%).

| Model | Terra mean | Jev mean | Jev pairwise score against Sonnet |
|---|---:|---:|---:|
| claude-sonnet-5-5 | 7.28 | 7.01 | anchor |
| gpt-5.6-luna | 7.30 | 6.82 | 0.462 |
| deepseek-v4-flash | 7.06 | 7.01 | 0.435 |
| deepseek-v4-pro | 6.66 | 6.70 | 0.328 |
| gemini-2.5-flash-lite | 6.18 | 6.53 | 0.225 |

Spearman terra against jev, pointwise: 0.709 (n = 499).

Jev pairwise position consistency: 0.755 (n = 400 pairs). Gate 2 needs at least 0.80. By model: gemini 0.82, deepseek-v4-pro 0.80, deepseek-v4-flash 0.70, gpt-5.6-luna 0.70. Letters chosen: B 443, A 291, tie 66.

## Test-retest (salted repeat, n = 20 each)

| Run | Result |
|---|---|
| terra pointwise | exact 0.65, within 1 point 1.00, mean gap 0.35 |
| jev pointwise | exact 0.00, within 1 point 1.00, mean gap 0.108 |
| jev pairwise | same verdict 1.00 |
