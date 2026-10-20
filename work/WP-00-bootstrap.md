# WP-00: Bootstrap the project and the session mechanism

> **How to start this one (the mechanism doesn't exist yet):**
> `mkdir ~/Downloads/RahnemaCollege2026/metis-auto && cd $_ && claude`, then paste:
> "Read ../metis-planning-kit/output/AGENTS.md and ../metis-planning-kit/output/work/WP-00-bootstrap.md
> and follow WP-00. Propose first and wait for my OK."

| Phase | Model | Size | Needs owner | Cost | Depends on | Unblocks |
|---|---|---|---|---|---|---|
| 0 | default (Opus 5.5) | ~80k | approve each install; `gh auth login`; Metis AI key later (WP-04) | $0 | – | all |

## Context
Nothing exists yet. This WP creates `metis-auto/` (next to the kit), puts the plan files in it, and
installs the continuity mechanism designed in `CONTINUITY.md` so that every later session starts with
`/start`. Kit path: `KIT=~/Downloads/RahnemaCollege2026/metis-planning-kit`.

## Read (only these)
- `$KIT/output/AGENTS.md` (rules) · `$KIT/output/CONTINUITY.md` §3, §4, §8 (the design to install)
- `$KIT/data/README.md` (secrets rule) · do **not** open `$KIT/data/sample_data/data.json`

## Steps
1. Propose the steps below in ≤ 8 lines, listing every install (`jq`, `gh`, `uv` if missing).
   ⏸ **STOP:** wait for the owner's OK.
2. Check tools: `git --version`, `python3 --version` (need ≥ 3.11), `jq --version`, `gh --version`,
   `uv --version`. Missing ones: propose `brew install …`. ⏸ **STOP** for approval before installing.
3. `git init -b main`; `git config user.name "Mehrdad Rahmani"`; set `user.email` to the owner's
   email (ask the owner which one to use).
4. Create the folder skeleton from `PLAN.md §10` (empty dirs get `.gitkeep`).
5. Write `.gitignore`: `data/`, `cache/`, `runs/`, `.env`, `*.env`, `.claude/state/`, `.DS_Store`,
   `__pycache__/`, `.venv/`, `*.sqlite`, `.pytest_cache/`.
6. Secret scan: `.githooks/pre-commit` (bash): reject staged files under `data/`, `cache/`, `runs/`;
   reject staged content matching `sk-[A-Za-z0-9_-]{10,}|sk-ant-|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{10,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}`.
   `git config core.hooksPath .githooks`. Test: stage a file containing `sk-TESTTESTTESTTEST` →
   blocked; remove it.
7. Copy planning files: `cp $KIT/output/{PLAN,ROADMAP,MASTER_LOG,PROJECT,CONTINUITY,STATUS,AGENTS,CLAUDE,START_HERE}.md $KIT/output/ROADMAP.html .`;
   `cp -R $KIT/output/work $KIT/output/diagrams .` (if present). Copy inputs into `ref/`:
   `UNIROUTE_PIPELINE.md`, `PLANNING-REQUEST.md`, `proposal/`, `docs/`, `papers/`, `diagrams/`.
8. Copy the sample data **without opening it**: `mkdir -p data/raw && cp $KIT/data/sample_data/data.json data/raw/sample.json`;
   verify `git check-ignore data/raw/sample.json` prints the path.
9. Python env (**uv only**, owner decision D-039): `pyproject.toml` for package `metis`
   (`src/metis/`, Python 3.12, `requires-python >= 3.11`); create the environment named
   **`metis-rahnema`** with `uv venv --python 3.12 --prompt metis-rahnema` (folder `.venv/`, shown as
   `(metis-rahnema)` when activated); dev deps via `uv add --dev pytest ruff`; `uv.lock` is committed.
   Always run things with `uv run …` (e.g. `uv run pytest`). Runtime deps are added by later WPs with
   `uv add`. `uv run pytest` runs (one import test OK).
10. Continuity mechanism (`CONTINUITY.md` §4): write `.claude/settings.json`, `.claude/statusline.sh`,
    `.claude/hooks/{session-start,context-guard,pre-compact,post-compact}.sh`,
    `.claude/skills/start/SKILL.md`, `.claude/skills/handoff/SKILL.md`; `chmod +x`. Show the owner
    the scripts (they are short). ⏸ **STOP:** owner approves before enabling.
11. GitHub: `gh auth status` (if not logged in, ask the owner to run `! gh auth login`);
    `gh repo create metis-auto --private --source . --remote origin`. Enable secret scanning / push
    protection if the plan allows (`gh api` or the web settings; tell the owner if manual).
12. First commit `WP-00: project skeleton, plan, continuity mechanism`; `git push -u origin main`.
13. **Test the mechanism** in a second terminal: `claude` → status line shows
    `ctx …% · 5h …% · WP-01`; ask "what is the next step?" → it answers from STATUS.md without reading
    files. `/compact` once → `.claude/state/precompact-*.md` and `compact-*.md` appear. Close it.
14. Update `STATUS.md` (current WP = WP-01), tick WP-00 in `ROADMAP.md`, log D-entry
    "continuity mechanism installed and tested" in `MASTER_LOG.md`, commit + push.

## Outputs
- `metis-auto/` with skeleton, plan files, `ref/`, ignored `data/raw/sample.json`, Python project,
  `.githooks/`, `.claude/` mechanism; private GitHub repo `metis-auto` with the first commits.

## Acceptance checks
- [ ] Fake key commit is blocked; `data/` is ignored.
- [ ] A new session shows STATUS in context and the status line works.
- [ ] `/handoff` updates STATUS, logs, commits as Mehrdad Rahmani, and pushes.
- [ ] `ref/` has the spec, proposal, docs, paper; no `data.json` anywhere in git (`git ls-files | grep -i json` shows only configs).

## If blocked
- `gh` login fails → continue with local git only, log an open issue, push later.
- A hook misbehaves → disable it in `settings.json`, log it, keep `/start` and `/handoff` (manual
  fallback = paste prompts in WP files).

## End of session
- `work/reports/WP-00-report.md` (≤ 30 lines: what's installed, tool versions, anything manual).
- Next: WP-01.

## If the context is getting full
Unlikely here. If it happens: finish the current step, write STATUS by hand (the skill may not exist
yet), commit, stop.
