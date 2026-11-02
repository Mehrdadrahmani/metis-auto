"""WP-19 step 7: real end-to-end latency through the gateway, 50 validation messages per setup. Stage live."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from metis.config import load_config
from metis.gateway.app import build_gateway, real_embedder
from metis.gateway.pipeline import ChatRequest
from metis.gateway.providers import LiveProvider
from metis.llm import stage as st
from metis.llm.messages import build_messages

load_dotenv()
split = pd.read_parquet("runs/s2/split.parquet", columns=["prompt_id", "split"])
ids = sorted(split[split["split"] == "val"].prompt_id.sample(50, random_state=20261020))
rows = st.load_rows(Path("runs/s1/prompts.parquet"), ids)
cfg = load_config("gateway") | {"provider": "live", "traces": {"path": "runs/gateway/live.sqlite"}}
cfg["cache"] = {**cfg["cache"], "enabled": False}
embed, _ = real_embedder()
provider = LiveProvider()
gw = build_gateway(cfg, embed=embed, provider=provider)
lines = ["# Live latency", "", "Measured through the real gateway and Metis AI, one at a time, 50 validation messages per row. Includes gateway overhead.", "",
         "| Setup | n ok | p50 s | p90 s | $ per 1k |", "|---|---:|---:|---:|---:|"]
data = {}
SETUPS = sys.argv[1:] or ["gemini-2.5-flash-lite", "deepseek-v4-flash", "gpt-5.6-luna", "takrouter", "claude-sonnet-5-5"]  # one process per router row: each run makes fresh calls
for setup in SETUPS:
    lat, cost = [], []
    for pid in ids:
        r0 = rows[pid]
        messages = build_messages(r0["instructions"], r0["text"], r0["history"], r0["rag_context"])
        r = gw.handle(ChatRequest(messages, model=setup, chatbot="live", prompt_id=pid))
        if r.trace["status"] == "ok":
            lat.append(r.trace["latency_ms"] / 1000)
            cost.append(r.trace["cost_usd"])
    data[setup] = {"n": len(lat), "p50": float(np.percentile(lat, 50)), "p90": float(np.percentile(lat, 90)), "usd_1k": float(np.mean(cost) * 1000)}
    lines.append(f"| {setup} | {len(lat)} | {data[setup]['p50']:.2f} | {data[setup]['p90']:.2f} | {data[setup]['usd_1k']:.3f} |")
    print(lines[-1], "spent", round(provider.cache.spent_usd("live"), 3), flush=True)
Path("results/final").mkdir(exist_ok=True)
old = Path("results/final/live_latency.json")
merged = (json.loads(old.read_text()) if old.exists() else {}) | data
old.write_text(json.dumps(merged, indent=1), encoding="utf-8")
