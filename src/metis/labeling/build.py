"""Local labeling tool (WP-06 step 7, WP-10, PLAN M11): one self-contained HTML file, no server.

The HTML holds no model names. Which answer is which lives in a key file next to it, read only by
``labeling.ingest``. Both go under ``runs/labeling/`` (git-ignored); they contain data text.

Usage:
  uv run python -m metis.labeling.build --responses runs/s6/responses_pilot.parquet \
      --prompts runs/s1/prompts.parquet --split runs/s2/split.parquet
  add --n 5 --any for a tool test, --relabel <cal csv> for the 20 repeat items.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from metis.config import load_config
from metis.judge.render import history_text, template
from metis.llm import stage as st

ANCHOR = "claude-sonnet-5-5"
TEMPLATE_HTML = Path(__file__).parent / "tool.html"
RELABEL_N = 20


def bands() -> list[str]:
    scale = template("pointwise").split("Scoring scale:")[1].split("Write the reason")[0]
    return [line.strip() for line in scale.splitlines() if line.strip()]


def pick_pairs(
    split: pd.DataFrame, answers: dict[tuple[str, str], str], candidates: list[str], use_any: bool
) -> list[tuple[str, str]]:
    """(prompt, candidate) pairs: the calibration set, or for a tool test any prompt with answers."""
    if not use_any:
        cal = split[split["cal_model"].notna()]
        return [(p, m) for p, m in zip(cal["prompt_id"], cal["cal_model"], strict=True)]
    ids = sorted({p for p, m in answers if m == ANCHOR})
    return [(p, candidates[i % len(candidates)]) for i, p in enumerate(ids)]


def make_items(
    pairs: list[tuple[str, str]],
    rows: dict[str, dict[str, Any]],
    answers: dict[tuple[str, str], str],
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """Shuffled items and the key. Failed answers cannot be labeled and are left out."""
    rng = random.Random(seed)
    usable = [x for x in pairs if answers.get(x) and answers.get((x[0], ANCHOR))]
    rng.shuffle(usable)
    items, key = [], {}
    for i, (pid, model) in enumerate(usable, 1):
        item_id = f"item-{i:03d}"
        candidate, anchor = answers[(pid, model)], answers[(pid, ANCHOR)]
        left_is_h = rng.random() < 0.5
        r = rows[pid]
        items.append({
            "id": item_id,
            "instructions": r.get("instructions") or "",
            "context": "\n\n".join(str(c) for c in r.get("rag_context") or [] if c),
            "history": history_text(r.get("history")),
            "user": r["text"],
            "answer": candidate,
            "left": candidate if left_is_h else anchor,
            "right": anchor if left_is_h else candidate,
        })
        key[item_id] = {"prompt_id": pid, "model_id": model, "left": "h" if left_is_h else "anchor"}
    return items, key


def render_html(items: list[dict[str, Any]], mode: str) -> str:
    data = json.dumps({"items": items, "mode": mode, "bands": bands()}, ensure_ascii=False)
    data = data.replace("<", "\\u003c")  # no text can close the script tag
    return TEMPLATE_HTML.read_text(encoding="utf-8").replace("/*DATA*/null", data)


def relabel_pairs(csv_path: Path, key: dict[str, dict[str, str]], seed: int) -> list[tuple[str, str]]:
    done = pd.read_csv(csv_path)
    ids = sorted(set(done["item_id"]) & set(key))
    picked = random.Random(seed).sample(ids, min(RELABEL_N, len(ids)))
    return [(key[i]["prompt_id"], key[i]["model_id"]) for i in picked]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", type=Path, required=True)
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("runs/labeling"))
    ap.add_argument("--n", type=int)
    ap.add_argument("--any", action="store_true", help="tool test: use any prompt with answers")
    ap.add_argument("--relabel", type=Path, help="CSV exported from the calibration file")
    ap.add_argument("--key", type=Path, help="key file of that calibration file")
    args = ap.parse_args()

    seed = load_config("pipeline")["seed"]
    df = pd.read_parquet(args.responses)
    df = df[df["status"] == "ok"]
    answers = {(a.prompt_id, a.model_id): a.text for a in df.itertuples()}
    candidates = sorted(set(df["model_id"]) - {ANCHOR})
    split = pd.read_parquet(args.split, columns=["prompt_id", "cal_model"])
    if args.relabel:
        key = json.loads(args.key.read_text(encoding="utf-8"))
        pairs, mode, seed = relabel_pairs(args.relabel, key, seed), "relabel", seed + 1
    else:
        pairs, mode = pick_pairs(split, answers, candidates, args.any), "cal"
    pairs = pairs[: args.n] if args.n else pairs
    rows = st.load_rows(args.prompts, sorted({p for p, _ in pairs}))
    items, key = make_items(pairs, rows, answers, seed)

    args.out.mkdir(parents=True, exist_ok=True)
    stem = f"{mode}_{date.today().isoformat()}"
    (args.out / f"{stem}.html").write_text(render_html(items, mode), encoding="utf-8")
    (args.out / f"{stem}.key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(f"wrote {args.out / stem}.html with {len(items)} items")


if __name__ == "__main__":
    main()
