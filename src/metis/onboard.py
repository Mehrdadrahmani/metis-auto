"""Add a model to the router (UniRoute: a new model needs only its fingerprint on validation).

From the developer page: register the model → one test call → estimate → the admin approves an
amount → answers on the same 798 validation prompts and the same pointwise judge (jev, tau 7)
→ its Psi row per cluster and its relative cost → activate: a new artifact with one more model.
Clusters, centroids and lambda stay as they are. The test set is never opened.

Spend goes to budget stage `add_model`, capped by what the admin approved and the global cap.
Answers and labels stay in runs/onboard/<model>/ (git-ignored); results are aggregates only.
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

import metis.config as _config
from metis.config import load_config
from metis.llm import stage as st
from metis.llm.budget import Budget, call_cost
from metis.llm.callcache import CallCache, get_or_call
from metis.llm.client import ADDED_MODELS, complete, is_mock, load_models
from metis.llm.messages import build_messages, gen_params
from metis.llm.runner import run_batch
from metis.router.artifact import RouterArtifact, load_artifact, save_artifact

ROOT = Path(__file__).resolve().parents[2]
STAGE = "add_model"
JUDGE = "jev"
JEV_USD_PER_CALL = 0.00026  # measured on val 800 (MASTER_LOG budget, judge_main)
LIVE_ARTIFACT = ROOT / "artifacts" / "router_live"
MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,48}$")
FIELDS = ("id", "provider", "api_path", "api_name", "price_in", "price_out", "context_window", "vision")


class OnboardError(ValueError):
    pass


# ------------------------------------------------------------------ registry
def added_path(config_dir: Path | None = None) -> Path:
    return (config_dir or _config.CONFIG_DIR) / f"{ADDED_MODELS}.yaml"


def register(spec: dict[str, Any], config_dir: Path | None = None) -> dict[str, Any]:
    """Add a model to configs/models_added.yaml (never one that exists already)."""
    mid = str(spec.get("id", "")).strip()
    if not MODEL_ID.match(mid):
        raise OnboardError("bad_id")
    if mid in load_models(config_dir):
        raise OnboardError("exists")
    try:
        entry = {
            "id": mid, "provider": str(spec.get("provider") or "openai"), "api_path": str(spec["api_path"]).strip(),
            "api_name": str(spec.get("api_name") or mid).strip(), "price_in": float(spec["price_in"]),
            "price_out": float(spec["price_out"]), "price_cached": float(spec.get("price_cached") or spec["price_in"]),
            "context_window": int(spec.get("context_window") or 128000), "vision": bool(spec.get("vision")),
            "is_anchor": False, "role": "added", "verified": False,
            "gen": {"rename": dict(spec.get("rename") or {}), "add": dict(spec.get("add") or {})},
            "added": time.strftime("%Y-%m-%d"),
        }
    except (KeyError, TypeError, ValueError):
        raise OnboardError("bad_fields") from None
    if not entry["api_path"].startswith("/") or entry["price_in"] < 0 or entry["price_out"] < 0:
        raise OnboardError("bad_fields")
    path = added_path(config_dir)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    data = data or {"models": []}
    data["models"].append(entry)
    path.write_text("# Models added from the developer page (metis.onboard). Same fields as models.yaml,\n"
                    "# plus `gen` (the gen_config rule for this model).\n"
                    + yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return entry


def unregister(model_id: str, config_dir: Path | None = None) -> None:
    path = added_path(config_dir)
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {"models": []}
    data["models"] = [m for m in data["models"] if m["id"] != model_id]
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def added_models(config_dir: Path | None = None) -> list[dict[str, Any]]:
    path = added_path(config_dir)
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("models") or [] if path.exists() else []


# ------------------------------------------------------------ validation set
class ValidationSet:
    """The 798 judged validation prompts, their cluster under the shipped centroids, and costs."""

    def __init__(self, base: RouterArtifact, root: Path = ROOT):
        self.base = base
        labels = pd.read_parquet(root / "runs/s7/labels_val.parquet")
        self.labels = labels
        self.ids = sorted(labels["prompt_id"].unique())
        self.prompts_path = root / "runs/s1/prompts.parquet"
        self._rows: dict[str, dict[str, Any]] | None = None
        self.cluster = self._clusters(root, base)
        # Tokens per model, as the artifact's c_hat was made (pilot + val answers).
        cols = ["prompt_id", "model_id", "tokens_in", "tokens_out"]
        tok = pd.concat(pd.read_parquet(root / f"runs/s6/responses_{s}.parquet", columns=cols) for s in ("pilot", "val"))
        tok = tok[tok["prompt_id"].isin(self.ids)].drop_duplicates(["prompt_id", "model_id"]).groupby("model_id")
        models = load_models()
        self.abs_cost = {m: call_cost(models[m], tok["tokens_in"].mean()[m], tok["tokens_out"].mean()[m]) for m in base.meta.models}
        self.norm = max(self.abs_cost.values())  # c_hat = cost / this; the anchor (Sonnet) is 1

    def _clusters(self, root: Path, base: RouterArtifact) -> np.ndarray:
        """Each prompt's nearest centroid. The vectors are read once (a few GB) and the result kept."""
        import hashlib

        key = hashlib.sha256(base.centroids.tobytes() + "\n".join(self.ids).encode()).hexdigest()[:16]
        saved = root / "runs/onboard" / f"val_clusters_{key}.npy"
        if saved.exists():
            return np.load(saved)
        ids, vecs = [], []
        for part in sorted((root / "runs/s4/full" / base.meta.embedder_id).glob("part-*.npz")):
            with np.load(part) as z:
                keep = np.isin(z["ids"], self.ids)
                ids.append(z["ids"][keep])
                vecs.append(z["vecs"][keep])
        all_ids = np.concatenate(ids)
        v = np.concatenate(vecs)[pd.Index(all_ids).get_indexer(self.ids)]
        out = ((v[:, None, :] - base.centroids[None]) ** 2).sum(-1).argmin(1)
        saved.parent.mkdir(parents=True, exist_ok=True)
        np.save(saved, out)
        return out

    @property
    def rows(self) -> dict[str, dict[str, Any]]:
        if self._rows is None:
            self._rows = st.load_rows(self.prompts_path, self.ids)
        return self._rows

    def mean_tokens_in(self) -> float:
        return float(np.mean([r["est_tokens_in"] for r in self.rows.values()]))

    def estimate(self, model_id: str) -> dict[str, float]:
        spec = load_models()[model_id]
        gen = call_cost(spec, self.mean_tokens_in(), st.T_OUT)
        n = len(self.ids)
        return {"prompts": n, "gen_per_call": gen, "judge_per_call": JEV_USD_PER_CALL,
                "total_usd": round(n * (gen + JEV_USD_PER_CALL) * 1.15, 4)}  # +15%: cut answers retried

    def fingerprint(self, losses: pd.Series) -> np.ndarray:
        """Psi row: the fail rate per cluster on the labeled prompts (losses indexed by prompt_id)."""
        idx = pd.Index(self.ids)
        loss = losses.reindex(idx).to_numpy(float)
        row = np.full(self.base.meta.k_star, np.nan)
        for k in range(self.base.meta.k_star):
            vals = loss[(self.cluster == k) & ~np.isnan(loss)]
            row[k] = vals.mean() if len(vals) else np.nan
        return row


