# Graph Report - metis-auto  (2026-10-24)

## Corpus Check
- 95 files · ~70,667 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: (none) 12, .drawio 7, .tex 1)

## Summary
- 855 nodes · 1374 edges · 92 communities (48 shown, 44 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ebd6c5fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Offline build diagram (S1-S12)
- System Overview and Gateway
- test_prompts.py
- UniRoute Paper Concepts
- Roadmap and Phases
- test_redact.py
- UniRoute Pipeline Spec
- Qdrant Vector Store
- embedder.py
- s4
- json
- Embedder Tests
- Embedder Core
- Research and Proposal
- Final Eval and Release
- Gateway, Cache, Replay WPs
- API Cost Estimates
- Embed Benchmark Script
- Pilot Decision and Judging
- Session Protocol Docs
- test_normalize_lang.py
- WP-04 LLM Client, Cache, Budget
- Report Notes and S1-S2
- WP-02 Prompts and Splits
- Bootstrap and Environment
- Model Registry Fields
- Decision Register
- Router Core WP-05
- Checks and Escalation
- System overview diagram (offline build + online gateway)
- Judging Methods
- System Design and Gateway
- WP-09 Pilot Run
- Bootstrap and Secret Scan
- Gates and Integrity
- Planning Request v2
- Data Access WP-01
- Generation WP-12
- Fingerprints and Freeze
- UniRoute Router Design
- Gateway Observability
- Sample Data Card
- UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)
- Embedder benchmark (WP-03 step 5)
- Owner Fixed Points
- WP-03 report: Embedder + Qdrant
- Metis AI and Risks
- UniRoute Diagram Explained
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

