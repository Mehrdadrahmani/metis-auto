# CONTINUITY: how work carries over from one session to the next

**Decision (2026-10-20, agreed with the owner):** a **hybrid**. A small automatic mechanism keeps
track of *where we are* (approach A), and a fixed list of work packages with ready-made instructions
says *what to do* (approach B).
Checked against Claude Code **v2.1.304** (installed on the owner's Mac) and its current docs
(hooks, status line, skills; fetched 2026-10-20).

---

## 1. The problem in one paragraph

The project needs ~22 work sessions in ~4 weeks. Each session starts with **no memory**. A long
session can be **auto-compacted** (details lost), can **end suddenly** (Pro usage limit, crash, laptop
closed), and results keep **changing later steps**. We need the next session to know exactly where we
are, what was decided and what to do next, **without the owner re-explaining anything**.

---

## 2. Options compared

### 2.1 What exists today (checked)

| Tool | What it does | Verdict for us |
|---|---|---|
| `CLAUDE.md` + `@` imports | Loaded automatically into every session in the folder | **Use.** Carries rules and pointers; keep it short |
| `claude --continue` / `--resume` | Re-opens an earlier conversation | **Extra only.** Brings back a long, possibly compacted history; restarts with a big context; useless after `/clear` |
| Auto-memory (`~/.claude/projects/.../memory/`) | Claude saves notes per project on the local machine | **Don't rely on it.** Lives outside the project and git, not reviewable, can go stale |
| Skills / slash commands (`.claude/skills/<name>/SKILL.md`) | Reusable instructions run by `/name` | **Use:** `/start`, `/handoff` |
| Hook `SessionStart` (matchers `startup`, `resume`, `clear`, `compact`) | Runs a script at session start; its output is injected as context | **Use:** auto-loads `STATUS.md`, also right **after a compaction** |
| Hook `PreCompact` (`manual`, `auto`) | Runs before compaction; can block it | **Use:** saves a safety snapshot (does not block; see §4.4) |
| Hook `PostCompact` | Receives the generated `compact_summary` | **Use:** saves the summary to a file so nothing is silently lost |
| Hook `UserPromptSubmit` | Runs on each user message; can add context | **Use:** "context guard": warns Claude at ≥ 60% context to finish and hand off |
| Hook `Stop` / `SessionEnd` | End of turn / end of session | Not needed. `SessionEnd` has only ~1.5 s and can't ask Claude to write anything |
| Status line (`context_window.used_percentage`, `rate_limits.five_hour.used_percentage`) | A bar at the bottom of the terminal, fed with session data | **Use:** shows context % and Pro 5-hour usage; also writes context % to a file for the guard |
| Subagents | Run a narrow task in their own context | **Use sparingly** (e.g. a big search), to save main context |
| Plan mode | Claude proposes before acting | **Use** at the start of each work package ("agree before code") |
| Built-in to-do list | Tracks steps inside one session | **Use inside a session**; not a cross-session record |
| git commits (+ private GitHub) | Durable history of what changed | **Use:** one commit per handoff, plus a backup on GitHub |
| GitHub Issues / Linear | Issue trackers | **Skip.** One person; `ROADMAP.md` does the same with zero setup and is read by the agent directly |
| Spec-driven agent workflows (spec → tasks frameworks) | Generate task lists from specs | **Skip.** Our spec and work packages already play this role; another framework adds files to read |
| Memory servers (MCP) | External long-term memory | **Skip.** Opaque, not in git, setup cost; plain files are more reliable |

### 2.2 A (mechanism) vs B (pre-defined sessions) vs hybrid

| Criterion | A only | B only | **Hybrid (chosen)** |
|---|---|---|---|
| Next session knows where we are | Good (status file) | Weak if a session stopped halfway | **Good** |
| Owner's manual work | Low | Paste a prompt each time | **Lowest:** open the folder, type `/start` |
| Setup effort | ~1 hour (one work package) | None | ~1 hour (WP-00) |
| Session ends early / compaction | Good (handoff + hooks) | Poor (the prompt assumes a clean start) | **Good** |
| Plans change after results | Good | Poor (prompts go stale) | **Good:** WP files are edited by the session that learns something |
| Clear route, nothing forgotten | Weak (no fixed list) | Good | **Good** (`ROADMAP.md`) |
| Fits Claude Code on Pro | Yes | Yes | Yes |

**Why the hybrid:** B alone breaks the first time a session stops in the middle or a result changes
the plan. A alone gives no fixed route through 4 weeks of work. The hybrid uses `ROADMAP.md` + `work/WP-*.md`
for the route and `STATUS.md` + hooks + `/handoff` for the position on it.

---

## 3. The files (in the project folder `metis-auto/`)

Facts live in **one** place. "Every session" files are short; everything else is read on demand.

| File | Holds | Size limit | Read when |
|---|---|---|---|
| `CLAUDE.md` | Imports `@AGENTS.md`; 5 lines of pointers | 15 lines | Auto, every session |
| `AGENTS.md` | Rules, golden rules, session protocol | ~150 lines | Auto (imported), every session |
| `STATUS.md` | **Where we are:** current WP, last step done, exact next step, blockers, money spent/cap, waiting-on-owner items | **≤ 60 lines** | **Auto-injected by the SessionStart hook** |
| `ROADMAP.md` | All work packages, status ticks, dependencies, what's next | ~120 lines | `/start` reads the table only |
| `work/WP-xx-*.md` | Instructions for one work package | ~150 lines each | Only the current one |
| `work/reports/WP-xx-report.md` | What a WP produced: numbers, decisions, surprises | ~100 lines | When a later WP lists it under "read" |
| `MASTER_LOG.md` | Decision register, open questions, budget ledger, dated log (last ~2 weeks) | ~300 lines; older log → `log/archive/YYYY-MM.md` | Only the sections a WP names |
| `PLAN.md` | Design decisions, phases, results→changes table, budget, risks | reference | Only named sections |
| `PROJECT.md` | Newcomer overview, file map, glossary | reference | First session or when lost |
| `CONTINUITY.md` | This file | reference | When the mechanism itself needs fixing |
| `ref/` | Copied inputs: spec, proposal, docs, paper | reference | Only named sections, never "all" |
| `.claude/state/` (git-ignored) | Context %, compaction snapshots and summaries | small | By hooks; by `/start` if a compaction happened |

**Size rules.** If `STATUS.md` exceeds 60 lines, move detail into the WP report or `MASTER_LOG.md`.
When `MASTER_LOG.md` passes ~300 lines, move log entries older than 2 weeks to
`log/archive/YYYY-MM.md` and leave a 3-line summary.

### 3.1 `STATUS.md` template

```markdown
# STATUS (read first; ≤ 60 lines)
Updated: 2026-10-21 14:05 · by session WP-02

## Now
- Current WP: WP-02 Prompt builder + hard rules + splits (in progress, step 5 of 9)
- Last step done: widget-click detector + tests pass (tests/test_rules.py)
- **Exact next step:** step 6, Persian normalization (work/WP-02 §Steps 6), start from src/metis/data/normalize.py
- Model: default (Opus 5.5)

## Waiting on the owner
- (none) | e.g. "approve budget memo work/reports/WP-08-report.md §Budget"

## Blockers / open issues
- Full dataset not arrived (Q-001); WP-08 blocked

## Money
- Spent $0.00 of cap $60.00 (ledger: MASTER_LOG.md §Budget)

## Recent decisions (last 3; full list in MASTER_LOG.md §Decisions)
- D-012 2026-10-21: huge-prompt threshold = 20,000 chars (WP-02)

## Next WPs that can start
- WP-03 (needs WP-01), WP-04 (no deps), WP-15 (needs WP-02)
```

---

## 4. The mechanism

### 4.1 Commands (skills)

**`/start`** (`.claude/skills/start/SKILL.md`, `disable-model-invocation: true`)

1. `STATUS.md` is already in context (hook). If the hook output says "compaction happened" or
   "handoff missing", read the newest file in `.claude/state/` first.
2. Read the `ROADMAP.md` table and the current WP file (`work/WP-xx-*.md`). Read nothing else yet.
3. Check `git status`: uncommitted changes from a crashed session? Summarize them.
4. Say to the owner, in ≤ 6 plain lines: where we are, what this session will do (which steps of the
   WP), whether it costs money, whether it needs the owner, and the 5-hour usage so far.
5. **Stop and wait for the owner's OK** (fixed point 3: agree before code). Use plan mode for the
   proposal if the WP says "Opus / design".
6. After the OK, read only the files and sections the WP lists under "Read", then work.

**`/handoff`** (`.claude/skills/handoff/SKILL.md`, `disable-model-invocation: false`, so Claude may
run it on its own when the guard warns)

1. Finish or cleanly stop the current step (never leave a half-edited file; if a long job is
   running, let it checkpoint).
2. Run the tests that exist for the touched code; note pass/fail.
3. Rewrite `STATUS.md` (template §3.1): done, not done, **exact next step** (file + function +
   WP step number), waiting-on-owner, blockers, money.
4. Append a dated entry to `MASTER_LOG.md §Log`: what was done, files changed, results, cost.
   New decisions → `§Decisions` with an ID. Spending → `§Budget`.
5. **Adapt the plan:** if a result triggers a row of `PLAN.md §Results → changes`, edit the affected
   `work/WP-*.md` files now and log "D-xxx: WP-yy updated because …".
6. If the WP is finished: write `work/reports/WP-xx-report.md`, tick it in `ROADMAP.md`, set the
   next WP in `STATUS.md`.
7. Run the secret scan, then `git add` (code, docs; never `data/`, `runs/`, `.env`) and commit
   `WP-xx: <what> (handoff)` authored by Mehrdad Rahmani; `git push` to the private GitHub repo.
8. Write `.claude/state/last-handoff` (timestamp). Tell the owner in 3 lines: what's done, what's
   next, and the 5-hour usage left.

### 4.2 Hooks (`.claude/settings.json`)

```json
{
  "statusLine": { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/statusline.sh" },
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume|clear|compact",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/session-start.sh", "timeout": 10 } ] }
    ],
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/context-guard.sh", "timeout": 5 } ] }
    ],
    "PreCompact": [
      { "matcher": "manual|auto",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/pre-compact.sh", "timeout": 20 } ] }
    ],
    "PostCompact": [
      { "matcher": "manual|auto",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/post-compact.sh", "timeout": 20 } ] }
    ]
  }
}
```

What each script does (WP-00 writes them; each ≤ 30 lines of bash + `jq`; the owner reviews them
before they are enabled):

| Script | Behavior |
|---|---|
| `statusline.sh` | Reads the JSON on stdin. Prints `[model] ctx 37% · 5h 22% · WP-02` (current WP read from line 4 of `STATUS.md`). Writes `context_window.used_percentage` to `.claude/state/context_pct`. Colors: green < 50%, yellow 50–60%, red ≥ 60% |
| `session-start.sh` | Prints `STATUS.md` (≤ 60 lines, so well under the 10,000-character hook limit) as `additionalContext`, phrased as facts. Adds a line if `source` = `compact` ("A compaction happened at …; the summary is in .claude/state/compact-….md; run /handoff before new work") or if there are uncommitted changes and no handoff newer than the last commit ("Previous session ended without a handoff; check git status") |
| `context-guard.sh` | Reads `.claude/state/context_pct`. ≥ 60%: injects "Context is at N%. Finish the current step, then run /handoff; don't start a new step." ≥ 75%: "Run /handoff now." |
| `pre-compact.sh` | Saves `git status --short`, `git diff --stat`, the current time and the `STATUS.md` line "Exact next step" to `.claude/state/precompact-<ts>.md`. **Does not block** |
| `post-compact.sh` | Saves `compact_summary` to `.claude/state/compact-<ts>.md` and touches `.claude/state/needs-handoff` |

### 4.3 Status-line thresholds

With 1M context, "60%" is ~600k tokens, far more than any WP should need (§6). So the practical
trigger is usually **the end of the WP**, not the guard. The guard is the safety net for a WP that
grows unexpectedly. The **5-hour Pro usage** (`rate_limits.five_hour.used_percentage`) is also on
the status line: at ≥ 90%, run `/handoff` instead of starting a new step, because a session cut off
by the limit can't write its own handoff.

### 4.4 Why `PreCompact` does not block

Blocking a *proactive* auto-compaction keeps the session running uncompacted, but blocking one
triggered by a context-limit error makes the request fail. A hook cannot write a good handoff (only
Claude can), so the design is: the guard makes Claude hand off **before** compaction is ever needed;
if it happens anyway, the snapshot + saved summary + the `compact` SessionStart message make the
next step recoverable.

---

## 5. The exact start and end of a session

### Start (owner: 2 actions)

1. Open a terminal in `metis-auto/`, run `claude` (the default model, Opus 5.5 on Pro).
2. Type **`/start`**. Read the ≤ 6-line proposal; answer "ok" or correct it.

Claude does the rest (§4.1).

### End (owner: 1 action, often 0)

- Claude runs `/handoff` by itself when the WP is done, the guard fires, or the 5-hour usage is
  ≥ 90%. Otherwise the owner types **`/handoff`**.
- Then close the session (or `/clear` and `/start` again for the next WP; a fresh context per WP is
  cheaper than continuing).

### If something went wrong

| Situation | What happens |
|---|---|
| Session died without a handoff | Next `/start` sees uncommitted changes + no recent handoff; it reconstructs from `git diff`, the WP file and `.claude/state/`, writes the missing log entry, then proposes |
| Auto-compaction happened | SessionStart(`compact`) re-injects `STATUS.md` and points to the saved summary; Claude runs `/handoff`, then the owner starts a fresh session |
| A long paid job was interrupted | Every call is cached (key = prompt, model, config hash); the runner checkpoints every 25 items; re-running resumes at the first missing item at $0 for finished items |
| A WP turns out too big | At the guard or at a natural break: `/handoff` with "WP-xx part 2" as the next step; if this happens twice, split the WP file into `WP-xxa`/`WP-xxb` and log it |
| Results change the plan | `/handoff` step 5 edits the affected WP files and logs a decision; `ROADMAP.md` is updated if order or dependencies change |
| The hooks break | Fallback B: each WP file starts with a one-line "paste prompt"; the owner pastes it into a fresh session |

---

## 6. Work-package sizing

| Rule | Value |
|---|---|
| Target size of one WP session | **100k–250k tokens** (10–25% of the 1M window) |
| Reading budget at start | ≤ 40k tokens (STATUS + AGENTS + WP file + named sections) |
| Guard | 60% warn, 75% hand off now |
| Never read in full | `ref/UNIROUTE_PIPELINE.md` (~30 KB: read only the named §), the paper (read only named pages), `data/**/*.json` (never print; structure scripts only), large result files (aggregate first) |
| Bigger than planned | Hand off and split (§5) |

Token estimates per WP are in `ROADMAP.md`.

## 7. Which Claude model

**Decision (owner, 2026-10-20): every session uses Claude Code's default model** (Opus 5.5 on the
Pro plan); no `--model` flag needed. Opus is the strongest choice for the statistics, design and
review work, and one model everywhere removes a choice per session.

