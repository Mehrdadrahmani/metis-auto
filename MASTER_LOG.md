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
| D-012 | 2026-10-20 | Full dataset expected soon and large (≥ 5,000 prompts); exact date unknown | A | D-013 | 2026-10-20 | API access through **Metis AI** | A | Q-002 |
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
| D-049 | 2026-10-22 | Jina v5 clustering input = model prompt **"Document: "** + message (model-card and standalone `-clustering` model default `default_prompt_name = document`); passed explicitly as `prompt_name` and part of `embedder_id` | P | WP-03 |
| D-050 | 2026-10-22 | Embedder weights stored in `models/<short>_<rev12>/` (git-ignored), fetched by `scripts/fetch_model.py` (curl, resumable; HF xet download stalled and a network drop lost 1 GB), loaded by local path; revisions pinned (small `dd76d535f544`, nano `8a7f00aac812`). Folder names must be Python identifiers (remote code import). Token-budget batching (`max_batch_tokens` 8,192) after an 11 GB out-of-memory kill | P | WP-03 |
| D-051 | 2026-10-24 | **graphify** (uv tool `graphifyy[pdf]` 0.9.95, project-scoped) = knowledge graph of the whole project (code by local AST, docs/PDFs by the session's own subagents; no external API, no Gemini key). Outputs `graphify-out/` (graph.json, graph.html, GRAPH_REPORT.md committed; cache ignored). `.graphifyignore` excludes data/, cache/, runs/, models/, qdrant/, mlflow/, .env, sealed files. Git hooks (post-commit/checkout/merge/rewrite in `.githooks/`) rebuild the code graph; `/handoff` step 2b refreshes docs when needed; CLAUDE.md tells agents to query the graph before grepping | A | owner |
| D-052 | 2026-10-24 | Embedder: keep **both** jina v5 small and nano as candidates; choose in **WP-08** on real train data (owner). Sample benchmark (`results/wp03_embedder/embedder_benchmark.md`): only nano meets 60 ms p95 at 512 tok (59 ms, adapter merged; small ≈ 220 ms); Persian pair AUC weak with `clustering` (small 0.61, nano 0.66), better with `text-matching` (0.76 / 0.85) → semantic cache uses `text-matching` (`s4.cache_task`). `merge_adapter` added (same vectors, ~2× faster). Owner's cluster verdict on the sample: "partly" (too small to judge). WP-08 step 6 updated | A | owner |
| D-053 | 2026-10-25 | WP-03b follows the **paper's embedding + K-means protocol** with Jina instead of Gecko (owner): random split train 60 % / val 400 / test, 10 repeats; K-means on train only; nearest-centroid assignment; K grid 3..N_val/50 (+ larger K for reference). K choice by deferral area impossible at $0 → label NMI + Khayyam human-difficulty gap (Prop. 2 proxy). Embedding cache keyed by text hash. HF login (`hf auth login`, token in the user's HF cache, never in the repo) for gated Khayyam (access granted) | A | owner |
| D-054 | 2026-10-30 | **Q-024 answered: cluster size follows the paper.** K ∈ {3…⌊N_val/50⌋} is the only limit (50 prompts per cluster *on average*); no per-cluster minimum, no K dropped for small clusters; α = 0 (Eq. 12) stays the default, α = 2 only as a robustness check; a cluster with no val prompts falls back to the model's overall error rate. This confirms D-040 / DEV-7; the "+ α-smoothing" in the Q-024 wording was wrong (it contradicted D-040). PLAN §phase-2 acceptance, WP-08 and WP-14 checks updated | A | owner |
| D-055 | 2026-10-30 | WP-03b closed: owner judged the cluster quality good. No change to the embedder decision: small and nano both stay until WP-08 (D-052); the Persian test did not separate them | A | owner |
| D-056 | 2026-10-31 | **Candidates updated to current models (owner; replaces D-016):** deepseek-v4-flash (unchanged), gpt-5.6-luna (was gpt-4o-mini), gemini-3.5-flash-lite (was gemini-2.5-flash; same price tier, gemini-3.5-flash is about 6× dearer), claude-sonnet-5-5 (was claude-sonnet-4-6; anchor). Prices from third-party trackers, luna and flash-lite roughly match dataset billing; none confirmed on Metis AI (WP-04). Holdout demo model follows gemini. Judge stays GPT-5.x: self-preference flag moves to gpt-5.6-luna | A | owner |
| D-057 | 2026-10-31 | **`workflow` traffic excluded from train, val and test (owner).** Reasons: not a single-model routing decision; bot instructions are a 23-char placeholder, so the task cannot be reproduced or judged; 63 % follow a button or form. Results therefore apply to direct single-model bots only (~73 % of all user messages, ~25 % since Sep). Full criteria: `report/data_selection.md`. Code unchanged (`REASONS_LABELED`, `REASONS_TRAIN`) | A | owner |
| D-058 | 2026-10-31 | Full data loaded through a new streaming parquet loader on DuckDB (`src/metis/data/load_parquet.py`; `uv add duckdb`); structure-only card and full secret scan in `results/wp08_full_data/`. PLAN P4 fallback retired, full data arrived before 2026-11-01 | A | owner |
| D-059 | 2026-10-31 | Judging stays LLM judge only, pointwise vs pairwise in the pilot. Dropped by the owner: reference-answer method, rule-based checks, embedding similarity as a grader. The judge prompt is **not final**: owner reviews it before WP-06 step 4 | A | owner |
| D-060 | 2026-10-31 | Confidence intervals and paired tests resample **whole sessions**, since messages in a session are not independent. WP-05 updated | P | WP-05 |
| D-061 | 2026-10-31 | **Q-020 answered: K is chosen by split-validation on val ($0), not graded train prompts. DEV-6 approved: R = 20.** Fixed rule 6 stays intact | O | WP-05 |
| D-062 | 2026-10-31 | WP-05a readings of the spec: K = 1 is scored but cannot win (M14 over S5); every K uses the same halvings; **halvings keep sessions whole** (follows D-060); the K search uses the Bradley-Terry closed form (the optimizer is tested equal to it); envelope = undominated points joined linearly (spec §7; the paper gives no more detail); an empty pairwise cluster uses the overall rate (D-054); `select_lambda` returns the closest point with `feasible=False` if no λ meets the target | P | WP-05 |
| D-063 | 2026-10-31 | WP-05b: `area()` adds nothing below a curve's cheapest point (bug fix); single models reported by cost and quality, not area; logistic baseline pointwise only; report shows QNC exact and within 1 point | P | WP-05 |
| D-064 | 2026-10-31 | **Q-025 answered: K by the paper's rule, highest score.** One-spread and fixed K = 8 rejected. No deviation. The rule is judged by routing quality; K* is not reported as the number of real topics. Step 9 checks changed accordingly | O | WP-05 |
| D-065 | 2026-10-31 | Owner explicitly confirmed D-061: split-validation with R = 20 (closes Q-026) | O | WP-05 |
| D-066 | 2026-10-31 | **Replaces the store part of D-048:** Qdrant runs as a Docker server (`docker-compose.yml`, image v1.19.1 = client version), loopback only, data in git-ignored `qdrant/`, telemetry off. Reason: the gateway and offline jobs need it at the same time. Local/in-memory modes stay for tests | O | WP-08 |
| D-067 | 2026-10-31 | Owner allows the agent to read small samples of **redacted user prompts** (train, val). Still barred: raw files, `.env`, instructions, RAG context, generated answers, test prompts. AGENTS §4 and CLAUDE.md changed | O | WP-08 |
| D-068 | 2026-10-31 | New order: WP-08 part A (S1, S2, embedder choice, embedding, near-duplicates) first, then WP-04 → 06 → 07 → WP-08 part B (S5, cluster names, budget, Gate 1). Risk accepted: a bug found in WP-07 may mean a free rerun of S1, S2 and S4 | O | WP-08 |
| D-069 | 2026-10-31 | Embedding input stays the current user message (option A; D-045/DEV-8 reviewed). Other inputs compared later on val, never test: T = 2 and chatbot as router input in WP-14; hybrid only if the S1 follow-up count is high | O | WP-08 |
| D-070 | 2026-10-31 | Image rule covers all of provider `imagination` plus `dalle`. Val/test/pilot balanced by RAG yes/no (`s2.balance_field: uses_rag`; a session takes its first eligible prompt's value). Exact repeats matched within `bot_id` because the full data has no category | O | WP-08 |
| D-071 | 2026-10-31 | Embedder = **nano** (owner), all eligible prompts. Agent defaults, not explicitly answered by the owner: the 11 messages over 32,768 tokens are cut at the limit (exception to D-047), and the 569 prompts with `[PLOT_HIDDEN_MEMORY_CONTEXT]` are left as they are. All eligible prompts are selected by flags, so the sealed test file stays closed | O/A | WP-08 |
| D-079 | 2026-11-01 | Owner answers: **D-076 confirmed** (equal chance per message). **Q-027 closed:** near-duplicates stay at 0.95. **K limit:** all of 3 to 20 are scored and reported, only K ≤ 11 can win (`router.k_ship_max: 11`; narrows DEV-10; highest score wins inside 3 to 11, D-064). Stability is the reason: ARI 0.99 or higher to K = 11, 0.60 to 0.84 from K = 12. Cluster names stay a draft until after WP-07 | O | WP-08 |
| D-078 | 2026-11-01 | Bot clusters kept as a later test, not in the main pipeline. Experiment in `experiments/bot_clusters/` (elbow K = 13, silhouette 0.28, ARI 0.82). Owner idea: a bot term in task difficulty; test in WP-14 at $0 (would be DEV-12). Owner also moved WP-08 part B ahead of WP-04, 06, 07 (changes D-068) | O | WP-08 |
| D-077 | 2026-11-01 | **Owner changed the data rule:** the agent may read anything in the data and results, including `instructions`, RAG context and generated answers. Replaces D-067 and D-073. Agent's handling: read through `metis.data.redact` so keys stay masked; test stays sealed under AGENTS.md §6; data text stays out of git, `results/`, `report/`. AGENTS.md §4 and CLAUDE.md updated | O | WP-08 |
| D-076 | 2026-11-01 | Agent decision, to report to the owner: first run drew sessions equally and missed the all-traffic target (val 28.5% business support against about 16% of eligible prompts). Draw changed to **each eligible prompt equally likely**; sessions stay in one split, max 3 per session. Seed unchanged. Judged on val vs eligible; test labels and text not used | P | WP-08 |
| D-075 | 2026-11-01 | Owner said go. **DEV-11:** S2 draws val and test as random whole sessions from all sessions; spec says "most recent period". No RAG balancing, max 3 per session, near-duplicates removed from train at 0.95, val 400 (pilot 100), test 300, seed 20261020 | O / DEV | WP-08 |
| D-074 | 2026-11-01 | Split target: **all traffic**, random whole sessions as in the paper; dates are not to be used to choose splits. Replaces the recent pool and RAG balancing once the owner says go (would be DEV-11). Embeddings and S1 are kept. Date-based proposals from the paper review are withdrawn, as is the 25% bot cap | O | WP-08 |
| D-073 | 2026-11-01 | Owner allows the agent to read the bot `description` field for all 1,830 bots, after redaction. `instructions` stays closed. Lists are in git-ignored `runs/bots/` | O | WP-08 |
| D-072 | 2026-10-31 | **DEV-10:** K candidates are 3 to 20 (`router.k_max: 20`), owner's requirement while testing. Paper rule N_val/50 gives 8 for val 400. Consequence stated to the owner: about 20 val prompts per cluster at K = 20. Spec default stays available (`k_max` unset) | O | WP-08 |

**Deviations waiting for the owner's explicit OK:** DEV-4, DEV-5 (planner proposals; DEV-2, DEV-3,
DEV-6 and DEV-7 agreed; DEV-1 withdrawn).