# ------------------------------------------------------------------- jobs
class Job:
    """One evaluation run in a background thread. Status is kept in runs/onboard/<model>/status.json."""

    def __init__(self, model_id: str, approved_usd: float, vset: ValidationSet, out: Path, limit: int | None = None,
                 cache: CallCache | None = None):
        self.model_id, self.approved, self.vset, self.out, self.limit = model_id, approved_usd, vset, out, limit
        self.cache = cache or CallCache()
        self.status: dict[str, Any] = {"model": model_id, "state": "queued", "phase": "", "done": 0, "total": 0,
                                       "cost_usd": 0.0, "approved_usd": approved_usd, "started": time.time()}
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> Job:
        self.out.mkdir(parents=True, exist_ok=True)
        self.thread.start()
        return self

    def _save(self, **kw) -> None:
        self.status.update(kw)
        (self.out / "status.json").write_text(json.dumps(self.status, indent=1), encoding="utf-8")

    def _budget(self) -> Budget:
        cfg = load_config("budget")
        spent_before = self.cache.spent_usd(STAGE)
        cfg["approved_usd"] = {**cfg["approved_usd"], STAGE: spent_before + self.approved}
        return Budget(self.cache, cfg)

    def _run(self) -> None:
        try:
            self._evaluate()
        except Exception as exc:  # noqa: BLE001  the page shows the class only
            self._save(state="failed", error=type(exc).__name__)

    def _evaluate(self) -> None:
        from metis.judge import pointwise, render
        from metis.judge.common import JudgeRun

        budget, mid = self._budget(), self.model_id
        cfg = load_config("gen_config")
        retries = [load_config("gen_retry"), load_config("gen_retry_2")]
        ids = self.vset.ids[: self.limit] if self.limit else self.vset.ids
        rows = self.vset.rows
        est = self.vset.estimate(mid)
        limits = budget.config["anomalies"]
        answers: dict[str, dict[str, Any]] = {}
        self._save(state="running", phase="answers", done=0, total=len(ids))

        def gen_one(pid: str):
            r = rows[pid]
            messages = build_messages(r["instructions"], r["text"], r["history"], r["rag_context"])
            result = get_or_call(self.cache, budget, STAGE, mid, messages, gen_params(mid, cfg), cfg["_id"],
                                 est["gen_per_call"], complete, prompt_id=pid)
            for retry in retries:  # the same rising limits the four models had
                if not (result.status == "ok" and result.response and result.response.finish_reason == "length"):
                    break
                result = get_or_call(self.cache, budget, STAGE, mid, messages, gen_params(mid, cfg, retry["max_tokens"]),
                                     retry["_id"], est["gen_per_call"] * 3, complete, prompt_id=pid)
            resp = result.response
            ok = result.status == "ok" and bool(resp and resp.text.strip())
            answers[pid] = {"prompt_id": pid, "text": resp.text if ok else None, "tokens_in": resp.tokens_in if resp else 0,
                            "tokens_out": resp.tokens_out if resp else 0, "latency_ms": resp.latency_ms if resp else None,
                            "status": "ok" if ok else "failed"}
            self._save(done=len(answers), cost_usd=round(self.cache.spent_usd(STAGE) - self._spent0, 5))
            return result

        self._spent0 = self.cache.spent_usd(STAGE)
        report = run_batch(f"{STAGE}_gen_{mid}", ids, gen_one, limits, 4, est_cost_per_call=est["gen_per_call"])
        pd.DataFrame(list(answers.values())).to_parquet(self.out / "answers.parquet", index=False)
        if report.stopped:
            self._save(state="stopped", reason=report.stopped_reason)
            return

        jcfg = render.judge_config()
        run = JudgeRun(self.cache, budget, STAGE, JUDGE, jcfg, JEV_USD_PER_CALL)
        records: list[dict[str, Any]] = []
        self._save(phase="judging", done=0)

        def judge_one(pid: str):
            result, record = pointwise.judge(run, rows[pid], mid, answers[pid]["text"])
            records.append(record)
            self._save(done=len(records), cost_usd=round(self.cache.spent_usd(STAGE) - self._spent0, 5))
            return result

        report = run_batch(f"{STAGE}_judge_{mid}", ids, judge_one, limits, 4, est_cost_per_call=JEV_USD_PER_CALL)
        judged = pd.DataFrame(records)
        judged.to_parquet(self.out / "judged.parquet", index=False)
        if report.stopped:
            self._save(state="stopped", reason=report.stopped_reason)
            return
        self._save(phase="results")
        (self.out / "result.json").write_text(json.dumps(summarize(self.vset, mid, judged, answers), indent=1), encoding="utf-8")
        self._save(state="done", phase="", finished=time.time())


