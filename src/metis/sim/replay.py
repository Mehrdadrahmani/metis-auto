"""Replay real prompts through the gateway with stored answers (WP-18). $0, simulated costs.

Stored answer, tokens and latency stand in for the model call. A repair retry returns the same
stored answer at its cost, so replay escalation is pessimistic. One tick = 6 simulated seconds, so
a 10-minute outage covers 100 requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.gateway.cache import SemanticCache
from metis.gateway.failover import ProviderError
from metis.gateway.pipeline import ChatRequest, Gateway
from metis.gateway.providers import Reply
from metis.gateway.traces import TraceStore
from metis.llm.client import load_models
from metis.router.artifact import RouterArtifact

TICK_S = 6.0
CACHE_MS = 5.0


@dataclass
class ReplayProvider:
    answers: dict[tuple[str, str], Reply]
    down: dict[str, tuple[int, int]] = field(default_factory=dict)
    tick: int = 0

    def call(self, model: str, messages: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        span = self.down.get(model)
        if span and span[0] <= self.tick < span[1]:
            raise ProviderError("outage")
        reply = self.answers.get((context["prompt_id"], model))
        if reply is None:
            raise ProviderError("missing")
        return reply


def load_answers(frame: pd.DataFrame) -> dict[tuple[str, str], Reply]:
    out = {}
    for r in frame.itertuples():
        if isinstance(r.text, str) and r.status == "ok":
            out[(r.prompt_id, r.model_id)] = Reply(r.text, int(r.tokens_in), int(r.tokens_out), str(r.finish_reason), float(r.latency_ms))
    return out


@dataclass
class Traffic:
    ids: list[str]
    vectors: np.ndarray
    meta: pd.DataFrame  # index prompt_id: session_id, msg_index, bot_id, system_prompt_id, text_norm, demands_json, uses_rag, has_image
    losses: pd.DataFrame  # index prompt_id, columns models
    groups: np.ndarray


@dataclass
class Settings:
    name: str
    fixed_model: str | None = None
    cache: bool = False
    checks: bool = False
    stick_delta: float | None = None
    outage: tuple[int, int] | None = None
    outage_model: str | None = None
    embed_ms: float = 23.4


def run(traffic: Traffic, answers: dict, artifact: RouterArtifact, s: Settings, theta: float = 0.97) -> pd.DataFrame:
    """One row per request: served model, pass (NaN if a cached answer), cost, latency, flags."""
    cfg = load_config("gateway")
    cfg = {**cfg, "checks": {**cfg["checks"], "enabled": s.checks}, "stickiness": {"enabled": s.stick_delta is not None, "delta": s.stick_delta or 0}}
    down = {s.outage_model: s.outage} if s.outage else {}
    provider = ReplayProvider(answers, down)
    clock = [0.0]
    cache = SemanticCache(theta, 7, clock=lambda: clock[0]) if s.cache else None
    gw = Gateway(artifact, provider, lambda t: None, cfg, load_models(), TraceStore(), cache, clock=lambda: clock[0])
    for b in gw.breakers.values():
        b.clock = lambda: clock[0]
    rows = []
    for tick, pid in enumerate(traffic.ids):
        provider.tick, clock[0] = tick, tick * TICK_S
        m = traffic.meta.loc[pid]
        user = [{"role": "user", "content": str(m.text_norm)}]
        earlier = [{"role": "user", "content": ""}] * int(m.msg_index > 1)
        req = ChatRequest([{"role": "system", "content": str(m.system_prompt_id)}, *earlier, *user], model=s.fixed_model or "takrouter",
                          chatbot=str(m.bot_id), session=str(m.session_id), wants_json=bool(m.demands_json), uses_rag=bool(m.uses_rag),
                          has_image=False, prompt_id=pid, route_text=str(m.text_norm), vector=traffic.vectors[tick])
        result = gw.handle(req)
        t = result.trace
        cached = (t["cache"] or "").startswith("hit")
        served = result.model
        loss = np.nan
        if served and not cached:
            loss = float(traffic.losses.loc[pid, served])
        elif not served:
            loss = 1.0
        rows.append({"prompt_id": pid, "model": served, "passed": 1 - loss, "cost": t["cost_usd"], "latency": t["latency_ms"] + (s.embed_ms if not s.fixed_model else 0),
                     "cache": t["cache"], "cached": cached, "escalations": t["escalations"], "tried": len(t["tried"]), "status": t["status"], "cluster": t["cluster"], "reasons": len(t.get("reasons") or [])})
    return pd.DataFrame(rows)
