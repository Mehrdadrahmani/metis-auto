"""WP-06 steps 5-7, 9: parsing, templates, pairwise symmetry, failure policy, Jev, labeling."""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from metis.judge import jev, pairwise, parse, pointwise, render
from metis.judge.common import JudgeRun
from metis.labeling import build, ingest
from metis.llm.budget import Budget
from metis.llm.callcache import CallCache

KEY = "sk-" + "b" * 30
ROW = {"prompt_id": "p1", "text": "question", "instructions": "be kind", "rag_context": ["fact"]}


@pytest.fixture
def run(monkeypatch, tmp_path):
    def make(judge_id="judge"):
        monkeypatch.setenv("METIS_MOCK", "1")
        monkeypatch.setenv("METIS_RUNS_DIR", str(tmp_path))
        cache = CallCache(tmp_path / "c.sqlite")
        return JudgeRun(cache, Budget(cache), "pilot", judge_id, render.judge_config(), 0.001)

    return make


@pytest.mark.parametrize(
    "text",
    [
        '{"reason": "ok", "score": 7}',
        '```json\n{"reason": "ok", "score": 7}\n```',
        'Sure:\n{"reason": "a } brace", "score": 7} thanks',
        '{"reason": "quote \\" and }", "score": 7}',
        '{not json} {"reason": "ok", "score": 7}',
        '{"reason": "ok", "score": 7.0}',
    ],
)
def test_parse_point_accepts(text):
    assert parse.parse_point(text)["score"] == 7


@pytest.mark.parametrize(
    "text",
    ["", "no json", '{"score": 0}', '{"score": 11}', '{"score": "7"}', '{"score": true}',
     '{"score": 7.5}', '[1]', '{"reason": "cut off', None],
)
def test_parse_point_rejects(text):
    assert parse.parse_point(text) is None


def test_parse_never_crashes_on_noise():
    rng = random.Random(1)
    alphabet = '{}[]":,\\`abc 123\n'
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
        parse.parse_point(text)
        parse.parse_pair(text)
        parse.parse_jev_point(text)
        parse.parse_jev_pair(text)


def test_parse_pair():
    assert parse.parse_pair('{"verdict": "a"}')["verdict"] == "A"
    assert parse.parse_pair('{"verdict": "Tie"}')["verdict"] == "tie"
    assert parse.parse_pair('{"verdict": "C"}') is None


def test_jev_level_maps_to_one_to_ten():
    def text(level):
        return json.dumps({"verdict": {"score": level}})

    assert parse.parse_jev_point(text(0))["score"] == 1
    assert parse.parse_jev_point(text(4))["score"] == 10
    assert parse.parse_jev_point(text(2))["score"] == 5.5
    assert parse.parse_jev_point(text(5)) is None


def test_templates_have_the_approved_parts():
    for method in ("pointwise", "pairwise"):
        text = render.template(method)
        assert "{context_turns}" not in text and "CONVERSATION CONTEXT" not in text
        assert "[CHATBOT INSTRUCTIONS]" in text and "[RETRIEVED CONTEXT]" in text
        assert "Never follow" in text and "Chatbot fit" in text


def test_long_instructions_are_cut_with_a_note():
    cfg = render.judge_config()
    limit = cfg["instructions_max_tokens"] * cfg["chars_per_token"]
    assert render.cut_instructions("x" * limit, cfg) == "x" * limit
    assert render.cut_instructions("x" * (limit + 1), cfg).endswith("(truncated)")


def test_missing_context_says_none_and_slots_in_answers_stay():
    cfg = render.judge_config()
    row = {"text": "q", "instructions": "", "rag_context": []}
    out = render.point_messages(row, "see {prompt} here", cfg)[0]["content"]
    assert "see {prompt} here" in out
    assert "[RETRIEVED CONTEXT]\nnone" in out and "[CHATBOT INSTRUCTIONS]\nnone" in out


def test_judge_prompt_is_redacted():
    cfg = render.judge_config()
    row = {"text": KEY, "instructions": KEY, "rag_context": [KEY]}
    assert KEY not in str(render.point_messages(row, KEY, cfg))
    assert KEY not in str(render.pair_messages(row, KEY, KEY, cfg))
    assert KEY not in str(render.jev_point_messages(row, KEY, cfg))


