"""WP-08 step 8: topics per K-means cluster from a train sample, with local Qwen3-8B through Ollama.

Usage: uv run python scripts/s5_topics.py --ks 9 [--per-cluster 500] [--limit-batches 1]

Local only, $0, resumable (one JSON per finished cluster). Train prompts only, redacted, cut to
MAX_CHARS. Writes runs/s5/topics/k_XX_cYY.json (git-ignored: topic text can echo prompts).
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from metis.config import load_config
from metis.data.redact import redact

ROOT = Path(__file__).resolve().parents[1]
URL = "http://localhost:11434/api/chat"
MODEL = "hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M"
BATCH = 50
MAX_CHARS = 300
BATCH_PROMPT = (
    "Below are numbered chat messages, mostly Persian, sent to chatbots. List the 3 to 5 main topics "
    "they cover. Name each topic in short English, 2 to 5 words, one per line, no numbering. "
    "Do not quote any message or include names or contact details.\n\n"
)
MERGE_PROMPT = (
    "These topic lists describe samples of one cluster of chat messages. Reply with JSON only: "
    '{"name": "<cluster name, 2 to 6 English words>", "topics": ["<up to 6 main topics>"], '
    '"mixed": <true if the topics are unrelated to each other>}\n\n'
)


def ask(prompt: str, seed: int) -> tuple[str, dict]:
    body = {"model": MODEL, "stream": False, "think": False, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": seed, "num_ctx": 8192, "num_predict": 300},
            "messages": [{"role": "user", "content": prompt + "\n/no_think"}]}  # fmt: skip
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.load(r)
    text = out["message"]["content"]
    return text.split("</think>")[-1].strip(), out  # some templates keep an empty think block


def train_table(cfg: dict) -> pd.DataFrame:
    """Train prompts in the order the saved fits use; the same selection as s5_cluster_view.py."""
    out = ROOT / "runs/s4/full" / cfg["s4"]["choice"]
    ids = np.concatenate([np.load(p)["ids"] for p in sorted(out.glob("part-*.npz"))])
    split = pd.read_parquet(ROOT / "runs/s2/split.parquet", columns=["prompt_id", "split"])
    train = set(split.loc[split["split"] == "train", "prompt_id"])
    ids = ids[np.array([i in train for i in ids])]
    df = pd.read_parquet(ROOT / "runs/s1/prompts.parquet", columns=["prompt_id", "embed_input"])
    return df.set_index("prompt_id").loc[ids].reset_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ks", type=int, nargs="+", required=True)
    ap.add_argument("--per-cluster", type=int, default=500)
    ap.add_argument("--limit-batches", type=int, help="speed test: stop each cluster early, save nothing")
    a = ap.parse_args()
    cfg = load_config("pipeline")
    df = train_table(cfg)
    folder = ROOT / "runs/s5/topics"
    folder.mkdir(parents=True, exist_ok=True)
    for k in a.ks:
        with np.load(ROOT / f"runs/s5/view/k_{k:02d}.npz") as z:
            labels = z["labels"]
        assert len(labels) == len(df), "saved fit does not match train"
        for c in range(k):
            path = folder / f"k_{k:02d}_c{c:02d}.json"
            if path.exists() and not a.limit_batches:
                continue
            rng = np.random.default_rng(cfg["seed"] + 1000 * k + c)
            rows = np.flatnonzero(labels == c)
            pick = rng.choice(rows, size=min(a.per_cluster, len(rows)), replace=False)
            texts = [redact(t[:MAX_CHARS])[0].replace("\n", " ") for t in df["embed_input"].iloc[pick]]
            t0 = time.perf_counter()
            lists, tok_in, tok_out = [], 0, 0
            for n, b in enumerate(range(0, len(texts), BATCH)):
                if a.limit_batches and n >= a.limit_batches:
                    break
                body = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(texts[b : b + BATCH]))
                text, r = ask(BATCH_PROMPT + body, cfg["seed"])
                lists.append(text)
                tok_in += r.get("prompt_eval_count", 0)
                tok_out += r.get("eval_count", 0)
            merged, r = ask(MERGE_PROMPT + "\n---\n".join(lists), cfg["seed"])
            secs = time.perf_counter() - t0
            if a.limit_batches:
                print(json.dumps({"k": k, "c": c, "secs": round(secs, 1), "tok_in": tok_in, "tok_out": tok_out,
                                  "batches": len(lists), "n": len(rows)}), merged[:300], lists[0][:300], flush=True)  # fmt: skip
                continue
            out = {"k": k, "cluster": c, "n_train": len(rows), "n_sampled": len(texts), "model": MODEL,
                   "merged": merged, "lists": lists, "seconds": round(secs, 1)}  # fmt: skip
            path.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
            print(k, c, merged[:160].replace("\n", " "), f"{secs:.0f}s", flush=True)


if __name__ == "__main__":
    main()
