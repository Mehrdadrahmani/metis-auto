"""Where a model call goes: mock (tests, demo), live (Metis AI), replay is in `metis.sim.replay`."""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from typing import Any, Protocol

from metis.gateway.failover import ProviderError

OWN_KEY_REJECTED = "own_key_rejected"  # the user's own key was refused (bad key or no balance)


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

    rejected_keys: set[str] = field(default_factory=set)  # tests: own keys the "provider" refuses

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        if context.get("api_key") and context["api_key"] in self.rejected_keys:
            raise ProviderError(OWN_KEY_REJECTED)
        if model in self.down or self.rng.random() < self.error_rate:
            raise ProviderError("mock_5xx")
        chars = sum(len(str(m.get("content", ""))) for m in messages)
        text = f"پاسخ نمایشی از {model}. این متن واقعی نیست."
        reply = Reply(text, chars // 3 + 1, len(text) // 3, "stop", float(self.latency_ms.get(model, 100)))
        return stream_out(reply, context)


def stream_out(reply: Reply, context: dict[str, Any]) -> Reply:
    """For answers that come whole (mock, call cache): still hand them out piece by piece."""
    on_delta = context.get("on_delta")
    if on_delta:
        import re
        import time

        pause = float(context.get("mock_pause_s", 0.0))
        for piece in re.findall(r"\S+\s*|\s+", reply.text):
            on_delta(piece)
            if pause:
                time.sleep(pause)
    return reply


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

    def send(self, model, messages, gen, permit=None, prompt_id=None, on_delta=None):
        import os

        from metis.llm.client import AccountBlocked, complete

        try:
            return complete(model, messages, gen, permit, prompt_id, on_delta=on_delta)
        except AccountBlocked:
            spare = os.environ.pop("METIS_API_KEY_SPARE", None)
            if not spare:
                raise
            os.environ["METIS_API_KEY"] = spare  # owner's spare key, used once the first runs out
            return complete(model, messages, gen, permit, prompt_id, on_delta=on_delta)

    def call_own_key(self, model: str, messages: list[dict[str, Any]], api_key: str, on_delta=None) -> Reply:
        """A user's own key: straight to the provider. Not in our ledger, cache or budget (the user pays)."""
        from metis.llm.client import AccountBlocked, CallFailed, complete
        from metis.llm.messages import gen_params

        try:
            r = complete(model, messages, gen_params(model, self.gen), api_key=api_key, on_delta=on_delta)
        except AccountBlocked:
            raise ProviderError(OWN_KEY_REJECTED) from None
        except CallFailed as exc:
            raise ProviderError(exc.kind) from None
        return Reply(r.text, r.tokens_in, r.tokens_out, r.finish_reason, r.latency_ms, r.cached_tokens)

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        from metis.llm.budget import call_cost
        from metis.llm.callcache import get_or_call
        from metis.llm.client import redact_messages
        from metis.llm.messages import gen_params

        clean = redact_messages(messages)
        if context.get("api_key"):
            return self.call_own_key(model, clean, context["api_key"], context.get("on_delta"))
        params = gen_params(model, self.gen)
        chars = sum(len(str(m.get("content", ""))) for m in clean)
        from metis.llm.budget import BudgetRefused

        estimate = call_cost(self.budget.models[model], chars // 3 + 1, 300)
        on_delta, streamed = context.get("on_delta"), []
        send = self.send
        if on_delta:  # stream the paid call; the ledger, budget and cache see one normal call
            def send(*a, **k):
                return self.send(*a, on_delta=lambda piece: (streamed.append(1), on_delta(piece)), **k)
        try:
            result = get_or_call(self.cache, self.budget, self.stage, model, clean, params, self.run_id, estimate, send,
                                 prompt_id=context.get("prompt_id"))
        except BudgetRefused:
            raise ProviderError("budget") from None
        if result.status != "ok" or result.response is None:
            raise ProviderError(result.error_kind or "call_failed")
        r = result.response
        reply = Reply(r.text, r.tokens_in, r.tokens_out, r.finish_reason, r.latency_ms, r.cached_tokens)
        return reply if streamed or not on_delta else stream_out(reply, {"on_delta": on_delta})  # stored answers come whole
