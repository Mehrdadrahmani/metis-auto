# Graph Report - metis-auto  (2026-11-01)

## Corpus Check
- 163 files · ~158,983 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 13, .tex 13, .drawio 8)

## Summary
- 1489 nodes · 2994 edges · 119 communities (88 shown, 31 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 227 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b5a4dd4e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Offline build diagram (S1-S12)
- System overview diagram (offline build + online gateway)
- Data card: `sample.json` (structure only)
- UniRoute Paper Concepts
- Roadmap and Phases
- ext_download.py
- test_rules.py
- UniRoute Pipeline Spec
- k_6
- ndarray
- manifest.json
- s4
- UniRoute's embedding + clustering step on public Persian data
- s4_persian_cluster.py
- config.py
- LLM routing state of the art (research)
- Final Eval and Release
- kmeans.py
- Gateway, Cache, Replay WPs
- UniRoute paper notes
- pytest
- Pilot Decision and Judging
- Session Protocol Docs
- S1 + S2 counts on the sample (WP-02 dry run)
- WP-04 LLM Client, Cache, Budget
- Report notes (running)
- WP-02 Prompts and Splits
- Bootstrap and Environment
- Model Registry Fields
- Decision Register
- Router Core WP-05
- Checks and Escalation
- Persian clustering test: the UniRoute paper's embedding + K-means step with Jina v5 (WP-03b)
- Judging Methods
- System Design and Gateway
- WP-09 Pilot Run
- Bootstrap and Secret Scan
- Gates and Integrity
- Proposal: Metis-Auto v2
- Data Access WP-01
- Generation WP-12
- Fingerprints and Freeze
- UniRoute Router Design
- Gateway Observability
- Embedder benchmark (WP-03 step 5)
- test_router_baselines.py
- results/README.md
- Owner Fixed Points
- test_redact.py
- Metis AI and Risks
- Fingerprint Ψ_k(h)
- run.py
- WP Template
- Evaluation Protocol
- Status Line
- Graphify Integration
- Context Guard Hook
- Post-compact Hook
- Pre-compact Hook
- Session-start Hook
- Context and Usage Guard
- metis Package
- test_load_parquet.py
- data_card_full.py
- Data card: full dataset (structure only)
- ladder
- ZeroRouter
- select_lambda.py
- baselines.py
- KNNRouter
- similarity
- bot_clusters/README.md
- budget_memo.md
- ._merge
- test_split.py
- WP-03b: Persian clustering test on public data (embedding + K-means only)
- Data selection criteria
- test_normalize_lang.py
- API costs diagram
- test_router_select.py
- json
- WP-03b report: Persian clustering test
- metrics.py
- qdrant
- route.py
- test_router_synthetic.py
- s4_embed_bench.py
- s4_latex_tables.py
- bt.py
- test_embed.py
- synthetic_validation.py
- UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)
- test_router_core.py
- WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)
- Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute
- nano
- What exists
- WP-03 report: Embedder + Qdrant
- router
- Synthetic validation of the router (WP-05 step 9)
- s2
- k_rule_review.md
- pipeline.yaml
- s1

## God Nodes (most connected - your core abstractions)
1. `UniRoute Pipeline Specification` - 40 edges
2. `Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute` - 27 edges
3. `Roadmap diagram (WP-00..WP-21)` - 27 edges
4. `Embedder` - 24 edges
5. `main()` - 23 edges
6. `ladder()` - 23 edges
7. `Offline build diagram (S1-S12)` - 22 edges
8. `System overview diagram (offline build + online gateway)` - 22 edges
9. `main()` - 21 edges
10. `UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Findings` --references--> `area()`  [INFERRED]
  work/reports/WP-05-report.md → src/metis/eval/metrics.py
- `Must check in step 9 (found in WP-05a)` --references--> `test_s9_runtime_under_two_minutes()`  [INFERRED]
  work/WP-05b-baselines-stats-synthetic.md → tests/test_router_select.py
- `What exists` --references--> `fingerprints()`  [INFERRED]
  work/reports/WP-05-report.md → src/metis/router/fingerprints.py
- `What exists` --references--> `route()`  [INFERRED]
  work/reports/WP-05-report.md → src/metis/router/route.py
- `What exists` --references--> `select_k()`  [INFERRED]
  work/reports/WP-05-report.md → src/metis/router/select_k.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Gateway components required by the brief** — plan_gateway_fastapi, plan_semantic_cache, plan_cascade_escalation, plan_honest_failover, plan_observability [EXTRACTED 1.00]
