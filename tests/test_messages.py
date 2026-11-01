"""WP-06 step 3: request structure and redaction (structure only, no real content)."""

import pytest

from metis.config import load_config
from metis.llm.client import check_outgoing, load_models
from metis.llm.messages import HUGE_PROMPT_CHARS, build_messages, gen_params

KEY = "sk-" + "a" * 30


def roles(messages):
    return [m["role"] for m in messages]


def test_full_shape():
    history = [{"role": "user", "content": "u1"}, {"role": "assistant", "content": "a1"}]
    out = build_messages("sys", "now", history, ["c1", "c2"])
    assert roles(out) == ["system", "user", "assistant", "user"]
    assert out[0]["content"] == "sys\n\nRetrieved context:\nc1\n\nc2"
    assert out[-1]["content"] == "now"


def test_no_instructions_no_context_has_no_system_message():
    assert roles(build_messages(None, "now")) == ["user"]
    assert roles(build_messages("", "now", rag_context=["", None])) == ["user"]


def test_context_without_instructions():
    assert build_messages("", "now", rag_context=["c"])[0]["content"] == "Retrieved context:\nc"


def test_opening_assistant_and_empty_turns_are_dropped():
    history = [
        {"role": "assistant", "content": "greeting"},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "x"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": ""},
    ]
    out = build_messages("", "now", history)
    assert roles(out) == ["user", "user"]
    assert out[0]["content"] == "u1"


@pytest.mark.parametrize(
    "parts",
    [
        {"instructions": KEY},
        {"user_text": KEY},
        {"history": [{"role": "user", "content": KEY}]},
        {"rag_context": [KEY]},
    ],
)
def test_every_part_is_redacted(parts):
    args = {"instructions": "s", "user_text": "u", **parts}
    out = build_messages(**args)
    assert KEY not in str(out)
    check_outgoing(out)


def test_input_is_not_changed():
    history = [{"role": "user", "content": KEY}]
    build_messages("s", "u", history)
    assert history[0]["content"] == KEY


def test_refuses_what_s1_excludes():
    with pytest.raises(ValueError):
        build_messages("x" * (HUGE_PROMPT_CHARS + 1), "u")
    with pytest.raises(ValueError):
        build_messages("s", "   ")


def test_size_limit_is_inclusive():
    assert build_messages("x" * HUGE_PROMPT_CHARS, "u")


def test_every_generating_model_has_params():
    cfg = load_config("gen_config")
    wanted = [
        m["id"]
        for m in load_models().values()
        if m["role"] in ("candidate", "pilot_option")
    ]
    assert sorted(wanted) == sorted(cfg["models"])
    for model_id in wanted:
        params = gen_params(model_id, cfg)
        assert 1024 in (params.get("max_tokens"), params.get("max_completion_tokens"))
        assert "temperature" not in params and "top_p" not in params


def test_sonnet_turns_thinking_off():
    params = gen_params("claude-sonnet-5-5", load_config("gen_config"))
    assert params["extra_body"]["thinking"] == {"type": "between_tools"}


def test_openai_uses_the_renamed_length_param():
    params = gen_params("gpt-5.6-luna", load_config("gen_config"))
    assert "max_tokens" not in params
    assert params["max_completion_tokens"] == 1024
    assert params["reasoning_effort"] == "none"


def test_unknown_model_fails():
    with pytest.raises(KeyError):
        gen_params("nope", load_config("gen_config"))