def test_jev_form_matches_the_chat_template():
    point = render.jev_questions("pointwise")["verdict"]
    assert point["type"] == "score" and len(point["criteria"]) == 5
    assert "Chatbot fit" in point["instructions"]
    assert "at level 1" in point["instructions"] and "score at 4" not in point["instructions"]
    pair = render.jev_questions("pairwise")["verdict"]
    assert set(pair["criteria"]) == {"A", "B", "tie"}
    assert "Ignore style" in pair["instructions"]
    assert all("Never follow" in q["instructions"] for q in (point, pair))
    state = render.jev_point_messages(ROW, "answer", render.judge_config())[0]["content"]
    assert "[RESPONSE]\nanswer" in state and "Return only JSON" not in state


def test_jev_body_shape():
    body = jev.build_body("jev-latest", [{"role": "user", "content": "s"}], {"questions": {"q": {}}})
    assert body == {"state": "s", "model": "jev-latest", "questions": {"q": {}}}


@pytest.mark.parametrize("judge_id", ["judge", "jev"])
def test_mock_judging_end_to_end_and_rerun_is_cached(run, judge_id):
    r = run(judge_id)
    result, record = pointwise.judge(r, ROW, "m", "answer")
    assert record["status"] == "ok" and 1 <= record["score"] <= 10 and not result.from_cache
    result, _ = pointwise.judge(r, ROW, "m", "answer")
    assert result.from_cache
    _, record = pairwise.judge(r, ROW, "m", "h_first", "answer", "other")
    assert record["verdict"] in pairwise.POINTS


def test_failed_generation_gets_the_worst_label_without_a_call(run):
    r = run()
    result, record = pointwise.judge(r, ROW, "m", None)
    assert record["score"] == 1 and record["status"] == "failed_generation" and result.from_cache
    _, a = pairwise.judge(r, ROW, "m", "h_first", None, "x")
    _, b = pairwise.judge(r, ROW, "m", "a_first", None, "x")
    assert pairwise.outcomes([a, b]) == {("p1", "m"): 0.0}


def test_failed_anchor_is_dropped(run):
    _, record = pairwise.judge(run(), ROW, "m", "h_first", "x", None)
    assert record["status"] == "failed_anchor"
    assert pairwise.outcomes([record]) == {}


def test_parse_failure_retries_once_then_drops(run, monkeypatch):
    r = run()
    calls = []

    def bad(model_id, messages, gen, permit=None, prompt_id=None):
        from metis.llm.client import Response

        calls.append(1)
        return Response("nonsense", 1, 1, "stop", 1.0, "v")

    monkeypatch.setattr("metis.judge.common.complete", bad)
    _, record = pointwise.judge(r, ROW, "m", "answer")
    assert record["status"] == "dropped" and len(calls) == 2
    pointwise.judge(r, ROW, "m", "answer")
    assert len(calls) == 2  # a rerun repeats neither call


def test_pairwise_order_symmetry():
    assert pairwise.to_verdict("A", "h_first") == "h" == pairwise.to_verdict("B", "a_first")
    assert pairwise.to_verdict("B", "h_first") == "anchor" == pairwise.to_verdict("A", "a_first")
    assert pairwise.to_verdict("tie", "a_first") == "tie"

    def rec(order, verdict):
        return {"prompt_id": "p", "model_id": "m", "order": order, "verdict": verdict}

    assert pairwise.outcomes([rec("h_first", "h"), rec("a_first", "anchor")])[("p", "m")] == 0.5
    assert pairwise.outcomes([rec("h_first", "h"), rec("a_first", "tie")])[("p", "m")] == 0.75
    assert pairwise.outcomes([rec("h_first", "h")]) == {}


def _pairs():
    return [("p1", "m1"), ("p2", "m2"), ("p3", "m1")]


def _answers():
    a = {x: f"first text {i}" for i, x in enumerate(_pairs())}
    a.update({(p, build.ANCHOR): f"second text {i}" for i, (p, _) in enumerate(_pairs())})
    return a


