"""Build the leaderboard from results/*.json and (optionally) write it into README.md.

  python -m bench.leaderboard                 # print markdown
  python -m bench.leaderboard --update-readme # replace the block between the LEADERBOARD markers

Every number comes straight from the results files; nothing in the README table is typed by hand.
MIRACL results come in two splits: results/miracl_<lang>.json (dev) and results/miracl_<lang>_train.json (train,
held out: never used to choose or tune a system).
"""
from __future__ import annotations

import argparse
import json
import os
import re

from .compare import paired

RESULTS = "results"
LANGS = ("zh", "ja", "ko")
SPLITS = (("dev", ""), ("train", "_train"))
BASELINE = "app_bigram"
# Systems whose ranking path is another system's: their ranking numbers are identical and not tested again.
SAME_RANKING_AS = {"trigram_like": "trigram"}
LAW_BUCKETS = (("char1", "1 char"), ("word2", "2-char words"), ("word3", "3-char words"),
               ("word4plus", "4+ char words"), ("span_nonword", "non-word spans"))
START, END = "<!-- LEADERBOARD:START -->", "<!-- LEADERBOARD:END -->"
N_BOOT = 10000


def _load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_runs():
    """{(lang, split): results} for the MIRACL files that exist."""
    runs = {}
    for lang in LANGS:
        for split, suffix in SPLITS:
            r = _load(f"miracl_{lang}{suffix}.json")
            if r:
                runs[(lang, split)] = r
    return runs


def sig(run, a, b, metric="ndcg10"):
    qa = {q["qid"]: q[metric] for q in run["systems"][a]["queries"]}
    qb = {q["qid"]: q[metric] for q in run["systems"][b]["queries"]}
    keys = sorted(set(qa) & set(qb))
    return paired([qa[k] for k in keys], [qb[k] for k in keys], n_boot=N_BOOT)


def fmt_p(p):
    # With 10,000 sign flips the smallest possible p is 1/10001: report it as a bound, not as "< 0.0001".
    return "p≤0.0001" if p <= 1 / (N_BOOT + 1) + 1e-12 else f"p={p:.3g}"


def fmt_diff(r, bold=True):
    lo, hi = r["ci95"]
    mark = "**" if bold and (lo > 0 or hi < 0) else ""
    return f"{mark}{r['mean_diff']:+.3f}{mark} [{lo:+.3f}, {hi:+.3f}] {fmt_p(r['p_value'])}"


def _names(law, runs):
    names = []
    for src in [law, *runs.values()]:
        if src:
            for n in src["systems"]:
                if n not in names:
                    names.append(n)
    return names


def _table(names, cols):
    """cols: (header, getter(name) -> float|None, higher_is_better, fmt). Best value per column in bold."""
    lines = ["| system | " + " | ".join(c[0] for c in cols) + " |", "|---|" + "---|" * len(cols)]
    best = {}
    for i, (_, get, hib, _) in enumerate(cols):
        vals = [v for v in (get(n) for n in names) if v is not None]
        if vals:
            best[i] = max(vals) if hib else min(vals)
    for n in names:
        cells = []
        for i, (_, get, _, fmt) in enumerate(cols):
            v = get(n)
            if v is None:
                cells.append("n/a")
            else:
                s = fmt.format(v)
                cells.append(f"**{s}**" if i in best and abs(v - best[i]) < 1e-12 else s)
        lines.append(f"| `{n}` | " + " | ".join(cells) + " |")
    return lines


def _bucket(src, n, key, bucket="all"):
    return src["systems"].get(n, {}).get("buckets", {}).get(bucket, {}).get(key) if src else None


