"""Resumable model download (WP-03): curl -C - with retries into models/<short>_<rev12>/.

The HF client lost 1 GB on a network drop; curl resumes partial files. Usage:
uv run python scripts/fetch_model.py jinaai/jina-embeddings-v5-text-small <revision>
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    repo, rev = sys.argv[1], sys.argv[2]
    # folder name must be a valid Python identifier (the model's remote code is imported from it)
    short = repo.split("/")[-1].replace("jina-embeddings-", "jina_").replace("-", "_")
    out = ROOT / "models" / f"{short}_{rev[:12]}"
    info = HfApi().model_info(repo, revision=rev, files_metadata=True)
    for s in sorted(info.siblings, key=lambda s: s.size or 0):
        dst = out / s.rfilename
        dst.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/{repo}/resolve/{rev}/{s.rfilename}"
        for attempt in range(200):
            if dst.exists() and dst.stat().st_size == s.size:
                break
            subprocess.run(["curl", "-sL", "-C", "-", "--retry", "5", "--retry-all-errors",
                            "--speed-limit", "10000", "--speed-time", "30",
                            "-o", str(dst), url], check=False)  # fmt: skip
            if attempt:
                time.sleep(5)
        ok = dst.stat().st_size == s.size
        print(f"{'OK ' if ok else 'FAIL'} {s.rfilename} {s.size}", flush=True)
        if not ok:
            sys.exit(1)
    print("DONE", out, flush=True)


if __name__ == "__main__":
    main()
