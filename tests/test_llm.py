"""WP-04 step 11: cache, budget guard, runner, outgoing guard, mock mode. No network."""

from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from typing import ClassVar

import pytest

from metis import llm  # noqa: F401
from metis.config import load_config
from metis.llm import client, stage
from metis.llm.budget import Budget, BudgetRefused, call_cost
from metis.llm.callcache import CallCache, cache_key, get_or_call
from metis.llm.client import (
    AccountBlocked,
    CallFailed,
    ModelNotReadyError,
    NoPermitError,
    OutgoingSecretError,
    Permit,
    Response,
    complete,
)
from metis.llm.runner import BatchReport, anomaly, run_batch

FAKE_KEY = "sk-" + "abcd1234" * 4
TEST_VALUE = "local"
MODELS = {
    "cheap": {"id": "cheap", "api_name": "cheap-1", "price_in": 1.0, "price_out": 2.0},
    "unpriced": {"id": "unpriced", "api_name": "x", "price_in": None, "price_out": None},
}
LIMITS = load_config("budget")["anomalies"]


def config(approved: float = 0, cap: float = 60) -> dict:
    return {"hard_cap_usd": cap, "approved_usd": {"pilot": approved, "live": approved}}


def msgs(text: str = "hello") -> list[dict]:
    return [{"role": "user", "content": text}]


def fake_response(tokens_in=1000, tokens_out=500, finish="stop", usage=True, reasoning=0):
    return Response("ok", tokens_in, tokens_out, finish, 1.0, "v1",
                    reasoning_tokens=reasoning, usage_reported=usage)