## 3. Open questions

| ID | Question | Owner | Needed by |
|---|---|---|---|
| Q-028 | Rule for empty clusters: new split has none at K 3 to 20, the fallback stays the overall rate (D-054); confirm in WP-14 | owner | WP-14 |
| Q-001 | Exact arrival date and size of the full dataset | course team | WP-08 |
| Q-006 | What is the `default` model in the data? Not blocking: `workflow` is excluded (D-057); only useful for describing the limitation in the report | owner asks course team | WP-20 |
| Q-007b | Exact deadline date and deliverable format (report/slides/demo/code) | owner | WP-20 (format), now (date) |
| Q-017 | Does Metis AI work from the same network as Claude Code (VPN)? Planner saw TLS resets to metisai.ir on 2026-10-20 (PLAN R17) | owner | WP-04 |
| Q-018 | Metis AI: exact model ids, prices (currency), rate limits, usage and cached-token reporting | WP-04 | WP-08 budget memo |
| Q-022 | GitHub secret scanning / push protection unavailable on the free private repo (HTTP 422). Accept local hook only, or upgrade/make public later? | owner | WP-21 |
| Q-023 | Test the router on public Persian data like the paper (owner idea; the embedding + clustering half is done in WP-03b, the routing half is open): (1) $0 run on persian-llm-eval's per-item results (17–20 models, ~294 items), (2) paid: Khayyam / Persian ARC / PMWP answered by our 4 candidates, exact-match graded (~$1–3, after the full data). Details `ref/docs/persian-datasets.md` | owner | WP-05 (option 1) / WP-14 |
| Q-019 | Approve DEV-4, DEV-5 | owner | WP-06 (DEV-5), WP-11 (DEV-4) |

