# PLAN: Metis-Auto v2 implementation plan

**Version:** 1.0 · 2026-10-20 · written by the planner session with the owner (Mehrdad Rahmani).
**Router spec (source of truth):** `ref/UNIROUTE_PIPELINE.md`; this plan marks every deviation as
**[DEV-n]** for the owner to approve. **Work packages:** `ROADMAP.md` + `work/WP-*.md`.
**Handover mechanism:** `CONTINUITY.md`. **Decisions and budget ledger:** `MASTER_LOG.md`.

Sections: 1 Design decisions · 2 Fixed setup · 3 Phases · 4 Timeline · 5 Before vs after the data ·
6 Results → changes · 7 Budget · 8 Statistics and evaluation protocol · 9 Risks · 10 Repository layout ·
11 Owner decision points.

---

## 1. Design decisions

Priority: **must** (the result is not credible or not compliant without it), **should** (clearly
better, cheap), **nice** (only if time remains). "Spec" = `UNIROUTE_PIPELINE.md`.

### 1.1 Method

| ID | Decision | Priority | Why |
|---|---|---|---|
| M1 | **UniRoute (K-means) is the router, implemented as in the paper** (owner decision 2026-10-20, D-040). The paper's baselines (always-best, always-cheapest, ZeroRouter / Pareto-random, K-NN) are built from the *same* labels and **reported for comparison only**; the gateway always ships UniRoute. | must | Owner wants every clustering and routing step as in the paper. With a fixed pool of 4 models the paper (App. G.5) finds UniRoute only comparable to simpler routers, so the comparison is reported honestly; the primary claim (M2) does not depend on UniRoute winning. |
| M2 | **The minimum credible result** is: routed system vs always-best (claude-sonnet-5-5) on the locked test set, cost saved with a pre-registered quality non-inferiority margin and paired CIs (§8). UniRoute vs ZeroRouter/K-NN is the secondary result. | must | It answers the brief's question ("cheaper without losing quality") whatever the ranking of routers. |
| M3 | **4 candidates:** deepseek-v4-flash, gpt-5.6-luna, gemini-3.5-flash-lite, claude-sonnet-5-5 (strong; premium baseline; anchor if pairwise). Updated to current models by D-056 (replaces D-016). | must (owner) | Current model of each family, same price tiers; not yet confirmed on Metis AI. |
| M4 | **"Unseen model" test becomes a demo:** hide gemini-3.5-flash-lite while choosing K and λ, then add it with its fingerprint only and show where it gets routed. Reported as an illustration, not as evidence. | should | With 4 models a real held-out evaluation (spec S3.4, ~1/3 of models) has 1 model; no statistics possible. Honest framing. |
| M5 | **Clustering input = the user's text only, embedded with a frozen general-purpose text embedder** (paper §5.1), never the system prompt. **Decided (Q-021, D-045):** the **current user message only** (paper), no previous turns. **[DEV-8]** vs spec S1 (T = 2), owner decision | must | System prompts are ~100× longer than user messages and would turn clusters into "one cluster per chatbot". The paper embeds the prompt itself. |
| M6 | **Generation keeps each chatbot's own system prompt, retrieved context and real history** (as production). `gen_config` = sampling parameters only (temperature, max tokens). **[DEV-2]** (spec S6 says one shared system prompt) | must (owner) | Grading answers produced without the chatbot's instructions would measure the wrong thing. |
| M7 | **Turns whose system prompt > 20,000 characters are excluded from val/test** (expected ~8% of turns; exact share reported). Online they are routed by the hard context rule. | must (owner) | A few prompts of 60k+ tokens would take a large part of the budget and bias costs. |
| M8 | **Label method by a slim pilot** (owner-approved **[DEV-3]**): 100 pilot val prompts, 4 models, both pointwise and pairwise judging; the owner labels 100 items; choose the method by human agreement (criterion B) **and** separability (D); ties → pointwise. Spec criteria A and C are computed but not decisive (too few prompts to be meaningful). | must | The spec's full pilot (2×2 cross-evaluation on 150 test prompts) is underpowered; this saves ~1 week and ~$10 of the 4. |
| M9 | **τ and the agreement gate use balanced measures:** choose τ by **balanced accuracy** on the calibration set; the gate is agreement ≥ 75% **and** Cohen's κ ≥ 0.40. **[DEV-4]** (spec: plain accuracy) | must | If 85% of answers pass, "always pass" already scores 85% accuracy; plain accuracy can pass a useless judge. |
| M10 | **Judge = GPT-5.x class** (e.g. gpt-5.4, as available on Metis AI), blind, temperature 0 (or lowest reasoning effort if temperature is not supported; recorded). Prompts = spec A1/A2 **extended** with the chatbot's instructions (truncated at ~6k tokens, with a note) and the retrieved context, plus a criterion "follows the chatbot's instructions / stays grounded in the context". **[DEV-5]** | must | Different family from 3 of 4 candidates; the extension follows from M6. |
| M11 | **Judge bias and noise controls:** same `max_tokens` for every candidate; length-bias check (Spearman score vs answer length within prompt); pairwise in both orders (position-consistency rate); self-preference check on gpt-5.6-luna (judge–human disagreement by model on the calibration set, descriptive); **re-judge 5% of items** to measure test–retest agreement; the owner re-labels 20 calibration items a few days later (intra-rater consistency, ~30 min). | must (first four) / should (last two) | One labeler and one judge: we must at least measure how noisy they are. |
| M12 | **One answer per (prompt, model)** (spec). Multiple samples per pair (DARS) are a "nice" upgrade. | must | Budget and time; noise is measured instead (M11). |
| M13 | **Split-validation repeats R = 20** instead of 5 for choosing K (and K-NN's k). **[DEV-6]** | should | $0 compute; reduces the noise of the choice with 400 prompts. |
| M14 | **As in the paper:** K candidates {3, …, ⌊N_val/50⌋} = {3…8} (App. G.2); K-means (k-means++, ≥ 10 restarts) on the train split; each prompt assigned to its **nearest centroid** (K-means assignment, §5.1); fingerprint = **plain per-cluster error rate, Eq. 12 (α = 0)**; routing rule Eq. 8/11; K chosen by the **normalized area under the deferral curve** on validation. K = 1 is computed only as a comparison (paper App. D.1). No per-cluster minimum rule; a cluster with no validation prompts falls back to the model's overall error rate (logged). **[DEV-7]** vs the spec (α = 2, cosine assignment, n_min drop), owner-requested. **Q-020 decided (D-061):** K-selection report cards come from split-validation on val ($0). | must | Owner decision: every routing and clustering step as in the paper. |
| M15 | **Similarity to production's answers** (the brief's metric) is reported as a **secondary** metric with a caveat: production used 18 models, so it measures "closeness to whatever production said", not quality. Same embedder, cosine. Judge-based quality is the primary metric. | must | The brief asks for it; it can't be the quality measure (v1 lesson). |
| M16 | **Freeze before test:** the router artifact (method, τ, K, centroids, Ψ, ĉ, λ, chosen router from the ladder) and an evaluation protocol are committed (git tag `pre-test`) **before** the test labels are read. | must | Makes "the test set was used once" verifiable by a reviewer. |

