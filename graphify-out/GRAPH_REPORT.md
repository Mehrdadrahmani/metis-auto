# Graph Report - metis-auto  (2026-11-02)

## Corpus Check
- 207 files · ~185,010 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 13, .tex 13, .drawio 8)

## Summary
- 1822 nodes · 3700 edges · 129 communities (97 shown, 32 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dd4f03fa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Offline build diagram (S1-S12)
- System overview diagram (offline build + online gateway)
- Data card: `sample.json` (structure only)
- UniRoute Paper Concepts
- Roadmap and Phases
- ext_download.py
- UniRoute Pipeline Spec
- k_6
- test_judge.py
- manifest.json
- s4
- UniRoute's embedding + clustering step on public Persian data
- s4_persian_cluster.py
- callcache.py
- LLM routing state of the art (research)
- Final Eval and Release
- tracking.py
- Gateway, Cache, Replay WPs
- UniRoute paper notes
- Budget
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
- models
- Metis AI and Risks
- Fingerprint Ψ_k(h)
- load_config
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
- complete
- test_load_parquet.py
- s4_embed_full.py
- Data card: full dataset (structure only)
- hashlib
- ndarray
- client.py
- Checkpoint: all work packages and tasks
- Online path diagram (G1-G7)
- pandas
- bot_clusters/README.md
- budget_memo.md
- test_embed.py
- runner.py
- Metis AI capabilities
- VectorStore
- Course brief: Intelligent LLM Routing Middleware (Metis-OS Team)
- test_split.py
- WP-03b: Persian clustering test on public data (embedding + K-means only)
- Data selection criteria
- test_normalize_lang.py
- WP-04 report: LLM client, call cache, budget
- anomalies
- test_router_select.py
- WP-05 report: router core and evaluation library
- load_config
- WP-03b report: Persian clustering test
- metrics.py
- qdrant
- numpy
- store.py
- test_router_synthetic.py
- s4_embed_bench.py
- s4_latex_tables.py
- numpy
- fixture
- synthetic_validation.py
- Embedder
- UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)
- artifact.py
- WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)
- Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute
- build.py
- nano
- FakeMetis
- summarize
- router
- Synthetic validation of the router (WP-05 step 9)
- s2
- k_rule_review.md
- pipeline.yaml
- s1

