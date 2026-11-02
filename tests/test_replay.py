import numpy as np
import pandas as pd

from metis.eval.report import metrics, session_ci
from metis.gateway.failover import ProviderError
from metis.gateway.providers import Reply
from metis.sim.replay import ReplayProvider


def test_session_ci_hand():
    mean, lo, hi = session_ci(np.array([1.0, 0.0, np.nan]), np.array([0, 1, 2]))
    assert mean == 0.5 and lo <= 0.5 <= hi


def test_metrics_formula():
    rows = pd.DataFrame({"passed": [1.0, 0.0], "cost": [0.002, 0.0], "latency": [100.0, 300.0], "cached": [False, True], "escalations": [0, 0],
                         "status": ["ok", "ok"], "tried": [1, 0], "reasons": [0, 0], "model": ["a", "a"]})
    m = metrics(rows, np.array([0, 1]))
    assert m["cost_1k"] == 1.0 and m["cache_rate"] == 0.5 and m["shares"] == {"a": 1.0}


def test_outage_and_missing():
    p = ReplayProvider({("x", "m"): Reply("t", 1, 1, "stop", 1)}, {"m": (2, 4)})
    assert p.call("m", [], {"prompt_id": "x"}).text == "t"
    p.tick = 3
    try:
        p.call("m", [], {"prompt_id": "x"})
        raise AssertionError
    except ProviderError as e:
        assert e.kind == "outage"