## 4. Budget ledger

Hard cap: **$60.00**. Per-stage approvals are set at Gate 1 (WP-08) and stored in `configs/budget.yaml`.

| Date | Stage | WP | Approved | Spent | Calls | Note |
|---|---|---|---|---|---|---|
| 2026-10-20 | – | planning | $0 | $0.00 | 0 | Planning estimate: ~$25 (pointwise path) / ~$35 (pairwise), PLAN §7 |
| | **Total** | | | **$0.00** | **0** | |

## 5. Log (newest first)

### 2026-11-01 · WP-08 split redo, part B start (Opus)
- New split: first draw (equal per session) missed all traffic (28.5% support); equal per prompt gives val 16.5% vs 16.0%, RAG 21.0% vs 19.3%. Train 179,185, near-duplicates 52,072, fitted 127,113. Old split in `runs/s2_old`.
- K-means 3..20 refit. Gap at K = 5: 0.43 to 0.05. ARI 0.99 or higher to K = 11, 0.60 to 0.84 from K = 12. No empty val cluster. Qdrant payload updated without re-embedding; snapshot in `qdrant/share/`.
- Added `scripts/s5_stability.py`, `set-split` step, `results/wp08_full_data/char_distribution.*`.
- Bot experiment: elbow K = 13 (soft), silhouette 0.28, ARI 0.82; one bot (Athena) about 37% of messages. Saved for WP-14 (D-078).
- Draft budget memo: real inputs about 2,800 tokens vs 1,640 planned; pointwise $13 / $35 / $73. Decisions D-075 to D-079. Tests 169 passed. Cost $0.