- **Gateway reliability layer (failover, checks, cascade)** — ref_diagrams_03_online_path_g5, ref_diagrams_03_online_path_failover, ref_diagrams_03_online_path_g6, ref_diagrams_03_online_path_cascade [EXTRACTED 1.00]
- **Gateway parts required by the brief** — ref_docs_design_semantic_cache, ref_docs_design_failover_circuit_breaker, ref_docs_design_checks_escalation, ref_docs_design_trace, ref_docs_design_hard_rules [EXTRACTED 1.00]
- **Maintenance without retraining (M1-M4)** — ref_diagrams_05_uniroute_m1, ref_diagrams_05_uniroute_m2, ref_diagrams_05_uniroute_m3, ref_diagrams_05_uniroute_m4 [EXTRACTED 1.00]
- **Paid-call infrastructure (cache, budget, runner)** — work_wp_04_llm_client_cache_budget_callcache, work_wp_04_llm_client_cache_budget_budget_guard, work_wp_04_llm_client_cache_budget_run_batch [EXTRACTED 1.00]
- **Pilot label-method decision** — ref_uniroute_pipeline_label_method_pilot, ref_uniroute_pipeline_pointwise_judging, ref_uniroute_pipeline_pairwise_judging, ref_uniroute_pipeline_s_cal, ref_uniroute_pipeline_judge_human_gate [EXTRACTED 1.00]
- **Baselines compared in dynamic-pool experiments** — ref_papers_uniroute_iclr_2026_zerorouter, ref_papers_uniroute_iclr_2026_knn_router, ref_papers_uniroute_iclr_2026_retrained_mlp, ref_papers_uniroute_iclr_2026_retrained_matfac, ref_papers_uniroute_iclr_2026_clairvoyant_oracles [EXTRACTED 1.00]
- **Router evaluation via deferral curves** — ref_papers_uniroute_iclr_2026_deferral_curve, ref_papers_uniroute_iclr_2026_qnc, ref_papers_uniroute_iclr_2026_area_deferral, ref_papers_uniroute_iclr_2026_lambda_cost_tradeoff [EXTRACTED 1.00]
- **UniRoute K-Means pipeline: cluster train set, per-cluster val errors, cost-adjusted argmin** — ref_papers_uniroute_iclr_2026_unlabeled_training_set, ref_papers_uniroute_iclr_2026_kmeans, ref_papers_uniroute_iclr_2026_validation_set, ref_papers_uniroute_iclr_2026_per_cluster_error, ref_papers_uniroute_iclr_2026_plugin_router, ref_papers_uniroute_iclr_2026_lambda_cost_tradeoff [EXTRACTED 1.00]
- **Router build S8-S12** — work_wp_14_fingerprints_freeze_s8_fingerprints, work_wp_14_fingerprints_freeze_s9_k_selection, work_wp_14_fingerprints_freeze_s10_lambda, work_wp_14_fingerprints_freeze_router_artifact_v1 [EXTRACTED 1.00]
- **Session continuity mechanism** — status_doc, _claude_skills_start_skill_start_skill, _claude_skills_handoff_skill_handoff_skill, continuity_hooks, continuity_context_guard, continuity_status_line [EXTRACTED 1.00]
- **UniRoute offline build flow (embed→cluster→judge→fingerprint→route)** — ref_uniroute_pipeline_s4_embed, ref_uniroute_pipeline_s5_kmeans, ref_uniroute_pipeline_s6_generate, ref_uniroute_pipeline_pointwise_judging, ref_uniroute_pipeline_fingerprint_psi, ref_uniroute_pipeline_online_routing_rule [EXTRACTED 1.00]
- **UniRoute online routing flow (embed, nearest cluster, score, route)** — ref_diagrams_05_uniroute_r1, ref_diagrams_05_uniroute_r2, ref_diagrams_05_uniroute_r3, ref_diagrams_05_uniroute_r4 [EXTRACTED 1.00]
- **UniRoute router core (clusters, fingerprints, routing, selection)** — work_wp_05_router_core_eval_kmeans_s5, work_wp_05_router_core_eval_fingerprints, work_wp_05_router_core_eval_route, work_wp_05_router_core_eval_select_k_lambda [EXTRACTED 1.00]
- **Gateway request pipeline components** — work_wp_15_gateway_core_gateway_pipeline_g1_g7, work_wp_15_gateway_core_failover, work_wp_15_gateway_core_traces, work_wp_16_checks_escalation_checks, work_wp_17_semantic_cache_cache, work_wp_16_checks_escalation_escalation_policy [INFERRED 0.85]
- **Redaction safety chain (redact, outgoing guard, leak test)** — work_wp_01_data_access_redact, work_wp_04_llm_client_cache_budget_llm_client, work_wp_07_dry_run_leak_test, work_wp_06_gen_judge_pipeline_messages_builder [INFERRED 0.85]
- **Test-set sealing and single-look evaluation** — work_wp_13_judging_labels_test_sealed, work_wp_14_fingerprints_freeze_gate_3_pre_test_tag, work_wp_19_final_evaluation_eval_test_script, work_wp_14_fingerprints_freeze_eval_protocol [INFERRED 0.85]
- **UniRoute routing method** — plan_uniroute_router, plan_embedder_jina, plan_fingerprint_psi, plan_lambda_cost_weight, master_log_d_040_paper_faithful [INFERRED 0.85]

