"""Where a model call goes: mock (tests, demo), live (Metis AI), replay is in `metis.sim.replay`."""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from typing import Any, Protocol

from metis.gateway.failover import ProviderError


@dataclass
class Reply:
    text: str
    tokens_in: int
    tokens_out: int
    finish_reason: str
    latency_ms: float
    cached_tokens: int | None = None


class Provider(Protocol):
    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply: ...


@dataclass
class MockProvider:
    """Deterministic fake answers with fault injection: down models and an error rate."""

    latency_ms: dict[str, float] = field(default_factory=dict)
    down: set[str] = field(default_factory=set)
    error_rate: float = 0.0
    seed: int = 20261020

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        if model in self.down or self.rng.random() < self.error_rate:
            raise ProviderError("mock_5xx")
        chars = sum(len(str(m.get("content", ""))) for m in messages)
        text = f"پاسخ نمایشی از {model}. این متن واقعی نیست."
        return Reply(text, chars // 3 + 1, len(text) // 3, "stop", float(self.latency_ms.get(model, 100)))


class LiveProvider:
    """Real calls: redaction, outgoing guard, budget guard and ledger through `get_or_call`."""

    def __init__(self, stage: str = "live"):
        import time

        from metis.config import load_config
        from metis.llm.budget import Budget
        from metis.llm.callcache import CallCache

        self.stage = stage
        self.cache = CallCache()
        self.budget = Budget(self.cache)
        self.gen = load_config("gen_config")
        self.run_id = f"live-{int(time.time())}"  # fresh calls, so latency is real
        self.lock = threading.Lock()

    def send(self, model, messages, gen, permit=None, prompt_id=None):
        import os

        from metis.llm.client import AccountBlocked, complete

        try:
            return complete(model, messages, gen, permit, prompt_id)
        except AccountBlocked:
            spare = os.environ.pop("METIS_API_KEY_SPARE", None)
            if not spare:
                raise
            os.environ["METIS_API_KEY"] = spare  # owner's spare key, used once the first runs out
            return complete(model, messages, gen, permit, prompt_id)

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        from metis.llm.budget import call_cost
        from metis.llm.callcache import get_or_call
        from metis.llm.client import redact_messages
        from metis.llm.messages import gen_params

        clean = redact_messages(messages)
        params = gen_params(model, self.gen)
        chars = sum(len(str(m.get("content", ""))) for m in clean)
        from metis.llm.budget import BudgetRefused

        estimate = call_cost(self.budget.models[model], chars // 3 + 1, 300)
        try:
            result = get_or_call(self.cache, self.budget, self.stage, model, clean, params, self.run_id, estimate, self.send,
                                 prompt_id=context.get("prompt_id"))
        except BudgetRefused:
            raise ProviderError("budget") from None
        if result.status != "ok" or result.response is None:
            raise ProviderError(result.error_kind or "call_failed")
        r = result.response
        return Reply(r.text, r.tokens_in, r.tokens_out, r.finish_reason, r.latency_ms, r.cached_tokens)