## God Nodes (most connected - your core abstractions)
1. `UniRoute Pipeline Specification` - 40 edges
2. `Proposal v2: Metis-Auto v2, a measured LLM router built on UniRoute` - 27 edges
3. `Roadmap diagram (WP-00..WP-21)` - 27 edges
4. `Offline build diagram (S1-S12)` - 22 edges
5. `System overview diagram (offline build + online gateway)` - 22 edges
6. `UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)` - 21 edges
7. `main()` - 20 edges
8. `UniRoute: Universal Model Routing for Efficient LLM Inference (ICLR 2026)` - 19 edges
9. `WP-02 Prompt Builder, Hard Rules, Splitter` - 18 edges
10. `Embedder` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Gate 2: agreement >= 75%, kappa >= 0.40` --semantically_similar_to--> `Judge-human agreement >= 75%?`  [INFERRED] [semantically similar]
  diagrams/07-roadmap.pdf → ref/diagrams/02-offline-build.pdf
- `Built` --references--> `Embedder`  [INFERRED]
  work/reports/WP-03-report.md → src/metis/embed/embedder.py
- `WP-09 Pilot run (100 prompts, both methods, ~$6)` --semantically_similar_to--> `Phase 3 Pilot: 4 models, 200 val, 150 test, 100 human labels (~$9-24)`  [INFERRED] [semantically similar]
  diagrams/07-roadmap.pdf → ref/diagrams/04-plan.pdf
- `WP-15 Gateway core (API, rules, failover, traces)` --semantically_similar_to--> `Phase 5 Gateway: rules, cache, router, failover, checks, traces ($0)`  [INFERRED] [semantically similar]
  diagrams/07-roadmap.pdf → ref/diagrams/04-plan.pdf
- `WP-19 Final evaluation (locked test once, live run ~$1.5)` --semantically_similar_to--> `Phase 6 Evaluate & report: S11 on locked test (~$1-2)`  [INFERRED] [semantically similar]
  diagrams/07-roadmap.pdf → ref/diagrams/04-plan.pdf

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

## Communities (92 total, 44 thin omitted)

### Community 0 - "Offline build diagram (S1-S12)"
Cohesion: 0.18
Nodes (21): Judge-human agreement >= 75%?, Offline build diagram (S1-S12), Pilot (section P): 4 models, 200 val, 150 test, criteria A-D, tie -> pointwise, Revise rubric / tau, S1 Ingest & clean (last user msg + <=2 turns, redact, language tag, de-dup), S10 Choose lambda: quality target or cost budget, S11 Evaluate on S_te (UniRoute vs always-best, always-cheapest, ZeroRouter, K-NN), S12 Router artifact (versioned: method, embedder, K, centroids, Psi, c, lambda, hashes) (+13 more)

### Community 1 - "System Overview and Gateway"
Cohesion: 0.07
Nodes (47): Answer, One repair, then escalate to next-lower Psi_k model (cascade), Online path diagram (G1-G7), Failover: next-lowest s(h), prefer another provider; breaker 3 fails -> 30 s pause, G1 Hard rules (menu->workflow, image->image model, filter -> allowed set A), G2 Preprocess + embed (same as offline S1/S4), G3 Semantic cache hit? (same chatbot, safe to cache), G4 UniRoute router (nearest centroid, s(h)=Psi_k(h)+lambda*c(h), tie->cheaper) (+39 more)

### Community 2 - "test_prompts.py"
Cohesion: 0.56
Nodes (8): bot(), build(), session(), test_exact_duplicates_keep_first_usable(), test_history_limits(), test_prompt_ids_stable(), test_rows_and_flags(), user()

### Community 3 - "UniRoute Paper Concepts"
Cohesion: 0.08
Nodes (35): Area under the deferral curve, Bradley-Terry-Luce model for per-cluster scores, Chatbot Arena (Zheng et al. 2023), Clairvoyant MLP / MatFac oracle baselines, Cluster membership map Phi_clust(x), Deferral curve (quality vs cost), Routing with a dynamic LLM pool, EmbedLLM benchmark (Zhuang et al. 2024) (+27 more)

### Community 4 - "Roadmap and Phases"
Cohesion: 0.11
Nodes (37): Roadmap diagram (WP-00..WP-21), Full dataset arrives, Gate 1: owner approves budget, Gate 2: agreement >= 75%, kappa >= 0.40, Gate 3: git tag pre-test, WP-00 Bootstrap (git, GitHub, session mechanism), WP-01 Data + redaction (safe loader, data card), WP-02 Prompts, rules, splits (S1, S2, hard rules) (+29 more)

### Community 5 - "test_redact.py"
Cohesion: 0.25
Nodes (6): fake(), test_each_kind_redacted(), test_idempotent(), test_key_inside_assignment_counted_once(), test_no_false_positive(), test_redact_message_all_fields()

### Community 7 - "UniRoute Pipeline Spec"
Cohesion: 0.15
Nodes (22): Pipeline explained step by step, Manager/employees report-card analogy, Online example: complaint message routed to gpt-4o-mini, Data artifacts schemas (§3), UniRoute Pipeline Specification, Deferral area and QNC, Experiment mode (holdout unseen models), Fingerprint Ψ_k(h) (+14 more)

### Community 9 - "Qdrant Vector Store"
Cohesion: 0.14
Nodes (5): _check_payload(), collection_name(), point_id(), VectorStore, test_point_id_stable()

### Community 11 - "s4"
Cohesion: 0.05
Nodes (39): nano, small, name, path, revision, s1, chars_per_token, embed_truncate (+31 more)

### Community 12 - "json"
Cohesion: 0.06
Nodes (23): main(), main(), main(), main(), stats(), main(), log(), config_id() (+15 more)

### Community 13 - "Embedder Tests"
Cohesion: 0.18
Nodes (12): emb(), FakeModel, FakeTokModel, test_deterministic(), test_embedder_id_changes_with_preprocessing(), test_empty_input(), test_l2_normalized_float32(), test_prefix_and_task_passed() (+4 more)

### Community 14 - "Embedder Core"
Cohesion: 0.26
Nodes (7): latency(), main(), persian_check(), synth_text(), Embedder, test_merged_adapter_gives_same_vectors(), Built

### Community 15 - "Research and Proposal"
Cohesion: 0.12
Nodes (15): DARS: one answer per prompt is noisy, LLM routing state of the art (research), RouterArena finding: routers too cautious, Routing approach families (RouteLLM, cascades, bandits...), Routing and cascading survey (arXiv 2603.04445), Three-stage router/check/escalate architecture, UniRoute paper notes, Paper experimental facts (datasets, val 400, Gecko) (+7 more)

### Community 16 - "Final Eval and Release"
Cohesion: 0.12
Nodes (17): runs/s7/labels_test.sealed.parquet (sealed), results/eval_protocol.md, WP-19: Final evaluation on test set, scripts/eval_test.py, Live latency run (stage live, ~$1.5, val messages), Primary analysis: router vs always-best (paired bootstrap, McNemar), Production comparison (cost, answer similarity, M15), results/final/ (+9 more)

### Community 18 - "Gateway, Cache, Replay WPs"
Cohesion: 0.13
Nodes (16): MLflow experiment router-selection (D-044), WP-15: Gateway core, scripts/gateway_smoke.py, configs/gateway.yaml, LiteLLM via Metis AI, gateway/mock_provider.py, OpenAI-compatible API (POST /v1/chat/completions), gateway/traces.py (SQLite traces + MLflow spans) (+8 more)

### Community 19 - "API Cost Estimates"
Cohesion: 0.17
Nodes (16): Paid total ~$25-35, hard cap $60, Add a new model: pointwise 800 calls ~$1-3, pairwise 1,200 calls ~$1.5-5, Call counting formulas (spec section 9), claude-sonnet-4-6 (strong, anchor, $0.0075/call), deepseek-v4-flash (cheap, $0.0003/call), API costs diagram, Evaluate cost (300-600 calls, $1-2), Free forever after: remove model, price change, new lambda, re-clustering (+8 more)

### Community 20 - "Embed Benchmark Script"
Cohesion: 0.15
Nodes (4): clusters(), rss_mb(), sample_table(), write_html()

### Community 21 - "Pilot Decision and Judging"
Cohesion: 0.16
Nodes (12): WP-11: Pilot decision (Gate 2), Bias and noise checks (length bias, self-preference, test-retest), Human calibration labels (cal_labels.csv), configs/judge_config.yaml, Pairwise judging, results/pilot_decision.md, Pointwise judging, One rubric revision fallback (DEV-5) (+4 more)

### Community 22 - "Session Protocol Docs"
Cohesion: 0.31
Nodes (13): /handoff skill, /start skill, AGENTS.md rules and session protocol, CLAUDE.md project pointers, CONTINUITY.md session mechanism, Claude Code hooks (SessionStart, UserPromptSubmit, PreCompact, PostCompact), STATUS.md template, Work-package sizing (100k-250k tokens) (+5 more)

### Community 24 - "WP-04 LLM Client, Cache, Budget"
Cohesion: 0.32
Nodes (8): WP-04 LLM Client, Cache, Budget, Budget guard (budget.py, hard cap $60), Call cache SQLite (callcache.py), Metis AI capability check, MLflow local tracing (D-044), Mock mode METIS_MOCK=1, run_batch runner (runner.py), Gate 1 budget approval

### Community 25 - "Report Notes and S1-S2"
Cohesion: 0.16
Nodes (11): S1 Ingest & clean prompts, S2 Split by user/time, Report notes (running), Jina v5-text-small embedder + Qdrant local (D-048), D-044 local MLflow tracing, S1+S2 counts on the sample (WP-02 dry run), Exclusions waterfall for labeled sets, Huge system prompts only in workflow turns (+3 more)

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

### Community 32 - "System overview diagram (offline build + online gateway)"
Cohesion: 0.19
Nodes (22): Answer, Cache hit?, Call model + failover, Code checks + escalation, Choose K and lambda on validation, Clean, redact secrets, split by conversation, System overview diagram (offline build + online gateway), Embed locally + K-means (no API calls) (+14 more)

### Community 33 - "Judging Methods"
Cohesion: 0.22
Nodes (9): Anchor model (pairwise), S8-PW Bradley-Terry per-cluster fingerprint, Judge prompts (Appendix A1/A2), Label-method pilot (§P), S7-PW Pairwise judging vs anchor, S7-PT Pointwise judging, S3 Model registry, costs, anchor, S6 Generate answers (+1 more)

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

### Community 38 - "Planning Request v2"
Cohesion: 0.22
Nodes (5): Continuing work across sessions (§5c), Planning deliverables (PLAN, CONTINUITY, ROADMAP, AGENTS, CLAUDE, MASTER_LOG, PROJECT), Planning request: Metis-Auto v2, Open questions Q-001..Q-009, Decisions needed

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

### Community 44 - "Sample Data Card"
Cohesion: 0.25
Nodes (7): Sample dataset (100 sessions, 907 messages), Secrets in the data: 44 redaction hits, Four usage categories (25 sessions each), Data card: sample.json, Key paths schema of sample.json, Bot model distribution (18 models, 7 providers), Redaction hits by field/kind (0 after re-scan)

### Community 45 - "UniRoute every-step diagram (S1-S12, R1-R4, M1-M4)"
Cohesion: 0.19
Nodes (21): UniRoute every-step diagram (S1-S12, R1-R4, M1-M4), M1 Add a model (answer 400 val prompts -> new Psi row), M2 Remove a model (delete Psi row, $0), M3 Price change (update c, re-pick lambda, $0), M4 Traffic drift (re-run S5, $0), R1 Embed (same model as S4), R2 Nearest cluster k*, R3 Score each model s(h)=Psi_k*(h)+lambda*c(h) (+13 more)

### Community 46 - "Embedder benchmark (WP-03 step 5)"
Cohesion: 0.29
Nodes (6): 1. Latency, p50 / p95 in ms (one message), 2. Determinism and devices, 3. Persian sanity (40 synthetic pairs: 20 paraphrase, 20 topically close but different), 4. Cluster readability on the sample (K-means, seed 20261020, `clustering` adapter), 5. Qdrant vs numpy, Embedder benchmark (WP-03 step 5)

### Community 47 - "Owner Fixed Points"
Cohesion: 0.29
Nodes (3): draw.io pastel diagram style, Reproducibility: cached calls, config hashes (E11), Secrets handling and redaction (E13)

### Community 48 - "WP-03 report: Embedder + Qdrant"
Cohesion: 0.50
Nodes (3): Decision table (details: `results/embedder_benchmark.md`), Outcome, WP-03 report: Embedder + Qdrant

### Community 50 - "Metis AI and Risks"
Cohesion: 0.33
Nodes (5): Fallback plan for late data (P4), Judge GPT-5.x class via Metis AI (M10), Metis AI API aggregator, R17 network split (Metis AI unreachable), Risks R1-R17

### Community 51 - "UniRoute Diagram Explained"
Cohesion: 0.33
Nodes (6): Diagram 05-uniroute, UniRoute explained with one diagram, M1 Add a model (no retraining), Online steps R1-R4, Seven diagram bands (prepare..maintain), Maintenance operations (add/remove model, recluster, drift)

### Community 53 - "WP Template"
Cohesion: 0.17
Nodes (14): WP Template, WP-03 Embedder and Vector Store, Embedder (src/metis/embed/embedder.py), Embedding latency budget <=60 ms p95 (E5), Persian sanity check (40 synthetic pairs, AUC>=0.85), Qdrant local store (src/metis/embed/store.py), Baselines: ZeroRouter, K-NN, logistic, estimate_costs.py (+6 more)

### Community 54 - "Evaluation Protocol"
Cohesion: 0.50
Nodes (3): 4 candidate models (deepseek-v4-flash, gpt-4o-mini, gemini-2.5-flash, claude-sonnet-4-6), Statistics and evaluation protocol (§8), WP-19 Final evaluation

## Knowledge Gaps
- **114 isolated node(s):** `metis`, `M2 Remove a model (delete Psi row, $0)`, `M3 Price change (update c, re-pick lambda, $0)`, `Decisions needed (dataset, API access, budget, labeling, pool)`, `Risks and mitigations` (+109 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 291 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **44 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Data card: sample.json` connect `Sample Data Card` to `json`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **What connects `metis`, `M2 Remove a model (delete Psi row, $0)`, `M3 Price change (update c, re-pick lambda, $0)` to the rest of the system?**
  _114 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `System Overview and Gateway` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Why does `Planning request: Metis-Auto v2` connect `Planning Request v2` to `Sample Data Card`, `UniRoute Pipeline Spec`, `Research and Proposal`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `UniRoute Paper Concepts` be split into smaller, more focused modules?**
  _Cohesion score 0.08130081300813008 - nodes in this community are weakly interconnected._
- **Why does `Sample dataset (100 sessions, 907 messages)` connect `Sample Data Card` to `Planning Request v2`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Roadmap and Phases` be split into smaller, more focused modules?**
  _Cohesion score 0.10810810810810811 - nodes in this community are weakly interconnected._