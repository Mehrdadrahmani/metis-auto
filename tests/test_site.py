"""The website (D-126): accounts, API keys, credit, trace, usage, compare, pages, adding a model."""

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from metis.config import load_config
from metis.gateway.app import PAGES, WEB, build_gateway, create_app
from metis.gateway.auth import Accounts, AuthError
from metis.gateway.providers import MockProvider
from metis.gateway.traces import TraceStore

FA = "سلام، لطفا درباره سفر به شیراز راهنمایی کن"
MSG = {"messages": [{"role": "user", "content": FA}]}


def site(required=True):
    cfg = load_config("gateway") | {"fake_embedder": True, "use_live_artifact": False,
                                    "auth": {"required": required, "path": ":memory:"}, "cache": {"enabled": False}}
    cfg["traces"] = {"path": ":memory:"}
    gw = build_gateway(cfg, provider=MockProvider())
    gw.traces = TraceStore()
    return TestClient(create_app(gw, Accounts(":memory:"))), gw


def signup(client, email, pw="password123", name=""):
    return client.post("/auth/signup", json={"email": email, "password": pw, "name": name})


# ---------------------------------------------------------------- accounts
def test_first_account_is_admin_then_users():
    a = Accounts(":memory:")
    assert a.signup("Owner@Example.com", "password123").role == "admin"
    assert a.signup("b@example.com", "password123").role == "user"
    with pytest.raises(AuthError, match="email_taken"):
        a.signup("owner@example.com", "password123")
    with pytest.raises(AuthError, match="short_password"):
        a.signup("c@example.com", "short")
    with pytest.raises(AuthError, match="bad_login"):
        a.check_password("b@example.com", "wrong-password")
    assert a.check_password("b@example.com", "password123").email == "b@example.com"
    raw = a.db.execute("SELECT pw_hash FROM users").fetchone()[0]
    assert b"password123" not in raw  # only the scrypt hash is stored


def test_login_session_and_chat_needs_auth():
    client, _ = site()
    assert client.post("/v1/chat/completions", json=MSG).status_code == 401
    assert client.get("/auth/me").json()["has_users"] is False
    r = signup(client, "owner@example.com", name="Owner")
    assert r.json()["user"]["role"] == "admin" and "tr_session" in r.cookies
    assert client.post("/v1/chat/completions", json=MSG).status_code == 200
    client.post("/auth/logout")
    assert client.get("/auth/me").json()["user"] is None
    assert client.post("/auth/login", json={"email": "owner@example.com", "password": "nope-nope"}).status_code == 401
    assert client.post("/auth/login", json={"email": "owner@example.com", "password": "password123"}).status_code == 200


def test_api_key_works_and_is_shown_once():
    client, _ = site()
    signup(client, "owner@example.com")
    key = client.post("/auth/keys", json={"name": "bot"}).json()["key"]
    assert key.startswith("tk-") and all(key not in str(k) for k in client.get("/auth/keys").json())
    bare = TestClient(client.app)
    assert bare.post("/v1/chat/completions", json=MSG).status_code == 401
    assert bare.post("/v1/chat/completions", json=MSG, headers={"Authorization": f"Bearer {key}"}).status_code == 200
    kid = client.get("/auth/keys").json()[0]["id"]
    client.delete(f"/auth/keys/{kid}")
    assert bare.post("/v1/chat/completions", json=MSG, headers={"Authorization": f"Bearer {key}"}).status_code == 401


def test_user_credit_runs_out_with_402():
    client, _ = site()
    signup(client, "owner@example.com")
    user = TestClient(client.app)
    uid = signup(user, "u@example.com").json()["user"]["id"]
    client.patch(f"/admin/users/{uid}", json={"credit_usd": 0.0})
    r = user.post("/v1/chat/completions", json=MSG)
    assert r.status_code == 402 and r.json()["error"]["type"] == "credit_exhausted"
    assert user.get("/admin/users").status_code == 403
    client.patch(f"/admin/users/{uid}", json={"credit_usd": 1.0})
    assert user.post("/v1/chat/completions", json=MSG).status_code == 200
    assert client.patch(f"/admin/users/{uid}", json={"credit_usd": -1}).status_code == 400


