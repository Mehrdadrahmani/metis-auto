# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-07 · repo public + CV prompt (handoff 13)

## Now
- Current WP: **WP-21 Release** (paused for the pitch deck, owner request). Test opened once (n = 299)
- Branch **`main`**. Remotes `origin` (owner), `team`. Router: K = 8 λ 0.5151 (`artifacts/router_v1`)
- This session (D-140): origin repo made **public** after a history secret scan of origin/main +
  origin/TakRoute (clean); wrote a CV + GitHub-page prompt for the owner (he runs it in another session). $0

## Pitch deck (D-135..D-139): exact next step, start here
- Main deck https://claude.ai/artifact/SpvxYs5pMU9j6cia75kknM (v64, shared "anyone with link"), sources
  `deck/v2/project/` (deck.json + slides/). Backup deck https://claude.ai/artifact/8y4kmGhVaxiMY9iKickkau
  (`deck/v2/backup_deck/`). Owner edits in the browser often: ALWAYS `read` deck.json + target slide first
- Order: pitch (cover problem insight topics learn whynow market competition product savings business team
  roadmap) → tech (techdiv t1idea t1clusters pipeall pipe1 pipe23 pipe45 lambda pipe6 pipe7 t2psi t3rule
  t6curves t7results t8data) → boverview → LLM Router lr1–lr6 (owner's file llm-router-slides-en.html,
  unchanged) → Evaluation e1–e5 (owner's routing-slides.html, UniRoute→TakRouter, our theme) → thanks
- **Owner rules:** English; minimal, one idea; no money ask (D-136); customers = users, students, tech
  companies; tech part only changed when he asks; formulas = LaTeX images; heatmaps soft green→coral
- Check with owner: v64 replaced a page-saved deck.json (possible lost reorder); "UniRoute" word on lr6
- Notes PDFs in ~/Downloads: TakRouter_speaker_notes.pdf (EN), TakRouter_speaker_notes_fa.pdf (FA bullets;
  source scratch notes_fa_b.py, not in git; new slides learn/lambda/lr/e/boverview not in the PDFs yet)
- ~/Downloads/TakRouter_val400.xlsx: first 400 val (runs/s2/split_val400.parquet), 4 answers + judge
- Next: ask owner which slide next; regenerate notes PDFs for new slides if wanted
## Product (D-125..D-131); tests 332 pass, ruff clean, CI green
- Run: `TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000`; site `web-node/` :3001
- **Done (D-139): TakRouter | Team toggle on our website** (2f10245). Run: gateway :8000 (metis-auto, live),
  site `web-node` :3001 (`next dev`, node_modules cloned from ../takrouter-node), team API :8100
  (`cd ../takrouter-merged && .venv/bin/python -m uvicorn ui.src.api:app --port 8100`). Was: Exists in team PR #17 (FETCH_HEAD of
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
- Repo is PUBLIC: never push team branches (they hold 732eb91/1bcb798/f430621 with keys) to origin
- Qdrant has old payload for 391 moved sessions; failed calls may be billed; site only on this Mac
- Router shows no gain over DeepSeek at low cost on chatbot data; Khayyam shows a small gain

## Money
- Spent about $30.06 of cap $60 (this session $0)

## Recent decisions
- D-140 origin repo Mehrdadrahmani/metis-auto made public (owner request; history scan clean)
- D-139 Team router toggle ported to our site (team commit 553a5b2); 5 unverified team models added
- D-138 Pitch restored to v39 (12 slides, Sequoia order); tech part frozen by owner
- D-135 Deck v3: rebuild to full JPMorgan + Antler structure, small slide diagrams, more context
- D-134 Pitch deck v2: English, pitch (Antler + JPMorgan structure) + technical part, light website style
- D-133 Team PRs #17/#18 · D-132 GitHub README/CI · D-131 Streaming
