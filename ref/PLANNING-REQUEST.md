# Planning request: Metis-Auto v2

**From:** Mehrdad Rahmani (project owner) · **Date:** 2026-10-19 · **Course:** Rahnema College 2026

---

## 0. Your role and your job

**You are a senior AI engineer.** You have built and run several LLM gateways in production, trained
and deployed LLMs and deep-learning models, and designed model-routing systems (learned routers,
cascades, semantic caches, failover). Plan this project the way you would plan it for your own team:
use that experience, be critical, and say clearly when something in the material is naive, risky or
over-engineered.

**Your job is to plan.** Read the material in this folder and **write the implementation plan** for
the project, using your experience to make it realistic and sound. Nothing has been built yet; no
code exists. Your output is the plan and the documents that will drive later work sessions. Someone
else (another AI session, together with me) will do the actual work, phase by phase, in separate
sessions. Where your experience says the current design should change, put that change into the plan
and explain it briefly; don't write a separate critique.

**Don't** write project code, call paid APIs, or edit the input files. Work only in `output/`.

How I want you to work:

1. Read everything listed in §2, in that order.
2. Tell me briefly what you understood (goal, method, constraints) and the few most important
   design changes you are likely to make (§5b), in plain, simple words: I am a student, not a senior
   engineer. Keep the technical depth for the documents.
3. **Ask me your questions** (§6 lists the ones I know are open). Wait for my answers.
4. Propose an outline of the plan (phases and why). Wait for my agreement.
5. Write the deliverables (§7) into `output/`, **one file at a time**, and keep
   `output/PLANNING_PROGRESS.md` up to date (see §5c): your own planning may also run out of
   context, so another planner session must be able to continue from your files alone.

You may challenge anything in the proposal or the docs, including the choice of UniRoute itself,
the phases and the budget, if you explain why. The only fixed points are in §4; if you think one of
them is a mistake, tell me, but don't override it.

---

## 1. The project in brief

Chatbot platforms pay very different prices for different LLMs: a strong model can cost 20–30× a cheap
one for the same message, while most messages are simple. The course asks for **Metis-Auto**, a
"virtual meta-model": middleware that sends each user message to the most suitable model, cheap when
that is enough and strong when it isn't, **without losing quality**, plus a gateway with semantic
caching, escalation (cascade) and failover, and observability.

Our approach is to **measure instead of guess**, using **UniRoute** (Jitkrittum et al., Google, ICLR
2026), as specified in `UNIROUTE_PIPELINE.md`:

- Offline: cluster a large **unlabeled** set of real prompts into K prompt types; have every candidate
  model answer a small **labeled validation set** (~400 prompts); an LLM judge (checked by humans)
  turns each answer into a loss; each model's **fingerprint** Ψ_k(h) is its average loss per cluster.
- Online: embed the message → nearest cluster k* → choose the model with the lowest
  **Ψ_k*(h) + λ · ĉ(h)** (ĉ = cost scaled to 0–1, λ = price weight).
- A new model only needs to answer the same ~400 validation prompts: no retraining.
- Around the router, a gateway: hard rules (menu clicks, images, context limits, provider down),
  semantic cache, failover, cheap quality checks with escalation, traces and a dashboard.

Most traffic is **Persian**. We found no router research measured on Persian, and LLM judges are less
reliable in Persian, so a human check of the judge is required.

---

## 2. What's in this folder (read in this order)

