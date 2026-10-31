# results/ — aggregates only (no prompt, answer or system-prompt text)

One folder per work package. Raw texts and per-item outputs stay in git-ignored `data/` and `runs/`.

| Folder | WP | What is inside |
|---|---|---|
| `wp01_data/` | WP-01 | Data card of the sample (`data_card_sample.md`) + manifest |
| `wp02_prompts_splits/` | WP-02 | S1/S2 counts on the sample (`s1_s2_sample_counts.md`), split manifest |
| `wp03_embedder/` | WP-03 | Embedder benchmark: latency, Persian pair AUC, sample clusters (`embedder_benchmark.md` + JSON per model) |
| `wp05_router/` | WP-05 | Router on planted synthetic data: routers compared; K rule review |
| `wp03b_persian/` | WP-03b | Persian clustering test on public data, paper protocol: |
| | | · `persian_clustering.md` — short results (full report: `report/persian_clustering/README.md`) |
| | | · `persian_data_card.md`, `persian_sources.json` — the 12 public sources |
| | | · `persian_clustering_{small,nano,nano_text-matching}.json` — scores per set and K |
| | | · `persian_cluster_meaning.json`, `persian_cluster_topics.json` — what is inside each cluster |
| | | · `figures/` — curves and maps |

Local pages with prompt texts (for the owner only, never committed): `runs/s4/`.
New WPs add their own `wpNN_<name>/` folder.
