# WP-xx: <title>

> **Paste prompt (fallback if hooks fail):** "Read STATUS.md, AGENTS.md and work/WP-xx-<name>.md, then
> follow the session protocol: propose, wait for my OK, work, /handoff."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| n | default (Opus 5.5) | ~Nk tokens | … | $… | WP-… | WP-… |

## Context
Why this WP exists, in 3–6 lines. What earlier results it builds on.

## Read (only these)
- `STATUS.md` (auto) · `AGENTS.md` (auto)
- specific files and sections (e.g. `ref/UNIROUTE_PIPELINE.md §4 S8 + §8`), reports of earlier WPs

## Steps
1. … concrete settings (paths, parameters, seeds)
2. …
⏸ **STOP:** wait for the owner when …

## Outputs
- files and their formats

## Acceptance checks
- [ ] …

## If blocked
- what to do; never improvise a paid call or a spec change

## End of session (in addition to `/handoff`)
- report file, decisions to log, which later WP files to update (see `PLAN.md §6`)

## If the context is getting full
Finish the current step, run `/handoff` with "next: WP-xx step n", stop. Never start a new step above
60% context or 90% of the 5-hour usage.
