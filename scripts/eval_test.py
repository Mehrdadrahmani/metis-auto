"""WP-19: the single look at the test set, as `results/eval_protocol.md` says. No choices are made here.

Usage: uv run python scripts/eval_test.py     Reruns recompute the same numbers.
Writes results/final/ (aggregates only). Replay costs $0; the live run is separate.
"""

from __future__ import annotations

import glob
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from router_check import MODELS, cluster_labels, load_val, vectors
from s18_replay import load_answers

from metis.config import load_config
from metis.data.sealed import read_sealed_parquet
from metis.eval.baselines import LogisticRouter
from metis.eval.metrics import area, qnc
from metis.eval.report import metrics
from metis.eval.stats import bootstrap, mcnemar_exact
from metis.llm.client import load_models
from metis.router.artifact import load_artifact
from metis.router.kmeans import assign
from metis.router.route import cluster_choices
from metis.router.select_k import fit_psi
from metis.router.select_lambda import lambda_grid
from metis.sim.replay import Settings, Traffic, run

OUT = Path("results/final")
SEED = 20261020
DEEPSEEK, LUNA, GEMINI, SONNET = range(4)


def pct(x):
    return f"{x:.1%}"


def points(choices, loss, cost):
    """Quality and dollars per (setting, prompt) for a (L, n) matrix of chosen models."""
    rows = np.arange(loss.shape[0])
    return 1 - loss[rows, choices], cost[rows, choices]


