# Cache threshold (WP-17, D-121)

Measured on train pairs, n = 350, jev pointwise, pass mark 7, routing vectors (nano, clustering).
Wrong hit: the saved answer fails for the new message while that message's own production answer passes.

| θ | Pairs at or above | Wrong hits | Rate | 95% Wilson |
|---:|---:|---:|---:|---|
| 0.99 | 50 | 4 | 8.0% | 3.2% to 18.8% |
| 0.97 | 100 | 10 | 10.0% | 5.5% to 17.4% |
| 0.95 | 150 | 16 | 10.7% | 6.7% to 16.6% |
| 0.93 | 200 | 28 | 14.0% | 9.9% to 19.5% |
| 0.90 | 250 | 44 | 17.6% | 13.4% to 22.8% |
| 0.85 | 300 | 56 | 18.7% | 14.7% to 23.5% |
| 0.80 | 350 | 70 | 20.0% | 16.1% to 24.5% |

Chosen θ = 0.97: no θ met both limits, so the fallback 0.97 applies and the wrong-hit bound above stands. Pairs in one bin are sampled evenly, so rows at or above θ are not traffic-weighted.

## Second check: text-matching vectors

Measured, n = 350. AUC for telling good hits from wrong hits: routing vectors 0.643, text-matching 0.660.

| Text-matching θ | Pairs | Wrong | Rate | 95% Wilson |
|---:|---:|---:|---:|---|
| 0.99 | 19 | 1 | 5.3% | 0.9% to 24.6% |
| 0.98 | 34 | 3 | 8.8% | 3.0% to 23.0% |
| 0.97 | 47 | 4 | 8.5% | 3.4% to 19.9% |
| 0.95 | 60 | 5 | 8.3% | 3.6% to 18.1% |
| 0.93 | 84 | 5 | 6.0% | 2.6% to 13.2% |
| 0.90 | 110 | 9 | 8.2% | 4.4% to 14.8% |
| 0.85 | 145 | 17 | 11.7% | 7.5% to 18.0% |

The new message's own production answer passes 37.7% of the time, and saved answers 22.3%. Repeat-judging noise also creates some wrong hits.
