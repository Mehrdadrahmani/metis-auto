import numpy as np
import pytest
from fastapi.testclient import TestClient

from metis.config import load_config
from metis.gateway.app import build_gateway, create_app
from metis.gateway.cache import SemanticCache
from metis.gateway.cache_policy import is_cacheable
from metis.gateway.checks import check_answer
from metis.gateway.failover import Breaker
from metis.gateway.pipeline import ChatRequest
from metis.gateway.providers import MockProvider, Reply
from metis.gateway.traces import TraceStore
from metis.router.route import route

FA = "سلام، لطفا درباره سفر به شیراز راهنمایی کن"


def make(provider=None, **over):
    cfg = load_config("gateway") | {"fake_embedder": True, "lam": None, "use_live_artifact": False,
                                    "auth": {"required": False, "path": ":memory:"}} | over
    cfg.pop("lam")
    cfg["traces"] = {"path": ":memory:"}
    gw = build_gateway(cfg, provider=provider or MockProvider())
    gw.traces = TraceStore()
    return gw


def req(text=FA, **kw):
    return ChatRequest([{"role": "user", "content": text}], **kw)


def test_routing_matches_offline_router():
    gw = make(cache={"enabled": False})
    res = gw.handle(req())
    vec = gw.embed(__import__("metis.data.normalize", fromlist=["normalize"]).normalize(FA))
    assert res.model == route(vec, gw.artifact.meta.models, gw.router, gw.lam).model


def test_one_model_down_no_failed_request():
    for down in load_config("gateway")["mock"]["latency_ms"]:
        gw = make(provider=MockProvider(down={down}), cache={"enabled": False})
        results = [gw.handle(req(f"{FA} {i}")) for i in range(30)]
        assert all(r.trace["status"] == "ok" and r.model != down for r in results)


def test_all_down_clean_503_with_trace():
    gw = make(provider=MockProvider(down=set(load_config("gateway")["mock"]["latency_ms"])), cache={"enabled": False})
    client = TestClient(create_app(gw))
    r = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": FA}]})
    assert r.status_code == 503 and gw.traces.rows()[0]["status"] == "all_failed"


def test_openai_shape_and_concrete_model_bypass():
    gw = make(cache={"enabled": False})
    client = TestClient(create_app(gw))
    r = client.post("/v1/chat/completions", json={"model": "claude-sonnet-5-5", "messages": [{"role": "user", "content": FA}]}).json()
    assert r["model"] == "claude-sonnet-5-5" and r["choices"][0]["message"]["role"] == "assistant"


def test_widget_click_no_llm():
    gw = make(provider=MockProvider(down={"x"}))
    assert gw.handle(req(widget_click=True)).trace["status"] == "workflow"


def test_image_only_vision_models():
    gw = make(cache={"enabled": False})
    assert "deepseek-v4-flash" not in gw.handle(req(has_image=True)).trace["scores"]


def test_breaker_cycle():
    t = [0.0]
    b = Breaker(3, 60, 30, clock=lambda: t[0])
    for _ in range(3):
        b.failure()
    assert b.state == "open" and not b.available()
    t[0] = 31
    assert b.state == "half-open" and b.available()
    b.before_call()
    assert not b.available()
    b.failure()
    assert b.state == "open"
    t[0] = 62
    b.before_call()
    b.success()
    assert b.state == "closed"


@pytest.mark.parametrize("text,finish,lang,js,want", [
    ("  ", "stop", "fa", False, "empty"),
    ("ok", "length", "fa", False, "truncated"),
    ("This is a long answer written in English only.", "stop", "fa", False, "wrong_language"),
    ("not json", "stop", "en", True, "bad_json"),
    ("متأسفم، نمی‌توانم", "stop", "fa", False, "refusal"),
    ("I can't help with that", "stop", "en", False, "refusal"),
    ("این پاسخ کامل و درست است و مشکلی ندارد.", "stop", "fa", False, None),
])
def test_checks(text, finish, lang, js, want):
    assert check_answer(text, finish, lang, js) == want


class Scripted:
    def __init__(self, texts):
        self.texts, self.calls = list(texts), []

    def call(self, model, messages, context):
        self.calls.append(model)
        return Reply(self.texts.pop(0), 10, 10, "stop", 5.0)


