# ROADMAP: work packages

**Where are we?** → `STATUS.md` (current WP and exact next step). This file is the route.
Tick a WP (☐ → ☑) only in `/handoff` when its done-criterion holds and its report exists.
Instructions per WP: `work/WP-xx-*.md`. Plan and reasons: `PLAN.md`. Session mechanics: `CONTINUITY.md`.

Legend: **$** paid API calls · **👤** needs the owner (approval, labels, data, login) · model: every session uses the **default model (Opus 5.5)** ·
tokens = rough session size (target ≤ 250k; hand off at 60% of context).

## At a glance

Diagram: `diagrams/07-roadmap.drawio` (`.png`, `.pdf`).

```
Phase 0 Setup            WP-00
Phase 1 Free build       WP-01 → WP-02 → WP-03 · WP-04 · WP-05 · WP-06 → WP-07        ($0)
Phase 2 Real data in     [full data] → WP-08 → ⛔G1 budget                               ($0)
Phase 3 Small pilot      WP-09$ → WP-10👤 → WP-11 → ⛔G2 judge                           (~$7)
Phase 4 Main build       WP-12$ → WP-13$ → WP-14 → ⛔G3 tag pre-test                     (~$17–27)
Phase 5 Gateway          WP-15 → WP-16 → WP-17 (decision) → WP-18   alongside phases 2–4 ($0–1)
Phase 6 Final test       WP-19$                                                          (~$1.5)
Phase 7 Report, release  WP-20 → WP-21                                                   ($0)
```

## Work packages

**Order changed 2026-10-31 (D-068):** WP-08 part A is done first, then WP-04 → 06 → 07 → WP-08 part B. WP-08 stays unticked until Gate 1.

| ☐ | WP | Phase | Goal | Model | Tokens | 👤 | $ | Needs | Unblocks |
|---|---|---|---|---|---|---|---|---|---|
| ☑ | **WP-00** Bootstrap | 0 | Project folder, git + private GitHub, secret scan, continuity mechanism installed and tested | default | 80k | 👤 approve installs, `gh` login | – | – | all |
| ☑ | **WP-01** Data access + redaction | 1 | Safe loader for the session/message schema; redaction; structure-only data card of the sample | default | 120k | – | – | 00 | 02, 06, 08 |
| ☑ | **WP-02** Prompts, rules, splits | 1 | S1 prompt builder (current user message only, D-045), Persian normalization, language tag, exclusions incl. huge prompts, hard-rule detectors, S2 session splitter | default | 200k | – | – | 01 | 03, 07, 08, 15 |
| ☑ | **WP-03** Embedder + Qdrant (choice → WP-08) | 1 | Set up Jina v5-text-small (local) + Qdrant local; check latency, Persian paraphrase sanity, cluster readability (D-048) | default | 150k | 👤 approve choice | – | 02 | 05-real, 08, 15 |
| ☑ | **WP-03b** Persian clustering test | 1 | Embed + K-means on public Persian benchmarks and chat prompts; measure clusters vs known subjects (Q-023) | default | 150k | 👤 OK, Khayyam access | – | 03 | 08 |
| ☑ | **WP-04** LLM client, call cache, budget | 1 | LiteLLM client → Metis AI, SQLite call cache, local MLflow tracing, budget guard + ledger, resumable runner, cost estimator, free Metis AI capability check | default | 180k | 👤 key in `.env`, OK for free model-list call | – | 00 | 06, 09, 15 |
| ☑ | **WP-05** Router core + evaluation library | 1 | S5, S8 (pointwise + BT), S9 (R = 20), S10, S11 metrics, baselines (ZeroRouter, K-NN, logistic), bootstrap/McNemar/κ, tested on synthetic data with a planted answer. Report: `work/reports/WP-05-report.md` | default | 250k | – | – | 00 | 07, 14 |
| ☑ | **WP-06** Generation + judge pipeline (mocked) | 1 | S6/S7 runners, judge templates (A1/A2 extended), robust JSON parsing, labeling tool (blind, randomized) | default | 200k | 👤 10-min tool test on 5 sample items | – | 01, 04 | 07, 09 |
| ☑ | **WP-07** End-to-end dry run | 1 | Whole S1–S12 on the sample with a mock LLM; artifact produced; rerun = 100% cache hits; no key in any outgoing request | default | 150k | – | – | 02–06 | 08 |
| ☑ | **WP-08** Full data in | 2 | Data card, S1–S5 on real data, splits locked, clusters named, **budget memo** | default | 200k | 👤 provide data; **⛔ Gate 1** approve budget | – | data, 07 | 09, 12 |
| ☑ | **WP-09** Pilot run | 3 | 4 models × 100 pilot prompts; pointwise + pairwise judging; labeling sheet | default | 120k | 👤 "go" | **~$6** | G1 | 10 |
| ☑ | **WP-10** Owner labels (done by Opus, D-098) | 3 | 100 calibration items (`human_pass`, `human_pref`) + 20 re-labels later | – (owner) | – | 👤 **~3.5 h** | – | 09 | 11 |
| ☑ | **WP-11** Pilot decision | 3 | Agreement + κ, τ, separability, bias + noise checks; choose method; update WP-13 | default | 150k | 👤 **⛔ Gate 2** | (~$2 if rubric revised) | 10 | 12, 13 |
| ☐ | **WP-12** Generation val + test | 4 | Remaining answers for 400 val + 300 test (pilot reused); cheap models first. **Val done, test left** | default | 100k | 👤 "go" | **~$7** | G2 | 13 |
| ☐ | **WP-13** Judging | 4 | Chosen method on all val + test + 5% re-judge. **Val done, test left** | default | 100k | 👤 "go" | **~$10 / ~$20** | 12 | 14 |
| ☐ | **WP-14** Fingerprints, settings, freeze | 4 | Ψ (Eq. 12), K by deferral-curve area, λ, baselines for comparison, holdout demo, artifact v1, evaluation protocol, **tag `pre-test`** | default | 250k | 👤 approve shipped router (+ DEV-1 if traits win) | – | 05, 13 | 18, 19 |
| ☐ | **WP-15** Gateway core | 5 | FastAPI OpenAI-compatible service, rules, router (mock artifact first), LiteLLM calls, failover + breaker, traces, fault-injection tests | default | 250k | – | – | 02, 03, 04 | 16, 17 |
| ☐ | **WP-16** Checks, escalation, latency | 5 | G6 checks + repair + escalation, stickiness option, latency measurement | default | 150k | – | – | 15 | 18 |
| ☐ | **WP-17** Semantic cache | 5 | **Decision point first** (threshold method), then exact + meaning cache with safety rules | default | 150k | 👤 decide method | ≤ $1 | 15 (+08 for real pairs) | 18 |
| ☐ | **WP-18** Replay + dashboard | 5 | Replay simulator on stored answers + measured latencies; metrics; dashboard | default | 200k | – | – | 14, 16, 17 | 19 |
| ☐ | **WP-19** Final evaluation | 6 | Open the test set once; protocol analyses; ladder + production; replay; small live latency run | default | 250k | 👤 "go" for live run | **~$1.5** | G3, 18 | 20 |
| ☐ | **WP-20** Report + presentation | 7 | Report with CIs and limitations, draw.io figures, dashboard + MLflow screenshots, optional pricing model | default | 200k | 👤 review | – | 19 | 21 |
| ☐ | **WP-21** Reproducibility + release | 7 | Fresh clone rerun from caches ($0), secret scan, README, tag `v1.0` | default | 100k | – | – | 20 | – |