def curve_area(q, c, idx, cost_norm, c_min, c_max):
    return area(cost_norm[:, idx].mean(1), q[:, idx].mean(1), c_min, c_max)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    changed = subprocess.run(["git", "diff", "pre-test", "--stat", "--", "artifacts", "results/eval_protocol.md"], capture_output=True, text=True).stdout.strip()
    ids = sorted(json.loads(Path("runs/s2/test_ids.sealed").read_text(encoding="utf-8")))
    labels = read_sealed_parquet("runs/s7/labels_test.sealed.parquet")
    responses = read_sealed_parquet("runs/s6/responses_test.sealed.parquet")
    repeats = read_sealed_parquet("runs/s7/noise_pointwise_jev_test.sealed.parquet")

    wide = labels.pivot(index="prompt_id", columns="model_id", values="loss")[MODELS]
    refused = int(wide.isna().any(axis=1).sum())
    order = sorted(wide.dropna().index)
    loss = wide.loc[order].to_numpy(float)
    meta = pd.read_parquet("runs/s1/prompts.parquet", columns=["prompt_id", "session_id", "msg_index", "bot_id", "system_prompt_id", "text_norm", "demands_json", "uses_rag", "has_image", "timestamp", "text_chars", "prod_model"], filters=[("prompt_id", "in", ids)]).set_index("prompt_id")
    groups = np.unique(meta.loc[order, "session_id"].to_numpy(), return_inverse=True)[1]
    x = vectors(order)
    n = len(order)

    known = load_models()
    tok = responses.pivot(index="prompt_id", columns="model_id", values="tokens_in").reindex(order)[MODELS].fillna(0).to_numpy()
    out_t = responses.pivot(index="prompt_id", columns="model_id", values="tokens_out").reindex(order)[MODELS].fillna(0).to_numpy()
    usd = np.stack([(tok[:, j] * known[m]["price_in"] + out_t[:, j] * known[m]["price_out"]) / 1e6 for j, m in enumerate(MODELS)], 1)

    art8, art4 = load_artifact("artifacts/router_v1"), load_artifact("artifacts/router_v1_k4")
    c_hat = art8.c_hat
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    cl8, cl4 = assign(x, art8.centroids), assign(x, art4.centroids)
    rows = np.arange(n)
    pick8 = cluster_choices(art8.psi, c_hat, np.array([art8.meta.lam]))[0][cl8]
    pick4 = cluster_choices(art4.psi, c_hat, np.array([art4.meta.lam]))[0][cl4]
    pass_all = 1 - loss
    r8, r4 = pass_all[rows, pick8], pass_all[rows, pick4]
    usd8, usd4 = usd[rows, pick8], usd[rows, pick4]

    def diff(a, b):
        return bootstrap(lambda i: float(a[i].mean() - b[i].mean()), groups, 10_000, SEED)

    prim = {}
    for name, a, cost in (("K = 8", r8, usd8), ("K = 4", r4, usd4)):
        for base, j in (("Sonnet", SONNET), ("DeepSeek", DEEPSEEK)):
            d = diff(a, pass_all[:, j])
            _, _, p = mcnemar_exact(a.astype(bool), pass_all[:, j].astype(bool))
            prim[f"{name} vs {base}"] = {"diff": d.estimate, "low": d.low, "high": d.high, "mcnemar_p": p, "cost_ratio": float(cost.mean() / usd[:, j].mean())}

    order_val, val_loss, val_groups, _ = load_val()
    xv = vectors(order_val)
    val_labels = cluster_labels(xv)
    cfg = load_config("pipeline")["router"]
    lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])

    def sweep_router(psi_by_cluster, cl):
        return cluster_choices(psi_by_cluster, c_hat, lams)[:, cl]

    grids = {"UniRoute K = 8": sweep_router(art8.psi, cl8), "UniRoute K = 4": sweep_router(art4.psi, cl4),
             "UniRoute K = 1": sweep_router(val_loss.mean(0, keepdims=True), np.zeros(n, int))}
    unit_t, unit_v = x / np.linalg.norm(x, axis=1, keepdims=True), xv / np.linalg.norm(xv, axis=1, keepdims=True)
    near = np.argsort(-(unit_t @ unit_v.T), axis=1)[:, :80]
    gamma_knn = val_loss[near].mean(1)
    gamma_log = LogisticRouter(xv, val_loss, c_hat, SEED, val_groups).predict_loss(x)
    from metis.router.route import rank_models  # noqa: PLC0415

    def per_prompt(gamma):
        return np.array([[rank_models(g + lam * c_hat, c_hat)[0] for g in gamma] for lam in lams])

    grids["K-NN k = 80"], grids["Logistic"] = per_prompt(gamma_knn), per_prompt(gamma_log)
    fixed = np.stack([np.full(n, j) for j in range(4)])
    grids["ZeroRouter"] = fixed  # area interpolates between single models, which is its mix
    grids["Always-cheapest"] = fixed[[GEMINI]]
    grids["Always-Sonnet"] = fixed[[SONNET]]
    mats = {}
    for name, g in grids.items():
        mats[name] = (1 - loss[rows[None, :], g], c_hat[g])

    def area_of(name, idx):
        q, c = mats[name]
        return area(c[:, idx].mean(1), q[:, idx].mean(1), c_min, c_max)

    full = rows
    q_best, c_best = pass_all[:, SONNET].mean(), c_hat[SONNET]
    ladder = []
    base8 = "UniRoute K = 8"
    for name in grids:
        q, c = mats[name]
        d = bootstrap(lambda i, nm=name: area_of(nm, i) - area_of(base8, i), groups, 2000 if name not in ("UniRoute K = 4", "ZeroRouter") else 10_000, SEED)
        ladder.append({"router": name, "area": area_of(name, full), "minus_k8": d.estimate, "low": d.low, "high": d.high,
                       "qnc": qnc(c.mean(1), q.mean(1), q_best, c_best), "qnc1": qnc(c.mean(1), q.mean(1), q_best - 0.01, c_best)})

    from metis.router.fingerprints import fingerprints  # noqa: PLC0415

    psi2 = fingerprints(val_loss, val_labels[8], 8, alpha=2.0).psi
    pick_a2 = cluster_choices(psi2, c_hat, np.array([art8.meta.lam]))[0][cl8]
    alpha2 = {"pass": float(pass_all[rows, pick_a2].mean()), "cost": float(usd[rows, pick_a2].mean())}

    budget_points = {}
    for label, art, cl, lam in (("K = 8 budget λ 0", art8, cl8, 0.0), ("K = 4 budget λ 0.007038", art4, cl4, 0.007038)):
        pick = cluster_choices(art.psi, c_hat, np.array([lam]))[0][cl]
        budget_points[label] = {"pass": float(pass_all[rows, pick].mean()), "usd_1k": float(usd[rows, pick].mean() * 1000)}

    dev = [0, 1, 3]
    psi_dev = art8.psi[:, dev]
    hold_grid = np.array(dev)[cluster_choices(psi_dev, c_hat[dev], lams)[:, cl8]]
    holdout = {"without": float(area(c_hat[hold_grid].mean(1), (1 - loss[rows[None, :], hold_grid]).mean(1), c_min, c_max)), "with": area_of(base8, full)}

    per_cluster = []
    for k in range(8):
        on = cl8 == k
        if on.any():
            per_cluster.append({"cluster": k, "name": art8.meta.cluster_names[k], "n": int(on.sum()), "router": float(r8[on].mean()), "deepseek": float(pass_all[on, 0].mean()), "sonnet": float(pass_all[on, 3].mean()), "usd_1k": float(usd8[on].mean() * 1000)})
    chars = meta.loc[order, "text_chars"].to_numpy(float)
    edges = np.quantile(chars, [1 / 3, 2 / 3])
    tercile = np.digitize(chars, edges)
    by_len = [{"tercile": t, "n": int((tercile == t).sum()), "router": float(r8[tercile == t].mean()), "deepseek": float(pass_all[tercile == t, 0].mean()), "sonnet": float(pass_all[tercile == t, 3].mean())} for t in range(3)]

    first = labels.set_index(["prompt_id", "model_id"]).score
    rep = repeats[repeats.score.notna()]
    gap = np.abs(rep.score.to_numpy() - first.reindex(pd.MultiIndex.from_frame(rep[["prompt_id", "model_id"]])).to_numpy())
    flips = (rep.score.to_numpy() >= 7) != (first.reindex(pd.MultiIndex.from_frame(rep[["prompt_id", "model_id"]])).to_numpy() >= 7)

    # production
    prod = meta.loc[order, "prod_model"]
    priced = prod.map(lambda m: m in known)
    prod_usd = np.array([(tok[i, 0] * known[m]["price_in"] + out_t[i, 0] * known[m]["price_out"]) / 1e6 if m in known else np.nan for i, m in enumerate(prod)])
    answers = responses[responses.status == "ok"].set_index(["prompt_id", "model_id"]).text
    sim = production_similarity(order, answers, pick8, pick4)

    # replay
    tr = Traffic([p for _, p in sorted(zip(meta.loc[order].timestamp, order, strict=True), key=lambda t: (t[0], t[1]))], np.empty((0,)), meta, pd.DataFrame(loss, index=order, columns=MODELS), np.array([]))
    pos = {p: i for i, p in enumerate(order)}
    rank = np.array([pos[p] for p in tr.ids])
    tr.vectors, tr.groups = x[rank], groups[rank]
    stored = load_answers(responses)
    replay = {}
    for s in (Settings("TakRouter plain"), Settings("TakRouter with cache and checks", cache=True, checks=True), Settings("Always Sonnet", fixed_model="claude-sonnet-5-5"), Settings("Always DeepSeek", fixed_model="deepseek-v4-flash"),
              Settings("10-minute outage of DeepSeek", cache=True, checks=True, outage=(100, 200), outage_model="deepseek-v4-flash")):
        replay[s.name] = metrics(run(tr, stored, art8, s), tr.groups)
    c1 = 1 - prim["K = 8 vs Sonnet"]["cost_ratio"] >= 0.40
    c2 = prim["K = 8 vs Sonnet"]["low"] >= -0.05
    c3 = replay["TakRouter plain"]["p90"] <= replay["Always Sonnet"]["p90"]
    ds = prim["K = 8 vs DeepSeek"]
    adds = ds["low"] > 0 and ds["cost_ratio"] <= 1.10

    data = dict(n=n, refused=refused, head=head, frozen_changed=changed, primary=prim, pass_rates={m: float(pass_all[:, j].mean()) for j, m in enumerate(MODELS)} | {"K = 8": float(r8.mean()), "K = 4": float(r4.mean())},
                usd_1k={m: float(usd[:, j].mean() * 1000) for j, m in enumerate(MODELS)} | {"K = 8": float(usd8.mean() * 1000), "K = 4": float(usd4.mean() * 1000)},
                shares={"K = 8": np.bincount(pick8, minlength=4).tolist(), "K = 4": np.bincount(pick4, minlength=4).tolist()}, ladder=ladder, alpha2=alpha2, budget_points=budget_points, holdout=holdout,
                per_cluster=per_cluster, by_length=by_len, repeats={"n": int(len(rep)), "mean_gap": float(np.nanmean(gap)), "pass_flips": float(np.mean(flips))},
                production={"priced_share": float(priced.mean()), "usd_1k_priced": float(np.nanmean(prod_usd)) * 1000, "top_models": prod.value_counts().head(6).to_dict()}, similarity=sim, replay=replay,
                criteria={"cost_40": bool(c1), "noninferior": bool(c2), "latency": bool(c3), "adds_over_deepseek": bool(adds)})
    (OUT / "final.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps({k: data[k] for k in ("n", "refused", "primary", "pass_rates", "usd_1k", "shares", "criteria", "frozen_changed")}, indent=1, default=float))


def production_similarity(order, answers, pick8, pick4):
    """Mean cosine to production's answer, nano vectors. Similarity is not quality (M15)."""
    from metis.gateway.app import ROOT
    from metis.embed.embedder import Embedder

    prod = pd.concat(pd.read_parquet(p, columns=["prompt_id", "prod_answer"], filters=[("prompt_id", "in", order)]) for p in sorted(glob.glob("runs/s1/context/part-*.parquet"))).set_index("prompt_id").prod_answer
    s4 = load_config("pipeline")["s4"]
    c = s4["candidates"][s4["choice"]]
    e = Embedder(c["name"], c["revision"], device="cpu", path=str(ROOT / c["path"]), task=s4["task"], prompt_name=s4["prompt_name"], merge_adapter=True, max_tokens=s4["max_tokens"], batch_size=8, max_batch_tokens=8192)

    def vec(texts):
        v = e.encode(texts)
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    have = [i for i, p in enumerate(order) if isinstance(prod.get(p), str) and prod.get(p).strip()]
    pv = vec([prod[order[i]] for i in have])
    out = {}
    tables = {}
    for j, m in enumerate(MODELS):
        ok = [t for t, i in enumerate(have) if (order[i], m) in answers.index]
        v = vec([answers[(order[have[t]], m)] for t in ok])
        table = np.full(len(have), np.nan)
        table[ok] = (v * pv[ok]).sum(1)
        tables[j] = table
        out[m] = float(np.nanmean(table))
    for name, pick in (("K = 8", pick8), ("K = 4", pick4)):
        out[name] = float(np.nanmean([tables[pick[i]][t] for t, i in enumerate(have)]))
    return out | {"n": len(have)}


if __name__ == "__main__":
    main()
