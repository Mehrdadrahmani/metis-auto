"""One door to every LLM (WP-04 step 4, PLAN E2, E4, E13).

``complete()`` refuses to send anything that still contains a key pattern: callers redact first
(``redact_messages``), so the check here is the last line of defence, not the cleaner. A real call
also needs a ``Permit`` from ``metis.llm.budget``, so spending cannot bypass the guard.
``METIS_MOCK=1`` answers locally with deterministic fake text and usage ($0).
"""

from __future__ import annotations

import hashlib
import math
import os
import random
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from dotenv import load_dotenv

from metis.config import load_config
from metis.data.redact import redact_counts, redact_obj
from metis.obs import tracking

MOCK_MEAN_OUT = 174  # mean output tokens in mock mode (WP-04 step 8)
MOCK_SIGMA = 0.6
CONNECT_TIMEOUT_S = 5.0  # PLAN E4
TOTAL_TIMEOUT_S = 60.0
MAX_ATTEMPTS = 2  # first try + 1 retry with jitter on 429/5xx


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


def load_models(config_dir: Any = None) -> dict[str, dict[str, Any]]:
    return {m["id"]: m for m in load_config("models", config_dir)["models"]}


def redact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mask key patterns in every message. Use this when building a request."""
    return redact_obj(messages)[0]


def check_outgoing(messages: list[dict[str, Any]], prompt_id: str | None = None) -> None:
    """Raise if a key pattern remains. The error carries the prompt id and kinds only."""
    _, kinds = redact_obj(messages)
    if kinds:
        raise OutgoingSecretError(f"prompt_id={prompt_id} kinds={sorted(kinds)}")


def _mock_response(model_id: str, messages: list[dict[str, Any]], gen: dict[str, Any]) -> Response:
    seed_text = repr((model_id, messages, sorted(gen.items())))
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    mu = math.log(MOCK_MEAN_OUT) - MOCK_SIGMA**2 / 2  # lognormal with mean MOCK_MEAN_OUT
    tokens_out = max(1, round(rng.lognormvariate(mu, MOCK_SIGMA)))
    limit = gen.get("max_tokens")
    finish = "stop"
    if limit is not None and tokens_out >= limit:
        tokens_out, finish = int(limit), "length"
    tokens_in = max(1, sum(len(str(m.get("content", ""))) for m in messages) // 4)
    return Response(
        text=f"mock answer from {model_id}: " + " ".join(["lorem"] * tokens_out),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        finish_reason=finish,
        latency_ms=float(rng.randint(100, 900)),
        model_version=f"mock-{model_id}",
        cached_tokens=0,
        reasoning_tokens=0,
    )


def _is_retryable(exc: BaseException) -> bool:
    code = getattr(exc, "status_code", None)
    return code == 429 or (isinstance(code, int) and code >= 500)


def _send(
    api_name: str, api_path: str, messages: list[dict[str, Any]], gen: dict[str, Any]
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
            api_key=os.environ["METIS_API_KEY"],
            timeout=httpx.Timeout(TOTAL_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
            num_retries=0,
            **gen,
        )

    return call()


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
) -> Response:
    """Send one request. Raises ``CallFailed`` after retries; never logs content."""
    gen = dict(gen_params or {})
    check_outgoing(messages, prompt_id)
    with tracking.call_span(model_id, messages) as finish:
        if is_mock():
            response = _mock_response(model_id, messages, gen)
        else:
            if not isinstance(permit, Permit):
                raise NoPermitError(f"model={model_id} prompt_id={prompt_id}")
            model = load_models()[model_id]
            api_name, api_path = model.get("api_name"), model.get("api_path")
            if not api_name or api_path is None:
                raise ModelNotReadyError(model_id)
            load_dotenv()
            if not (os.environ.get("METIS_BASE_URL") and os.environ.get("METIS_API_KEY")):
                raise ModelNotReadyError("METIS_BASE_URL or METIS_API_KEY is not set")
            start = time.perf_counter()
            try:
                raw = _send(api_name, api_path, messages, gen)
            # Provider errors can echo the prompt: keep the class only.
            except Exception as exc:  # noqa: BLE001
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