### 2026-11-01 · WP-08 part A review (Opus)
- Reread the paper against the spec. Measured: val vs train gap 0.43 at K = 5; stability about 1.00 up to K = 8, 0.71 to 0.85 at K = 12 and 20.
- Val is 53.8% `b_1724` and 90.2% company support; eligible prompts are 15.8% support. The top bot is also 51.9% of the recent pool, so a bot cap was withdrawn.
- Read 781 unique redacted bot descriptions (D-073); keyword groups in `runs/bots/`.
- Owner chose all traffic (D-074). New split plan written in STATUS; not run. No files in `runs/s2` or Qdrant changed. Cost $0.

### 2026-10-31 · WP-08 part A on the full data (Opus)
- Reordered the work (D-068). Qdrant moved to Docker (D-066). Rules: D-067, D-069 to D-072 (DEV-10).
- S1 streamed in session batches; long context stored in `runs/s1/context/`. S2 balanced by RAG, test sealed.
- Nano vs small on 10,000 train prompts, owner chose nano. 209,162 prompts embedded in 47 min: GPU to
  208,000, CPU for the last 1,162 after a GPU out-of-memory hang. No work lost.
- Near-duplicates: 61,242 of 208,163 train prompts removed (29.4%). K-means K = 3..20 on 146,921 prompts in 8 min.
- Silhouette best at K = 5 (0.118), about 0.09 at K = 6..8, about 0.05 to 0.06 from K = 9.
- Val spreads unevenly: smallest cluster has 10 val at K = 8, 3 at K = 9, 0 from K = 16.
- Sample outputs moved to `runs/sample/`. Tests: 165 passed. Cost $0.