def test_repair_then_escalate_capped():
    p = Scripted(["  "] * 10)
    gw = make(provider=p, cache={"enabled": False})
    res = gw.handle(req())
    assert res.trace["escalations"] <= 2 and len(p.calls) <= 4
    assert res.trace["reasons"][0] == "empty"


def test_repair_fixes_without_escalation():
    p = Scripted(["  ", "پاسخ درست و کامل به زبان فارسی اینجاست."])
    gw = make(provider=p, cache={"enabled": False})
    res = gw.handle(req())
    assert res.trace["escalations"] == 0 and p.calls[0] == p.calls[1]


def test_stickiness_keeps_previous_model():
    gw = make(cache={"enabled": False}, stickiness={"enabled": True, "delta": 100})
    gw.session_model["s"] = "gpt-5.6-luna"
    assert gw.handle(req(session="s")).model == "gpt-5.6-luna"


def test_cache_namespace_ttl_threshold():
    t = [0.0]
    c = SemanticCache(0.97, 7, clock=lambda: t[0])
    v = np.ones(4)
    c.store("a", "k", v, "ans", "m")
    assert c.lookup("b", "k", v) is None
    assert c.lookup("a", "k", v)[0] == "hit_exact"
    assert c.lookup("a", "z", v)[0] == "hit_semantic"
    assert c.lookup("a", "z", np.array([1.0, -1, 1, -1])) is None
    t[0] = 8 * 86400
    assert c.lookup("a", "k", v) is None


def test_gateway_cache_hit_second_time_and_no_cross_bot():
    gw = make(cache={"enabled": True, "theta": 0.97, "ttl_days": 7})
    assert gw.handle(req(chatbot="a")).trace["cache"] == "miss"
    assert gw.handle(req(chatbot="a")).trace["cache"] == "hit_exact"
    assert gw.handle(req(chatbot="b")).trace["cache"] == "miss"


@pytest.mark.parametrize("text,first,why", [
    ("شماره من 09123456789 است", True, "personal"),
    ("قیمت امروز چنده", True, "time"),
    ("همین رو توضیح بده", False, "history"),
    ("پایتخت ایران کجاست", True, "ok"),
])
def test_cache_policy(text, first, why):
    assert is_cacheable(text, first)[1] == why


# Chat app (D-125): lambda per request, router and budget endpoints, pages -----------------------
def test_lambda_per_request_moves_the_choice():
    gw = make(cache={"enabled": False})
    humanities = list(gw.artifact.meta.cluster_names).index("Humanities and religion")
    gw.embed = lambda text: gw.artifact.centroids[humanities]
    picked = {lam: gw.handle(req(lam=lam)).model for lam in (0.0, None, 100.0)}
    assert picked == {0.0: "claude-sonnet-5-5", None: "gpt-5.6-luna", 100.0: "gemini-2.5-flash-lite"}


def test_chat_app_endpoints_and_pages():
    gw = make(cache={"enabled": False})
    client = TestClient(create_app(gw))
    info = client.get("/v1/router", params={"lam": 0}).json()
    assert info["lambda"] == 0 and len(info["clusters"]) == gw.artifact.meta.k_star
    assert info["breakpoints"][:3] == [0.009929, 0.027051, 0.044601]
    assert all(m["price_in"] and m["price_out"] for m in info["models"])
    assert client.get("/v1/router", params={"lam": -1}).status_code == 422
    assert client.get("/v1/budget").json() == {"live": False}
    assert client.get("/health").json()["live"] is False
    body = {"messages": [{"role": "user", "content": FA}], "metadata": {"lambda": 0}}
    r = client.post("/v1/chat/completions", json=body).json()["takrouter"]
    assert r["lam"] == 0 and r["cluster_name"] and r["chosen"] and r["tried"]
    bad = {"messages": [{"role": "user", "content": FA}], "metadata": {"lambda": -0.5}}
    assert client.post("/v1/chat/completions", json=bad).status_code == 422
    assert "TakRouter" in client.get("/").text and "site.js" in client.get("/").text
    assert client.get("/results").status_code == 200


def test_budget_refusal_is_a_clear_402():
    from metis.gateway.failover import ProviderError

    class Broke:
        def call(self, model, messages, context):
            raise ProviderError("budget")

    gw = make(provider=Broke(), cache={"enabled": False})
    r = TestClient(create_app(gw)).post("/v1/chat/completions", json={"messages": [{"role": "user", "content": FA}]})
    assert r.status_code == 402 and r.json()["error"]["type"] == "budget_exhausted"
