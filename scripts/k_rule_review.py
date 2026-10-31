"""K-rule review (Q-025): four ways to set K on 8 simulated scenarios, 100 fresh datasets each.

Usage: uv run python scripts/k_rule_review.py results/wp05_router/k_rule_review.json
Seeds 5000-5099, not used to design the rule. Simulated data only, $0.
"""

import json
import sys

sys.path.insert(0, "tests")
import collections

import numpy as np

from metis.eval.metrics import area, sweep
from metis.router.fingerprints import fail_rates
from metis.router.kmeans import *
from metis.router.route import normalize_costs
from metis.router.select_k import select_k
from metis.router.select_lambda import lambda_grid
from synthetic import COSTS, Bed, _split

C = normalize_costs(COSTS)
L = lambda_grid()
Ks = [3, 4, 5, 6, 7, 8]
DIM = 64


def bed(seed, rates, spread):
    r = np.random.default_rng(seed)
    n = len(rates)
    c = r.normal(size=(n, DIM))
    c /= np.linalg.norm(c, axis=1, keepdims=True)
    return Bed(
        _split(3000, c, rates, r, spread),
        _split(400, c, rates, r, spread),
        _split(300, c, rates, r, spread),
        rates,
    )


def rates(seed, t, lo, hi):
    # each group: random one or two cheap models weak; strong steady
    r = np.random.default_rng(seed + 77)
    R = np.full((t, 4), lo)
    for g in range(t):
        R[g, :3] = lo + (hi - lo) * (r.random(3) < 0.5)
    # guarantee distinct rows where possible
    if t <= 3:
        for g in range(t):
            R[g, :3] = lo
            R[g, g] = hi
    if t == 6:
        pats = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1)]
        for g, p in enumerate(pats):
            R[g, :3] = [hi if x else lo for x in p]
    return R


scen = {
    "clean K=3 (fresh)": (3, 0.05, 0.60, 0.05),
    "small gaps K=3 (10% vs 30%)": (3, 0.10, 0.30, 0.05),
    "overlapping K=3": (3, 0.05, 0.60, 0.40),
    "overlap+small gaps K=3": (3, 0.10, 0.30, 0.40),
    "true K=6 clean": (6, 0.05, 0.60, 0.05),
    "true K=6 small gaps": (6, 0.10, 0.30, 0.05),
    "true K=6 overlap": (6, 0.05, 0.60, 0.40),
    "true K=6 overlap+small gaps": (6, 0.10, 0.30, 0.40),
}
N = 100
out = {}
for name, (t, lo, hi, spr) in scen.items():
    pick = collections.defaultdict(collections.Counter)
    g = collections.defaultdict(list)
    best = []
    for i in range(N):
        s = 5000 + i
        R = rates(s, t, lo, hi)
        b = bed(s, R, spr)
        f = fit_all(b.train.emb, [1] + Ks, s, n_init=3)
        lab = {k: assign(b.val.emb, m.centroids) for k, m in f.items()}
        c = select_k(lab, b.val.losses, C, L, seed=s, groups=b.val.sessions)
        ta = {}
        for k in [1] + Ks:
            cs, q = sweep(
                assign(b.test.emb, f[k].centroids),
                fail_rates(b.val.losses, lab[k], k),
                C,
                L,
                b.test.losses,
            )
            ta[k] = area(cs, q, C.min(), C.max())
        m = c.mean_area
        bk = max(Ks, key=lambda k: m[k])
        sd = float(c.areas[bk].std())
        ks = {
            "highest": bk,
            "one_spread": next(k for k in Ks if m[k] >= m[bk] - sd),
            "fixed3": 3,
            "fixed8": 8,
        }
        for r_, k in ks.items():
            pick[r_][k] += 1
            g[r_].append(ta[k])
        best.append(max(ta[k] for k in Ks))
    true_k = t
    out[name] = {
        r_: {
            "picks": dict(sorted(pick[r_].items())),
            "area": round(float(np.mean(g[r_])), 4),
            "regret": round(float(np.mean(np.array(best) - np.array(g[r_]))), 4),
        }
        for r_ in pick
    }
    print(name)
    [
        print("  ", r_, sorted(pick[r_].items()), "test area", round(np.mean(g[r_]), 4))
        for r_ in pick
    ]
    sys.stdout.flush()
with open(sys.argv[1], "w") as f:
    json.dump(out, f, indent=1)
