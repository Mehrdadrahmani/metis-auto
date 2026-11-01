# AGENTS.md: rules and session protocol for Metis-Auto v2

Applies to every agent working in `metis-auto/` (Claude Code imports it via `CLAUDE.md`).
Owner: **Mehrdad Rahmani** (a student). Talk to him in plain, simple language; keep technical depth
in files. Plan: `PLAN.md`. Route: `ROADMAP.md`. Where we are: `STATUS.md`. Mechanism: `CONTINUITY.md`.

## 1. Session protocol (every session)

**Start** (`/start` does this):
1. `STATUS.md` is in your context (SessionStart hook). If not, read it first.
2. Read the `ROADMAP.md` table and the current `work/WP-xx-*.md`. Nothing else yet.
3. `git status`: uncommitted work from a crashed session? Summarize it.
4. Tell the owner in ≤ 6 plain lines: where we are, what you'll do now (which steps), cost (if any),
   and what you need from him.
5. **Wait for his OK.** Then read only the files/sections the WP lists.

**During:**
- Work step by step through the WP; use the to-do list for the steps of this session.
- Stop at every ⏸ in the WP. Never skip a stop because "it's obviously fine".
- Keep the context small: read sections, not whole files; aggregate before reading results; use a
  subagent for broad searches.
- Watch the status line: at **≥ 60% context** or **≥ 90% of the 5-hour usage**, finish the current step
  and run `/handoff`; don't start a new step.

**End** (`/handoff` does this): finish or cleanly stop the step → run the tests → rewrite `STATUS.md`
(≤ 60 lines; exact next step) → `MASTER_LOG.md` log entry (+ decisions, + budget) → apply
`PLAN.md §6` changes to later WP files → WP report + ROADMAP tick if done → secret scan → commit
(`WP-xx: … (handoff)`, author Mehrdad Rahmani) → push → tell the owner in 3 lines.

## 2. Fixed points (from the owner; never change without asking)

1. `ref/UNIROUTE_PIPELINE.md` is the router spec and source of truth. Deviations are marked
   (DEV-n in `PLAN.md §11`) and the owner decides.
2. **No paid API call before the full dataset arrives.** Free work (code, mocks, dry runs) is fine.
3. **Agree before code:** each session proposes and waits for the OK.
4. **Ask before every paid call or run,** with a cost estimate; the hard budget cap is enforced in
   code (`configs/budget.yaml`, $60).
5. **Secrets:** see §4.
6. **Golden rules of the spec:** the test set is never used for any choice; the train split stays
   unlabeled; fingerprints only from validation; every LLM and judge call cached; seeds recorded.
7. The gateway parts the brief requires (semantic cache, cascade/escalation, failover,
   observability) are part of the project.
8. Plain explanations for the owner. Diagrams in draw.io, pastel style: blue `#dae8fc/#6c8ebf`
   free/offline, orange `#ffe6cc/#d79b00` paid, green `#d5e8d4/#82b366` online, grey
   `#f5f5f5/#666666` maintenance, yellow `#fff2cc/#d6b656` totals/gates; dashed grey group outlines;
   thin black arrows; no title inside images. draw.io CLI: `/opt/homebrew/bin/drawio`.
9. Git commits are authored by **Mehrdad Rahmani**; remote = private GitHub repo `metis-auto`.

## 3. Decisions already made (details in `MASTER_LOG.md §Decisions`)

4 candidates (deepseek-v4-flash, gpt-5.6-luna, gemini-3.5-flash-lite, claude-sonnet-5-5 = premium
baseline/anchor) · judge GPT-5.x class via Metis AI · val 400 / test 300 / cal 100 / pilot 100 ·
clusters from **user text only** · generation with each chatbot's own system prompt, RAG context and
history; prompts > 20,000 chars excluded from labeled sets · slim pilot · categories only for
balancing and reporting · cache threshold method decided in WP-17 · every session uses the default
model (Opus 5.5).

## 4. Secrets and data (strict)

- `data/` holds raw data with **live API keys** (inside `instructions`). **Never** print, `cat`,
  `head` or open data files; never paste their text; never commit `data/`, `cache/`, `runs/`, `.env`.
- **Owner decision D-067:** the agent may read **small samples of redacted user prompts** from train
  and val (through `metis.data.redact`) when it helps. Reading sends them to the model provider of
  this session. Bot `description` may also be read after redaction (D-073). Test prompts stay sealed; prompt text never goes into git, `results/` or `report/`.
- **You (the agent) never read system prompts, `instructions`, retrieved context, generated answers
  or raw data files.** Otherwise work with counts, lengths, hashes, scores and statistics. When a
  human must read such content (labeling, spot checks), write a **local, git-ignored HTML/CSV file**
  and ask the owner to open it.
- Everything sent to an LLM API goes through `metis.data.redact` and the outgoing guard in
  `metis.llm.client` (refuses if a key pattern remains).
- Key patterns: `sk-…`, `sk-ant-…`, `AIza…`, `ghp_…`, `Bearer …`, JWT-like `eyJ….…`, URLs with
  `key=`/`token=`, `api_key=`, `password=`, long hex/base64 strings in quotes.
- `results/` and `report/` contain aggregates only (no prompt or answer text).
- Never print `.env` or any key. Read keys only through `os.environ`.

## 5. Money

- Every paid stage: show the estimate (`scripts/estimate_costs.py`) and the approved amount →
  ⏸ owner says "go" → run through `metis.llm.runner` (cache, budget guard, checkpoints).
- Cheapest model first, claude-sonnet-5-5 last. Stop on anomalies: failures > 5%, cost/call > 2×
  estimate, truncation > 10%, unexpected reasoning tokens.
- Record every spend in `MASTER_LOG.md §Budget`.

## 6. Evaluation integrity

- Test ids and test labels are **sealed** (`*.sealed*`); only `scripts/eval_test.py` (WP-19) opens
  them, once, after the `pre-test` tag.
- No choice (method, K, λ, τ, rubric, thresholds, shipped router, cache θ) is ever made with test data.
- Every reported number says measured/simulated, n, and a CI.

## 7. Code conventions

- Environment: **uv** with the virtual environment **`metis-rahnema`** (`.venv/`, prompt name
  `metis-rahnema`). Add packages only with `uv add` (dev: `uv add --dev`), run with `uv run …`; never
  `pip install` into the system Python; commit `pyproject.toml` and `uv.lock`.
- Python ≥ 3.11 (3.12 used), package `src/metis/`, tests in `tests/` (`pytest`), lint `ruff`. Configs in
  `configs/*.yaml` (each with an id = hash). Seeds: 20261020 unless a config says otherwise.
- Every stage script writes a manifest (inputs hash, config hash, seed, counts, duration, cost).
- Long jobs: resumable, checkpoint every 25 items, safe to kill.
- Prefer reuse (LiteLLM, scikit-learn, sentence-transformers, FastAPI) over custom plumbing.

## 8. When something goes wrong

- Blocked → write it in `STATUS.md §Blockers` and the log, say it to the owner plainly, do the next
  unblocked step or hand off. Never improvise a paid call, a spec change or a test-set peek.
- Results change the plan → follow `PLAN.md §6`, edit later WP files, log a decision.
- A WP is too big → hand off at a clean step; split the WP file (`WP-xxa/b`) if it happens twice.

## 9. Models

All sessions use Claude Code's default model (Opus 5.5 on Pro; owner decision D-027). If the Pro
5-hour limit blocks work often, the owner may switch routine WPs to Sonnet (`CONTINUITY.md §7`).