def build() -> str:
    law = _load("law_substring.json")
    runs = load_runs()
    names = _names(law, runs)
    out = []

    cols = []
    if law:
        cols.append(("Law substring recall", lambda n: _bucket(law, n, "recall"), True, "{:.1%}"))
    for lang in LANGS:
        for split, _ in SPLITS:
            if (lang, split) in runs:
                cols.append((f"MIRACL {lang} {split}", lambda n, r=runs[(lang, split)]: _bucket(r, n, "ndcg10"),
                             True, "{:.3f}"))
    if ("zh", "dev") in runs:
        cols.append(("zh dev p50 ms", lambda n: _bucket(runs[("zh", "dev")], n, "p50_ms"), False, "{:.2f}"))
    out += ["MIRACL columns are nDCG@10. **dev** = the MIRACL dev queries the benchmark was developed on "
            "(`app_bigram_first` was chosen after looking at them); **train** = MIRACL train queries, held out: "
            "never used to choose or tune a system. Absolute values are not comparable across splits (different "
            "queries and a different 100,000-passage sample); compare systems within a column. Best value per "
            "column in bold. n/a = not run: jieba segments Chinese only; `jieba_big` uses jieba's Traditional "
            "Chinese dictionary and runs on the law task only; systems added after the dev run have no dev numbers; "
            "`fts5_cjk_qfirst`/`_qedge` change only fts5_cjk's ranking query, so their substring results are fts5_cjk's. "
            "Latency is from one run (see Limits).", "", *_table(names, cols)]

    if law:
        md_n = {b: sum(1 for q in next(iter(law["systems"].values()))["queries"] if q["bucket"] == b)
                for b, _ in LAW_BUCKETS}
        qs = next(iter(law["systems"].values()))["queries"]
        short = sum(1 for q in qs if len(q["query"]) <= 2)
        lcols = [(f"{label} (n={md_n[b]})", lambda n, b=b: _bucket(law, n, "recall", b), True, "{:.1%}")
                 for b, label in LAW_BUCKETS]
        lcols.append((f"all (n={len(qs)})", lambda n: _bucket(law, n, "recall"), True, "{:.1%}"))
        out += ["", "Law substring recall by query type. The overall figure depends on this mix: "
                f"{short} of the {len(qs)} queries ({short / len(qs):.1%}) are one or two characters long.", "",
                *_table([n for n in names if n in law["systems"]], lcols)]

    for split, _ in SPLITS:
        langs = [lang for lang in LANGS if (lang, split) in runs]
        if not langs:
            continue
        out += ["", f"Paired difference in nDCG@10 against `{BASELINE}`, MIRACL **{split}** "
                "(95% bootstrap CI, randomization p):", "", "| system | " + " | ".join(langs) + " |",
                "|---|" + "---|" * len(langs)]
        for n in names:
            if n == BASELINE or n in SAME_RANKING_AS:
                continue
            cells = []
            for lang in langs:
                run = runs[(lang, split)]
                if n not in run["systems"] or BASELINE not in run["systems"]:
                    cells.append("n/a")
                else:
                    cells.append(fmt_diff(sig(run, n, BASELINE)))
            if any(c != "n/a" for c in cells):
                out.append(f"| `{n}` | " + " | ".join(cells) + " |")
    if runs:
        out += ["", "Bold = the 95% CI excludes zero (no multiple-comparison correction; see Limits). "
                + "; ".join(f"`{a}` ranks exactly like `{b}` (same ranking path) and is not repeated"
                            for a, b in SAME_RANKING_AS.items()) + "."]

    size_srcs = [("law", law)] + [(f"{lang} train", runs.get((lang, "train"))) for lang in LANGS]
    size_srcs = [(label, s) for label, s in size_srcs
                 if s and s["metadata"].get("raw_table_bytes")
                 and all("index_bytes_contentless" in v for v in s["systems"].values())]
    if size_srcs:
        out += ["", "Index size in MB (10^6 bytes) after VACUUM: **index only** (FTS5 `content=''`) / **index + one "
                "raw copy** of the original text / **default** (the FTS5 table with its stored copy of what the "
                "system indexes: transformed text for app-level systems, original text otherwise; the measure "
                "used before 2026-11). Only the first two compare like with like.", "",
                "| system | " + " | ".join(label for label, _ in size_srcs) + " |", "|---|" + "---|" * len(size_srcs)]
        for n in names:
            cells = []
            for _, s in size_srcs:
                v = s["systems"].get(n)
                if not v:
                    cells.append("n/a")
                    continue
                raw = s["metadata"]["raw_table_bytes"]
                cl = v["index_bytes_contentless"]
                cells.append(f"{cl / 1e6:.1f} / {(cl + raw) / 1e6:.1f} / {v['index_bytes'] / 1e6:.1f}")
            out.append(f"| `{n}` | " + " | ".join(cells) + " |")

    env = []
    for label, src in [("law", law), *[(f"MIRACL {k[0]} {k[1]}", v) for k, v in runs.items()]]:
        if src:
            m = src["metadata"]
            tv = m.get("tool_versions") or {}
            extra = f", Node {tv['node']} (ICU {tv['icu']})" if tv.get("node") else ""
            env.append(f"{label}: SQLite {m.get('sqlite_version')}, Python {m.get('python_version')}{extra}, "
                       f"{m.get('platform', '?')}")
    out += ["", "Run environments: " + "; ".join(env) + "."]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-readme", action="store_true")
    args = ap.parse_args(argv)
    md = build()
    if not args.update_readme:
        print(md)
        return
    with open("README.md", encoding="utf-8") as fh:
        readme = fh.read()
    if START not in readme:
        raise SystemExit(f"README.md has no {START} marker")
    readme = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: START + "\n" + md + "\n" + END,
                    readme, flags=re.S)
    with open("README.md", "w", encoding="utf-8") as fh:
        fh.write(readme)
    print("README.md leaderboard updated")


if __name__ == "__main__":
    main()