## Communities (119 total, 31 thin omitted)

### Community 0 - "Offline build diagram (S1-S12)"
Cohesion: 0.18
Nodes (21): Judge-human agreement >= 75%?, Offline build diagram (S1-S12), Pilot (section P): 4 models, 200 val, 150 test, criteria A-D, tie -> pointwise, Revise rubric / tau, S1 Ingest & clean (last user msg + <=2 turns, redact, language tag, de-dup), S10 Choose lambda: quality target or cost budget, S11 Evaluate on S_te (UniRoute vs always-best, always-cheapest, ZeroRouter, K-NN), S12 Router artifact (versioned: method, embedder, K, centroids, Psi, c, lambda, hashes) (+13 more)

### Community 1 - "System overview diagram (offline build + online gateway)"
Cohesion: 0.08
Nodes (51): Answer, Cache hit?, Call model + failover, Code checks + escalation, Choose K and lambda on validation, Clean, redact secrets, split by conversation, System overview diagram (offline build + online gateway), Embed locally + K-means (no API calls) (+43 more)

### Community 2 - "Data card: `sample.json` (structure only)"
Cohesion: 0.19
Nodes (19): Categorical value sets, Counts, Data card: `sample.json` (structure only), Key paths, Models (bot messages), Providers, Redaction hits, Roles (+11 more)

### Community 3 - "UniRoute Paper Concepts"
Cohesion: 0.08
Nodes (35): Area under the deferral curve, Bradley-Terry-Luce model for per-cluster scores, Chatbot Arena (Zheng et al. 2023), Clairvoyant MLP / MatFac oracle baselines, Cluster membership map Phi_clust(x), Deferral curve (quality vs cost), Routing with a dynamic LLM pool, EmbedLLM benchmark (Zhuang et al. 2024) (+27 more)

### Community 4 - "Roadmap and Phases"
Cohesion: 0.11
Nodes (37): Roadmap diagram (WP-00..WP-21), Full dataset arrives, Gate 1: owner approves budget, Gate 2: agreement >= 75%, kappa >= 0.40, Gate 3: git tag pre-test, WP-00 Bootstrap (git, GitHub, session mechanism), WP-01 Data + redaction (safe loader, data card), WP-02 Prompts, rules, splits (S1, S2, hard rules) (+29 more)

### Community 5 - "ext_download.py"
Cohesion: 0.10
Nodes (11): arena100(), arena140(), build(), filtered(), get_json(), hf_request(), HTTPRange, log() (+3 more)

### Community 7 - "UniRoute Pipeline Spec"
Cohesion: 0.18
Nodes (16): Anchor model (pairwise), Data artifacts schemas (§3), UniRoute Pipeline Specification, Deferral area and QNC, Experiment mode (holdout unseen models), K-NN router baseline, LearnedMap (out of scope), S11 Evaluate on test vs baselines (+8 more)

### Community 8 - "k_6"
Cohesion: 0.08
Nodes (23): k_3, 0, 1, 2, k_4, 0, 1, 2 (+15 more)

### Community 9 - "ndarray"
Cohesion: 0.15
Nodes (7): LogisticRouter, LossRouter, lower_hull(), UniRoute, test_hull_drops_dominated_and_not_convex_models(), test_logistic_learns_the_type_and_handles_a_constant_model(), test_uniroute_interface_matches_route()

### Community 10 - "manifest.json"
Cohesion: 0.08
Nodes (34): config_id, cost_usd, difference, No structure, Planted structure, duration_s, 3, 4 (+26 more)

### Community 11 - "s4"
Cohesion: 0.18
Nodes (11): s4, batch_size, cache_task, choice, device, dtype, max_batch_tokens, max_tokens (+3 more)

