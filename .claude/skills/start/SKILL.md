---
name: start
description: Start a work session on Metis-Auto - read status, roadmap and the current WP, propose the plan, and wait for the owner's OK.
disable-model-invocation: true
---

# /start

1. `STATUS.md` is already in your context (SessionStart hook). If it is not, read it first.
   If the hook said "compaction happened" or "without a handoff", or `.claude/state/needs-handoff`
   exists, read the newest file in `.claude/state/` first.
2. Read the `ROADMAP.md` table and the current WP file (`work/WP-xx-*.md`). Read nothing else yet.
3. Run `git status`. Uncommitted changes from a crashed session? Summarize them.
4. Tell the owner in **≤ 6 plain lines**: where we are, what this session will do (which WP steps),
   whether it costs money, whether it needs the owner, and the 5-hour usage so far (status line).
5. **Stop and wait for the owner's OK** (AGENTS.md fixed point 3). If the WP says "Opus / design",
   use plan mode for the proposal.
6. After the OK, read only the files and sections the WP lists under "Read", then work step by step,
   stopping at every ⏸.
