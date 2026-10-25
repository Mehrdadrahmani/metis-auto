"""Counts report for S1 + S2 (WP-02 step 8). Aggregates only, no text.

Usage: uv run python scripts/s1_s2_counts.py runs/s1 runs/s2 results/wp02_prompts_splits/split_manifest_sample.json \
       results/wp02_prompts_splits/s1_s2_sample_counts.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from metis.data.prompts import REASONS_LABELED

NUM_COLS = [
    "prompt_id", "session_id", "lang", "est_tokens_in", "text_chars", "instr_chars", "huge_prompt",
    "reply_workflow", "reply_no_model", "reply_image", "widget_click", "widget_click_exact",
    "prev_bot_widget", "eligible_labeled", "eligible_train", "uses_rag", "demands_json",
    "instr_len_bucket", "prod_latency_s", *REASONS_LABELED,
]  # fmt: skip


def stats(s: pd.Series) -> str:
    if s.empty:
        return "– | – | – | – | 0"
    q = s.quantile([0.5, 0.9])
    return f"{s.mean():.0f} | {q[0.5]:.0f} | {q[0.9]:.0f} | {s.max():.0f} | {len(s)}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("s1_dir", type=Path)
    ap.add_argument("s2_dir", type=Path)
    ap.add_argument("split_manifest", type=Path)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()

    df = pd.read_parquet(a.s1_dir / "prompts.parquet", columns=list(dict.fromkeys(NUM_COLS)))
    s1 = json.loads((a.s1_dir / "prompts.manifest.json").read_text())
    s2 = json.loads(a.split_manifest.read_text())
    split = pd.read_parquet(a.s2_dir / "split.parquet", columns=["prompt_id", "split"])
    test_ids = set(json.loads((a.s2_dir / "test_ids.sealed").read_text()))
    sp = df[["prompt_id", "session_id", "eligible_labeled", "eligible_train"]].merge(
        split, how="left"
    )
    sp.loc[sp["prompt_id"].isin(test_ids), "split"] = "test"
    llm = df[~df["reply_workflow"] & ~df["reply_no_model"] & ~df["reply_image"]]
    c = s1["counts"]

    L = [
        "# S1 + S2 counts on the sample (WP-02 dry run)",
        "",
        "Aggregates only. Sizes scaled for the sample (val 60 / test 40 / pilot 20).",
        f"S1 config `{s1['config_id']}`, seed {s1['seed']}, input sha256 {s1['input_sha256']}.",
        "",
        "## S1: prompt rows",
        "",
        "| item | n |",
        "|---|---|",
        f"| user messages | {c['user_messages']} |",
        f"| user messages without a bot reply right after | {c['user_without_reply']} |",
        f"| prompt rows (user message + reply) | {c['prompt_rows']} |",
        f"| rows with an LLM reply (not workflow / no model / image) | {len(llm)} |",
        f"| eligible for val/test | {c['eligible_labeled']} |",
        f"| eligible for train (clustering) | {c['eligible_train']} |",
        "",
        "## Exclusions (labeled sets)",
        "",
        "`flag` = rows with this reason (a row may have several); `waterfall` = rows removed by",
        "this reason after the reasons above it.",
        "",
        "| reason | flag | waterfall |",
        "|---|---|---|",
    ]
    L += [f"| {r} | {c[f'flag_{r}']} | {c[f'waterfall_{r}']} |" for r in REASONS_LABELED]
    n_huge = int(df["huge_prompt"].sum())
    L += [
        "",
        (
            f"Huge system prompts (> 20k chars): {n_huge} of {len(df)} rows "
            f"({n_huge / len(df):.1%}); among LLM replies: {int(llm['huge_prompt'].sum())} of {len(llm)}"
            f" ({llm['huge_prompt'].mean():.1%}). All huge prompts belong to workflow turns"
            f" (model `default`): {bool(df.loc[df['huge_prompt'], 'reply_workflow'].all())}."
        ),
        "",
        "## Widget clicks",
        "",
        (
            f"- User messages right after a bot message with choices: {int(df['prev_bot_widget'].sum())}"
            " (the other widget messages are last in the session or followed by a bot message)."
        ),
        (
            f"- Matched a choice exactly: {int(df['widget_click_exact'].sum())}; after normalization: "
            f"{int(df['widget_click'].sum())}; free text instead of a choice: "
            f"{int((df['prev_bot_widget'] & ~df['widget_click']).sum())}."
        ),
        (
            f"- Widget clicks answered by a workflow step: "
            f"{int((df['widget_click'] & df['reply_workflow']).sum())} of {int(df['widget_click'].sum())}."
        ),
        "",
        "## Language",
        "",
        "| lang | all rows | eligible val/test | eligible train |",
        "|---|---|---|---|",
    ]
    for lang in ["fa", "en", "mixed", "other"]:
        m = df["lang"] == lang
        L.append(
            f"| {lang} | {int(m.sum())} | {int((m & df['eligible_labeled']).sum())} |"
            f" {int((m & df['eligible_train']).sum())} |"
        )
    el = df[df["eligible_labeled"]]
    L += [
        "",
        "## Size estimates (chars / 3)",
        "",
        "| set | mean | p50 | p90 | max | n |",
        "|---|---|---|---|---|---|",
        f"| est_tokens_in, eligible val/test | {stats(el['est_tokens_in'])} |",
        f"| est_tokens_in, LLM replies incl. huge | {stats(llm['est_tokens_in'])} |",
        (
            f"| est_tokens_in, LLM replies without huge | "
            f"{stats(llm.loc[~llm['huge_prompt'], 'est_tokens_in'])} |"
        ),
        f"| user text chars, eligible | {stats(el['text_chars'])} |",
        f"| system prompt chars, eligible | {stats(el['instr_chars'])} |",
        f"| production latency s, eligible | {stats(el['prod_latency_s'].dropna())} |",
        "",
        (
            f"Eligible rows using RAG: {int(el['uses_rag'].sum())}; system prompt mentions JSON: "
            f"{int(el['demands_json'].sum())}. Instruction length buckets (eligible): "
            f"{el['instr_len_bucket'].value_counts().sort_index().to_dict()}."
        ),
        "",
        "## S2: split (by session)",
        "",
        (
            f"Sessions with prompt rows: {s2['sessions_total']}; recent pool: {s2['pool_sessions']} "
            f"sessions, capacity {s2['pool_capacity']} prompts (≤ 3 per session); val sessions "
            f"{s2['val_sessions']}, test sessions {s2['test_sessions']}. Shortfall: "
            f"{'none' if not any(v for d in s2['shortfall'].values() for v in d.values()) else s2['shortfall']}."
        ),
        "",
        "| split | prompts |",
        "|---|---|",
    ]
    L += [f"| {k} | {v} |" for k, v in s2["counts_by_split"].items()]
    lab_sess = set(sp.loc[sp["split"].isin(["val", "test"]), "session_id"])
    none = sp[sp["split"].fillna("none") == "none"]
    in_lab = none["session_id"].isin(lab_sess)
    L += [
        "",
        (
            f"`none` = {len(none)}: in a val/test session but not drawn (cap 3 or not eligible): "
            f"{int(in_lab.sum())} (of which eligible: {int((in_lab & none['eligible_labeled']).sum())});"
            f" in a train session but not eligible for train: {int((~in_lab).sum())}."
        ),
        f"Pilot {s2['pilot']} (⊂ val); cal per model {s2['cal_per_model']}.",
        "",
        "| split × category | n |",
        "|---|---|",
    ]
    by = pd.DataFrame(s2["counts_split_category_lang"]).groupby(["split", "category"])["n"].sum()
    L += [f"| {s} × {cat} | {n} |" for (s, cat), n in by.items()]
    L += [
        "",
        "Hashes of the sorted id lists (rerun with the same seed reproduces them):",
        "",
        *[f"- {k}: {v}" for k, v in s2["sha256"].items()],
        "",
    ]
    a.out.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