### Community 12 - "UniRoute's embedding + clustering step on public Persian data"
Cohesion: 0.11
Nodes (16): 10. Next steps (proposals, need the owner's OK), 1. What UniRoute does, and what we tested, 2. Data, 3. Do the clusters follow real topics?, 4. What is inside the clusters? (nano, K = 8, one split, test prompts), 5. Cluster maps, 6. Would these clusters help routing? (human-difficulty test), 7. small vs nano (and the text-matching adapter) (+8 more)

### Community 13 - "s4_persian_cluster.py"
Cohesion: 0.07
Nodes (35): main(), mix_table(), features(), labelled(), main(), curve(), k_curves(), main() (+27 more)

### Community 14 - "config.py"
Cohesion: 0.14
Nodes (7): embedder(), main(), run_embed(), run_near_dups(), config_id(), load_config(), collection_name()

### Community 15 - "LLM routing state of the art (research)"
Cohesion: 0.29
Nodes (6): DARS: one answer per prompt is noisy, LLM routing state of the art (research), RouterArena finding: routers too cautious, Routing approach families (RouteLLM, cascades, bandits...), Routing and cascading survey (arXiv 2603.04445), Three-stage router/check/escalate architecture

### Community 16 - "Final Eval and Release"
Cohesion: 0.12
Nodes (17): runs/s7/labels_test.sealed.parquet (sealed), results/eval_protocol.md, WP-19: Final evaluation on test set, scripts/eval_test.py, Live latency run (stage live, ~$1.5, val messages), Primary analysis: router vs always-best (paired bootstrap, McNemar), Production comparison (cost, answer similarity, M15), results/final/ (+9 more)

### Community 17 - "kmeans.py"
Cohesion: 0.19
Nodes (10): candidate_ks(), cluster_counts(), fit_all(), fit_kmeans(), KMeansModel, blobs(), test_assign_is_nearest_centroid(), test_candidates_follow_the_paper() (+2 more)

### Community 18 - "Gateway, Cache, Replay WPs"
Cohesion: 0.13
Nodes (16): MLflow experiment router-selection (D-044), WP-15: Gateway core, scripts/gateway_smoke.py, configs/gateway.yaml, LiteLLM via Metis AI, gateway/mock_provider.py, OpenAI-compatible API (POST /v1/chat/completions), gateway/traces.py (SQLite traces + MLflow spans) (+8 more)

### Community 19 - "UniRoute paper notes"
Cohesion: 0.25
Nodes (4): UniRoute paper notes, Paper experimental facts (datasets, val 400, Gecko), Ideas for later (attribute clusters, coreset, budget control), UniRoute paper (Jitkrittum et al., ICLR 2026)

### Community 20 - "pytest"
Cohesion: 0.16
Nodes (5): path(), test_bad_structure(), test_strict_raises_without_content(), test_ceiling_flag_and_range(), test_fits_context()

### Community 21 - "Pilot Decision and Judging"
Cohesion: 0.16
Nodes (12): WP-11: Pilot decision (Gate 2), Bias and noise checks (length bias, self-preference, test-retest), Human calibration labels (cal_labels.csv), configs/judge_config.yaml, Pairwise judging, results/pilot_decision.md, Pointwise judging, One rubric revision fallback (DEV-5) (+4 more)

### Community 22 - "Session Protocol Docs"
Cohesion: 0.31
Nodes (13): /handoff skill, /start skill, AGENTS.md rules and session protocol, CLAUDE.md project pointers, CONTINUITY.md session mechanism, Claude Code hooks (SessionStart, UserPromptSubmit, PreCompact, PostCompact), STATUS.md template, Work-package sizing (100k-250k tokens) (+5 more)

### Community 23 - "S1 + S2 counts on the sample (WP-02 dry run)"
Cohesion: 0.25
Nodes (7): Exclusions (labeled sets), Language, S1: prompt rows, S1 + S2 counts on the sample (WP-02 dry run), S2: split (by session), Size estimates (chars / 3), Widget clicks

### Community 24 - "WP-04 LLM Client, Cache, Budget"
Cohesion: 0.32
Nodes (8): WP-04 LLM Client, Cache, Budget, Budget guard (budget.py, hard cap $60), Call cache SQLite (callcache.py), Metis AI capability check, MLflow local tracing (D-044), Mock mode METIS_MOCK=1, run_batch runner (runner.py), Gate 1 budget approval

### Community 25 - "Report notes (running)"
Cohesion: 0.22
Nodes (6): S1 Ingest & clean prompts, S4 Embed (frozen multilingual local), Report notes (running), Jina v5-text-small embedder + Qdrant local (D-048), D-044 local MLflow tracing, Secrets in the data: 44 redaction hits

### Community 26 - "WP-02 Prompts and Splits"
Cohesion: 0.31
Nodes (9): WP-02 Report, Sample exclusion waterfall (434 rows, 375 LLM replies, 343 eligible), WP-02 Prompt Builder, Hard Rules, Splitter, eligible_labeled filter, lang_tag (lang.py), Persian normalization (normalize.py), prompts table S1 (prompts.py), Seed 20261020 (+1 more)

### Community 27 - "Bootstrap and Environment"
Cohesion: 0.17
Nodes (11): uv virtual environment metis-rahnema, Budget ledger ($60 cap, $0 spent), Open questions (Q-001..Q-022), Q-017 Metis AI reachability (VPN), Q-020 K selection report cards, Budget estimate (~$25 pointwise / ~$35 pairwise), Budget guard in code (E12), Target repository layout (+3 more)

### Community 28 - "Model Registry Fields"
Cohesion: 0.12
Nodes (16): models, api_name, context_window, exp_role, id, is_anchor, price_in, price_out (+8 more)

### Community 29 - "Decision Register"
Cohesion: 0.21
Nodes (6): Decision register (D-001..D-050), Spec deviations DEV-1..DEV-9, Embedder jina-embeddings-v5-text-small, Qdrant local vector store, WP-03 Embedder + Qdrant, WP-03 step 5 embed benchmark pending (Low Power Mode)

### Community 30 - "Router Core WP-05"
Cohesion: 0.33
Nodes (9): WP-05 Router Core and Evaluation, Bradley-Terry S8-PW vs anchor, Fingerprints S8-PT (Eq. 12, alpha=0), K-means clustering S5 (nearest centroid, DEV-7), Pareto area and QNC metrics (eval/metrics.py), route() (router/route.py), Router artifact S12, select_k (S9, R=20) and select_lambda (S10) (+1 more)

### Community 31 - "Checks and Escalation"
Cohesion: 0.21
Nodes (11): Router artifact v1 (artifacts/router_v1/), gateway/failover.py with circuit breaker, Gateway pipeline G1-G7 (rules, embed, cache, route, call, checks, trace), Jina v5-small embedder, current user message only (D-045, D-048), WP-16: Quality checks and escalation, gateway/checks.py (empty, truncated, wrong_language, bad_json, refusal), results/gateway_latency.md benchmark, Prompt-cache cost model (estimate_cost) (+3 more)

### Community 32 - "Persian clustering test: the UniRoute paper's embedding + K-means step with Jina v5 (WP-03b)"
Cohesion: 0.25
Nodes (7): 1. What we did (= paper §5.1, §6, App. G.1–G.3, Gecko → Jina), 2. Results, 3. Does clustering help routing? (human-difficulty test, Khayyam), 4. What this tells us (plain), 5. Limits, Owner questions, Persian clustering test: the UniRoute paper's embedding + K-means step with Jina v5 (WP-03b)

### Community 33 - "Judging Methods"
Cohesion: 0.28
Nodes (7): S8-PW Bradley-Terry per-cluster fingerprint, Judge prompts (Appendix A1/A2), Label-method pilot (§P), S7-PW Pairwise judging vs anchor, S7-PT Pointwise judging, S6 Generate answers, S8-PT smoothed fail rate (Eq. 12, alpha)

### Community 34 - "System Design and Gateway"
Cohesion: 0.31
Nodes (10): Candidate models and judge, G6 Checks + escalation (cascade), Metis-Auto v2 system design, G5 Call + failover, circuit breaker, Goals G1-G7 and success criteria, G1 Hard rules, Online gateway G1-G7, Design risks and mitigations (+2 more)

### Community 35 - "WP-09 Pilot Run"
Cohesion: 0.33
Nodes (7): Statistics: bootstrap, McNemar, kappa (eval/stats.py), Local HTML labeling tool, WP-09 Pilot Run, Judge test-retest noise sample, Slim pilot (M8, DEV-3), WP-10 Owner Labels Calibration Set, Gate 2 (judge agreement >=75%, kappa>=0.40)

### Community 36 - "Bootstrap and Secret Scan"
Cohesion: 0.24
Nodes (9): WP-00 Report, Q-022 GitHub secret scanning unavailable, WP-00 Bootstrap, Continuity mechanism (hooks, statusline, /start, /handoff), Private GitHub repo metis-auto, gitignore of data/cache/runs/.env, Pre-commit secret scan hook, uv environment metis-rahnema (+1 more)

### Community 37 - "Gates and Integrity"
Cohesion: 0.22
Nodes (6): Three gates (budget, judge, freeze), Phases 0-7, WP-08 Full data in, WP-10 Owner labels, WP-14 Fingerprints, settings, freeze, Blockers: full dataset not arrived (Q-001)

### Community 38 - "Proposal: Metis-Auto v2"
Cohesion: 0.17
Nodes (11): Continuing work across sessions (§5c), Planning deliverables (PLAN, CONTINUITY, ROADMAP, AGENTS, CLAUDE, MASTER_LOG, PROJECT), Planning request: Metis-Auto v2, Open questions Q-001..Q-009, Sample dataset (100 sessions, 907 messages), Decisions needed, Proposal: Metis-Auto v2, Proposal evaluation strategies and success criteria (+3 more)

### Community 39 - "Data Access WP-01"
Cohesion: 0.21
Nodes (12): WP-01 Report, WP-01 Data Access and Redaction, Structure-only data card (scripts/data_card.py), load_dataset (src/metis/data/load.py), redact / redact_message (src/metis/data/redact.py), src/metis/data/schema.py dataclasses, LLM client complete() with outgoing guard, WP-06 Generation and Judge Pipeline (+4 more)

### Community 40 - "Generation WP-12"
Cohesion: 0.25
Nodes (7): WP-12: Answer generation (S6), Anomaly monitoring after 50 calls, Budget stage gen_main (~$7), Measured latency per call (for replay), runs/s6/responses.parquet, scripts/s6_generate.py, sim/replay.py replay simulator

### Community 41 - "Fingerprints and Freeze"
Cohesion: 0.25
Nodes (7): runs/s7/labels_val.parquet, WP-14: Fingerprints, K, lambda, freeze (Gate 3), Baselines: always-cheapest, always-best, ZeroRouter, K-NN, Holdout demo (gemini-2.5-flash hidden, M4), S10 lambda (quality mode primary, budget mode), S8 fingerprints Psi (Eq. 12, alpha=0), UniRoute (ships regardless, M1)

### Community 42 - "UniRoute Router Design"
Cohesion: 0.32
Nodes (7): Fingerprint Psi (Eq. 12, per-cluster error rate), Lambda price weight in routing score, UNIROUTE_PIPELINE.md router spec, UniRoute K-means router (M1), PROJECT.md overview, Project glossary, Metis-Auto virtual model

### Community 43 - "Gateway Observability"
Cohesion: 0.29
Nodes (6): Quality checks + escalation cascade (E7), FastAPI OpenAI-compatible gateway with LiteLLM (E1), Observability: MLflow traces, SQLite, dashboard (E10), Semantic cache (E8, WP-17 decision), Gateway flow G1-G7, WP-17 Semantic cache

### Community 44 - "Embedder benchmark (WP-03 step 5)"
Cohesion: 0.29
Nodes (6): 1. Latency, p50 / p95 in ms (one message), 2. Determinism and devices, 3. Persian sanity (40 synthetic pairs: 20 paraphrase, 20 topically close but different), 4. Cluster readability on the sample (K-means, seed 20261020, `clustering` adapter), 5. Qdrant vs numpy, Embedder benchmark (WP-03 step 5)

### Community 45 - "test_router_baselines.py"
Cohesion: 0.08
Nodes (28): balanced_accuracy(), BootResult, bootstrap(), cohen_kappa(), fingerprint_stability(), mcnemar_exact(), separability(), session_resample() (+20 more)

### Community 47 - "Owner Fixed Points"
Cohesion: 0.29
Nodes (3): draw.io pastel diagram style, Reproducibility: cached calls, config hashes (E11), Secrets handling and redaction (E13)

### Community 48 - "test_redact.py"
Cohesion: 0.23
Nodes (6): fake(), test_each_kind_redacted(), test_idempotent(), test_key_inside_assignment_counted_once(), test_no_false_positive(), test_redact_message_all_fields()

### Community 50 - "Metis AI and Risks"
Cohesion: 0.33
Nodes (5): Fallback plan for late data (P4), Judge GPT-5.x class via Metis AI (M10), Metis AI API aggregator, R17 network split (Metis AI unreachable), Risks R1-R17

### Community 51 - "Fingerprint Ψ_k(h)"
Cohesion: 0.16
Nodes (14): Pipeline explained step by step, Manager/employees report-card analogy, Online example: complaint message routed to gpt-4o-mini, Diagram 05-uniroute, UniRoute explained with one diagram, M1 Add a model (no retraining), Online steps R1-R4, Seven diagram bands (prepare..maintain) (+6 more)

### Community 52 - "run.py"
Cohesion: 0.25
Nodes (5): bot_table(), elbow(), main(), run_cluster(), run_embed()

### Community 53 - "WP Template"
Cohesion: 0.17
Nodes (14): WP Template, WP-03 Embedder and Vector Store, Embedder (src/metis/embed/embedder.py), Embedding latency budget <=60 ms p95 (E5), Persian sanity check (40 synthetic pairs, AUC>=0.85), Qdrant local store (src/metis/embed/store.py), Baselines: ZeroRouter, K-NN, logistic, estimate_costs.py (+6 more)

### Community 54 - "Evaluation Protocol"
Cohesion: 0.50
Nodes (3): 4 candidate models (deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash, claude-sonnet-4-6), Statistics and evaluation protocol (§8), WP-19 Final evaluation

### Community 76 - "test_load_parquet.py"
Cohesion: 0.18
Nodes (3): _msg(), root(), test_length_mismatch_and_unknown_type()

### Community 77 - "data_card_full.py"
Cohesion: 0.29
Nodes (4): _files(), main(), scan(), table()

### Community 78 - "Data card: full dataset (structure only)"
Cohesion: 0.20
Nodes (9): Billing (currency not stated), Data card: full dataset (structure only), Finish reasons, Integrity, Message types (length in characters), Messages per month, Secret scan (`metis.data.redact`, may include false positives), Tables (+1 more)

### Community 79 - "ladder"
Cohesion: 0.27
Nodes (7): ladder(), difference(), tune_knn_k(), area(), sweep(), test_area_by_hand(), statistic()

### Community 80 - "ZeroRouter"
Cohesion: 0.29
Nodes (3): ZeroRouter, test_area_of_baselines_is_comparable(), test_zero_router_mix_follows_the_spec_formula()

### Community 81 - "select_lambda.py"
Cohesion: 0.25
Nodes (4): LambdaChoice, select_lambda(), test_select_lambda_modes(), test_select_lambda_reports_an_unreachable_target()

### Community 82 - "baselines.py"
Cohesion: 0.39
Nodes (4): always_best(), always_cheapest(), AlwaysModel, test_always_routers()

### Community 83 - "KNNRouter"
Cohesion: 0.33
Nodes (3): KNNRouter, neighbor_order(), test_knn_matches_numpy_and_recovers_types()

### Community 92 - "test_split.py"
Cohesion: 0.30
Nodes (13): run(), synthetic(), test_deterministic_and_seed_sensitive(), test_each_prompt_is_equally_likely_so_long_sessions_count_more(), test_input_dates_are_not_used(), test_no_balancing_by_default(), test_only_eligible_in_labeled_and_draws_from_all_sessions(), test_pilot_and_cal() (+5 more)

### Community 93 - "WP-03b: Persian clustering test on public data (embedding + K-means only)"
Cohesion: 0.22
Nodes (8): Acceptance checks, Context, End of session (in addition to `/handoff`), If blocked, Outputs, Read (only these), Steps, WP-03b: Persian clustering test on public data (embedding + K-means only)

### Community 94 - "Data selection criteria"
Cohesion: 0.20
Nodes (9): 1. Dataset, 2. What counts as a prompt, 3. Exclusion rules, 4. Why `workflow` is excluded (D-057), 5. How val and test are drawn, 6. Counts on the full data (S1, 2026-10-31), 7. Open items for WP-08, Data selection criteria (+1 more)

### Community 97 - "API costs diagram"
Cohesion: 0.17
Nodes (16): Paid total ~$25-35, hard cap $60, Add a new model: pointwise 800 calls ~$1-3, pairwise 1,200 calls ~$1.5-5, Call counting formulas (spec section 9), claude-sonnet-4-6 (strong, anchor, $0.0075/call), deepseek-v4-flash (cheap, $0.0003/call), API costs diagram, Evaluate cost (300-600 calls, $1-2), Free forever after: remove model, price change, new lambda, re-clustering (+8 more)

### Community 98 - "test_router_select.py"
Cohesion: 0.25
Nodes (11): KSelection, select_k(), lambda_grid(), planted(), test_k1_cannot_win_even_when_it_scores_best(), test_lambda_grid_shape(), test_routing_beats_a_single_cluster_on_planted_data(), test_s9_runtime_under_two_minutes() (+3 more)

### Community 100 - "json"
Cohesion: 0.15
Nodes (7): main(), main(), build_streaming(), input_hash(), main(), main(), main()

### Community 101 - "WP-03b report: Persian clustering test"
Cohesion: 0.29
Nodes (6): Acceptance, Built, Limits, Outcome, Results (measured, K = 8, small / nano), WP-03b report: Persian clustering test

### Community 102 - "metrics.py"
Cohesion: 0.14
Nodes (12): best_single(), cost_quality(), envelope_quality(), operating_point(), OperatingPoint, pareto_envelope(), qnc(), cluster_choices() (+4 more)

### Community 103 - "qdrant"
Cohesion: 0.20
Nodes (9): QDRANT__TELEMETRY_DISABLED, container_name, environment, image, ports, restart, volumes, services (+1 more)

### Community 104 - "route.py"
Cohesion: 0.15
Nodes (12): next_best(), normalize_costs(), rank_models(), route(), RouteDecision, Router, app_b_router(), test_batch_and_single_routing_agree() (+4 more)

### Community 106 - "test_router_synthetic.py"
Cohesion: 0.19
Nodes (10): assign(), dev_pool(), area_difference(), build(), test_dev_pool_is_respected_when_choosing_k(), test_fingerprints_recover_the_planted_rates(), test_new_model_changes_only_its_row_and_lambda(), test_no_structure_gives_no_gain() (+2 more)

### Community 107 - "s4_embed_bench.py"
Cohesion: 0.14
Nodes (14): main(), train_sample(), clusters(), latency(), log(), main(), persian_check(), rss_mb() (+6 more)

### Community 108 - "s4_latex_tables.py"
Cohesion: 0.39
Nodes (14): load(), main(), pm(), t_chat_clusters(), t_compare(), t_difficulty(), t_full(), t_khayyam_clusters() (+6 more)

### Community 109 - "bt.py"
Cohesion: 0.20
Nodes (8): BTFit, closed_form_psi(), fit_bt(), _objective(), _prepare(), cluster_sums(), test_bt_fit_equals_closed_form_and_anchor_row(), test_bt_handles_all_wins_and_empty_clusters()

### Community 110 - "test_embed.py"
Cohesion: 0.08
Nodes (20): load_table(), run_set_split(), _check_payload(), point_id(), VectorStore, emb(), FakeModel, FakeTokModel (+12 more)

### Community 111 - "synthetic_validation.py"
Cohesion: 0.15
Nodes (10): bed(), fit_bed(), main(), rule_picks(), rule_study(), Bed, make_bed(), _split() (+2 more)

### Community 113 - "UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)"
Cohesion: 0.19
Nodes (21): UniRoute every-step diagram (S1-S12, R1-R4, M1-M4), M1 Add a model (answer 400 val prompts -> new Psi row), M2 Remove a model (delete Psi row, $0), M3 Price change (update c, re-pick lambda, $0), M4 Traffic drift (re-run S5, $0), R1 Embed (same model as S4), R2 Nearest cluster k*, R3 Score each model s(h)=Psi_k*(h)+lambda*c(h) (+13 more)

### Community 114 - "test_router_core.py"
Cohesion: 0.14
Nodes (12): check_inputs(), fail_rates(), Fingerprints, fingerprints(), fit_psi(), halvings(), test_alpha_zero_is_paper_eq12_exactly(), test_code_defaults_match_the_config() (+4 more)

### Community 115 - "WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)"
Cohesion: 0.29
Nodes (6): Context, End of session, Must check in step 9 (found in WP-05a), Read (only these), Steps, WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)

