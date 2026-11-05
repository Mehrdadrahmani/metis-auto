"""Preview: ask the team router (Farzaneh's LangGraph service, `POST /route`) which model to use.

The team service only decides; TakRouter's gateway makes the answer call (one cache, budget guard,
redaction, failover, credit and trace). Service URL: TEAM_ROUTER_URL (default http://127.0.0.1:8100).
"""

from __future__ import annotations

import os
from typing import Any

import httpx


def team_route(text: str, timeout: float = 5.0) -> dict[str, Any]:
    url = os.environ.get("TEAM_ROUTER_URL", "http://127.0.0.1:8100").rstrip("/") + "/route"
    r = httpx.post(url, json={"message": text}, timeout=timeout)
    r.raise_for_status()
    return r.json()
