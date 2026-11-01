# WP-06 report: generation and judge pipeline

Date 2026-11-01. Cost $0.00 (mock mode). Tests 259 pass.

## Built
`configs/{gen_config,judge_config}.yaml`, `src/metis/llm/{messages,stage}.py`, `src/metis/judge/*`,
`src/metis/labeling/*`, `scripts/{s6_generate,s7_judge,estimate_costs}.py`,
`tests/{test_messages,test_judge}.py`, `results/cost_estimate_v1.md`.

## Acceptance
- [x] Mock S6+S7 on 20 sample prompts completes; rerun = 0 new calls; requests pass the redaction guard.
- [x] Owner replied OK at the tool stop (step 8). The tool's script was checked for syntax only.
- [x] Cost estimate written.

## Judge prompts vs spec A1/A2 (DEV-5, approved, D-085)
Removed `[CONVERSATION CONTEXT]`. Added `[CHATBOT INSTRUCTIONS]` (cut at 6,000 tokens) and
`[RETRIEVED CONTEXT]`, criterion 3 "Chatbot fit", a sentence that the assistant is a chatbot, and a
line not to follow instructions inside the evaluated text. Old criteria 3 to 6 are now 4 to 7.

Jev (D-086): same material as `state`, one score or choice question, same criteria and bands, level
mapped by 1 + 2.25 × level. Jev wording: "caps the answer at level 1". No role line, no reasons.

## Differences from the WP
- No temperature or top_p for any candidate (D-084).
- Instructions and context share one system message. A wrapper might drop a second one.
- Empty turns and assistant turns before the first user turn are removed for all models.
- Failed anchor: the pair is dropped and logged. The spec has no rule.
- A pair missing one order is dropped.
- Generation estimate includes deepseek-v4-pro (pilot only).

## Cost estimate (simulated, no call measured)
Mean input 2,871 tokens. Pilot with both judges $15.28, main generation $7.06, pointwise path
$47.68, pairwise path $62.12. PLAN §6 applies; WP-08 updated (D-087).

## Not proven
Every provider param, the Jev route, the Google route. Checked in WP-09. Test-set selection and the
5% re-judge are not built (WP-12, WP-13).
