"""Build the Khayyam demo router and check it through its own gateway. $0: stored answers only.

Usage: uv run python scripts/khayyam_build.py [--models extra-model-1,extra-model-2]

Same method as scripts/khayyam_run.py (K on 400 val by split-halves area, Psi on val, lambda =
largest with val accuracy >= best single - 2 points), then:
  artifacts/router_khayyam/           the router file (numbers and subject names only)
  runs/khayyam/demo.parquet           test questions and every model's stored answer (local only)
  runs/khayyam/test_vecs.npy          their routing vectors
  results/khayyam/khayyam_router.json aggregates: per subject, deferral curve, gateway replay
A model is used only when all 1,500 of its answers are stored; nothing is ever paid here.
"""

from __future__ import annotations

import argparse
import shutil
import time

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from metis import khayyam as kh
from metis.config import load_config
from metis.eval.baselines import ZeroRouter
from metis.eval.metrics import area, sweep
from metis.eval.stats import bootstrap
from metis.gateway.failover import ProviderError
from metis.gateway.pipeline import ChatRequest
from metis.llm.budget import Budget, BudgetRefused, call_cost
from metis.llm.callcache import CallCache, get_or_call
from metis.llm.client import complete
from metis.llm.messages import gen_params
from metis.router.artifact import Meta, RouterArtifact, save_artifact
from metis.router.route import cluster_choices, normalize_costs
from metis.router.select_k import fit_psi, halvings
from metis.router.select_lambda import lambda_grid