### 2026-10-31 · WP-05 closed (Opus)
- Owner chose highest score (D-064). K* = 3 check replaced by routing quality at K*. WP-05 ticked. Cost $0.

### 2026-10-31 · K rule review (Opus)
- Read the paper's tuning section; ran 4 ways of setting K on 8 scenarios, 100 fresh datasets each.
- My one-spread proposal failed the fresh check: mean area 0.9332 vs 0.9354 (highest score), 0.9360
  (fixed K = 8). Recommendation changed to keep highest score. Simulated data only. Cost $0.

### 2026-10-31 · WP-05b: baselines, statistics, synthetic proof, artifact (Opus)
- New: `eval/baselines.py`, `eval/stats.py`, `router/artifact.py`, `tests/synthetic.py`,
  `tests/test_router_baselines.py`, `tests/test_router_synthetic.py`,
  `scripts/synthetic_validation.py`, `results/wp05_router/`, `work/reports/WP-05-report.md`.
- 161 tests passed, 1 expected failure (K* = 3, Q-025); ruff clean.
- UniRoute minus ZeroRouter area +0.0845 [+0.0520, +0.1178] on planted data, -0.0057
  [-0.0253, +0.0217] with no structure (simulated, n_test = 300).
- Found: the spec's K rule picks K = 3 in 12 of 100 planted datasets (Q-025). Bug fixed in `area()`.
- WP-05 not ticked: waits for Q-025. Synthetic data only. Cost $0.

### 2026-10-31 · WP-05a: router core, steps 2–6 (Opus)
- Owner approved split-validation (Q-020) and R = 20 (DEV-6), D-061; WP-05 split, steps 7–10 are
  now `work/WP-05b-baselines-stats-synthetic.md`.
- New: `router/kmeans.py`, `fingerprints.py`, `bt.py`, `route.py`, `select_k.py`, `select_lambda.py`,
  `eval/metrics.py`, `tests/test_router_core.py`, `tests/test_router_select.py`; `router:` block in
  `configs/pipeline.yaml`; `uv add scipy`.
- Tests: 137 passed (31 new); ruff clean. App. B example, α = 0 = Eq. 12, BT = closed form (< 1e-6)
  and a new model changing only its own column are tested. S9 with R = 20, 7 K values, 61 λ: 0.05 s.
- Found: extra clusters can gain area by luck on no-structure data (WP-05b must measure it).
- Synthetic data only; no real data read. Cost $0.

### 2026-10-31 · Full data arrived; candidates updated (Opus)
- Full dataset downloaded to `data/raw/metis/` (35 parquet files, 1.1 GB; private HF repo, owner-supplied token, not stored). Owner states the data is theirs and has no licence conflict. Q-001 answered: still to be closed at handoff.
- Aggregate EDA only (no text read). Recent traffic (since Sep) is 74.9% `workflow`; owner excluded it (D-057). `report/data_selection.md` written.
- D-056: candidates updated; configs, PLAN, AGENTS and WP-06/09/11/12/14/19 changed. Plan generation estimate now ~$6.0; rest of §7 not recomputed.
- Loader: `src/metis/data/load_parquet.py` + tests. Full read strict: 80,179 sessions, 710,640 messages, 12 s, peak 3.4 GB, no mismatches. A DuckDB setting broke row order (2,009 of 2,000 sessions); removed, guard added.
- Data card `results/wp08_full_data/data_card_full.md`. Secret scan: 1,544 rows hit, 0 left after redaction; includes bot `functions` (3 rows). `chat_message_rag_chunks` not scanned separately (same text as `chat_message.rag`).
- Correction: 700 prompts reach paid models (not 800–900). Tests 106 pass. Cost $0.

