"""The Khayyam exam demo: its own router, gateway and data, never mixed with the chatbot router.

Khayyam Challenge (Persian school-exam questions, four options, true answers). Licence: academic
only, so question text stays in runs/khayyam/ (git-ignored); the router file holds numbers and
subject names only. Built from answers already paid for (stage `khayyam`); rebuilding costs $0.

    uv run python scripts/khayyam_build.py      # artifacts/router_khayyam + runs/khayyam/demo.parquet
"""

from __future__ import annotations

import glob
import json
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from metis.gateway.failover import ProviderError
from metis.gateway.providers import Reply

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261020
OUT = ROOT / "runs/khayyam"
ARTIFACT = ROOT / "artifacts/router_khayyam"
DEMO = OUT / "demo.parquet"
RESULTS = ROOT / "results/khayyam"
SYSTEM = "به این پرسش چهارگزینه‌ای پاسخ بده. فقط شماره گزینه درست (۱، ۲، ۳ یا ۴) را بنویس."
BASE_MODELS = ["gemini-2.5-flash-lite", "deepseek-v4-flash", "gpt-5.6-luna", "deepseek-v4-pro"]
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
SUBJECTS = {  # final_category_fa (majority in a cluster) -> English
    "شیمی": "Chemistry", "ریاضی": "Maths and logic", "تاریخ": "History", "ادبیات": "Persian literature",
    "فیزیک": "Physics", "زیست": "Biology and geology", "جغرافیا": "Geography", "عربی": "Arabic",
    "دین": "Religion", "زبان انگلیسی": "English", "اقتصاد": "Economics", "روانشناسی": "Psychology",
}


def parse(text: str | None) -> str | None:
    """The chosen option: the last one named ("گزینه ۲"), else the last digit 1-4."""
    text = (text or "").translate(DIGITS)
    named = re.findall(r"(?:گزینه|پاسخ|option)\D{0,12}([1-4])", text, re.IGNORECASE)
    if named:
        return named[-1]
    found = re.findall(r"[1-4]", text)
    return found[-1] if found else None


def load(root: Path = ROOT) -> pd.DataFrame:
    """Questions with options, key and subject, in the order every Khayyam run used."""
    files = glob.glob(str(root / "data/external/raw/raia-center__khayyam-challenge/**/*.parquet"), recursive=True)
    raw = pd.concat(pd.read_parquet(f) for f in files)
    ch = [c for c in raw.columns if re.fullmatch(r"(Choice|choice)\s*\d", c)]
    keep = raw["Key"].astype("Int64").astype(str).isin(list("1234")) & raw["Question Body"].notna()
    raw = raw[keep].reset_index(drop=True)
    return pd.DataFrame({
        "id": np.arange(len(raw)).astype(str), "q": raw["Question Body"].astype(str),
        "options": raw[ch].astype(str).agg(lambda r: "\n".join(f"{i + 1}) {t}" for i, t in enumerate(r)), axis=1),
        "choices": raw[ch].astype(str).values.tolist(), "key": raw["Key"].astype("Int64").astype(str),
        "course": raw["Course Title"].astype(str), "category": raw["final_category_fa"].astype(str),
    })


def split(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    idx = np.random.default_rng(SEED).permutation(n)
    return idx[:400], idx[400:1500], idx[1500:]  # val, test, unlabeled (clusters)


def messages(row) -> list[dict[str, str]]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{row.q}\n{row.options}"}]


def subject_name(categories: pd.Series, courses: pd.Series | None = None, taken: set[str] = frozenset()) -> dict[str, str]:
    """The main exam category of a cluster; when another cluster already has that name, its two
    most common subjects among the course titles instead (e.g. psychology and economics)."""
    top = categories.value_counts().index[0] if len(categories) else ""
    en = next((v for k, v in SUBJECTS.items() if k in top), top)
    fa = re.sub(r"\s*دوره.*$", "", top).strip() or top
    if en in taken and courses is not None:
        found: dict[str, int] = {}
        for title, n in courses.value_counts().items():
            for k, v in SUBJECTS.items():
                if k in title and v != en:
                    found[k] = found.get(k, 0) + int(n)
        two = sorted(found, key=found.get, reverse=True)[:2]
        if two:
            fa, en = "ترکیبی (" + "، ".join(two) + ")", "Mixed (" + ", ".join(SUBJECTS[k] for k in two) + ")"
    return {"en": en, "fa": fa}


# ----------------------------------------------------------------- serving
class KhayyamReplay:
    """Answers each demo question with the answer that model really gave (stored, $0)."""

    def __init__(self, demo: pd.DataFrame):
        self.rows = {(r.id, r.model): r for r in demo.itertuples()}

    def call(self, model: str, messages_: list[dict[str, Any]], context: dict[str, Any]) -> Reply:
        r = self.rows.get((context.get("prompt_id"), model))
        if r is None:
            raise ProviderError("no_stored_answer")
        return Reply(r.text or "", int(r.t_in), int(r.t_out), "length" if r.cut else "stop", float(r.ms or 0))


def build_gateway(embed=None, live: bool = False, provider=None):
    """A gateway with the Khayyam router only. Replay answers stored questions; live calls Metis;
    `provider` overrides both (tests, mock mode)."""
    from metis.config import load_config
    from metis.gateway.app import hash_embedder
    from metis.gateway.pipeline import Gateway
    from metis.gateway.providers import LiveProvider
    from metis.gateway.traces import TraceStore
    from metis.llm.client import load_models
    from metis.router.artifact import load_artifact

    artifact = load_artifact(ARTIFACT)
    demo = pd.read_parquet(DEMO) if DEMO.exists() else pd.DataFrame(columns=["id", "model", "text", "t_in", "t_out", "cut", "ms"])
    cfg = load_config("gateway") | {"cache": {"enabled": False}, "stickiness": {"enabled": False},
                                    "checks": {"enabled": True, "max_escalations": 2, "min_lang_chars": 10_000}}
    if provider is None:
        provider = LiveProvider("product") if live else KhayyamReplay(demo)
    return Gateway(artifact, provider, embed or hash_embedder(artifact.centroids.shape[1]), cfg, load_models(),
                   TraceStore(ROOT / "runs/gateway/khayyam_traces.sqlite"), None)


def summary_path() -> Path:
    return RESULTS / "khayyam_router.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def stamp() -> str:
    return time.strftime("%Y-%m-%d")