| # | File | What it is |
|---|---|---|
| 1 | `docs/course-brief.pdf` | The course assignment: requirements and evaluation metrics |
| 2 | `UNIROUTE_PIPELINE.md` | **The router specification. Source of truth** (offline build S1–S12, label pilot §P, online rule, maintenance, evaluation, budget formulas, judge prompts) |
| 3 | `proposal/proposal.md` (PDF: `proposal/latex/proposal.pdf`, source `.tex`) | Our current proposal: problem, method, evaluation, a suggested plan and budget. **Treat its plan and budget as a previous suggestion, not as decided** |
| 4 | `docs/uniroute-explained.md` + `diagrams/05-uniroute.png` | Every UniRoute step explained with one diagram |
| 5 | `docs/design.md` + `diagrams/01-overview`, `02-offline-build`, `03-online-path` | System design: the spec inside the gateway, project-level choices |
| 6 | `docs/uniroute-paper-notes.md` | What the paper did (models, data sizes, results) and how our pipeline maps to it |
| 7 | `papers/UniRoute-ICLR-2026.pdf` | The paper itself (50 pages; the notes above summarize it) |
| 8 | `docs/pipeline-explained.md`, `docs/research.md` | Plain-language walkthrough; background research on LLM routing (2026) |
| 9 | `diagrams/04-plan`, `06-api-costs` | The proposal's suggested phases and cost estimate (for reference) |
| 10 | `data/README.md` → `data/sample_data/data.json` | The 100-session sample dataset. **Read `data/README.md` first: the JSON contains live API keys** |

Diagrams are draw.io files (`.drawio`) with `.png` / `.pdf` exports. Links in the docs to
`../metis-v2/archive/` point to an old v1 design outside this folder; ignore them.

---

## 3. Facts

**Sample dataset** (`data/sample_data/data.json`, ~7.5 MB): 100 anonymized sessions, 907 messages,
4 equal usage categories (unnamed on purpose), collected January–September 2026, mostly Persian.
Each session has an id, creation time, user/bot turn counts and the ordered transcript; each message
has role, content, timestamp; bot messages have the model and provider (18 models, 7 providers) and,
when used, retrieved context. 14 messages have attachments, 29 have structured input widgets,
71 have retrieval context. From our earlier analysis: 442 bot turns, **377 "usable"** (answered by a
real LLM; the rest are a `default` workflow step, `dalle` image turns or have no model), 68 distinct
system prompts, production used one fixed model per chatbot, ~1,640 input tokens per usable turn
(~866 of them system prompt), ~174 output tokens, median user message 31 characters. The workflow
configs inside the JSON contain **live API keys**.

**Full dataset:** promised by the course team, **date and size unknown**. The spec needs a large
unlabeled train split (ideally ≥ 5,000 prompts) plus ~700 labeled prompts (validation + test), which
the sample cannot provide.

**Cost assumptions used so far** (list prices per 1M tokens in/out; to be confirmed):
gemini-2.5-flash-lite 0.10/0.40 · deepseek-v4-flash 0.14/0.28 · gpt-4o-mini 0.15/0.60 ·
gemini-2.5-flash 0.30/2.50 · claude-sonnet-4-6 3.00/15.00 · judge ≈ $0.002–0.006 per call.
The proposal estimated ~$17–50 total API cost ($60 planned); **not approved yet**.

**Environment:** macOS, Python 3, LaTeX (latexmk), draw.io CLI. No git repository yet. All work is
done with **Claude Code on a Claude Pro plan** (one person, one subscription). Each session has a
**1M-token context window**; see §5c.

**Lessons from an earlier design (v1) that was rejected:** it clustered and computed fingerprints on
the same small labeled set (overfits); it tuned and reported results on the same data; it graded
answers against production's answers, which came from 18 different models (unstable reference); it
ignored the "unseen new model" test, which is the paper's main claim.

---

## 4. Fixed points (decided by me; don't change without asking)

1. **`UNIROUTE_PIPELINE.md` is the router spec and the source of truth.** Deviations must be marked
   and justified; I decide on them.
2. **No paid API call before the full dataset arrives.** Work that is free (code, tests with mocks,
   dry runs on the sample, synthetic tests) can happen before.
3. **Agree before code:** each work session proposes its plan and waits for my agreement.
4. **Ask before any paid API call,** with a cost estimate; enforce a hard budget cap in code.
5. **Secrets:** never print, commit or send `data.json` or generated answers; redact keys before any
   text leaves the machine; inspect the data by structure only.
6. **Golden rules of the spec:** the test set is never used for any choice; the train split stays
   unlabeled; fingerprints come only from validation; every LLM and judge call is cached; seeds recorded.
7. **The gateway parts the brief requires** (semantic cache, cascade/escalation, failover,
   observability) are part of the project, around the router.
