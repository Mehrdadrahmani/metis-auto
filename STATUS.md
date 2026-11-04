# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-04 · deck feedback session (handoff 10)

## Now
- Current WP: **WP-21 Release** (paused for the pitch deck, owner request). Test opened once (n = 299)
- Branch **`main`**. Remotes `origin` (owner), `team`. Router: K = 8 λ 0.5151 (`artifacts/router_v1`)
- This session: owner feedback on deck v2, tips saved (D-135), $0. WP-21 step 2 not started

## Pitch deck v3 (D-135): exact next step, start here
- Owner REJECTED deck v2 (artifact https://claude.ai/artifact/SpvxYs5pMU9j6cia75kknM, version 14):
  needs more context per slide; draw.io diagrams too large to follow -> make NEW small slide diagrams
  (one idea each); storytelling weak; misses many Antler + JPMorgan tips
- Tips file (local, git-ignored): `deck/v2/sources/pitch_tips.md`. JPMorgan checklist saved. Antler
  (https://www.antler.co/blog/pre-seed-pitch-deck) NOT saved: site refused automated reads -> ask owner
  to paste it into that file (or into chat). Also HBS NVC template PDF saved there
  (`hbs_nvc_pitch_template.pdf`, 16 slides), text not extracted yet (no PDF tool; download timed out)
- Next session: (1) read pitch_tips.md; (2) write a tip-by-tip checklist + slide-by-slide story outline
  (problem+urgency/why now, product+UVP, market TAM/SAM/SOM, team/why us, traction/demand evidence,
  competition matrix (no blue ocean), revenue model + GTM, milestones/timeline, clear ask + use of
  funds; then technical part); ⏸ owner OK; (3) rebuild slides + new slide-sized diagrams; $0
- Sources in `deck/v2/` (project/, charts/, diagrams/, img/); assets uploaded to the artifact (ids in
  slide files; re-upload from img/ if lost). Style: Inter, gradient #3366ff→#9933ff→#ff3366, white cards
- References: [1] Verasight AI survey June 2026 (n=1,690) · [2] OpenRouter catalog 500+ models, 80+
  providers · [3] Artificial Analysis Apr 30 2026 · [4] results/final/test_report.md · [5]
  results/khayyam · [6] Menlo Ventures Nov 3 2026 ($176.8B, 86% to 2 providers) · [7]
  results/fingerprints.md, holdout_demo.md
- Older decks: Persian `deck/project/` (PHP39n…, 1JAvu3…), English v1 SAJoJk1w… (keep)

## Product (D-125..D-131); tests 332 pass, ruff clean, CI green
- Run: `TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000`; site `web-node/` :3001
- **Open (owner asked): TakRouter | Team toggle on our website.** Exists in team PR #17 (FETCH_HEAD of
  `team/takrouter-full`, commit 553a5b2): port `takrouter/web-node/site/chat.html` toggle (27-line
  diff), `src/metis/team_router/__init__.py`, pipeline.py `req.router == "team"` branch, app.py
  `metadata.router`. Owner questions pending: add 5 team models (unverified)? restart :8000/:3001?

## Exact next steps (after the deck)
1. WP-21 step 2: fresh clone, copy data/ + cache/, rerun stages with `METIS_ASSERT_NO_NEW_CALLS=1`,
   compare result hashes; step 5 budget close; step 6 tag v1.0
2. Housekeeping: delete remote `TakRoute`; point :3001 at `web-node/`; mock mode must not write the
   live semantic cache
3. Paid (needs "go"): Khayyam + gpt-5.2 + gemini-2.5-flash (~$4.60)
4. Live product: Docker compose + VPS

## Waiting on the owner
- Toggle questions above; Farzaneh merge steps; rotate Metis spare key + HF token
- Team repo has live `Bearer` keys in history (f430621, 732eb91, 1bcb798): tell team to rotate/purge

## Blockers / open issues
- Qdrant has old payload for 391 moved sessions; failed calls may be billed; site only on this Mac
- Router shows no gain over DeepSeek at low cost on chatbot data; Khayyam shows a small gain

## Money
- Spent about $30.06 of cap $60 (this session $0)

## Recent decisions
- D-135 Deck v3: rebuild to full JPMorgan + Antler structure, small slide diagrams, more context
- D-134 Pitch deck v2: English, pitch (Antler + JPMorgan structure) + technical part, light website style
- D-133 Team PRs #17/#18 · D-132 GitHub README/CI · D-131 Streaming
