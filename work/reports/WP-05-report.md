# WP-05 report: router core and evaluation library

Status: **code complete, one acceptance check open** (Q-025). Not ticked in ROADMAP.

## What exists
- `router/`: `kmeans`, `fingerprints`, `bt`, `route`, `select_k`, `select_lambda`, `artifact`.
- `eval/`: `metrics`, `baselines` (always-best, always-cheapest, ZeroRouter, K-NN, logistic; one
  interface), `stats` (session bootstrap, McNemar, Wilson, κ, balanced accuracy, Spearman, C, D).
- `tests/synthetic.py`, `tests/test_router_*.py`, `scripts/synthetic_validation.py`,
  `results/wp05_router/synthetic_validation.md`, `manifest.json`.

## Results (simulated data; n_test = 300; 95% CIs from 10,000 session resamples)
- Planted structure, K = 3: UniRoute area 0.9495, ZeroRouter 0.8650, difference +0.0845
  [+0.0520, +0.1178]. K-NN 0.9524, logistic 0.9495.
- No structure: difference -0.0057 [-0.0253, +0.0217], so no false gain.
- Quality within 1 point of the strong model at 3.6% of its cost (ZeroRouter: 94.5%).
- S9 with R = 20, 7 K values, 61 λ: 0.05 s (limit 2 min).

## Acceptance
| Check | Result |
|---|---|
| K* = 3 chosen | **Fails with the spec rule: 12 of 100 datasets (Q-025)** |
| Ψ recovers planted rates | Pass; see the note below on 2 SE |
| UniRoute area > ZeroRouter, CI excludes 0 | Pass |
| No structure: UniRoute ≈ ZeroRouter | Pass |
| No structure: K* = smallest K | **Fails with the spec rule: 22 of 100 (Q-025)** |
| BT = closed form, α = 0 = Eq. 12, anchor row 0.5, App. B, new mock model | Pass |
| Runtime | Pass |

## Findings
1. **The spec's K rule barely identifies K (Q-025).** Extra clusters cut true groups into pieces
   with the same rates, so areas for K = 3..8 differ by less than their noise and the highest score
   is close to a random pick. Routing quality is unaffected (mean change in test area at most
   0.0006), but a large K means fewer prompts per cluster and harder cluster names. The one-spread
   candidate looked better at first (K = 3 in 93 of 100) but failed a fresh check with true K = 6:
   withdrawn, see `results/wp05_router/k_rule_review.md`. Recommended: keep highest score and judge
   it by routing quality, not by finding K. K* must not be read as the number of real topics.
2. **Bug found and fixed:** `area()` gave a model credit at budgets below its cost. Always-best
   showed 0.9533, above every router. Routers reaching the cheapest model were not affected, so the
   K search results did not change. Single models are now reported by cost and quality only.
3. **Exact QNC is fragile.** UniRoute matches the strong model's true rate but scored one prompt
   lower in 300, so QNC says 1.000 (never reached). The report shows QNC within 1 point as well.
   Decide before the `pre-test` tag which one the protocol uses.
4. **"Ψ within 2 SE" read as a share:** with 12 cells, one beyond 2 SE is expected by chance. The
   test asks for at least 75% within 2 SE and all within 3 SE.

## Spec readings (D-062, D-063)
K = 1 scored but cannot win; sessions kept whole in halvings; closed form in the K search; envelope =
undominated points joined linearly. Logistic is pointwise only (ties are not binary). McNemar treats
prompts as independent; the session bootstrap is the main interval (D-060).