8. **Plain, simple explanations** for me. Diagrams in **draw.io**, pastel style: blue `#dae8fc/#6c8ebf`
   free/offline, orange `#ffe6cc/#d79b00` paid, green `#d5e8d4/#82b366` online, grey `#f5f5f5/#666666`
   maintenance, yellow `#fff2cc/#d6b656` totals/gates; dashed grey group outlines; thin black arrows;
   no title inside images.
9. If git is used, commits are authored by **Mehrdad Rahmani**.

Everything else in the proposal and docs (candidate models, anchor, judge, splits sizes, phases,
budget, gateway details) is a **proposal you may improve**.

---

## 5. Things the plan must handle well

- **Limited sessions and context windows.** The work will NOT fit in one session, and every session
  has a limited context window. This is a core constraint of the plan; see §5c.
- **Results change later steps.** Data size changes split sizes, K range and budget; the pilot's
  label method changes judging cost; whether UniRoute beats simple baselines changes what the gateway
  ships. The plan must say how each phase's results feed into later phases, and how the later
  instructions get updated.
- **Human work:** someone must label ~100 judge-calibration items (and, for the semantic cache,
  ~200 message pairs "same answer OK?"). Who and when is open.
- **Waiting time:** the full dataset's arrival is unknown; use the waiting time well.
- **Known risks:** only 5 candidates makes the "new model" test weak; if most messages are easy,
  every model passes and routing is trivial; the judge may be unreliable in Persian; the cache needs
  labeled pairs to set its threshold; the hard rules need to know which data fields mark widgets,
  attachments and image requests.

---

## 5b. Use your experience while planning

Your plan should take a position on these questions (answer the ones that matter; add your own).
The answers belong in the plan's design-decisions section and shape the phases:

**Method**
- Is UniRoute (K-means fingerprints) the right core for a **fixed pool of 5 models** and a few
  hundred labels? The paper itself says it is only comparable to simpler routers in that setting.
  Would you start with a simpler router (ZeroRouter, K-NN, a small classifier on prompt features, a
  cascade with a confidence check) and add UniRoute later, or keep UniRoute as the core for its
  "add a model without retraining" property? What is the minimum that gives a credible result?
- Is ~400 validation prompts with K ≤ 8 clusters enough statistical power to tell 5 models apart
  per cluster? What sample sizes, confidence intervals and significance tests would you insist on?
- Label quality: one LLM judge in Persian, one answer per (prompt, model), pointwise vs pairwise vs
  an anchor. How would you control judge bias (length, position, self-preference) and noise? Is the
  pilot design (§P of the spec) sound?
