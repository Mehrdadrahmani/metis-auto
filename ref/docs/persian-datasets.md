# Persian datasets for testing the router (owner idea, 2026-10-24; Q-023)

**Goal:** test our UniRoute pipeline on public Persian data the way the paper does on English data.
The paper's datasets (EmbedLLM, RouterBench, SPROUT, Headlines, OpenLLM v2, Math+Code, Chatbot
Arena) are **English benchmarks with pre-computed answers from many models and a 0/1 correct label
per (question, model)**, or human pairwise votes (Arena). The authors never called the models.

So a Persian equivalent needs either
- **(A) ready routing data:** Persian questions + per-model results already computed → $0, or
- **(B) Persian questions with gold answers** (multiple choice / short answer): we generate answers
  with our 4 candidates and grade automatically (exact match, no LLM judge) → small API cost.

Found by web search on 2026-10-24 (not yet downloaded; licences to be checked before use).

## (A) Ready routing data (per-model, per-question results)

| Dataset | What | Size | Models with per-item scores | Licence | Fit |
|---|---|---|---|---|---|
| [heyparsadev/persian-llm-eval](https://github.com/heyparsadev/persian-llm-eval) | Iranian-Persian benchmark: knowledge, short QA, reading, instruction, culture, hard reasoning/math; deterministic scoring (mcq / exact / F1 / instruction / json) | 149 public_eval + 145 hard (+150 practical, 100 challenge) | **17** on public_eval, **20** on hard (Claude 4.x/5.5, GPT-5.x incl. claude-sonnet-4-6); `results/*.json` hold per-item `prediction` + `score` | MIT | **Closest to the paper: a mini "RouterBench" in Persian, $0.** Small (~294 items; paper val ≈ 400), and only OpenAI/Anthropic models (none of our deepseek/gemini/gpt-4o-mini) |

No public Persian human-preference arena with votes was found. LMArena's public sets (e.g.
`lmsys/chatbot_arena_conversations`, `lmarena-ai/arena-human-preference-100k`) carry a language tag;
the number of Persian rows is unknown (probably small).

## (B) Persian questions with gold answers (we would generate + auto-grade)

| Dataset | English counterpart | Size | Where | Licence / access |
|---|---|---|---|---|
| Khayyam Challenge (PersianMMLU) | MMLU | 20,192 four-choice, 38 tasks, difficulty + human answer rates | HF `raia-center/khayyam-challenge` (gated) | CC BY-NC-ND, academic only |
| Global-MMLU (fa) | MMLU (translated) | MMLU size per language | HF `CohereForAI/Global-MMLU` | check card |
| Persian ARC | ARC | 1K–10K | HF `MatinaAI/persian_arc` | check card |
| PerCoR | HellaSwag-like commonsense | 106K multiple choice | HF `MCINext/PerCoR` | check card |
| PMWP | GSM8K-like math word problems | 15K | paper (SilkRoadNLP 2026) | check |
| PQuAD / PersianQA / ParsiNLU | SQuAD / reading comprehension, MC QA | 80K / 10K / 14.5K | HF / GitHub | various |
| FarsEval-PKBETS | mixed benchmark | 4,000 (MC, short, descriptive) | arXiv 2504.14690 | check |
| TARAZ, PersLitEval, MELAC sets | culture / literature / exams | various | arXiv | various |

Open Persian LLM Leaderboard (PartAI/AUT, 40K+ samples) publishes only a sample of its data and no
per-item model outputs.

## How it could be used (proposal, not decided)

1. **$0, any time:** run S4–S11 (embed, K-means, Eq. 12 fingerprints, K by deferral area, routing)
   on persian-llm-eval's per-item scores, with a few of its models as "candidates" and list prices
   as cost. Shows whether UniRoute beats always-best / always-cheapest on Persian at all. Caveat:
   ~294 items → K ≤ 5 and wide CIs.
2. **Paid (after the full dataset, fixed rule 2):** ~1,000 items from Khayyam / Persian ARC / PMWP,
   answers from our 4 candidates, exact-match grading (no judge). Rough cost $1–3 (short answers).
   Gives a Persian check of our exact model pool with objective labels, independent of the judge.

Sources: [Khayyam Challenge](https://huggingface.co/datasets/raia-center/khayyam-challenge) ·
[Khayyam paper](https://www.arxiv.org/abs/2404.06644) · [Global-MMLU paper](https://arxiv.org/pdf/2412.03304) ·
[Persian ARC](https://huggingface.co/datasets/MatinaAI/persian_arc/tree/refs%2Fconvert%2Fparquet/ARC-Challenge/train) ·
[PerCoR](https://arxiv.org/pdf/2510.22616) · [PMWP](https://preview.aclanthology.org/credits/2026.silkroadnlp-1.8) ·
[PQuAD](https://arxiv.org/abs/2202.06219) · [FarsEval-PKBETS](https://arxiv.org/pdf/2504.14690) ·
[TARAZ](https://arxiv.org/pdf/2602.22827) · [PersLitEval](https://arxiv.org/html/2605.27015) ·
[MELAC](https://preview.aclanthology.org/setup/2025.ijcnlp-long.105) ·
[Open Persian LLM Leaderboard](https://huggingface.co/spaces/PartAI/open-persian-llm-leaderboard/blame/4b7489333e901a8e24642645f905d456bbac3ce9/utils.py) ·
[persian-llm-eval](https://github.com/heyparsadev/persian-llm-eval) ·
[awesome-persian-datasets](https://github.com/MasoudKaviani/awesome-persian-datasets) ·
[Chatbot Arena data](https://huggingface.co/datasets/lmsys/chatbot_arena_conversations)
