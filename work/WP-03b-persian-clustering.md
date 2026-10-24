# WP-03b: Persian clustering test on public data (embedding + K-means only)

> **Paste prompt (fallback if hooks fail):** "Read STATUS.md, AGENTS.md and
> work/WP-03b-persian-clustering.md, then follow the session protocol: propose, wait for my OK, work, /handoff."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~150k | OK (given 2026-10-24); Khayyam access (pending) | $0 | WP-03 | WP-08 (embedder choice input) |

## Context
The full dataset has not arrived. Owner (2026-10-24, Q-023): test **only the embedding and clustering
part** of UniRoute (S4, S5) on public Persian data, the way the paper's K-means works on EmbedLLM (a mix
of benchmarks → clear clusters) and is weak on Headlines (one topic). **No model answers, no API calls.**
Benchmarks carry known source/subject labels, so cluster quality can be **measured** (no human reading).
Real Persian chat prompts (Arena, WildChat, lmsys) show how chat traffic clusters. Feeds D-052
(small vs nano). Candidate list: `ref/docs/persian-datasets.md`.

## Read (only these)
- `results/embedder_benchmark.md` · `ref/docs/persian-datasets.md` · `scripts/s4_embed_bench.py` (reuse)

## Steps
> **Updated 2026-10-25 (D-053):** steps 1–5 done with the paper protocol (train 60 % / val 400 / test,
> 10 repeats, K = 3..8 + reference K, Khayyam human-difficulty proxy); figures by `scripts/s4_cluster_plots.py`.
> Results `results/persian_clustering.md`. Waiting at the step-5 ⏸.

1. `scripts/ext_download.py`: download public sets to `data/external/<name>/` (git-ignored) via the HF
   datasets-server parquet/filter API (plain HTTP, resumable). Record source, config, split, licence,
   row count, sha256 in `data/external/manifest.json` (+ a copy without paths in `results/`).
   Labelled: Global-MMLU fa (57 subjects / 6 categories), INCLUDE Persian (domain), Persian ARC,
   ParsiNLU multiple-choice (category), Persian BBH (20 tasks), PerCoR (domain, sample), Iran legal QA
   and Persian medical QA (samples), Persian math (sample); Khayyam (38 tasks) when access is granted.
   Chat (no labels): Arena fa (140k + 100k sets), WildChat-1M Persian, Persian_lmsys_QA (first user turn).
2. `scripts/s4_persian_cluster.py`: build the sets — **T1 mix** (all labelled sources, label = source,
   fine label = subject where it exists), **T2 Global-MMLU fa** alone (labels = subject, category),
   **T3 chat** (first user message only, D-045). Dedupe exact texts; record counts and token stats.
3. Embed with small and nano (`clustering`, merged, MPS; checkpointed to `data/external/emb/`).
4. As the paper: split 60/40 (seed 20261020); K-means (k-means++, 10 restarts) on the 60 % part for
   K ∈ {3, 4, 6, 8, 12, 16, 24, 32, 48, 64} (+ K = #labels); assign the 40 % by nearest centroid.
   Metrics on the 40 %: NMI, ARI, purity vs labels; cosine silhouette; cluster size spread. T3: silhouette,
   sizes, length/script mix per cluster (no labels). Reference: `text-matching` adapter for T1 (one K).
5. `results/persian_clustering.md` (+ JSON); `runs/s4/persian_clusters_<model>.html` with 8 random
   items per cluster for the owner (T1 and T3).
   ⏸ **STOP:** owner reads the results and the HTML; says what changes (e.g. small vs nano).
6. Log decisions; Q-023 updated; `/handoff`.

## Outputs
- `scripts/ext_download.py`, `scripts/s4_persian_cluster.py`, `results/persian_clustering.md`,
  `results/persian_clustering_<model>.json`, local HTML pages.

## Acceptance checks
- [ ] No API call to any LLM; downloads only public HF datasets; nothing from `data/` committed.
- [ ] Metrics on held-out items only (K-means fitted on the 60 % part), seed recorded.
- [ ] Same embedder settings as `configs/pipeline.yaml` `s4:`.

## If blocked
- Dataset gated / download fails → skip it, note it; Khayyam added later (`--only khayyam`).
- datasets-server filter index "loading" → retry with back-off; fall back to parquet + local filter.

## End of session (in addition to `/handoff`)
- `work/reports/WP-03b-report.md`; log decisions; update WP-08 step 6 if the results favour a model.