- Is "semantic similarity to production's answer" (the course's metric) meaningful when production
  used 18 different models? How should it sit next to judge-based quality?

**Engineering**
- Gateway architecture you would use (framework, OpenAI-compatible API, async calls, streaming,
  timeouts, retries, circuit breakers, rate limits, provider fallbacks) and what to reuse (e.g.
  LiteLLM-style libraries) vs build.
- Latency budget for the router (embedding on CPU vs GPU, model size, batching) and for the cache.
- Semantic cache in a multi-tenant chatbot platform: namespacing, poisoning, staleness, personal
  data, follow-up messages, how to set and monitor the threshold safely.
- Prompt caching at the providers (system prompts are ~866 tokens): does switching models per message
  waste it, and should the router account for it?
- Observability: traces, metrics, dashboards, cost accounting, and how to detect drift and silent
  quality regressions after launch (online sampling, shadow evaluation).
- Reproducibility and safety of the offline pipeline: call caching, versioning of models, prompts,
  judge config and data splits; secrets handling (the dataset contains live keys).

**Project**
- What can be built and validated before the full dataset arrives, so the paid work later is fast
  and safe?
- Where are the biggest risks of wasted money or wasted weeks, and how do you de-risk them early?
- What would make the final evaluation convincing to a skeptical reviewer?

---

## 5c. Continuing work across sessions (decide this first)

**The situation.** The project will take many Claude Code sessions. I use **Claude Code on a Claude
Pro plan; each session has a 1M-token context window**. A session can end before its work is done,
long sessions lose detail (Claude Code auto-compacts near the limit and details can be lost), and a
new session starts with **no memory** except what is in the project folder. I can manage opening and
closing sessions myself. **What I need from you is the best way to hand work over from one session
to the next, so a new session continues exactly where the last one stopped, without me re-explaining.**

**Your task: compare two approaches and choose (or combine) with reasons.**

- **A. A continuity mechanism.** Design one, or find an existing solution, that lets any new session
  pick up the work automatically: it knows the current state, the decisions made, what was just done,
  and the next step. Things worth evaluating (check what exists and works today; don't assume):
  - Claude Code built-ins: `CLAUDE.md` project memory and `@` imports; `claude --continue` /
    `--resume`; auto-memory; custom slash commands / skills (e.g. a "start" and a "handoff" command);
    **hooks** (e.g. SessionStart to load the status automatically, PreCompact or Stop/SessionEnd to
    write a handoff before details are lost); subagents for narrow tasks; plan mode; to-do lists.
  - Project conventions: a short status file read first, a decision register, a dated log, git
    commits with meaningful messages as history, checkpoints and caches for long-running jobs.
  - External tools: issue trackers (GitHub Issues; a Linear connector is available to me),
    spec-driven or task-management workflows for coding agents, memory servers (MCP). Say whether
    they are worth their setup cost for a one-person course project.
- **B. Pre-defined sessions.** A session-by-session roadmap where each session has its own ready-made
  prompt and content (what to read, what to do, what to produce), revised as results come in.

**Judge them on:** reliability (does the next session really know where we are?), how little I have to
do by hand, setup effort, robustness to sessions ending early or being compacted, how well it handles
plans that change after each result, and fit with Claude Code on Pro. If you recommend A, **design it
concretely** (files, commands or skills, hooks, the exact start-of-session and end-of-session steps)
and make its setup one of the first work packages. If you recommend B, design the session list and the
prompts. A hybrid (e.g. a mechanism plus a phase roadmap) is fine if you explain why.

**Whatever you choose, these must hold:**

1. **Right-sized work.** Each unit of work fits comfortably in one session with a large margin below
   1M tokens (give rough token estimates); say what to do if it turns out bigger.
2. **Minimal reading.** A new session reads only what it needs: specific files and sections, not
   "everything". Large inputs: `UNIROUTE_PIPELINE.md` (~30 KB), the UniRoute paper (50 pages), the
   proposal PDF, and `data/sample_data/data.json` (~7.5 MB, never read directly).
3. **State lives in files, not in the conversation.** A compact status that every session reads first
   (with a size limit), a decision register, a dated log whose old entries get summarized or archived.
4. **Clean handoffs.** A session that ends or stops early leaves a short handoff: done, not done, exact
   next step, open issues, files changed. Stop starting new work when `/context` shows the window
   getting full, and write the handoff before auto-compaction.
5. **Resumable long jobs.** Long-running steps (e.g. generating thousands of answers) resume from
   checkpoints and caches, so an interrupted session costs nothing to restart.
6. **Plans that adapt.** Results of each step update what the next steps do, and that update is
   recorded where the next session will see it.
7. **Lean documents.** Short "read every session" files are kept separate from reference documents;
   facts live in one place.
8. **Model choice.** Say which work needs the strongest model (planning, design decisions, tricky
   math) and which can use a lighter one (routine code, tests, reports).

**Your own planning session has the same limit.** Write deliverables to `output/` one at a time and keep
`output/PLANNING_PROGRESS.md` current: which deliverables are done, which are next, decisions agreed
with me, open questions. If your context gets full, stop, update that file, and tell me; a new planner
session will continue from it.

---

## 6. Open questions I know about

| ID | Question |
|---|---|
| Q-001 | When does the full dataset arrive, and how large is it? |
| Q-002 | API access: OpenRouter, direct provider keys, AvalAI, or Google Cloud? |
| Q-003 | Budget approval (the proposal says ~$60; final number after the full data) |
| Q-004 | Who does the human labeling, and when? |
| Q-005 | Keep 5 candidate models, or add 1–3? |
| Q-006 | What is the `default` model in the data (ask the course team)? |
| Q-007 | Deadline and deliverable format? |
| Q-008 | Should each turn keep its own chatbot's system prompt when generating answers (the spec says one shared gen_config)? |
| Q-009 | Use git for the project? |

Add your own questions.

---

## 7. What I need from you (write into `output/`)

1. **`PLAN.md`**: the implementation plan:
   - a short **design-decisions section** first: what you keep from the current material, what you
     change or cut and why (your answers to §5b), each marked "must", "should" or "nice to have";
   - phases in order, each with goal, inputs, tasks, outputs, acceptance checks, estimated time,
     API cost, dependencies, and the points where I must decide or approve;
   - what can run before the full dataset arrives and what must wait;
   - how each phase's results change later phases (a table), and how the instructions get updated;
   - a budget estimate with the formulas and assumptions (use spec §9);
   - risks and mitigations; a target repository layout.
2. **`CONTINUITY.md`**: your answer to §5c: the approaches you compared (including existing tools
   you checked), your choice and why, and the concrete design: files, commands or skills, hooks, and the
   exact start-of-session and end-of-session steps. Include setup instructions if anything must be
   installed or configured (I approve before anything is installed).
3. **`ROADMAP.md`**: the ordered list of work packages: goal, phase, what to read (files and sections),
   what it produces, done-criterion, rough token size, whether it needs me (approval, labels, data),
   whether it costs money, which packages it unblocks; what can run before the full dataset, what
   waits, what can run in parallel. One glance must tell me "where are we, what's next". With
   approach A this can be lighter (the mechanism tracks progress); with B it is the session list.
4. **Work instructions** in the form your §5c choice needs: either a ready-to-paste, self-contained
   prompt per session / work package (approach B), or per-phase instructions that the continuity
   mechanism loads (approach A). Either way they must contain: context, what to read, numbered
   steps with concrete settings, stop points where the session must wait for me, outputs and
   formats, acceptance checks, what to do if blocked, an end-of-session checklist (update the log,
   write a report, revise later instructions if needed), and what to do if the context is getting
   full (write the handoff and stop).
5. **`AGENTS.md`** and **`CLAUDE.md`**: rules and session protocol for any agent doing the work
   (`CLAUDE.md` can import `AGENTS.md` with `@AGENTS.md`).
6. **`MASTER_LOG.md`**: the running record, pre-filled: current status, decision register (with what
   is fixed in §4 and what you decided with me), open questions, budget ledger, dated log.
7. **`PROJECT.md`**: one file that explains the whole project to a newcomer (idea, method, gateway,
   evaluation, plan, file map, glossary) and tells a new session what to read first (including the
   proposal).
8. Optional: a draw.io diagram of your plan or roadmap (`output/diagrams/`, style as in §4).
9. **`PLANNING_PROGRESS.md`**: your own progress while planning (§5c), so planning can continue in
   another session.

Keep everything in plain language, with tables where they help.

---

## 8. Start prompt (paste into a new session opened in this folder)

```
You are a senior AI engineer who has built LLM gateways, trained and deployed LLMs and deep-learning
models, and designed model-routing systems. Read PLANNING-REQUEST.md in this folder and follow it
exactly. Start with §0 and the reading order in §2 (read data/README.md before touching anything in
data/, and never print data/sample_data/data.json). Don't write code or call paid APIs. When you've
read everything, tell me briefly in plain words what you understood and the main design changes
you expect to make, then ask me your questions. After my answers, propose an outline of the plan,
and once I agree, write the plan and the other deliverables into output/. The work spans many
Claude Code sessions (Pro plan, 1M-token context per session, no memory between sessions): first
decide in CONTINUITY.md how work carries over to a new session (§5c): design or find a continuity
mechanism, or pre-define the sessions, or combine them, with reasons. Your own context is limited
too: write files one at a time and keep output/PLANNING_PROGRESS.md current so another session can
continue.
```
