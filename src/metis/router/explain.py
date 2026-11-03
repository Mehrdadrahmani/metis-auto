"""What lambda does to the shipped router: each cluster's pick, and where the picks change.

Used by the chat page's lambda slider (GET /v1/router). Same rule as `route`: the lowest
Psi + lambda * c_hat wins, ties to the cheaper model.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from metis.router.artifact import RouterArtifact
from metis.router.route import cluster_choices


def picks(artifact: RouterArtifact, lam: float) -> list[str]:
    choice = cluster_choices(artifact.psi, artifact.c_hat, np.array([lam]))[0]
    return [artifact.meta.models[i] for i in choice]


def breakpoints(artifact: RouterArtifact) -> list[float]:
    """The lambdas where some cluster changes model, ascending. Between two of them nothing changes."""
    psi, c = artifact.psi, artifact.c_hat
    found = set()
    for k in range(len(psi)):
        for a in range(len(c)):
            for b in range(len(c)):
                if c[a] > c[b]:  # a costs more: a wins below lam*, b above
                    lam = float((psi[k, b] - psi[k, a]) / (c[a] - c[b]))
                    if lam > 0:
                        found.add(lam)
    # Exact values: rounding first can step over the switch.
    out = {round(lam, 6) for lam in sorted(found) if picks(artifact, lam * (1 - 1e-6)) != picks(artifact, lam * (1 + 1e-6))}
    return sorted(out)


def describe(artifact: RouterArtifact, lam: float, default_lam: float) -> dict[str, Any]:
    m = artifact.meta
    chosen = picks(artifact, lam)
    return {
        "lambda": lam,
        "default_lambda": default_lam,
        "breakpoints": breakpoints(artifact),
        "models": [{"id": mid, "relative_cost": round(float(artifact.c_hat[i]), 5)} for i, mid in enumerate(m.models)],
        "clusters": [{
            "cluster": k, "name": m.cluster_names[k], "n_val": int(artifact.counts[k]),
            # 1 - Psi: the share of validation prompts each model passed in this cluster (judge, tau 7).
            "pass_rate": {mid: round(1 - float(artifact.psi[k, i]), 3) for i, mid in enumerate(m.models)},
            "pick": chosen[k],
        } for k in range(m.k_star)],
    }
