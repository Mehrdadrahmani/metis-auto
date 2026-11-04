"""Streaming replies (server-sent events): same routing, budget, checks and trace as a normal reply;
a backup model starts over with a `reset` event; errors arrive as an error event. All $0."""

import json
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from metis.config import load_config
from metis.gateway.app import build_gateway, create_app
from metis.gateway.auth import Accounts
from metis.gateway.providers import MockProvider
from metis.gateway.traces import TraceStore

FA = "سلام، لطفا درباره سفر به شیراز راهنمایی کن"
MSG = {"messages": [{"role": "user", "content": FA}], "stream": True}


def site(provider=None):
    cfg = load_config("gateway") | {"fake_embedder": True, "use_live_artifact": False,
                                    "auth": {"required": False, "path": ":memory:"}, "cache": {"enabled": False}}
    cfg["traces"] = {"path": ":memory:"}
    gw = build_gateway(cfg, provider=provider or MockProvider())
    gw.traces = TraceStore()
    return TestClient(create_app(gw, Accounts(":memory:"))), gw


def events(response):
    out = []
    for line in response.text.splitlines():
        if line.startswith("data: "):
            out.append(line[6:] if line[6:] == "[DONE]" else json.loads(line[6:]))
    return out


def test_stream_pieces_add_up_to_the_answer_and_end_with_the_result():
    client, gw = site()
    r = client.post("/v1/chat/completions", json=MSG)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    ev = events(r)
    assert ev[-1] == "[DONE]"
    final = ev[-2]
    assert final["choices"][0]["finish_reason"] == "stop" and final["takrouter"]["served_by"] == final["model"]
    text = "".join(e["choices"][0]["delta"].get("content", "") for e in ev[:-2])
    assert text == f"پاسخ نمایشی از {final['model']}. این متن واقعی نیست."
    assert len([e for e in ev[:-2] if e["choices"][0]["delta"].get("content")]) > 3  # really in pieces
    assert gw.traces.rows()[0]["status"] == "ok"


def test_backup_model_starts_over_with_reset():
    class HalfThenFail(MockProvider):
        def call(self, model, messages, context):
            if not getattr(self, "failed", False):
                self.failed = True
                context["on_delta"]("نیمه‌ی ")
                from metis.gateway.failover import ProviderError
                raise ProviderError("APIConnectionError")
            return super().call(model, messages, context)

    client, _ = site(HalfThenFail())
    ev = events(client.post("/v1/chat/completions", json=MSG))
    kinds = ["reset" if e != "[DONE]" and e.get("takrouter", {}).get("event") == "reset" else "x" for e in ev]
    assert "reset" in kinds
    after = ev[kinds.index("reset") + 1:-2]
    assert "".join(e["choices"][0]["delta"].get("content", "") for e in after).startswith("پاسخ نمایشی")
    assert len(ev[-2]["takrouter"]["tried"]) == 2


def test_errors_arrive_as_an_error_event():
    client, gw = site()
    gw.provider.down = set(gw.artifact.meta.models)
    ev = events(client.post("/v1/chat/completions", json=MSG))
    assert ev[-2]["error"]["status"] == 503 and ev[-2]["error"]["reasons"] == ["mock_5xx"] and ev[-1] == "[DONE]"


def test_normal_reply_unchanged_without_stream():
    client, _ = site()
    r = client.post("/v1/chat/completions", json={"messages": MSG["messages"]})
    assert r.headers["content-type"].startswith("application/json") and r.json()["choices"][0]["message"]["content"]


def test_client_streams_a_paid_call_and_still_counts_tokens(monkeypatch):
    from metis.llm import client
    from metis.llm.client import Permit

    def chunk(text=None, finish=None, usage=None):
        return NS(model="deepseek-v4-flash", usage=usage,
                  choices=[NS(delta=NS(content=text), finish_reason=finish)] if text or finish else [])

    fake = [chunk("سلام "), chunk("دنیا"), chunk(finish="stop"),
            chunk(usage=NS(prompt_tokens=11, completion_tokens=3, prompt_tokens_details=None, completion_tokens_details=None,
                           model_dump=dict))]
    seen = {}
    monkeypatch.setattr(client, "_send", lambda *a, **k: seen.update(stream=k.get("stream")) or iter(fake))
    monkeypatch.setenv("METIS_BASE_URL", "http://example.invalid")
    monkeypatch.setenv("METIS_API_KEY", "test-not-a-real-key-000000")
    monkeypatch.delenv("METIS_MOCK", raising=False)
    pieces = []
    r = client.complete("deepseek-v4-flash", [{"role": "user", "content": "hi"}], {}, Permit("t", 0.01), on_delta=pieces.append)
    assert seen["stream"] is True and pieces == ["سلام ", "دنیا"]
    assert (r.text, r.tokens_in, r.tokens_out, r.finish_reason, r.usage_reported) == ("سلام دنیا", 11, 3, "stop", True)


def test_cached_answer_is_streamed_whole():
    cfg = load_config("gateway") | {"fake_embedder": True, "use_live_artifact": False, "auth": {"required": False, "path": ":memory:"}}
    cfg["traces"] = {"path": ":memory:"}
    cfg["cache"] = {**cfg["cache"], "enabled": True, "path": None}
    gw = build_gateway(cfg, provider=MockProvider())
    gw.traces = TraceStore()
    client = TestClient(create_app(gw, Accounts(":memory:")))
    msg = {"messages": [{"role": "user", "content": "پایتخت فرانسه کجاست؟"}], "stream": True}
    first = events(client.post("/v1/chat/completions", json=msg))
    second = events(client.post("/v1/chat/completions", json=msg))
    assert second[-2]["takrouter"]["cache"].startswith("hit")
    text = lambda ev: "".join(e["choices"][0]["delta"].get("content", "") for e in ev[:-2])
    assert text(second) == text(first) and text(first)


def test_provider_without_streaming_falls_back_to_a_normal_call(monkeypatch):
    from metis.llm import client
    from metis.llm.client import Permit

    plain = NS(model="m", usage=NS(prompt_tokens=5, completion_tokens=2, prompt_tokens_details=None,
                                   completion_tokens_details=None, model_dump=dict),
               choices=[NS(message=NS(content="سلام دنیا"), finish_reason="stop")])
    calls = []

    def fake_send(*a, **k):
        calls.append(k.get("stream", False))
        if k.get("stream"):
            raise RuntimeError("stream not supported")
        return plain

    monkeypatch.setattr(client, "_send", fake_send)
    monkeypatch.setenv("METIS_BASE_URL", "http://example.invalid")
    monkeypatch.setenv("METIS_API_KEY", "test-not-a-real-key-000000")
    monkeypatch.delenv("METIS_MOCK", raising=False)
    pieces = []
    r = client.complete("deepseek-v4-flash", [{"role": "user", "content": "hi"}], {}, Permit("t", 0.01), on_delta=pieces.append)
    assert calls == [True, False] and "".join(pieces) == "سلام دنیا" and r.tokens_out == 2