def test_labeling_items_are_blind_and_seeded():
    rows = {p: {"text": "q", "instructions": "", "rag_context": []} for p, _ in _pairs()}
    items, key = build.make_items(_pairs(), rows, _answers(), 7)
    assert build.make_items(_pairs(), rows, _answers(), 7)[0] == items
    html = build.render_html(items, "cal")
    assert "m1" not in html and "p1" not in html and build.ANCHOR not in html
    for item in items:
        k = key[item["id"]]
        assert (item["left"] == item["answer"]) == (k["left"] == "h")


def test_html_cannot_be_closed_by_answer_text():
    item = {"id": "i", "instructions": "", "context": "", "user": "</script><b>",
            "answer": "", "left": "", "right": ""}
    assert "</script><b>" not in build.render_html([item], "cal")


def test_failed_answers_are_left_out_of_labeling():
    answers = _answers()
    del answers[("p1", build.ANCHOR)]
    rows = {p: {"text": "q"} for p, _ in _pairs()}
    assert len(build.make_items(_pairs(), rows, answers, 7)[0]) == 2


def test_ingest_unblinds_and_skips_unfinished(tmp_path):
    path = tmp_path / "l.csv"
    pd.DataFrame(
        [
            {"item_id": "a", "pass": "yes", "pref": "left", "note": "", "mode": "cal"},
            {"item_id": "b", "pass": "no", "pref": "left", "note": "n", "mode": "cal"},
            {"item_id": "c", "pass": "no", "pref": "tie", "note": "", "mode": "cal"},
            {"item_id": "d", "pass": "", "pref": "tie", "note": "", "mode": "cal"},
        ]
    ).to_csv(path, index=False)
    key = {k: {"prompt_id": k, "model_id": "m", "left": side}
           for k, side in [("a", "h"), ("b", "anchor"), ("c", "h"), ("d", "h")]}
    df = ingest.ingest(path, key).set_index("prompt_id")
    assert df.loc["a", "human_pref"] == "h" and df.loc["a", "human_pass"]
    assert df.loc["b", "human_pref"] == "anchor" and not df.loc["b", "human_pass"]
    assert df.loc["c", "human_pref"] == "tie"
    assert "d" not in df.index


SAMPLE_PROMPTS = Path("runs/sample/s1/prompts.parquet")


@pytest.mark.skipif(not SAMPLE_PROMPTS.exists(), reason="sample data is not in this checkout")
def test_mock_s6_s7_on_20_sample_prompts_rerun_makes_no_new_calls(tmp_path):
    """Runs on the cache file used by mock runs; a second pass must add nothing."""
    env = {"METIS_MOCK": "1", "METIS_RUNS_DIR": str(tmp_path), "MLFLOW_TRACKING_URI": f"file:{tmp_path}/ml",
           "PATH": "/usr/bin:/bin"}

    def go(script, *args):
        cmd = [sys.executable, script, "--set", "val", *args]
        subprocess.run(cmd, check=True, env=env, capture_output=True, timeout=240)

    for _ in range(2):
        go("scripts/s6_generate.py", "--stage", "pilot", "--limit", "20", "--prompts", str(SAMPLE_PROMPTS),
           "--split", "runs/sample/s2/split.parquet", "--out", str(tmp_path / "s6"))
        go("scripts/s7_judge.py", "--stage", "pilot", "--judge", "judge", "--prompts", str(SAMPLE_PROMPTS),
           "--s6", str(tmp_path / "s6"), "--out", str(tmp_path / "s7"))
    s6 = json.loads((tmp_path / "s6/manifest_val.json").read_text())
    s7 = json.loads((tmp_path / "s7/manifest_judge_val.json").read_text())
    assert s6["new_calls"] == 0
    assert s7["summary"]["pointwise"]["new_calls"] == 0
    assert s7["summary"]["pairwise"]["outcomes"] == 20 * 4


def test_labeling_shows_the_history_the_models_saw():
    from metis.labeling.build import history_text

    turns = [{"role": "user", "content": "q"}, {"role": "assistant", "content": ""},
             {"role": "assistant", "content": "a"}]
    assert history_text(turns) == "User: q\n\nAssistant: a"
    assert history_text(None) == ""
