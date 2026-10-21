# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-21 · by session WP-01

## Now
- Current WP: **WP-02 Prompts, rules, splits** (not started)
- Last step done: WP-01 finished: `src/metis/data/{schema,load,redact,inspect}.py`,
  `scripts/data_card.py`, 48 tests pass; `results/data_card_sample.md` matches all expected counts;
  redaction re-scan 0 (report: `work/reports/WP-01-report.md`)
- **Exact next step:** `/start` → read `work/WP-02-prompts-rules-splits.md` → WP-02 step 1
  (propose, wait for OK). Needs Q-021 answered (embedded text) first.
- Model: default (Opus 5.5)

## Waiting on the owner
- Q-021 (embedded text: user message only, or + 2 previous turns) before WP-02
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
- D-044 MLflow (local) for traces + router run comparison; added to WP-04/14/15/18
- D-043 WP-06: all outgoing text redacted (keys also found in `content` and attachment URLs)
- D-042 redaction pattern set incl. `opaque_value`; D-041 continuity mechanism

## Next WPs that can start
- WP-02 now (needs Q-021); WP-04 and WP-05 in parallel (depend only on WP-00); WP-06 after WP-04
