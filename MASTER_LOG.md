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
| D-080 | 2026-11-01 | **Candidate replaced (owner; updates D-056):** gemini-2.5-flash-lite replaces gemini-3.5-flash-lite, for a wider quality spread at lower cost. Keeps the holdout role. Price not yet confirmed. Calibration names in `runs/s2` still use the old id until the free split rerun in WP-07 | O | AGENTS §3, PLAN M3 |
| D-081 | 2026-11-01 | Jev (`jev-latest`, TypeSafe, on Metis) kept as a judge option (owner: "may use"). Not chosen; needs an adapter. Decide before WP-09 | O | configs/models.yaml |
| D-082 | 2026-11-01 | Sonnet stays the candidate and anchor for now. deepseek-v4-pro joins the pilot as a cheaper comparison; WP-11 decides whether it replaces Sonnet (saves about $3.55 of generation). The pilot is 5 models, not 4 | O | WP-09, WP-11 |
| D-083 | 2026-11-01 | Pilot judges: gpt-5.6-terra and jev-latest side by side on the same answers; WP-11 keeps the one that agrees better with the owner's labels, the cheaper on a tie. Metis prices recorded (WP-04 step 10) | O | WP-09, WP-11 |
| D-084 | 2026-11-01 | No temperature or top_p for any candidate: claude-sonnet-5-5 answers 400 to non-default values, so all models run at their defaults alike. Replaces the planned 0.3 | O | configs/gen_config.yaml, WP-06 |
| D-085 | 2026-11-01 | DEV-5 approved: judge prompts as in `src/metis/judge/templates/`, including an added line not to follow instructions inside the evaluated text | O | WP-06 report |
| D-086 | 2026-11-01 | Jev form approved: same material as `state`, one score or choice question, level mapped by 1 + 2.25 × level (not rounded). Jev-only wording: "caps the answer at level 1". No written reason | O | src/metis/judge/render.py |
| D-087 | 2026-11-01 | Later WPs updated: WP-08 recomputes the budget (estimate above the $45 line, PLAN §6); WP-09 checks provider params first; WP-11 splits agreement by context and instruction length; WP-12 adds test selection; WP-13 adds the 5% re-judge | C | WP-08, 09, 11, 12, 13 |
| D-088 | 2026-11-02 | **Near-duplicates are kept (owner).** Replaces the 0.95 removal in D-075 and D-079: K-means fits on all train prompts (179,185 on the current split). Exact duplicates are still removed. Frequent messages now weigh more in the clusters. K limit, stability and cluster names need a rerun in WP-07 | O | WP-07, WP-08 |
| D-089 | 2026-11-02 | **K limit is now 9 (owner).** Replaces K ≤ 11 in D-079: after D-088, mean ARI is 0.99 or higher to K = 9, then 0.89 at K = 10 and 0.85 at K = 11 (three fits each). All of 3 to 20 are still scored and reported, only K ≤ 9 can win (`router.k_ship_max: 9`) | O | WP-14 |
| D-090 | 2026-11-02 | No S1 rules bug exists on record: the STATUS and CHECKPOINT note came from the D-068 risk line, `rules.py` is unchanged since S1 and its tests pass. Note removed. WP-08 cluster names must be redone on the D-088 clusters. PLAN §7 high is exceeded (WP-07 acceptance not met), decide at Gate 1 | A | WP-08 |
| D-091 | 2026-11-02 | **Val stays 400 for now (owner); size decided after the pilot, at Gate 2.** A larger val adds sessions from train and never changes `n_val`, because that would redraw test. Owner also chose local Qwen3-8B for a topic sample per cluster | O | WP-08, WP-11 |
| D-092 | 2026-11-02 | K = 8 cluster names kept for now (owner), marked as based on local Qwen3-8B topics (500 train prompts per cluster, 23 min, $0): `configs/cluster_names.yaml`. Other K need new names if chosen in WP-14 | O | WP-08, WP-14 |
| D-093 | 2026-11-02 | **Pilot: gpt-5.6-terra pointwise only for now (owner), jev-latest both methods (DEV-13, narrows spec "method = both" and D-083).** Saves $8.57; pilot estimate $6.71. Terra pairwise can be added later, answers are cached. Method comparison uses jev. WP-09, WP-11 updated | O | WP-09, WP-11 |
| D-094 | 2026-11-02 | **Gate 1 passed (owner).** Pilot limit $10 in `configs/budget.yaml`; gen_main, judge_main, cache_labels and live stay $0 until Gate 2, then set from measured costs. Pointwise stays the planned path | O | WP-09, WP-11 |
| D-103 | 2026-11-02 | Pilot re-judged by Jev with chat history, pointwise and pairwise (owner). $0.29 by ledger. Results in `runs/s7_history/`; old ones kept in `runs/s7/`. Use the history results from now on | O | WP-11 |
| D-104 | 2026-11-02 | `tpsg-` key pattern added to `metis.data.redact`. New Metis key in `.env`, also pasted in chat; owner to replace it again when possible | A | src/metis/data/redact.py |
| D-105 | 2026-11-02 | **Gate 2 failed by one item; owner went ahead with a weaker gate on record.** Pointwise jev with history, τ = 7, against Opus labels (n = 100): agreement 0.74 (CI 0.65 to 0.82, line 0.75), κ 0.431 (CI 0.24 to 0.62), AUC 0.79. Pairwise κ 0.285, position consistency 0.738. D 0.333 at K = 1, 0.111 at K = 3. Owner declined the rubric revision and re-judge. No rubric change; wrong-prompt test not run. Report must state the miss. Choice in `configs/judge_choice.yaml`, not `judge_config.yaml`, to keep the config id | O | WP-13, WP-14, WP-19, WP-20 |
| D-106 | 2026-11-02 | Main judging is pointwise only, narrowing D-101. Terra stays out: without history it ties jev on AUC (0.727 both) with κ 0.27 against 0.36 at τ = 7; about 13 times the cost | O | WP-13 |
| D-107 | 2026-11-02 | Sonnet stays candidate and anchor, deepseek-v4-pro not adopted (closes D-082): mean score gap -0.29 (CI -0.53 to -0.04, n = 100), pairwise 0.282. Owner declined local Qwen3-8B as a candidate | O | WP-12 |
| D-108 | 2026-11-02 | Val stays 400 (owner, closes D-091). Growing later reuses cached answers and judgments if the configs stay the same, about $2 per 100 new prompts; compare the Jev version first | O | WP-12, WP-14 |
| D-109 | 2026-11-02 | Validation first: test generation and judging wait for a separate "go" (owner). `s6_generate.py` still cannot select test | O | WP-12 |
| D-110 | 2026-11-02 | Bad key or empty balance stops a paid run at once and stores nothing, so a rerun resumes. Stopped runs write only `.partial` tables. `--retry-failed` retries stored failures | A | WP-12 |
| D-111 | 2026-11-02 | Sonnet's guard estimate set to the measured $0.0175 per call (`--est-usd`) after a false cost stop; the 2× rule unchanged (owner OK) | O | WP-12 |
| D-112 | 2026-11-02 | Validation labels: score < 7 is a loss, failed answer keeps score 1, the one prompt Jev refused (400) has no labels | A | WP-13 |
| D-113 | 2026-11-02 | Team branch `TakRoute` with README and `.env.example` (owner) | O | – |
| D-114 | 2026-11-02 | WP-14 updated: free validation check first, protocol must state refused prompts, failed and cut-off answers before the freeze. Test judged and sealed, no choice used it | A | WP-14 |
| D-115 | 2026-11-03 | **Val grows to 800 (owner "go", reverses D-108, DEV-15).** 400 new prompts drawn at random from train sessions, cap 3 per session, seed 20261103 (`scripts/s2_grow_val.py`, `results/split_grow_manifest.json`). Train is the only safe pool: split `none` is mostly leftovers of test sessions. Moved sessions (391) leave train; 8,519 train rows went to `none`. Centroids not refit, so these sessions took part in K-means at 0.2% of train. Old split kept as `runs/s2/split_val400.parquet`. Limits raised: gen_main $21.50, judge_main $3 | O | WP-14 |
| D-116 | 2026-11-03 | Pairwise jev run on all 800 val prompts as a second view (owner "go pairwise"; D-106 stays for the main method). Test has no pairwise labels | O | WP-14 |
| D-117 | 2026-11-03 | **Owner chose K = 8 as main router, K = 4 kept as comparison.** The D-064 rule on val 800 gives K = 4 (area 0.6634; K = 3 0.6629; K = 8 0.6522). Set aside on purpose; report must state it, and that K = 8 lost to DeepSeek by 2.0 points on the new 400 when fitted on the old 400. Final approval at Gate 3 | O | WP-14 |
| D-118 | 2026-11-03 | **Proposed, needs owner at Gate 3 (DEV-16):** λ chosen on unseen folds as the largest λ not below always-DeepSeek, because S10's in-sample rule missed its target on unseen prompts (K = 8: 63.7% vs 64.2%). Protocol draft also adds always-DeepSeek as a main comparison. Used as defaults overnight | A | WP-14 |
| D-119 | 2026-11-03 | **Owner overnight consent ("i consent all"):** continue through all WPs in one session, handoffs included; wait out the 5-hour limit and resume; Gate 3 freeze, `pre-test` tag and the one test opening; WP-17 labels (≤ $1), WP-19 live run (~$1.50); Khayyam after the main work ("go khayyam", limit $5). Owner did not read the protocol before the freeze, so the agent commits it for later audit. UniRoute stays the shipped router; no faked results | O | WP-14..21 |
| D-120 | 2026-11-03 | D-118 applied: λ = 0.5151 (K = 8), λ = 0.04954 (K = 4). Protocol adds always-DeepSeek as second main comparison. Gate 3 passed by consent D-119 (DEV-16) | O | WP-14 |
| D-121 | 2026-11-03 | Cache: AI-grader method (agent choice under D-119). No θ met ≤ 2% wrong hits; WP-17 fallback θ = 0.97, 10.0% wrong hits (5.5% to 17.4%), report it. One routing vector reused, text-matching gain too small | A | WP-17 |
| D-122 | 2026-11-03 | Replay settings pinned before test: K = 8, cache on, checks on, stickiness off (no change on val), per `configs/gateway.yaml` | A | WP-18 |
| D-123 | 2026-11-03 | Product name **TakRouter** (owner). Internal package stays `metis`; both `takrouter` and `metis-auto` route | O | all |
| D-124 | 2026-11-03 | Khayyam run done (owner go, D-119): UniRoute K = 7 beats ZeroRouter on area +0.020 (0.001 to 0.044), not the best single model at chosen λ. Metis key ran out mid-run; owner spare key used | O | Khayyam |
| D-125 | 2026-11-03 | Customer chat app on live models (owner: "use my api token", "a real product", "both English and Persian"): `/` is the chat app, `/results` the evaluation page; new budget stage `product` $3; per-request λ; 402 when the stage is used up | O | Product |
| D-126 | 2026-11-03 | Website with 11 pages (home, chat, compare, tutorials, developers, dashboard, pricing, how, login, account, models) in Persian and English; accounts (first sign-up is admin, scrypt passwords, per-user credit $0.50 default), API keys, optional decision trace, admin page to add a model the UniRoute way (798 val prompts + jev, stage `add_model` approved per run; activation writes artifacts/router_live) | O | Product |
| D-127 | 2026-11-03 | Khayyam exam demo kept separate from the chatbot router (owner: "different tab… dont merge it with the real data"): own artifact `artifacts/router_khayyam` (K = 7, λ 21, from stored answers, $0), own replay gateway and traces, page /khayyam. Two more models (gpt-5.2, gemini-2.5-flash) proposed, waiting for go | O | Khayyam |
| D-128 | 2026-11-03 | Khayyam gets its own sub-menu (overview, Khayyam chat, subjects) and a live chat page /khayyam/chat (owner: "khayyam test should have a chat option too"): `POST /v1/khayyam/ask`, question + 4 options → Khayyam router → live model (stage `product`) or mock; vector = jina of the question body[:2000], not normalized (as khayyam_run.py); sign-in required; spend counts against user credit. Typed questions never used in evaluation | O | Khayyam |
| D-128b | 2026-11-03 | Team merge: our project goes into the team repo as PR #16 (`takrouter-full` → `develop`, merge commit, history kept), team router becomes a decide-only service (`POST /route`, port 8100) behind TakRouter's gateway, one website with a TakRouter / Team toggle; live merge done by Farzaneh via `MERGE_LIVE_PROMPT.md` | O | Team |
| D-129 | 2026-11-04 | Website on Node.js: `web-node/` (Next.js 16) serves the 14 pages with server-side lang/dir, RTL fixes (bdi isolation, `dir` per text box instead of `unicode-bidi: plaintext`, which froze Safari's caret in Persian) and API pass-through to the gateway. `web/` stays unchanged (owner: "don't overwrite the first format"). Chat redesigned after ChatGPT/Claude (owner): no site header on /chat, collapsible sidebar rail, search, day groups, edit/copy/retry, code copy, jump-to-latest, shortcuts. Next.js `compress: false` (gzip held back streams) | O | Product |
| D-130 | 2026-11-04 | Own provider key (owner: "add a section for api key … it should work"): a user stores their own Metis key, Fernet-encrypted (`TAKROUTER_SECRET` or `runs/gateway/provider.secret`), only the last 4 shown. Their calls skip our ledger/budget/credit; a refused key → 400 `own_key_rejected`, shared breakers untouched. Traces get `billing` | O | Product |
| D-131 | 2026-11-04 | Streaming (owner "go"): `stream: true` → SSE in the OpenAI chunk format; routing, budget, secret guard, ledger, checks, failover and trace unchanged; `reset` chunk on a new attempt; whole answer for cache hits; if the provider cannot stream, one normal call. Real test: Metis streams, $0.000065 | O | Product |
| D-132 | 2026-11-04 | GitHub (owner): professional README with screenshots (example conversations, no user data, no Khayyam text) and diagrams, CI (ruff + pytest mock + Next build). PR #1 TakRoute → main merged with a merge commit; `main` is the working branch | O | Repo |
| D-133 | 2026-11-04 | Team repo (owner): PR #17 `takrouter-full` → develop keeps only the Node site under takrouter/ (team toggle carried over); PR #18 `develop-into-main` → main (conflict-free #14) for contributor credit. All merges are done by Farzaneh with merge commits; owner sends her the step list | O | Team |
| D-139 | 2026-11-05 | TakRouter | Team toggle on our Next.js site: team commit 553a5b2 ported (chat.html, pipeline/app, team_router adapter, 5 unverified team models). Tests 332 pass | O | Product |
| D-140 | 2026-11-07 | origin repo Mehrdadrahmani/metis-auto made public for the owner's CV. Before: key-pattern scan of all origin/main + origin/TakRoute history (clean; only `api_key=os.environ` code), no data/cache/runs/.env ever pushed. Team branches with leaked keys are not on origin and must never be pushed there | O | Release |
| D-138 | 2026-11-04 | Pitch part reworked many rounds; owner froze tech part; final = 12-slide Sequoia-order pitch (artifact v42 = git 04398be); workshop rebuild rejected | O | Deck |
| D-137 | 2026-11-04 | Owner rejected deck v3 ("previous much better; main problem not understood"); artifact restored to the v2 slides (version 18). v3 generator kept in git history (9392768) only | O | Deck |
| D-136 | 2026-11-04 | Deck v3 ask (owner): no budget/money amount; ask for cleaner, more classifiable data and resources to build the product. Financial forecast and capital slides dropped | O | outline_v3 |
| D-135 | 2026-11-04 | Deck v2 rejected by owner (too little context, diagrams too large, weak story, Antler/JPMorgan tips missing). Rebuild as v3 from the full tips in local `deck/v2/sources/pitch_tips.md`; outline first | O | STATUS |
| D-134 | 2026-11-04 | Pitch deck v2 (owner): English; pitch part in the Antler + JPMorgan order (team early, clear ask, no unsupported claims), then a technical part (clustering, Ψ, rule, add-a-model, updated original draw.io diagrams, deferral curves/AUDC/QNC, results, data limits vs Khayyam); light website style; every number referenced; providers (not models) on the iceberg; public sources: Verasight 2026, OpenRouter catalog, Artificial Analysis Apr 2026, Menlo Ventures Nov 2026. Sources in `deck/v2/` | O | Deck || D-100 | 2026-11-02 | Real pilot spend **$6.29** (owner, Metis dashboard), ledger $5.87, gap $0.42 (7%). Cause not proven; likely prompt-cache writes (1.15M tokens, not in the cost formula). Budget uses the dashboard figure | O | MASTER_LOG §4 |
| D-101 | 2026-11-02 | **Terra dropped for the main run (owner).** Jev keeps both pointwise and pairwise. Replaces D-083's choice between judges. Gate 2 still applies; Jev is 70% and kappa 0.36 pointwise, position consistency 0.755 pairwise, against Opus labels | O | WP-11, WP-13 |
| D-102 | 2026-11-02 | **Chat history goes to the judge from now on (owner, replaces D-046, DEV-9).** All judging after the pilot uses it, val and test. Pilot 100 re-judged too if money allows: Jev only, estimate $0.25. Needs a `{history}` slot in the templates and Jev form. Mixed inputs until then: pilot judgments have no history | O | WP-13 |
| D-098 | 2026-11-02 | **Owner: labels by Claude Opus instead of the owner (DEV-14, replaces WP-10).** Owner has no time. 10 fresh Opus agents rated 100 items blind (Answer 1/2, re-shuffled, no key or score files). Stored as `runs/labeling/opus/opus_labels.parquet`, rater `claude-opus-5-5`, never as `human_labels`. Not a human check; report must say so. Conflict: Sonnet is the same family as the rater. No test data | O | WP-10, WP-11 |
| D-099 | 2026-11-02 | Labeling page shows chat history (81 of 100 prompts have it). Owner prefers judges with history too (would replace D-046, DEV-9); re-judge held, owner said not yet. Estimate $3.63, 81 prompts only | O | src/metis/labeling, WP-11 |
| D-095 | 2026-11-02 | **Answer limit raised in steps (owner).** 1,024 cut 9 of 100 Sonnet answers, 1 to 3 for the others, because Sonnet fits about 1.5 chars per token here against 2.4 to 3. s6 now redoes only cut answers at 2,048 (`configs/gen_retry.yaml`), then 4,096 (`gen_retry_2.yaml`), same limits for all models. `gen_config.yaml` unchanged: its hash is in the cache key. Applies to the main run too | O | scripts/s6_generate.py |
| D-096 | 2026-11-02 | Owner chose to run the pilot on the old Metis key, the one pasted in chat. Still to be replaced | O | STATUS |
| D-097 | 2026-11-02 | `s7_judge.py` pre-check prices only work not yet done: it refused a 2-call rerun at the $10 limit by counting 500 cached calls. Limit unchanged, per-call guard unchanged. `s6_generate.py` still has the old pre-check | A | scripts/s7_judge.py |
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
| Q-017 (closed 2026-11-01: yes) | Does Metis AI work from the same network as Claude Code (VPN)? Planner saw TLS resets to metisai.ir on 2026-10-20 (PLAN R17) | owner | WP-04 |
| Q-018 | Metis AI: exact model ids, prices (currency), rate limits, usage and cached-token reporting | WP-04 | WP-08 budget memo |
| Q-022 | GitHub secret scanning / push protection unavailable on the free private repo (HTTP 422). Accept local hook only, or upgrade/make public later? | owner | WP-21 |
| Q-023 | Test the router on public Persian data like the paper (owner idea; the embedding + clustering half is done in WP-03b, the routing half is open): (1) $0 run on persian-llm-eval's per-item results (17–20 models, ~294 items), (2) paid: Khayyam / Persian ARC / PMWP answered by our 4 candidates, exact-match graded (~$1–3, after the full data). Details `ref/docs/persian-datasets.md` | owner | WP-05 (option 1) / WP-14 |
| Q-019 | Approve DEV-4, DEV-5 | owner | WP-06 (DEV-5), WP-11 (DEV-4) |

## 4. Budget ledger

Hard cap: **$60.00**. Per-stage approvals are set at Gate 1 (WP-08) and stored in `configs/budget.yaml`.

| Date | Stage | WP | Approved | Spent | Calls | Note |
|---|---|---|---|---|---|---|
| 2026-10-20 | – | planning | $0 | $0.00 | 0 | Planning estimate: ~$25 (pointwise path) / ~$35 (pairwise), PLAN §7 |
| 2026-11-02 | pilot | WP-09 | $10 | $0.00 | 0 | Gate 1 (D-094). Estimate $6.71. Other stages $0 until Gate 2 |
| 2026-11-02 | pilot | WP-09 | $10 | $6.29 | 2,361 | Dashboard figure (D-100). Ledger $5.87. Sonnet $1.75, deepseek-v4-pro $0.28, luna $0.08, flash $0.07, gemini $0.04, terra $3.42, jev $0.23 |
| 2026-11-02 | pilot | WP-11 | $10 | about $6.60 | 3,638 | Jev re-judge with history, ledger $0.29, 1,277 new calls. Total ledger $6.16; dashboard figure + re-judge. 23 failed 401 calls at $0 |
| 2026-11-02 | gen_main | WP-12 | $8 | $5.76 | 1,234 | Validation only. Sonnet $5.17, luna $0.26, flash $0.20, gemini $0.13. 3 failed tries, all one Sonnet prompt |
| 2026-11-02 | judge_main | WP-13 | $1 | $0.28 | 1,251 | Validation only, Jev, 80 repeat calls included. 8 failed tries, all the one refused prompt |
| 2026-11-02 | gen_main | WP-12 | $14 | $6.12 | 1,253 | Test set, owner "go", estimate $5.90. Sonnet $5.49, luna $0.27, flash $0.22, gemini $0.14. 0 failed |
| 2026-11-02 | judge_main | WP-13 | $1 | $0.30 | 1,240 | Test set, sealed, owner "go". 60 repeats included. 8 failed tries, all one refused prompt |
| 2026-11-03 | gen_main | WP-14 | $21.50 | $7.54 | 1,600 | Val +400, owner "go" (D-115), estimate $7.86. Sonnet about $6.74. Key ran out once (402), resumed with spare key. Stopped once at the old $20 limit |
| 2026-11-03 | judge_main | WP-14 | $3 | $0.42 | 1,717 | Val +400 pointwise jev + repeats. 2x cost stop after 52 calls was a few long prompts; final about $0.00024 per call |
| 2026-11-03 | cache_labels | WP-17 | $1 | $0.06 | 700 | Cache pairs, consent D-119 |
| 2026-11-03 | live | WP-19 | $1.50 | $0.99 | 300 | Consent D-119 |
| 2026-11-03 | khayyam | Q-023 | $5 | $0.47 | 6,000 | Owner go, D-119 |
| 2026-11-03 | judge_main | WP-14 | $3 | $1.05 | 4,092 | Pairwise jev on val 800 (D-116), estimate $1.15 to $1.50 |
| 2026-11-03 | product | D-125 | $3 | $0.0134 | ~10 | Chat app smoke test (3 calls by the agent) and the owner's own chats |
| 2026-11-04 | product | D-131 | $3 | $0.0148 total | +~3 | Owner's chats + 1 real streaming test by the agent ($0.000065, owner "test") |
| | **Total** | | | **about $28.07** | | Ledger + dashboard gap (D-100) |

## 5. Log (newest first)

### 2026-11-04 · Handoff 9: pitch deck v2 (detour from WP-21)
- Owner asked for a new deck from two articles (Antler pre-seed guide; JPMorgan text pasted by the owner, site blocked automated reads). Built several versions as a Slides artifact (https://claude.ai/artifact/SpvxYs5pMU9j6cia75kknM; earlier English v1 SAJoJk1w… kept). Owner feedback drove: English, pitch then technical part, light website style, iceberg by providers, fewer words, references per number, original diagrams.
- New charts from aggregates only (`deck/v2/charts/`): validation deferral curves (held-out 2-fold; areas K8 0.650, K4 0.663, Zero 0.653, K-NN 0.657, logistic 0.649), AUDC/QNC bars from `results/final/final.json`, Ψ heat map with picks (DeepSeek 7 clusters, Luna 1), Khayyam winner heat map, t-SNE cluster map of validation embeddings (no text), typeset formulas. Updated copies of ref/diagrams 01/03/05 (val 800, train 209,109, K = 8, λ = 0.515).
- Finding for the report: on chatbot data the lowest-error model per cluster is DeepSeek or Sonnet in all 8 clusters; on Khayyam winners differ by subject (DeepSeek, Luna, Gemini) — supports "data too easy/general" as the reason for no gain over DeepSeek.
- Continued with owner consent: deck v2 rebuilt story-first and published (version 14): 10 pitch + divider + 8 technical + thanks + 6 backup; refs [1]–[8] on every number; provider iceberg (drawn, owner chose illustration over a CC BY-SA photo); typeset formulas; updated draw.io diagrams. Owner page edit on t3rule merged (content unchanged).
- Not done: owner review of deck v2; WP-21 step 2; website Team toggle port (owner questions pending). Cost $0. No code in `src/` changed.

### 2026-11-04 · Handoff 8: product session 2 and GitHub
- Node site (`web-node/`, D-129): pixel-equal to the Python site except the fixed header; RTL fixes; chat after ChatGPT/Claude; live typing then real streaming. Own provider key (D-130). Streaming (D-131): gzip in Next.js held back SSE, fixed with `compress: false`; real Metis test streamed 46 chunks, $0.000065. Safari caret bug in Persian text boxes fixed (dir instead of plaintext).
- GitHub (D-132, D-133): README with screenshots/diagrams, CI green; PR #1 merged into main. Team: PR #17 (Node site only in takrouter/), PR #18 (conflict-free develop→main, 72 linked commits); Farzaneh merges. Contributors list counts only the default branch.
- Tests 332 pass; browser checks 26/36/23/7/14 pass. Files: src/metis/gateway/{app,auth,pipeline,providers,traces}.py, src/metis/llm/client.py, tests/test_own_key.py, tests/test_streaming.py, web-node/, README.md, docs/, diagrams/pitch/, .github/. Cost: product +$0.0009 (incl. owner chats).

### 2026-11-03 · Handoff 7
- PR #16 now holds the preview (3fbc212) and MERGE_LIVE_PROMPT.md (f6f07ee). Preview runs live on 8001; preview demo-cache served fake answers after the switch to live, fixed by clearing runs/preview/cache.sqlite and restarting. Main site restarted live on 8000. Tests 319 pass. Product spend $0.0139 total.

### 2026-11-03 · Demo answers removed from the live cache
- Owner: "delete them". 635 mock answers (`پاسخ نمایشی…`, space `default|…`) deleted from runs/gateway/cache.sqlite; 4 real entries kept; backup kept locally. Preview switched to live on 8001 after its own demo cache served fake answers (same bug). Cost $0.

### 2026-11-03 · Merge preview + live merge prompt
- Local repo ../takrouter-merged (both routers, toggle, mock/replay, $0). Wrote work/MERGE_LIVE_PROMPT.md. Found 636 demo answers in the real cache (owner decision pending). Removed my own test account, 2 trace rows and 1 cache row from the real files. Cost $0.

### 2026-11-03 · Team PR #16: whole project into the team repo
- Owner asked to put the whole project into Farzaneh's repo as a PR and write one merge prompt. Branch `takrouter-full` on `team` = `team/develop` + our history under `takrouter/` (unrelated-history subtree merge, 71 owner commits kept) + `TAKROUTER_MERGE_PROMPT.md`. Added-files secret scan 0 hits. PR https://github.com/farzanenadem/Metis/pull/16. Cost $0.

### 2026-11-03 · WP-21 start: replay guard, history secret scan
- Owner: "just go for wp21" (WP-20 left open). Added `METIS_ASSERT_NO_NEW_CALLS` guard (`NewCallRefused`) + test; tests 319 pass.
- Secret scan, own branches' full history: 0 hits. Team repo history has live keys in data files (commits f430621, 732eb91, 1bcb798, by teammates): reported to owner.
- Next: WP-21 step 2 reproduction in a fresh clone. Cost $0.

### 2026-11-03 · Khayyam chat page (D-128)
- New: `POST /v1/khayyam/ask` (`src/metis/gateway/app.py`, `kh_live()`), `metis.khayyam.build_gateway(provider=…)`, page `web/khayyam_chat.html` (/khayyam/chat), shared `TR.subnav` in `web/assets/site.js` + `.subnav` CSS, sub-menu on /khayyam (subjects anchor `#subjects`), main nav stays on "Khayyam" for /khayyam/*. "Example question" fills the form from `/v1/khayyam/sample` ($0).
- Test `test_khayyam_chat_asks_own_question` (mock). Tests 318 pass. Not yet tried live or in a browser. Cost $0.

### 2026-11-03 · Website, accounts, add-a-model, Khayyam demo (D-126, D-127)
- 12-page bilingual site on shared `web/assets/site.{css,js}`; accounts (`metis.gateway.auth`), API keys, credit, optional trace (`pipeline.trace_view`), usage (`TraceStore.usage`), compare (`/v1/compare`), `/docs` freed from FastAPI (now `/api-docs`).
- `metis.onboard`: add a model the UniRoute way (798 val + jev, stage `add_model` approved per run, `artifacts/router_live`). Reproduces the shipped fingerprints and costs exactly; mock run on 10 prompts OK. Bug found and fixed: lock re-entry deadlock on /v1/models.
- `metis.khayyam` + `scripts/khayyam_build.py` ($0): separate Khayyam router, replay gateway, page /khayyam. Per-subject test accuracy: DeepSeek flash best at maths/physics, Luna at biology/humanities, Gemini at literature. Gateway replay 55.5%, 0 failed; Luna outage 54.3%, 0 failed.
- Tests 317 pass. No new paid stage; product spend $0.0134 in total.

### 2026-11-03 · TakRouter chat app (D-125), team PR #15
- Chat app `web/app.html` at `/`: Persian and English (switch, `?lang=`), Economy / Balanced / Best quality (λ 3 / 0.515 / 0), slider over the λ breakpoints, fixed-model option, system prompt, per-answer model, cost, time, saving vs Sonnet, "Why this model?". Results page moved to `/results`.
- Backend: `TAKROUTER_PROVIDER=live` uses `LiveProvider("product")`; `metadata.lambda`; `GET /v1/router`, `GET /v1/budget`; budget refusal is a 402. New `metis.router.explain`. Tests 305 pass.
- Live smoke test with the real jina embedder: 3 calls, $0.0056. Screenshots seen in Persian and English.
- Team repo PR #15 (`uniroute-fix-lambda` into `develop`): UniRoute on the vector it was fitted on (100% same cluster vs 36%), peft, Luna and Sonnet 5.5 as uniroute-only, λ slider. Out-of-fold: cache vector routes as well as the clustering vector when refitted (area 0.6547 vs 0.6535).

### 2026-11-03 · Overnight: WP-15 to WP-19, site, deck, Khayyam (Opus)
- Gateway, cache, replay, final test (n = 299), live run, site, README, report draft, Persian deck, Khayyam. Test opened once. First live router row redone (cached calls). WP-20 review, draw.io figures and WP-21 fresh-clone rerun not done; no `v1.0` tag. Site not seen in a browser. Spent $1.52 tonight, total about $29.59.

### 2026-11-03 · WP-14 close (Opus, overnight)
- Sealed guard, artifacts v1 (K = 8, K = 4), frozen λ, protocol, report; tag `pre-test`. Tests 276 passed. $0.

### 2026-11-03 · WP-14 handoff 3 before overnight run (Opus)
- /start, owner gave overnight consent (D-119). No code changed. Tests: 273 passed. Keys: 3 Metis keys in total, original ran out, 1 spare in `.env`, 1 spare unused and not on disk. $0.

### 2026-11-03 · WP-14: signal tests
- `scripts/s11_signal_tests.py`, `results/signal_tests.md`: bot groups (D-078) and simple features show no clear gain, $0. `scripts/s12_input_test.py`, `results/representation_test.md`: previous-message input gives small area changes, no gain over DeepSeek at low cost, $0. Committed test fix after a commit that had one failing test.

### 2026-11-03 · WP-14: val 800, K = 8 luck exposed, pairwise
- Free router check first: on val 400, K = 8 looked +1.3 points over ZeroRouter (CI -1.0 to +3.6). Owner grew val to 800 (D-115). Cost $9.01 this session.
- Val 800: pass DeepSeek 65.4%, Sonnet 66.2%, Luna 61.5%, Gemini 53.5%, ceiling 79.4%. K* = 4. K = 8 fitted on old 400 lost to DeepSeek on new 400 by 2.0 points (-4.2 to 0.0); shuffle test p = 0.44.
- Pairwise (0.5 = equal to Sonnet): DeepSeek 0.403, Luna 0.409, Gemini 0.176. Position consistency 0.753, later answer favored. Topic routing adds nothing on pairwise labels either.
- New: `scripts/router_check.py`, `s9_router_val.py`, `s10_lambda_holdout.py`, `s2_grow_val.py`; `s7_judge.py --est-usd`. Results: `fingerprints`, `select_k`, `ladder_val`, `router_check_val`, `lambda_val`, `holdout_demo`.

### 2026-11-02 · Handoff, both remotes
- WP-12 and WP-13 closed. `TakRoute` pushed to the team repo and the owner's repo; owner's `main` moved to the same commit. Team `main` untouched. Tests 273 pass.

### 2026-11-02 · WP-13 done, test labels sealed
- 1,196 of 1,200 test answers scored, 1 prompt refused by Jev, $0.30, 60 sealed repeats. No test score read. Report: `work/reports/WP-13-report.md`. Next: WP-14.

### 2026-11-02 · WP-12 done, test answers sealed
- 1,200 test answers, 0 failed, 3 still cut off, $6.12. `s6_generate.py --set test` reads `test_ids.sealed`; outputs are `*.sealed*`. S7 refuses test until WP-13. No test text read, no test quality computed. Report: `work/reports/WP-12-report.md`.

### 2026-11-02 · Validation generated and judged, team branch
- WP-12 and WP-13 run on validation only (D-109). Generation $5.76, 1,599 of 1,600 answers. Judging $0.28, 1,595 scored, repeat check n = 80 mean gap 0.147.
- Pass rates at 7: Sonnet 65.2%, DeepSeek 64.9%, Luna 61.2%, Gemini 53.9% (n = 400). All pass 41%, all fail 21%, best possible 79%. Routing still untested.
- Bugs fixed: stored failures blocked resume (D-110); a failed answer loaded as NaN crashed the judge; Jev had no account stop. Budget test updated for the new limits.
- `cost_estimate_v2` counted 500 new prompts, the real number is 600. Corrected total about $21.30.
- `graphify update .` refused to overwrite (saved semantic nodes missing), so the graph is behind the code. History scan clean before sharing (46 commits). Team branch made (D-113).

### 2026-11-02 · WP-11 pilot decision, Gate 2
- Gate 2 failed by one item: pointwise jev with history, τ = 7, agreement 0.74 (line 0.75), κ 0.431 (n = 100, Opus labels). Pairwise κ 0.285, position consistency 0.738. Separability 0.333 at K = 1, 0.111 at K = 3.
- Owner declined the rubric revision and any re-judge, and went ahead with a weaker gate on record (D-105). Main judging pointwise only, terra out (D-106). Sonnet stays, no deepseek-v4-pro, no Qwen (D-107). Val 400 (D-108).
- Files: `scripts/pilot_decision.py`, `results/pilot_decision.md`, `results/pilot_decision.json`, `configs/judge_choice.yaml`, `work/reports/WP-11-report.md`; WP-12, WP-13, WP-14 updated. `judge_config.yaml` left alone to keep id 356e63e52245.
- Tests 265 passed. Cost $0.

### 2026-11-02 · Jev re-judge with history
- Against Opus labels at pass mark 7: agreement 0.68 to 0.74, kappa 0.36 to 0.43. Pairwise agreement 0.647 (n = 68) to 0.736 (n = 72). Position consistency 0.755 to 0.738. Mean score 6.81 to 7.40, so pass marks must be set again. Decisions D-103, D-104.

### 2026-11-02 · Pilot close: dashboard $6.29, judge plan
- Decisions D-100 to D-102. Free preview of routing on the pilot: router level with ZeroRouter, within noise (`report/NOTES.md`).

### 2026-11-02 · WP-10 done by Opus labels, no spend
- Page history fix, blind Opus labels (D-098, D-099). Local only: `runs/labeling/opus/`. No API charge.

### 2026-11-02 · WP-09 pilot run, first paid stage ($5.87)
- 500 answers, 499 terra pointwise, 500 jev pointwise, 800 jev pairwise, 60 test-retest calls. Stats: `results/pilot_run_stats.md`. Estimates: `results/cost_estimate_v2.md`.
- Every route worked, including Jev and Google. Usage returned by all. Only luna and terra report reasoning tokens.
- Jev pairwise position consistency 0.755, under the Gate 2 line of 0.80. Spearman terra against jev 0.709.
- Files: `configs/gen_retry*.yaml`, `scripts/s7_noise.py`, `scripts/s6_generate.py`, `scripts/s7_judge.py`, `src/metis/llm/{messages,callcache}.py`, tests. Tests 264 pass.
- Decisions D-095 to D-097.

### 2026-11-02 · WP-08 closed, Gate 1 passed
- Cluster names for K = 8 from local Qwen3-8B (`scripts/s5_topics.py`, 23 min, $0). Budget memo from `scripts/budget_memo.py`. Terra pairwise left out of the pilot (D-093). Pilot limit $10 (D-094). Tests 262 passed. Cost $0.

### 2026-11-02 · WP-07 dry run, clusters on all train, K limit 9
- D-088 applied: near-duplicate step removed from S4 and S5 scripts. K 3 to 20 and stability rerun on 179,185 train prompts (old results in `runs/s5/old_near_dedup/`). Stable to K = 9 only, so K limit 9 (D-089).
- Split rerun (D-080): sets unchanged by hash, 33 calibration rows renamed to gemini-2.5-flash-lite. Qdrant unchanged.
- `scripts/pipeline.py`: S1 to S12 on the sample, mock. Second run 0 new calls, 11 of 11 stages identical. Leak test: 4,802 requests, 13,720 planted fake keys, 0 hits.
- Cost estimate unchanged: pointwise $47.68, pairwise $62.12, both above PLAN §7 high ($39, $54). Tests 262 passed. Cost $0.

### 2026-11-01 WP-04 finished ($0.00)
- Built the client, cache, budget guard, runner, mock mode, MLflow tracing and Metis check; 39 new tests, 208 pass.
- Metis reached; key in `.env`. Model-list and metadata GETs only, no generation. Prices stored from the public pricing address.
- Decisions D-080 to D-083. Later WP files updated: 06, 07, 09, 11, and the model name in 12, 14. PLAN M3, M4 and §7.2 row updated; §7 totals wait for the Gate 1 recompute (prices differ by more than 25% for some models).
- Q-017 closed: Metis works from this network. The Metis key was pasted in chat: owner should replace it.

### 2026-11-01 · WP-06: generation and judge pipeline, labeling tool (Opus)
- Built `configs/{gen_config,judge_config}.yaml`, `src/metis/llm/{messages,stage}.py`, `src/metis/judge/*`
  (templates, parse, render, pointwise, pairwise, common, jev), `src/metis/labeling/*`,
  `scripts/{s6_generate,s7_judge,estimate_costs}.py`, tests (51 new). `api_path` set for jev.
- Decisions D-084 to D-087. Mock S6+S7 on 20 sample prompts: rerun 0 new calls. Tests 259 pass.
- Cost estimate (simulated): pointwise $47.68, pairwise $62.12, pilot $15.28. Above the $45 line.
- Tool built with 5 mock items; the owner replied OK at step 8. Cost $0.00.

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

### 2026-11-04 · WP-21 (deck feedback, handoff 10)
- Owner rejected deck v2; pasted JPMorgan tips (saved as local git-ignored checklist `deck/v2/sources/pitch_tips.md`). Antler page refused automated fetch; owner to paste. D-135. Cost $0.

### 2026-11-04 · WP-21 (pitch rework, handoff 11)
- Tech part: full pipeline diagram walked in parts, clustering slides first, LaTeX simple formulas (exact in backup), soft heatmaps, Jina v5 nano + Qdrant on clustering image. Pitch: public-benchmark insight, Sequoia/Kawasaki/YC/DocSend restructure (kept); v3, workshop and enrichment versions rejected. Research briefs saved locally (deck/v2/sources). Cost $0.

### 2026-11-05/06 · WP-21 (deck sections + toggle, handoff 12)
- Deck: learn slide, λ slide, UniRoute-only curve on T5, LLM Router section (owner file), Evaluation section (owner file, renamed TakRouter), backup slides moved to separate deck, system overview before LLM Router; Persian bullet notes PDF; val-400 Excel in Downloads (local only). Product: Team toggle ported (D-139). GitHub push failing (network). Cost $0.

### 2026-11-07 · WP-21 (repo public + CV prompt, handoff 13)
- Owner asked for a CV prompt (TakRouter project, CV entry + GitHub page polish) to run in another session; wrote it in chat. Made origin repo public after history secret scan (D-140). Found that team commits 732eb91/1bcb798 (team/add-evaluation-test) contain raw golden-set data with live keys; not in our main/origin. No code changed, no tests needed. Cost $0.
