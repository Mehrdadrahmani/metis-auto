# Pilot decision (WP-11, Gate 2)

All numbers are measured on the pilot, n = 100 prompts, from `scripts/pilot_decision.py` (seed 20261020, $0). Full tables: `results/pilot_decision.json`.
Judge: jev with history (D-103). Reference: Opus labels, not human (D-098, DEV-14). CIs are 95%.

## Pointwise, pass mark sweep (n = 100, Opus pass rate 0.62)

| τ | Agreement | Balanced | κ | Judge pass rate |
|---:|---:|---:|---:|---:|
| 4 | 0.63 | 0.513 | 0.032 | 0.99 |
| 5 | 0.65 | 0.550 | 0.118 | 0.93 |
| 6 | 0.74 | 0.683 | 0.399 | 0.78 |
| **7** | **0.74** | **0.709** | **0.431** | 0.68 |
| 8 | 0.66 | 0.690 | 0.345 | 0.42 |
| 9 | 0.44 | 0.548 | 0.075 | 0.06 |

τ* = 7. Plain accuracy ties at 6 and 7, and the tie goes to the higher τ, so DEV-4 does not change τ*. Agreement CI 0.65 to 0.82, κ CI 0.24 to 0.62, AUC 0.79 (CI 0.69 to 0.88). Leave-one-out choice of τ gives the same 0.74 and 0.431.

Outside the gate, for context only: adding the 100 Sonnet answers gives 0.77 and κ 0.44 (n = 200). This was not the agreed measure.

Pass rate at τ = 7: flash 0.73, Sonnet 0.72, luna 0.65, deepseek-v4-pro 0.64, gemini 0.57. No ceiling, so τ + 1 is not needed.

## Pairwise (Opus preference non-tie n = 96)

| Measure | Value |
|---|---:|
| Agreement, both orders agree (n = 72) | 0.736 (CI 0.62 to 0.82), κ 0.285 (CI 0.04 to 0.52) |
| Undecided by the judge | 24 of 96; agreement 0.552 if they count as wrong |
| Soft score from Jev probabilities (n = 96) | 0.698, κ 0.284 (CI 0.08 to 0.50) |
| Position consistency (n = 400) | 0.738 (CI 0.69 to 0.78), line 0.80 |
| Model wins when shown second / first | 0.367 / 0.188 |
| Tie rate | 0.087 |

## Separability (D) and stability (C), 4 candidates

| Method | D, K = 1 | D, K = 3 | D, K = 8 | C, K = 3 | C, K = 8 |
|---|---:|---:|---:|---:|---:|
| Pointwise τ = 7 | 0.333 | 0.111 | 0.042 | 0.635 | 0.280 |
| Pointwise τ = 8 | 0.500 | 0.167 | 0.062 | 0.579 | 0.281 |
| Pairwise | 0.500 | 0.278 | 0.062 | 0.823 | 0.575 |
| Pairwise soft | 0.500 | 0.000 | 0.000 | 0.877 | 0.735 |

K = 3 cells hold about 33 prompts and K = 8 cells about 12, so D is low partly from small n.

Cross-evaluation (A), informative, underpowered: K = 3, 20 halvings, mean area ± sd. Pointwise router 0.702 ± 0.034 on pass rate, 0.402 ± 0.066 on win rate. Pairwise router 0.706 ± 0.044 and 0.466 ± 0.041. Not decisive (DEV-3).

## Bias and noise

- Length, pointwise: mean within-prompt ρ 0.008 (n = 100). No flag.
- Length, pairwise: longer answer wins 0.656 (n = 730), but Sonnet is longer in 94.7% of these. When the other model is longer it wins 0.128 (n = 39), against 0.314 when shorter (n = 691). No sign of a preference for length.
- Position, pairwise: strong, see above. Flag.
- Self-preference, luna: 3 over-passed, 4 under-passed (n = 33). Not visible. Gemini is over-passed most: 8 over, 3 under (n = 33).
- Test-retest, before history (n = 20): jev pointwise mean gap 0.108, pairwise same verdict 1.00.
- Rater consistency: 20 re-labels not done (DEV-14).

## Groups, pointwise at τ = 7 (warning signs only)

| Group | Agreement | n | κ |
|---|---:|---:|---:|
| Gemini / flash / luna | 0.667 / 0.765 / 0.788 | 33 / 34 / 33 | 0.35 / 0.40 / 0.51 |
| No context / context | 0.723 / 0.824 | 83 / 17 | 0.39 / 0.64 |
| Instructions ≤ 1k / 1-5k / 5-20k | 0.652 / 0.766 / 0.769 | 23 / 64 / 13 | 0.29 / 0.49 / 0.45 |
| Persian / other | 0.75 / 0.50 | 96 / 4 | 0.45 / 0.00 |

No item had instructions cut.

## Disagreements (26 at τ = 7)

10 under-passed, 16 over-passed. Opus notes exist for 17. Under-passed items are mostly bot-rule behaviour: a required hand-over signal, a required output format, staying in persona. Over-passed items are mostly fit to the bot: too long, too formal or bland for the character, or weak on the actual question.

## deepseek-v4-pro against Sonnet

Mean score gap -0.29 (CI -0.53 to -0.04, n = 100). Pairwise score 0.282. Cost per answer $0.0027 against $0.0156. No Opus labels for this model.

## Rule outcome

- Pointwise has the higher κ (0.431 against 0.285, gap over 0.05).
- Pointwise D is 0.333 at K = 1, 0.111 at K = 3, so it meets D ≥ 0.2 at K = 1 only. Pairwise meets it at both, but fails κ and position consistency.
- Gate 2 for pointwise: agreement 0.74 misses 0.75 by one item, κ passes. Strict result: **fail**, with the CI covering the line.
- Owner decision (D-105): go ahead with pointwise jev, τ = 7, weaker gate on record. No rubric revision and no re-judge.

## Terra against Jev (same Opus labels, n = 99 terra, n = 100 jev)

| Measure | Terra, no history | Jev, no history | Jev, history |
|---|---:|---:|---:|
| Agreement, τ = 7 | 0.667 | 0.680 | 0.740 |
| κ, τ = 7 | 0.268 | 0.360 | 0.431 |
| AUC | 0.727 | 0.727 | 0.789 |

Terra with history was not measured.
