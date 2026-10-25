"""WP-03b: LaTeX tables for the Persian clustering report, generated from results/wp03b_persian/*.json.

Numbers only (no prompt text). Writes report/persian_clustering/latex/tables/*.tex.

Usage: uv run python scripts/s4_latex_tables.py
"""

from __future__ import annotations

import json
from pathlib import Path

from s4_persian_cluster import CHAT, load_all

from metis.data.lang import lang_tag

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "wp03b_persian"
OUT = ROOT / "report" / "persian_clustering" / "latex" / "tables"
SETS = {"mix": ("mix", "source"), "khayyam": ("Khayyam", "label"), "mmlu": ("Global-MMLU", "fine"),
        "one_topic": ("one topic", "fine"), "chat": ("chat", None)}  # fmt: skip
KHAYYAM_EN = {
    "زبان و ادبیات فارسی دوره دوم متوسطه": "Persian literature (upper sec.)",
    "زبان و ادبیات فارسی دوره اول متوسطه": "Persian literature (lower sec.)",
    "زبان و ادبیات فارسی دوره دوم ابتدایی": "Persian literature (upper prim.)",
    "زبان و ادبیات فارسی دوره اول ابتدایی": "Persian literature (lower prim.)",
    "فیزیک دوره دوم متوسطه": "Physics (upper sec.)",
    "شیمی دوره دوم متوسطه": "Chemistry (upper sec.)",
    "زیست شناسی دوره دوم متوسطه": "Biology (upper sec.)",
    "زمین شناسی دوره دوم متوسطه": "Geology (upper sec.)",
    "ریاضی دوره دوم متوسطه": "Mathematics (upper sec.)",
    "ریاضی و آمار دوره دوم متوسطه": "Mathematics \\& statistics (upper sec.)",
    "حسابان دوره دوم متوسطه": "Calculus (upper sec.)",
    "هندسه دوره دوم متوسطه": "Geometry (upper sec.)",
    "آمار و احتمال دوره دوم متوسطه": "Statistics \\& probability (upper sec.)",
    "ریاضیات گسسته دوره دوم متوسطه": "Discrete mathematics (upper sec.)",
    "ریاضی دوره اول متوسطه": "Mathematics (lower sec.)",
    "ریاضی دوره دوم ابتدایی": "Mathematics (upper prim.)",
    "ریاضی دوره اول ابتدایی": "Mathematics (lower prim.)",
    "هوش ریاضی و منطقی دوره دوم ابتدایی": "Mathematical \\& logical IQ (upper prim.)",
    "هوش کلامی و ادبی دوره دوم ابتدایی": "Verbal \\& literary IQ (upper prim.)",
    "سرعت و دقت دوره دوم ابتدایی": "Speed \\& accuracy (upper prim.)",
    "استعداد تحلیلی دوره اول متوسطه": "Analytical aptitude (lower sec.)",
    "علوم تجربی دوره اول متوسطه": "Science (lower sec.)",
    "علوم تجربی دوره دوم ابتدایی": "Science (upper prim.)",
    "علوم تجربی دوره اول ابتدایی": "Science (lower prim.)",
    "تاریخ دوره دوم متوسطه": "History (upper sec.)",
    "جغرافیا دوره دوم متوسطه": "Geography (upper sec.)",
    "جامعه شناسی دوره دوم متوسطه": "Sociology (upper sec.)",
    "اقتصاد دوره دوم متوسطه": "Economics (upper sec.)",
    "روانشناسی دوره دوم متوسطه": "Psychology (upper sec.)",
    "فلسفه دوره دوم متوسطه": "Philosophy (upper sec.)",
    "منطق دوره دوم متوسطه": "Logic (upper sec.)",
    "دین و زندگی دوره دوم متوسطه": "Religion \\& life (upper sec.)",
    "تعلیم و تربیت اسلامی دوره اول متوسطه": "Islamic education (lower sec.)",
    "تعلیم و تربیت اسلامی دوره دوم ابتدایی": "Islamic education (upper prim.)",
    "تعلیم و تربیت اسلامی دوره اول ابتدایی": "Islamic education (lower prim.)",
    "مطالعات اجتماعی دوره اول متوسطه": "Social studies (lower sec.)",
    "مطالعات اجتماعی دوره دوم ابتدایی": "Social studies (upper prim.)",
    "مطالعات اجتماعی دوره اول ابتدایی": "Social studies (lower prim.)",
}


