# WP-21: Reproducibility check and release

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-21-release.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 7 | default (Opus 5.5) | ~100k | final OK; copy of `cache/` if the clone is on another folder | $0 | WP-20 | – |

## Context
Prove the result can be reproduced without new spending, and leave the repository clean and safe.

## Read (only these)
- `README` draft (if any), `PLAN.md` §10 (layout), `CONTINUITY.md` §8 step 4 (secret scan).

## Steps
1. Propose; ⏸ wait for OK.
2. Fresh clone into a temp folder; copy `data/` and `cache/` (local only); create the env; run the
   pipeline S1→S12 and `scripts/eval_test.py` with `METIS_ASSERT_NO_NEW_CALLS=1` → identical result
   hashes, **0 new calls, $0**.
3. Secret scan of the whole git history (`git log -p | grep -E <patterns>` and a scan of `results/`
   and `report/` for message text patterns): 0 hits.
4. `README.md`: what it is, how to run the gateway, the replay, the dashboard, the tests; where the
   results are; what is not in git (data, cache) and why.
5. Final budget line in MASTER_LOG; close open questions; archive old log entries.
6. Tag `v1.0`; push; tell the owner what's in the release.

## Outputs
- `README.md`, tag `v1.0`, `work/reports/WP-21-report.md`.

## Acceptance checks
- [ ] Reproduction identical with 0 new calls; secret scan clean; tests green.

## If blocked
- Non-determinism found → document which numbers vary and by how much; fix seeds if possible.

## End of session
- STATUS: "project complete"; ROADMAP all ticked.

## If the context is getting full
`/handoff` with the next step, stop.
