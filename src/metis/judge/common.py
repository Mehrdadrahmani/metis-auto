"""One judged item: ask, parse, retry once on a parse failure, else drop (spec S7)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from metis.judge import jev
from metis.llm.callcache import CallCache, CallResult, get_or_call
from metis.llm.client import complete

# Handed to the runner when no call was needed (a failed generation is labeled directly).
NO_CALL = CallResult("", "ok", True, None, None, 0.0)
RETRY_SUFFIX = ":retry"


@dataclass
class JudgeRun:
    cache: CallCache
    budget: Any
    stage: str
    judge_id: str
    cfg: dict[str, Any]
    estimate_usd: float
    retry_failed: bool = False

    @property
    def is_jev(self) -> bool:
        return self.budget.models[self.judge_id]["provider"] == "typesafe"

    @property
    def params(self) -> dict[str, Any]:
        return self.cfg["judges"][self.judge_id]["params"]


def ask(
    run: JudgeRun,
    messages: list[dict[str, Any]],
    gen: dict[str, Any],
    parse: Callable[[str], dict[str, Any] | None],
    prompt_id: str,
) -> tuple[CallResult, dict[str, Any] | None]:
    """The retry has its own cache key, so a rerun repeats neither call."""
    send = jev.complete if run.is_jev else complete
    config = run.cfg["judge_config_id"]
    for suffix in ("", RETRY_SUFFIX):
        result = get_or_call(
            run.cache, run.budget, run.stage, run.judge_id, messages, gen,
            config + suffix, run.estimate_usd, send, retry_failed=run.retry_failed,
            prompt_id=prompt_id,
        )
        if result.status != "ok":
            return result, None
        parsed = parse(result.response.text)
        if parsed is not None:
            return result, {**parsed, "raw_output": result.response.text}
    return result, None
