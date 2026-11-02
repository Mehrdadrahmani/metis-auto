"""WP-07: the whole offline pipeline S1 to S12 as one command, on the sample with a mock LLM ($0).

Usage: uv run python scripts/pipeline.py --config configs/pipeline.yaml --sizes sample --mock
       uv run python scripts/pipeline.py ... --stages s8 s9      (only these, inputs must exist)
       uv run python scripts/pipeline.py ... --check             (fresh run, second run, leak test,
                                                                  results/dry_run_report.md)

Everything lives in runs/dry/ with its own cache, so real runs/ and the paid cache are never read or
written. The numbers mean nothing: only the plumbing is tested. The test set here is the sample's
own scaled draw, not the sealed real one. Refuses to run without --mock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DRY = ROOT / "runs/dry"
SAMPLE = ROOT / "data/raw/sample.json"
STAGES = ("s1", "s2", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "s12")
KS = (1, 3, 4)  # WP-07 step 4; candidate_ks is empty for 60 prompts, and K = 1 is a comparison only
TAU = 7  # mock pass score; the real one comes from the calibration set in WP-11
BUDGET = 0.5  # mock lambda target on the normalized cost
METHODS = ("pt", "pw")
ENV = {**os.environ, "METIS_MOCK": "1", "METIS_MOCK_CACHE": str(DRY / "cache/llm_calls.sqlite"),
       "METIS_RUNS_DIR": str(DRY)}  # fmt: skip


def sh(*args: object, env: dict | None = None) -> None:
    subprocess.run([sys.executable, *map(str, args)], check=True, cwd=ROOT, env=env or ENV,
                   stdout=subprocess.DEVNULL)  # fmt: skip


def seed_of(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256(repr(parts).encode()).digest()[:8], "big")


def load(cfg: dict, name: str) -> np.ndarray:
    with np.load(DRY / "s4" / f"{name}.npz") as z:
        return z["vecs"]


def ids_of(name: str) -> list[str]:
    return json.loads((DRY / "s4" / f"{name}_ids.json").read_text("utf-8"))


def stage_s1(cfg: dict) -> dict:
    sh("scripts/s1_ingest.py", SAMPLE, DRY / "s1")
    df = pd.read_parquet(DRY / "s1/prompts.parquet", columns=["eligible_labeled", "eligible_train"])
    return {"prompts": len(df), "labeled": int(df.eligible_labeled.sum()), "train": int(df.eligible_train.sum())}


def stage_s2(cfg: dict) -> dict:
    sh("scripts/s2_split.py", DRY / "s1/prompts.parquet", DRY / "s2", DRY / "s2/copy.manifest.json",
       "--sizes", "sample_dry_run")  # fmt: skip
    t = pd.read_parquet(DRY / "s2/split.parquet")
    test = json.loads((DRY / "s2/test_ids.sealed").read_text("utf-8"))
    # S6 and S7 have no way to select test (WP-12 adds it), so a dry-only split calls it val.
    frame = pd.DataFrame({"prompt_id": test, "split": "val", "in_pilot": False})
    frame.to_parquet(DRY / "s2/dry_test_as_val.parquet", index=False)
    return {**t["split"].value_counts().to_dict(), "pilot": int(t["in_pilot"].sum()), "test": len(test)}


def stage_s4(cfg: dict) -> dict:
    from s4_embed_full import embedder

    df = pd.read_parquet(DRY / "s1/prompts.parquet", columns=["prompt_id", "embed_input"])
    t = pd.read_parquet(DRY / "s2/split.parquet", columns=["prompt_id", "split"])
    sets = {n: t.loc[t["split"] == n, "prompt_id"].sort_values().tolist() for n in ("train", "val")}
    sets["test"] = sorted(json.loads((DRY / "s2/test_ids.sealed").read_text("utf-8")))
    text = df.set_index("prompt_id")["embed_input"]
    emb = embedder(cfg, "cpu")  # CPU: the same bits on every run
    for name, ids in sets.items():
        np.savez(DRY / "s4" / f"{name}.npz", vecs=emb.encode(text.loc[ids].tolist()))
        (DRY / "s4" / f"{name}_ids.json").write_text(json.dumps(ids), "utf-8")
    (DRY / "s4/embedder_id.txt").write_text(emb.embedder_id, "utf-8")
    return {n: len(v) for n, v in sets.items()}


def stage_s5(cfg: dict) -> dict:
    from metis.router.kmeans import assign, cluster_counts, fit_kmeans

    x = load(cfg, "train")
    out = {}
    for k in KS:
        m = fit_kmeans(x, k, cfg["seed"], cfg["router"]["kmeans_n_init"])
        labels = {n: assign(load(cfg, n), m.centroids) for n in ("train", "val", "test")}
        np.savez(DRY / "s5" / f"k_{k}.npz", centroids=m.centroids, **labels)
        out[f"k{k}_val_counts"] = cluster_counts(labels["val"], k).tolist()
    return out


def stage_s6(cfg: dict) -> dict:
    split, p = DRY / "s2/split.parquet", DRY / "s1/prompts.parquet"
    gen = ("scripts/s6_generate.py", "--prompts", p)
    sh(*gen, "--split", split, "--out", DRY / "s6", "--set", "pilot", "--stage", "pilot")
    sh(*gen, "--split", split, "--out", DRY / "s6", "--set", "val", "--stage", "gen_main")
    sh(*gen, "--split", DRY / "s2/dry_test_as_val.parquet", "--out", DRY / "s6/test",
       "--set", "val", "--stage", "gen_main")  # fmt: skip
    return new_calls(DRY / "s6")


def stage_s7(cfg: dict) -> dict:
    p = DRY / "s1/prompts.parquet"
    sh("scripts/s7_judge.py", "--prompts", p, "--s6", DRY / "s6", "--out", DRY / "s7", "--set", "pilot",
       "--stage", "pilot", "--judge", "judge", "--method", "pointwise")  # fmt: skip (D-093)
    sh("scripts/s7_judge.py", "--prompts", p, "--s6", DRY / "s6", "--out", DRY / "s7", "--set", "pilot",
       "--stage", "pilot", "--judge", "jev")  # fmt: skip
    sh("scripts/s7_judge.py", "--prompts", p, "--s6", DRY / "s6", "--out", DRY / "s7", "--set", "val",
       "--stage", "judge_main", "--judge", "judge")  # fmt: skip
    sh("scripts/s7_judge.py", "--prompts", p, "--s6", DRY / "s6/test", "--out", DRY / "s7/test",
       "--set", "val", "--stage", "judge_main", "--judge", "judge")  # fmt: skip
    return mock_judge(cfg) | new_calls(DRY / "s7")


def new_calls(folder: Path) -> dict:
    total, records = 0, 0
    for path in folder.rglob("manifest_*.json"):
        m = json.loads(path.read_text("utf-8"))
        rows = [m] + list(m.get("summary", {}).values())
        total += sum(r.get("new_calls", 0) for r in rows)
        records += sum(r.get("records", 0) for r in rows)
    return {"new_calls": total, "records": records}


def mock_judge(cfg: dict) -> dict:
    """WP-07 step 3: the mock client's random grades carry no structure, so replace them with draws
    from a seeded latent quality per (K = 4 cluster, model). Parsing was exercised by S7 itself.
    K = 4, because the sample leaves only 20 train sessions and K = 3 puts all of val in one cluster."""
    from metis.judge import pairwise
    from metis.llm.client import load_models
    from metis.llm.stage import cheapest_first

    all_models = load_models()
    with np.load(DRY / "s5/k_4.npz") as z:
        cluster = {"val": z["val"], "test": z["test"]}
    n = 0
    for name, folder in (("val", DRY / "s7"), ("test", DRY / "s7/test")):
        where = dict(zip(ids_of(name), cluster[name].tolist(), strict=True))
        point = pd.read_parquet(folder / "pointwise_judge_val.parquet")
        pair = pd.read_parquet(folder / "pairwise_judge_val.parquet")
        if not (point["status"].eq("ok").all() and pair["status"].eq("ok").all()):
            raise RuntimeError(f"mock judge left failed rows in {name}")
        models = cheapest_first(all_models, sorted(point["model_id"].unique()))
        mean = {}
        for c in range(4):
            rng = np.random.default_rng(seed_of("latent", cfg["seed"], c))
            draw = rng.uniform(4, 8, len(models)) + np.linspace(0, 1.5, len(models))
            mean |= {(c, m): float(v) for m, v in zip(models, draw, strict=True)}

        def quality(pid: str, model: str, mean=mean, where=where) -> float:
            rng = np.random.default_rng(seed_of("answer", cfg["seed"], pid, model))
            return float(mean[where[pid], model] + rng.normal(0, 1.5))

        point["score"] = [int(np.clip(round(quality(p, m)), 1, 10))
                          for p, m in zip(point.prompt_id, point.model_id, strict=True)]  # fmt: skip
        anchor = pair_anchor()

        def verdict(pid: str, model: str, order: str, anchor=anchor, quality=quality) -> str:
            rng = np.random.default_rng(seed_of("pair", cfg["seed"], pid, model, order))
            gap = quality(pid, model) - quality(pid, anchor) + rng.normal(0, 0.5)
            return "tie" if abs(gap) < 0.5 else ("h" if gap > 0 else "anchor")

        pair["verdict"] = [verdict(p, m, o) for p, m, o in
                           zip(pair.prompt_id, pair.model_id, pair.order, strict=True)]  # fmt: skip
        point.to_parquet(folder / "mock_scores.parquet", index=False)
        outcomes = pairwise.outcomes(pair.to_dict("records"))
        rows = [(p, m, o) for (p, m), o in sorted(outcomes.items())]
        pd.DataFrame(rows, columns=["prompt_id", "model_id", "o"]).to_parquet(
            folder / "mock_outcomes.parquet", index=False
        )
        n += len(point)
    return {"mock_scores": n}


def pair_anchor() -> str:
    from metis.judge.render import judge_config

    return judge_config()["anchor"]


def tables(name: str) -> dict:
    """Loss matrices (n, N) for one set, in the order of ids_of(name); a pool in cheapest-first order."""
    from metis.llm.client import load_models
    from metis.llm.stage import cheapest_first

    folder = DRY / "s7" if name == "val" else DRY / "s7/test"
    ids = ids_of(name)
    point = pd.read_parquet(folder / "mock_scores.parquet")
    models = cheapest_first(load_models(), sorted(point["model_id"].unique()))
    scores = point.pivot(index="prompt_id", columns="model_id", values="score").loc[ids, models]
    out = pd.read_parquet(folder / "mock_outcomes.parquet")
    wins = out.pivot(index="prompt_id", columns="model_id", values="o").reindex(index=ids)
    anchor = models.index(pair_anchor())
    pw = np.full((len(ids), len(models)), 0.5)
    for j, m in enumerate(models):
        if j != anchor:
            pw[:, j] = 1 - wins[m].to_numpy()
    return {"models": models, "anchor": anchor, "pt": (scores.to_numpy() < TAU).astype(float), "pw": pw}


def groups(name: str) -> np.ndarray:
    df = pd.read_parquet(DRY / "s1/prompts.parquet", columns=["prompt_id", "session_id"])
    return df.set_index("prompt_id")["session_id"].loc[ids_of(name)].to_numpy()


def cost_hat(models: list[str]) -> np.ndarray:
    """S3: mean real token counts on val times price, normalized (spec S3)."""
    from metis.llm.budget import call_cost
    from metis.llm.client import load_models
    from metis.router.route import normalize_costs

    known = load_models()
    r = pd.read_parquet(DRY / "s6/responses_val.parquet").groupby("model_id")
    t_in, t_out = r["tokens_in"].mean(), r["tokens_out"].mean()
    return normalize_costs([call_cost(known[m], t_in[m], t_out[m]) for m in models])


def labels_for(k: int, name: str) -> np.ndarray:
    with np.load(DRY / f"s5/k_{k}.npz") as z:
        return z[name]


def stage_s8(cfg: dict) -> dict:
    """Every K, both methods, with the spec's checks on the pairwise fit."""
    from metis.router.bt import closed_form_psi, fit_bt
    from metis.router.select_k import fit_psi

    t = tables("val")
    out = {}
    for k in KS:
        labels = labels_for(k, "val")
        for method in METHODS:
            psi = fit_psi(t[method], labels, k, method, anchor=t["anchor"])
            np.save(DRY / "s8" / f"psi_{method}_k{k}.npy", psi)
        o = 1 - t["pw"]
        gap = np.abs(fit_bt(o, labels, k, t["anchor"]).psi - closed_form_psi(o, labels, k, t["anchor"]))
        out[f"bt_vs_closed_form_k{k}"] = float(gap.max())
    return out


