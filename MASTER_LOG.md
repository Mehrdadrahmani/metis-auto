# MASTER_LOG: Metis-Auto v2

The running record. **Short current status is in `STATUS.md`**; this file holds the decision register,
open questions, budget ledger and the dated log. Log entries older than 2 weeks move to
`log/archive/YYYY-MM.md` (leave a 3-line summary). Limit ~300 lines.

## 1. Current status (summary; STATUS.md is authoritative)

- 2026-10-20: planning finished (planner session 1). WP-00 done (bootstrap). Next: **WP-01**.
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
| D-041 | 2026-10-20 | Continuity mechanism installed and tested (status line, SessionStart/UserPromptSubmit/PreCompact/PostCompact hooks, `/start`, `/handoff`); uv env pinned to uv-managed Python (`python-preference = only-managed`, owner chose this over Anaconda); secret-scan regex adjusted: `sk-` only at a word start (false hit on "risk-management"), bare `sk-ant-` dropped (covered by `sk-` rule), doc example `sk-TESTTESTTESTTEST` allow-listed in `.githooks/secret-allowlist` | A | owner, WP-00 |
| D-042 | 2026-10-21 | Redaction (`metis.data.redact`): AGENTS §4 patterns + Slack, AWS, extra GitHub token kinds, signed-URL params (`sig`, `x-amz-*`), names like `X_API_KEY`/`DB_PASSWORD`, `credential` (token/secret = ≥ 16 key chars), `long_token` (quoted ≥ 32, letters+digits, not UUID) and `opaque_value` (≥ 24 letters+digits after `:`/`=`, added after a residual scan found 9 such values in instructions); idempotent; replaces with `[REDACTED:<kind>]` | P | WP-01 |
| D-043 | 2026-10-21 | WP-06 updated: every outgoing text (history, user message, RAG, instructions, judge prompts) goes through `redact_message`, because WP-01 found key hits in `content` (4) and attachment URLs (13), not only in instructions | P | WP-01 |
| D-044 | 2026-10-21 | **MLflow** (local only, SQLite store, UI on 127.0.0.1, telemetry off) for tracing LLM/judge/gateway calls and comparing router-selection runs; chosen over Phoenix (weaker run comparison), Langfuse/Opik (Docker-heavy) and cloud tools (data would leave the machine). Traces hold redacted text only; the agent never reads them. WP-04 (8b), WP-14, WP-15 (5), WP-18 (5) updated; WP-18 dashboard stays for aggregates | A | owner |
| D-045 | 2026-10-21 | **Q-021 answered:** the embedding/clustering input is the **current user message only** (no previous turns), as in the paper; deviation **DEV-8** from spec S1 (T = 2). Generation still uses the real history (M6). WP-02 (step 4), WP-15 (G2), PLAN M5/§11, ROADMAP updated | A | owner |
| D-046 | 2026-10-21 | Judge input = **current user message only** (+ chatbot instructions and RAG context, DEV-5); spec A1/A2 `{context_turns}` dropped → **DEV-9**. Generation keeps the real history (M6). Risk: weaker judging of short follow-ups ("yes, the second one"); report as a limitation. WP-02, WP-06, PLAN §11, WP-20 updated | A | owner |
| D-047 | 2026-10-21 | Embedding input = the **whole** current user message (no 512-token cut); light normalization only (ي→ی, ك→ک, digits, spaces). WP-03 prefers a long-input embedder (e.g. bge-m3, 8,192 tokens) and reports messages over the limit; any truncation needs the owner | A | owner |
| D-048 | 2026-10-21 | Embedder = **jina-embeddings-v5-text-small** (local, `clustering` adapter; nano fallback for latency; CC BY-NC 4.0 noted for the report); vector store = **Qdrant local mode** (K-NN baseline, near-duplicates, semantic cache, gateway lookups; payload ids/numbers only). Nearest-centroid routing unchanged (paper). Light normalization kept (owner OK). WP-03/05/08/15/17, PLAN, ROADMAP updated | A | owner |

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
| Q-022 | GitHub secret scanning / push protection unavailable on the free private repo (HTTP 422). Accept local hook only, or upgrade/make public later? | owner | WP-21 |
| Q-019 | Approve DEV-4, DEV-5, DEV-6 | owner | WP-06 (DEV-5), WP-11 (DEV-4), WP-05 (DEV-6) |

## 4. Budget ledger