## God Nodes (most connected - your core abstractions)
1. `UniRoute Pipeline Specification` - 40 edges
2. `complete()` - 33 edges
3. `load_config()` - 31 edges
4. `Budget` - 30 edges
5. `Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute` - 27 edges
6. `Roadmap diagram (WP-00..WP-21)` - 27 edges
7. `Embedder` - 24 edges
8. `main()` - 23 edges
9. `ladder()` - 23 edges
10. `Offline build diagram (S1-S12)` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Findings` --references--> `area()`  [INFERRED]
  work/reports/WP-05-report.md → src/metis/eval/metrics.py
- `Must check in step 9 (found in WP-05a)` --references--> `test_s9_runtime_under_two_minutes()`  [INFERRED]
  work/WP-05b-baselines-stats-synthetic.md → tests/test_router_select.py
- `What exists` --references--> `artifact()`  [INFERRED]
  work/reports/WP-05-report.md → tests/test_router_baselines.py
- `Differences from the WP` --references--> `complete()`  [INFERRED]
  work/reports/WP-04-report.md → src/metis/llm/client.py
- `What exists` --references--> `stats()`  [INFERRED]
  work/reports/WP-05-report.md → scripts/s1_s2_counts.py

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

## Communities (129 total, 32 thin omitted)

### Community 0 - "Offline build diagram (S1-S12)"
Cohesion: 0.18
Nodes (21): Judge-human agreement >= 75%?, Offline build diagram (S1-S12), Pilot (section P): 4 models, 200 val, 150 test, criteria A-D, tie -> pointwise, Revise rubric / tau, S1 Ingest & clean (last user msg + <=2 turns, redact, language tag, de-dup), S10 Choose lambda: quality target or cost budget, S11 Evaluate on S_te (UniRoute vs always-best, always-cheapest, ZeroRouter, K-NN), S12 Router artifact (versioned: method, embedder, K, centroids, Psi, c, lambda, hashes) (+13 more)

### Community 1 - "System overview diagram (offline build + online gateway)"
Cohesion: 0.19
Nodes (22): Answer, Cache hit?, Call model + failover, Code checks + escalation, Choose K and lambda on validation, Clean, redact secrets, split by conversation, System overview diagram (offline build + online gateway), Embed locally + K-means (no API calls) (+14 more)

### Community 2 - "Data card: `sample.json` (structure only)"
Cohesion: 0.11
Nodes (25): Categorical value sets, Counts, Data card: `sample.json` (structure only), Key paths, Models (bot messages), Providers, Redaction hits, Roles (+17 more)

### Community 3 - "UniRoute Paper Concepts"
Cohesion: 0.08
Nodes (35): Area under the deferral curve, Bradley-Terry-Luce model for per-cluster scores, Chatbot Arena (Zheng et al. 2023), Clairvoyant MLP / MatFac oracle baselines, Cluster membership map Phi_clust(x), Deferral curve (quality vs cost), Routing with a dynamic LLM pool, EmbedLLM benchmark (Zhuang et al. 2024) (+27 more)

### Community 4 - "Roadmap and Phases"
Cohesion: 0.07
Nodes (53): Roadmap diagram (WP-00..WP-21), Full dataset arrives, Gate 1: owner approves budget, Gate 2: agreement >= 75%, kappa >= 0.40, Gate 3: git tag pre-test, Paid total ~$25-35, hard cap $60, WP-00 Bootstrap (git, GitHub, session mechanism), WP-01 Data + redaction (safe loader, data card) (+45 more)

### Community 5 - "ext_download.py"
Cohesion: 0.10
Nodes (12): arena100(), arena140(), build(), filtered(), get_json(), hf_request(), HTTPRange, log() (+4 more)

### Community 7 - "UniRoute Pipeline Spec"
Cohesion: 0.18
Nodes (16): Anchor model (pairwise), Data artifacts schemas (§3), UniRoute Pipeline Specification, Deferral area and QNC, Experiment mode (holdout unseen models), K-NN router baseline, LearnedMap (out of scope), S11 Evaluate on test vs baselines (+8 more)

### Community 8 - "k_6"
Cohesion: 0.08
Nodes (23): k_3, 0, 1, 2, k_4, 0, 1, 2 (+15 more)

### Community 9 - "test_judge.py"
Cohesion: 0.07
Nodes (14): _answers(), _pairs(), run(), test_failed_anchor_is_dropped(), test_failed_answers_are_left_out_of_labeling(), test_failed_generation_gets_the_worst_label_without_a_call(), test_jev_level_maps_to_one_to_ten(), test_labeling_items_are_blind_and_seeded() (+6 more)

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
Cohesion: 0.10
Nodes (25): main(), features(), main(), curve(), k_curves(), main(), maps(), assign() (+17 more)

### Community 14 - "callcache.py"
Cohesion: 0.08
Nodes (13): BudgetRefused, call_cost(), cache_key(), CallCache, default_path(), get_or_call(), is_mock(), ModelNotReadyError (+5 more)

### Community 15 - "LLM routing state of the art (research)"
Cohesion: 0.29
Nodes (6): DARS: one answer per prompt is noisy, LLM routing state of the art (research), RouterArena finding: routers too cautious, Routing approach families (RouteLLM, cascades, bandits...), Routing and cascading survey (arXiv 2603.04445), Three-stage router/check/escalate architecture

### Community 16 - "Final Eval and Release"
Cohesion: 0.12
Nodes (17): runs/s7/labels_test.sealed.parquet (sealed), results/eval_protocol.md, WP-19: Final evaluation on test set, scripts/eval_test.py, Live latency run (stage live, ~$1.5, val messages), Primary analysis: router vs always-best (paired bootstrap, McNemar), Production comparison (cost, answer similarity, M15), results/final/ (+9 more)

### Community 17 - "tracking.py"
Cohesion: 0.24
Nodes (5): batch_run(), call_span(), enabled(), _mlflow(), mlflow_dir()

### Community 18 - "Gateway, Cache, Replay WPs"
Cohesion: 0.13
Nodes (16): MLflow experiment router-selection (D-044), WP-15: Gateway core, scripts/gateway_smoke.py, configs/gateway.yaml, LiteLLM via Metis AI, gateway/mock_provider.py, OpenAI-compatible API (POST /v1/chat/completions), gateway/traces.py (SQLite traces + MLflow spans) (+8 more)

### Community 19 - "UniRoute paper notes"
Cohesion: 0.25
Nodes (4): UniRoute paper notes, Paper experimental facts (datasets, val 400, Gecko), Ideas for later (attribute clusters, coreset, budget control), UniRoute paper (Jitkrittum et al., ICLR 2026)

### Community 20 - "Budget"
Cohesion: 0.12
Nodes (25): Budget, call(), config(), Crash, fake_response(), mock_batch(), Sender, test_budget_refusal_stops_batch() (+17 more)

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
Cohesion: 0.27
Nodes (10): WP-02 Report, Sample exclusion waterfall (434 rows, 375 LLM replies, 343 eligible), WP-02 Prompt Builder, Hard Rules, Splitter, eligible_labeled filter, lang_tag (lang.py), Persian normalization (normalize.py), prompts table S1 (prompts.py), Seed 20261020 (+2 more)

### Community 27 - "Bootstrap and Environment"
Cohesion: 0.17
Nodes (11): uv virtual environment metis-rahnema, Budget ledger ($60 cap, $0 spent), Open questions (Q-001..Q-022), Q-017 Metis AI reachability (VPN), Q-020 K selection report cards, Budget estimate (~$25 pointwise / ~$35 pairwise), Budget guard in code (E12), Target repository layout (+3 more)

### Community 28 - "Model Registry Fields"
Cohesion: 0.11
Nodes (17): models, api_name, api_path, context_window, exp_role, id, is_anchor, price_in (+9 more)

### Community 29 - "Decision Register"
Cohesion: 0.21
Nodes (6): Decision register (D-001..D-050), Spec deviations DEV-1..DEV-9, Embedder jina-embeddings-v5-text-small, Qdrant local vector store, WP-03 Embedder + Qdrant, WP-03 step 5 embed benchmark pending (Low Power Mode)

### Community 30 - "Router Core WP-05"
Cohesion: 0.29
Nodes (10): WP-05 Router Core and Evaluation, Baselines: ZeroRouter, K-NN, logistic, Bradley-Terry S8-PW vs anchor, Fingerprints S8-PT (Eq. 12, alpha=0), K-means clustering S5 (nearest centroid, DEV-7), Pareto area and QNC metrics (eval/metrics.py), route() (router/route.py), Router artifact S12 (+2 more)

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
Cohesion: 0.10
Nodes (19): balanced_accuracy(), BootResult, bootstrap(), cohen_kappa(), fingerprint_stability(), mcnemar_exact(), separability(), session_resample() (+11 more)

### Community 47 - "Owner Fixed Points"
Cohesion: 0.29
Nodes (3): draw.io pastel diagram style, Reproducibility: cached calls, config hashes (E11), Secrets handling and redaction (E13)

### Community 48 - "models"
Cohesion: 0.10
Nodes (22): extra_body, reasoning_effort, add, drop, common, max_tokens, temperature, top_p (+14 more)

### Community 50 - "Metis AI and Risks"
Cohesion: 0.33
Nodes (5): Fallback plan for late data (P4), Judge GPT-5.x class via Metis AI (M10), Metis AI API aggregator, R17 network split (Metis AI unreachable), Risks R1-R17

### Community 51 - "Fingerprint Ψ_k(h)"
Cohesion: 0.16
Nodes (14): Pipeline explained step by step, Manager/employees report-card analogy, Online example: complaint message routed to gpt-4o-mini, Diagram 05-uniroute, UniRoute explained with one diagram, M1 Add a model (no retraining), Online steps R1-R4, Seven diagram bands (prepare..maintain) (+6 more)

### Community 52 - "load_config"
Cohesion: 0.08
Nodes (21): config_id(), load_config(), load_models(), build_messages(), gen_params(), roles(), test_context_without_instructions(), test_every_generating_model_has_params() (+13 more)

### Community 53 - "WP Template"
Cohesion: 0.21
Nodes (12): WP Template, WP-03 Embedder and Vector Store, Embedder (src/metis/embed/embedder.py), Embedding latency budget <=60 ms p95 (E5), Persian sanity check (40 synthetic pairs, AUC>=0.85), Qdrant local store (src/metis/embed/store.py), estimate_costs.py, WP-07 End-to-End Dry Run (+4 more)

### Community 54 - "Evaluation Protocol"
Cohesion: 0.50
Nodes (3): 4 candidate models (deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash, claude-sonnet-4-6), Statistics and evaluation protocol (§8), WP-19 Final evaluation

### Community 72 - "complete"
Cohesion: 0.17
Nodes (20): complete(), Permit, cache(), fn(), msgs(), test_gives_up_after_one_retry(), test_guard_sees_nested_content_and_runs_before_send(), test_missing_env_is_not_a_failed_call() (+12 more)

### Community 76 - "test_load_parquet.py"
Cohesion: 0.08
Nodes (9): list_ids(), main(), matches(), report(), _msg(), test_length_mismatch_and_unknown_type(), path(), test_bad_structure() (+1 more)

### Community 77 - "s4_embed_full.py"
Cohesion: 0.36
Nodes (4): embedder(), load_table(), main(), run_embed()

### Community 78 - "Data card: full dataset (structure only)"
Cohesion: 0.20
Nodes (9): Billing (currency not stated), Data card: full dataset (structure only), Finish reasons, Integrity, Message types (length in characters), Messages per month, Secret scan (`metis.data.redact`, may include false positives), Tables (+1 more)

### Community 79 - "hashlib"
Cohesion: 0.09
Nodes (12): bot_table(), elbow(), main(), run_cluster(), run_embed(), _files(), main(), scan() (+4 more)

### Community 80 - "ndarray"
Cohesion: 0.08
Nodes (16): always_best(), always_cheapest(), AlwaysModel, KNNRouter, LogisticRouter, LossRouter, lower_hull(), neighbor_order() (+8 more)

### Community 81 - "client.py"
Cohesion: 0.09
Nodes (12): CallFailed, check_outgoing(), _detail(), _failure_kind(), _is_retryable(), _mock_response(), NoPermitError, OutgoingSecretError (+4 more)

### Community 82 - "Checkpoint: all work packages and tasks"
Cohesion: 0.11
Nodes (18): Checkpoint: all work packages and tasks, Done, WP-06 Generation and judge pipeline, WP-07 End-to-end dry run, WP-08 Full data in, WP-09 Pilot run 💲, WP-10 Owner labels ⏸, WP-11 Pilot decision ⛔ (+10 more)

### Community 83 - "Online path diagram (G1-G7)"
Cohesion: 0.25
Nodes (16): Answer, One repair, then escalate to next-lower Psi_k model (cascade), Online path diagram (G1-G7), Failover: next-lowest s(h), prefer another provider; breaker 3 fails -> 30 s pause, G1 Hard rules (menu->workflow, image->image model, filter -> allowed set A), G2 Preprocess + embed (same as offline S1/S4), G3 Semantic cache hit? (same chatbot, safe to cache), G4 UniRoute router (nearest centroid, s(h)=Psi_k(h)+lambda*c(h), tie->cheaper) (+8 more)

### Community 84 - "pandas"
Cohesion: 0.10
Nodes (10): main(), stats(), main(), similarity(), smd(), mix_table(), labelled(), run_near_dups() (+2 more)

### Community 87 - "test_embed.py"
Cohesion: 0.18
Nodes (11): emb(), FakeModel, FakeTokModel, test_deterministic(), test_embedder_id_changes_with_preprocessing(), test_empty_input(), test_l2_normalized_float32(), test_prefix_and_task_passed() (+3 more)

### Community 88 - "runner.py"
Cohesion: 0.25
Nodes (11): CallResult, _add(), anomaly(), BatchReport, _checkpoint(), _progress(), _run(), run_batch() (+3 more)

### Community 90 - "VectorStore"
Cohesion: 0.24
Nodes (5): run_set_split(), _check_payload(), VectorStore, test_store_upsert_idempotent_and_guards(), knn_setup()

### Community 91 - "Course brief: Intelligent LLM Routing Middleware (Metis-OS Team)"
Cohesion: 0.28
Nodes (13): Action 1: Smart classifier & dynamic routing, Action 2: Cascade architecture & semantic caching, Action 3 (optional): Financial modeling & observability dashboard, AI decision fatigue, API fragmentation, Course brief: Intelligent LLM Routing Middleware (Metis-OS Team), Feature extraction (language, intent, code, multimodal), Metis-Auto virtual meta-model (+5 more)

### Community 92 - "test_split.py"
Cohesion: 0.30
Nodes (13): run(), synthetic(), test_deterministic_and_seed_sensitive(), test_each_prompt_is_equally_likely_so_long_sessions_count_more(), test_input_dates_are_not_used(), test_no_balancing_by_default(), test_only_eligible_in_labeled_and_draws_from_all_sessions(), test_pilot_and_cal() (+5 more)

### Community 93 - "WP-03b: Persian clustering test on public data (embedding + K-means only)"
Cohesion: 0.22
Nodes (8): Acceptance checks, Context, End of session (in addition to `/handoff`), If blocked, Outputs, Read (only these), Steps, WP-03b: Persian clustering test on public data (embedding + K-means only)

### Community 94 - "Data selection criteria"
Cohesion: 0.20
Nodes (9): 1. Dataset, 2. What counts as a prompt, 3. Exclusion rules, 4. Why `workflow` is excluded (D-057), 5. How val and test are drawn, 6. Counts on the full data (S1, 2026-10-31), 7. Open items for WP-08, Data selection criteria (+1 more)

### Community 96 - "WP-04 report: LLM client, call cache, budget"
Cohesion: 0.33
Nodes (5): Acceptance, Built, Metis findings, Not proven, WP-04 report: LLM client, call cache, budget

### Community 97 - "anomalies"
Cohesion: 0.14
Nodes (13): anomalies, max_cost_ratio, max_failure_rate, max_reasoning_share, max_truncation_rate, min_calls, approved_usd, cache_labels (+5 more)

### Community 98 - "test_router_select.py"
Cohesion: 0.14
Nodes (16): KSelection, select_k(), lambda_grid(), LambdaChoice, select_lambda(), test_code_defaults_match_the_config(), planted(), test_k1_cannot_win_even_when_it_scores_best() (+8 more)

### Community 99 - "WP-05 report: router core and evaluation library"
Cohesion: 0.33
Nodes (5): Acceptance, Findings, Results (simulated data; n_test = 300; 95% CIs from 10,000 session resamples), Spec readings (D-062, D-063), WP-05 report: router core and evaluation library

### Community 100 - "load_config"
Cohesion: 0.15
Nodes (6): main(), load_vectors(), main(), page(), gap(), main()

### Community 101 - "WP-03b report: Persian clustering test"
Cohesion: 0.29
Nodes (6): Acceptance, Built, Limits, Outcome, Results (measured, K = 8, small / nano), WP-03b report: Persian clustering test

### Community 102 - "metrics.py"
Cohesion: 0.09
Nodes (23): fit_bed(), ladder(), difference(), main(), rule_picks(), rule_study(), tune_knn_k(), area() (+15 more)

### Community 103 - "qdrant"
Cohesion: 0.20
Nodes (9): QDRANT__TELEMETRY_DISABLED, container_name, environment, image, ports, restart, volumes, services (+1 more)

### Community 104 - "numpy"
Cohesion: 0.12
Nodes (25): fingerprints(), cluster_counts(), normalize_costs(), rank_models(), route(), Router, test_set_payload_changes_field_and_keeps_vector(), app_b_router() (+17 more)

### Community 105 - "store.py"
Cohesion: 0.24
Nodes (3): collection_name(), point_id(), test_point_id_stable()

### Community 106 - "test_router_synthetic.py"
Cohesion: 0.09
Nodes (18): assign(), candidate_ks(), fit_all(), fit_kmeans(), KMeansModel, dev_pool(), next_best(), RouteDecision (+10 more)

### Community 107 - "s4_embed_bench.py"
Cohesion: 0.17
Nodes (11): main(), train_sample(), clusters(), latency(), log(), main(), persian_check(), rss_mb() (+3 more)

### Community 108 - "s4_latex_tables.py"
Cohesion: 0.39
Nodes (14): load(), main(), pm(), t_chat_clusters(), t_compare(), t_difficulty(), t_full(), t_khayyam_clusters() (+6 more)

### Community 109 - "numpy"
Cohesion: 0.15
Nodes (10): BTFit, closed_form_psi(), fit_bt(), _objective(), _prepare(), check_inputs(), cluster_sums(), fail_rates() (+2 more)

### Community 110 - "fixture"
Cohesion: 0.50
Nodes (3): go(), env(), fake_metis()

### Community 111 - "synthetic_validation.py"
Cohesion: 0.23
Nodes (6): bed(), Bed, make_bed(), _split(), SplitData, structured()

### Community 112 - "Embedder"
Cohesion: 0.13
Nodes (7): Embedder, _Model, test_merged_adapter_gives_same_vectors(), Built, Decision table (details: `results/wp03_embedder/embedder_benchmark.md`), Outcome, WP-03 report: Embedder + Qdrant

### Community 113 - "UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)"
Cohesion: 0.19
Nodes (21): UniRoute every-step diagram (S1-S12, R1-R4, M1-M4), M1 Add a model (answer 400 val prompts -> new Psi row), M2 Remove a model (delete Psi row, $0), M3 Price change (update c, re-pick lambda, $0), M4 Traffic drift (re-run S5, $0), R1 Embed (same model as S4), R2 Nearest cluster k*, R3 Score each model s(h)=Psi_k*(h)+lambda*c(h) (+13 more)

### Community 114 - "artifact.py"
Cohesion: 0.21
Nodes (11): load_artifact(), Meta, RouterArtifact, save_artifact(), _sha256(), artifact(), meta(), test_artifact_checks_its_fields() (+3 more)

### Community 115 - "WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)"
Cohesion: 0.29
Nodes (6): Context, End of session, Must check in step 9 (found in WP-05a), Read (only these), Steps, WP-05b: Baselines, statistics, synthetic proof, artifact (steps 7–10 of WP-05)

### Community 116 - "Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute"
Cohesion: 0.13
Nodes (18): Evaluation: quality, cache hit rate, cost vs premium baseline, latency, Baselines: always-best, always-cheapest, ZeroRouter, K-NN, production, DARS (EMNLP 2026), Decisions needed (dataset, API access, budget, labeling, pool), Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute, Later upgrades (LearnedMap, safety-net judge, cache-aware cost, Redis), How Reliable is Multilingual LLM-as-a-Judge? (EMNLP 2025), Simulating new models (hide a third of models) (+10 more)

### Community 117 - "build.py"
Cohesion: 0.15
Nodes (8): bands(), history_text(), main(), make_items(), pick_pairs(), relabel_pairs(), render_html(), test_labeling_shows_the_history_the_models_saw()

### Community 118 - "nano"
Cohesion: 0.22
Nodes (9): nano, small, name, path, revision, candidates, name, path (+1 more)

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
- **111 isolated node(s):** `metis`, `M2 Remove a model (delete Psi row, $0)`, `M3 Price change (update c, re-pick lambda, $0)`, `Decisions needed (dataset, API access, budget, labeling, pool)`, `Risks and mitigations` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 674 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_config()` connect `load_config` to `test_router_select.py`, `load_config`, `metrics.py`, `s4_embed_bench.py`, `s4_embed_full.py`, `s4_persian_cluster.py`, `hashlib`, `callcache.py`, `client.py`, `pandas`, `build.py`, `Budget`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **What connects `metis`, `M2 Remove a model (delete Psi row, $0)`, `M3 Price change (update c, re-pick lambda, $0)` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Data card: `sample.json` (structure only)` be split into smaller, more focused modules?**
  _Cohesion score 0.1051693404634581 - nodes in this community are weakly interconnected._
- **Why does `complete()` connect `complete` to `ext_download.py`, `callcache.py`, `client.py`, `tracking.py`, `load_config`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Should `UniRoute Paper Concepts` be split into smaller, more focused modules?**
  _Cohesion score 0.08130081300813008 - nodes in this community are weakly interconnected._
- **Why does `main()` connect `s4_persian_cluster.py` to `load_config`, `ext_download.py`, `numpy`, `s4_embed_bench.py`, `Embedder`, `pandas`, `load_config`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Should `Roadmap and Phases` be split into smaller, more focused modules?**
  _Cohesion score 0.06778476589797344 - nodes in this community are weakly interconnected._