def test_prefs_trace_and_usage():
    client, _ = site()
    signup(client, "owner@example.com")
    assert client.patch("/auth/me", json={"prefs": {"show_trace": True, "evil": 1}}).json()["user"]["prefs"]["show_trace"] is True
    out = client.post("/v1/chat/completions", json=MSG | {"metadata": {"trace": True, "lambda": 0}}).json()["takrouter"]
    tr = out["trace"]
    assert tr["available"] and tr["cluster"] is not None and tr["attempts"][0]["ok"] and tr["rag"] is False
    assert set(tr["stage_ms"]) >= {"rules", "embed", "route", "call"} and tr["lam"] == 0
    assert "trace" not in client.post("/v1/chat/completions", json=MSG).json()["takrouter"]
    u = client.get("/v1/usage", params={"days": 7}).json()
    assert u["requests"] == 2 and u["premium_usd"] >= u["cost_usd"] and u["days"]
    assert client.get("/v1/stats").json()["requests"] == 2


def test_compare_answers_with_every_model_and_marks_the_pick():
    client, gw = site()
    signup(client, "owner@example.com")
    r = client.post("/v1/compare", json=MSG).json()
    assert {a["model"] for a in r["answers"]} == set(gw.artifact.meta.models)
    assert r["pick"] in gw.artifact.meta.models and all(a["ok"] for a in r["answers"])


def test_every_page_is_served_fresh():
    client, _ = site()
    for path, file in PAGES.items():
        assert (WEB / file).exists(), file
        r = client.get(path)
        assert r.status_code == 200 and "no-store" in r.headers["cache-control"], path
        if file != "index.html":
            assert "/web/assets/site.js" in r.text, path
    assert client.get("/web/assets/site.css").status_code == 200


def test_models_admin_only():
    client, _ = site()
    signup(client, "owner@example.com")
    user = TestClient(client.app)
    signup(user, "u@example.com")
    assert user.get("/v1/models").status_code == 403
    assert user.post("/v1/models", json={"id": "x"}).status_code == 403


# ------------------------------------------------------------ adding a model
def test_register_validates_and_writes_its_own_file(tmp_path, monkeypatch):
    import shutil

    import metis.config
    from metis import onboard
    from metis.llm.client import load_models
    from metis.llm.messages import gen_params

    for name in ("models", "gen_config"):
        shutil.copy(metis.config.CONFIG_DIR / f"{name}.yaml", tmp_path / f"{name}.yaml")
    monkeypatch.setattr(metis.config, "CONFIG_DIR", tmp_path)
    spec = {"id": "new-model-1", "api_path": "/openai/v1", "price_in": 0.1, "price_out": 0.4,
            "rename": {"max_tokens": "max_completion_tokens"}, "add": {"reasoning_effort": "none"}}
    onboard.register(spec)
    assert load_models()["new-model-1"]["role"] == "added"
    params = gen_params("new-model-1", load_config("gen_config"))
    assert params["max_completion_tokens"] == 1024 and params["reasoning_effort"] == "none"
    for bad, code in (({**spec, "id": "Bad Id"}, "bad_id"), (spec, "exists"), ({**spec, "id": "deepseek-v4-flash"}, "exists"),
                      ({**spec, "id": "m2", "api_path": "openai"}, "bad_fields"), ({"id": "m3"}, "bad_fields")):
        with pytest.raises(onboard.OnboardError, match=code):
            onboard.register(bad)
    onboard.unregister("new-model-1")
    assert "new-model-1" not in load_models()