### Community 116 - "Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute"
Cohesion: 0.13
Nodes (18): Evaluation: quality, cache hit rate, cost vs premium baseline, latency, Baselines: always-best, always-cheapest, ZeroRouter, K-NN, production, DARS (EMNLP 2026), Decisions needed (dataset, API access, budget, labeling, pool), Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute, Later upgrades (LearnedMap, safety-net judge, cache-aware cost, Redis), How Reliable is Multilingual LLM-as-a-Judge? (EMNLP 2025), Simulating new models (hide a third of models) (+10 more)

### Community 118 - "nano"
Cohesion: 0.22
Nodes (9): nano, small, name, path, revision, candidates, name, path (+1 more)

### Community 120 - "What exists"
Cohesion: 0.22
Nodes (7): stats(), Acceptance, Findings, Results (simulated data; n_test = 300; 95% CIs from 10,000 session resamples), Spec readings (D-062, D-063), What exists, WP-05 report: router core and evaluation library

### Community 121 - "WP-03 report: Embedder + Qdrant"
Cohesion: 0.50
Nodes (3): Decision table (details: `results/wp03_embedder/embedder_benchmark.md`), Outcome, WP-03 report: Embedder + Qdrant

### Community 124 - "router"
Cohesion: 0.20
Nodes (10): router, alpha_pair, alpha_point, k_max, k_ship_max, kmeans_n_init, lambda_high, lambda_low (+2 more)

