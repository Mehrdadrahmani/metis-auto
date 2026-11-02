"""TakRouter: an OpenAI-compatible FastAPI service. Run: uv run uvicorn metis.gateway.app:app"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from metis.config import load_config
from metis.gateway.cache import SemanticCache
from metis.gateway.pipeline import ChatRequest, Gateway, openai_response
from metis.gateway.providers import LiveProvider, MockProvider
from metis.gateway.traces import TraceStore
from metis.llm.client import load_models
from metis.router.artifact import load_artifact

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "web"


class Completion(BaseModel):
    model: str = "takrouter"
    messages: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None


def real_embedder():
    from metis.embed.embedder import Embedder

    s4 = load_config("pipeline")["s4"]
    cand = s4["candidates"][s4["choice"]]
    def build(task: str) -> Embedder:
        return Embedder(cand["name"], cand["revision"], device=s4["device"], path=str(ROOT / cand["path"]), task=task,
                        prompt_name=s4["prompt_name"], merge_adapter=s4["merge_adapter"], max_tokens=s4["max_tokens"],
                        batch_size=s4["batch_size"], max_batch_tokens=s4["max_batch_tokens"])
    model = build(s4["task"])  # one vector for routing and cache (D-121)
    return (lambda t: model.encode([t])[0]), None


def hash_embedder(dim: int):
    """Stand-in for tests and demos without the model: stable random unit vector per text."""
    def embed(text: str) -> np.ndarray:
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
        v = np.random.default_rng(seed).normal(size=dim)
        return v / np.linalg.norm(v)
    return embed


def build_gateway(cfg: dict[str, Any] | None = None, embed=None, cache_embed=None, provider=None) -> Gateway:
    cfg = cfg or load_config("gateway")
    artifact = load_artifact(ROOT / cfg["artifact"])
    if embed is None:
        fake = cfg.get("fake_embedder") or os.environ.get("TAKROUTER_FAKE_EMBED") == "1"
        embed = hash_embedder(artifact.centroids.shape[1]) if fake else None
    if embed is None:
        embed, cache_embed = real_embedder()
    if provider is None:
        provider = LiveProvider() if cfg["provider"] == "live" else MockProvider(cfg["mock"]["latency_ms"])
    c = cfg["cache"]
    cache = SemanticCache(c["theta"], c["ttl_days"], c.get("path"), c.get("semantic", True)) if c.get("enabled") else None
    return Gateway(artifact, provider, embed, cfg, load_models(), TraceStore(ROOT / cfg["traces"]["path"]), cache, cache_embed)


def create_app(gateway: Gateway | None = None) -> FastAPI:
    api = FastAPI(title="TakRouter", version="1.0")
    state: dict[str, Gateway | None] = {"gw": gateway}

    def gw() -> Gateway:
        if state["gw"] is None:
            state["gw"] = build_gateway()
        return state["gw"]

    @api.get("/health")
    def health() -> dict[str, Any]:
        g = gw()
        return {"status": "ok", "product": "TakRouter", "breakers": {m: b.state for m, b in g.breakers.items()},
                "lambda": g.lam, "k": g.artifact.meta.k_star, "provider": type(g.provider).__name__}

    @api.get("/metrics")
    def metrics() -> dict[str, Any]:
        return gw().traces.summary()

    @api.get("/v1/traces")
    def traces(limit: int = 50) -> list[dict[str, Any]]:
        return gw().traces.rows(min(limit, 200))

    @api.post("/v1/chat/completions")
    def chat(body: Completion, x_metis_chatbot: str | None = Header(None), x_metis_session: str | None = Header(None)) -> JSONResponse:
        meta = body.metadata or {}
        req = ChatRequest(body.messages, body.model, x_metis_chatbot or meta.get("chatbot", "default"), x_metis_session or meta.get("session"),
                          has_image=any(isinstance(m.get("content"), list) and any(p.get("type") == "image_url" for p in m["content"] if isinstance(p, dict)) for m in body.messages),
                          wants_json=(body.response_format or {}).get("type") == "json_object", widget_click=bool(meta.get("widget_click")),
                          uses_rag=bool(meta.get("uses_rag")), context_hash=meta.get("context_hash"))
        try:
            result = gw().handle(req)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        status = result.trace["status"]
        if status in ("all_failed", "no_model"):
            return JSONResponse({"error": {"message": "no model is available", "type": "service_unavailable", "trace": result.trace["request_id"]}}, 503)
        return JSONResponse(openai_response(result))

    if WEB.exists():
        @api.get("/")
        def home() -> FileResponse:
            return FileResponse(WEB / "index.html")
        api.mount("/web", StaticFiles(directory=WEB), name="web")
    return api


app = create_app()