def tex(s: str) -> str:
    return (
        str(s).replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("\\\\&", "\\&")
    )


def pm(x: dict, d: int = 3) -> str:
    return f"{x['mean']:.{d}f}" + (f" $\\pm$ {x['ci95']:.{d}f}" if x.get("ci95") else "")


def write(name: str, body: str) -> None:
    (OUT / f"{name}.tex").write_text(body, encoding="utf-8")


def load(run: str) -> dict:
    return json.loads((RES / f"persian_clustering_{run}.json").read_text())


def t_sources() -> None:
    man = json.loads((RES / "persian_sources.json").read_text())
    df = load_all()
    df = df.assign(chars=df["text"].str.len(), fa=df["text"].map(lang_tag) == "fa")
    g = df.groupby("source")
    rows = []
    for s in df["source"].value_counts().index:
        x = g.get_group(s)
        lab = x["label"].nunique() if s not in CHAT and x["label"].nunique() > 1 else "--"
        fine = x["fine"].nunique() if x["fine"].notna().any() and x["fine"].nunique() > 1 else "--"
        rows.append(f"{tex(s)} & {'chat' if s in CHAT else 'benchmark'} & {man[s]['rows']:,} & {len(x):,} & {lab} & {fine} & "
                    f"{x.chars.median():.0f} / {x.chars.quantile(.9):.0f} & {x.fa.mean():.0%} & {tex(man[s]['licence'].split(' (')[0])} \\\\")  # fmt: skip
    write("sources", "\\begin{tabular}{llrrrrrrl}\n\\toprule\nSource & Kind & Rows & Kept & Labels & Fine & Chars p50/p90 & Persian & Licence \\\\\n\\midrule\n"
          + "\n".join(rows).replace("%", "\\%") + f"\n\\midrule\nTotal & & & {len(df):,} & & & & {df.fa.mean():.0%} & \\\\\n\\bottomrule\n\\end{{tabular}}\n".replace("%", "\\%"))  # fmt: skip


