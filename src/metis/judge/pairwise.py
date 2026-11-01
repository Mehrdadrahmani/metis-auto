"""S7-PW: candidate against the anchor, both orders (spec S7-PW, A1 extended by DEV-5)."""

from __future__ import annotations

from typing import Any

from metis.judge import parse, render
from metis.judge.common import NO_CALL, JudgeRun, ask
from metis.llm.callcache import CallResult

ORDERS = ("h_first", "a_first")
POINTS = {"h": 1.0, "tie": 0.5, "anchor": 0.0}


def to_verdict(letter: str, order: str) -> str:
    if letter == "tie":
        return "tie"
    h_letter = "A" if order == "h_first" else "B"
    return "h" if letter == h_letter else "anchor"


def judge(
    run: JudgeRun,
    row: dict[str, Any],
    model_id: str,
    order: str,
    answer: str | None,
    anchor_answer: str | None,
) -> tuple[CallResult, dict[str, Any]]:
    base = {"prompt_id": row["prompt_id"], "model_id": model_id, "order": order,
            "judge_id": run.judge_id, "judge_config_id": run.cfg["judge_config_id"]}
    if not anchor_answer:  # no fair comparison exists; the spec has no rule, so drop and log
        return NO_CALL, {**base, "status": "failed_anchor"}
    if not answer:  # spec S6: o = 0
        return NO_CALL, {**base, "verdict": "anchor", "reason": "", "status": "failed_generation"}
    first, second = (answer, anchor_answer) if order == "h_first" else (anchor_answer, answer)
    if run.is_jev:
        messages = render.jev_pair_messages(row, first, second, run.cfg)
        gen, read = {"questions": render.jev_questions("pairwise")}, parse.parse_jev_pair
    else:
        messages = render.pair_messages(row, first, second, run.cfg)
        gen, read = run.params, parse.parse_pair
    result, found = ask(run, messages, gen, read, row["prompt_id"])
    if found is None:
        return result, {**base, "status": "dropped"}
    verdict = to_verdict(found.pop("verdict"), order)
    return result, {**base, **found, "verdict": verdict, "status": "ok"}


def outcomes(records: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    """o(x, h) = mean of both orders. Pairs missing an order are left out (spec: drop and log)."""
    seen: dict[tuple[str, str], dict[str, float]] = {}
    for r in records:
        if r.get("verdict") in POINTS:
            seen.setdefault((r["prompt_id"], r["model_id"]), {})[r["order"]] = POINTS[r["verdict"]]
    return {k: sum(v.values()) / 2 for k, v in seen.items() if len(v) == 2}
