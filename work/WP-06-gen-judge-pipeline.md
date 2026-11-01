# WP-06: Generation and judge pipeline (S6, S7), judge prompts, labeling tool, all mocked

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-06-gen-judge-pipeline.md; follow
> the session protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 1 | default (Opus 5.5) | ~200k | 10-min test of the labeling tool on 5 sample items | $0 (mock mode) | WP-01, WP-04 | WP-07, WP-09 |

## Context
S6 makes each candidate answer like production did (own system prompt, RAG context, history; PLAN
M6). S7 grades answers: pointwise (score 1–10) and pairwise (vs claude-sonnet-5-5, both orders); the
pilot picks one (M8). The judge prompts are the spec's A1/A2 extended with the chatbot's instructions
and context (DEV-5). The owner labels 100 items with a local tool (WP-10), so the tool must be ready
and pleasant to use now.

## Read (only these)
- `ref/UNIROUTE_PIPELINE.md` §4 S6, S7-PT, S7-PW, App. A1, A2, §3 (artifact schemas).
- `PLAN.md` §1.1 M6, M8–M12; `work/reports/WP-02-report.md` (token stats), WP-04 report.

## Steps
1. Propose; ⏸ wait for OK.
2. `configs/gen_config.yaml` (id = hash): `temperature: 0.3`, `max_tokens: 1024`, `top_p: 1`;
   **thinking/reasoning off or minimal for every candidate** (e.g. gemini-2.5-flash-lite thinking budget 0,
   deepseek non-thinking mode) so costs match the estimate and the comparison is fair; record the
   exact provider parameters per model. Same for all models.
3. `src/metis/llm/messages.py`: build the request: `system` = redacted chatbot instructions;
   if `rag_context`: one extra system block "Retrieved context:\n…" (same format for all models);
   then the `history` turns; then the user message. Instructions > 20k chars never reach here (M7).
   **Every part is redacted** with `metis.data.redact.redact_message` (history, user message and
   RAG text too, not only instructions): WP-01 found key hits in user/bot `content` (4) and in
   attachment URLs (13), D-043. The judge prompt (step 4) also uses only redacted text.
4. ⏸ **Owner reviews the judge prompt first (D-059).** **Judge templates** `src/metis/judge/templates/{pointwise,pairwise}.txt` = spec A2/A1 **without
   `{context_turns}`** (judge sees the current user message only, D-046 / DEV-9) plus:
   sections `[CHATBOT INSTRUCTIONS]` (truncated to 6,000 tokens with a "(truncated)" note) and
   `[RETRIEVED CONTEXT]` (or "none"); an added criterion after instruction following: "Follows the
   chatbot's own instructions (role, scope, format, language rules) and stays grounded in the
   retrieved context; invented facts count as errors." Keep "do not reward length" and the JSON
   output contract. `configs/judge_config.yaml`: judge model id (from WP-04), temperature 0 (or the
   lowest reasoning effort if temperature is unsupported), `max_tokens: 400`, template hashes →
   `judge_config_id`.
5. `src/metis/judge/parse.py`: robust JSON extraction (strip code fences, first balanced `{…}`),
   validate fields (`score` int 1–10 / `verdict` ∈ {A, B, tie}); parse failure → retry once → drop
   and log (spec).
6. `src/metis/judge/{pointwise,pairwise}.py` + `scripts/s6_generate.py`, `scripts/s7_judge.py`:
   use `runner.run_batch` (cache, budget guard, checkpoints). Pairwise: both orders with a seeded A/B
   assignment; `o(x,h) = mean`; failed generation → worst label (spec S6 policy).
   Order of models inside a stage: cheapest first, sonnet last (PLAN P3). Stage names for the
   budget: `pilot`, `gen_main`, `judge_main`.
7. **Labeling tool** `src/metis/labeling/build.py` → one self-contained local HTML file
   (`runs/labeling/cal_<date>.html`, git-ignored; RTL-aware, Vazirmatn or system font), no server:
   for each item, show the instructions (collapsed), context, user message and the candidate's answer
   → **"Acceptable? A demanding user would accept it without asking again" yes/no**; then candidate vs
   anchor answers in random left/right order → **better: left / right / tie**; optional note. Model
   names hidden; item order randomized (seeded). Labels autosave in the browser and export to CSV;
   `labeling/ingest.py` reads the CSV into `human_labels`. A guideline box at the top (1 screen, plain
   Persian + English) with the score anchors of spec A2. Also a "re-label" mode for 20 items.
8. Test the tool with **5 mock items** (sample prompts with mock answers). ⏸ **STOP:** ask the owner
   to try it for ~10 minutes and say what to change. Claude doesn't open the HTML content itself.
9. Tests: request building per model (snapshot of the structure, not content), parse fuzzing,
   pairwise order symmetry, failed-call policy, mock-mode run of S6+S7 on 20 sample prompts with
   cost estimate printed.
10. `scripts/estimate_costs.py`: per-stage call counts and $ from PLAN §7.1 formulas with real token
    stats from WP-02 and prices from `models.yaml`.

## Outputs
- `configs/{gen_config,judge_config}.yaml`, `src/metis/llm/messages.py`, `src/metis/judge/*`,
  `src/metis/labeling/*`, `scripts/s6_generate.py`, `scripts/s7_judge.py`, `scripts/estimate_costs.py`, tests.

## Acceptance checks
- [ ] Mock S6+S7 run completes; rerun = 0 new calls; every outgoing request passes the redaction guard.
- [ ] Owner tried the tool and is OK with it (or changes were made).
- [ ] Cost estimator output for the planned sizes is written to `results/cost_estimate_v1.md`.

## If blocked
- The judge model doesn't support JSON mode → rely on the parser; measure parse-failure rate in WP-09.

## End of session
- `work/reports/WP-06-report.md` (configs, template diffs vs spec A1/A2, estimator output).
  Log DEV-5 text as implemented for owner approval.

## If the context is getting full
Finish the current step, `/handoff` with "next: WP-06 step n", stop.

## Added by D-082, D-083
- Add a Jev adapter: `https://api.metisai.ir/typesafe/v1/systemone` uses `state` and `questions`, not chat messages. Write the A1/A2 judge prompts in that form, and test it with a mock. Set `api_path` for `jev` in `configs/models.yaml` only then.
- Callers must use `redact_messages` when building requests: `complete()` refuses any request with a key pattern.