def test_new_model_column_keeps_clusters_and_lambda():
    from metis import onboard
    from metis.router.artifact import load_artifact
    from metis.router.route import route

    base = load_artifact("artifacts/router_v1")
    k = base.meta.k_star
    better = {"model": "deepseek-v4-flash-x", "psi": [0.0] * k, "pass_rate": 1.0, "c_hat": 0.01}
    load_models_backup = onboard.load_models
    onboard.load_models = lambda: {**load_models_backup(), "deepseek-v4-flash-x": {"price_in": 0.01, "price_out": 0.01}}
    try:
        art = onboard.build_artifact(base, [better])
    finally:
        onboard.load_models = load_models_backup
    assert art.meta.models[-1] == "deepseek-v4-flash-x" and art.psi.shape == (k, 5)
    assert np.array_equal(art.centroids, base.centroids) and art.meta.lam == base.meta.lam
    assert np.allclose(art.psi[:, :4], base.psi) and np.allclose(art.c_hat[:4], base.c_hat)
    # Perfect and cheapest: it wins every cluster.
    assert all(route(c, art.meta.models, art.router(), art.meta.lam).model == "deepseek-v4-flash-x" for c in base.centroids)


def test_fingerprint_reproduces_shipped_psi():
    from pathlib import Path

    from metis.onboard import ValidationSet
    from metis.router.artifact import load_artifact

    if not Path("runs/s7/labels_val.parquet").exists():
        pytest.skip("needs the local validation data (runs/)")
    base = load_artifact("artifacts/router_v1")
    v = ValidationSet(base)
    assert np.bincount(v.cluster, minlength=base.meta.k_star).tolist() == base.counts.tolist()
    for i, m in enumerate(base.meta.models):
        loss = v.labels[v.labels["model_id"] == m].set_index("prompt_id")["loss"]
        assert np.allclose(v.fingerprint(loss), base.psi[:, i])
        assert v.abs_cost[m] / v.norm == pytest.approx(base.c_hat[i], abs=1e-9)
    assert isinstance(v.labels, pd.DataFrame)


def test_khayyam_demo_is_separate():
    from pathlib import Path

    from metis import khayyam as kh

    if not (kh.ARTIFACT / "artifact.json").exists() or not kh.DEMO.exists():
        pytest.skip("needs the local Khayyam build (scripts/khayyam_build.py)")
    client, gw = site()
    info = client.get("/v1/khayyam/info").json()
    assert info["models"] != list(gw.artifact.meta.models)  # its own pool, not the chat router's
    assert len(info["clusters"]) == 7  # K = 7, chosen on validation
    best = client.get("/v1/khayyam/info", params={"lam": 0}).json()
    assert best["router"]["accuracy"] >= info["router"]["accuracy"] - 1e-9
    s = client.get("/v1/khayyam/sample", params={"seed": 1}).json()
    assert s["key"] in "1234" and len(s["models"]) == len(info["models"]) and s["router"]["trace"]["cluster"] == s["cluster"]
    assert client.get("/khayyam").status_code == 200
    assert Path("artifacts/router_khayyam/artifact.json").read_text().count("Question") == 0  # numbers and names only


def test_khayyam_chat_asks_own_question():
    from metis import khayyam as kh

    if not (kh.ARTIFACT / "artifact.json").exists():
        pytest.skip("needs the local Khayyam build (scripts/khayyam_build.py)")
    client, _ = site()
    body = {"question": "کدام عدد اول است؟", "choices": ["۴", "۶", "۷", "۹"]}
    assert client.post("/v1/khayyam/ask", json=body).status_code == 401  # sign in first
    signup(client, "kh@x.io")
    out = client.post("/v1/khayyam/ask", json=body).json()
    assert out["live"] is False and out["model"] in out["trace"]["scores"]  # mock provider in tests
    assert out["trace"]["cluster"] is not None
    cheap = client.post("/v1/khayyam/ask", json=body | {"lam": 100}).json()
    assert cheap["trace"]["lam"] == 100
    assert client.post("/v1/khayyam/ask", json=body | {"choices": ["a", "b", "c"]}).status_code == 422
    assert client.get("/khayyam/chat").status_code == 200
