# MASTER_LOG: Metis-Auto v2

The running record. **Short current status is in `STATUS.md`**; this file holds the decision register,
open questions, budget ledger and the dated log. Log entries older than 2 weeks move to
`log/archive/YYYY-MM.md` (leave a 3-line summary). Limit ~300 lines.

## 1. Current status (summary; STATUS.md is authoritative)

- 2026-10-20: planning finished (planner session 1). No code yet. Next: **WP-00** (bootstrap).
- Full dataset: not arrived ("coming soon, large"). Fallback dates: 2026-11-01 / 2026-11-08.
- Spent: **$0.00** of $60.00.

## 2. Decision register

Status: **F** = fixed by the owner (PLANNING-REQUEST §4) · **A** = agreed with the owner ·
**P** = planner decision (owner may revisit) · **DEV** = deviation from the spec, needs/has owner OK.

| ID | Date | Decision | Status | Source |
|---|---|---|---|---|
| D-001 | 2026-10-19 | `UNIROUTE_PIPELINE.md` is the router spec and source of truth; deviations marked | F | §4.1 |
| D-002 | 2026-10-19 | No paid API call before the full dataset arrives | F | §4.2 |
| D-003 | 2026-10-19 | Agree before code; each session proposes and waits | F | §4.3 |
| D-004 | 2026-10-19 | Ask before every paid call with an estimate; hard cap in code | F | §4.4 |
| D-005 | 2026-10-19 | Secrets: never print/commit/send data or answers; redact; structure-only inspection | F | §4.5 |
| D-006 | 2026-10-19 | Spec golden rules (test never used for choices; train unlabeled; Ψ from val only; all calls cached; seeds) | F | §4.6 |
| D-007 | 2026-10-19 | Gateway parts of the brief are in scope (cache, cascade, failover, observability) | F | §4.7 |
| D-008 | 2026-10-19 | Plain explanations; draw.io pastel style | F | §4.8 |
| D-009 | 2026-10-19 | Commits authored by Mehrdad Rahmani | F | §4.9 |
| D-010 | 2026-10-20 | Session continuity = hybrid: STATUS.md + hooks (SessionStart, UserPromptSubmit guard, PreCompact/PostCompact snapshots) + `/start`, `/handoff` + ROADMAP/WP files + git | A | CONTINUITY.md |
| D-011 | 2026-10-20 | Deadline ~4 weeks (assumed 2026-11-17) | A | Q-007 |
| D-012 | 2026-10-20 | Full dataset expected soon and large (≥ 5,000 prompts); exact date unknown | A | Q-001 |
| D-013 | 2026-10-20 | API access through **Metis AI** | A | Q-002 |
| D-014 | 2026-10-20 | Budget hard cap **$60**; each paid stage approved separately | A | Q-003 |
| D-015 | 2026-10-20 | Human labeling by the owner only (100 cal items + 20 re-labels) | A | Q-004 |
| D-016 | 2026-10-20 | Candidates: deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash, claude-sonnet-4-6 (premium/anchor) | A | Q-005 |
| D-017 | 2026-10-20 | Judge: GPT-5.x class via Metis AI (exact id in WP-04) | A | Q-014 |
| D-018 | 2026-10-20 | Clustering input = user text only, never the system prompt (context turns: open Q-021); instruction-traits test withdrawn | A | Q-008a, revised |
| D-019 | 2026-10-20 | Generation with each chatbot's own system prompt, RAG context, history; turns with system prompt > 20,000 chars excluded from val/test (**DEV-2**) | A / DEV | Q-008b |
| D-020 | 2026-10-20 | Slim pilot: 100 prompts, both methods, owner labels 100; choose by human agreement + separability (**DEV-3**) | A / DEV | Q-010 |
| D-021 | 2026-10-20 | Semantic cache threshold method deferred to WP-17 (decision point) | A | Q-CACHE |
| D-022 | 2026-10-20 | Gateway shown as a small working server + replay of test traffic | A | Q-011 |
| D-023 | 2026-10-20 | Git local + private GitHub repo `metis-auto` | A | Q-009 |
| D-024 | 2026-10-20 | Project folder `RahnemaCollege2026/metis-auto/` | A | Q-015 |
| D-025 | 2026-10-20 | The 4 data categories used only to balance splits and report results, never for routing | A | Q-016 |
| D-026 | 2026-10-20 | Install hooks + `/start` + `/handoff` (owner approves scripts in WP-00) | A | S1 |
| D-027 | 2026-10-20 | All sessions use Claude Code's default model (Opus 5.5 on Pro); fallback to Sonnet for routine WPs only if usage limits bite (replaces the earlier Opus/Sonnet split) | A | S2 (revised) |
| D-028 | 2026-10-20 | Split sizes: val **400**, test **300**, cal 100 ⊂ val, pilot 100 ⊂ val | A | outline |
| D-029 | 2026-10-20 | Baselines built from the same labels, reported for comparison only (superseded by D-040) | P | PLAN M1–M2 |
| D-030 | 2026-10-20 | τ by balanced accuracy; gate = agreement ≥ 75% **and** κ ≥ 0.40 (**DEV-4**) | P / DEV | PLAN M9 |
| D-031 | 2026-10-20 | Judge prompts = spec A1/A2 + chatbot instructions + RAG context + "follows instructions / grounded" criterion (**DEV-5**) | P / DEV | PLAN M10 |
| D-032 | 2026-10-20 | Split-validation repeats R = 20 (**DEV-6**) | P / DEV | PLAN M13 |
| D-033 | 2026-10-20 | Success criteria: ≥ 40% cheaper than always-best, quality CI lower bound ≥ −5 points, p90 latency ≤ always-best | P | PLAN §8.2 |
| D-034 | 2026-10-20 | Freeze artifact + protocol with git tag `pre-test` before opening the test set | P | PLAN M16 |
| D-035 | 2026-10-20 | Agents never read message text/answers; the owner reads content in local HTML files | P | PLAN E13 |
| D-036 | 2026-10-20 | gen_config: temperature 0.3, max_tokens 1024, thinking/reasoning off for candidates | P | WP-06 |
| D-037 | 2026-10-20 | Gateway built on FastAPI + LiteLLM; failover model-to-model, tested by fault injection | P | PLAN E1–E3 |
| D-038 | 2026-10-20 | Fallback dates: 2026-11-01 reduced plan; 2026-11-08 sample-only demo | P | PLAN P4 |
| D-039 | 2026-10-20 | Python environment managed with **uv**; virtual environment named **`metis-rahnema`** (`.venv/` with that prompt name); packages only via `uv add`, run via `uv run` | A | owner |
| D-040 | 2026-10-20 | **Every clustering and routing step as in the UniRoute paper:** UniRoute always ships; Eq. 12 (α = 0); nearest-centroid assignment; K ∈ {3…N_val/50}; K by normalized area under the deferral curve; no instruction traits (DEV-7, DEV-1 withdrawn) | A | owner |

