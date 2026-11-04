"""One door to every LLM (WP-04 step 4, PLAN E2, E4, E13).

``complete()`` refuses to send anything that still contains a key pattern: callers redact first
(``redact_messages``), so the check here is the last line of defence, not the cleaner. A real call
also needs a ``Permit`` from ``metis.llm.budget``, so spending cannot bypass the guard.
``METIS_MOCK=1`` answers locally with deterministic fake text and usage ($0).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from dotenv import load_dotenv

from metis.config import load_config
from metis.data.redact import redact_counts, redact_obj
from metis.obs import tracking

MOCK_MEAN_OUT = 174  # mean output tokens in mock mode (WP-04 step 8)
MOCK_SIGMA = 0.6
MOCK_JUDGE_OUT = 120  # WP-06: judge replies in mock mode
_RECORD_LOCK = threading.Lock()
CONNECT_TIMEOUT_S = 5.0  # PLAN E4
TOTAL_TIMEOUT_S = 60.0
MAX_ATTEMPTS = 2  # first try + 1 retry with jitter on 429/5xx
QUOTA_WORDS = ("quota", "insufficient", "balance", "credit", "billing")  # a 429 that waiting won't fix


class OutgoingSecretError(RuntimeError):
    """A key pattern is still in an outgoing request. The message names kinds, never text."""


class NoPermitError(RuntimeError):
    """A real call was attempted without a budget Permit."""


class ModelNotReadyError(RuntimeError):
    """The model has no api name or prices yet (configs/models.yaml)."""


class CallFailed(RuntimeError):
    """The provider failed after retries. Carries a short kind, never content."""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


class AccountBlocked(RuntimeError):
    """The key or balance is the problem, not this prompt: stop, store nothing, resume later."""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True)
class Permit:
    """Issued only by ``Budget.guard``. ``complete`` will not make a real call without one."""

    stage: str
    reserved_usd: float


@dataclass
class Response:
    text: str
    tokens_in: int
    tokens_out: int
    finish_reason: str
    latency_ms: float
    model_version: str
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    usage_reported: bool = True
    raw_usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_mock() -> bool:
    return os.environ.get("METIS_MOCK", "0") == "1"


ADDED_MODELS = "models_added"  # configs/models_added.yaml: models added from the developer page


def load_models(config_dir: Any = None) -> dict[str, dict[str, Any]]:
    """configs/models.yaml, plus the models added from the developer page (never replacing one)."""
    models = {m["id"]: m for m in load_config("models", config_dir)["models"]}
    from metis.config import CONFIG_DIR

    if ((config_dir or CONFIG_DIR) / f"{ADDED_MODELS}.yaml").exists():
        for m in load_config(ADDED_MODELS, config_dir).get("models") or []:
            models.setdefault(m["id"], m)
    return models


def redact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mask key patterns in every message. Use this when building a request."""
    return redact_obj(messages)[0]


def check_outgoing(messages: list[dict[str, Any]], prompt_id: str | None = None) -> None:
    """Raise if a key pattern remains. The error carries the prompt id and kinds only."""
    _, kinds = redact_obj(messages)
    if kinds:
        raise OutgoingSecretError(f"prompt_id={prompt_id} kinds={sorted(kinds)}")


def _record_mock(model_id: str, messages: list[dict[str, Any]]) -> None:
    """Leak test (WP-07): keep the exact outgoing request in a git-ignored file."""
    path = os.environ.get("METIS_MOCK_RECORD")
    if path:
        line = json.dumps({"model": model_id, "messages": messages}, ensure_ascii=False) + "\n"
        with _RECORD_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(line)


