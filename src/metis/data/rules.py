"""Hard-rule detectors (G1), shared by the offline pipeline and the gateway (WP-02 step 5, PLAN E6).

Functions take plain values so the gateway can call them without the dataset classes; the
``*_msg`` helpers adapt dataset ``Message`` objects.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from metis.config import load_config
from metis.data.normalize import match_key
from metis.data.schema import Message

WORKFLOW_PROVIDERS = {"workflow"}
WORKFLOW_MODELS = {"default"}
IMAGE_MODELS = {"dalle"}
CHARS_PER_TOKEN = 3


def is_widget_click(choices: Iterable[Any], user_text: str | None) -> bool:
    """User text equals (after normalization) one of the previous bot message's choices."""
    key = match_key(user_text)
    if not key:
        return False
    return any(isinstance(c, str) and match_key(c) == key for c in choices)


def needs_vision(content_types: Iterable[str | None]) -> bool:
    return any((t or "").upper() == "IMAGE" for t in content_types)


def is_workflow_turn(provider: str | None, model: str | None) -> bool:
    return provider in WORKFLOW_PROVIDERS or model in WORKFLOW_MODELS


def is_image_generation(model: str | None) -> bool:
    return model in IMAGE_MODELS


def estimate_tokens(text: str | None, chars_per_token: float = CHARS_PER_TOKEN) -> int:
    """Rough token estimate (chars / 3) until real tokenizers are known."""
    return math.ceil(len(text or "") / chars_per_token)


_MODELS_CFG: dict[str, Any] | None = None


def _models_cfg() -> dict[str, Any]:
    global _MODELS_CFG
    if _MODELS_CFG is None:
        _MODELS_CFG = load_config("models")
    return _MODELS_CFG


def fits_context(model_id: str, tokens_in: int, cfg: dict[str, Any] | None = None) -> bool:
    """True if `tokens_in` + the reserved output tokens fit the model's context window.
    Unknown window → True (no evidence to exclude)."""
    cfg = cfg or _models_cfg()
    reserve = cfg.get("reserve_output_tokens", 0)
    for m in cfg["models"]:
        if m["id"] == model_id:
            window = m.get("context_window")
            return window is None or tokens_in + reserve <= window
    raise KeyError(f"unknown model id: {model_id}")


def vision_models(cfg: dict[str, Any] | None = None) -> list[str]:
    cfg = cfg or _models_cfg()
    return [m["id"] for m in cfg["models"] if m.get("role") == "candidate" and m.get("vision")]


# --- adapters for dataset messages -------------------------------------------------------------


def widget_choices(bot_msg: Message | None) -> list[Any]:
    if bot_msg is None or bot_msg.role != "bot":
        return []
    return [c for w in bot_msg.input for c in w.choices]


def is_widget_click_msg(prev_bot: Message | None, user_msg: Message) -> bool:
    return is_widget_click(widget_choices(prev_bot), user_msg.content)


def needs_vision_msg(msg: Message) -> bool:
    return needs_vision(a.content_type for a in msg.attachments)


def is_workflow_turn_msg(bot_msg: Message) -> bool:
    return is_workflow_turn(bot_msg.provider, bot_msg.model)