**Deviations waiting for the owner's explicit OK:** DEV-4, DEV-5, DEV-6 (planner proposals; DEV-2 and
DEV-3 and DEV-7 agreed; DEV-1 withdrawn).

## 3. Open questions

| ID | Question | Owner | Needed by |
|---|---|---|---|
| Q-001 | Exact arrival date and size of the full dataset | course team | WP-08 |
| Q-006 | What is the `default` model in the data? (assumed: a workflow step; `provider = workflow`) | owner asks course team | WP-08 |
| Q-007b | Exact deadline date and deliverable format (report/slides/demo/code) | owner | WP-20 (format), now (date) |
| Q-017 | Does Metis AI work from the same network as Claude Code (VPN)? Planner saw TLS resets to metisai.ir on 2026-10-20 (PLAN R17) | owner | WP-04 |
| Q-018 | Metis AI: exact model ids, prices (currency), rate limits, usage and cached-token reporting | WP-04 | WP-08 budget memo |
| Q-020 | K selection: report cards from graded train prompts (paper; ~$14, breaks fixed rule 6) or split-validation on val (spec, $0) | owner | WP-05 |
| Q-021 | Text embedded for clustering: user message only (paper) or + 2 previous turns (spec) | owner | WP-02 |
| Q-019 | Approve DEV-4, DEV-5, DEV-6 | owner | WP-06 (DEV-5), WP-11 (DEV-4), WP-05 (DEV-6) |

## 4. Budget ledger

Hard cap: **$60.00**. Per-stage approvals are set at Gate 1 (WP-08) and stored in `configs/budget.yaml`.

| Date | Stage | WP | Approved | Spent | Calls | Note |
|---|---|---|---|---|---|---|
| 2026-10-20 | – | planning | $0 | $0.00 | 0 | Planning estimate: ~$25 (pointwise path) / ~$35 (pairwise), PLAN §7 |
| | **Total** | | | **$0.00** | **0** | |

## 5. Log (newest first)

### 2026-10-20 · Planner session 1 (Opus)
- Read the kit (brief, spec, proposal, docs, paper notes and key paper sections, diagrams); inspected
  `data.json` by structure only. Findings: categories are named in the data; widget options live on
  bot messages (the user's next message is the click); system prompts are very skewed (p50 3,578
  chars, max 271k; 33 turns > 20k chars); key-like strings inside `instructions`.
- Asked and recorded the owner's answers (D-011…D-028).
- Wrote `CONTINUITY.md`, `PLAN.md`, `ROADMAP.md`, `work/WP-00…21`, `AGENTS.md`, `CLAUDE.md`, this log,
  `STATUS.md`, `PROJECT.md`.
- Checked Claude Code v2.1.304 docs: hooks (SessionStart matchers incl. `compact`, PreCompact can
  block, PostCompact gets `compact_summary`), status line `context_window.used_percentage` and
  `rate_limits.five_hour.used_percentage`, skills in `.claude/skills/<name>/SKILL.md`.
- Metis AI unreachable from this machine (TLS reset) → PLAN R17, Q-017.
- Next: WP-00, in a new session in `metis-auto/`.
