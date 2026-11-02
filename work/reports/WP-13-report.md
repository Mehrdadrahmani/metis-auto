# WP-13 report: judging

Date 2026-11-02. Cost $0.58 of the $1 approved. Pointwise jev with history, τ = 7, judge config id 356e63e52245, returned version jev-1.14.0 on every call.

| Set | Slots | Scored | Failed answer | Refused by Jev | Repeats | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Val | 1,600 | 1,595 | 1 | 4 (1 prompt, all 4 models) | 80 | $0.28 |
| Test | 1,200 | 1,196 | 0 | 4 (1 prompt, all 4 models) | 60 | $0.30 |

Refused items stayed at error 400 on every retry. They have no label, 0.25% and 0.33%, under the 2% limit. The cause is not confirmed: the val prompt is very long.

Val results: `results/s7_stats.md`, `results/val_vs_pilot.md`. Val repeat: mean gap 0.147, n = 80.

Test scores, labels and repeats are in `runs/s7/*.sealed*`. No test score was read and no test metric computed. `scripts/s7_stats.py --set test` prints row counts only. The test repeat comparison waits for WP-19, so the judge noise on test is still unknown.

Limits: labels rest on a judge that missed Gate 2 by one item, against Opus labels.
