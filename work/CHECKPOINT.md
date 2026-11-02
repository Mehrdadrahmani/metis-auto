# Checkpoint: all work packages and tasks

Snapshot of 2026-11-01, after WP-04. Source of truth for "where we are": `STATUS.md`. Details of each task:
`work/WP-xx-*.md`. Spent so far: $0.00 of $60.

Marks: ☑ done · ◐ partly done · ☐ not started · ⏸ needs the owner · ⛔ gate · 💲 paid

| Phase | WP | Status |
|---|---|---|
| 0 | WP-00 Bootstrap | ☑ |
| 1 | WP-01 Data access and redaction | ☑ |
| 1 | WP-02 Prompts, rules, splits | ☑ |
| 1 | WP-03 Embedder and Qdrant | ☑ |
| 1 | WP-03b Persian clustering test | ☑ |
| 1 | WP-04 LLM client, cache, budget | ☑ |
| 1 | WP-05 Router core and evaluation (incl. WP-05b) | ☑ |
| 1 | WP-06 Generation and judge pipeline | ☐ **current** |
| 1 | WP-07 End-to-end dry run | ☑ |
| 2 | WP-08 Full data in | ◐ part A done, part B paused |
| 3 | WP-09 Pilot run | ☐ 💲 ~$6 |
| 3 | WP-10 Owner labels | ☐ ⏸ ~3.5 h |
| 3 | WP-11 Pilot decision | ☐ ⛔ Gate 2 |
| 4 | WP-12 Generation val + test | ☐ 💲 ~$7 |
| 4 | WP-13 Judging | ☐ 💲 |
| 4 | WP-14 Fingerprints, settings, freeze | ☐ ⛔ Gate 3 |
| 5 | WP-15 Gateway core | ☐ |
| 5 | WP-16 Checks, escalation, latency | ☐ |
| 5 | WP-17 Semantic cache | ☐ ⏸ |
| 5 | WP-18 Replay and dashboard | ☐ |
| 6 | WP-19 Final evaluation | ☐ 💲 ~$1.5 |
| 7 | WP-20 Report and presentation | ☐ ⏸ |
| 7 | WP-21 Reproducibility and release | ☐ |

Stage costs above are planning values; the draft memo (`results/budget_memo.md`) puts the pointwise
total at about $35 mid, $73 high. Gate 1 is not passed.

## Done

- **WP-00:** tools, git and private GitHub, folders, `.gitignore`, secret scan hook, uv environment, session mechanism, first commit.
- **WP-01:** schema, loader, redaction, data card, tests.
- **WP-02:** Persian normalization, language tag, S1 prompt table, hard rules, duplicates, S2 splitter, sample run.
- **WP-03:** embedder wrapper, Qdrant store, benchmarks, choice frozen in config.
- **WP-03b:** public Persian sets, embedding, K-means, report.
- **WP-04:** client, cache, budget guard, runner, mock mode, MLflow, Metis check, real prices. Report: `work/reports/WP-04-report.md`.
- **WP-05 / 05b:** K-means, fingerprints, routing, metrics, K and λ selection, baselines, statistics, synthetic proof, artifact.

## WP-06 Generation and judge pipeline

- ☐ 1. Propose
- ☐ 2. `configs/gen_config.yaml`
- ☐ 3. `llm/messages.py`: request building
- ☐ ⏸ 4. Owner reviews the judge prompt, then templates
- ☐ 5. Robust JSON parsing
- ☐ 6. Pointwise and pairwise judges, S6 and S7 scripts
- ☐ 7. Labeling tool
- ☐ ⏸ 8. Tool test on 5 mock items
- ☐ 9. Tests
- ☐ 10. `scripts/estimate_costs.py`

## WP-07 End-to-end dry run

- ☑ 1. Propose
- ☑ 2. Pipeline script for all stages
- ☑ 3. Mock judge
- ☑ 4. Run all stages on the sample
- ☑ 5. Second run: 0 new calls
- ☑ 6. Leak test on outgoing requests
- ☑ 7. `results/dry_run_report.md`
- ☑ 8. Cost estimate for real sizes

Split and clusters rerun (D-080, D-088). No S1 rules bug exists (D-090).

## WP-08 Full data in

