# Prompt: merge the team repo and PR #16 into one live product

Paste the prompt below into Claude Code, opened at the root of a fresh clone of
`farzanenadem/Metis`, on a new branch from `develop`.

---

You are merging two working LLM routers into **one live product**. Nothing may be demo or mock in
the result: real model answers, real routing by both routers.

**Inputs**
1. `develop` of this repo is the **team router** by Farzaneh Nadem. It lives in `agent/` and is a
   LangGraph graph (`agent/graphs/metis_graph.py`). Its LLM router is `llm_choice` with
   deepseek-v4-flash, a feature card, Qdrant evidence (`metis_turns`) and a cluster bank. Its API
   is `ui/src/api.py`.
2. **PR #16** (branch `takrouter-full`) is **TakRouter** by Mehrdad Rahmani, under `takrouter/`.
   - It is the UniRoute router: jina clusters, error fingerprints Ψ, and the rule `argmin Ψ + λ·ĉ`.
     Its artifact is `takrouter/artifacts/router_v1`.
   - Its gateway, `takrouter/src/metis/gateway/`, is OpenAI-compatible and has accounts, credit,
     a budget guard, a semantic cache, failover and traces.
   - Its website is `takrouter/web/` (Persian/English).
   - Read `takrouter/README.md`, `takrouter/AGENTS.md` §4–§6 and `TAKROUTER_MERGE_PROMPT.md` first.
3. PR #16 already contains a working **preview** of this merge (commit `3fbc212`):
   - `POST /route` in `ui/src/api.py`;
   - the adapter `takrouter/src/metis/team_router/`;
   - `metadata.router` in the gateway;
   - the chat toggle.

   It runs in replay/mock mode. Build on it, make it live, and add the fixes listed below.

**Step 0: git (do first, then stop and show me)**
- Merge PR #16 into `develop` with **"Create a merge commit"**: `git merge --no-ff takrouter-full`.
  Never squash or rebase, so Mehrdad's commits keep his authorship.
- Then create the working branch `live-merge`. No force-push. Never rewrite history.

**Target design**
- **One website**, TakRouter's `takrouter/web/`. Every chat-like page gets a toggle
  **Router: TakRouter | Team (LLM router)**: /chat, /compare (both routers' picks side by side,
  both answers), the decision trace (each router's reason), and /dashboard (cost, latency and model
  mix per router).
- **Two processes:**
  - TakRouter gateway on port 8000.
  - Team router API on port 8100, run with `uv run uvicorn ui.src.api:app --port 8100`.
  - Qdrant on 6333 (docker-compose service).
  - Each part keeps its own uv project and lock file. Do not merge the lock files.
- **Team router = decide only.** Add `POST /route {message}` to `ui/src/api.py`.
  - It runs the graph steps receive → feature_card → hard_filter → evidence → llm_route, then stops.
  - It returns `{model, backup, reason, source, confidence, router_cost_usd, mode, events, ms}`.
  - **TakRouter's gateway makes every answer call.** That gives one cache, one budget guard,
    redaction, failover, credit and traces.
  - Adapter: `takrouter/src/metis/team_router/__init__.py`, `team_route(text)` over HTTP
    (`TEAM_ROUTER_URL`, 5 s timeout). If the team service fails, fall back to TakRouter and say so
    in the trace.
  - Request field: `metadata.router = "takrouter" | "team"`.
- **Live mode for both:**
  - The team graph runs with `mode: live`, so its LLM router (deepseek-v4-flash) really decides,
    not the replay rule.
  - Its router call must go through TakRouter's money path: redaction, outgoing key guard, budget
    guard, ledger. Easiest is to route the team's OpenAI client to TakRouter's
    `metis.llm.client`, or to count its cost (`router_cost_usd`) in TakRouter's ledger.
  - That cost goes into the user's credit and the trace.
  - The TakRouter gateway runs with `TAKROUTER_PROVIDER=live` (stage `product`).
- **Evidence for the team router:** build its Qdrant collection `metis_turns` and cluster bank from
  the **train split only**, using `metis-auto cluster` / `agent/utilities/offline/`. Never use
  validation or test data.
- **Models:**
  - Restrict the team router's `allowed_models` to models TakRouter's gateway can call.
  - Add the team catalog models that are missing (gpt-4o-mini, gpt-4.1-mini, gpt-4.1,
    gemini-2.5-flash, claude-sonnet-4-6) to `takrouter/configs/models.yaml`, with Metis
    `api_path`/`api_name` and prices.
  - Send one test call per new model first, and only after my "go".

**Fixes from the preview (must include)**
1. The team API imports FastAPI but `pyproject.toml` does not list it: `uv add fastapi uvicorn httpx`.
2. Gateway circuit breakers exist only for the router's models: create one for every model in
   `models.yaml` (`pipeline.py`, `self.breakers`).
3. Gateway `psi` lookup for models outside the TakRouter artifact: give them a neutral value
   instead of raising an error.
4. **Demo answers must never enter the live cache.** Mock/demo mode must use its own cache and
   trace files (e.g. `runs/demo/`).
   - Mehrdad's live cache had 636 fake rows (`answer LIKE 'پاسخ نمایشی%'`, space `default|…`).
     Make the code refuse to store mock answers in a live cache, and add a test.
5. Tests must never write to the real `runs/gateway/users.sqlite`, `cache.sqlite` or
   `traces.sqlite`. Use `:memory:`.

**Rules (strict)**
- **Money:**
  - No paid call without my explicit "go" and an estimate (`takrouter/scripts/estimate_costs.py`).
  - Hard cap is `takrouter/configs/budget.yaml`; never raise it yourself.
  - One paid process at a time.
  - Cheapest model first; stop on failures > 5% or cost per call > 2× the estimate.
- **Secrets:**
  - Keys come only from `.env` via `os.environ`. Never print them.
  - Never commit `.env`, `data/`, `cache/`, `runs/`, `models/` or any chatbot text.
  - Scan every diff for `sk-`, `Bearer `, `AIza`, `ghp_`, `hf_`, `eyJ…`, `key=`, `token=`.
  - This repo's history has live Bearer keys in `evaluation/data/sample_golden_set.jsonl` and
    `data/goldenset/*` (branch add-evaluation-test). Remove those files, tell the team to rotate
    the keys, and never copy them.
- **Evaluation integrity:** do not change `takrouter/results/`, `takrouter/report/` or the
  TakRouter artifact. Its test set is sealed. Any router-vs-router comparison is a new experiment
  on validation data, reported with n and a confidence interval.
- Keep the team's Streamlit/Next.js pages but mark them "legacy". Delete nothing without asking.
- **Work in steps:** propose the plan → wait for my OK → after each step run both test suites
  (`uv run pytest` at the root, and in `takrouter/`) → stop at every paid step.

**Done when**
- Both routers answer **live** from the one website, with the toggle on chat, compare, trace and
  dashboard.
- Spend goes through one ledger.
- Tests are green, the secret scan is clean, and the README explains how to run and credits both
  authors.
