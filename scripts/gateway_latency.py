"""WP-16 step 5: gateway overhead with the real embedder, 1,000 synthetic Persian messages. No text from data."""

from __future__ import annotations

import random
import time
from pathlib import Path

import numpy as np

from metis.config import load_config
from metis.gateway.app import build_gateway, real_embedder
from metis.gateway.pipeline import ChatRequest
from metis.gateway.providers import MockProvider

WORDS = "سلام لطفا درباره سفر شیراز کتاب برنامه نویسی سفارش ارسال بازگشت پول حساب کاربری رمز عبور بیمه درمان دانشگاه ثبت نام آموزش زبان انگلیسی راهنمایی کن چطور می توانم".split()
rng = random.Random(20261020)
sizes = [rng.choice((3, 8, 20, 60, 150, 400)) for _ in range(1000)]
texts = [" ".join(rng.choices(WORDS, k=n)) + f" {i}" for i, n in enumerate(sizes)]
embed, _ = real_embedder()
embed("گرم کردن مدل")
cfg = load_config("gateway") | {"traces": {"path": "runs/gateway/latency.sqlite"}}
gw = build_gateway(cfg, embed=embed, provider=MockProvider())
rows = []
for t in texts:
    r = gw.handle(ChatRequest([{"role": "user", "content": t}])).trace
    rows.append(r)
stage = lambda s, q: np.percentile([r["stage_ms"].get(s, 0) for r in rows], q)  # noqa: E731
total = [sum(r["stage_ms"].values()) for r in rows]
lines = ["# Gateway latency", "", f"Measured on this Mac, MPS, nano embedder, n = {len(rows)} synthetic Persian messages, 3 to 400 words. Mock model call, so the model's own time is not included.", "",
         "| Stage | p50 ms | p95 ms | p99 ms |", "|---|---:|---:|---:|"]
for s in ("rules", "embed", "cache", "route"):
    lines.append(f"| {s} | {stage(s, 50):.2f} | {stage(s, 95):.2f} | {stage(s, 99):.2f} |")
lines.append(f"| total overhead | {np.percentile(total, 50):.1f} | {np.percentile(total, 95):.1f} | {np.percentile(total, 99):.1f} |")
lines += ["", f"Budget p95 ≤ 100 ms: {'met' if np.percentile(total, 95) <= 100 else 'not met'}."]
Path("results/gateway_latency.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
