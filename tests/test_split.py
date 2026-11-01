"""S2 splitter tests on a synthetic prompts table."""

import pandas as pd

from metis.data.split import make_splits, split_manifest

CAL = ["deepseek-v4-flash", "gpt-4o-mini", "gemini-2.5-flash"]


def synthetic(n_sessions=120, per_session=5):
    rows = []
    for s in range(n_sessions):
        cat = ["a", "b", "c", "d"][s % 4] if s % 10 else "a"
        for i in range(per_session):
            rows.append(
                {
                    "prompt_id": f"p{s:03d}_{i}",
                    "session_id": f"s{s:03d}",
                    "category": cat,
                    "lang": "fa" if i % 3 else "en",
                    "session_created_at": f"2026-01-{1 + s // 5:02d} 10:{s % 60:02d}:00",
                    "eligible_labeled": i != 4 or s % 2 == 0,
                    "eligible_train": i != 3,
                }
            )
    return pd.DataFrame(rows)


def run(df, seed=20261020, **kw):
    args = {
        "n_val": 60,
        "n_test": 40,
        "n_pilot": 20,
        "max_per_session": 3,
        "cal_models": CAL,
        "seed": seed,
    }
    args.update(kw)
    return make_splits(df, **args)


def test_sizes_and_no_session_leak():
    res = run(synthetic())
    t = res.table
    assert (t["split"] == "val").sum() == 60 and (t["split"] == "test").sum() == 40
    labeled = t[t["split"].isin(["val", "test"])]
    assert labeled.groupby("session_id")["split"].nunique().max() == 1
    for s in ("val", "test"):
        part = t[t["split"] == s]
        assert part.groupby("session_id").size().max() <= 3
    # a labeled session never also feeds train
    lab_sess = set(labeled["session_id"])
    assert not (t[t["split"] == "train"]["session_id"].isin(lab_sess)).any()
    assert t["prompt_id"].is_unique


def test_only_eligible_in_labeled_and_draws_from_all_sessions():
    df = synthetic(n_sessions=400)
    res = run(df)
    t = res.table.merge(df[["prompt_id", "eligible_labeled", "session_created_at"]])
    lab = t[t["split"].isin(["val", "test"])]
    assert lab["eligible_labeled"].all()
    assert res.info["capacity"] >= 3 * 100
    # no recent pool: labeled sessions cover the whole date range
    days = df["session_created_at"].sort_values()
    assert lab["session_created_at"].min() < days.iloc[len(days) // 4]
    assert lab["session_created_at"].max() > days.iloc[3 * len(days) // 4]


def test_input_dates_are_not_used():
    df = synthetic()
    moved = df.assign(session_created_at="2020-01-01 00:00:00")
    assert split_manifest(run(df), {})["sha256"] == split_manifest(run(moved), {})["sha256"]


def test_each_prompt_is_equally_likely_so_long_sessions_count_more():
    rows = []
    for s in range(3000):  # 3000 one-prompt sessions, 300 ten-prompt sessions: half of the prompts
        n = 1 if s < 2700 else 10
        rows += [{"prompt_id": f"p{s}_{i}", "session_id": f"s{s}", "lang": "fa",
                  "eligible_labeled": True, "eligible_train": True} for i in range(n)]  # fmt: skip
    df = pd.DataFrame(rows)
    t = run(df, n_val=600, n_test=0, n_pilot=0).table
    val = t[t["split"] == "val"]
    long_share = val["session_id"].str[1:].astype(int).ge(2700).mean()
    assert 0.45 < long_share < 0.60  # sessions alone would give about 0.1 to 0.25


def test_no_balancing_by_default():
    t = run(synthetic()).table
    assert set(t["stratum"]) == {"all"}


def test_stratified_by_category():
    df = synthetic()
    t = run(df, balance="category").table
    val = t[t["split"] == "val"]["stratum"].value_counts(normalize=True)
    # category "a" holds more sessions (every 10th session + its share)
    assert val["a"] > val["b"]


def test_pilot_and_cal():
    t = run(synthetic()).table
    pilot = t[t["in_pilot"]]
    assert len(pilot) == 20 and (pilot["split"] == "val").all()
    counts = pilot["cal_model"].value_counts()
    assert set(counts.index) == set(CAL) and counts.max() - counts.min() <= 1
    assert t.loc[~t["in_pilot"], "cal_model"].isna().all()


def test_deterministic_and_seed_sensitive():
    df = synthetic()
    m1 = split_manifest(run(df), {})
    m2 = split_manifest(run(df.sample(frac=1, random_state=1)), {})  # input order must not matter
    assert m1["sha256"] == m2["sha256"]
    m3 = split_manifest(run(df, seed=1), {})
    assert m3["sha256"]["val"] != m1["sha256"]["val"]


def test_shortfall_reported_when_too_small():
    res = run(synthetic(n_sessions=10), n_val=60, n_test=40)
    assert (res.table["split"] == "val").sum() < 60 or (res.table["split"] == "test").sum() < 40
    assert res.info["sessions_total"] == 10


def test_session_stratum_is_first_eligible_prompt():
    df = synthetic()
    df["msg_index"] = df["prompt_id"].str[-1].astype(int)
    df["uses_rag"] = df["msg_index"] == 0  # only each session's first prompt
    res = run(df, balance="uses_rag")
    assert res.info["balance_field"] == "uses_rag"
    t = res.table
    assert set(t["stratum"]) == {"True", "False"}
    # every session's first prompt is eligible and RAG, so sessions all fall in one stratum
    assert res.info["shortfall"]["val"] == {"True": 0}


def test_session_stratum_follows_first_eligible_when_first_prompt_is_excluded():
    df = synthetic()
    df["msg_index"] = df["prompt_id"].str[-1].astype(int)
    df["uses_rag"] = df["msg_index"] == 1
    df["eligible_labeled"] = df["msg_index"] >= 1  # prompt 0 excluded, prompt 1 is RAG
    res = run(df, balance="uses_rag")
    assert res.info["shortfall"]["val"] == {"True": 0}
