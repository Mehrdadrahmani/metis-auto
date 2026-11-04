"""A user's own provider key (bring your own key): stored encrypted, used for their calls only,
not charged to their credit or our budget, a refused key gives a clear error and never trips the
shared breakers. All $0 (mock provider)."""

from dataclasses import dataclass, field

from fastapi.testclient import TestClient

from metis.config import load_config
from metis.gateway.app import build_gateway, create_app
from metis.gateway.auth import Accounts
from metis.gateway.providers import MockProvider
from metis.gateway.traces import TraceStore

FA = "سلام، لطفا درباره سفر به شیراز راهنمایی کن"
MSG = {"messages": [{"role": "user", "content": FA}]}
KEY = "test-own-key-000000000000000001"  # fake test value
BAD = "test-own-key-refused-0000000002"  # fake test value


@dataclass
class Recording(MockProvider):
    keys: list = field(default_factory=list)

    def call(self, model, messages, context):
        self.keys.append(context.get("api_key"))
        return super().call(model, messages, context)


def site():
    cfg = load_config("gateway") | {"fake_embedder": True, "use_live_artifact": False,
                                    "auth": {"required": True, "path": ":memory:"}, "cache": {"enabled": False}}
    cfg["traces"] = {"path": ":memory:"}
    provider = Recording(rejected_keys={BAD})
    gw = build_gateway(cfg, provider=provider)
    gw.traces = TraceStore()
    accounts = Accounts(":memory:")
    return TestClient(create_app(gw, accounts)), gw, provider, accounts


def signup(client, email):
    assert client.post("/auth/signup", json={"email": email, "password": "password123"}).status_code == 200


def test_key_is_encrypted_and_only_the_tail_is_shown():
    client, _, _, accounts = site()
    signup(client, "owner@example.com")
    signup(client, "user@example.com")
    r = client.put("/auth/provider-key", json={"key": "Bearer " + KEY})
    assert r.status_code == 200 and r.json()["set"] and r.json()["tail"] == KEY[-4:]
    assert KEY not in r.text
    raw = accounts.db.execute("SELECT enc FROM provider_keys").fetchone()[0]
    assert KEY.encode() not in raw
    assert client.get("/auth/me").json()["own_key"]["tail"] == KEY[-4:]
    assert KEY not in client.get("/auth/me").text
    for bad in ("short", "has spaces in the middle of it", "tk-" + "x" * 30):
        assert client.put("/auth/provider-key", json={"key": bad}).status_code == 400
    assert client.delete("/auth/provider-key").json() == {"deleted": True}
    assert client.get("/auth/provider-key").json()["set"] is False


def test_own_key_is_used_and_not_charged_to_credit():
    client, gw, provider, _ = site()
    signup(client, "owner@example.com")
    client.post("/auth/logout")
    signup(client, "user@example.com")
    before = client.get("/auth/me").json()["credit_left_usd"]
    client.put("/auth/provider-key", json={"key": KEY})
    r = client.post("/v1/chat/completions", json=MSG)
    assert r.status_code == 200
    assert provider.keys[-1] == KEY
    assert client.get("/auth/me").json()["credit_left_usd"] == before
    rows = gw.traces.rows()
    assert rows[0]["billing"] == "own_key"
    assert KEY not in str(rows)
    # switched off: back to the service key and the user's credit
    client.patch("/auth/me", json={"prefs": {"use_own_key": False}})
    assert client.post("/v1/chat/completions", json=MSG).status_code == 200
    assert provider.keys[-1] is None and gw.traces.rows()[0]["billing"] == "service"


def test_own_key_bypasses_a_used_up_credit():
    client, _, _, accounts = site()
    signup(client, "owner@example.com")
    client.post("/auth/logout")
    signup(client, "user@example.com")
    accounts.update(2, credit_usd=0.0)
    assert client.post("/v1/chat/completions", json=MSG).status_code == 402
    client.put("/auth/provider-key", json={"key": KEY})
    assert client.post("/v1/chat/completions", json=MSG).status_code == 200


def test_refused_key_is_a_clear_error_and_breakers_stay_closed():
    client, gw, _, _ = site()
    signup(client, "owner@example.com")
    client.put("/auth/provider-key", json={"key": BAD})
    for _ in range(6):
        r = client.post("/v1/chat/completions", json=MSG)
        assert r.status_code == 400 and r.json()["error"]["type"] == "own_key_rejected"
    assert all(b.state == "closed" for b in gw.breakers.values())
    assert client.get("/auth/provider-key").json()["ok"] is False
    t = client.post("/auth/provider-key/test").json()
    assert t["test"] == {"ok": False, "reason": "own_key_rejected", "model": t["test"]["model"]}
    client.put("/auth/provider-key", json={"key": KEY})
    t = client.post("/auth/provider-key/test").json()
    assert t["test"]["ok"] and t["ok"] is True


def test_503_names_the_failure_kinds():
    client, gw, provider, _ = site()
    signup(client, "owner@example.com")
    provider.down = set(gw.artifact.meta.models)
    r = client.post("/v1/chat/completions", json=MSG)
    assert r.status_code == 503 and r.json()["error"]["reasons"] == ["mock_5xx"]


def test_live_provider_own_key_skips_ledger(monkeypatch):
    import metis.llm.client as client_mod
    from metis.gateway.failover import ProviderError
    from metis.gateway.providers import LiveProvider
    from metis.llm.client import AccountBlocked, Response

    seen = {}

    def fake_complete(model, messages, gen=None, permit=None, prompt_id=None, api_key=None, on_delta=None):
        seen.update(permit=permit, api_key=api_key)
        if api_key == BAD:
            raise AccountBlocked("AuthenticationError:401")
        return Response("ok", 5, 1, "stop", 10.0, model)

    monkeypatch.setattr(client_mod, "complete", fake_complete)
    lp = LiveProvider.__new__(LiveProvider)  # no ledger, no budget: they must not be touched
    lp.gen = load_config("gen_config")
    reply = lp.call("deepseek-v4-flash", [{"role": "user", "content": "hi"}], {"api_key": KEY})
    assert reply.text == "ok" and seen == {"permit": None, "api_key": KEY}
    try:
        lp.call("deepseek-v4-flash", [{"role": "user", "content": "hi"}], {"api_key": BAD})
        raise AssertionError("refused key must raise")
    except ProviderError as exc:
        assert exc.kind == "own_key_rejected"