- ☑ 1–2. Data in, data card
- ☑ 3. S1 on full data
- ☑ 4. Sizes: val 400, test 300
- ☑ 5. Split on all traffic, test sealed (DEV-11, D-076)
- ☑ 6. Embedder nano, Qdrant, near-duplicates at 0.95
- ☑ 7. K-means K 3 to 20, stability
- ☑ ⏸ 8. Cluster names: K = 8 from Qwen3-8B (D-092)
- ☑ ⏸ ⛔ 9. Budget memo; Gate 1 passed (D-094)
- ☑ 10. Update later WPs if a PLAN §6 row triggers
- ☑ WP-08 report

## WP-09 Pilot run 💲

- ☐ ⏸ 1. Show estimate, owner says go
- ☐ 2. S6: 100 prompts × 4 models
- ☐ 3. S7 pointwise: 400 judgments
- ☐ 4. S7 pairwise: 600 judgments
- ☐ 5. Noise sample
- ☐ 6. Labeling page for 100 items
- ☐ 7. Record spend

## WP-10 Owner labels ⏸

- ☐ Label 100 calibration items, about 3.5 h, plus 20 re-labels later

## WP-11 Pilot decision ⛔

- ☐ 1. Propose, load labels
- ☐ 2. Pointwise agreement and τ
- ☐ 3. Pairwise agreement
- ☐ 4. Separability and stability
- ☐ 5. Bias and noise checks
- ☐ 6. Decide by the rule
- ☐ ⏸ ⛔ 7. Gate 2
- ☐ 8. Write `configs/judge_config.yaml`

## WP-12 Generation val + test 💲

- ☐ ⏸ 1. Estimate, owner says go
- ☐ 2. Generate, cheapest model first
- ☐ 3. Monitor each model after 50 calls
- ☐ 4. Handle failed calls
- ☐ 5. Record latency

## WP-13 Judging 💲

- ☐ ⏸ 1. Estimate, owner says go
- ☐ 2. Judge all val and test answers
- ☐ 3. Re-judge 5%
- ☐ 4. Monitor after 100
- ☐ 5. Derive val labels; test stays sealed

## WP-14 Fingerprints, settings, freeze ⛔

- ☐ 1. Propose
- ☐ 2. Fingerprints for K 3 to 20
- ☐ 3. Choose K, only K ≤ 11 can win (D-079)
- ☐ 4. Baselines
- ☐ 6. Choose λ
- ☐ 7. Holdout demo
- ☐ 8. Artifact v1
- ☐ 9. Evaluation protocol
- ☐ Later tests: bot term (D-078), history input (D-069)
- ☐ ⏸ ⛔ 10. Gate 3, tag `pre-test`

## WP-15 Gateway core

- ☐ 1. Propose
- ☐ 2. FastAPI service
- ☐ 3. Request pipeline
- ☐ 4. Failover and breaker
- ☐ 5. Traces
- ☐ 6. Gateway config
- ☐ 7. Mock provider
- ☐ 8. Tests
- ☐ 9. Smoke test

## WP-16 Checks, escalation, latency

- ☐ 1. Propose
- ☐ 2. Quality checks
- ☐ 3. Repair and escalation
- ☐ 4. Stickiness option
- ☐ 5. Latency benchmark
- ☐ 6. Tests

## WP-17 Semantic cache

- ☐ ⏸ 1. Owner picks the threshold method
- ☐ 2. Cache per chatbot
- ☐ 3. Cacheability rules
- ☐ 4. Threshold
- ☐ 5. Wire into the gateway
- ☐ 6. Tests

## WP-18 Replay and dashboard

- ☐ 1. Propose
- ☐ 2. Replay simulator
- ☐ 3. Metrics
- ☐ 4. Runs on val
- ☐ 5. Dashboard
- ☐ 6. Tests

## WP-19 Final evaluation 💲

- ☐ 1. Propose, verify tag
- ☐ 2. Open test labels once
- ☐ 3. Primary analysis
- ☐ 4. Secondary analyses
- ☐ 5. Production comparison
- ☐ 6. Replay on test
- ☐ ⏸ 7. Live latency run
- ☐ 8. Final tables and report

## WP-20 Report and presentation

- ☐ ⏸ 1. Confirm format, outline
- ☐ 2. Write outline sections
- ☐ 3. Figures
- ☐ 4. Draft and fresh review
- ☐ 5. Presentation and demo script

## WP-21 Reproducibility and release

- ☐ 1. Propose
- ☐ 2. Fresh clone rerun
- ☐ 3. Secret scan of history
- ☐ 4. README
- ☐ 5. Final budget, close questions
- ☐ 6. Tag `v1.0`
