"""TakRouter: an OpenAI-compatible FastAPI service and its website.

    uv run uvicorn metis.gateway.app:app                          mock answers, free
    TAKROUTER_PROVIDER=live uv run uvicorn metis.gateway.app:app  real Metis models (stage `product`)

Pages: / (home), /chat, /compare, /learn, /docs, /dashboard, /pricing, /how, /login, /account,
/models (admin: add a model), /results (evaluation). Accounts: metis.gateway.auth; the first
account is the admin. API callers use a key from /account (`Authorization: Bearer tk-...`).
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from metis.config import load_config
from metis.data.normalize import normalize
from metis.gateway.auth import Accounts, AuthError, User
from metis.gateway.cache import SemanticCache
from metis.gateway.failover import ProviderError
from metis.gateway.pipeline import ChatRequest, Gateway, openai_response, trace_view, user_text
from metis.gateway.providers import LiveProvider, MockProvider
from metis.gateway.traces import TraceStore
from metis.llm.client import load_models
from metis.router.artifact import load_artifact
from metis.router.route import route

ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "web"
PRODUCT_STAGE = "product"  # configs/budget.yaml: what the website may spend
PREMIUM = "claude-sonnet-5-5"  # "saved compared with sending everything to ..."
COOKIE = "tr_session"
PAGES = {"/": "home.html", "/chat": "chat.html", "/compare": "compare.html", "/learn": "learn.html",
         "/docs": "docs.html", "/dashboard": "dashboard.html", "/pricing": "pricing.html", "/how": "how.html",
         "/login": "login.html", "/account": "account.html", "/models": "models.html", "/results": "index.html",
         "/khayyam": "khayyam.html"}


class Completion(BaseModel):
    model: str = "takrouter"
    messages: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None


class Credentials(BaseModel):
    email: str
    password: str
    name: str = ""


def provider_kind(cfg: dict[str, Any]) -> str:
    return os.environ.get("TAKROUTER_PROVIDER") or cfg["provider"]


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


def artifact_path(cfg: dict[str, Any]) -> Path:
    """The live artifact (with added models) when there is one, else the shipped one."""
    from metis.onboard import LIVE_ARTIFACT

    if cfg.get("use_live_artifact", True) and (LIVE_ARTIFACT / "artifact.json").exists():
        return LIVE_ARTIFACT
    return ROOT / cfg["artifact"]


def build_gateway(cfg: dict[str, Any] | None = None, embed=None, cache_embed=None, provider=None) -> Gateway:
    cfg = cfg or load_config("gateway")
    artifact = load_artifact(artifact_path(cfg))
    if embed is None:
        fake = cfg.get("fake_embedder") or os.environ.get("TAKROUTER_FAKE_EMBED") == "1"
        embed = hash_embedder(artifact.centroids.shape[1]) if fake else None
    if embed is None:
        embed, cache_embed = real_embedder()
    if provider is None:
        provider = LiveProvider(PRODUCT_STAGE) if provider_kind(cfg) == "live" else MockProvider(cfg["mock"]["latency_ms"])
    c = cfg["cache"]
    cache = SemanticCache(c["theta"], c["ttl_days"], c.get("path"), c.get("semantic", True)) if c.get("enabled") else None
    return Gateway(artifact, provider, embed, cfg, load_models(), TraceStore(":memory:" if cfg["traces"]["path"] == ":memory:" else ROOT / cfg["traces"]["path"]), cache, cache_embed)


def error(status: int, kind: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"message": message, "type": kind}}, status)


def create_app(gateway: Gateway | None = None, accounts: Accounts | None = None) -> FastAPI:
    # /docs is the site's developer page; FastAPI's own reference moves to /api-docs.
    api = FastAPI(title="TakRouter", version="1.1", docs_url="/api-docs", redoc_url=None)
    state: dict[str, Any] = {"gw": gateway, "accounts": accounts, "jobs": {}, "vset": None}
    lock = threading.RLock()  # vset() builds the gateway while holding it

    def gw() -> Gateway:
        with lock:
            if state["gw"] is None:
                state["gw"] = build_gateway()
        return state["gw"]

    def auth_required() -> bool:
        return bool(gw().cfg.get("auth", {}).get("required", True))

    def accts() -> Accounts:
        if state["accounts"] is None:
            path = gw().cfg.get("auth", {}).get("path", "runs/gateway/users.sqlite")
            state["accounts"] = Accounts(":memory:" if path == ":memory:" else ROOT / path)
        return state["accounts"]

    # ------------------------------------------------------------ who is calling
    def caller(request: Request, authorization: str | None = Header(None)) -> User | None:
        key = authorization.split(" ", 1)[1].strip() if authorization and authorization.lower().startswith("bearer ") else None
        return accts().key_user(key) or accts().session_user(request.cookies.get(COOKIE))

    def signed_in(user: User | None = Depends(caller)) -> User:
        if user is None:
            raise HTTPException(401, "sign in first")
        return user

    def admin(user: User = Depends(signed_in)) -> User:
        if not user.is_admin:
            raise HTTPException(403, "admins only")
        return user

    def chat_user(user: User | None = Depends(caller)) -> User | None:
        if user is None and auth_required():
            raise HTTPException(401, "sign in first or send an API key")
        return user

    def prices() -> dict[str, dict[str, float]]:
        return {m: {"price_in": v.get("price_in", 0), "price_out": v.get("price_out", 0)} for m, v in gw().models.items()}

    def credit_left(user: User | None) -> float | None:
        """None: no personal limit (admin, or no accounts)."""
        if user is None or user.is_admin:
            return None
        return user.credit_usd - gw().traces.spent(user.id)

    def budget_left() -> float | None:
        g = gw()
        if not isinstance(g.provider, LiveProvider):
            return None
        b = g.provider.budget
        return float(b.config["approved_usd"].get(PRODUCT_STAGE, 0)) - b.cache.spent_usd(PRODUCT_STAGE)

    def spend_gate(user: User | None) -> JSONResponse | None:
        left = budget_left()
        if left is not None and left <= 0.001:
            return error(402, "budget_exhausted", "the spending limit of this service is reached")
        mine = credit_left(user)
        if mine is not None and mine <= 0:
            return error(402, "credit_exhausted", "your credit is used up")
        return None

    # ------------------------------------------------------------------ accounts
    def start(response: Response, user: User) -> dict[str, Any]:
        response.set_cookie(COOKIE, accts().start_session(user), httponly=True, samesite="lax",
                            max_age=14 * 86400, path="/")
        return {"user": user.public()}

    @api.post("/auth/signup")
    def signup(body: Credentials, response: Response) -> dict[str, Any]:
        try:
            return start(response, accts().signup(body.email, body.password, body.name))
        except AuthError as exc:
            raise HTTPException(400, str(exc)) from None

    @api.post("/auth/login")
    def login(body: Credentials, response: Response) -> dict[str, Any]:
        try:
            return start(response, accts().check_password(body.email, body.password))
        except AuthError as exc:
            raise HTTPException(401, str(exc)) from None

    @api.post("/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, Any]:
        token = request.cookies.get(COOKIE)
        if token:
            accts().end_session(token)
        response.delete_cookie(COOKIE, path="/")
        return {"ok": True}

    @api.get("/auth/me")
    def me(user: User | None = Depends(caller)) -> dict[str, Any]:
        if user is None:
            return {"user": None, "has_users": bool(accts().users()), "auth_required": auth_required()}
        left = credit_left(user)
        return {"user": user.public(), "spent_usd": round(gw().traces.spent(user.id), 5),
                "credit_left_usd": None if left is None else round(left, 5), "auth_required": auth_required()}

    @api.patch("/auth/me")
    def update_me(body: dict[str, Any], user: User = Depends(signed_in)) -> dict[str, Any]:
        return {"user": accts().update(user.id, name=body.get("name"), prefs=body.get("prefs")).public()}

    @api.get("/auth/keys")
    def keys(user: User = Depends(signed_in)) -> list[dict[str, Any]]:
        return accts().keys(user)

    @api.post("/auth/keys")
    def new_key(body: dict[str, Any], user: User = Depends(signed_in)) -> dict[str, Any]:
        return {"key": accts().create_key(user, str(body.get("name") or "")), "keys": accts().keys(user)}

    @api.delete("/auth/keys/{key_id}")
    def drop_key(key_id: str, user: User = Depends(signed_in)) -> dict[str, Any]:
        return {"deleted": accts().delete_key(user, key_id)}

    @api.get("/admin/users")
    def users(_: User = Depends(admin)) -> list[dict[str, Any]]:
        t = gw().traces
        return [{**u.public(), "spent_usd": round(t.spent(u.id), 5), "created": u.created} for u in accts().users()]

    @api.patch("/admin/users/{user_id}")
    def edit_user(user_id: int, body: dict[str, Any], me_: User = Depends(admin)) -> dict[str, Any]:
        role = body.get("role")
        if role not in (None, "admin", "user") or (user_id == me_.id and role == "user"):
            raise HTTPException(400, "bad_role")
        credit = body.get("credit_usd")
        if credit is not None and (not isinstance(credit, int | float) or credit < 0):
            raise HTTPException(400, "bad_credit")
        return accts().update(user_id, role=role, credit_usd=credit).public()

    # -------------------------------------------------------------- public info
    @api.get("/health")
    def health() -> dict[str, Any]:
        g = gw()
        return {"status": "ok", "product": "TakRouter", "breakers": {m: b.state for m, b in g.breakers.items()},
                "lambda": g.lam, "k": g.artifact.meta.k_star, "provider": type(g.provider).__name__,
                "live": isinstance(g.provider, LiveProvider), "models": list(g.artifact.meta.models)}

    @api.get("/v1/router")
    def router_info(lam: float | None = Query(None, ge=0)) -> dict[str, Any]:
        """Each cluster's pick at this lambda and the lambdas where picks change (the slider)."""
        from metis.router.explain import describe

        g = gw()
        out = describe(g.artifact, g.lam if lam is None else lam, g.lam)
        for row in out["models"]:  # USD per 1M tokens, for "saved vs the premium model"
            info = g.models.get(row["id"], {})
            row.update(price_in=info.get("price_in"), price_out=info.get("price_out"))
        return out

    @api.get("/v1/stats")
    def stats() -> dict[str, Any]:
        """The home page counter: all requests, no per-user data."""
        u = gw().traces.usage(prices(), PREMIUM)
        return {"requests": u["requests"], "cost_usd": round(u["cost_usd"], 4),
                "saved_usd": round(max(0.0, u["premium_usd"] - u["cost_usd"]), 4), "mix": u["mix"]}

    @api.get("/v1/budget")
    def budget() -> dict[str, Any]:
        """What the website may still spend (live only)."""
        g = gw()
        if not isinstance(g.provider, LiveProvider):
            return {"live": False}
        b = g.provider.budget
        spent = b.cache.spent_usd(PRODUCT_STAGE)
        approved = float(b.config["approved_usd"].get(PRODUCT_STAGE, 0))
        return {"live": True, "spent_usd": round(spent, 4), "approved_usd": approved,
                "left_usd": round(max(0.0, approved - spent), 4)}

    @api.get("/v1/usage")
    def usage(days: int = Query(30, ge=1, le=365), scope: str = "me", user: User = Depends(signed_in)) -> dict[str, Any]:
        """Dashboard numbers: yours, or everyone's for an admin (scope=all)."""
        uid = None if scope == "all" and user.is_admin else user.id
        out = gw().traces.usage(prices(), PREMIUM, uid, time.time() - days * 86400)
        out.update(scope="all" if uid is None else "me", breakers={m: b.state for m, b in gw().breakers.items()},
                   budget=budget(), credit_left_usd=credit_left(user))
        return out

    @api.get("/metrics")
    def metrics(_: User = Depends(admin)) -> dict[str, Any]:
        return gw().traces.summary()

    @api.get("/v1/traces")
    def traces(limit: int = 50, _: User = Depends(admin)) -> list[dict[str, Any]]:
        return gw().traces.rows(min(limit, 200))

    # --------------------------------------------------------------------- chat
    @api.post("/v1/chat/completions")
    def chat(body: Completion, x_metis_chatbot: str | None = Header(None), x_metis_session: str | None = Header(None),
             user: User | None = Depends(chat_user)) -> JSONResponse:
        meta = body.metadata or {}
        lam = meta.get("lambda")
        if lam is not None and (not isinstance(lam, int | float) or lam < 0):
            raise HTTPException(422, "metadata.lambda must be a number >= 0")
        gate = spend_gate(user)
        if gate is not None:
            return gate
        req = ChatRequest(body.messages, body.model, x_metis_chatbot or meta.get("chatbot", "default"), x_metis_session or meta.get("session"),
                          has_image=any(isinstance(m.get("content"), list) and any(p.get("type") == "image_url" for p in m["content"] if isinstance(p, dict)) for m in body.messages),
                          wants_json=(body.response_format or {}).get("type") == "json_object", widget_click=bool(meta.get("widget_click")),
                          uses_rag=bool(meta.get("uses_rag")), context_hash=meta.get("context_hash"), lam=lam,
                          user_id=user.id if user else None)
        try:
            result = gw().handle(req)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        status = result.trace["status"]
        if status == "all_failed" and any(a.get("reason") == "budget" for a in result.attempts):
            return error(402, "budget_exhausted", "the spending limit of this service is reached")
        if status in ("all_failed", "no_model"):
            return JSONResponse({"error": {"message": "no model is available", "type": "service_unavailable", "trace": result.trace["request_id"]}}, 503)
        out = openai_response(result)
        if meta.get("trace"):
            out["takrouter"]["trace"] = trace_view(result)
        return JSONResponse(out)

    @api.post("/v1/compare")
    def compare(body: Completion, user: User | None = Depends(chat_user)) -> JSONResponse:
        """Every model answers the same messages, side by side, and TakRouter's pick is marked."""
        gate = spend_gate(user)
        if gate is not None:
            return gate
        g = gw()
        lam = (body.metadata or {}).get("lambda")
        lam = g.lam if lam is None else float(lam)
        vec = g.embed(normalize(user_text(body.messages)))
        decision = route(vec, g.artifact.meta.models, g.router, lam)

        def one(model: str) -> dict[str, Any]:
            t0 = time.perf_counter()
            try:
                reply = g.provider.call(model, body.messages, {"compare": True})
            except ProviderError as exc:
                return {"model": model, "ok": False, "reason": exc.kind}
            return {"model": model, "ok": True, "text": reply.text, "cost_usd": g.cost(model, reply),
                    "seconds": round(time.perf_counter() - t0, 2), "tokens_in": reply.tokens_in, "tokens_out": reply.tokens_out}

        with ThreadPoolExecutor(len(g.artifact.meta.models)) as pool:
            answers = list(pool.map(one, g.artifact.meta.models))
        cost = sum(a.get("cost_usd", 0) for a in answers)
        g.traces.add({"request_id": f"compare-{time.time()}", "ts": time.time(), "chatbot": "compare", "status": "ok",
                      "served_by": "compare", "cost_usd": cost, "user_id": user.id if user else None,
                      "tokens_in": sum(a.get("tokens_in", 0) for a in answers),
                      "tokens_out": sum(a.get("tokens_out", 0) for a in answers), "cluster": decision.cluster})
        return JSONResponse({"pick": decision.model, "cluster": decision.cluster, "lam": lam,
                             "cluster_name": g.artifact.meta.cluster_names[decision.cluster],
                             "scores": decision.scores, "answers": answers, "cost_usd": cost})

    # ---------------------------------------------------------- add a model
    def vset():
        from metis.onboard import ValidationSet

        base = load_artifact(ROOT / gw().cfg["artifact"])
        with lock:
            if state["vset"] is None:
                state["vset"] = ValidationSet(base)
        return state["vset"]

    def model_rows() -> list[dict[str, Any]]:
        import json as _json

        from metis.onboard import added_models

        g, out = gw(), []
        active = set(g.artifact.meta.models)
        base = load_artifact(ROOT / g.cfg["artifact"]).meta.models
        for m in g.artifact.meta.models + tuple(a["id"] for a in added_models() if a["id"] not in active):
            info = g.models.get(m, {})
            folder = ROOT / "runs/onboard" / m
            job = state["jobs"].get(m)
            status = job.status if job else (_json.loads((folder / "status.json").read_text()) if (folder / "status.json").exists() else None)
            result = _json.loads((folder / "result.json").read_text()) if (folder / "result.json").exists() else None
            out.append({"id": m, "shipped": m in base, "active": m in active, "price_in": info.get("price_in"),
                        "price_out": info.get("price_out"), "vision": info.get("vision"), "api_path": info.get("api_path"),
                        "status": status, "result": result})
        return out

    @api.get("/v1/models")
    def models_list(_: User = Depends(admin)) -> dict[str, Any]:
        g = gw()
        labels = vset().labels
        shipped = {m: round(float(1 - labels[labels["model_id"] == m]["loss"].mean()), 4) for m in labels["model_id"].unique()}
        return {"models": model_rows(), "shipped_pass_rate": shipped, "lambda": g.lam,
                "cluster_names": list(g.artifact.meta.cluster_names), "live": isinstance(g.provider, LiveProvider)}

    @api.post("/v1/models")
    def models_add(body: dict[str, Any], _: User = Depends(admin)) -> dict[str, Any]:
        from metis.onboard import OnboardError, register

        try:
            entry = register(body)
        except OnboardError as exc:
            raise HTTPException(400, str(exc)) from None
        g = gw()
        g.models = load_models()
        if hasattr(g.provider, "budget"):
            g.provider.budget.models = g.models
        return {"model": entry, "estimate": vset().estimate(entry["id"])}

    @api.post("/v1/models/{model_id}/test")
    def models_test(model_id: str, _: User = Depends(admin)) -> dict[str, Any]:
        from metis.onboard import test_call

        if model_id not in load_models():
            raise HTTPException(404, "unknown model")
        return test_call(model_id)

    @api.get("/v1/models/{model_id}/estimate")
    def models_estimate(model_id: str, _: User = Depends(admin)) -> dict[str, Any]:
        if model_id not in load_models():
            raise HTTPException(404, "unknown model")
        return vset().estimate(model_id)

    @api.post("/v1/models/{model_id}/evaluate")
    def models_evaluate(model_id: str, body: dict[str, Any], _: User = Depends(admin)) -> dict[str, Any]:
        """Start the validation run. ``approved_usd`` is the admin's approval for this run."""
        from metis.onboard import Job

        approved = body.get("approved_usd")
        if model_id not in load_models() or model_id in load_artifact(ROOT / gw().cfg["artifact"]).meta.models:
            raise HTTPException(400, "only an added model can be evaluated")
        if not isinstance(approved, int | float) or approved <= 0:
            raise HTTPException(400, "approve an amount first")
        running = state["jobs"].get(model_id)
        if running and running.thread.is_alive():
            raise HTTPException(409, "already running")
        limit = body.get("limit") if isinstance(body.get("limit"), int) else None
        job = Job(model_id, float(approved), vset(), ROOT / "runs/onboard" / model_id, limit=limit).start()
        state["jobs"][model_id] = job
        return job.status

    @api.post("/v1/models/{model_id}/activate")
    def models_activate(model_id: str, _: User = Depends(admin)) -> dict[str, Any]:
        """Serve the router with every evaluated added model that is switched on (this one included)."""
        return set_active(model_id, True)

    @api.post("/v1/models/{model_id}/deactivate")
    def models_deactivate(model_id: str, _: User = Depends(admin)) -> dict[str, Any]:
        return set_active(model_id, False)

    def set_active(model_id: str, on: bool) -> dict[str, Any]:
        import json as _json
        import shutil

        from metis.onboard import LIVE_ARTIFACT, activate

        g = gw()
        base = load_artifact(ROOT / g.cfg["artifact"])
        keep = [m for m in g.artifact.meta.models if m not in base.meta.models and m != model_id]
        if on:
            keep.append(model_id)
        results = []
        for m in keep:
            path = ROOT / "runs/onboard" / m / "result.json"
            if not path.exists():
                raise HTTPException(400, f"{m} has no finished evaluation")
            r = _json.loads(path.read_text())
            if not r.get("complete"):
                raise HTTPException(400, f"{m} was evaluated on part of the set only")
            results.append(r)
        if results:
            art = activate(base, results)
        else:
            shutil.rmtree(LIVE_ARTIFACT, ignore_errors=True)
            art = base
        g.swap(art, load_models())
        return {"models": list(art.meta.models)}

    @api.delete("/v1/models/{model_id}")
    def models_remove(model_id: str, _: User = Depends(admin)) -> dict[str, Any]:
        from metis.onboard import unregister

        if model_id in gw().artifact.meta.models:
            raise HTTPException(400, "switch it off first")
        unregister(model_id)
        return {"removed": model_id}

    # ------------------------------------------------- Khayyam exam demo (separate router)
    def kh_state() -> dict[str, Any]:
        """The Khayyam router, its replay gateway and the stored test answers; loaded once."""
        import json as _json

        import pandas as pd

        from metis import khayyam as kh

        with lock:
            if state.get("kh") is None:
                if not (kh.ARTIFACT / "artifact.json").exists() or not kh.DEMO.exists():
                    raise HTTPException(503, "khayyam demo not built: run scripts/khayyam_build.py")
                demo = pd.read_parquet(kh.DEMO)
                state["kh"] = {"gw": kh.build_gateway(), "demo": demo, "vecs": np.load(kh.OUT / "test_vecs.npy"),
                               "summary": _json.loads(kh.summary_path().read_text(encoding="utf-8")),
                               "by_id": {i: g for i, g in demo.groupby("id")}}
        return state["kh"]

    @api.get("/v1/khayyam/info")
    def kh_info(lam: float | None = Query(None, ge=0)) -> dict[str, Any]:
        """Per subject and overall on the 1,100 test questions, at this lambda (stored answers)."""
        from metis.router.explain import breakpoints
        from metis.router.route import cluster_choices

        s = kh_state()
        art, demo, summ = s["gw"].artifact, s["demo"], s["summary"]
        lam = art.meta.lam if lam is None else lam
        pick = cluster_choices(art.psi, art.c_hat, np.array([lam]))[0]
        models = list(art.meta.models)
        first = demo.drop_duplicates("id")[["id", "cluster"]]
        chosen = first.assign(model=[models[pick[c]] for c in first.cluster])
        hit = chosen.merge(demo[["id", "model", "correct"]], on=["id", "model"])
        return {"lambda": lam, "default_lambda": art.meta.lam, "breakpoints": breakpoints(art), "models": models,
                "c_hat": art.c_hat.tolist(), "usd_per_call": summ["usd_per_call"],
                "router": {"accuracy": float(hit.correct.mean()), "cost": float(np.mean([art.c_hat[pick[c]] for c in first.cluster]))},
                "single": summ["test_accuracy"], "curve": summ["curve"], "area": {k: summ[k] for k in ("area_router", "area_zero", "area_gain", "area_gain_ci")},
                "gateway_replay": summ["gateway_replay"], "n": {"val": summ["n_val"], "test": summ["n_test"], "clusters": summ["n_cluster_fit"]},
                "clusters": [{**c, "pick": models[pick[c["cluster"]]]} for c in summ["clusters"]]}

    @api.get("/v1/khayyam/sample")
    def kh_sample(lam: float | None = Query(None, ge=0), cluster: int | None = None, seed: int | None = None) -> dict[str, Any]:
        """A random test question through the Khayyam gateway, with every model's stored answer."""
        import random

        from metis import khayyam as kh

        s = kh_state()
        demo = s["demo"]
        pool = demo if cluster is None else demo[demo.cluster == cluster]
        if pool.empty:
            raise HTTPException(404, "no question in that subject")
        qid = random.Random(seed).choice(sorted(pool.id.unique()))
        rows = s["by_id"][qid]
        r0 = rows.iloc[0]
        req = ChatRequest([{"role": "system", "content": kh.SYSTEM}, {"role": "user", "content": r0.q}], "takrouter", "khayyam",
                          None, prompt_id=qid, vector=s["vecs"][int(r0.pos)], lam=lam)
        out = s["gw"].handle(req)
        return {"id": qid, "question": r0.q, "choices": list(r0.choices), "key": r0.key, "course": r0.course, "cluster": int(r0.cluster),
                "router": {"model": out.model, "answer": kh.parse(out.text), "correct": kh.parse(out.text) == r0.key,
                           "trace": trace_view(out)},
                "models": [{"model": r.model, "answer": r.answer, "correct": bool(r.correct), "cut": bool(r.cut), "usd": float(r.usd),
                            "ms": None if r.ms is None or r.ms != r.ms else float(r.ms)} for r in rows.itertuples()]}

    # -------------------------------------------------------------------- pages
    if WEB.exists():
        fresh = {"Cache-Control": "no-cache, no-store, must-revalidate"}  # browsers always load the current site

        def page(file: str):
            return lambda: FileResponse(WEB / file, headers=fresh)

        for path, file in PAGES.items():
            if (WEB / file).exists():
                api.add_api_route(path, page(file), methods=["GET"], include_in_schema=False)
        api.mount("/web", StaticFiles(directory=WEB), name="web")
    return api


app = create_app()