def lambda_grid(cfg: dict) -> np.ndarray:
    from metis.router.select_lambda import lambda_grid as grid

    r = cfg["router"]
    return grid(r["lambda_n"], r["lambda_low"], r["lambda_high"])


def stage_s9(cfg: dict) -> dict:
    from metis.router.select_k import select_k

    t = tables("val")
    c_hat = cost_hat(t["models"])
    labels = {k: labels_for(k, "val") for k in KS}
    comparison = [k for k in KS if k == 1 or k > cfg["router"]["k_ship_max"]]
    out = {}
    for method in METHODS:
        s = select_k(labels, t[method], c_hat, lambda_grid(cfg), cfg["seed"],
                     cfg["router"]["select_k_repeats"], groups("val"), None, comparison, method,
                     anchor=t["anchor"] if method == "pw" else None)  # fmt: skip
        out[method] = {"k_star": s.k_star, "mean_area": {str(k): v for k, v in s.mean_area.items()},
                       "empty_events": s.empty_events}  # fmt: skip
    (DRY / "s9/choice.json").write_text(json.dumps(out, indent=1, sort_keys=True), "utf-8")
    return {m: out[m]["k_star"] for m in METHODS}


def choice() -> dict:
    return json.loads((DRY / "s9/choice.json").read_text("utf-8"))