### 2026-10-30 · WP-03b close (Opus)
- Owner: cluster quality good; clusters follow the paper (D-054, closes Q-024; D-055). WP-03b finished,
  report `work/reports/WP-03b-report.md`, ROADMAP ticked, Q-023 updated.
- Found the Q-024 wording ("+ α-smoothing") contradicted D-040 (α = 0); decision recorded with α = 0.
- Removed leftover "every cluster ≥ 50" checks from PLAN, WP-08, WP-14; results and LaTeX report updated.
- Cost $0.

### 2026-10-25..28 · WP-03b session part 3 (Opus)
- Data card for the public Persian data; separate Persian clustering report with figures, pipeline
  diagram and cluster-meaning analysis; full LaTeX review (`report/persian_clustering/latex/`,
  tables from `scripts/s4_latex_tables.py`); `results/` tidied into one folder per WP.
- Owner studied the UniRoute paper (metrics Area/QNC, benchmarks, sign test, K choice). Two private
  study PDFs written **outside the project** (`RahnemaCollege2026/uniroute-math/`, not in git): the
  formula version in the paper's notation and a plain router/LLM version. Noted: the paper defines
  Area and QNC only in words; our formulas are a formalisation (marked as such).
- Still at the step-5 ⏸ (owner review, Q-024). Tests 100 pass. Cost $0.

### 2026-10-25 · WP-03b session part 2 (Opus, overnight, owner asleep after OK)
- HF access fixed: `scripts/ext_download.py` sends the HF token (from `hf auth login`) only to
  huggingface.co hosts, never on redirects, curl header via stdin. Owner logged in; Khayyam source added
  (20,805 items, 38 categories, 95 courses). Arena (2,160) and WildChat (3,913) downloads finished.
- `scripts/s4_persian_cluster.py` rewritten to the paper protocol (D-053); new `scripts/s4_cluster_plots.py`
  (K curves, difficulty gap, UMAP maps; interactive local maps in `runs/s4/`). Dev deps: matplotlib,
  umap-learn, plotly.
- Runs: small, nano, nano text-matching on 65,897 unique texts. Results `results/wp03b_persian/persian_clustering.md`:
  paper picture holds (mix clusters well, one topic not, chat in between); small ≈ nano (±0.015 NMI), nano
  2.5× faster; clusters cut the Khayyam human-error gap ~5–6 % (one topic ~0 %); val 400 limits K (gain peaks
  K ≈ 8–16). New Q-024 (S5 cluster-size rule).
- Tests 100 pass. Cost $0.

### 2026-10-24 · WP-03b session part 1 (Opus)
- Owner explained the paper's data: benchmarks with pre-computed answers; asked for Persian data like
  that, then clarified: **only embedding + clustering** now (no model calls, $0); model testing later.
- Searched HF/GitHub/web: no large free Persian set with per-model answers (leaderboards publish only
  totals; Khayyam has questions + answers only). Found labelled Persian benchmarks (Global-MMLU fa,
  INCLUDE, Persian ARC, ParsiNLU, Persian BBH, PerCoR, legal/med QA) and real Persian chats (Arena
  ~2,160, WildChat ~3,600, lmsys 5,431). Gated, requested by owner / to request: Khayyam (pending),
  FarsEval-PKBETS, PEKA.
- New `work/WP-03b-persian-clustering.md`, `scripts/ext_download.py`, `scripts/s4_persian_cluster.py`.
  9 sources downloaded (45K items). Nano interim: benchmark-mix NMI 0.42 (K = 6), Global-MMLU subject
  NMI 0.50 (K = 57). Small 16/41 chunks; chat download partial. Stopped for the owner's break.
