# WP-20: Report and presentation

> **Paste prompt (fallback):** "Read STATUS.md, AGENTS.md and work/WP-20-report.md; follow the session
> protocol."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 7 | default (Opus 5.5) | ~200k | review drafts; final OK | $0 | WP-19 | WP-21 |

## Context
The course deliverable (format per Q-007: confirm with the owner at the start; default = PDF report
via LaTeX in `report/` + slide outline + dashboard demo). The report must convince a skeptical
reviewer: method, deviations from the spec and why, results with CIs, what didn't work, limitations
(Persian judge, one labeler, 4 models, single aggregator, sample sizes).

## Read (only these)
- `work/reports/WP-08…WP-19-report.md` (summaries), `results/final/*` (tables), `results/eval_protocol.md`,
  `PLAN.md` §1 (decisions, DEV list), `report/NOTES.md` (running notes from every WP), `MASTER_LOG.md §2` (decision register), `ref/proposal/proposal.md` (structure and wording to reuse).

## Steps
1. ⏸ Confirm format and length with the owner; propose the outline (≤ 12 lines).
2. Outline: 1 Problem (brief) · 2 Data (data card, splits, secrets found and redacted) · 3 Method (UniRoute as in the paper + deviations DEV-2…8)
   · 4 Labels (pilot, gate, biases) · 5 Router results (primary verdict first, then ladder, Ψ table,
   holdout demo) · 6 Gateway (rules, cache, failover, checks; replay + live latency) · 7 Economics
   (cost per 1k queries, savings; optional pricing model: fixed vs dynamic subscription from the
   measured cost/query, brief Action 3) · 8 Limitations and next steps · appendix (configs, hashes,
   reproducibility).
3. Figures: draw.io (pastel style of PLANNING-REQUEST §4: blue free/offline, orange paid, green
   online, grey maintenance, yellow totals/gates; dashed grey groups; thin black arrows; no titles
   inside images) for architecture/pipeline; matplotlib for curves (consistent palette). Export
   PNG + PDF. `ref/diagrams/02-offline-build` and `05-uniroute` still show "+ 2 turns" as the
   embedding input: redraw with the current message only (D-045). Screenshots of the local MLflow UI
   (taken by the owner; check that no message text is visible) for the observability section.
4. Draft; then a **separate fresh session** reviews: every claim backed by a number in
   `results/final/`, CI present, deviations honest, no prompt/answer text anywhere.
5. Presentation outline (10–12 slides) + a 3-minute demo script (dashboard + one gateway request).

## Outputs
- `report/` (sources + PDF), `report/slides_outline.md`, figures in `report/figures/`.

## Acceptance checks
- [ ] Primary verdict stated in the first page; every number traceable to `results/final/`.
- [ ] No message/answer text, no secrets; owner OK.

## If blocked
- LaTeX build fails → Markdown → PDF fallback (`pandoc`), owner approves the install.

## End of session
- `work/reports/WP-20-report.md` (what's in the deliverable, open polish items).

## If the context is getting full
Finish the current section, `/handoff` with "next: WP-20 section n", stop.