def stage_s10(cfg: dict) -> dict:
    from metis.eval.metrics import sweep
    from metis.router.select_lambda import select_lambda

    t = tables("val")
    c_hat, lams = cost_hat(t["models"]), lambda_grid(cfg)
    out = {}
    for method in METHODS:
        k = choice()[method]["k_star"]
        psi = np.load(DRY / "s8" / f"psi_{method}_k{k}.npy")
        costs, qualities = sweep(labels_for(k, "val"), psi, c_hat, lams, t[method])
        c = select_lambda(lams, costs, qualities, "budget", BUDGET)
        out[method] = {"lam": c.lam, "cost": c.cost, "quality": c.quality, "mode": c.mode,
                       "target": c.target, "feasible": c.feasible}  # fmt: skip
    (DRY / "s10/lambda.json").write_text(json.dumps(out, indent=1, sort_keys=True), "utf-8")
    return {m: out[m]["lam"] for m in METHODS}


class MemoryStore:
    """Exact cosine search with Qdrant's `search` shape, so the K-NN baseline runs without a server."""

    def __init__(self, ids: list[str], vecs: np.ndarray):
        self.ids, self.vecs = ids, vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

    def search(self, q: np.ndarray, k: int, filter: dict | None = None, exact: bool = True) -> list:
        sims = self.vecs @ (q / np.linalg.norm(q))
        return [(self.ids[i], float(sims[i])) for i in np.argsort(-sims, kind="stable")[:k]]


