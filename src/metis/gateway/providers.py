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
    """Real calls through `metis.llm.client`: redaction, outgoing guard, budget permit per call."""

    def __init__(self, stage: str = "live", gen: dict[str, dict[str, Any]] | None = None, max_tokens: int = 1024):
        from metis.llm.budget import Budget
        from metis.llm.client import load_models

        self.stage, self.gen, self.max_tokens = stage, gen or {}, max_tokens
        self.budget, self.models = Budget(), load_models()
        self.semaphores: dict[str, threading.Semaphore] = {}

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        from metis.llm.budget import call_cost
        from metis.llm.client import CallFailed, complete, redact_messages

        clean = redact_messages(messages)
        chars = sum(len(str(m.get("content", ""))) for m in clean)
        estimate = call_cost(self.models[model], chars // 3 + 1, self.max_tokens)
        permit = self.budget.guard(self.stage, estimate)
        try:
            r = complete(model, clean, self.gen.get(model, {"max_tokens": self.max_tokens}), permit)
        except CallFailed as exc:
            self.budget.release(permit)
            raise ProviderError(exc.kind if hasattr(exc, "kind") else "call_failed") from None
        return Reply(r.text, r.tokens_in, r.tokens_out, r.finish_reason, r.latency_ms, r.cached_tokens)