def summarize(vset: ValidationSet, model_id: str, judged: pd.DataFrame, answers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aggregates only: pass rates, fingerprint, relative cost. No prompt or answer text."""
    tau = vset.base.meta.tau
    kept = judged[judged["status"].isin(["ok", "failed_generation"])].copy()
    kept["loss"] = (kept["score"] < tau).astype(int)
    losses = kept.set_index("prompt_id")["loss"]
    psi_row = vset.fingerprint(losses)
    spec = load_models()[model_id]
    a = pd.DataFrame(list(answers.values()))
    ok = a[a["status"] == "ok"]
    abs_cost = call_cost(spec, ok["tokens_in"].mean(), ok["tokens_out"].mean()) if len(ok) else float("nan")
    base = vset.base
    others = {m: 1 - vset.labels[vset.labels["model_id"] == m]["loss"].mean() for m in base.meta.models}
    return {
        "model": model_id, "n_judged": len(kept), "n_prompts": len(vset.ids),
        "failed_answers": int((a["status"] != "ok").sum()), "dropped_judgments": int((judged["status"] == "dropped").sum()),
        "pass_rate": float(1 - kept["loss"].mean()) if len(kept) else None,
        "others_pass_rate": {m: round(float(v), 4) for m, v in others.items()},
        "psi": [None if np.isnan(x) else round(float(x), 4) for x in psi_row],
        "c_hat": float(abs_cost / vset.norm), "usd_per_call": float(abs_cost),
        "latency_p50_ms": float(ok["latency_ms"].median()) if len(ok) else None,
        "complete": bool(len(kept) == len(vset.ids)),
    }


# --------------------------------------------------------------- activate
def build_artifact(base: RouterArtifact, results: list[dict[str, Any]]) -> RouterArtifact:
    """The shipped artifact plus one column per added model. Clusters and lambda unchanged.

    A cluster where the new model has no label gets its overall fail rate. c_hat keeps the base
    normalisation (Sonnet = 1), so lambda keeps its meaning; a model dearer than Sonnet is > 1.
    """
    models, psi, c_hat, prices = list(base.meta.models), base.psi.copy(), base.c_hat.copy(), dict(base.meta.prices)
    specs = load_models()
    for r in results:
        if r["model"] in models:
            continue
        row = np.array([np.nan if x is None else x for x in r["psi"]], dtype=float)
        row[np.isnan(row)] = 1 - (r["pass_rate"] or 0)
        models.append(r["model"])
        psi = np.column_stack([psi, row])
        c_hat = np.append(c_hat, r["c_hat"])
        s = specs[r["model"]]
        prices[r["model"]] = {"in": s["price_in"], "out": s["price_out"]}
    meta = replace(base.meta, models=tuple(models), prices=prices, build_date=time.strftime("%Y-%m-%d"))
    return RouterArtifact(meta=meta, centroids=base.centroids, psi=psi, counts=base.counts, c_hat=c_hat)


def activate(base: RouterArtifact, results: list[dict[str, Any]], folder: Path = LIVE_ARTIFACT) -> RouterArtifact:
    """Write the live artifact (replacing the previous live one, never the shipped one)."""
    import shutil

    art = build_artifact(base, results)
    if folder.exists():
        shutil.rmtree(folder)
    save_artifact(art, folder)
    return load_artifact(folder)


def test_call(model_id: str, cache: CallCache | None = None) -> dict[str, Any]:
    """One short real call, so a wrong path or name fails before any money is approved."""
    cache = cache or CallCache()
    cfg = load_config("budget")
    cfg["approved_usd"] = {**cfg["approved_usd"], STAGE: cache.spent_usd(STAGE) + 0.01}
    budget = Budget(cache, cfg)
    gen = load_config("gen_config")
    messages = [{"role": "user", "content": "Reply with the single word: ok"}]
    params = {**gen_params(model_id, gen), "max_tokens": 16}
    if "max_completion_tokens" in params:
        params["max_completion_tokens"] = 16
        params.pop("max_tokens", None)
    t0 = time.perf_counter()
    result = get_or_call(cache, budget, STAGE, model_id, messages, params, f"test-{time.time()}", 0.001, complete)
    ok = result.status == "ok" and result.response is not None
    return {"ok": ok, "latency_ms": round((time.perf_counter() - t0) * 1000), "mock": is_mock(),
            "error": None if ok else (result.error_kind or "failed"),
            "tokens_out": result.response.tokens_out if ok else 0}
