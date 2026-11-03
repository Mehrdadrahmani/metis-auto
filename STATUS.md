# STATUS (read first; ≤ 60 lines)
Updated: 2026-11-03 · WP-21 started (handoff 6)

## Now
- Current WP: **WP-21 Release** (owner: "just go for wp21"; WP-20 report review still open, skipped by owner choice). Test opened once (n = 299)
- Team PR #16 open (`farzanenadem/Metis`, branch `takrouter-full` → `develop`): whole project under `takrouter/` with history + `TAKROUTER_MERGE_PROMPT.md` (Farzaneh merges with a merge commit, then runs the prompt: one site, Router TakRouter | Team toggle)
- Branch `TakRoute`, remotes `origin` (owner) and `team`. Team PR #15 open (`farzanenadem/Metis`, branch `uniroute-fix-lambda` into `develop`)
- Router: K = 8 λ 0.5151 (`artifacts/router_v1`). Judge jev pointwise τ = 7. Model: default (Opus 5.5)

## Product built this session (D-125, D-126, D-127)
- Site, 12 pages, Persian/English (`web/*.html`, shared `web/assets/site.{css,js}`): / home, /chat, /compare, /khayyam, /learn, /docs, /dashboard, /pricing, /how, /login, /account, /models (admin), /results
- Run live: `TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000` (real jina embedder, LiveProvider stage `product` $3)
- Accounts `metis.gateway.auth` (runs/gateway/users.sqlite): first sign-up = admin (the owner signed up); user credit $0.50 default; API keys `tk-…`
- Optional decision trace (`metadata.trace`, per-user pref). Per-request λ (`metadata.lambda`). 402 on credit/budget
- Add a model (`metis.onboard`, /models): register → test call → estimate → admin approves → 798 val + jev → Psi column → activate (`artifacts/router_live`). Mock run on 10 prompts OK; fingerprints of the 4 shipped models reproduce exactly. No live add yet
- Khayyam demo (`metis.khayyam`, `scripts/khayyam_build.py`, $0 from stored answers): own artifact `artifacts/router_khayyam` (K = 7, λ 21), own gateway (replay of stored answers) and traces. Gateway replay: 55.5% acc, 0 failed; Luna outage 54.3%, 0 failed
- Tests: 318 pass

## Done this session (D-128)
- Khayyam sub-menu (overview · Khayyam chat · subjects) and page **/khayyam/chat** (`web/khayyam_chat.html`): type a question + 4 options → `POST /v1/khayyam/ask` (`kh_live()` in `src/metis/gateway/app.py`) → Khayyam router → live model (stage `product`) or mock. Sign-in needed; spend counts against user credit. "Example question" button fills from a stored test question ($0)
- Tests: 318 pass (new `test_khayyam_chat_asks_own_question`, mock). NOT yet tried live or in a browser

## WP-21 progress
- Step 1 OK (owner). Step 3 done: secret scan of all history of TakRoute, main, origin/* = 0 hits (one `password={tail}` is a fake test value); results/ and report/ hold no message text
- Guard for step 2 done: `METIS_ASSERT_NO_NEW_CALLS=1` makes `get_or_call` (`src/metis/llm/callcache.py`) raise `NewCallRefused` on a cache miss; test `test_replay_mode_refuses_new_calls`. Tests 319 pass
- ⚠ TEAM repo `farzanenadem/Metis` (not ours) has chatbot data with live `Bearer` keys in history: commits f430621 (develop, `evaluation/data/sample_golden_set.jsonl`), 732eb91 + 1bcb798 (branch add-evaluation-test, `data/goldenset/*`). Owner to tell the team: rotate those keys, purge history

## Merge preview (this session)
- Local-only repo `../takrouter-merged` (no remote, commit 3fbc212): team router `POST /route` (port 8100, replay rule) + TakRouter gateway `metadata.router` toggle (port 8001, mock). Tested: TakRouter→deepseek, Team→gemini-2.5-flash
- Live merge prompt for Farzaneh: `work/MERGE_LIVE_PROMPT.md` (not yet pushed to PR #16)
- ⚠ Real `runs/gateway/cache.sqlite` holds 636 fake demo answers (space `default|…`, `answer LIKE 'پاسخ نمایشی%'`), from older mock runs: owner to approve deleting them; then make mock mode use its own cache

## Exact next step
0. WP-21 step 2: fresh clone to scratchpad, copy data/ + cache/, `uv sync`, re-run the stages that make the reported numbers with `METIS_ASSERT_NO_NEW_CALLS=1` (s6/s7 replay from cache, s9, s10, s12, eval_test) and compare result hashes; then steps 4 (README), 5 (budget close, archive log), 6 (tag v1.0, push). Khayyam-chat upgrade plan (merge into chat.html, optional options) waits after that
1. Owner check: run live (`TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app --port 8000`), open /khayyam/chat, ask 1–2 questions (fraction of a cent each); check the sub-menu in fa/en and on a phone width
2. Wait for owner "go": add **gpt-5.2 + gemini-2.5-flash** to Khayyam (1,500 answers each; ~$4.60 expected, $8.70 max; one test call each first). Needs entries in `configs/models.yaml` + `configs/gen_config.yaml` (gpt-5.2: rename max_tokens→max_completion_tokens, reasoning_effort none), stage `khayyam` approved +$9, then `scripts/khayyam_run.py`-style answering and `scripts/khayyam_build.py --models gpt-5.2,gemini-2.5-flash`
3. Then WP-20 / WP-21 as planned

## Owner discussions (not decided)
- Validation 2,000 (+1,200 prompts) with Sonnet replaced: proposed gpt-5.2 (~$27 total) or gpt-4.1; Luna may beat gemini-2.5-flash. A new sealed test would be needed for a clean score
- More clusters: val area falls after K = 4 (`results/select_k.md`); more labels first

## Waiting on the owner
- Read `results/eval_protocol.md` (frozen by consent D-119)
- Rotate the Metis key pasted in chat (`METIS_API_KEY_SPARE`) and the Hugging Face token
- Check in a browser: /account and /models in English (headless screenshots timed out there; Persian versions fine)
- Team PR #15 review/merge by Farzaneh (credits the owner as contributor once on `main`)

## Blockers / open issues
- `graphify update .` refuses to overwrite (saved semantic nodes missing): graph is behind the code
- Qdrant still has the old train/val payload for 391 moved sessions
- Failed calls book $0, but a provider may bill them. Run one paid process at a time
- Router on chatbot data shows no gain over DeepSeek at low cost: report plainly (P6)
- Site runs only on this Mac; no hosting, no payments. Khayyam licence: academic only (no question text in git)
- Team worktree at the scratchpad (`git worktree list`): remove with `git worktree remove` when PR #15 is merged

## Money
- Spent about $30.06 of cap $60 (product $0.0134 this session; add_model $0)

## Recent decisions (full list in MASTER_LOG.md §2)
- D-127 Khayyam demo: separate router, gateway and page
- D-126 Website with accounts, trace, add-a-model
- D-125 Live chat app, stage `product` $3
- D-124 Khayyam: area gain over ZeroRouter
- D-123 Name TakRouter
