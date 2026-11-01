"""Jev adapter (D-082, D-083): a form-style scorer, not a chat model.

Same signature as ``client.complete``, so ``get_or_call`` caches and budgets it the same way.
``messages`` holds the ``state`` text; ``gen_params["questions"]`` holds the form. Response text is
the ``answers`` object as JSON, read by ``parse_jev_*``.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from typing import Any

from dotenv import load_dotenv

from metis.data.redact import redact_counts
from metis.llm import client
from metis.llm.client import (
    CONNECT_TIMEOUT_S,
    MAX_ATTEMPTS,
    TOTAL_TIMEOUT_S,
    CallFailed,
    ModelNotReadyError,
    NoPermitError,
    Permit,
    Response,
)
from metis.obs import tracking


def build_body(api_name: str, messages: list[dict[str, Any]], gen: dict[str, Any]) -> dict[str, Any]:
    return {"state": messages[-1]["content"], "model": api_name, "questions": gen["questions"]}


def _mock(model_id: str, messages: list[dict[str, Any]], gen: dict[str, Any]) -> Response:
    seed = hashlib.sha256(repr((messages, gen)).encode("utf-8")).digest()[:8]
    rng = random.Random(int.from_bytes(seed, "big"))
    answers = {}
    for name, q in gen["questions"].items():
        if q["type"] == "score":
            answers[name] = {"type": "score", "score": float(rng.randint(0, 4)), "confidence": 0.9}
        else:
            answers[name] = {"type": "choice", "choice": rng.choice(list(q["criteria"])), "confidence": 0.9}
    tokens_in = max(1, len(str(messages[-1]["content"])) // 4)
    return Response(json.dumps(answers), tokens_in, 0, "stop", 100.0, f"mock-{model_id}", 0, 0)


def _post(url: str, body: dict[str, Any]) -> dict[str, Any]:
    import httpx
    from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random

    def retryable(exc: BaseException) -> bool:
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return code == 429 or (isinstance(code, int) and code >= 500)

    @retry(
        retry=retry_if_exception(retryable),
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_random(0.5, 2.0),
        reraise=True,
    )
    def call() -> dict[str, Any]:
        reply = httpx.post(
            url,
            json=body,
            headers={"Authorization": f"Bearer {os.environ['METIS_API_KEY']}"},
            timeout=httpx.Timeout(TOTAL_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
        )
        reply.raise_for_status()
        return reply.json()

    return call()


def _failure_kind(exc: Exception) -> str:
    code = getattr(getattr(exc, "response", None), "status_code", None)
    return f"{type(exc).__name__}:{code}" if code else type(exc).__name__


def complete(
    model_id: str,
    messages: list[dict[str, Any]],
    gen_params: dict[str, Any] | None = None,
    permit: Permit | None = None,
    prompt_id: str | None = None,
) -> Response:
    gen = dict(gen_params or {})
    client.check_outgoing([*messages, {"questions": gen.get("questions")}], prompt_id)
    with tracking.call_span(model_id, messages) as finish:
        if client.is_mock():
            response = _mock(model_id, messages, gen)
        else:
            if not isinstance(permit, Permit):
                raise NoPermitError(f"model={model_id} prompt_id={prompt_id}")
            model = client.load_models()[model_id]
            load_dotenv()
            base = os.environ.get("METIS_BASE_URL")
            if not (base and os.environ.get("METIS_API_KEY")):
                raise ModelNotReadyError("METIS_BASE_URL or METIS_API_KEY is not set")
            start = time.perf_counter()
            try:
                raw = _post(base.rstrip("/") + model["api_path"], build_body(model["api_name"], messages, gen))
                usage = raw.get("usage") or {}
                response = Response(
                    text=json.dumps(raw["answers"], ensure_ascii=False),
                    tokens_in=usage.get("input_tokens", 0),
                    tokens_out=usage.get("output_tokens", 0),
                    finish_reason="stop",
                    latency_ms=(time.perf_counter() - start) * 1000,
                    model_version=raw.get("model") or model["api_name"],
                    usage_reported="input_tokens" in usage,
                    raw_usage=usage,
                )
            # Provider errors can echo the prompt: keep the class only.
            except Exception as exc:  # noqa: BLE001
                raise CallFailed(_failure_kind(exc)) from None
        finish(
            {
                "text": redact_counts(response.text)[0],
                "tokens_in": response.tokens_in,
                "tokens_out": response.tokens_out,
                "finish_reason": response.finish_reason,
            }
        )
    return response
