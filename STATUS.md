# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-04 · pitch rework session (handoff 11)

## Now
- Current WP: **WP-21 Release** (paused for the pitch deck, owner request). Test opened once (n = 299)
- Branch **`main`**. Remotes `origin` (owner), `team`. Router: K = 8 λ 0.5151 (`artifacts/router_v1`)
- This session: pitch rework (D-135..D-138), $0. WP-21 step 2 not started

## Pitch deck (D-135..D-138): exact next step, start here
- Artifact https://claude.ai/artifact/SpvxYs5pMU9j6cia75kknM, live = **version 42 = git 04398be content**
  (owner chose "version 39": 12-slide pitch, Sequoia order). Sources `deck/v2/project/` (deck.json + slides/)
- Pitch order: cover(purpose) problem(iceberg) insight(public benchmarks) topics(solution) whynow market(circles)
  competition product(+features) savings(proof 1.6¢→0.08¢) business(table) team roadmap(+ask+vision)
- **Owner rules:** never touch part 2 (tech: techdiv…t8data) or backup; English only; minimal slides, one idea,
  ≥30 px; no money ask (D-136: ask = cleaner labeled data + resources); customers = everyday users, students,
  tech companies; compare with GPT Luna and Sonnet using our measured numbers; formulas LaTeX images
- Owner REJECTED: v3 rewrite (story), crowded savings/market, workshop rebuild + enrichment (v40/41). Owner
  liked: iceberg, insight benchmarks, minimal big-number slides, topics picture, pipeline walkthrough
- Rule sources (local, git-ignored): `deck/v2/sources/pitch_tips.md` (JPMorgan, HBS), market_global.md,
  market_iran.md; workshop file ~/Downloads/pitch-deck-workshop.html (Persian; 10 parts, bottom-up market from
  SOM, 2x2 competition, moat, traction w/o customers, demo, "what if model fails" Q&A)
- Project fact sheet highlights (verified by agent): 710,640 msgs / 1,830 chatbots / 80,179 sessions;
  live run n=50 p50 4.84 s vs Sonnet 8.88 s, $0.257 vs $17.408 per 1k; add-a-model ≈ $0.85; spend ≈ $28;
  Khayyam: router 55.0% vs Luna 56.2% (do NOT claim it beats every model); Jina embedder licence CC BY-NC
- Next: ask owner which single slide to improve next; change one slide at a time, show, wait for OK
- Open: team one-liners (owner gave none), Antler tips never pasted, market numbers are assumptions
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
- D-138 Pitch restored to v39 (12 slides, Sequoia order); tech part frozen by owner
- D-135 Deck v3: rebuild to full JPMorgan + Antler structure, small slide diagrams, more context
- D-134 Pitch deck v2: English, pitch (Antler + JPMorgan structure) + technical part, light website style
- D-133 Team PRs #17/#18 · D-132 GitHub README/CI · D-131 Streaming
