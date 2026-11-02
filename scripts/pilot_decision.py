"""WP-11 steps 2 to 6: pilot decision numbers from stored scores and labels. No API calls.

Reference labels are Opus (D-098, DEV-14), not human. Jev judgments come from runs/s7_history (D-103).
Only pilot prompts are touched; test rows are filtered out before any join.
Usage: uv run python scripts/pilot_decision.py
Writes results/pilot_decision.json (aggregates only).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from metis.config import load_config
from metis.eval.metrics import area, sweep
from metis.eval.stats import (
    balanced_accuracy,
    cohen_kappa,
    fingerprint_stability,
    separability,
    wilson_ci,
)
from metis.router.route import normalize_costs
from metis.router.select_k import fit_psi, halvings
from metis.router.select_lambda import lambda_grid

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261020
ANCHOR = "claude-sonnet-5-5"
PRO = "deepseek-v4-pro"
CANDIDATES = ["deepseek-v4-flash", "gpt-5.6-luna", "gemini-2.5-flash-lite", ANCHOR]
TAUS = list(range(4, 10))
BOOT = 2000
CUT_CHARS = 18_000  # instructions_max_tokens 6000 x chars_per_token 3


def rate(k: int, n: int) -> dict:
    lo, hi = wilson_ci(k, n)
    return {"value": round(k / n, 3) if n else None, "n": n, "ci": [round(lo, 3), round(hi, 3)]}


def agree(truth: np.ndarray, pred: np.ndarray) -> dict:
    truth, pred = np.asarray(truth, bool), np.asarray(pred, bool)
    both = truth.any() and (~truth).any()
    return {
        **rate(int((truth == pred).sum()), len(truth)),
        "balanced": round(balanced_accuracy(truth, pred), 3) if both else None,
        "kappa": round(cohen_kappa(truth, pred), 3)
        if both and pred.any() and (~pred).any()
        else None,
    }


def boot_ci(fn, n: int, rng: np.random.Generator) -> list[float]:
    vals = []
    for _ in range(BOOT):
        v = fn(rng.integers(0, n, n))
        if not np.isnan(v):
            vals.append(v)
    return [round(float(x), 3) for x in np.percentile(vals, [2.5, 97.5])]


def safe_kappa(a: np.ndarray, b: np.ndarray) -> float:
    if len(set(a)) < 2 or len(set(b)) < 2:
        return float("nan")
    return cohen_kappa(a, b)


def best_tau(score: np.ndarray, truth: np.ndarray) -> int:
    """Balanced accuracy, ties to the higher tau (WP-11 step 2)."""
    best, pick = -1.0, TAUS[0]
    for t in TAUS:
        pred = score >= t
        b = balanced_accuracy(truth, pred) if len(set(truth)) > 1 else 0.0
        if b >= best - 1e-12:
            best, pick = b, t
    return pick


def soft_h(row_raw: str, order: str) -> float:
    """Jev's chance that h is better, ties split, for one order."""
    p = json.loads(row_raw)["verdict"]["probabilities"]
    h, a = ("B", "A") if order == "a_first" else ("A", "B")
    return float(p.get(h, 0.0)) + 0.5 * float(p.get("tie", 0.0)) + 0.0 * float(p.get(a, 0.0))


