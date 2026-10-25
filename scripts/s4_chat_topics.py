"""WP-03b: name clusters without reading prompts: nearest topic anchor per prompt (numbers only).

Each topic = a short description we wrote (Persian + English), embedded with the same Jina model and adapter
as the prompts. Each prompt gets the topic with the highest cosine similarity; we report the topic mix
of every K-means cluster (nano, K = 8, split 1, test part). Checked first on Khayyam, where the true
subject is known (agreement of anchor topic with the known subject group).
Writes results/persian_cluster_topics.json.

Usage: uv run python scripts/s4_chat_topics.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from s4_persian_cluster import EXT, ROOT, SEED, Store, assign, build_sets, load_all, log, split
from sklearn.cluster import KMeans

from metis.config import load_config
from metis.embed.embedder import Embedder

TOPICS = {
    "programming": "برنامه نویسی، کد، پایتون، خطای نرم افزار — programming, code, software bug",
    "math": "ریاضی، معادله، حل مسئله، محاسبه — mathematics, equation, calculation",
    "physics_chem": "فیزیک و شیمی، نیرو، انرژی، واکنش شیمیایی — physics and chemistry",
    "biology_health": "زیست شناسی، پزشکی، بیماری، سلامت، دارو — biology, medicine, health",
    "law": "حقوق، قانون، دادگاه، قرارداد، وکیل — law, court, contract",
    "literature_poetry": "ادبیات فارسی، شعر، شاعر، دستور زبان — Persian literature, poetry, grammar",
    "history_society": "تاریخ، جغرافیا، جامعه، سیاست — history, geography, society, politics",
    "religion_philosophy": "دین، اسلام، قرآن، فلسفه، اخلاق — religion, Islam, philosophy, ethics",
    "business_economy": "اقتصاد، کسب و کار، بازاریابی، پول، بورس — economy, business, marketing",
    "writing_help": "نوشتن متن، مقاله، ایمیل، خلاصه، ترجمه — write a text, essay, email, summary, translation",
    "tech_ai": "هوش مصنوعی، کامپیوتر، موبایل، اینترنت، فناوری — AI, computers, phones, technology",
    "personal_life": "زندگی شخصی، روابط، احساسات، روانشناسی، مشاوره — personal life, relationships, psychology",
    "chitchat": "سلام، احوالپرسی، شوخی، گفتگوی روزمره — hello, greetings, small talk",
}
KHAYYAM_GROUP = {  # known Khayyam subject keyword → expected anchor topic (sanity check)
    "ریاضی": "math", "حسابان": "math", "هندسه": "math", "آمار": "math", "گسسته": "math",
    "فیزیک": "physics_chem", "شیمی": "physics_chem", "زیست": "biology_health",
    "ادبیات": "literature_poetry", "تاریخ": "history_society", "جغرافیا": "history_society",
    "جامعه": "history_society", "مطالعات اجتماعی": "history_society", "اقتصاد": "business_economy",
    "دین": "religion_philosophy", "اسلامی": "religion_philosophy", "فلسفه": "religion_philosophy",
    "روانشناسی": "personal_life",
}  # fmt: skip


def mix_table(topic: np.ndarray, c: np.ndarray, k: int) -> list[dict]:
    rows = []
    for j in range(k):
        vc = pd.Series(topic[c == j]).value_counts(normalize=True)
        rows.append(
            {
                "cluster": j,
                "n": int((c == j).sum()),
                "topics": {a: round(float(b), 3) for a, b in vc.head(4).items()},
            }
        )
    return rows


def main() -> None:
    s4 = load_config("pipeline")["s4"]
    cand = s4["candidates"]["nano"]
    emb = Embedder(cand["name"], cand["revision"], device=s4["device"], path=str(ROOT / cand["path"]),
                   task=s4["task"], prompt_name=s4["prompt_name"], merge_adapter=s4["merge_adapter"],
                   max_tokens=2048, batch_size=s4["batch_size"], max_batch_tokens=s4["max_batch_tokens"])  # fmt: skip
    names = list(TOPICS)
    anchors = emb.encode(list(TOPICS.values()))
    store = Store(EXT / "emb" / "nano_clustering")
    sets = build_sets(load_all())
    out: dict = {"model": "nano", "K": 8, "topics": TOPICS, "sets": {}}
    for name in ("khayyam", "chat"):
        d, _ = sets[name]
        d = d.reset_index(drop=True)
        v = store.get(d["text"].tolist())
        tr, _, te = split(len(d), SEED)
        c = assign(
            v, KMeans(n_clusters=8, n_init=10, random_state=SEED).fit(v[tr]).cluster_centers_
        )
        topic = np.array(names)[np.argmax(v[te] @ anchors.T, axis=1)]
        r = {
            "clusters": mix_table(topic, c[te], 8),
            "overall": pd.Series(topic).value_counts(normalize=True).round(3).to_dict(),
        }
        if name == "khayyam":
            lab = d["label"].astype(str).to_numpy()[te]
            exp = np.array(
                [next((t for kw, t in KHAYYAM_GROUP.items() if kw in lb), "") for lb in lab]
            )
            m = exp != ""
            r["sanity_n"] = int(m.sum())
            r["sanity_agreement"] = round(float((topic[m] == exp[m]).mean()), 3)
            r["sanity_chance"] = round(
                float(sum((exp[m] == t).mean() * (topic[m] == t).mean() for t in names)), 3
            )
            log(f"khayyam sanity: anchor topic = expected subject for {r['sanity_agreement']:.1%} "
                f"(chance {r['sanity_chance']:.1%}, n = {r['sanity_n']})")  # fmt: skip
        out["sets"][name] = r
    (ROOT / "results" / "persian_cluster_topics.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False)
    )
    log("done: results/persian_cluster_topics.json")


if __name__ == "__main__":
    main()
