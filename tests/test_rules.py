"""Hard-rule detector tests (synthetic)."""

import pytest

from metis.config import config_id, load_config
from metis.data.rules import (
    estimate_tokens,
    fits_context,
    is_image_generation,
    is_widget_click,
    is_widget_click_msg,
    is_workflow_turn,
    needs_vision,
    needs_vision_msg,
    vision_models,
)
from metis.data.schema import Attachment, InputWidget, Message


def test_widget_click_normalized():
    choices = ["بله", "خير", "Order status"]
    assert is_widget_click(choices, "بله")
    assert is_widget_click(choices, "  خیر ")  # Arabic vs Persian yeh, spaces
    assert is_widget_click(choices, "order STATUS")
    assert not is_widget_click(choices, "بله، ولی سوال دارم")
    assert not is_widget_click(choices, "")
    assert not is_widget_click([], "بله")
    assert not is_widget_click([None, 3], "3")


def test_widget_click_msg():
    bot = Message(role="bot", input=[InputWidget(type="SINGLE_CHOICE", choices=["الف", "ب"])])
    assert is_widget_click_msg(bot, Message(role="user", content="ب"))
    assert not is_widget_click_msg(None, Message(role="user", content="ب"))
    assert not is_widget_click_msg(Message(role="user"), Message(role="user", content="ب"))


def test_vision_and_workflow():
    assert needs_vision(["IMAGE"]) and needs_vision(["image"]) and not needs_vision([None])
    assert needs_vision_msg(Message(role="user", attachments=[Attachment(content_type="IMAGE")]))
    assert not needs_vision_msg(Message(role="user"))
    assert is_workflow_turn("workflow", "x") and is_workflow_turn("openai", "default")
    assert not is_workflow_turn("openai", "gpt-4o-mini")
    assert is_image_generation("dalle") and not is_image_generation("gpt-4o-mini")


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 2
    assert estimate_tokens(None) == 0


def test_fits_context():
    cfg = load_config("models")
    reserve = cfg["reserve_output_tokens"]
    assert fits_context("gpt-4o-mini", 1000, cfg)
    assert not fits_context("gpt-4o-mini", 128000 - reserve + 1, cfg)
    assert fits_context("gemini-2.5-flash", 500000, cfg)
    assert fits_context("judge", 10**9, cfg)  # unknown window
    with pytest.raises(KeyError):
        fits_context("nope", 1, cfg)


def test_models_config():
    cfg = load_config("models")
    cands = [m for m in cfg["models"] if m["role"] == "candidate"]
    assert [m["id"] for m in cands] == [
        "deepseek-v4-flash", "gpt-4o-mini", "gemini-2.5-flash", "claude-sonnet-4-6",
    ]  # fmt: skip
    assert sum(m["is_anchor"] for m in cands) == 1
    assert "deepseek-v4-flash" not in vision_models(cfg)
    assert len(cfg["_id"]) == 12


def test_config_id_stable():
    assert config_id({"a": 1, "b": [1, 2]}) == config_id({"b": [1, 2], "a": 1})
    assert config_id({"a": 1}) != config_id({"a": 2})
