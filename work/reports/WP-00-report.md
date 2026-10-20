# WP-00 report: bootstrap (2026-10-20)

## Installed / created
- Tools (all were present): git 2.54.0, gh 2.100.0, jq 1.6 (Anaconda), uv 0.13.1.
- Python: uv-managed CPython 3.12.15 in `.venv/`, prompt `metis-rahnema`; `[tool.uv]
  python-preference = "only-managed"` so Anaconda's Python is never picked. Dev deps: pytest 9.1.1,
  ruff 0.17.1. `uv run pytest` → 1 passed; `uv run ruff check .` clean.
- Skeleton per PLAN §10; plan files in root; `ref/` = spec, planning request, proposal, docs,
  papers, diagrams. Sample data at `data/raw/sample.json` (never opened, git-ignored).
- `.githooks/pre-commit` secret scan (`core.hooksPath .githooks`).
- `.claude/`: settings.json, statusline.sh, 4 hooks, skills `start` and `handoff`.
- Private GitHub repo `Mehrdadrahmani/metis-auto`, branch `main`, author Mehrdad Rahmani
  <mehrdad.rahmani100@gmail.com>.

## Acceptance checks
- [x] Fake key commit blocked; forced `data/` commit blocked; `data/` ignored.
- [x] New session got STATUS in context; status line ran (wrote `context_pct`); `/compact` wrote
  `precompact-*.md`, `compact-*.md` and `needs-handoff`.
- [ ] `/handoff` end-to-end: first real use at the end of WP-01 (this session committed by hand).
- [x] `ref/` complete; `git ls-files | grep -i json` → only `.claude/settings.json`.

## Deviations from the WP text (D-041)
- Secret regex: `sk-` must start a word (it falsely matched inside the word "risk-management"); bare `sk-ant-` dropped
  (real keys still match `sk-…`); `sk-TESTTESTTESTTEST` from this WP file is allow-listed, so the
  block test used a different fake key. Hook runs with `LC_ALL=C` so PDFs scan cleanly.
- Status line finds the WP via the `Current WP:` line of STATUS.md (not "line 4"); 5-hour usage is
  yellow ≥ 75%, red ≥ 90%; context yellow ≥ 50%, red ≥ 60%.

## Manual / open
- GitHub secret scanning + push protection: not available for this free private repo (HTTP 422) → Q-022.
- ROADMAP.html not updated (static overview).

Next: WP-01.