def stored_answers(df, labeled, models):
    """Every model's answer from the call cache. The stage is locked at $0, so a missing answer
    raises instead of being bought."""
    cache, cfg = CallCache(), load_config("gen_config")
    budget = Budget(cache)
    budget.config = {**budget.config, "approved_usd": {**budget.config["approved_usd"], "khayyam": 0}}
    out = {}
    for m in models:
        params = gen_params(m, cfg, 300)
        for i in labeled:
            row = df.iloc[i]
            try:
                r = get_or_call(cache, budget, "khayyam", m, kh.messages(row), params, "khayyam-v1", 1e-6, complete, prompt_id=row.id)
            except BudgetRefused:
                raise SystemExit(f"{m}: answer for question {row.id} is not stored; run the paid step first") from None
            if r.status == "ok":
                x = r.response
                out[(row.id, m)] = {"text": x.text, "t_in": x.tokens_in, "t_out": x.tokens_out, "ms": x.latency_ms,
                                    "cut": x.finish_reason == "length"}
    return out, budget


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="", help="extra models whose 1,500 answers are already stored")
    args = ap.parse_args()
    t0 = time.perf_counter()
    models = kh.BASE_MODELS + [m for m in args.models.split(",") if m]
    df = kh.load()
    val, test, train = kh.split(len(df))
    vecs = np.load(kh.OUT / "vecs.npy")
    labeled = np.concatenate([val, test])
    ans, budget = stored_answers(df, labeled, models)

    loss = np.ones((len(df), len(models)))
    t_in, t_out = np.zeros(len(models)), np.zeros(len(models))
    for j, m in enumerate(models):
        got = [ans[(df.id.iloc[i], m)] for i in labeled if (df.id.iloc[i], m) in ans]
        t_in[j], t_out[j] = np.mean([g["t_in"] for g in got]), np.mean([g["t_out"] for g in got])
        for i in labeled:
            r = ans.get((df.id.iloc[i], m))
            loss[i, j] = 0.0 if r and not r["cut"] and kh.parse(r["text"]) == df.key.iloc[i] else 1.0
    usd = np.array([call_cost(budget.models[m], t_in[j], t_out[j]) for j, m in enumerate(models)])
    c_hat = normalize_costs(usd)

    rcfg = load_config("pipeline")["router"]
    lams = lambda_grid(rcfg["lambda_n"], rcfg["lambda_low"], rcfg["lambda_high"])
    Lv, Lt = loss[val], loss[test]
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    fit_rows = train[:12000]
    cands, k_scores = {}, {}
    for k in (1, 3, 4, 5, 6, 7, 8):
        km = KMeans(k, n_init=10, random_state=kh.SEED).fit(vecs[fit_rows])
        cands[k] = km
        lv = km.predict(vecs[val])
        s = []
        for a, b in halvings(len(val), 20, kh.SEED):
            for fit, sc in ((a, b), (b, a)):
                s.append(area(*sweep(lv[sc], fit_psi(Lv[fit], lv[fit], k), c_hat, lams, Lv[sc]), c_min, c_max))
        k_scores[k] = float(np.mean(s))
    k_star = max((k for k in k_scores if k > 1), key=lambda k: (round(k_scores[k], 6), -k))
    km = cands[k_star]
    lv, lt, lfit = km.predict(vecs[val]), km.predict(vecs[test]), km.predict(vecs[fit_rows])
    psi = fit_psi(Lv, lv, k_star)
    q_v = sweep(lv, psi, c_hat, lams, Lv)[1]
    best = int(np.argmin(Lv.mean(0)))
    ok = np.flatnonzero(q_v >= 1 - Lv[:, best].mean() - 0.02)
    lam = float(lams[ok[-1]])

    names, taken = [], set()
    purity = [df.category.iloc[fit_rows[lfit == k]].value_counts(normalize=True).iloc[0] for k in range(k_star)]
    for k in sorted(range(k_star), key=lambda k: -purity[k]):  # the purest cluster keeps the plain name
        rows_k = fit_rows[lfit == k]
        names.append((k, kh.subject_name(df.category.iloc[rows_k], df.course.iloc[rows_k], taken)))
        taken.add(names[-1][1]["en"])
    names = [n for _, n in sorted(names)]
    meta = Meta(method="point", embedder_id="nano", k_star=k_star, cluster_names=tuple(n["en"] for n in names),
                models=tuple(models), prices={m: {"in": budget.models[m]["price_in"], "out": budget.models[m]["price_out"]} for m in models},
                lam=lam, lambda_mode="quality-val", lambda_target=float(1 - Lv[:, best].mean() - 0.02), router_type="uniroute",
                hashes={"dataset": "khayyam", "val_set": str(abs(hash(tuple(val.tolist()))) % 10**12)}, build_date=kh.stamp(), tau=0.5)
    art = RouterArtifact(meta=meta, centroids=km.cluster_centers_.astype(float), psi=psi.astype(float),
                         counts=np.bincount(lv, minlength=k_star).astype(int), c_hat=c_hat)
    shutil.rmtree(kh.ARTIFACT, ignore_errors=True)
    save_artifact(art, kh.ARTIFACT)

    # Demo table: test questions, every model's stored answer (local, git-ignored).
    rows = []
    for pos, i in enumerate(test):
        r0 = df.iloc[i]
        for j, m in enumerate(models):
            a = ans.get((r0.id, m), {})
            rows.append({"id": r0.id, "pos": pos, "cluster": int(lt[pos]), "q": r0.q, "choices": list(r0.choices), "key": r0.key,
                         "course": r0.course, "model": m, "text": a.get("text"), "t_in": a.get("t_in", 0), "t_out": a.get("t_out", 0),
                         "ms": a.get("ms"), "cut": bool(a.get("cut", True)), "answer": kh.parse(a.get("text")) if a else None,
                         "correct": bool(loss[i, j] == 0), "usd": call_cost(budget.models[m], a.get("t_in", 0), a.get("t_out", 0)) if a else 0.0})
    demo = pd.DataFrame(rows)
    demo.to_parquet(kh.DEMO, index=False)
    np.save(kh.OUT / "test_vecs.npy", vecs[test])

    # Offline numbers on test.
    curve_c, curve_q = sweep(lt, psi, c_hat, lams, Lt)
    zero = ZeroRouter(Lv, c_hat)
    pick = cluster_choices(psi, c_hat, np.array([lam]))[0]
    routed = 1 - Lt[np.arange(len(test)), pick[lt]]
    gain = bootstrap(lambda ix: area(*sweep(lt[ix], psi, c_hat, lams, Lt[ix]), c_min, c_max)
                     - area(*zero.curve(None, None, Lt[ix]), c_min, c_max), np.arange(len(test)), 500, kh.SEED)
    per = []
    for k in range(k_star):
        tv, tt = lv == k, lt == k
        per.append({"cluster": k, "name_en": names[k]["en"], "name_fa": names[k]["fa"], "n_val": int(tv.sum()), "n_test": int(tt.sum()),
                    "val": {m: float(1 - Lv[tv, j].mean()) for j, m in enumerate(models)},
                    "test": {m: float(1 - Lt[tt, j].mean()) for j, m in enumerate(models)},
                    "pick": models[pick[k]]})

    # The same 1,100 questions through the Khayyam gateway (replay of stored answers).
    gw = kh.build_gateway()
    tv_ = np.load(kh.OUT / "test_vecs.npy")

    def replay(down: set[str] = frozenset()):
        provider = gw.provider
        if down:
            class Down:
                def call(self, model, msgs, ctx):
                    if model in down:
                        raise ProviderError("down")
                    return provider.call(model, msgs, ctx)
            gw.provider = Down()
        res = []
        try:
            for pos, i in enumerate(test):
                r0 = df.iloc[i]
                out = gw.handle(ChatRequest(kh.messages(r0), "takrouter", "khayyam", None, prompt_id=r0.id, vector=tv_[pos]))
                res.append({"ok": out.trace["status"] == "ok", "correct": kh.parse(out.text) == r0.key and out.trace["status"] == "ok",
                            "model": out.model, "cost": out.trace["cost_usd"], "ms": out.trace["latency_ms"], "esc": out.trace["escalations"]})
        finally:
            gw.provider = provider
            for b in gw.breakers.values():
                b.recent.clear(); b.opened_at = None
        r = pd.DataFrame(res)
        return {"accuracy": float(r.correct.mean()), "failed": float(1 - r.ok.mean()), "usd_per_1k": float(r.cost.mean() * 1000),
                "latency_p50_ms": float(r.ms.median()), "latency_p90_ms": float(r.ms.quantile(.9)), "escalated": float((r.esc > 0).mean()),
                "shares": r.model.value_counts(normalize=True).round(4).to_dict()}

    gateway = {"normal": replay(), "outage_" + models[pick[np.bincount(lt).argmax()]]: replay({models[pick[np.bincount(lt).argmax()]]})}
    data = {"built": kh.stamp(), "models": models, "k_star": k_star, "k_scores": k_scores, "lambda": lam, "c_hat": c_hat.tolist(),
            "usd_per_call": usd.tolist(), "n_val": len(val), "n_test": len(test), "n_cluster_fit": len(fit_rows),
            "test_accuracy": {m: float(1 - Lt[:, j].mean()) for j, m in enumerate(models)},
            "router_accuracy": float(routed.mean()), "router_cost": float(c_hat[pick[lt]].mean()),
            "area_router": area(curve_c, curve_q, c_min, c_max), "area_zero": area(*zero.curve(None, None, Lt), c_min, c_max),
            "area_gain": gain.estimate, "area_gain_ci": [gain.low, gain.high],
            "curve": [{"lam": float(lam_), "cost": float(c), "acc": float(q)} for lam_, c, q in zip(lams, curve_c, curve_q, strict=True)],
            "clusters": per, "gateway_replay": gateway, "seconds": round(time.perf_counter() - t0, 1)}
    kh.write_json(kh.summary_path(), data)
    print({k: v for k, v in data.items() if k not in ("curve", "clusters", "k_scores")})


if __name__ == "__main__":
    main()