def stage_s11(cfg: dict) -> dict:
    from metis.eval import baselines as b
    from metis.eval.metrics import area
    from metis.eval.stats import bootstrap

    val, test = tables("val"), tables("test")
    if val["models"] != test["models"]:
        raise RuntimeError("val and test have different model orders")
    c_hat, lams, seed = cost_hat(val["models"]), lambda_grid(cfg), cfg["seed"]
    c_min, c_max = float(c_hat.min()), float(c_hat.max())
    x_val, x_test = load(cfg, "val"), load(cfg, "test")
    g_val, g_test = groups("val"), groups("test")
    store = MemoryStore(ids_of("val"), x_val)
    order = b.neighbor_order(store, ids_of("val"), x_val)
    report: dict = {"n_val": len(x_val), "n_test": len(x_test), "models": val["models"],
                    "c_hat": c_hat.tolist()}  # fmt: skip
    for method in METHODS:
        k = choice()[method]["k_star"]
        v, y = val[method], test[method]
        with np.load(DRY / f"s5/k_{k}.npz") as z:
            centroids = z["centroids"]
        psi = np.load(DRY / "s8" / f"psi_{method}_k{k}.npy")
        knn_k, _ = b.tune_knn_k(order, v, c_hat, lams, seed, groups=g_val)
        routers = {
            "uniroute": b.UniRoute(centroids, psi, c_hat),
            "zerorouter": b.ZeroRouter(v, c_hat),
            "knn": b.KNNRouter(store, ids_of("val"), v, c_hat, knn_k),
            "always_cheapest": b.always_cheapest(v, c_hat),
            "always_best": b.always_best(v, c_hat),
        }
        if method == "pt":
            routers["logistic"] = b.LogisticRouter(x_val, v, c_hat, seed, g_val)
        curves = {n: r.curve(x_test, lams, y) for n, r in routers.items()}
        areas = {n: area(c, q, c_min, c_max) for n, (c, q) in curves.items()}

        def diff(idx: np.ndarray, y=y, r=routers) -> float:
            one = [area(*r[n].curve(x_test[idx], lams, y[idx]), c_min, c_max)
                   for n in ("uniroute", "zerorouter")]  # fmt: skip
            return one[0] - one[1]

        boot = bootstrap(diff, g_test, n_boot=200, seed=seed)
        report[method] = {
            "k_star": k, "knn_k": knn_k, "areas": areas,
            "uniroute_minus_zero": {"estimate": boot.estimate, "low": boot.low, "high": boot.high,
                                    "n_boot": boot.n_boot},
            "curve": {"cost": curves["uniroute"][0][::12].tolist(),
                      "quality": curves["uniroute"][1][::12].tolist()},
            "psi": psi.tolist(),
            "counts": np.bincount(labels_for(k, "val"), minlength=k).tolist(),
        }  # fmt: skip
    (DRY / "s11/metrics.json").write_text(json.dumps(report, indent=1, sort_keys=True), "utf-8")
    return {m: report[m]["areas"]["uniroute"] for m in METHODS}


