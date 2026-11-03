"""The gateway pipeline, one request at a time: G1 rules → G2 embed → G3 cache → G4 route →
G5 call with failover → G6 checks and escalation → G7 trace. The router is UniRoute (Eq. 8/11)."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from metis.data.lang import lang_tag
from metis.data.normalize import match_key, normalize
from metis.data.rules import estimate_tokens, fits_context
from metis.gateway.cache import SemanticCache
from metis.gateway.cache_policy import is_cacheable
from metis.gateway.checks import HINTS, check_answer
from metis.gateway.failover import Breaker, ProviderError
from metis.gateway.providers import Provider, Reply
from metis.gateway.traces import TraceStore
from metis.router.artifact import RouterArtifact
from metis.router.route import route

CACHE_LATENCY_MS = 5.0


class NoModelAvailable(RuntimeError):
    pass


@dataclass
class ChatRequest:
    messages: list[dict[str, Any]]
    model: str = "takrouter"
    chatbot: str = "default"
    session: str | None = None
    has_image: bool = False
    wants_json: bool = False
    widget_click: bool = False
    uses_rag: bool = False
    context_hash: str | None = None
    lam: float | None = None  # lambda for this request; None uses the gateway's (the chat page's slider)
    user_id: int | None = None  # the signed-in account, for usage and credit
    prompt_id: str | None = None  # replay only
    route_text: str | None = None  # replay only: text as it was embedded offline
    vector: np.ndarray | None = None  # replay only: stored vector


@dataclass
class ChatResult:
    text: str
    model: str | None
    cluster: int | None
    trace: dict[str, Any] = field(default_factory=dict)
    attempts: list[dict[str, Any]] = field(default_factory=list)


def user_text(messages: list[dict[str, Any]]) -> str:
    """The current user message only (D-045)."""
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content")
            if isinstance(content, list):
                return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
            return content or ""
    return ""


def instructions_of(messages: list[dict[str, Any]]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system")


class Gateway:
    def __init__(self, artifact: RouterArtifact, provider: Provider, embed: Callable[[str], np.ndarray], cfg: dict[str, Any],
                 models: dict[str, dict[str, Any]], traces: TraceStore | None = None, cache: SemanticCache | None = None,
                 cache_embed: Callable[[str], np.ndarray] | None = None, clock: Callable[[], float] = time.time):
        self.artifact, self.provider, self.embed, self.cfg, self.models = artifact, provider, embed, cfg, models
        self.router = artifact.router()
        self.lam = float(cfg.get("lam", artifact.meta.lam))
        self.traces = traces or TraceStore()
        self.cache = cache
        self.cache_embed = cache_embed or embed
        self.clock = clock
        b = cfg.get("breaker", {})
        self.breakers = {m: Breaker(b.get("failures", 3), b.get("window_s", 60), b.get("open_s", 30)) for m in artifact.meta.models}
        self.session_model: dict[str, str] = {}

    def swap(self, artifact: RouterArtifact, models: dict[str, dict[str, Any]]) -> None:
        """Serve a new artifact (a model was added or removed). Lambda, cache and traces stay."""
        b = self.cfg.get("breaker", {})
        self.breakers = {m: self.breakers.get(m) or Breaker(b.get("failures", 3), b.get("window_s", 60), b.get("open_s", 30))
                         for m in artifact.meta.models}
        self.models, self.artifact, self.router = models, artifact, artifact.router()
        if hasattr(self.provider, "budget"):
            self.provider.budget.models = models  # the live provider prices calls from this table

    # G1
    def available(self, req: ChatRequest, text_chars: int, dropped: dict[str, str] | None = None) -> list[str]:
        """Models that can take this request; ``dropped`` collects why the others cannot."""
        tokens = estimate_tokens("x" * text_chars)
        out = []
        for m in self.artifact.meta.models:
            info = self.models.get(m, {})
            why = ("no_vision" if req.has_image and not info.get("vision") else
                   "too_long" if not fits_context(m, tokens) else
                   "breaker_open" if not self.breakers[m].available() else None)
            if why is None:
                out.append(m)
            elif dropped is not None:
                dropped[m] = why
        return out

    def cost(self, model: str, reply: Reply) -> float:
        info = self.models.get(model, {})
        cached = reply.cached_tokens or 0
        rate_in, rate_out = info.get("price_in", 0), info.get("price_out", 0)
        rate_cached = info.get("price_cached", rate_in)
        return ((reply.tokens_in - cached) * rate_in + cached * rate_cached + reply.tokens_out * rate_out) / 1e6

    # G5
    def call_with_failover(self, order: list[str], messages, context, attempts) -> tuple[str, Reply]:
        for model in order:
            breaker = self.breakers[model]
            if not breaker.available():
                continue
            breaker.before_call()
            try:
                reply = self.provider.call(model, messages, context)
            except ProviderError as exc:
                breaker.failure()
                attempts.append({"model": model, "ok": False, "reason": exc.kind})
                continue
            breaker.success()
            attempts.append({"model": model, "ok": True, "cost": self.cost(model, reply), "latency_ms": reply.latency_ms,
                             "tokens_in": reply.tokens_in, "tokens_out": reply.tokens_out})
            return model, reply
        raise NoModelAvailable

    # G6
    def checked_call(self, req, lang, order, context, attempts, reasons) -> tuple[str, Reply, int]:
        cfg = self.cfg.get("checks", {})
        model, reply = self.call_with_failover(order, req.messages, context, attempts)
        if not cfg.get("enabled", True):
            return model, reply, 0
        check = lambda r: check_answer(r.text, r.finish_reason, lang, req.wants_json, cfg.get("min_lang_chars", 20))
        reason = check(reply)
        if reason is None:
            return model, reply, 0
        reasons.append(reason)
        hinted = [*req.messages, {"role": "system", "content": HINTS[reason]}]
        try:
            model, reply = self.call_with_failover([model], hinted, {**context, "repair": True}, attempts)
            reason = check(reply)
        except NoModelAvailable:
            pass
        escalations, used = 0, {a["model"] for a in attempts}
        psi = context["psi"]
        while reason is not None and escalations < cfg.get("max_escalations", 2):
            stronger = sorted((m for m in order if m not in used and psi[m] < psi[model]), key=lambda m: psi[m])
            if not stronger:
                break
            escalations += 1
            try:
                model, reply = self.call_with_failover(stronger, req.messages, {**context, "escalated": True}, attempts)
            except NoModelAvailable:
                break
            used.add(model)
            reason = check(reply)
            if reason:
                reasons.append(reason)
        return model, reply, escalations

    def choose(self, req: ChatRequest, vec: np.ndarray, available: list[str]):
        decision = route(vec, available, self.router, self.lam if req.lam is None else req.lam)
        order = list(decision.ranking)
        stick = self.cfg.get("stickiness", {})
        previous = self.session_model.get(req.session or "")
        if stick.get("enabled") and previous in decision.scores and decision.scores[previous] <= min(decision.scores.values()) + stick.get("delta", 0):
            order = [previous, *[m for m in order if m != previous]]
        return decision, order

    def handle(self, req: ChatRequest) -> ChatResult:
        started = time.perf_counter()
        stages: dict[str, float] = {}
        def lap(name: str, since: float) -> float:
            now = time.perf_counter()
            stages[name] = (now - since) * 1000
            return now

        rid = uuid.uuid4().hex
        text = req.route_text if req.route_text is not None else user_text(req.messages)
        lang = lang_tag(text)
        row = {"request_id": rid, "ts": self.clock(), "session_id": req.session, "chatbot": req.chatbot, "lang": lang,
               "user_id": req.user_id, "rag": req.uses_rag, "image": req.has_image, "dropped": {},
               "artifact": self.artifact.meta.hashes.get("val_set"), "escalations": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}

        def finish(result: ChatResult, status: str, cache: str, extra_ms: float = 0.0) -> ChatResult:
            overhead = (time.perf_counter() - started) * 1000
            row.update(status=status, cache=cache, stage_ms=stages, latency_ms=overhead + extra_ms, overhead_ms=overhead,
                       tried=[a["model"] for a in result.attempts], cluster=result.cluster, served_by=result.model)
            self.traces.add(row)
            result.trace = row
            row["attempts"] = result.attempts
            return result

        mark = time.perf_counter()
        if req.widget_click:
            lap("rules", mark)
            return finish(ChatResult("", None, None), "workflow", "skip")
        if req.model not in (self.cfg.get("model_alias", "takrouter"), "metis-auto"):
            if req.model not in self.artifact.meta.models:
                raise ValueError("unknown model")
            available = [req.model]
        else:
            available = self.available(req, sum(len(str(m.get("content", ""))) for m in req.messages), row["dropped"])
        row["available"] = available
        mark = lap("rules", mark)
        if not available:
            return finish(ChatResult("", None, None), "no_model", "skip")

        vec = req.vector if req.vector is not None else self.embed(normalize(text))
        mark = lap("embed", mark)

        first_turn = sum(1 for m in req.messages if m.get("role") == "user") <= 1
        ok, why = is_cacheable(text, first_turn, req.has_image, req.uses_rag, req.context_hash)
        state = f"skip_{why}"
        space = key = None
        cache_vec = None
        if self.cache and ok:
            digest = hashlib.sha256(instructions_of(req.messages).encode()).hexdigest()[:16]
            space = f"{req.chatbot}|{digest}|{lang}|{req.context_hash or ''}"
            key = match_key(text)
            cache_vec = vec if self.cache_embed is self.embed else self.cache_embed(normalize(text))
            hit = self.cache.lookup(space, key, cache_vec)
            state = "miss"
            if hit:
                state, entry = hit
                stages["cache"] = (time.perf_counter() - mark) * 1000
                row.update(chosen=entry.model, scores={}, reasons=[])
                return finish(ChatResult(entry.answer, entry.model, None), "ok", state, CACHE_LATENCY_MS)
        mark = lap("cache", mark)

        decision, order = self.choose(req, vec, available)
        mark = lap("route", mark)
        row.update(chosen=order[0], scores=decision.scores, lam=self.lam if req.lam is None else req.lam,
                   cluster_name=self.artifact.meta.cluster_names[decision.cluster])
        psi = {m: float(self.router.psi[decision.cluster, self.router.models.index(m)]) for m in order}
        context = {"prompt_id": req.prompt_id, "psi": psi, "cluster": decision.cluster}
        attempts: list[dict[str, Any]] = []
        reasons: list[str] = []
        try:
            model, reply, escalations = self.checked_call(req, lang, order, context, attempts, reasons)
        except NoModelAvailable:
            row["reasons"] = reasons
            lap("call", mark)
            return finish(ChatResult("", None, decision.cluster, attempts=attempts), "all_failed", state)
        lap("call", mark)
        paid = [a for a in attempts if a.get("ok")]
        row.update(reasons=reasons, escalations=escalations, cost_usd=sum(a["cost"] for a in paid),
                   tokens_in=sum(a["tokens_in"] for a in paid), tokens_out=sum(a["tokens_out"] for a in paid))
        if req.session:
            self.session_model[req.session] = model
        failed_final = check_answer(reply.text, reply.finish_reason, lang, req.wants_json) if self.cfg.get("checks", {}).get("enabled", True) else None
        if self.cache and ok and failed_final is None:
            self.cache.store(space, key, cache_vec, reply.text, model)
        result = ChatResult(reply.text, model, decision.cluster, attempts=attempts)
        return finish(result, "ok", state, sum(a.get("latency_ms", 0) for a in attempts))


def openai_response(result: ChatResult) -> dict[str, Any]:
    t = result.trace
    return {"id": f"chatcmpl-{t['request_id']}", "object": "chat.completion", "created": int(t["ts"]), "model": result.model or "takrouter",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": result.text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": t["tokens_in"], "completion_tokens": t["tokens_out"], "total_tokens": t["tokens_in"] + t["tokens_out"]},
            "takrouter": json.loads(json.dumps({k: t.get(k) for k in (
                "cluster", "cluster_name", "lam", "scores", "chosen", "served_by", "tried", "reasons", "cache",
                "escalations", "cost_usd", "latency_ms", "overhead_ms", "status")}))}


def trace_view(result: ChatResult) -> dict[str, Any]:
    """Every step of one request, for the chat page's optional trace. Ids and numbers only."""
    t = result.trace
    keys = ("request_id", "available", "dropped", "rag", "image", "lang", "cache", "cluster", "cluster_name", "lam",
            "scores", "chosen", "served_by", "attempts", "reasons", "escalations", "stage_ms", "overhead_ms",
            "latency_ms", "cost_usd", "status")
    return json.loads(json.dumps({k: t.get(k) for k in keys}, default=float))
