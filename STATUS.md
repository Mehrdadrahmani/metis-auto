# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-21 · by session WP-01/WP-02

## Now
- Current WP: **WP-03 Embedder + Qdrant** (not started)
- Last step done: WP-02 finished: S1 prompts table, hard rules, S2 splitter, configs, 90 tests
  pass; sample dry run → `results/s1_s2_sample_counts.md` (report: `work/reports/WP-02-report.md`)
- **Exact next step:** `/start` → read `work/WP-03-embedder-choice.md` → WP-03 step 1 (propose,
  wait for OK; mentions the model download, Jina v5-text-small ≈ 1.4 GB + nano)
- Model: default (Opus 5.5)

## Waiting on the owner
- Q-017 (VPN / Metis AI reachability) before WP-04; Q-020 (K selection) before WP-05
- Approve DEV-4, DEV-5, DEV-6 (MASTER_LOG §2) when convenient

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 and everything paid wait for it
- Metis AI unreachable from the planner's network (PLAN R17)
- GitHub secret scanning / push protection not available on this free private repo (HTTP 422);
  protection = local `.githooks/pre-commit` only (Q-022)

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §4)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-048 Jina v5-text-small (local, clustering adapter; nano fallback) + Qdrant local mode
- D-047 embed the whole message; D-046 / DEV-9 judge sees the current message only
- D-045 / DEV-8 embedding input = current user message only; D-044 local MLflow

## Next WPs that can start
- WP-03 now; WP-04 and WP-05 in parallel (depend only on WP-00); WP-06 after WP-04