- Tests 100 pass. Cost $0.

### 2026-10-24 · WP-03 session part 2 (Opus)
- **graphify** added for the whole project (D-051): uv tool `graphifyy[pdf]` 0.9.95, project skill,
  CLAUDE.md rules, PreToolUse hooks, git hooks (post-commit/checkout/merge/rewrite in `.githooks/`),
  `.graphifyignore` (data/cache/runs/models/qdrant/mlflow/.env/sealed). Full build: 930 nodes, 1,764
  edges, 75 communities; docs/PDFs read by 6 session subagents (~640k tokens of usage, $0); 170
  dangling edges (doc→code name mismatches). `/handoff` step 2b added.
- Step 5 benchmark run on battery (Low Power Mode off; owner said no charger needed): results in
  `results/wp03_embedder/embedder_benchmark.md` + `_small.json` / `_nano.json`. MPS p95 at 512 tok: small 311 ms,
  nano 95 ms. Found the Jina code switches LoRA adapters per call → `Embedder(merge_adapter=True)`
  (same vectors ≤ 4.6e-7, small 221 ms, nano **59 ms**). fp16 adds little.
- Persian pairs AUC with `clustering`: small 0.61, nano 0.66 (fails 0.85 guide); `text-matching`
  0.76 / 0.85 → cache adapter. Clustering adapter puts same-topic pairs together by design.
- Qdrant 17/20 → ties between duplicate messages; check now compares scores (20/20).
- Owner: cluster pages "partly" (sample too small); keep small + nano, choose in WP-08 (D-052;
  WP-08 step 6 updated; `configs/pipeline.yaml` `s4:` block with candidates, choice pending).
- Owner idea: test on public Persian data like the paper → web search → `ref/docs/persian-datasets.md`,
  Q-023 (persian-llm-eval has per-item scores for 17–20 models, MIT, $0).
- Tests: 100 pass (new: merged adapter == unmerged). Cost $0.

### 2026-10-22 · WP-03 session part 1 (Opus)
- Steps 2–4b done: deps (sentence-transformers 6.2, torch 2.14, qdrant-client 1.19, peft, scikit-learn,
  psutil); `src/metis/embed/{embedder,store}.py`; `tests/test_embed.py` (9 tests; 99 total pass);
  `scripts/fetch_model.py`, `scripts/s4_embed_bench.py`, `scripts/data/persian_pairs.yaml` (40
  synthetic pairs written by the agent). D-049, D-050.
- Model facts: small = Qwen3-0.6B-Base (119 languages, Persian expected), 1024-dim, 32K tokens; nano =
  EuroBERT-210M (Persian likely not covered). Smoke test small: Persian paraphrase cos 0.91 vs
  unrelated 0.54; CPU load 7 s (warm).
- Step 5 not valid yet: run 1 killed at 11 GB (fixed); run 2 stopped: battery + Low Power Mode
  (M1 Pro 16 GB), throttled CPU p95 193/373/644 ms (30/200/512 tok). Rerun plugged in. Cost $0.

### 2026-10-21 · WP-02 session (Opus)
- Wrote `src/metis/data/{normalize,lang,rules,prompts,split}.py`, `src/metis/config.py`,
  `configs/{models,pipeline}.yaml`, scripts `s1_ingest.py`, `s2_split.py`, `s1_s2_counts.py`,
  tests (90 pass). Deps added: pandas, pyarrow, pyyaml.
- Sample: 434 prompt rows, 375 LLM replies, 343 eligible val/test, 371 train; huge prompts only
  in workflow turns (0 of 375 LLM replies); widget clicks 14/19 exact; est_tokens_in mean 1,675.
  Dry-run split 60/40/20 reproducible; test ids sealed. `results/wp02_prompts_splits/s1_s2_sample_counts.md`.
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
- Data card on the sample → `results/wp01_data/data_card_sample.md` (+ manifest): all expected counts match
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
