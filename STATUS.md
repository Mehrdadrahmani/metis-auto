# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-04 · product session 2 + GitHub (handoff 8)

## Now
- Current WP: **WP-21 Release** (owner: "just go for wp21"; WP-20 report review still open, skipped by owner choice). Test opened once (n = 299)
- Branch **`main`** (TakRoute merged into main via PR #1, merge commit 5e1d134; CI green on main). Remote branch `TakRoute` still exists (deleting it was blocked by the permission system; owner to confirm). Remotes `origin` (owner), `team`
- Router: K = 8 λ 0.5151 (`artifacts/router_v1`). Judge jev pointwise τ = 7. Model: default (Opus 5.5)

## Product (D-125..D-131); tests 332 pass, ruff clean, CI (`.github/workflows/ci.yml`) green
- Gateway: own provider key (D-130), streaming SSE (D-131), 503 names failure kinds, traces `billing` column
- Website: **`web-node/`** (Node.js, Next.js 16, D-129) = the site with RTL fixes, Claude-style chat (collapsible sidebar, edit/copy/retry, code copy, streaming, stop keeps partial), own-key section. `web/` kept unchanged (served by the gateway)
- Run: `TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000`; site: `cd web-node && npm ci && npm run build && npx next start -p 3001`
- Running now: live gateway :8000; Node site :3001 from **`../takrouter-node`** (older copy with the same site files; switch the server to `web-node/` next time); `../takrouter-next` experiment :3000
- Browser tests ($0) in `web-node/scripts/`: check 26/26, chat-ux 36/36, byok-ui 23/23, stream-ui 7/7, typing-dir 14/14; README shots: `readme-shots.mjs`
- Real streaming test (owner "test"): Metis streams (46 chunks, no fallback), usage reported, $0.000065 booked

## GitHub (D-132, D-133)
- Own repo: README with 9 screenshots + diagrams, CI. PR #1 merged
- Team repo `farzanenadem/Metis`: PR #16 merged into `develop` earlier. **PR #17** (`takrouter-full` → develop): takrouter/ = Node site only (`takrouter/web/` removed, Team toggle carried over), own key, streaming, README, `make site`. **PR #18** (`develop-into-main` → main): conflict-free version of #14 (Makefile .PHONY), 72 commits linked to Mehrdadrahmani. Review requested from farzanenadem on both
- Contributor credit on the team repo comes only when develop reaches `main` with a merge commit. Owner sends Farzaneh the exact steps (given in chat 2026-11-04): #18 merge commit → close #14 → test + merge #17 → PR develop→main, Makefile line `.PHONY: help install test lint steps ask route eval dashboard graph doctor phoenix web site team api ui clean build up`
- Team `main` CI already red: Roham's `tests/test_safety_regressions.py` imports missing `agent.utilities.judge` (not ours)

## WP-21 progress
- Step 1 OK (owner). Step 3 done: secret scan of all history = 0 hits. Step 4 (README) largely done in D-132
- Guard for step 2 done: `METIS_ASSERT_NO_NEW_CALLS=1` makes `get_or_call` raise `NewCallRefused` on a cache miss
- ⚠ TEAM repo has chatbot data with live `Bearer` keys in history (f430621, 732eb91, 1bcb798). Owner to tell the team: rotate keys, purge history

## Exact next step
0. WP-21 step 2: fresh clone to scratchpad, copy data/ + cache/, `uv sync`, re-run the stages behind the reported numbers with `METIS_ASSERT_NO_NEW_CALLS=1` (s6/s7 replay from cache, s9, s10, s12, eval_test), compare result hashes; then step 5 (budget close, archive log), step 6 (tag v1.0 on `main`, push)
1. Housekeeping: delete remote `TakRoute` (owner OK), point the :3001 server at `web-node/`, retire `../takrouter-node` and `../takrouter-next`; code fix still open: mock mode must never write the live semantic cache
2. Wait for owner "go": Khayyam + gpt-5.2 + gemini-2.5-flash (~$4.60, max $8.70), see MASTER_LOG Q-items
3. Live product (owner asked; not started): Docker compose (gateway CPU + web-node + Caddy), Iranian VPS recommended; embedder `device: mps` → cpu on Linux; `TAKROUTER_SECRET` env for own-key encryption

## Waiting on the owner
- Send Farzaneh the step list (PR #18 → #17 → develop→main, merge commits); confirm deleting `TakRoute`
- Rotate the Metis key pasted in chat (`METIS_API_KEY_SPARE`) and the Hugging Face token
- Read `results/eval_protocol.md`; check Safari typing in Persian on :3001 (fix verified in Chrome only)

## Blockers / open issues
- Qdrant still has the old train/val payload for 391 moved sessions
- Failed calls book $0, but a provider may bill them. Run one paid process at a time
- Router on chatbot data shows no gain over DeepSeek at low cost: report plainly (P6)
- Site runs only on this Mac; no hosting, no payments. Khayyam licence: academic only (no question text in git or screenshots)
- `runs/gateway/provider.secret` (git-ignored) encrypts users' own keys; losing it = users re-enter keys
- Team worktree `uniroute-fix-lambda` at an old scratchpad (`git worktree list`): remove when PR #15 is settled

## Money
- Spent about $30.06 of cap $60 (product stage $0.0148 so far)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-133 Team PRs #17/#18; Farzaneh merges with merge commits
- D-132 GitHub: README/screenshots/CI, TakRoute → main
- D-131 Streaming; D-130 own provider key; D-129 Node site web-node/
