# Data selection criteria

Which messages the project uses, which it leaves out, and why. This feeds the data section of the
final report. Aggregates only, no message text. Rules live in `src/metis/data/prompts.py` and
`configs/pipeline.yaml`; decisions in `MASTER_LOG.md §2`.

Status: criteria set 2026-10-31. The counts per rule on the full dataset are added in WP-08 (S1).

## 1. Dataset

Measured on the full dataset (`data/raw/metis/`, 2026-03-01 to 2026-10-11):

| Item | Count |
|---|---|
| Messages | 710,640 |
| User messages (the candidates for a prompt) | 355,965 |
| Sessions | 80,179 |
| Bots with sessions | 675 of 1,830 |
| Users with sessions | 133 of 448 |

## 2. What counts as a prompt

A prompt is **one user message that has a bot reply right after it**. Only the current message is
embedded (D-045). Earlier turns, bot instructions and RAG context are used for generation, and
instructions and RAG context for judging (D-019, D-031, D-046). They do not enter clustering.

## 3. Exclusion rules

| Rule | Excluded when | Val / test | Train | Reason |
|---|---|---|---|---|
| No reply | No bot message right after the user message | Yes | Yes | No complete turn to study |
| `reply_workflow` | Bot provider is `workflow` or model is `default` | Yes | Yes | See section 4 (D-057) |
| `reply_image` | The reply is an image generation | Yes | Yes | Text judging does not apply |
| `reply_no_model` | The reply has no model recorded | Yes | No | No production reference; user text is still valid for clusters |
| `widget_click` | The message equals a button choice of the previous bot message | Yes | Yes | A click, not a request; no meaning alone |
| `has_image` | The user attached an image | Yes | No | Not every candidate reads images; user text is still valid for clusters |
| `huge_prompt` | Bot instructions over 20,000 characters | Yes | No | Cost and context limits (D-019) |
| `too_short` | Under 2 characters after normalization | Yes | Yes | No content |
| `junk` | No letter or digit at all | Yes | Yes | No content |
| `dup_exact` | Exact repeat of another eligible prompt | Yes | Yes (`dup_exact_train`) | Repeats would count one prompt several times |

## 4. Why `workflow` is excluded (D-057)

Owner decision, 2026-10-31. Applies to train, val and test.

`workflow` is 96,669 user messages: 27.2 % of all, 74.9 % since 2026-09-01.

1. **It is not a routing decision.** The router picks one model for one message. A workflow runs its
   own steps and picks its own models, so there is no single choice to replace or to compare with.
2. **The real task cannot be reproduced.** Workflow bots store only a 23-character placeholder as
   instructions, against a median of 1,173 characters (3,482 since September) for normal bots. The
   real step instructions are not in the bot table, so a candidate would answer a different, generic task.
3. **The judge could not grade it properly.** Following the bot's instructions is a main criterion.
   With a placeholder, that criterion has nothing to check.
4. **Most messages depend on the flow.** 63.0 % come right after a button or form (60.6 % since
   September), against 0.0 % for normal bots. Median length is 16 characters against 34, so many
   mean little on their own, and clusters built on them would be weaker.
5. **Labels are scarce.** Only 700 prompts are labeled. Spending them on tasks we cannot reproduce
   would weaken the scores of every cluster.
6. **The result stays clear.** Each labeled prompt has a defined bot, instructions and context, as
   each test item has in the paper.

### Limitation to state in the final report

- Results apply to **direct single-model bot traffic** only. That is about 73 % of all user messages
  but only about 25 % of those since September.
- No claim is made about workflow traffic. The gateway does not route it.
- Any saving must be reported as a share of direct-bot traffic, not of all traffic.
- With workflow removed, recent prompts lean to RAG: 73.9 % of recent direct-bot replies used RAG,
  against 17.4 % overall. Val and test will carry this mix, so results are reported with and
  without RAG.

## 5. How val and test are drawn

- Whole sessions go to one group, so no session is in two groups.
- Val (400, including the 100-prompt pilot and 100 calibration items) and test (300) come from the
  most recent sessions. The recent pool holds about 3 × 700 prompts.
- At most 3 prompts per session in val and test. Messages in a session are not independent, so
  confidence intervals resample whole sessions.
- Train is all remaining eligible prompts. It stays unlabeled.
- Test is sealed until WP-19. Seed 20261020.

## 6. Counts on the full data (S1, 2026-10-31)

| Step | Prompts |
|---|---|
| User messages | 355,965 |
| No bot reply | -17,640 |
| Prompt rows | 338,325 |
| `reply_workflow` | 94,190 |
| `reply_image` (after workflow) | 123 |
| `has_image` | 6,436 |
| `huge_prompt` | 406 |
| `too_short` | 2,373 |
| `junk` | 1,162 |
| `dup_exact` | 26,906 |
| **Eligible for val and test** | **206,729** |
| **Eligible for train** | **209,109** |

Counted in this order, each prompt under its first reason. All 48,170 widget clicks are also workflow turns. Balancing field: RAG yes/no. Exact repeats are matched within one bot.

## 7. Open items for WP-08

- Model, provider and instructions are the bot's current settings, not recorded per message.
  Bots changed later may be misattributed.