def stage_s12(cfg: dict) -> dict:
    from metis.data.split import ids_sha256
    from metis.judge.render import judge_config
    from metis.llm.client import load_models
    from metis.router.artifact import Meta, RouterArtifact, load_artifact, save_artifact
    from metis.router.route import route

    t = tables("val")
    c_hat, known = cost_hat(t["models"]), load_models()
    picks = json.loads((DRY / "s10/lambda.json").read_text("utf-8"))
    gen_id = pd.read_parquet(DRY / "s6/responses_val.parquet", columns=["gen_config_id"]).iloc[0, 0]
    out = {}
    for method, name in (("pt", "point"), ("pw", "pair")):
        k = choice()[method]["k_star"]
        with np.load(DRY / f"s5/k_{k}.npz") as z:
            centroids = z["centroids"]
        psi = np.load(DRY / "s8" / f"psi_{method}_k{k}.npy")
        prices = {m: {"in": known[m]["price_in"], "out": known[m]["price_out"]} for m in t["models"]}
        meta = Meta(
            method=name, embedder_id=(DRY / "s4/embedder_id.txt").read_text("utf-8"), k_star=k,
            cluster_names=tuple(f"mock {c}" for c in range(k)), models=tuple(t["models"]), prices=prices,
            lam=picks[method]["lam"], lambda_mode="budget", lambda_target=BUDGET, router_type="uniroute",
            hashes={"val_set": ids_sha256(ids_of("val")), "gen_config": str(gen_id),
                    "judge_config": judge_config()["judge_config_id"]},
            build_date="dry-run", tau=TAU if method == "pt" else None,
            anchor=t["models"][t["anchor"]] if method == "pw" else None,
        )  # fmt: skip
        counts = np.bincount(labels_for(k, "val"), minlength=k)
        folder = DRY / "s12" / f"artifact_{name}"
        save_artifact(RouterArtifact(meta, centroids, psi, counts, c_hat), folder)
        back = load_artifact(folder)
        d = route(load(cfg, "test")[0], t["models"], back.router(), back.meta.lam)
        out[name] = {"k": k, "routed_one_prompt_to_a_model": d.model in t["models"]}
    return out


RUN: dict[str, Callable[[dict], dict]] = {s: globals()[f"stage_{s}"] for s in STAGES}