class Sender:
    """Stands in for ``complete`` and counts real sends."""

    def __init__(self, response=None, fail_with=None):
        self.calls = 0
        self.response = response or fake_response()
        self.fail_with = fail_with

    def __call__(self, model_id, messages, gen_params, permit=None, prompt_id=None):
        assert isinstance(permit, Permit)
        self.calls += 1
        if self.fail_with:
            raise CallFailed(self.fail_with)
        return self.response


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("METIS_TRACING", "0")
    monkeypatch.setenv("METIS_MOCK", "0")
    monkeypatch.setenv("METIS_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.delenv("METIS_API_KEY", raising=False)


@pytest.fixture
def cache(tmp_path):
    c = CallCache(tmp_path / "calls.sqlite")
    yield c
    c.close()


def call(cache, budget, send, text="hello", estimate=0.01, **kw):
    return get_or_call(cache, budget, "pilot", "cheap", msgs(text), {"max_tokens": 10}, "cfg",
                       estimate, send, **kw)


# Cache ---------------------------------------------------------------------------------------


def test_key_is_stable_and_sensitive():
    a = cache_key("m", "n", msgs(), {"a": 1, "b": 2}, "c")
    assert a == cache_key("m", "n", msgs(), {"b": 2, "a": 1}, "c")
    assert a != cache_key("m", "n", msgs("other"), {"a": 1, "b": 2}, "c")
    assert a != cache_key("m", "n2", msgs(), {"a": 1, "b": 2}, "c")
    assert a != cache_key("m", "n", msgs(), {"a": 1, "b": 2}, "c2")


def test_mock_and_real_keys_differ(monkeypatch):
    real = cache_key("m", "n", msgs(), {}, "c")
    monkeypatch.setenv("METIS_MOCK", "1")
    assert cache_key("m", "n", msgs(), {}, "c") != real


def test_hit_does_not_pay_twice(cache):
    budget, send = Budget(cache, config(1), MODELS), Sender()
    first = call(cache, budget, send)
    second = call(cache, budget, send)
    assert (first.from_cache, second.from_cache, send.calls) == (False, True, 1)
    assert first.cost_usd == pytest.approx(0.002)
    assert cache.spent_usd() == pytest.approx(0.002)


def test_cache_hit_needs_no_budget(cache):
    call(cache, Budget(cache, config(1), MODELS), Sender())
    assert call(cache, Budget(cache, config(0), MODELS), Sender()).from_cache


def test_failed_call_retried_only_on_flag(cache):
    budget, bad = Budget(cache, config(1), MODELS), Sender(fail_with="Timeout")
    assert call(cache, budget, bad).status == "failed"
    stored = call(cache, budget, bad)
    assert (stored.status, stored.from_cache, stored.error_kind) == ("failed", True, "Timeout")
    assert bad.calls == 1
    good = Sender()
    assert call(cache, budget, good, retry_failed=True).status == "ok"
    assert call(cache, budget, good).from_cache


# Budget --------------------------------------------------------------------------------------


def test_shipped_config_allows_only_approved_stages(cache):
    """Pilot (D-094) and generation (owner "go", WP-12) have limits; the rest are refused."""
    cfg = load_config("budget")
    assert cfg["hard_cap_usd"] == 60
    assert set(cfg["approved_usd"]) == {"pilot", "gen_main", "judge_main", "cache_labels", "live", "khayyam"}
    assert cfg["approved_usd"]["pilot"] == 10
    assert cfg["approved_usd"]["gen_main"] == 21.5
    assert cfg["approved_usd"]["judge_main"] == 3
    budget = Budget(cache, cfg, MODELS)
    budget.guard("pilot", 0.0001)
    with pytest.raises(BudgetRefused):
        budget.guard("pilot", 10.01)
    with pytest.raises(BudgetRefused):
        budget.guard("gen_main", 21.51)
    with pytest.raises(BudgetRefused):
        budget.guard("judge_main", 3.01)
    for locked in ("cache_labels", "live", "khayyam"):
        with pytest.raises(BudgetRefused):
            budget.guard(locked, 0.0001)


def test_stage_limit_counts_spend(cache):
    budget, send = Budget(cache, config(0.003), MODELS), Sender()
    call(cache, budget, send, "a", estimate=0.002)
    with pytest.raises(BudgetRefused, match="stage pilot"):
        call(cache, budget, send, "b", estimate=0.002)
    assert send.calls == 1


def test_hard_cap_beats_stage_approval(cache):
    with pytest.raises(BudgetRefused, match="hard cap"):
        Budget(cache, config(100, cap=1), MODELS).guard("pilot", 2)


def test_in_flight_calls_are_reserved(cache):
    budget = Budget(cache, config(1), MODELS)
    permit = budget.guard("pilot", 0.8)
    with pytest.raises(BudgetRefused):
        budget.guard("pilot", 0.8)
    budget.release(permit)
    budget.guard("pilot", 0.8)


def test_unknown_stage_and_zero_estimate_refused(cache):
    budget = Budget(cache, config(1), MODELS)
    with pytest.raises(BudgetRefused):
        budget.guard("nope", 0.1)
    with pytest.raises(BudgetRefused):
        budget.guard("pilot", 0)


def test_missing_usage_books_the_estimate(cache):
    budget = Budget(cache, config(1), MODELS)
    result = call(cache, budget, Sender(fake_response(0, 0, usage=False)), estimate=0.05)
    assert result.cost_usd == 0.05 and cache.spent_usd() == pytest.approx(0.05)


def test_estimate_and_missing_price(cache):
    budget = Budget(cache, config(1), MODELS)
    plan = [{"model_id": "cheap", "calls": 10, "tokens_in": 1000, "tokens_out": 500}]
    assert budget.estimate("pilot", plan) == pytest.approx(0.02)
    with pytest.raises(ModelNotReadyError):
        call_cost(MODELS["unpriced"], 1, 1)


def test_ledger_report(cache):
    budget = Budget(cache, config(1), MODELS)
    call(cache, budget, Sender())
    report = budget.ledger_report()
    assert "| pilot | 1 | 0 | 1000 | 500 | 0.0020 |" in report and "Spent $0.0020" in report


# Client --------------------------------------------------------------------------------------


def test_outgoing_guard_blocks_key_and_hides_it(monkeypatch):
    monkeypatch.setenv("METIS_MOCK", "1")
    with pytest.raises(OutgoingSecretError) as err:
        complete("cheap", msgs(f"my key {FAKE_KEY}"), prompt_id="p7")
    assert "p7" in str(err.value) and FAKE_KEY not in str(err.value)


def test_guard_sees_nested_content_and_runs_before_send(monkeypatch):
    monkeypatch.setattr(client, "_send", lambda *a: pytest.fail("sent"))
    nested = [{"role": "user", "content": [{"type": "text", "text": FAKE_KEY}]}]
    with pytest.raises(OutgoingSecretError):
        complete("cheap", nested, permit=Permit("pilot", 0.1))


def test_redacted_messages_pass_guard():
    clean = client.redact_messages(msgs(f"my key {FAKE_KEY}"))
    assert FAKE_KEY not in str(clean)
    client.check_outgoing(clean)


def test_real_call_needs_permit(monkeypatch):
    monkeypatch.setattr(client, "_send", lambda *a: pytest.fail("sent"))
    with pytest.raises(NoPermitError):
        complete("deepseek-v4-flash", msgs())


def test_real_call_needs_api_name(monkeypatch):
    monkeypatch.setattr(client, "_send", lambda *a: pytest.fail("sent"))
    monkeypatch.setattr(client, "load_models", lambda: {"m": {"api_name": None}})
    with pytest.raises(ModelNotReadyError):
        complete("m", msgs(), permit=Permit("pilot", 0.1))


def test_parse_and_failure_kind_keep_no_content(monkeypatch):
    usage = SimpleNamespace(
        prompt_tokens=7, completion_tokens=3,
        prompt_tokens_details=SimpleNamespace(cached_tokens=2),
        completion_tokens_details=SimpleNamespace(reasoning_tokens=1),
    )
    choice = SimpleNamespace(message=SimpleNamespace(content="hi"), finish_reason="stop")
    raw = SimpleNamespace(usage=usage, choices=[choice], model="ver-1")
    monkeypatch.setattr(client, "_send", lambda *a: raw)
    monkeypatch.setattr(client, "load_models", lambda: {"m": {"api_name": "n", "api_path": ""}})
    monkeypatch.setenv("METIS_BASE_URL", "http://unused")
    monkeypatch.setenv("METIS_API_KEY", "unused")
    r = complete("m", msgs(), permit=Permit("pilot", 0.1))
    assert (r.tokens_in, r.tokens_out, r.cached_tokens, r.reasoning_tokens) == (7, 3, 2, 1)
    assert r.model_version == "ver-1"

    def boom(*a):
        err = RuntimeError("echo of secret prompt")
        err.status_code = 400
        raise err

    monkeypatch.setattr(client, "_send", boom)
    with pytest.raises(CallFailed) as err:
        complete("m", msgs(), permit=Permit("pilot", 0.1))
    assert str(err.value) == "RuntimeError:400" and err.value.__cause__ is None


class FakeMetis(BaseHTTPRequestHandler):
    """Local OpenAI-style endpoint: answers `script` status codes in order, then 200."""

    script: ClassVar[list[int]] = []
    bodies: ClassVar[list[dict]] = []
    auth: ClassVar[list[str]] = []
    paths: ClassVar[list[str]] = []

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        type(self).bodies.append(json.loads(self.rfile.read(length)))
        type(self).auth.append(self.headers.get("authorization", ""))
        type(self).paths.append(self.path)
        code = type(self).script.pop(0) if type(self).script else 200
        body = {
            "id": "1", "object": "chat.completion", "created": 1, "model": "served-v2",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": "real answer"}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16,
                      "prompt_tokens_details": {"cached_tokens": 4},
                      "completion_tokens_details": {"reasoning_tokens": 2}},
        } if code == 200 else {"error": {"message": "nope", "type": "x"}}
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_metis(monkeypatch):
    FakeMetis.script, FakeMetis.bodies, FakeMetis.auth, FakeMetis.paths = [], [], [], []
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeMetis)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("METIS_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("METIS_API_KEY", TEST_VALUE)
    monkeypatch.setattr(client, "load_models", lambda: {"m": {"api_name": "served", "api_path": "/route"}})
    yield FakeMetis
    server.shutdown()


def test_wire_path_through_litellm(fake_metis):
    r = complete("m", msgs(), {"max_tokens": 9, "temperature": 0}, Permit("pilot", 0.1))
    assert (r.text, r.tokens_in, r.tokens_out) == ("real answer", 11, 5)
    assert (r.cached_tokens, r.reasoning_tokens) == (4, 2)
    assert (r.model_version.endswith("served-v2"), r.finish_reason) == (True, "stop")
    assert fake_metis.bodies[0]["model"] == "served"
    assert fake_metis.bodies[0]["max_tokens"] == 9
    assert fake_metis.auth[0].split()[-1] == TEST_VALUE
    assert fake_metis.paths[0] == "/v1/route/chat/completions"


def test_one_retry_on_429_then_success(fake_metis):
    fake_metis.script = [429]
    assert complete("m", msgs(), permit=Permit("pilot", 0.1)).text == "real answer"
    assert len(fake_metis.bodies) == 2


def test_gives_up_after_one_retry(fake_metis):
    fake_metis.script = [500, 500, 500]
    with pytest.raises(CallFailed):
        complete("m", msgs(), permit=Permit("pilot", 0.1))
    assert len(fake_metis.bodies) == 2


def test_no_retry_on_400(fake_metis):
    fake_metis.script = [400]
    with pytest.raises(CallFailed):
        complete("m", msgs(), permit=Permit("pilot", 0.1))
    assert len(fake_metis.bodies) == 1


def test_missing_env_is_not_a_failed_call(monkeypatch):
    monkeypatch.setattr(client, "load_dotenv", lambda: None)
    monkeypatch.delenv("METIS_BASE_URL", raising=False)
    monkeypatch.setattr(client, "load_models", lambda: {"m": {"api_name": "n", "api_path": ""}})
    with pytest.raises(ModelNotReadyError):
        complete("m", msgs(), permit=Permit("pilot", 0.1))


def test_retry_rule():
    assert client._is_retryable(SimpleNamespace(status_code=429))
    assert client._is_retryable(SimpleNamespace(status_code=503))
    assert not client._is_retryable(SimpleNamespace(status_code=400))


# Mock mode -----------------------------------------------------------------------------------


def test_mock_is_deterministic_with_realistic_length(monkeypatch):
    monkeypatch.setenv("METIS_MOCK", "1")
    assert complete("cheap", msgs("a")).text == complete("cheap", msgs("a")).text
    sizes = [complete("cheap", msgs(str(i))).tokens_out for i in range(2000)]
    assert 150 < sum(sizes) / len(sizes) < 200


def test_mock_respects_max_tokens(monkeypatch):
    monkeypatch.setenv("METIS_MOCK", "1")
    r = complete("cheap", msgs(), {"max_tokens": 1})
    assert (r.tokens_out, r.finish_reason) == (1, "length")


def test_mock_store_is_a_separate_file(monkeypatch):
    from metis.llm.callcache import default_path

    real = default_path()
    monkeypatch.setenv("METIS_MOCK", "1")
    assert default_path() != real


def mock_batch(cache, budget, n=60, **kw):
    def fn(i):
        return get_or_call(cache, budget, "pilot", "cheap", client.redact_messages(msgs(f"p{i}")),
                           {}, "cfg", 0.0, complete, prompt_id=str(i))

    return run_batch("pilot", range(n), fn, LIMITS, **kw)


def test_mock_batch_second_run_makes_no_new_calls(monkeypatch, cache):
    monkeypatch.setenv("METIS_MOCK", "1")
    budget = Budget(cache, config(0), MODELS)
    first = mock_batch(cache, budget)
    second = mock_batch(cache, budget)
    assert (first.new_calls, first.done, first.stopped) == (60, 60, False)
    assert (second.new_calls, second.cache_hits) == (0, 60)


# Runner --------------------------------------------------------------------------------------


class Crash(Exception):
    pass


@pytest.mark.parametrize("concurrency", [1, 4])
def test_resume_after_crash_at_item_37(cache, concurrency):
    budget, send = Budget(cache, config(1), MODELS), Sender()

    def fn(i, crash=True):
        if crash and i == 37:
            raise Crash
        return call(cache, budget, send, f"p{i}", estimate=0.002)

    with pytest.raises(Crash):
        run_batch("pilot", range(60), fn, LIMITS, concurrency=concurrency)
    paid = send.calls
    assert 37 <= paid < 60
    report = run_batch("pilot", range(60), lambda i: fn(i, crash=False), LIMITS,
                       concurrency=concurrency)
    assert send.calls == 60
    assert (report.new_calls, report.cache_hits, report.done) == (60 - paid, paid, 60)


def test_empty_balance_stops_stores_nothing_and_resumes(cache):
    budget, send = Budget(cache, config(1), MODELS), Sender()
    blocked = {"on": False}

    def fn(i):
        if blocked["on"] or i == 10:
            blocked["on"] = True
            raise AccountBlocked("AuthenticationError:401")
        return call(cache, budget, send, f"p{i}", estimate=0.002)

    report = run_batch("pilot", range(30), fn, LIMITS, concurrency=1)
    assert report.stopped and "account" in report.stopped_reason
    assert (report.done, send.calls) == (10, 10)
    blocked["on"] = None
    again = run_batch(
        "pilot", range(30),
        lambda i: call(cache, budget, send, f"p{i}", estimate=0.002), LIMITS, concurrency=1,
    )
    assert not again.stopped
    assert (again.cache_hits, again.new_calls, send.calls) == (10, 20, 30)


@pytest.mark.parametrize("code,text,expected", [
    (401, "bad key", True), (402, "", True), (403, "", True),
    (429, "insufficient_quota", True), (429, "slow down", False), (500, "balance", False),
])
def test_account_problem_detection(code, text, expected):
    exc = Exception(text)
    exc.status_code = code
    assert client._is_account_problem(exc) is expected


def test_stops_on_failures(cache):
    budget = Budget(cache, config(1), MODELS)
    send = Sender(fail_with="Timeout")
    report = run_batch("pilot", range(200),
                       lambda i: call(cache, budget, send, f"p{i}"), LIMITS, concurrency=1)
    assert report.stopped and "failures" in report.stopped_reason
    assert report.done == LIMITS["min_calls"]


def test_stops_on_cost_over_twice_estimate(cache):
    budget = Budget(cache, config(1), MODELS)
    send = Sender(fake_response(1000, 500))
    report = run_batch("pilot", range(200), lambda i: call(cache, budget, send, f"p{i}"),
                       LIMITS, concurrency=1, est_cost_per_call=0.0005)
    assert report.stopped and "cost per call" in report.stopped_reason


def test_budget_refusal_stops_batch(cache):
    budget, send = Budget(cache, config(0), MODELS), Sender()
    with pytest.raises(BudgetRefused):
        run_batch("pilot", range(5), lambda i: call(cache, budget, send, f"p{i}"), LIMITS)
    assert send.calls == 0


@pytest.mark.parametrize(
    ("fields", "word"),
    [
        ({"truncated": 3}, "truncated"),
        ({"tokens_out": 100, "reasoning_tokens": 11}, "reasoning"),
    ],
)
def test_other_anomalies(fields, word):
    report = BatchReport("pilot", 20, new_calls=20, **fields)
    assert word in anomaly(report, LIMITS, None)


def test_no_verdict_on_a_small_sample():
    assert anomaly(BatchReport("pilot", 5, new_calls=5, failed_new=5), LIMITS, None) is None


def test_progress_output_has_no_content(monkeypatch, cache, capsys):
    monkeypatch.setenv("METIS_MOCK", "1")
    mock_batch(cache, Budget(cache, config(0), MODELS), n=30)
    out = capsys.readouterr().out
    assert "lorem" not in out and "p29" not in out


# MLflow --------------------------------------------------------------------------------------


def test_planted_key_never_reaches_mlflow(monkeypatch, cache, tmp_path):
    folder = tmp_path / "mlflow"
    monkeypatch.setenv("METIS_MOCK", "1")
    monkeypatch.setenv("METIS_TRACING", "1")
    monkeypatch.setenv("METIS_MLFLOW_DIR", str(folder))
    budget = Budget(cache, config(0), MODELS)

    def fn(i):
        clean = client.redact_messages(msgs(f"prompt {i} key {FAKE_KEY}"))
        return get_or_call(cache, budget, "pilot", "cheap", clean, {}, "cfg", 0.0, complete)

    report = run_batch("pilot", range(30), fn, LIMITS)
    assert report.new_calls == 30
    with pytest.raises(OutgoingSecretError):
        complete("cheap", msgs(FAKE_KEY))

    store = (folder / "mlflow.db").read_bytes()
    assert b"REDACTED" in store  # the traces really were written
    assert re.search(rb"sk-[A-Za-z0-9_-]{10,}", store) is None
    assert FAKE_KEY.encode() not in store


def test_ok_calls_counts_one_model_in_one_stage(tmp_path):
    cache = CallCache(tmp_path / "c.sqlite")
    assert cache.ok_calls("pilot", "cheap") == 0


def test_test_set_reads_sealed_ids_only(tmp_path):
    (tmp_path / "test_ids.sealed").write_text('["b", "a", "c"]', encoding="utf-8")
    assert stage.select_ids(tmp_path / "split.parquet", "test") == ["a", "b", "c"]
    assert stage.select_ids(tmp_path / "split.parquet", "test", 2) == ["a", "b"]
    assert stage.file_tag("test") == "test.sealed"
    assert "test" not in stage.OPEN_SETS