### 1.2 Engineering

| ID | Decision | Priority | Why |
|---|---|---|---|
| E1 | **Gateway = FastAPI service with an OpenAI-compatible `/v1/chat/completions`** (non-streaming must; streaming should), using **LiteLLM (Python SDK)** for provider calls, retries, timeouts and cost accounting. We build only: hard rules, router, cache policy, checks/escalation, traces. | must | Reuse the plumbing that is already solved; spend the 4 weeks on the router and the evaluation. |
| E2 | **All model calls through Metis AI** (owner's choice), OpenAI-compatible base URL, model names mapped in `configs/models.yaml`. WP-04 verifies: all 5 models available, prices, usage/token reporting, rate limits, whether provider prompt caching passes through. | must | One key, one bill. |
| E3 | **Honest failover:** with a single aggregator, "provider down" is mostly simulated. Failover is model-to-model (next-best s(h), preferring another upstream provider) through Metis AI; a second aggregator (e.g. OpenRouter) as a fallback route is **nice**. Failover is proven with **fault injection** in tests (mock provider returns 5xx / timeouts). | must | The brief wants failover; we must not over-claim a "parallel provider" we don't have. |
| E4 | **Resilience settings:** connect timeout 5 s, total 60 s (first token 20 s when streaming); 1 retry with jitter on 429/5xx; circuit breaker per model (3 failures in 60 s → open 30 s → 1 probe); per-model concurrency limit. | must | Standard values; configurable. |
| E5 | **Latency budget for gateway overhead: p95 ≤ 100 ms** on the owner's Apple Silicon Mac (16 GB+): embedding ≤ 60 ms p95 for ≤ 512 tokens (CPU or MPS), cluster lookup < 1 ms, cache lookup ≤ 5 ms (in-memory numpy per chatbot namespace; no vector DB needed at this scale). The embedder (BGE-M3 vs multilingual-E5 base/large) is chosen in WP-03 by measured latency + Persian paraphrase sanity + cluster readability on the sample. | must | The brief requires a cheap, low-latency classifier. |
| E6 | **Hard rules (G1)** from real data fields: widget click = previous bot message has `input.items[].choices` and the user text equals a choice → workflow step, no LLM; `attachments[].contentType == IMAGE` → vision-capable models only; `provider == workflow` / `model == default` turns are workflow steps; `model == dalle` → image model; context-length rule removes models whose context window < estimated tokens; open breaker removes models. | must | Fields verified on the sample (structure only). |
| E7 | **Quality checks + escalation (cascade, G6):** free code checks (empty, truncated / `finish_reason=length`, wrong language vs user, invalid JSON when the instructions demand JSON, refusal pattern). Fail → one retry on the same model with a repair hint → escalate to the model with the next-lower Ψ_k. Escalation rate and its cost are measured in replay. | must | The brief's cascade, without paying a judge per message. |
| E8 | **Semantic cache: decision deferred** (owner, 2026-10-20). Planned as WP-17 with rules fixed now: exact match after Persian normalization + meaning match above a threshold; namespace = chatbot + instruction hash + language; only standalone messages (first turn or no reference to history); never images, personal data patterns, time-sensitive words, or RAG-dependent answers unless the context hash matches; only answers that passed checks; TTL 7 days. Threshold method chosen at WP-17's decision point (recommended: AI grader labels ~200–300 pairs "does the saved answer fit the new message?", ≤ ~$1, target ≤ 2% wrong hits). | must (cache exists) / decision later | Required by the brief; hit rate will likely be low in this traffic and is reported honestly. |
| E9 | **Provider prompt caching:** cost is computed both without and with provider cache discounts; replay tests a **stickiness** option (stay with the conversation's previous model unless its score is worse by > δ). | should | System prompts are long (median ~3.6k chars); switching models per message can lose the discount. |
| E10 | **Observability:** local **MLflow** (D-044) for browsing traces of every LLM/judge/gateway call and comparing router-selection runs; one trace row per request in SQLite (request id, chatbot, cluster, all scores, chosen model, fallbacks, escalations, cache hit, tokens, cost, latency per stage, artifact version); metrics (cost/query, savings vs always-best, p50/p90/p99 latency, hit rate, routing share, escalation and failure rates, cluster-share drift vs validation via PSI); a small dashboard (static HTML or Streamlit) from the traces. Online quality sampling (judge 1–2% of live answers) is **designed, not run**. | must / nice (live sampling) | Brief's observability + Action 3 dashboard. |
| E11 | **Reproducibility:** every LLM/judge call cached in SQLite keyed by a hash of (model id, full request, config id); YAML configs with hashes (`models.yaml` with dated price snapshot, `gen_config`, `judge_config`, `pipeline`); split files with content hashes; seeds recorded; a run manifest per stage; returned model version recorded. Rerun = 100% cache hits, $0. | must | Spec golden rules 2 and 8; required by fixed point 6. |
| E12 | **Budget guard in code:** `budget.yaml` hard cap ($60), a pre-run estimate for every paid stage, refusal to start if estimate + spent > approved amount for that stage, running ledger in SQLite mirrored to `MASTER_LOG.md §Budget`. Every paid stage needs the owner's explicit "go" in the session. | must | Fixed point 4. |
| E13 | **Secrets:** redaction of `instructions`, `content` and `rag.context` before anything leaves the machine (key patterns: `sk-`, `sk-ant-`, `AIza`, `ghp_`, `Bearer …`, JWT-like, URL `key=`/`token=`); a test that scans every outgoing request in dry-run mode; pre-commit secret scan; GitHub push protection; `data/`, `cache/`, `runs/` never committed. Only aggregate results (no prompt/answer text) go to `results/`. **Claude Code sessions never read message text, instructions or generated answers** (reading = sending to Anthropic): they work with counts and statistics; anything that needs a human to read content (cluster samples, labeling, spot checks) is written to a local git-ignored HTML/CSV file for the owner. Redacted text is sent only to the model/judge APIs via the pipeline. | must | Fixed point 5 ("inspect by structure only"); the sample contains live keys (found inside `instructions`). |

### 1.3 Project

| ID | Decision | Priority | Why |
|---|---|---|---|
| P1 | **Build and test everything free before the data arrives** (WP-01…07, WP-15/16): when the data lands, the paid part is "run the stage", not "write code under pressure". | must | 4-week deadline; data date unknown. |
| P2 | **Three gates** where money or validity is at stake: Gate 1 budget approval (after real token counts), Gate 2 judge quality (before the main build), Gate 3 freeze (`pre-test` tag before opening the test set). | must | Biggest money/time risks. |
| P3 | **Cheapest-first paid order:** pilot (~$6) before the main build; within each stage, cheap models first, sonnet last; stop on any anomaly (failure rate > 5%, cost per call > 2× estimate). | must | De-risks money. |
| P4 | **(Retired 2026-10-31, D-058: full data arrived.)** Fallback plan if the data is late: trigger date **2026-11-01**. Reduced plan: N_val 300 / N_te 200, K ≤ 6, pilot merged into the main build (owner labels while judging runs). If no data by **2026-11-08**: a sample-only demonstration (labeled sample split by session; clearly labeled "illustrative, underpowered") so the gateway and pipeline can still be shown. | must | Deadline is fixed; the data date is not. |
| P5 | **Git local + private GitHub**, commits authored by Mehrdad Rahmani, one commit per handoff. | must (owner) | Fixed point 9; continuity. |
| P6 | **Report the negative case well:** if UniRoute ≈ ZeroRouter, or everything passes (ceiling), that is a valid finding ("most traffic doesn't need the premium model"); the report explains it with the Ψ table and separability numbers. | must | Credibility with a skeptical reviewer. |

---

## 2. Fixed setup (summary)

| Item | Value |
|---|---|
| Candidates | deepseek-v4-flash · gpt-5.6-luna · gemini-3.5-flash-lite · claude-sonnet-5-5 (anchor/premium) |
| Judge | GPT-5.x class via Metis AI (confirm in WP-04) |
| Splits | by session; val **400**, test **300** (locked), cal 100 items ⊂ val, pilot val 100 ⊂ val; train = all remaining eligible prompts (unlabeled); val/test drawn from the most recent period, stratified by the 4 categories |
| Embedder | **jina-embeddings-v5-text-small** (`clustering` adapter), local; nano as latency fallback (D-048) |
| Vector store | **Qdrant**, local mode (`qdrant/`, git-ignored): K-NN baseline, near-duplicates, semantic cache (D-048) |
| K | {3…8} (+ K = 1 comparison); Eq. 12 (α = 0); nearest centroid; area under the deferral curve; K selected by split-validation (D-061) |
| λ | {0} ∪ 60 log-spaced in [1e-3, 1e2]; quality mode (target set on val) and budget mode both reported |
| Budget | hard cap **$60**; expected ~$25 (pointwise) / ~$35 (pairwise) (§7) |
| Human work | owner labels 100 calibration items (~3 h) + 20 re-labels (~30 min) |
| Deadline | ~4 weeks → assumed **2026-11-17** |

---

## 3. Phases

Each phase lists goal, inputs, tasks, outputs, acceptance checks, time, API cost, dependencies and
owner points. Step-level detail is in the WP files.

### Phase 0: Setup (WP-00)
- **Goal:** a project folder where any session can resume from files alone.
- **Inputs:** this kit's `output/` and inputs; `CONTINUITY.md §8`.
- **Tasks:** create `metis-auto/`, git + private GitHub, `.gitignore`, secret-scan pre-commit, copy
  docs and `ref/`, copy `data.json` into git-ignored `data/raw/`, Python env with **uv**, environment
  `metis-rahnema` (Python 3.12), install the continuity mechanism and test it.
- **Outputs:** repo with first commit; working `/start`, `/handoff`, hooks, status line.
- **Acceptance:** a fresh session shows STATUS in context; a test commit containing a fake key is
  blocked; `/handoff` commits and pushes.
- **Time / cost:** ~0.5 day · $0. **Deps:** none. **Owner:** approve installs (jq, hooks, gh login).

### Phase 1: Free foundations before the data (WP-01…WP-07)
- **Goal:** the whole offline pipeline S1–S12, the evaluation library and the paid-call machinery,
  tested without spending money.
- **Inputs:** sample data (structure + local processing only), spec §0–§9 and App. A.
- **Tasks:** data loader + redaction (WP-01); prompt builder S1, hard-rule detectors, splitter S2
  (WP-02); embedder choice S4 (WP-03); LLM client + call cache + budget guard + Metis AI check
  (WP-04); router core S5/S8–S10, metrics S11, baselines, bootstrap, tested on **synthetic data with a
  planted answer** (WP-05); generation and judge runners, judge prompts, labeling tool, with mocks
  (WP-06); end-to-end dry run on the sample with a mock LLM (WP-07).
- **Outputs:** `src/metis/...` with tests; data card of the sample; embedder decision; cost
  estimator; dry-run report.
- **Acceptance:** all tests green; synthetic test recovers the planted Ψ and the right router ranking;
  BT closed form = fit; α = 0 reproduces Eq. 12; dry run produces a router artifact; rerun = 100%
  cache hits; no outgoing request in dry run contains a key pattern.
- **Time / cost:** ~5 days · $0 (one free model-list call to Metis AI, owner OK).
- **Deps:** WP-00. **Owner:** Metis AI key in `.env`; approve the embedder decision (short).

### Phase 2: Full data in (WP-08)
- **Goal:** clean, split, embed and cluster the real data; real budget.
- **Tasks:** structural inspection + data card; S1 (exclusions counted per rule, incl. huge prompts);
  S2 splits locked (hashes committed, test ids sealed); S4 embeddings; S5 K-means for all K; the owner names
  clusters from a local file of 10 redacted prompts per cluster (~15 min); recompute the budget from real token counts and
  Metis AI prices (§7 formulas).
- **Outputs:** `work/reports/WP-08-report.md` with data card, split table, cluster names, budget memo.
- **Acceptance:** no session in two splits; val/test distributions ≈ recent traffic (language,
  length, category); K candidates {3…⌊N_val/50⌋} with no per-cluster minimum (D-054).
- **Time / cost:** 1–2 days · $0. **Deps:** full dataset, WP-01…07.
- **⛔ Gate 1 (owner):** approve the budget memo (per-stage amounts, under the $60 cap).

### Phase 3: Slim pilot (WP-09, WP-10, WP-11)
- **Goal:** a trustworthy grading method and τ before paying for the full build.
- **Tasks:** WP-09 (paid): 4 models answer the 100 pilot val prompts; judge pointwise (400 calls)
  and pairwise vs sonnet in both orders (600 calls); build the 100-item labeling sheet (blind,
  randomized, ~33 per non-anchor model). WP-10 (owner, ~3 h): label `human_pass` and `human_pref`.
  WP-11: agreement + κ per method, τ by balanced accuracy, separability (D), stability (C, for
  information), bias checks (length, position consistency, self-preference), re-judge noise;
  choose the method; update WP-13 instructions.
- **Outputs:** `work/reports/WP-11-report.md` with the decision table.
- **Acceptance / ⛔ Gate 2:** chosen method: agreement ≥ 75% and κ ≥ 0.40; position consistency
  ≥ 80% (pairwise); no length bias with |ρ| > 0.3. If it fails: revise the rubric once (re-judge
  pilot only, ~$2) and re-check; if it fails again, the owner decides (another judge model, or
  continue with a documented weaker gate).
- **Time / cost:** ~3 days · ~$6 (gen 400 + point 400 + pair 600 calls; + ~$2 if one rubric revision). **Deps:** Gate 1.

### Phase 4: Main build (WP-12, WP-13, WP-14)
- **Goal:** fingerprints, settings and a frozen router artifact.
- **Tasks:** WP-12 generation on remaining val + all test (pilot answers reused; cheap models first;
  resumable); WP-13 judging with the chosen method (+5% re-judge); WP-14 (free): S8 fingerprints,
  S9 K by split-validation (R = 20), S10 λ, the router ladder on validation, representation test
  holdout demo (gemini-3.5-flash-lite), package S12 artifact; write the evaluation protocol;
  **tag `pre-test`** (Gate 3).
- **Outputs:** `router_artifact/v1`, Ψ table with cluster names, validation curves, protocol.
- **Acceptance:** spec §10 checklist items that don't need test; adding a mock model touches only
  its row and λ; rerun = cache hits; artifact hashes recorded.
- **Time / cost:** ~4–5 days · ~$17 pointwise / ~$27 pairwise. **Deps:** Gate 2.
- **Owner:** "go" before WP-12 and WP-13 (each with the estimate).

### Phase 5: Gateway (WP-15…WP-18), in parallel with Phases 2–4
- **Goal:** the brief's gateway around the router, measured by replay.
- **Tasks:** WP-15 core service (rules, router with a mock artifact until v1 exists, LiteLLM calls,
  failover, breaker, traces, fault-injection tests); WP-16 checks + escalation, stickiness option,
  latency measurement; WP-17 semantic cache (**decision point** first); WP-18 replay simulator
  (uses stored answers, judgments and measured latencies; $0) + dashboard.
- **Acceptance:** fault injection: 0 failed requests while one model is "down"; overhead p95
  ≤ 100 ms; cache wrong-hit rate ≤ ~2% by the chosen method; replay reproduces offline router
  choices exactly for the same inputs.
- **Time / cost:** ~5–6 days spread alongside Phases 2–4 · $0 (+ ≤ $1 cache labels if chosen).
- **Deps:** WP-02 (rules), WP-03 (embedder), WP-04 (client); WP-14 for the real artifact.

### Phase 6: Final evaluation (WP-19)
- **Goal:** the one-time test-set result.
- **Tasks:** check `pre-test` tag; run S11 for the ladder + production (cost and similarity only);
  primary and secondary analyses exactly as in the protocol (§8); per-category and per-cluster
  tables; holdout demo; replay test traffic through the gateway (cost, latency, hit rate, escalation);
  a small **live** run (~50 messages per model through the real gateway) for real latency.
- **Outputs:** `work/reports/WP-19-report.md`, `results/` tables and figures.
- **Acceptance:** every number labeled measured/simulated with a CI; protocol followed (any
  deviation written down).
- **Time / cost:** ~2 days · ~$1–2 (live run). **Deps:** Gate 3, WP-18. **Owner:** "go" for the live run.

### Phase 7: Report and release (WP-20, WP-21)
- **Goal:** the course deliverable.
- **Tasks:** report (problem, method, deviations, results with CIs, limitations), draw.io figures
  (§4 style), dashboard + MLflow screenshots, optional pricing model (brief Action 3: fixed vs dynamic
  pricing from the measured cost per query), presentation outline; reproducibility check from a
  fresh clone (rerun from caches = $0), final secret scan, tag `v1.0`.
- **Time / cost:** ~3 days · $0. **Deps:** WP-19.

---

## 4. Phase durations (total ~4 weeks; deadline ~2026-11-17)

The plan is organized by **phases, not weeks** (owner preference). Phases run in order; Phase 5 runs
alongside Phases 2–4.

| Phase | Work packages | Duration | Starts when |
|---|---|---|---|
| 0 Setup | WP-00 | ~½ day | now |
| 1 Free build | WP-01 → WP-07 | ~5 days | after Phase 0 |
| 2 Real data in | WP-08, Gate 1 | 1–2 days | the full dataset arrives |
| 3 Small pilot | WP-09, WP-10 (owner), WP-11, Gate 2 | ~3 days | Gate 1 |
| 4 Main build | WP-12, WP-13, WP-14, Gate 3 | 4–5 days | Gate 2 |
| 5 Gateway | WP-15 → WP-18 | 5–6 days, spread | after WP-02/03/04; WP-18 needs WP-14 |
| 6 Final test | WP-19 | ~2 days | Gate 3 + WP-18 |
| 7 Report and release | WP-20, WP-21 | ~3 days | Phase 6 |

Critical path: data → WP-08 → WP-09 → WP-10 (owner) → WP-11 → WP-12 → WP-13 → WP-14 → WP-19 →
WP-20. **The owner's labeling (WP-10) is on the critical path:** plan ~3 hours within a day of WP-09.
Fallback dates for late data: PLAN P4.

---

## 5. Before the full data vs after

| Can run now ($0) | Must wait for the full data |
|---|---|
| WP-00…WP-07: setup, loader, redaction, prompt builder, rules, splitter, embedder choice, LLM client + cache + budget, router math + evaluation on synthetic data, judge/generation pipeline with mocks, labeling tool, sample dry run | WP-08 real splits/clusters and the real budget; everything paid (WP-09, 12, 13, 17-labels, 19-live) |
| WP-15, WP-16, WP-18 (gateway with a mock artifact; replay on the sample with mock answers) | WP-14 real artifact; WP-19 test evaluation |
| Judge prompt wording, labeling-tool usability test on 5 sample items (owner, 10 min, no API) | WP-10 real labeling |

---

## 6. How results change later phases

The session that produces a result applies the change: it edits the affected `work/WP-*.md`
files, logs a decision in `MASTER_LOG.md`, and updates `ROADMAP.md` if order or dependencies change
(`/handoff` step 5).

| Result (where) | Changes | Edit these files |
|---|---|---|
| Full data size: eligible prompts after S1 (WP-08) | < 1,500: reduced plan (val 300 / test 200, K ≤ 6). 1,500–3,000: spec sizes, K ≤ 6, note weak clustering. ≥ 3,000: as planned | WP-08 report, PLAN §2, WP-09…14, WP-19 |
| Real token counts and Metis AI prices (WP-04, WP-08) | Budget per stage; if pointwise path > $45: shorten `max_tokens`, truncate instructions for the judge earlier, or drop the 5% re-judge | MASTER_LOG §Budget, WP-12/13 settings |
| Share of huge-prompt turns (WP-08) | If > 15%: raise the threshold or truncate instead of exclude (owner decides) | WP-02 config, WP-12 |
| Embedder latency/quality (WP-03) | Model name, max tokens, batch size in configs; gateway latency budget | configs, WP-08, WP-15 |
| Metis AI capabilities (WP-04) | Judge model id; whether prompt-cache discounts apply (E9); concurrency limits | models.yaml, WP-09/12/13, WP-16 |
| Pilot method choice (WP-11) | Pointwise: WP-13 judges 4 × 600 remaining; pairwise: 3 × 600 × 2 (+$10); anchor fixed | WP-13, PLAN §7, WP-14 |
| τ and gate result (WP-11) | τ in judge config; if the gate failed twice → owner decision | WP-13, MASTER_LOG |
| Separability D low / ceiling (WP-11, WP-14) | Raise τ (free, from stored scores) or switch to pairwise; report framing changes to "ceiling" (P6) | WP-14, WP-19, WP-20 |
| Bias checks (WP-11) | Length bias → length-controlled analysis added to WP-19; self-preference → flag gpt-5.6-luna results | WP-19 |
| K* and λ (WP-14) | Artifact v1 shipped by the gateway | WP-15/16 config, WP-18, WP-19 |
| UniRoute vs baselines on val (WP-14) | Report framing only (UniRoute ships regardless, M1) | WP-19, WP-20 |
| Escalation/failure rates in replay (WP-18) | Check thresholds; fallback order | WP-16 |
| Cache decision (WP-17) | Cache on/off and threshold in gateway config | WP-18, WP-19 |
| Data late (calendar) | P4 reduced plan or sample-only demo | ROADMAP, PLAN §4 |

---

## 7. Budget

### 7.1 Formulas (spec §9, adapted)

Let N = 4 models, N_val = 400, N_te = 300, M = N_val + N_te = 700, P = 100 pilot prompts (⊂ val),
J = 2, T_in / T_out = mean input / output tokens of eligible turns, p_in / p_out = prices per token.

- Generation calls: `G = N · M = 2,800` · cost `Σ_h M · (T_in · p_in(h) + T_out(h) · p_out(h))`
- Pointwise judging: `N · M = 2,800` calls
- Pairwise judging (full): `(N − 1) · M · J = 4,200` calls
- Pilot extra pairwise: `(N − 1) · P · J = 600` calls (the pilot pointwise calls are part of the 2,800)
- Re-judge 5%: `0.05 · 2,800 = 140` calls
- Add a model later: pointwise `2 · N_val = 800`; pairwise `N_val · (1 + J) = 1,200`

### 7.2 Estimate (assumptions: T_in = 1,640, T_out = 300 with `max_tokens` = 1,024, list prices from PLANNING-REQUEST §3, judge $0.002–0.006 per call; **no** prompt-cache discount; recomputed at Gate 1)

| Item | Calls | Low | Mid | High |
|---|---|---|---|---|
| Generation: deepseek-v4-flash ($0.00031/call) | 700 | | $0.22 | |
| Generation: gpt-5.6-luna ($0.00069) | 700 | | $0.48 | |
| Generation: gemini-3.5-flash-lite ($0.0012) | 700 | | $0.87 | |
| Generation: claude-sonnet-5-5 ($0.0063) | 700 | | $4.40 | |
| **Generation total** | 2,800 | $4.5 | **$6.0** | $8.0 |
| Pilot pairwise extra | 600 | $1.5 | **$3.0** | $4.5 |
| Main judging, pointwise | 2,800 | $5.6 | **$11.2** | $16.8 |
| Re-judge 5% | 140 | $0.3 | **$0.6** | $0.8 |
| Rubric revision (only if Gate 2 fails once) | ~500 | $0 | $0 | $2.5 |
| Cache labels (if chosen at WP-17) | ~300 | $0 | **$1.0** | $1.8 |
| Live latency run (WP-19) | ~250 | $0.8 | **$1.5** | $2.5 |
| **Total, pointwise path** | ~7,000 | **$15** | **$25** | **$39** |
| Extra if pairwise is chosen (4,200 − 2,800 calls, longer prompts) | +1,400 | +$5 | **+$10** | +$15 |
| **Total, pairwise path** | ~8,400 | $20 | **$35** | **$54** |

Hard cap **$60**; every paid stage has its own approved amount (Gate 1). Metis AI may add a margin
over list prices or price in another currency; WP-04 records real prices and WP-08 recomputes.
Sonnet is ~73% of the generation cost (recomputed for the D-056 models; totals below it not yet); that is why the strong model goes last in each run.

---

## 8. Statistics and evaluation protocol

### 8.1 What is measured

- **Primary quality:** pass rate `Q_pt` (pointwise) or win rate vs anchor `Q_pw` (pairwise), per
  spec §7, on the locked test set.
- **Primary comparison:** the shipped router at its pre-registered λ vs always-best (sonnet):
  cost reduction and quality difference, paired by prompt.
- **Secondary:** deferral area and QNC for the whole ladder; per-cluster and per-category quality;
  routing share; similarity to production; cache hit rate; latency p50/p90; escalation rate;
  holdout demo.

### 8.2 Power with N_val = 400 / N_te = 300 (owner's choice) and what it means

- **Fingerprints:** with ~50 val prompts per cluster, the standard error of a fail rate of 0.2 is
  ~0.057 (95% CI ±0.11). Two models are distinguishable in a cluster only if their fail rates differ
  by ~0.16+. So K* will be small, and Ψ must be shown with its counts and CIs.
- **Test comparison:** with 300 paired prompts and ~20% discordant pairs, the 95% CI on the quality
  difference is about **±5 points**. "At most 2 points lower" can be the target point estimate but
  **cannot be proven**. Pre-registered success criterion (replaces the proposal's):
  1. cost per query ≥ 40% lower than always-best, **and**
  2. the lower bound of the 95% CI of (router − always-best) quality ≥ **−5 points**
     (non-inferiority margin 5 points), **and**
  3. p90 latency (replay with measured latencies) ≤ always-best's.
- **Router vs router** (UniRoute vs ZeroRouter/K-NN): paired bootstrap CI of the area difference;
  "no significant difference" is an acceptable, reportable result.

### 8.3 Tests and intervals

- Paired **bootstrap over prompts** (10,000 resamples, recorded seed) for every difference and area;
  **exact McNemar** for pass/fail differences at a fixed λ; Wilson intervals for single rates;
  Cohen's κ for judge–human agreement.
- One primary comparison (no multiplicity correction); everything else labeled exploratory.
- The protocol (metrics, λ, margins, analyses) is committed with the `pre-test` tag (M16).

### 8.4 Overfitting checks ($0)

Locked test; K by split-validation (R = 20); K = 1 baseline; fingerprint stability (C);
separability (D); val-vs-test gap; α = 2 smoothing reported only as a robustness check.

---

## 9. Risks and mitigations

| # | Risk | Likelihood / impact | Mitigation | Early signal |
|---|---|---|---|---|
| R1 | Full data late | medium / high | P1 (all free work first), P4 fallback dates | no data by 11-01 |
| R2 | Data smaller or messier than promised | medium / medium | §6 size rows; data card in WP-08 | WP-08 counts |
| R3 | Judge unreliable in Persian | medium / high | Gate 2 with κ; rubric revision; bias checks; alternative judge | WP-11 agreement |
| R4 | Ceiling: every model passes | medium / medium | τ from stored scores, pairwise option, P6 framing | WP-11 separability D |
| R5 | UniRoute no better than simple routers | high / low (if framed well) | M1 ladder, M2 primary result | WP-14 validation curves |
| R6 | One labeler (owner) = no inter-annotator agreement | certain / medium | intra-rater re-label (M11), blind randomized tool, clear guideline | WP-10 |
| R7 | Owner labeling delays the critical path | medium / high | labeling tool ready in WP-06; book the 3 hours in advance | WP-09 done |
| R8 | Metis AI lacks a model, has rate limits, or prices differ | medium / medium | WP-04 check before any data; OpenRouter as a backup route | WP-04 |
| R9 | Secret leak (keys in data) | low / severe | E13: redaction, outgoing-request scan, pre-commit, push protection | tests |
| R10 | Budget overrun | low / medium | E12 guard, per-stage approval, sonnet last, stop on anomalies | ledger |
| R11 | Session loss / context compaction loses work | medium / medium | `CONTINUITY.md` mechanism, caches, checkpoints | hooks |
| R12 | Huge system prompts distort costs | certain / medium | M7 exclusion, report share | WP-08 |
| R13 | Single aggregator makes failover partly simulated | certain / low | E3 honest framing + fault injection; optional 2nd route | WP-15 |
| R14 | Model versions change mid-project | low / medium | record returned versions; generate each model in one short window | WP-12 logs |
| R15 | Pro usage limits slow the work (all sessions on Opus 5.5, D-027) | medium / medium | status line shows 5-hour usage, small sessions; fallback: Sonnet for routine WPs (`CONTINUITY.md §7`) | status line |
| R16 | Hidden reasoning ("thinking") tokens inflate cost (gemini-3.5-flash-lite, deepseek, GPT-5.x judge) | medium / medium | thinking off/minimal for candidates (WP-06 gen_config), lowest reasoning effort for the judge; budget guard stops at 2× estimated cost per call | WP-09 cost per call |
| R17 | **Network split:** Metis AI (metisai.ir, api., docs.) was unreachable from this machine on 2026-10-20 (TLS connection reset), likely because the connection used by Claude Code (e.g. a VPN) cannot reach Iranian services, and vice versa | medium / high | WP-04 tests reachability first; paid runs are plain scripts the owner can start from a terminal on a network that reaches Metis AI (outside the Claude session if needed; the cache makes results visible to the next session); fallback provider route (e.g. OpenRouter) for the same models | WP-04 step 9 |

---

## 10. Target repository layout (`metis-auto/`)

```
metis-auto/
├── CLAUDE.md  AGENTS.md  STATUS.md  ROADMAP.md  MASTER_LOG.md
├── PLAN.md  PROJECT.md  CONTINUITY.md
├── work/                 WP-00-*.md … WP-21-*.md, reports/WP-xx-report.md
├── ref/                  copied inputs: UNIROUTE_PIPELINE.md, proposal/, docs/, papers/, diagrams/
├── configs/              models.yaml (prices + date), gen_config.yaml, judge_config.yaml,
│                         pipeline.yaml (K, α, λ grid, seeds), budget.yaml, gateway.yaml
├── src/metis/
│   ├── data/             load.py, redact.py, normalize.py, prompts.py (S1), split.py (S2), rules.py
│   ├── embed/            embedder.py (S4), store.py (Qdrant)
│   ├── llm/              client.py (LiteLLM → Metis AI), callcache.py, budget.py, runner.py (resumable)
│   ├── judge/            templates/, pointwise.py, pairwise.py, parse.py, calibration.py
│   ├── router/           kmeans.py (S5), fingerprints.py + bt.py (S8), select_k.py (S9),
│   │                     select_lambda.py (S10), artifact.py (S12), route.py (§5)
│   ├── eval/             metrics.py (area, QNC), baselines.py, stats.py (bootstrap, McNemar, κ), report.py
│   ├── gateway/          app.py (FastAPI), rules.py, cache.py, checks.py, failover.py, traces.py
│   ├── sim/              replay.py
│   └── labeling/         tool (local HTML or terminal; blind, randomized)
├── scripts/              one CLI per stage: s1_ingest … s12_package, pilot_*, eval_test
├── tests/                unit tests + synthetic-data tests + fault injection
├── dashboard/            static HTML or Streamlit app over traces/results
├── qdrant/               git-ignored local Qdrant store (vectors + ids, no text)
├── mlflow/               git-ignored local MLflow store (traces, runs; redacted text only)
├── artifacts/            router_v1/ (frozen router: centroids, Ψ, ĉ, λ, configs, hashes; no text)
├── results/              committed aggregates only (tables, figures; no prompt/answer text)
├── report/               final report sources + figures
├── diagrams/             draw.io sources + exports
├── data/  cache/  runs/  git-ignored: raw data, call cache (SQLite), per-stage outputs
├── .claude/              settings.json, hooks/, skills/start, skills/handoff, statusline.sh
└── .githooks/pre-commit  secret scan
```

---

## 11. Owner decision points (all in one place)

| When | Decision | Default if no answer |
|---|---|---|
| WP-00 | Approve installs (hooks, skills, jq, gh), GitHub repo creation | wait |
| WP-03 | Embedder check | Jina v5-small OK (latency, Persian, clusters) or nano |
| WP-04 | Metis AI key in `.env`; confirm judge model id | wait |
| WP-08 | Name the clusters from a local sample file (~15 min) | wait |
| WP-08 | **Gate 1:** budget memo; huge-prompt threshold if > 15% excluded | wait |
| WP-09 | "Go" for the pilot spend (~$6) | wait |
| WP-10 | Label 100 items (~3 h) + 20 re-labels | wait (critical path) |
| WP-11 | **Gate 2:** accept the method/τ; what to do if the gate fails twice | wait |
| WP-12 / WP-13 | "Go" for each paid run with its estimate | wait |
| WP-14 | Read the evaluation protocol before the freeze | wait |
| WP-17 | **Cache threshold method** (deferred decision) | AI-grader labels (≤ $1) |
| WP-19 | **Gate 3** is automatic (tag exists); "go" for the live latency run (~$1.5) | wait |
| Any time | Deviations DEV-2…DEV-10 (§1); deadline or data-date changes | — |

Deviations: ~~DEV-1~~ (withdrawn: no instruction traits) · **DEV-2**
per-chatbot system prompt in generation (agreed) · **DEV-3** slim pilot (agreed) · **DEV-4** balanced
accuracy + κ in the gate · **DEV-5** judge prompt extended with instructions/context · **DEV-6**
R = 20 split-validation repeats (agreed, D-061) · **DEV-7** paper-faithful
clustering/routing: α = 0, nearest centroid, no n_min drop (owner-requested, agreed) · **DEV-8**
embedding input = current user message only, no context turns (owner decision, agreed) · **DEV-9**
judge input = current user message only (spec A1/A2 `{context_turns}` dropped; generation keeps the
history, M6; owner decision, agreed).
