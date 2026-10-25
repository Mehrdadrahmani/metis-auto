# Data card: public Persian data for the clustering test (WP-03b)

Date 2026-10-25 · counts and statistics only (no text read) · downloaded by `scripts/ext_download.py`
(sources, row counts and sha256 in `results/wp03b_persian/persian_sources.json`) · used by `scripts/s4_persian_cluster.py`.

**12 sources, 70,186 unique texts** after removing duplicates and empty texts. Only the question or the
first user message is used (no answer choices, no replies).

| Source | Kind | Rows (kept) | Labels | Length in chars (median / p90) | Persian share | Licence |
|---|---|---|---|---|---|---|
| Khayyam (`raia-center/khayyam-challenge`) | school exams, native Persian | 20,577 | 38 categories, 95 courses, 5 difficulty levels | 115 / 314 | 91 % | CC BY-NC-ND, academic only (gated) |
| Global-MMLU fa (`CohereLabs/Global-MMLU`) | exam, machine-translated | 13,867 | 6 categories, 57 subjects | 102 / 641 | 99 % | Apache-2.0 |
| Persian ARC (`MatinaAI/persian_arc`) | school science | 7,778 | Easy / Challenge | 89 / 204 | 100 % | CC BY-SA 4.0 |
| Persian BBH (`MatinaAI/persian_bbh`) | reasoning puzzles | 4,511 | 19 tasks | 345 / 738 | 94 % | unknown |
| PerCoR (`MCINext/PerCoR`) | commonsense | 3,998 (sample) | 43 domains | 108 / 194 | 100 % | Apache-2.0 |
| Legal QA (`PerSets/iran-legal-persian-qa`) | people's legal questions | 3,000 (sample) | none | 283 / 666 | 100 % | CC |
| Medical QA (`aictsharif/persian-med-qa`) | medical questions | 2,822 (sample) | none | 45 / 65 | 99 % | Apache-2.0 |
| ParsiNLU MC (`PartAI/ParsiNLU-multiple-choice`) | multiple choice | 2,436 | 3 categories | 53 / 125 | 100 % | CC BY-NC-SA 4.0 (ParsiNLU) |
| INCLUDE (`CohereLabs/include-base-44`) | regional exams | 546 | 5 domains, 18 subjects | 75 / 235 | 100 % | Apache-2.0 |
| lmsys fa (`mshojaei77/Persian_lmsys_QA`) | real chat, first message | 5,401 | none | 52 / 124 | 97 % | MIT |
| WildChat (`allenai/WildChat-1M`, Persian) | real chat, first message | 3,222 | none | 59 / 611 | 89 % | ODC-BY |
| Arena (`lmarena-ai/arena-human-preference-140k` + `100k`, Persian) | real chat, first message | 2,028 | none | 71 / 528 | 96 % | CC BY 4.0 |

Language overall (`metis.data.lang.lang_tag`): 96 % Persian, 3 % mixed Persian/English, 0.6 % English,
0.4 % other.

## Test sets

| Set | Size | Role |
|---|---|---|
| mix | 28,802 | 9 benchmarks, ≤ 4,000 each; like the paper's EmbedLLM (a mix of benchmarks) |
| Khayyam | 20,577 | 38 known categories + examinee answer rates (difficulty test) |
| Global-MMLU | 13,867 | 57 known subjects |
| one topic | 1,672 | Khayyam's largest category; like the paper's Headlines (one topic) |
| chat | 10,651 | real Persian chat, no labels; closest to Metis traffic |

## Notes

- Benchmarks are short exam questions; chat messages are shorter on average but have a long tail
  (111 over 2,048 tokens with small, 71 with nano; truncated for this test only).
- Global-MMLU is machine-translated; Khayyam, ParsiNLU, PerCoR and the chats are native Persian.
- Khayyam: academic use only, no derivatives; fine for this course project, never redistribute the data
  (`data/` is git-ignored). Examinee answer rates exist for 16,777 questions.
- Samples (PerCoR, legal QA, med QA) drawn with seed 20261020.
- Results: `results/wp03b_persian/persian_clustering.md`.
