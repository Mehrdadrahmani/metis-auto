"""WP-03b step 1: download public Persian datasets for the clustering test (no LLM calls).

Uses the Hugging Face datasets-server (plain HTTP): parquet files for benchmarks; for the large chat sets
only the `language` column and the row groups holding Persian rows are read, via HTTP range requests. Each source is saved as `data/external/<name>.parquet` with columns
`ext_id, source, text, label, fine` (label = coarse topic, fine = subject or None). Text is only stored,
never printed. Resumable: finished sources are skipped; per-file chat extracts are cached.

Usage: uv run python scripts/ext_download.py [--only name,name]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import get_token

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "external"
API = "https://datasets-server.huggingface.co"
SEED = 20261020


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def hf_request(url: str, **kw) -> urllib.request.Request:
    """Request carrying the HF token (gated sets) for huggingface.co hosts only; never sent on redirects."""
    req = urllib.request.Request(url, **kw)
    tok = get_token()  # HF_TOKEN env var or `hf auth login`; never printed
    if tok and (urllib.parse.urlparse(url).hostname or "").endswith("huggingface.co"):
        req.add_unredirected_header("Authorization", f"Bearer {tok}")
    return req


def get_json(url: str, tries: int = 12) -> dict:
    for i in range(tries):
        try:
            with urllib.request.urlopen(hf_request(url), timeout=90) as r:
                d = json.load(r)
            if "error" not in d:
                return d
            log(f"  retry {i + 1}: {str(d['error'])[:80]}")
        except (OSError, ValueError) as e:  # network hiccup, bad JSON
            log(f"  retry {i + 1}: {type(e).__name__}")
        time.sleep(min(60, 5 * (i + 1)))
    raise RuntimeError(f"failed: {url}")


def parquet(ds: str, config: str, split: str, columns: list[str]) -> pd.DataFrame:
    q = urllib.parse.urlencode({"dataset": ds, "config": config, "split": split})
    files = [f for f in get_json(f"{API}/parquet?{q}")["parquet_files"] if f["split"] == split]
    parts = []
    for f in files:
        dest = OUT / "raw" / ds.replace("/", "__") / config / split / f["filename"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_size != f["size"]:
            tok = get_token()  # header via stdin, so it is not visible in the process list
            subprocess.run(
                ["curl", "-sSL", "--retry", "5", "-C", "-", "-H", "@-", "-o", str(dest), f["url"]],
                input=f"Authorization: Bearer {tok}\n" if tok else "",
                text=True,
                check=True,
            )
        parts.append(pd.read_parquet(dest, columns=columns))
    return pd.concat(parts, ignore_index=True)


class HTTPRange(io.RawIOBase):
    """Seekable read-only file over HTTP range requests (pyarrow reads only the parts it needs)."""

    def __init__(self, url: str) -> None:
        with urllib.request.urlopen(hf_request(url, method="HEAD"), timeout=90) as r:
            self.url, self.size = (
                r.url,
                int(r.headers["Content-Length"]),
            )  # follow the CDN redirect once
        self.pos = 0

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, off: int, whence: int = 0) -> int:
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def read(self, n: int = -1) -> bytes:
        end = self.size if n is None or n < 0 else min(self.size, self.pos + n)
        if end <= self.pos:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end - 1}"})
        for i in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = r.read()
                break
            except OSError:
                time.sleep(5 * (i + 1))
        else:
            raise RuntimeError(f"range read failed: {self.url}")
        self.pos += len(data)
        return data


def filtered(ds: str, lang: str, columns: list[str], extract) -> pd.DataFrame:
    """Rows with language == `lang` from every parquet file of `ds`; `extract(row) -> dict`."""
    files = get_json(f"{API}/parquet?dataset={urllib.parse.quote(ds)}")["parquet_files"]
    rows = []
    for f in files:
        cache = (
            OUT
            / "raw"
            / ds.replace("/", "__")
            / (f["config"] + "_" + f["split"] + "_" + f["filename"] + ".jsonl")
        )
        if not cache.exists():
            pf = pq.ParquetFile(HTTPRange(f["url"]))
            got = []
            for g in range(pf.num_row_groups):
                langs = pf.read_row_group(g, columns=["language"]).column("language").to_pylist()
                if lang not in langs:
                    continue
                t = pf.read_row_group(g, columns=columns).to_pylist()
                got += [extract(r) for r, x in zip(t, langs, strict=True) if x == lang]
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in got), encoding="utf-8"
            )
            log(f"  {ds} {f['filename']}: {len(got)} rows")
        rows += [json.loads(x) for x in cache.read_text(encoding="utf-8").splitlines()]
    return pd.DataFrame(rows)


def arena140(r):
    msg = r["conversation_a"][0]
    return {
        "id": r["id"],
        "text": " ".join(c.get("text") or "" for c in msg["content"]),
        "role": msg["role"],
    }


def arena100(r):
    msg = r["conversation_a"][0]
    return {"id": r["question_id"], "text": msg["content"], "role": msg["role"]}


def wildchat(r):
    msg = r["conversation"][0]
    return {"id": r["conversation_hash"], "text": msg["content"], "role": msg["role"]}


def build(name: str) -> tuple[pd.DataFrame, dict]:
    """Return the standard frame and the source record (dataset, licence)."""
    if name == "global_mmlu":
        df = parquet(
            "CohereLabs/Global-MMLU",
            "fa",
            "test",
            ["sample_id", "question", "subject", "subject_category"],
        )
        return pd.DataFrame({"ext_id": df.sample_id, "text": df.question, "label": df.subject_category,
                             "fine": df.subject}), {"dataset": "CohereLabs/Global-MMLU:fa", "licence": "apache-2.0"}  # fmt: skip
    if name == "include":
        df = parquet(
            "CohereLabs/include-base-44", "Persian", "test", ["question", "domain", "subject"]
        )
        return pd.DataFrame({"ext_id": df.index.astype(str), "text": df.question, "label": df.domain,
                             "fine": df.subject}), {"dataset": "CohereLabs/include-base-44:Persian", "licence": "apache-2.0"}  # fmt: skip
    if name == "persian_arc":
        parts = []
        for cfg in ("ARC-Challenge", "ARC-Easy"):
            for sp in ("train", "validation", "test"):
                d = parquet("MatinaAI/persian_arc", cfg, sp, ["id", "question_fa"])
                parts.append(d.assign(fine=cfg))
        df = pd.concat(parts, ignore_index=True)
        return pd.DataFrame({"ext_id": df.id, "text": df.question_fa, "label": "science (ARC)",
                             "fine": df.fine}), {"dataset": "MatinaAI/persian_arc", "licence": "cc-by-sa-4.0"}  # fmt: skip
    if name == "parsinlu_mc":
        df = pd.concat([parquet("PartAI/ParsiNLU-multiple-choice", "default", sp, ["id", "question", "category"])
                        for sp in ("train", "dev", "test")], ignore_index=True)  # fmt: skip
        return pd.DataFrame({"ext_id": df.id.astype(str), "text": df.question, "label": df.category,
                             "fine": df.category}), {"dataset": "PartAI/ParsiNLU-multiple-choice", "licence": "unknown (ParsiNLU: CC BY-NC-SA 4.0)"}  # fmt: skip
    if name == "persian_bbh":
        cfgs = [
            c
            for c in get_json(f"{API}/info?dataset=MatinaAI/persian_bbh")["dataset_info"]
            if c != "cot"
        ]
        parts = [
            parquet("MatinaAI/persian_bbh", c, "train", ["input"]).assign(fine=c) for c in cfgs
        ]
        df = pd.concat(parts, ignore_index=True)
        return pd.DataFrame({"ext_id": df.fine + ":" + df.index.astype(str), "text": df.input,
                             "label": "reasoning (BBH)", "fine": df.fine}), {"dataset": "MatinaAI/persian_bbh", "licence": "unknown"}  # fmt: skip
    if name == "percor":
        df = parquet("MCINext/PerCoR", "default", "validation", ["text_1", "domain"])
        df = df.sample(n=min(4000, len(df)), random_state=SEED)
        return pd.DataFrame({"ext_id": df.index.astype(str), "text": df.text_1, "label": "commonsense (PerCoR)",
                             "fine": df.domain}), {"dataset": "MCINext/PerCoR:validation (4,000 sampled)", "licence": "apache-2.0"}  # fmt: skip
    if name == "legal_qa":
        df = parquet(
            "PerSets/iran-legal-persian-qa",
            "default",
            "train",
            ["id", "questionTitle", "questionBody"],
        )
        df = df.sample(n=3000, random_state=SEED)
        text = df.questionBody.where(df.questionBody.fillna("").str.len() > 0, df.questionTitle)
        return pd.DataFrame({"ext_id": df.id.astype(str), "text": text, "label": "law (legal QA)",
                             "fine": None}), {"dataset": "PerSets/iran-legal-persian-qa (3,000 sampled)", "licence": "cc"}  # fmt: skip
    if name == "med_qa":
        df = parquet("aictsharif/persian-med-qa", "default", "train", ["question"])
        df = df.sample(n=3000, random_state=SEED)
        return pd.DataFrame({"ext_id": df.index.astype(str), "text": df.question, "label": "medicine (med QA)",
                             "fine": None}), {"dataset": "aictsharif/persian-med-qa (3,000 sampled)", "licence": "apache-2.0"}  # fmt: skip
    if name == "khayyam":  # gated: needs `hf auth login` with access granted by the authors
        df = parquet("raia-center/khayyam-challenge", "default", "train",
                     ["ID", "Question Body", "Course Title", "final_category_fa"])  # fmt: skip
        return pd.DataFrame({"ext_id": df.ID.astype(str), "text": df["Question Body"], "label": df.final_category_fa,
                             "fine": df["Course Title"]}), {"dataset": "raia-center/khayyam-challenge (gated)", "licence": "cc-by-nc-nd-4.0 (academic only)"}  # fmt: skip
    if name == "arena":
        a = filtered(
            "lmarena-ai/arena-human-preference-140k", "fa", ["id", "conversation_a"], arena140
        )
        b = filtered(
            "lmarena-ai/arena-human-preference-100k",
            "Persian",
            ["question_id", "conversation_a"],
            arena100,
        )
        df = pd.concat(
            [a.assign(fine="arena-140k"), b.assign(fine="arena-100k")], ignore_index=True
        )
        df = df[df.role == "user"]
        return pd.DataFrame({"ext_id": df.id.astype(str), "text": df.text, "label": "chat (Arena)",
                             "fine": df.fine}), {"dataset": "lmarena-ai/arena-human-preference-140k + 100k (Persian)", "licence": "cc-by-4.0"}  # fmt: skip
    if name == "wildchat":
        df = filtered(
            "allenai/WildChat-1M", "Persian", ["conversation_hash", "conversation"], wildchat
        )
        df = df[df.role == "user"]
        return pd.DataFrame({"ext_id": df.id.astype(str), "text": df.text, "label": "chat (WildChat)",
                             "fine": None}), {"dataset": "allenai/WildChat-1M (Persian)", "licence": "odc-by"}  # fmt: skip
    if name == "lmsys_fa":
        df = parquet("mshojaei77/Persian_lmsys_QA", "default", "train", ["question"])
        return pd.DataFrame({"ext_id": df.index.astype(str), "text": df.question, "label": "chat (lmsys)",
                             "fine": None}), {"dataset": "mshojaei77/Persian_lmsys_QA", "licence": "mit"}  # fmt: skip
    raise ValueError(name)


SOURCES = ["global_mmlu", "include", "persian_arc", "parsinlu_mc", "persian_bbh", "percor",
           "legal_qa", "med_qa", "khayyam", "lmsys_fa", "arena", "wildchat"]  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    man_path = OUT / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else {}
    for name in a.only.split(",") if a.only else SOURCES:
        path = OUT / f"{name}.parquet"
        if path.exists() and name in manifest:
            log(f"{name}: done ({manifest[name]['rows']} rows)")
            continue
        log(f"{name}: downloading")
        df, rec = build(name)
        df = df.assign(source=name, text=df.text.fillna("").astype(str))[
            ["ext_id", "source", "text", "label", "fine"]
        ]
        df["fine"] = df["fine"].astype("string")
        df.to_parquet(path, index=False)
        rec |= {"rows": len(df), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
                "date": time.strftime("%Y-%m-%d")}  # fmt: skip
        manifest[name] = rec
        man_path.write_text(json.dumps(manifest, indent=1))
        log(f"{name}: {len(df)} rows")
    (ROOT / "results" / "persian_sources.json").write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
