"""UniRoute on the Khayyam Challenge (Q-023): true answers, no judge. Stage khayyam, limit $5.

No Sonnet. Same steps as the paper: K-means on a large unlabeled part, Psi and lambda on 400 val,
scores on 1,100 test. Khayyam's licence is academic only: no question text leaves `runs/`.
Usage: uv run python scripts/khayyam_run.py [--spare]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans

from metis.config import load_config
from metis.embed.embedder import Embedder
from metis.eval.baselines import ZeroRouter
from metis.eval.metrics import area, sweep
from metis.eval.stats import bootstrap
from metis.llm.budget import Budget, call_cost
from metis.llm.callcache import CallCache, get_or_call
from metis.llm.client import complete
from metis.llm.messages import gen_params
from metis.llm.runner import run_batch
from metis.router.route import cluster_choices, normalize_costs
from metis.router.select_k import fit_psi, halvings
from metis.router.select_lambda import lambda_grid

SEED = 20261020
MODELS = ["gemini-2.5-flash-lite", "deepseek-v4-flash", "gpt-5.6-luna", "deepseek-v4-pro"]
OUT = Path("runs/khayyam")
SYSTEM = "به این پرسش چهارگزینه‌ای پاسخ بده. فقط شماره گزینه درست (۱، ۲، ۳ یا ۴) را بنویس."
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def load() -> pd.DataFrame:
    files = glob.glob("data/external/raw/raia-center__khayyam-challenge/**/*.parquet", recursive=True)
    raw = pd.concat(pd.read_parquet(f) for f in files)
    print(list(raw.columns))
    q = next(c for c in raw.columns if "Question Body" in c or c.lower() == "question body")
    ch = [c for c in raw.columns if re.fullmatch(r"(Choice|choice)\s*\d", c)]
    key = next(c for c in raw.columns if c.lower() in ("key", "answer", "correct_answer"))
    df = pd.DataFrame({"q": raw[q], "options": raw[ch].astype(str).agg(lambda r: "\n".join(f"{i + 1}) {t}" for i, t in enumerate(r)), axis=1), "key": raw[key].astype("Int64").astype(str)})
    df = df[df.key.isin(list("1234")) & df.q.notna()].reset_index(drop=True)
    df["id"] = np.arange(len(df)).astype(str)
    return df


def parse(text: str | None) -> str | None:
    text = (text or "").translate(DIGITS)
    named = re.findall(r"(?:گزینه|پاسخ|option)\D{0,12}([1-4])", text, re.IGNORECASE)
    if named:
        return named[-1]  # a short reasoning may come first; the conclusion is last
    found = re.findall(r"[1-4]", text)
    return found[-1] if found else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spare", action="store_true")
    args = ap.parse_args()
    load_dotenv()
    if args.spare:
        os.environ["METIS_API_KEY"] = os.environ["METIS_API_KEY_SPARE"]
    OUT.mkdir(exist_ok=True)
    df = load()
    idx = np.random.default_rng(SEED).permutation(len(df))
    val, test, train = idx[:400], idx[400:1500], idx[1500:]
    print("rows", len(df), "train", len(train))
    s4 = load_config("pipeline")["s4"]
    c = s4["candidates"][s4["choice"]]
    vec_path = OUT / "vecs.npy"
    if vec_path.exists():
        vecs = np.load(vec_path)
    else:
        e = Embedder(c["name"], c["revision"], device="mps", path=c["path"], task=s4["task"], prompt_name=s4["prompt_name"], merge_adapter=True, max_tokens=s4["max_tokens"], batch_size=32, max_batch_tokens=8192)
        vecs = e.encode(df.q.astype(str).str[:2000].tolist())
        np.save(vec_path, vecs)

    cache, cfg = CallCache(), load_config("gen_config")
    budget = Budget(cache)
    labeled = np.concatenate([val, test])
    results: dict[tuple[str, str], dict] = {}

    for model in MODELS:  # cheapest first
        params = gen_params(model, cfg, 300)
        price = call_cost(budget.models[model], 350, 150)

        def one(i, model=model, params=params, price=price):
            row = df.iloc[i]
            messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{row.q}\n{row.options}"}]
            r = get_or_call(cache, budget, "khayyam", model, messages, params, "khayyam-v1", price, complete, prompt_id=row.id)
            if r.status == "ok":
                results[(row.id, model)] = {"text": r.response.text, "t_in": r.response.tokens_in, "t_out": r.response.tokens_out, "ms": r.response.latency_ms, "cut": r.response.finish_reason == "length"}
            return r

        report = run_batch(f"khayyam_{model}", [int(i) for i in labeled], one, {**budget.config["anomalies"], "max_truncation_rate": 0.5}, 8, est_cost_per_call=price, params={})
        print(model, "cost", round(report.cost_usd, 3), "failed", report.failed_new, "stop", report.stopped_reason, flush=True)
        if report.stopped:
            raise SystemExit(f"stopped: {report.stopped_reason}")

    ids = df.id.to_numpy()
    loss = np.ones((len(df), len(MODELS)))
    t_in, t_out = np.zeros(len(MODELS)), np.zeros(len(MODELS))
    for j, m in enumerate(MODELS):
        got = [results[(ids[i], m)] for i in labeled if (ids[i], m) in results]
        t_in[j], t_out[j] = np.mean([g["t_in"] for g in got]), np.mean([g["t_out"] for g in got])
        for i in labeled:
            r = results.get((ids[i], m))
            loss[i, j] = 0.0 if r and not r["cut"] and parse(r["text"]) == df.key.iloc[i] else 1.0  # a cut answer gave no answer
    c_hat = normalize_costs([call_cost(budget.models[m], t_in[j], t_out[j]) for j, m in enumerate(MODELS)])

    router = load_config("pipeline")["router"]
    lams = lambda_grid(router["lambda_n"], router["lambda_low"], router["lambda_high"])
    Lv, Lt = loss[val], loss[test]
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    train_fit = train[:min(12000, len(train))]
    cands, scores = {}, {}
    for k in (1, 3, 4, 5, 6, 7, 8):
        km = KMeans(k, n_init=10, random_state=SEED).fit(vecs[train_fit])
        cands[k] = km.cluster_centers_
        lv = km.predict(vecs[val])
        s = []
        for a, b in halvings(len(val), 20, SEED):
            for fit, sc in ((a, b), (b, a)):
                psi = fit_psi(Lv[fit], lv[fit], k)
                s.append(area(*sweep(lv[sc], psi, c_hat, lams, Lv[sc]), c_min, c_max))
        scores[k] = float(np.mean(s))
    k_star = max((k for k in scores if k > 1), key=lambda k: (round(scores[k], 6), -k))
    assign_ = lambda x, c: ((x[:, None] - c[None]) ** 2).sum(-1).argmin(1)
    lv, lt = assign_(vecs[val], cands[k_star]), assign_(vecs[test], cands[k_star])
    psi = fit_psi(Lv, lv, k_star)
    a_router = area(*sweep(lt, psi, c_hat, lams, Lt), c_min, c_max)
    zero = ZeroRouter(Lv, c_hat)
    a_zero = area(*zero.curve(None, None, Lt), c_min, c_max)
    costs_v, q_v = sweep(lv, psi, c_hat, lams, Lv)
    best = int(np.argmin(Lv.mean(0)))
    target = 1 - Lv[:, best].mean() - 0.02
    ok = np.flatnonzero(q_v >= target)
    lam = float(lams[ok[-1]])
    pick = cluster_choices(psi, c_hat, np.array([lam]))[0][lt]
    rows = np.arange(len(test))
    routed = 1 - Lt[rows, pick]
    d = bootstrap(lambda i: float(routed[i].mean() - (1 - Lt[i, best]).mean()), np.arange(len(test)), 10_000, SEED)
    pa = bootstrap(lambda i: area(*sweep(lt[i], psi, c_hat, lams, Lt[i]), c_min, c_max) - area(*zero.curve(None, None, Lt[i]), c_min, c_max), np.arange(len(test)), 500, SEED)
    data = {"models": MODELS, "accuracy_test": {m: float(1 - Lt[:, j].mean()) for j, m in enumerate(MODELS)}, "c_hat": c_hat.tolist(), "k_scores": scores, "k_star": k_star,
            "area_router": a_router, "area_zero": a_zero, "area_gain": pa.estimate, "area_gain_ci": [pa.low, pa.high], "lambda": lam, "router_acc": float(routed.mean()), "router_cost": float(c_hat[pick].mean()),
            "best": MODELS[best], "best_cost": float(c_hat[best]), "diff_vs_best": d.estimate, "diff_ci": [d.low, d.high], "shares": (np.bincount(pick, minlength=4) / len(pick)).tolist(), "spent": cache.spent_usd("khayyam"), "cut_share": {m: float(np.mean([results[(ids[i], m)]["cut"] for i in test if (ids[i], m) in results])) for m in MODELS}}
    Path("results/khayyam").mkdir(exist_ok=True)
    Path("results/khayyam/khayyam.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(json.dumps(data, indent=1))


if __name__ == "__main__":
    main()
