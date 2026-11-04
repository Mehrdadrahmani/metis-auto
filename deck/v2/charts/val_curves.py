"""Held-out deferral curves on validation (one 2-fold split), for the deck. Validation only, $0.

Run from the repo root: uv run python <this file> <out.json>
"""
import json
import sys

sys.path.insert(0, "scripts")
import numpy as np
from router_check import MODELS, SEED, cluster_labels, load_val, vectors

from metis.config import load_config
from metis.eval.baselines import LogisticRouter, ZeroRouter
from metis.eval.metrics import area, sweep
from metis.router.select_k import fit_psi, halvings
from metis.router.select_lambda import lambda_grid

cfg = load_config("pipeline")["router"]
order, losses, groups, c_hat = load_val()
x = vectors(order)
labels = cluster_labels(x)
lams = lambda_grid(cfg["lambda_n"], cfg["lambda_low"], cfg["lambda_high"])
n = len(losses)
a, b = next(iter(halvings(n, 1, SEED, groups)))
unit = x / np.linalg.norm(x, axis=1, keepdims=True)
KNN = 80

curves = {}


from metis.eval.metrics import pareto_envelope

GRID = np.geomspace(float(c_hat.min()), float(c_hat.max()), 80)


def add(name, fn):
    # each half's Pareto envelope, read at common budgets (flat outside its range), size-weighted
    qs = []
    for fit, score in ((a, b), (b, a)):
        c, q = fn(fit, score)
        ec, eq = pareto_envelope(np.asarray(c), np.asarray(q))
        qg = np.interp(GRID, ec, eq)
        qg[GRID < ec[0]] = np.nan
        qs.append(qg * len(score) / n)
    q = qs[0] + qs[1]
    keep = ~np.isnan(q)
    curves[name] = {"cost": GRID[keep].tolist(), "quality": q[keep].tolist()}


for k in (8, 4):
    add(f"UniRoute K = {k}", lambda f, s, k=k: sweep(labels[k][s], fit_psi(losses[f], labels[k][f], k), c_hat, lams, losses[s]))
add("ZeroRouter", lambda f, s: ZeroRouter(losses[f], c_hat).curve(None, None, losses[s]))


def knn(f, s):
    sims = unit[s] @ unit[f].T
    near = np.argsort(-sims, axis=1, kind="stable")[:, :KNN]
    return sweep(np.arange(len(s)), losses[f][near].mean(1), c_hat, lams, losses[s])


add(f"K-NN k = {KNN}", knn)
add("Logistic", lambda f, s: sweep(np.arange(len(s)), LogisticRouter(x[f], losses[f], c_hat, SEED, groups[f]).predict_loss(x[s]), c_hat, lams, losses[s]))

c_min, c_max = float(c_hat.min()), float(c_hat.max())
out = {
    "n": n,
    "models": MODELS,
    "c_hat": c_hat.tolist(),
    "single_quality": (1 - losses.mean(0)).tolist(),
    "curves": curves,
    "areas": {k: area(np.array(v["cost"]), np.array(v["quality"]), c_min, c_max) for k, v in curves.items()},
}
json.dump(out, open(sys.argv[1], "w"), indent=1)
print({k: round(v, 4) for k, v in out["areas"].items()}, "c_hat", np.round(c_hat, 4), "single", np.round(out["single_quality"], 3))
