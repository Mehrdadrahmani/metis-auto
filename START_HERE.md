# START HERE: how to begin the project in a new session

You don't need to know what is installed. The first session checks everything and asks you before
installing anything.

## 1. Open a new terminal and run

```
mkdir -p ~/Downloads/RahnemaCollege2026/metis-auto
cd ~/Downloads/RahnemaCollege2026/metis-auto
claude
```

## 2. Paste this prompt

```
Read ../metis-planning-kit/output/AGENTS.md and ../metis-planning-kit/output/work/WP-00-bootstrap.md
and follow WP-00 from step 1. First check which tools are installed (git, Python 3.11+, jq, gh, uv)
and tell me in simple words what is missing; ask me before installing anything. Use uv with a
virtual environment named metis-rahnema. Propose your steps first and wait for my OK.
```

## 3. What the session will do (WP-00, about 30 minutes)

1. **Check tools** and tell you what's missing. For anything missing it proposes `brew install …` and waits
   for your OK. (On 2026-10-20 all of them were found installed: git, Python 3.12, jq, gh logged in as
   Mehrdadrahmani, uv.)
2. Create the folders, git on your laptop, and the secret check.
3. Copy the plan files and the reference documents into the project, and the data (without opening it).
4. Create the uv environment **metis-rahnema** with Python 3.12.
5. ⏸ **Show you the session scripts and `/start`, `/handoff` commands** → you say OK.
6. ⏸ **Ask before creating the private GitHub repo** `metis-auto`, and which email to put on commits
   (`alimhd.m@gmail.com` or GitHub's private noreply address).
7. First commit and push to GitHub.
8. Ask you to open one more terminal to test that the new session setup works (5 minutes).

## 4. Things to have ready

- Your GitHub login (if `gh` is not logged in, the session will ask you to run `! gh auth login`).
- Not needed yet: the Metis AI key (asked later, in WP-04).

## 5. Every session after that

```
cd ~/Downloads/RahnemaCollege2026/metis-auto
claude
```
then type **`/start`**. Claude tells you where we are and what it will do, and waits for your OK.
At the end, **`/handoff`** saves everything (status, log, git, GitHub).

## 6. Where to look

- Visual roadmap: `metis-auto/ROADMAP.html` (open in a browser)
- Where we are: `metis-auto/STATUS.md`
- The whole plan: `metis-auto/PLAN.md`

## Open questions you can answer any time (Claude will also ask when needed)

- Do you use a VPN with Claude Code? (Metis AI wasn't reachable from here.)
- Choosing K: our way (halves of validation, $0) or exactly the paper (~$14 more)?
- Allow one ~$1 real test on 20 sample messages before the full data arrives?
- Backup of the data and saved answers: where (external drive, iCloud, Google Drive)?
- Exact deadline date, and what the `default` model in the data means (ask the course team).
