# WP-08 report: full data in, Gate 1

Date 2026-11-02. Cost $0.00. Tests 262 pass. Gate 1 passed.

## Results
- S1, S2, S4 and S5 on the full data: train 179,185, val 400, test 300 (sealed), pilot 100. Details: `results/split_manifest.json`, `results/wp08_full_data/`.
- K-means on all train prompts (D-088). All K 3 to 20 are scored, only K <= 9 can ship (D-089).
- K = 8 names from local Qwen3-8B topics, 500 train prompts per cluster, 23 minutes (D-092). Clusters 0 and 6, about 40% of train, have no clear theme. Other K need new names if chosen.
- Budget (`results/budget_memo.md`, simulated, mid case): pointwise $41.61, pairwise $56.05, high case $59.49 and $78.08.

## Gate 1
Owner approved the pilot at a $10 limit; every other stage stays at $0 until Gate 2 (D-094). Estimate $6.71, terra pointwise only (D-093, DEV-13). Val stays 400 until after the pilot (D-091).

## Open
Paid routes, prices and usage reporting are unproven until the first paid call. Silhouette 0.07 to 0.12: message-only routing may gain little; WP-11 and WP-14 measure it.