def _mock_response(model_id: str, messages: list[dict[str, Any]], gen: dict[str, Any]) -> Response:
    _record_mock(model_id, messages)
    seed_text = repr((model_id, messages, sorted(gen.items())))
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    mu = math.log(MOCK_MEAN_OUT) - MOCK_SIGMA**2 / 2  # lognormal with mean MOCK_MEAN_OUT
    tokens_out = max(1, round(rng.lognormvariate(mu, MOCK_SIGMA)))
    limit = gen.get("max_tokens", gen.get("max_completion_tokens"))
    finish = "stop"
    if limit is not None and tokens_out >= limit:
        tokens_out, finish = int(limit), "length"
    tokens_in = max(1, sum(len(str(m.get("content", ""))) for m in messages) // 4)
    text = f"mock answer from {model_id}: " + " ".join(["lorem"] * tokens_out)
    last = str(messages[-1].get("content", "")) if messages else ""
    # Judge prompts must parse in mock runs too, and short replies are never cut off.
    if '"score": <integer 1-10>' in last:
        text = json.dumps({"reason": "mock", "score": rng.randint(1, 10)})
        tokens_out, finish = MOCK_JUDGE_OUT, "stop"
    elif '"verdict": "A"' in last:
        text = json.dumps({"reason": "mock", "verdict": rng.choice(["A", "B", "tie"])})
        tokens_out, finish = MOCK_JUDGE_OUT, "stop"
    return Response(
        text=text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        finish_reason=finish,
        latency_ms=float(rng.randint(100, 900)),
        model_version=f"mock-{model_id}",
        cached_tokens=0,
        reasoning_tokens=0,
    )


def account_problem(code: int | None, body: str) -> bool:
    """Bad or expired key, or no money left. Only a yes/no leaves this function."""
    if code in (401, 402, 403):
        return True
    return code == 429 and any(word in body.lower() for word in QUOTA_WORDS)


def _is_account_problem(exc: BaseException) -> bool:
    return account_problem(getattr(exc, "status_code", None), str(exc))


def _is_retryable(exc: BaseException) -> bool:
    code = getattr(exc, "status_code", None)
    return code == 429 or (isinstance(code, int) and code >= 500)


def _send(
    api_name: str, api_path: str, messages: list[dict[str, Any]], gen: dict[str, Any], api_key: str | None = None,
    stream: bool = False,
) -> Any:
    """Real request through LiteLLM to Metis AI, assumed OpenAI-compatible (checked in step 9)."""
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")  # no price download at import
    import httpx
    import litellm
    from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random

    litellm.telemetry = False

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_random(0.5, 2.0),
        reraise=True,
    )
    def call() -> Any:
        return litellm.completion(
            model=f"openai/{api_name}",
            messages=messages,
            api_base=os.environ["METIS_BASE_URL"].rstrip("/") + api_path,
            api_key=api_key or os.environ["METIS_API_KEY"],
            timeout=httpx.Timeout(TOTAL_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
            num_retries=0,
            **({"stream": True, "stream_options": {"include_usage": True}} if stream else {}),
            **gen,
        )

    return call()


class _Streamed:
    """A streamed reply put back together, shaped like a normal response for ``_parse``."""

    def __init__(self, chunks: Any, on_delta: Any):
        parts, self.usage, self.model, finish = [], None, None, None
        for chunk in chunks:
            self.model = getattr(chunk, "model", None) or self.model
            if getattr(chunk, "usage", None) is not None:
                self.usage = chunk.usage
            for choice in getattr(chunk, "choices", None) or []:
                piece = getattr(getattr(choice, "delta", None), "content", None)
                if piece:
                    parts.append(piece)
                    on_delta(piece)
                finish = getattr(choice, "finish_reason", None) or finish
        message = type("M", (), {"content": "".join(parts)})()
        self.choices = [type("C", (), {"message": message, "finish_reason": finish or "stop"})()]


def _stream_or_plain(api_name, api_path, messages, gen, api_key, on_delta) -> Any:
    """Stream if the provider can; if the streamed request fails before any text arrived (a provider
    without streaming), send it once as a normal request and hand the text out whole."""
    got = []
    try:
        return _Streamed(_send(api_name, api_path, messages, gen, api_key, stream=True),
                         lambda piece: (got.append(1), on_delta(piece)))
    except Exception as exc:
        if got or _is_account_problem(exc):
            raise
    raw = _send(api_name, api_path, messages, gen, api_key)
    _mock_stream(raw.choices[0].message.content or "", on_delta)
    return raw


def _mock_stream(text: str, on_delta: Any) -> None:
    for piece in re.findall(r"\S+\s*|\s+", text):
        on_delta(piece)


def _detail(usage: Any, group: str, name: str) -> int | None:
    value = getattr(getattr(usage, group, None), name, None)
    return value if isinstance(value, int) else None


def _parse(raw: Any, latency_ms: float, api_name: str) -> Response:
    usage = getattr(raw, "usage", None)
    choice = raw.choices[0]
    has_usage = usage is not None and getattr(usage, "prompt_tokens", None) is not None
    return Response(
        text=choice.message.content or "",
        tokens_in=usage.prompt_tokens if has_usage else 0,
        tokens_out=usage.completion_tokens if has_usage else 0,
        finish_reason=str(choice.finish_reason),
        latency_ms=latency_ms,
        model_version=getattr(raw, "model", None) or api_name,
        cached_tokens=_detail(usage, "prompt_tokens_details", "cached_tokens"),
        reasoning_tokens=_detail(usage, "completion_tokens_details", "reasoning_tokens"),
        usage_reported=has_usage,
        raw_usage=usage.model_dump() if has_usage and hasattr(usage, "model_dump") else {},
    )


def complete(
    model_id: str,
    messages: list[dict[str, Any]],
    gen_params: dict[str, Any] | None = None,
    permit: Permit | None = None,
    prompt_id: str | None = None,
    api_key: str | None = None,
    on_delta: Any = None,
) -> Response:
    """Send one request. Raises ``CallFailed`` after retries; never logs content.

    ``api_key``: a website user's own Metis key. The user pays the provider, so no budget
    ``Permit`` is needed; the outgoing secret guard still applies to the messages.
    ``on_delta``: called with each piece of text as it arrives (streaming); the full response is
    still returned at the end, so budget, ledger and checks work as for a normal call."""
    gen = dict(gen_params or {})
    check_outgoing(messages, prompt_id)
    with tracking.call_span(model_id, messages) as finish:
        if is_mock():
            response = _mock_response(model_id, messages, gen)
            if on_delta:
                _mock_stream(response.text, on_delta)
        else:
            if not isinstance(permit, Permit) and not api_key:
                raise NoPermitError(f"model={model_id} prompt_id={prompt_id}")
            model = load_models()[model_id]
            api_name, api_path = model.get("api_name"), model.get("api_path")
            if not api_name or api_path is None or model.get("provider") == "typesafe":
                raise ModelNotReadyError(model_id)
            load_dotenv()
            if not (os.environ.get("METIS_BASE_URL") and (api_key or os.environ.get("METIS_API_KEY"))):
                raise ModelNotReadyError("METIS_BASE_URL or METIS_API_KEY is not set")
            start = time.perf_counter()
            try:
                if on_delta:
                    raw = _stream_or_plain(api_name, api_path, messages, gen, api_key, on_delta)
                else:
                    raw = _send(api_name, api_path, messages, gen, api_key)
            # Provider errors can echo the prompt: keep the class only.
            except Exception as exc:  # noqa: BLE001
                if _is_account_problem(exc):
                    raise AccountBlocked(_failure_kind(exc)) from None
                raise CallFailed(_failure_kind(exc)) from None
            response = _parse(raw, (time.perf_counter() - start) * 1000, api_name)
        finish(
            {
                "text": redact_counts(response.text)[0],
                "tokens_in": response.tokens_in,
                "tokens_out": response.tokens_out,
                "finish_reason": response.finish_reason,
            }
        )
    return response


def _failure_kind(exc: BaseException) -> str:
    code = getattr(exc, "status_code", None)
    return f"{type(exc).__name__}:{code}" if code else type(exc).__name__
