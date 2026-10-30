# WP-03b report: Persian clustering test

Sessions: 2026-10-24..28, closed 2026-10-30. Cost $0, no LLM calls. Full results:
`results/wp03b_persian/persian_clustering.md`; review: `report/persian_clustering/latex/main.pdf`.

## Built
- `scripts/ext_download.py` (public sets, plain HTTP), `scripts/s4_persian_cluster.py` (paper protocol,
  Jina instead of Gecko), `scripts/s4_cluster_plots.py`, `scripts/s4_latex_tables.py`.
- Local pages for the owner: `runs/s4/persian_map_{nano,small}.html`, `runs/s4/persian_clusters_{nano,small}.html`.

## Results (measured, K = 8, small / nano)

| Set | NMI vs known label | Note |
|---|---|---|
| Mix of benchmarks (source) | 0.35 / 0.35 | clear clusters, like EmbedLLM in the paper |
| Khayyam (38 categories) | 0.42 / 0.41 | |
| Global-MMLU (57 subjects) | 0.41 / 0.39 | |
| One topic | 0.10 / 0.11 | weak, like Headlines in the paper |

- Chat silhouette 0.15 against 0.15–0.30 for benchmarks: real traffic should cluster more softly.
- Clusters shrink the human-error gap by about 5–6 % against K = 1 (Khayyam proxy, not a routing result).
- The val size limits K, not the embedder: with Ψ from val 400 the gain stops rising after K ≈ 8–16.

## Outcome
- Owner: cluster quality good (D-055).
- Q-024 closed (D-054): K ≤ N_val/50, no per-cluster minimum, α = 0. PLAN, WP-08 and WP-14 checks updated.
- small vs nano not decided: quality about equal, nano 2.5× faster; choice stays in WP-08 (D-052).
- Q-023: embedding + clustering half done; routing half stays open (option 1 after WP-05).

## Limits
- No model answers, so no deferral curve and no real K choice; NMI and the human-difficulty test are proxies.
- Benchmarks are exam questions; real Metis traffic may differ.

## Acceptance
- No LLM calls; only public HF data; nothing from `data/` committed.
- Metrics on held-out items, K-means fitted on train only, seed recorded.
- Same embedder settings as `configs/pipeline.yaml` `s4:`.
