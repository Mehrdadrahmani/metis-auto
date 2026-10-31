# Review: how to set K (Q-025)

Simulated data only: 8 scenarios, 100 fresh datasets each (seeds 5000-5099), 400 val / 300 test.
Script: `scripts/k_rule_review.py`; raw counts: `k_rule_review.json`. Area = mean test area.

| Scenario | True K | Highest score | One spread | Fixed K = 8 | Fixed K = 3 |
|---|---:|---:|---:|---:|---:|
| Clean | 3 | 0.9557 | 0.9569 | 0.9564 | 0.9568 |
| Small gaps | 3 | 0.9098 | 0.9087 | 0.9091 | 0.9085 |
| Overlapping | 3 | 0.9409 | 0.9435 | 0.9419 | 0.9437 |
| Overlap + small gaps | 3 | 0.9031 | 0.9039 | 0.9041 | 0.9040 |
| Clean | 6 | 0.9548 | 0.9525 | 0.9552 | 0.9105 |
| Small gaps | 6 | 0.9043 | 0.8978 | 0.9062 | 0.8838 |
| Overlapping | 6 | 0.9232 | 0.9179 | 0.9245 | 0.8833 |
| Overlap + small gaps | 6 | 0.8910 | 0.8846 | 0.8903 | 0.8725 |
| **Mean** | | **0.9354** | **0.9332** | **0.9360** | 0.9130 |

True K picked, of 100: highest score 7-17 (true K = 3), 30-47 (true K = 6); one spread 88-91 and
17-44; fixed K = 8 never, by design.

Not tested: clusters of very different sizes, gaps smaller than 10% vs 30%, true K above 6, real
data. All rules stop at K = 8. Simulated gaps favour the larger K less than real noise might.

Paper: K is the value with the largest area on the validation set, among 3..N_val/50, using
training-model labels (section "Hyper-parameter tuning"). With no training models it sets
K = N_val/50 directly. The paper states that UniRoute is robust to the choice of K.
Project documents cite this as App. G.2; the heading in the PDF is G.1.

**Recommendation:** keep highest score. One spread is withdrawn.