### Community 125 - "Synthetic validation of the router (WP-05 step 9)"
Cohesion: 0.40
Nodes (4): Choosing K: which rule finds the truth? (100 simulated datasets each), No structure: routers at K = 3 (simulated, n_test = 300, one dataset), Planted structure: routers at K = 3 (simulated, n_test = 300, one dataset), Synthetic validation of the router (WP-05 step 9)

### Community 126 - "s2"
Cohesion: 0.29
Nodes (7): s2, balance_field, cal_models, max_per_session, n_pilot, n_test, n_val

### Community 128 - "pipeline.yaml"
Cohesion: 0.29
Nodes (6): sample_dry_run, balance_field, n_pilot, n_test, n_val, seed

### Community 129 - "s1"
Cohesion: 0.29
Nodes (7): s1, chars_per_token, embed_truncate, history_max_tokens, history_max_turns, huge_prompt_chars, min_text_chars

## Knowledge Gaps
- **111 isolated node(s):** `metis`, `Later upgrades: safety-net judge, cache-aware cost, LearnedMap`, `Sample dataset sample-data/data.json (100 sessions, 907 messages, 4 categories)`, `M2 Remove a model (delete Psi row, $0)`, `M3 Price change (update c, re-pick lambda, $0)` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 545 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `s4_persian_cluster.py` to `s4_embed_bench.py`, `json`, `config.py`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **What connects `metis`, `Later upgrades: safety-net judge, cache-aware cost, LearnedMap`, `Sample dataset sample-data/data.json (100 sessions, 907 messages, 4 categories)` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `System overview diagram (offline build + online gateway)` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Why does `Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute` connect `Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute` to `Offline build diagram (S1-S12)`, `System overview diagram (offline build + online gateway)`, `API costs diagram`, `Roadmap and Phases`, `UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Should `UniRoute Paper Concepts` be split into smaller, more focused modules?**
  _Cohesion score 0.08130081300813008 - nodes in this community are weakly interconnected._
- **Should `Roadmap and Phases` be split into smaller, more focused modules?**
  _Cohesion score 0.10810810810810811 - nodes in this community are weakly interconnected._
- **Should `ext_download.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09848484848484848 - nodes in this community are weakly interconnected._