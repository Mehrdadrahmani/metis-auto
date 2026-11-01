"""S7-PT: score one answer 1 to 10 (spec S7-PT, A2 extended by DEV-5)."""

from __future__ import annotations

from typing import Any

from metis.judge import parse, render
from metis.judge.common import NO_CALL, JudgeRun, ask
from metis.llm.callcache import CallResult

FAILED_SCORE = 1.0  # spec S6: a failed generation counts as the worst label


def judge(
    run: JudgeRun, row: dict[str, Any], model_id: str, answer: str | None
) -> tuple[CallResult, dict[str, Any]]:
    base = {"prompt_id": row["prompt_id"], "model_id": model_id, "judge_id": run.judge_id,
            "judge_config_id": run.cfg["judge_config_id"]}
    if not answer:
        return NO_CALL, {**base, "score": FAILED_SCORE, "reason": "", "status": "failed_generation"}
    if run.is_jev:
        messages = render.jev_point_messages(row, answer, run.cfg)
        gen, read = {"questions": render.jev_questions("pointwise")}, parse.parse_jev_point
    else:
        messages = render.point_messages(row, answer, run.cfg)
        gen, read = run.params, parse.parse_point
    result, found = ask(run, messages, gen, read, row["prompt_id"])
    return result, {**base, **(found or {}), "status": "ok" if found else "dropped"}