Trade-off: Opus uses the Pro 5-hour limit faster. If the limit stops work more than about once a day,
switch the routine WPs (WP-01, 02, 04, 07, 09, 12, 13, 15–18, 21) to Sonnet with `/model sonnet`
and log the change in `MASTER_LOG.md`. Subagents for narrow searches may use a lighter model.

---

## 8. Setup (done in WP-00; the owner approves before anything is installed)

1. Create `RahnemaCollege2026/metis-auto/`; `git init`; set `user.name "Mehrdad Rahmani"` and the
   owner's email locally.
2. Create a **private** GitHub repo `metis-auto` (`gh repo create --private`, owner logs in with
   `! gh auth login` if needed); add it as `origin`.
3. `.gitignore`: `data/`, `runs/`, `cache/`, `.env`, `*.env`, `.claude/state/`, `.DS_Store`,
   `__pycache__/`, `.venv/`.
4. Pre-commit secret scan (a small script in `.githooks/pre-commit`; `git config core.hooksPath
   .githooks`): blocks commits containing key patterns (`sk-`, `sk-ant-`, `AIza`, `ghp_`,
   `Bearer `, JWT-like strings) or any file under `data/`. Also enable GitHub secret scanning / push
   protection on the repo.
5. Copy the planning outputs (`PLAN.md`, `ROADMAP.md`, `work/`, `AGENTS.md`, `CLAUDE.md`,
   `MASTER_LOG.md`, `PROJECT.md`, `CONTINUITY.md`, `STATUS.md`, `diagrams/`) into the project root,
   and the kit's inputs into `ref/` (spec, proposal, docs, diagrams, paper). Never copy `data.json`
   into git. It is copied to `metis-auto/data/raw/` (git-ignored).
6. Write `.claude/settings.json`, the 5 scripts (§4.2) and the 2 skills (§4.1); `chmod +x`; check
   that `jq` is installed (`brew install jq` if not, owner approves).
7. **Test the mechanism:** open a new session → the status line shows; `STATUS.md` appears in
   context; `/start` proposes WP-01; run `/compact` manually once in a scratch session → the snapshot
   and summary files appear; `/handoff` commits and pushes.
8. Log `D-xxx: continuity mechanism installed and tested` in `MASTER_LOG.md`.