Hard cap: **$60.00**. Per-stage approvals are set at Gate 1 (WP-08) and stored in `configs/budget.yaml`.

| Date | Stage | WP | Approved | Spent | Calls | Note |
|---|---|---|---|---|---|---|
| 2026-10-20 | – | planning | $0 | $0.00 | 0 | Planning estimate: ~$25 (pointwise path) / ~$35 (pairwise), PLAN §7 |
| | **Total** | | | **$0.00** | **0** | |

## 5. Log (newest first)

### 2026-10-21 · WP-02 session (Opus)
- Wrote `src/metis/data/{normalize,lang,rules,prompts,split}.py`, `src/metis/config.py`,
  `configs/{models,pipeline}.yaml`, scripts `s1_ingest.py`, `s2_split.py`, `s1_s2_counts.py`,
  tests (90 pass). Deps added: pandas, pyarrow, pyyaml.
- Sample: 434 prompt rows, 375 LLM replies, 343 eligible val/test, 371 train; huge prompts only
  in workflow turns (0 of 375 LLM replies); widget clicks 14/19 exact; est_tokens_in mean 1,675.
  Dry-run split 60/40/20 reproducible; test ids sealed. `results/s1_s2_sample_counts.md`.
- Owner decisions this session: D-045, D-046 (DEV-9), D-047, D-048. No content read. Cost $0.

### 2026-10-21 · WP-01 follow-up (Opus)
- Consistency pass for the report: WP-02 keeps `context_turns` for the judge only (spec A1/A2); START_HERE, ROADMAP.html, PLAN (E10, phase 7, tree), ROADMAP WP-20 row, WP-20 updated (DEV-8, MLflow screenshots, redraw diagrams 02/05). New running file `report/NOTES.md`; `/handoff` step 5b adds report notes each session.
- Owner answered Q-021: embed the current user message only (D-045, DEV-8); WP-02/WP-15/PLAN/ROADMAP updated.
- Owner asked for a UI to see results; compared Phoenix, MLflow, Langfuse, Opik, cloud tools; owner
  chose MLflow (D-044). Plan text updated in WP-04/14/15/18 and ROADMAP; `/mlflow/` git-ignored.
  Nothing installed yet (WP-04). Cost $0.

### 2026-10-21 · WP-01 session (Opus)
- Wrote `src/metis/data/{schema,load,redact,inspect}.py`, `scripts/data_card.py`,
  `tests/test_redact.py`, `tests/test_load.py` (48 tests pass, ruff clean). Text fields are hidden
  from `repr`; loader keeps unknown fields in `extra` and counts turn mismatches.
- Data card on the sample → `results/data_card_sample.md` (+ manifest): all expected counts match
  (100 sessions, 907 messages 465/442, 18 models, 7 providers, 14 attachment / 29 widget / 71 RAG
  messages, 408 instructions, 78 distinct, 33 > 20k chars, 9 distinct > 20k). No unknown fields,
  no turn-count mismatches.
- Redaction hits: 44 (instructions 27, attachment URLs 13, content 4; kinds url_param 19,
  opaque_value 9, credential 5, api_key 4, long_token 4, jwt 3) in 29 messages / 10 sessions.
  Re-scan after redaction 0; the pre-commit key regex finds 3 raw → 0 after. Residual scan of
  high-entropy strings left only 3 distinct hyphenated slugs. D-042, D-043 (WP-06 updated).
- No content was read or printed (counts, masks and hashes only). Cost $0.

### 2026-10-20 · WP-00 session (Opus)
- Tools present, nothing installed: git 2.54.0, gh 2.100.0 (logged in as Mehrdadrahmani), jq 1.6,
  uv 0.13.1; uv downloaded CPython 3.12.15 for `.venv/` (`metis-rahnema`).
- Created skeleton (PLAN §10), `.gitignore`, `.githooks/pre-commit` (tested: fake key blocked, forced
  `data/` file blocked, docs clean), copied plan files + `ref/`, copied sample data unopened to
  `data/raw/sample.json` (ignored), `pyproject.toml` + `uv.lock`, `tests/test_import.py` (1 passed).
- Continuity mechanism written, approved by the owner, enabled; tested in a second session: STATUS
  injected at start, status line wrote `context_pct`, `/compact` produced `precompact-*.md`,
  `compact-*.md`, `needs-handoff`. D-041.
- GitHub: private repo `Mehrdadrahmani/metis-auto`; first commit 18833d8 pushed. Secret scanning not
  available (Q-022). Cost $0.

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
