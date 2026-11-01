"""Metis AI capability check (WP-04 step 9). Model-list GETs only; no generation, no spend.

Needs the owner's OK before running. Reads METIS_BASE_URL and METIS_API_KEY from `.env` and
never prints them. Writes `results/metis_capabilities.md` (ids and counts only).
Prices come from the public pricing address that Metis AI's pricing page uses (no key sent).
Rate limits and token reporting are not available from these requests.

    uv run python scripts/metis_check.py
"""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "metis_capabilities.md"
PRICING_URL = "https://api.metisai.ir/api/v1/meta/providers/pricing"
PRICED = [
    "deepseek-v4-flash",
    "gpt-5.6-luna",
    "gemini-2.5-flash-lite",
    "claude-sonnet-5-5",
    "jev-latest",
]
BEARER = {"Authorization": "Bearer {key}"}
ROUTES = [
    ("openai", "/openai/v1/models", BEARER),
    ("deepseek", "/deepseek/v1/models", BEARER),
    ("anthropic", "/api/v1/wrapper/anthropic/models", BEARER),
    ("google", "/api/v1/wrapper/google/models", BEARER),  # undocumented, OpenAI-style
]
# Name fragments used to spot each candidate; the judge is any GPT-5.x model.
WANTED = {
    "deepseek-v4-flash": ("deepseek", "v4", "flash"),
    "gpt-5.6-luna": ("gpt-5.6", "luna"),
    "gemini-2.5-flash-lite": ("gemini-2.5", "flash-lite"),
    "claude-sonnet-5-5": ("claude", "sonnet", "5"),
    "judge (GPT-5.x)": ("gpt-5",),
}


def matches(ids: list[str]) -> dict[str, list[str]]:
    lowered = [(i, i.lower().replace("_", "-")) for i in ids]
    return {
        name: [i for i, low in lowered if all(part in low for part in parts)]
        for name, parts in WANTED.items()
    }


def list_ids(base_url: str, key: str) -> tuple[list[str], dict[str, int]]:
    """Ask each provider route for its models. Returns ids and HTTP status per route."""
    ids: list[str] = []
    status: dict[str, int] = {}
    for route, path, headers in ROUTES:
        hdr = {k: v.format(key=key) for k, v in headers.items()}
        try:
            reply = httpx.get(base_url + path, headers=hdr, timeout=15.0)
        except httpx.HTTPError as exc:
            status[route] = 0
            print(f"{route}: {type(exc).__name__}")
            continue
        status[route] = reply.status_code
        print(f"{route}: HTTP {reply.status_code}")
        if reply.status_code == 200:
            body = reply.json()
            rows = body.get("data") or body.get("models") or []
            ids += [str(m.get("id") or m.get("name")) for m in rows]
    return sorted(set(ids)), status


def report(base_url: str, ids: list[str], status: dict[str, int]) -> str:
    found = matches(ids)
    lines = [
        "# Metis AI capabilities",
        "",
        f"Checked {date.today().isoformat()} with model-list requests (no generation).",
        f"Base URL: `{base_url}`. Model ids listed: {len(ids)}. HTTP by route: {status}.",
        "",
        "| Wanted | Matching ids |",
        "|---|---|",
    ]
    lines += [f"| {k} | {', '.join(v) or '**missing**'} |" for k, v in found.items()]
    lines += ["", "## Prices (USD per 1M tokens, Metis AI)", ""]
    lines += ["| Model | Input | Output | Cached input |", "|---|---:|---:|---:|"]
    rows = {r["model"]: r for r in httpx.get(PRICING_URL, timeout=30.0).json()["llm"]}
    for name in PRICED:
        row = rows.get(name)
        if row is None:
            lines.append(f"| {name} | **missing** | | |")
            continue
        rules = row.get("pricingRules", {}).get("params", {})
        cached = (rules.get("tiers") or [rules])[0].get("cached_input_token")
        cached_text = f"{cached * 1e6:.4g}" if cached else "not listed"
        lines.append(
            f"| {name} | {row['inputTokenUnitIncome'] * 1e6:.4g} "
            f"| {row['outputTokenUnitIncome'] * 1e6:.4g} | {cached_text} |"
        )
    lines += [
        "",
        "DeepSeek costs double in peak hours (Mon-Fri 01:00-04:00, 06:00-10:00 UTC).",
        "Not known yet: rate limits, and whether usage and cached tokens are returned for each",
        "route (needs a first paid call).",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    load_dotenv(ROOT / ".env")
    base_url = os.environ.get("METIS_BASE_URL", "").rstrip("/")
    key = os.environ.get("METIS_API_KEY", "")
    if not base_url or not key:
        print("METIS_BASE_URL or METIS_API_KEY is missing from .env")
        return 2
    ids, status = list_ids(base_url, key)
    if not ids:
        return 1
    OUT.write_text(report(base_url, ids, status), encoding="utf-8")
    missing = [k for k, v in matches(ids).items() if not v]
    print(f"{len(ids)} model ids; missing: {missing or 'none'}; wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