Paid total (pointwise path) ≈ **$25**, pairwise ≈ **$35**, cap **$60** (`PLAN.md §7`).

## What can run when

| Lane | Before the full data | After the data |
|---|---|---|
| Pipeline | WP-00 → 01 → 02 → 03 / 04 / 05 / 06 → 07 | 08 → 09 → 10 → 11 → 12 → 13 → 14 → 19 |
| Gateway | WP-15, WP-16 (mock artifact), WP-17 code (rules + exact match) | WP-17 threshold, WP-18 |
| Report | outline + method chapter can start after WP-07 | WP-20, WP-21 |

**Parallel-safe pairs** (different files): WP-03 ∥ WP-04 ∥ WP-05 ∥ WP-06 (after 01/02); WP-15/16 ∥
WP-09…14. Run them as separate sessions, one at a time on Pro; their reports must not edit each
other's WP files except through the results → changes table (`PLAN.md §6`).

## Gates

| Gate | Where | Pass condition | If it fails |
|---|---|---|---|
| ⛔ G1 Budget | end of WP-08 | Owner approves the per-stage amounts under $60 | Reduce sizes / `max_tokens` per `PLAN.md §6` |
| ⛔ G2 Judge | end of WP-11 | Agreement ≥ 75%, κ ≥ 0.40 (+ position consistency ≥ 80% if pairwise) | One rubric revision, then owner decides |
| ⛔ G3 Freeze | end of WP-14 | Tag `pre-test` with artifact + protocol committed | WP-19 must not start |

## Fallback dates (`PLAN.md` P4)

- **2026-11-01** no full data → reduced plan (val 300 / test 200, K ≤ 6, pilot merged into WP-12/13).
- **2026-11-08** still no data → sample-only demonstration, clearly labeled underpowered.