def main() -> None:
    t0 = time.perf_counter()
    rng = np.random.default_rng(SEED)
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet")
    split = split[split["in_pilot"]].drop(columns=["split"])
    pids = set(split["prompt_id"])
    assert len(pids) == 100
    meta = pd.read_parquet(
        ROOT / "runs/s1/prompts.parquet",
        columns=["prompt_id", "uses_rag", "instr_chars", "instr_len_bucket", "lang"],
    )
    meta = meta[meta["prompt_id"].isin(pids)].drop(columns=["lang"])
    meta = meta.merge(split[["prompt_id", "session_id", "lang"]], on="prompt_id")

    pt = pd.read_parquet(ROOT / "runs/s7_history/pointwise_jev_pilot.parquet")
    pw = pd.read_parquet(ROOT / "runs/s7_history/pairwise_jev_pilot.parquet")
    resp = pd.read_parquet(
        ROOT / "runs/s6/responses_pilot.parquet",
        columns=["prompt_id", "model_id", "tokens_in", "tokens_out"],
    )
    labels = pd.read_parquet(ROOT / "runs/labeling/opus/opus_labels.parquet")
    for t in (pt, pw, resp, labels):
        assert set(t["prompt_id"]) <= pids
    out: dict = {
        "labels": "Opus, not human (D-098)",
        "judge": "jev, with history (D-103)",
        "n_prompts": 100,
    }

    # Step 2 pointwise
    cal = labels.merge(pt[["prompt_id", "model_id", "score"]], on=["prompt_id", "model_id"]).merge(
        meta, on="prompt_id"
    )
    anc = labels[["prompt_id", "opus_pass_anchor"]].merge(
        pt[pt.model_id == ANCHOR][["prompt_id", "score"]], on="prompt_id"
    )
    truth, score = cal["opus_pass"].to_numpy(), cal["score"].to_numpy()
    assert len(cal) == 100
    out["base_rate_pass"] = {
        "cal": round(float(truth.mean()), 3),
        "anchor": round(float(anc["opus_pass_anchor"].mean()), 3),
    }
    sweep_rows = {}
    for t in TAUS:
        sweep_rows[t] = agree(truth, score >= t) | {
            "judge_pass": round(float((score >= t).mean()), 3)
        }
    tau = best_tau(score, truth)
    out["tau_sweep"] = sweep_rows
    out["tau_star"] = tau
    out["auc"] = round(float(roc_auc_score(truth, score)), 3)
    idx = lambda f: boot_ci(f, len(truth), rng)
    out["pointwise_ci"] = {
        "accuracy": idx(lambda i: float(((score[i] >= tau) == truth[i]).mean())),
        "kappa": idx(lambda i: safe_kappa(truth[i], score[i] >= tau)),
        "auc": idx(
            lambda i: roc_auc_score(truth[i], score[i]) if len(set(truth[i])) > 1 else float("nan")
        ),
    }
    # tau chosen on the same items flatters the result: leave-one-out shows by how much
    loo = np.array(
        [score[i] >= best_tau(np.delete(score, i), np.delete(truth, i)) for i in range(len(truth))]
    )
    out["pointwise_loo"] = agree(truth, loo)
    all_truth = np.concatenate([truth, anc["opus_pass_anchor"].to_numpy()])
    all_score = np.concatenate([score, anc["score"].to_numpy()])
    out["pointwise_with_anchor_items"] = {
        str(t): agree(all_truth, all_score >= t) for t in (tau, 7)
    }
    wide = pt.pivot(index="prompt_id", columns="model_id", values="score")
    out["pass_by_model"] = {
        str(t): {m: round(float((wide[m] >= t).mean()), 3) for m in wide.columns}
        for t in sorted({tau, tau + 1, 7, 8})
    }
    out["mean_score"] = {m: round(float(wide[m].mean()), 3) for m in wide.columns}

    # Step 3 pairwise
    pw["soft"] = [soft_h(r, o) for r, o in zip(pw["raw_output"], pw["order"], strict=True)]
    pw["s"] = pw["verdict"].map({"h": 1.0, "tie": 0.5, "anchor": 0.0})
    both = pw.pivot(
        index=["prompt_id", "model_id"], columns="order", values=["verdict", "s", "soft"]
    )
    both.columns = [f"{a}_{b}" for a, b in both.columns]
    both = both.reset_index()
    both["o"] = (both["s_a_first"].astype(float) + both["s_h_first"].astype(float)) / 2
    both["soft"] = (both["soft_a_first"].astype(float) + both["soft_h_first"].astype(float)) / 2
    both["consistent"] = both["verdict_a_first"] == both["verdict_h_first"]
    n_pairs = len(both)
    out["position"] = {
        "all_models": rate(int(both["consistent"].sum()), n_pairs),
        "candidates_only": rate(
            int(both[both.model_id != PRO]["consistent"].sum()), int((both.model_id != PRO).sum())
        ),
        "tie_rate": round(float((pw["verdict"] == "tie").mean()), 3),
        "h_wins_when_h_is": {
            o: round(float((g["verdict"] == "h").mean()), 3) for o, g in pw.groupby("order")
        },
        "by_model": {
            m: rate(int(g["consistent"].sum()), len(g)) for m, g in both.groupby("model_id")
        },
    }
    pair = labels.merge(both, on=["prompt_id", "model_id"])
    nt = pair[pair["opus_pref"] != "tie"].copy()
    want = (nt["opus_pref"] == "h").to_numpy()
    o = nt["o"].to_numpy()
    decided = o != 0.5
    res = {"non_tie_items": len(nt), "judge_undecided": int((~decided).sum())}
    res["decided_only"] = agree(want[decided], o[decided] > 0.5)
    res["undecided_as_wrong"] = rate(int(((o > 0.5) == want)[decided].sum()), len(nt))
    res["soft_score"] = agree(want, nt["soft"].to_numpy() > 0.5)
    w = nt.merge(wide.reset_index(), on="prompt_id")
    diff = np.array([r[r["model_id"]] - r[ANCHOR] for _, r in w.iterrows()])
    res["pointwise_gap_predicts_pref"] = agree(want, diff > 0)
    res["auc_soft"] = round(float(roc_auc_score(want, nt["soft"])), 3)
    res["auc_pointwise_gap"] = round(float(roc_auc_score(want, diff)), 3)
    for order, col in (("a_first", "verdict_a_first"), ("h_first", "verdict_h_first")):
        v = nt[col].to_numpy()
        keep = v != "tie"
        res[f"single_order_{order}"] = agree(want[keep], v[keep] == "h")
    s = nt["soft"].to_numpy()
    res["soft_ci"] = {
        "accuracy": boot_ci(lambda i: float(((s[i] > 0.5) == want[i]).mean()), len(s), rng),
        "kappa": boot_ci(lambda i: safe_kappa(want[i], s[i] > 0.5), len(s), rng),
    }
    res["hard_ci"] = {
        "kappa": boot_ci(
            lambda i: safe_kappa(want[decided][i], o[decided][i] > 0.5), int(decided.sum()), rng
        ),
    }
    out["pairwise"] = res

    # Step 4 separability, stability, cross-evaluation
    order = sorted(pids)
    sess = meta.set_index("prompt_id").loc[order, "session_id"].to_numpy()
    groups = np.unique(sess, return_inverse=True)[1]
    cfg = load_config("pipeline")
    ids, vecs = [], []
    for p in sorted((ROOT / "runs/s4/full" / cfg["s4"]["choice"]).glob("part-*.npz")):
        with np.load(p) as z:
            keep = np.isin(z["ids"], order)
            ids.append(z["ids"][keep])
            vecs.append(z["vecs"][keep])
    ids, vecs = np.concatenate(ids), np.concatenate(vecs)
    vecs = vecs[pd.Index(ids).get_indexer(order)]
    assert len(vecs) == 100
    cl = {1: np.zeros(100, int)}
    for k in (3, 8):
        with np.load(ROOT / f"runs/s5/view/k_{k:02d}.npz") as z:
            cl[k] = ((vecs[:, None, :] - z["centers"][None, :, :]) ** 2).sum(-1).argmin(1)
    out["cluster_sizes"] = {str(k): np.bincount(v, minlength=k).tolist() for k, v in cl.items()}

    models = CANDIDATES
    a = models.index(ANCHOR)
    sc = wide.loc[order, models].to_numpy()
    loss = {f"pt_tau{t}": (sc < t).astype(float) for t in sorted({tau, tau + 1, 7})}
    ow = both.pivot(index="prompt_id", columns="model_id", values="o").loc[order]
    osoft = both.pivot(index="prompt_id", columns="model_id", values="soft").loc[order]

    def pw_loss(tbl: pd.DataFrame) -> np.ndarray:
        m = np.full((100, len(models)), 0.5)
        for j, name in enumerate(models):
            if name != ANCHOR:
                m[:, j] = 1 - tbl[name].to_numpy(float)
        return m

    loss["pw"] = pw_loss(ow)
    loss["pw_soft"] = pw_loss(osoft)
    sd = {}
    for name, ls in loss.items():
        method = "pw" if name.startswith("pw") else "pt"
        sd[name] = {}
        for k, lab in cl.items():
            psi = fit_psi(ls, lab, k, method, anchor=a)
            d = separability(psi, np.bincount(lab, minlength=k))
            st = (
                fingerprint_stability(
                    ls, lab, k, SEED, repeats=5, groups=groups, method=method, anchor=a
                )
                if k > 1
                else None
            )
            sd[name][str(k)] = {"D": round(d, 3), "C": None if st is None else round(st, 3)}
    out["separability_stability"] = sd

    resp_mean = resp.groupby("model_id")[["tokens_in", "tokens_out"]].mean()
    mcfg = {m["id"]: m for m in load_config("models")["models"]}
    cost = np.array(
        [
            (
                resp_mean.loc[m, "tokens_in"] * mcfg[m]["price_in"]
                + resp_mean.loc[m, "tokens_out"] * mcfg[m]["price_out"]
            )
            / 1e6
            for m in models
        ]
    )
    out["cost_per_answer"] = {m: round(float(c), 6) for m, c in zip(models, cost, strict=True)}
    c_hat = normalize_costs(cost)
    lams = lambda_grid()
    k = 3
    lab = cl[k]
    pairs = halvings(100, 20, SEED, groups)
    pair_tbl = {"router_pt": {"Qpt": [], "Qpw": []}, "router_pw": {"Qpt": [], "Qpw": []}}
    lpt, lpw = loss[f"pt_tau{tau}"], loss["pw"]
    for x, y in pairs:
        for rname, ls, m in (("router_pt", lpt, "pt"), ("router_pw", lpw, "pw")):
            psi = fit_psi(ls[x], lab[x], k, m, anchor=a)
            for qname, q in (("Qpt", lpt), ("Qpw", lpw)):
                cs, qs = sweep(lab[y], psi, c_hat, lams, q[y])
                pair_tbl[rname][qname].append(area(cs, qs, float(c_hat.min()), float(c_hat.max())))
    out["cross_eval_informative_underpowered"] = {
        r: {q: [round(float(np.mean(v)), 3), round(float(np.std(v)), 3)] for q, v in t.items()}
        for r, t in pair_tbl.items()
    }

    # Step 5 bias and noise
    tok = pt.merge(resp, on=["prompt_id", "model_id"])
    per = []
    for _, g in tok.groupby("prompt_id"):
        if g["tokens_out"].nunique() > 1 and g["score"].nunique() > 1:
            per.append(spearmanr(g["score"], g["tokens_out"]).statistic)
    dem = tok.assign(
        s=tok["score"] - tok.groupby("prompt_id")["score"].transform("mean"),
        t=tok["tokens_out"] - tok.groupby("prompt_id")["tokens_out"].transform("mean"),
    )
    out["length_bias"] = {
        "mean_within_prompt_rho": round(float(np.mean(per)), 3),
        "n_prompts": len(per),
        "pooled_demeaned_rho": round(float(spearmanr(dem["s"], dem["t"]).statistic), 3),
    }
    tk = resp.pivot(index="prompt_id", columns="model_id", values="tokens_out")
    lp = pw[pw["verdict"] != "tie"].copy()
    lp["h_len"] = [tk.at[p, m] for p, m in zip(lp["prompt_id"], lp["model_id"], strict=True)]
    lp["a_len"] = lp["prompt_id"].map(tk[ANCHOR])
    lp = lp[lp["h_len"] != lp["a_len"]]
    longer = (lp["verdict"] == "h") == (lp["h_len"] > lp["a_len"])
    out["length_bias"]["pairwise_longer_wins"] = rate(int(longer.sum()), len(lp))
    out["length_bias"]["sonnet_longer_share"] = round(float((lp["a_len"] > lp["h_len"]).mean()), 3)
    lh = lp[lp["h_len"] > lp["a_len"]]
    out["length_bias"]["h_win_when_h_longer"] = rate(int((lh["verdict"] == "h").sum()), len(lh))
    ls_ = lp[lp["h_len"] < lp["a_len"]]
    out["length_bias"]["h_win_when_h_shorter"] = rate(int((ls_["verdict"] == "h").sum()), len(ls_))

    cal["pred"] = cal["score"] >= tau
    cal["agree"] = cal["pred"] == cal["opus_pass"]
    by = {}
    by["model"] = {
        m: agree(g["opus_pass"], g["pred"])
        | {
            "judge_over": int((g["pred"] & ~g["opus_pass"]).sum()),
            "judge_under": int((~g["pred"] & g["opus_pass"]).sum()),
        }
        for m, g in cal.groupby("model_id")
    }
    cal["cut"] = cal["instr_chars"] > CUT_CHARS
    cal["persian"] = cal["lang"] == "fa"
    for name, col in (
        ("rag", "uses_rag"),
        ("instr_bucket", "instr_len_bucket"),
        ("instr_cut", "cut"),
        ("persian", "persian"),
    ):
        by[name] = {str(v): agree(g["opus_pass"], g["pred"]) for v, g in cal.groupby(col)}
    out["pointwise_groups"] = by
    nt2 = nt.merge(meta, on="prompt_id")
    nt2["agree"] = (nt2["soft"] > 0.5) == (nt2["opus_pref"] == "h")
    out["pairwise_groups_soft"] = {
        "model": {m: rate(int(g["agree"].sum()), len(g)) for m, g in nt2.groupby("model_id")},
        "persian": {
            str(v): rate(int(g["agree"].sum()), len(g)) for v, g in nt2.groupby(nt2["lang"] == "fa")
        },
        "rag": {str(v): rate(int(g["agree"].sum()), len(g)) for v, g in nt2.groupby("uses_rag")},
    }
    pref = labels["opus_pref"].value_counts().to_dict()
    out["opus_pref_counts"] = {str(k_): int(v) for k_, v in pref.items()}

    # Sonnet against deepseek-v4-pro
    dp = (wide[PRO] - wide[ANCHOR]).to_numpy()
    bs = [float(dp[rng.integers(0, 100, 100)].mean()) for _ in range(BOOT)]
    po = both[both.model_id == PRO]
    co = resp_mean.loc[[PRO, ANCHOR]]
    out["pro_vs_sonnet"] = {
        "mean_gap_pro_minus_sonnet": round(float(dp.mean()), 3),
        "gap_ci": [round(float(x), 3) for x in np.percentile(bs, [2.5, 97.5])],
        "pairwise_o": round(float(po["o"].mean()), 3),
        "pairwise_soft": round(float(po["soft"].mean()), 3),
        "pro_cost_per_answer": round(
            float(
                (
                    co.loc[PRO, "tokens_in"] * mcfg[PRO]["price_in"]
                    + co.loc[PRO, "tokens_out"] * mcfg[PRO]["price_out"]
                )
                / 1e6
            ),
            6,
        ),
    }
    out["pairwise_o_by_model"] = {
        m: round(float(g["o"].mean()), 3) for m, g in both.groupby("model_id")
    }
    out["pairwise_soft_by_model"] = {
        m: round(float(g["soft"].mean()), 3) for m, g in both.groupby("model_id")
    }
    out["seconds"] = round(time.perf_counter() - t0, 1)
    (ROOT / "results/pilot_decision.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, indent=None)[:200], "... written")


if __name__ == "__main__":
    main()