def t_main() -> None:
    res = {m: load(m) for m in ("small", "nano")}
    rows = []
    for s, (title, lb) in SETS.items():
        for k in ("3", "4", "5", "6", "7", "8"):
            cells = []
            for m in ("small", "nano"):
                x = res[m]["sets"][s]["K"][k]
                cells += [
                    pm(x[lb]["nmi"]) if lb else "--",
                    f"{x['silhouette']['mean']:.3f}",
                    f"{x['val_small']['mean']:.1f}",
                ]
            first = f"\\multirow{{6}}{{*}}{{{title}}}" if k == "3" else ""
            rows.append(f"{first} & {k} & " + " & ".join(cells) + " \\\\")
        rows.append("\\midrule")
    write("main_k", "\\begin{tabular}{llrrrrrr}\n\\toprule\n & & \\multicolumn{3}{c}{small} & \\multicolumn{3}{c}{nano} \\\\\n"
          "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}\nSet & $K$ & NMI & Sil. & $<50$ & NMI & Sil. & $<50$ \\\\\n\\midrule\n"
          + "\n".join(rows[:-1]) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_compare() -> None:
    runs = {"small": "small", "nano": "nano", "nano_text-matching": "nano (text-m.)"}
    res = {r: load(r) for r in runs}
    rows = []
    for s, (title, lb) in SETS.items():
        cells = [
            pm(res[r]["sets"][s]["K"]["8"][lb]["nmi"])
            if lb
            else f"sil. {res[r]['sets'][s]['K']['8']['silhouette']['mean']:.3f}"
            for r in runs
        ]
        rows.append(f"{title} ({tex(lb) if lb else 'no labels'}) & " + " & ".join(cells) + " \\\\")
    d = [res[r]["sets"]["khayyam"]["K"]["8"]["difficulty"]["val"]["gap_reduction"] for r in runs]
    rows.append(
        "Khayyam difficulty gap shrink & "
        + " & ".join(f"{x['mean']:.1%} $\\pm$ {x['ci95']:.1%}" for x in d).replace("%", "\\%")
        + " \\\\"
    )
    rows.append(
        "Run time (min) & " + " & ".join(f"{res[r]['duration_s'] / 60:.0f}" for r in runs) + " \\\\"
    )
    write("compare", "\\begin{tabular}{lccc}\n\\toprule\n$K = 8$ & " + " & ".join(runs.values()) + " \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_difficulty() -> None:
    res = {m: load(m) for m in ("small", "nano")}
    ks = ["3", "5", "8", "16", "32", "64"]
    rows = []
    for s, title in (("khayyam", "Khayyam"), ("one_topic", "one topic")):
        for m in ("small", "nano"):
            for src, name in (("val", "$\\Psi$ from val (400)"), ("train", "$\\Psi$ from train")):
                cells = []
                for k in ks:
                    x = res[m]["sets"][s]["K"][k]["difficulty"][src]["gap_reduction"]
                    cells.append(
                        f"{x['mean'] * 100:.1f}"
                        + (f"$\\pm${x['ci95'] * 100:.1f}" if src == "val" and x["ci95"] else "")
                    )
                rows.append(f"{title} & {m} & {name} & " + " & ".join(cells) + " \\\\")
        rows.append("\\midrule")
    write("difficulty", "\\begin{tabular}{lll" + "r" * len(ks) + "}\n\\toprule\nSet & Model & Profile & "
          + " & ".join(f"$K={k}$" for k in ks) + " \\\\\n\\midrule\n" + "\n".join(rows[:-1]) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_khayyam_clusters() -> None:
    r = json.loads((RES / "persian_cluster_meaning.json").read_text())["sets"]["khayyam"]["label"]
    names = {0: "humanities mix", 1: "mathematics", 2: "Persian literature", 3: "religion \\& philosophy",
             4: "chemistry", 5: "history \\& society", 6: "biology \\& science", 7: "physics"}  # fmt: skip
    rows = []
    for c in r["clusters"]:
        top = "; ".join(
            f"{KHAYYAM_EN.get(a, tex(a))} {b:.0%}" for a, b in list(c["top"].items())[:3]
        ).replace("%", "\\%")
        rows.append(
            f"{c['cluster']} & {names[c['cluster']]} & {c['n']:,} & \\footnotesize {top} & {c['human_error']:.2f} \\\\"
        )
    write("khayyam_clusters", "\\begin{tabular}{rlr>{\\raggedright\\arraybackslash}p{8.2cm}r}\n\\toprule\n\\# & Name & $n$ & Largest categories (share of cluster) & Error \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip
    rows = []
    for lb, x in sorted(r["labels"].items(), key=lambda t: -t[1]["share_in_main"]):
        rows.append(
            f"{KHAYYAM_EN.get(lb, tex(lb))} & {x['n']} & {x['main_cluster']} ({names[x['main_cluster']]}) & {x['share_in_main']:.0%} \\\\".replace(
                "%", "\\%"
            )
        )
    write("khayyam_loyalty", "\\begin{longtable}{lrlr}\n\\toprule\nKhayyam category & $n$ (test) & Main cluster & Share there \\\\\n\\midrule\n\\endhead\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{longtable}\n")  # fmt: skip


def t_mmlu_clusters() -> None:
    r = json.loads((RES / "persian_cluster_meaning.json").read_text())["sets"]["mmlu"]
    rows = []
    for c, d in zip(r["fine"]["clusters"], r["label"]["clusters"]):
        top = "; ".join(
            f"{tex(a.replace('_', ' '))} {b:.0%}" for a, b in list(c["top"].items())[:3]
        ).replace("%", "\\%")
        cat = "; ".join(f"{tex(a)} {b:.0%}" for a, b in list(d["top"].items())[:2]).replace(
            "%", "\\%"
        )
        rows.append(f"{c['cluster']} & {c['n']} & \\footnotesize {top} & \\footnotesize {cat} \\\\")
    write("mmlu_clusters", "\\begin{tabular}{rr>{\\raggedright\\arraybackslash}p{7.2cm}>{\\raggedright\\arraybackslash}p{4.2cm}}\n\\toprule\n\\# & $n$ & Largest subjects & Largest categories \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_mix_clusters() -> None:
    r = json.loads((RES / "persian_cluster_meaning.json").read_text())["sets"]["mix"]["source"]
    rows = [f"{c['cluster']} & {c['n']:,} & \\footnotesize " + "; ".join(f"{tex(a)} {b:.0%}" for a, b in list(c["top"].items())[:4]).replace("%", "\\%") + " \\\\"
            for c in r["clusters"]]  # fmt: skip
    write("mix_clusters", "\\begin{tabular}{rr>{\\raggedright\\arraybackslash}p{10cm}}\n\\toprule\n\\# & $n$ & Largest sources (share of cluster) \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_chat_clusters() -> None:
    top = json.loads((RES / "persian_cluster_topics.json").read_text())["sets"]["chat"]["clusters"]
    mean = json.loads((RES / "persian_cluster_meaning.json").read_text())["sets"]["chat"]
    names = {0: "general / poetry", 1: "general, writing, personal", 2: "short general questions", 3: "health",
             4: "science", 5: "business \\& money", 6: "history \\& society", 7: "coding \\& tech"}  # fmt: skip
    rows = []
    for t, f, s in zip(top, mean["features"], mean["source"]["clusters"]):
        tp = "; ".join(f"{a.replace('_', ' ')} {b:.0%}" for a, b in list(t["topics"].items())[:3])
        src = max(s["top"], key=s["top"].get)
        rows.append((f"{t['cluster']} & {names[t['cluster']]} & {t['n']} & \\footnotesize {tp} & {f['chars_p50']:.0f} & "
                     f"{f['latin_share']:.0%} & {f['code'] + f['math']:.0%} & {tex(src)} {s['top'][src]:.0%} \\\\").replace("%", "\\%"))  # fmt: skip
    write("chat_clusters", "\\begin{tabular}{rlr>{\\raggedright\\arraybackslash}p{5.0cm}rrrl}\n\\toprule\n\\# & Name & $n$ & Nearest topic & Chars & Latin & Code/math & Main source \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")  # fmt: skip


def t_full(model: str) -> None:
    res = load(model)
    parts = []
    for s, (title, lb) in SETS.items():
        r = res["sets"][s]
        rows = []
        for k in sorted(r["K"], key=int):
            x = r["K"][k]
            lab = (
                [pm(x[lb]["nmi"]), f"{x[lb]['ari']['mean']:.3f}", f"{x[lb]['purity']['mean']:.3f}"]
                if lb
                else ["--"] * 3
            )
            rows.append(
                f"{k} & {x['silhouette']['n_splits']} & "
                + " & ".join(lab)
                + f" & {x['silhouette']['mean']:.3f} & {x['val_min']['mean']:.0f} & {x['val_small']['mean']:.1f} & {x['test_max_share']['mean']:.2f} \\\\"
            )
        parts.append(f"\\multicolumn{{9}}{{l}}{{\\textbf{{{title}}} ($n = {r['n']:,}$; label: {tex(lb) if lb else 'none'})}} \\\\\n\\midrule\n" + "\n".join(rows))  # fmt: skip
    write(f"full_{model}", "\\begin{longtable}{rrrrrrrrr}\n\\toprule\n$K$ & splits & NMI & ARI & Purity & Sil. & val min & val $<50$ & max share \\\\\n\\midrule\n\\endhead\n"
          + "\n\\midrule\n".join(parts) + "\n\\bottomrule\n\\end{longtable}\n")  # fmt: skip


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t_sources()
    t_main()
    t_compare()
    t_difficulty()
    t_khayyam_clusters()
    t_mmlu_clusters()
    t_mix_clusters()
    t_chat_clusters()
    for m in ("small", "nano"):
        t_full(m)
    print(f"tables: {sorted(p.name for p in OUT.glob('*.tex'))}")


if __name__ == "__main__":
    main()