def digest(folder: Path) -> str:
    """Hash of a stage's files. Manifests hold durations, so they are left out."""
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "manifest" not in p.name and p.suffix != ".log":
            h.update(str(p.relative_to(folder)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def run_stages(cfg: dict, stages: list[str]) -> dict:
    from metis.config import config_id

    results = {}
    previous = ""
    for s in stages:
        t0 = time.perf_counter()
        folder = DRY / s
        if s not in ("s1", "s2"):
            shutil.rmtree(folder, ignore_errors=True)  # output of an older run, never the real runs/
        folder.mkdir(parents=True, exist_ok=True)
        counts = RUN[s](cfg)
        results[s] = {"counts": counts, "duration_s": round(time.perf_counter() - t0, 1),
                      "outputs_sha256": digest(folder), "cost_usd": 0.0}  # fmt: skip
        manifest = {"stage": s, "inputs_sha256": previous, "config_id": config_id(cfg), "seed": cfg["seed"],
                    **results[s]}  # fmt: skip
        (folder / "stage.manifest.json").write_text(json.dumps(manifest, indent=1, default=str), "utf-8")
        previous = results[s]["outputs_sha256"]
        print(s, json.dumps(counts, default=str)[:160], f"{results[s]['duration_s']}s", flush=True)
    return results


def fake_keys() -> str:
    """One made-up value per key pattern in AGENTS.md section 4; none of these is a real key."""
    tail = "a1B2c3D4e5F6g7H8i9J0" * 2
    return " ".join([
        f"sk-{tail}", f"sk-ant-{tail}", f"AIza{tail[:35]}", f"ghp_{tail[:36]}", f"Bearer {tail}",
        f"eyJ{tail}.{tail}.{tail}", f"https://x.example/a?key={tail}", f"api_key={tail}",
        f"password={tail}", f'"{tail}{tail}"',
    ])  # fmt: skip


def plant_keys(prompts: Path, ids: list[str], target: Path) -> int:
    """A copy of the eligible prompts with fake keys in every field that reaches a request."""
    from metis.data.redact import redact_obj

    fake = fake_keys()
    df = pd.read_parquet(prompts)
    df = df[df["prompt_id"].isin(ids)].reset_index(drop=True)
    df["text"] = df["text"] + " " + fake
    df["instructions"] = df["instructions"].fillna("") + " " + fake
    df["rag_context"] = [[*(c if c is not None else []), fake] for c in df["rag_context"]]
    df["history"] = [[{"role": "user", "content": fake}, *(h if h is not None else [])] for h in df["history"]]
    df.to_parquet(target, index=False)
    return sum(redact_obj([fake])[1].values()) * 4 * len(df)


def leak_test() -> dict:
    """WP-07 step 6: fake keys in every eligible sample prompt, an empty cache so each request is
    really built, both judges; scan what would have been sent. The stored prompts hold no key
    patterns, so without planting them this test would have nothing to catch."""
    from metis.data.redact import redact_obj

    box = DRY / "leak"
    shutil.rmtree(box, ignore_errors=True)
    box.mkdir(parents=True)
    rec = box / "requests.jsonl"
    env = {**ENV, "METIS_MOCK_CACHE": str(box / "cache.sqlite"), "METIS_MOCK_RECORD": str(rec)}
    prompts = DRY / "s1/prompts.parquet"
    table = pd.read_parquet(prompts, columns=["prompt_id", "eligible_labeled"])
    ids = sorted(table.loc[table["eligible_labeled"], "prompt_id"])  # what a real run may send
    planted = plant_keys(prompts, ids, box / "planted.parquet")
    pd.DataFrame({"prompt_id": ids, "split": "val", "in_pilot": False}).to_parquet(box / "all.parquet")
    args = ("--prompts", box / "planted.parquet", "--set", "val", "--stage")
    sh("scripts/s6_generate.py", *args, "gen_main", "--split", box / "all.parquet", "--out", box, env=env)
    for judge in ("judge", "jev"):
        sh("scripts/s7_judge.py", *args, "judge_main", "--s6", box, "--out", box, "--judge", judge, env=env)
    requests = hits = 0
    with open(rec, encoding="utf-8") as f:
        for line in f:
            requests += 1
            hits += sum(redact_obj(json.loads(line)["messages"])[1].values())
    shutil.rmtree(box)  # holds prompt text; the counts are all we keep
    return {"prompts": len(ids), "planted_key_values": planted, "requests_scanned": requests,
            "secret_hits": hits}  # fmt: skip


def checklist(first: dict, second: dict, leak: dict) -> list[tuple[str, str, str]]:
    from metis.router.fingerprints import fail_rates

    t = pd.read_parquet(DRY / "s2/split.parquet", columns=["session_id", "split"])
    test = set(groups("test"))
    val_s, train_s = set(t.loc[t.split == "val", "session_id"]), set(t.loc[t.split == "train", "session_id"])
    clean = not (val_s & train_s or val_s & test or train_s & test)
    v = tables("val")
    k = choice()["pt"]["k_star"]
    labels = labels_for(k, "val")
    grown = np.column_stack([v["pt"], np.zeros(len(labels))])  # a mock new model
    same = np.array_equal(fail_rates(grown, labels, k)[:, :-1], fail_rates(v["pt"], labels, k))
    psi_pw = np.load(DRY / "s8" / f"psi_pw_k{choice()['pw']['k_star']}.npy")
    gap = max(x for key, x in first["s8"]["counts"].items() if key.startswith("bt_vs"))
    m = json.loads((DRY / "s11/metrics.json").read_text("utf-8"))
    beats = all(m["pt"]["areas"]["uniroute"] >= m["pt"]["areas"][n] for n in ("zerorouter", "knn"))

    def mark(ok: bool) -> str:
        return "✓" if ok else "✗"

    return [
        ("No prompt or conversation in two splits", mark(clean), "sessions compared on the sample"),
        ("Every val cluster has at least n_min prompts; clusters nameable", "–", "real clusters: WP-08, WP-14"),
        ("Pilot decision recorded", "n.a.", "WP-11"),
        ("Judge-human agreement gate passed", "n.a.", "WP-11"),
        ("Pointwise: tau chosen on S_cal; alpha 0 reproduces Eq. 12", "–", "Eq. 12 in tests; tau is a mock value here"),
        ("Pairwise: closed form matches the BT fit; anchor row 0.5",
         mark(gap < 1e-4 and np.allclose(psi_pw[:, v["anchor"]], 0.5)), f"largest gap {gap:.1e}"),
        ("Test set not used for method, K, lambda, tau, rubric, thresholds", "✓",
         "S9 and S10 read val only; the mock test here is the sample's own draw"),
        ("UniRoute area at least ZeroRouter's and K-NN's on test", "n.a." if not beats else "–",
         f"mock numbers mean nothing (holds here: {beats}); real check in WP-19"),
        ("Adding a mock new model touches only its row and lambda", mark(same), "pointwise, K*"),
        ("A rerun gets cache hits for every call", mark(second["s6"]["counts"]["new_calls"] == 0 and
         second["s7"]["counts"]["new_calls"] == 0), "second run"),
    ]  # fmt: skip


def write_report(first: dict, second: dict, leak: dict) -> None:
    m = json.loads((DRY / "s11/metrics.json").read_text("utf-8"))
    same = {s: first[s]["outputs_sha256"] == second[s]["outputs_sha256"] for s in first}
    calls = {r: second[r]["counts"]["new_calls"] for r in ("s6", "s7")}
    lines = [
        "# Dry run report (WP-07)", "",
        ("**MOCK.** Sample only, mock LLM, mock grades: every quality number here is made up and says "
         "nothing about the models. Only the plumbing is tested. Measured: stage durations, counts, hashes."),
        "", f"K values: {KS} (explicit: `candidate_ks` is empty for 60 prompts). Mock tau = {TAU}.",
        "", "## Stages (first run)", "",
        "| Stage | Counts | Seconds | $ | Second run identical |", "|---|---|---:|---:|---|",
    ]  # fmt: skip
    for s, r in first.items():
        text = json.dumps(r["counts"], default=str).replace("|", "/")
        lines.append(f"| {s} | `{text[:110]}` | {r['duration_s']} | 0 | {'yes' if same[s] else '**NO**'} |")
    lines += ["", f"Second run: new mock calls S6 = {calls['s6']}, S7 = {calls['s7']}.", "",
              "## Leak test", "", (f"All {leak['prompts']} eligible sample prompts, 4 models, both judges. The stored prompts hold no key "
              f"patterns, so {leak['planted_key_values']} fake key values were planted in the message, instructions, "
              f"RAG context and history. Requests scanned: {leak['requests_scanned']}. "
              f"Secret hits: {leak['secret_hits']}."),
              "", "## Mock fingerprints (MOCK)", ""]  # fmt: skip
    head = "| cluster | n | " + " | ".join(m["models"]) + " |"
    for method in METHODS:
        r = m[method]
        lines += [f"{method}, K* = {r['k_star']} (MOCK)", "", head, "|---|---:|" + "---:|" * len(m["models"])]
        lines += [f"| {c} | {n} | " + " | ".join(f"{x:.2f}" for x in row) + " |"
                  for c, (n, row) in enumerate(zip(r["counts"], r["psi"], strict=True))]  # fmt: skip
        lines.append("")
    lines += ["## Mock deferral curves (MOCK)", "", f"Test n = {m['n_test']}, val n = {m['n_val']}.", "",
              "| method | router | area |", "|---|---|---:|"]  # fmt: skip
    for method in METHODS:
        lines += [f"| {method} | {n} | {a:.3f} |" for n, a in sorted(m[method]["areas"].items())]
    for method in METHODS:
        c = m[method]
        d = c["uniroute_minus_zero"]
        lines += ["", (f"{method}: UniRoute minus ZeroRouter {d['estimate']:.3f}, 95% CI {d['low']:.3f} to "
                  f"{d['high']:.3f} (session bootstrap, n_boot = {d['n_boot']}, MOCK)."), "",
                  "| cost | " + " | ".join(f"{x:.2f}" for x in c["curve"]["cost"]) + " |",
                  "|---|" + "---:|" * len(c["curve"]["cost"]),
                  "| quality | " + " | ".join(f"{x:.2f}" for x in c["curve"]["quality"]) + " |"]  # fmt: skip
    lines += ["", "## Artifacts", "", "`runs/dry/s12/artifact_point`, `runs/dry/s12/artifact_pair` (git-ignored)",
              "", "## Spec section 10 checklist", "", "| Item | Status | Note |", "|---|---|---|"]  # fmt: skip
    lines += [f"| {a} | {b} | {c} |" for a, b, c in checklist(first, second, leak)]
    lines += ["", "## Not covered", "",
              "- Qdrant: K-NN used an in-memory exact search. Real calls, prices and usage reporting wait for WP-09.",
              "- S3 and S4 full-data runs are not repeated here. The holdout demo is WP-14.",
              "- Val and test use most of the 100 sample sessions, so train has only 56 prompts; some K = 3 and",
              "  K = 4 clusters are empty in val. Mock grades use K = 4. This exercises the empty-cluster path.",
              ""]  # fmt: skip
    (ROOT / "results/dry_run_report.md").write_text("\n".join(lines), "utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--sizes", choices=("sample",), default="sample")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--stages", nargs="+", choices=STAGES, default=list(STAGES))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not args.mock:
        raise SystemExit("this script is mock only: pass --mock (real runs are WP-09 onward)")
    os.environ.update(METIS_MOCK="1", METIS_MOCK_CACHE=ENV["METIS_MOCK_CACHE"])

    from metis.config import load_config

    cfg = load_config(Path(args.config).stem)
    if not args.check:
        run_stages(cfg, args.stages)
        return 0
    shutil.rmtree(DRY, ignore_errors=True)
    print("first run", flush=True)
    first = run_stages(cfg, list(STAGES))
    print("second run", flush=True)
    second = run_stages(cfg, list(STAGES))
    leak = leak_test()
    write_report(first, second, leak)
    same = all(first[s]["outputs_sha256"] == second[s]["outputs_sha256"] for s in STAGES)
    calls = second["s6"]["counts"]["new_calls"] + second["s7"]["counts"]["new_calls"]
    print(json.dumps({"identical": same, "new_calls_second_run": calls, **leak}))
    return 0 if same and calls == 0 and leak["secret_hits"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
