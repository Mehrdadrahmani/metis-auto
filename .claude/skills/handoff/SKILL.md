---
name: handoff
description: End or pause a Metis-Auto session cleanly - tests, STATUS.md, MASTER_LOG.md, plan updates, report, secret scan, commit and push. Use when the context guard or the 5-hour usage warns, or at the end of a WP.
disable-model-invocation: false
---

# /handoff

1. Finish or cleanly stop the current step. Never leave a half-edited file; let a running long job
   checkpoint first.
2. Run the tests for the touched code (`uv run pytest …`); note pass/fail.
2b. Knowledge graph: the git hooks rebuild the code part of `graphify-out/` on every commit (free,
   no LLM). If docs (`*.md`, `work/`, `ref/`) changed a lot this session, run `/graphify . --update`
   (re-reads only changed docs; uses session usage, no money) and include `graphify-out/` in the commit.
3. Rewrite `STATUS.md` (template in `CONTINUITY.md §3.1`, ≤ 60 lines): done, not done,
   **exact next step** (file + function + WP step number), waiting-on-owner, blockers, money.
   Keep the line `- Current WP: **WP-xx …**` (the status line reads it).
4. Append a dated entry to `MASTER_LOG.md §Log`: what was done, files changed, results, cost.
   New decisions → `§Decisions` with an ID. Spending → `§Budget`.
5. **Adapt the plan:** if a result triggers a row of `PLAN.md §6`, edit the affected
   `work/WP-*.md` files now and log "D-xxx: WP-yy updated because …".
5b. Add report-worthy findings of this session (numbers, decisions, surprises, what didn't work)
   to `report/NOTES.md` under the WP's heading (aggregates only, no content).
6. If the WP is finished: write `work/reports/WP-xx-report.md`, tick it in `ROADMAP.md`, set the
   next WP in `STATUS.md`.
7. `git add` code and docs only (never `data/`, `cache/`, `runs/`, `.env`); the pre-commit hook runs
   the secret scan. Commit `WP-xx: <what> (handoff)` (author Mehrdad Rahmani, from git config);
   `git push`.
8. `date > .claude/state/last-handoff`; `rm -f .claude/state/needs-handoff`.
   Tell the owner in 3 plain lines: what's done, what's next, 5-hour usage left.
