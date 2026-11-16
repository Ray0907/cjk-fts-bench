"""Build the leaderboard from results/*.json and (optionally) write it into README.md.

  python -m bench.leaderboard                 # print markdown
  python -m bench.leaderboard --update-readme # replace the block between the LEADERBOARD markers

Every number comes straight from the results files; nothing in the README table is typed by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import re

from .compare import paired

RESULTS = "results"
LANGS = ("zh", "ja", "ko")
BASELINE = "app_bigram"
START, END = "<!-- LEADERBOARD:START -->", "<!-- LEADERBOARD:END -->"


def _load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _sig(run, a, b, metric="ndcg10"):
    qa = {q["qid"]: q[metric] for q in run["systems"][a]["queries"]}
    qb = {q["qid"]: q[metric] for q in run["systems"][b]["queries"]}
    keys = sorted(set(qa) & set(qb))
    return paired([qa[k] for k in keys], [qb[k] for k in keys], n_boot=10000)


def build() -> str:
    law = _load("law_substring.json")
    runs = {lang: _load(f"miracl_{lang}.json") for lang in LANGS}
    runs = {k: v for k, v in runs.items() if v}
    names = []
    for src in [law, *runs.values()]:
        if src:
            for n in src["systems"]:
                if n not in names:
                    names.append(n)

    cols = []  # (header, getter(name) -> float|None, higher_is_better, fmt)
    if law:
        cols.append(("Law substring recall", lambda n: law["systems"].get(n, {}).get("buckets", {})
                     .get("all", {}).get("recall"), True, "{:.1%}"))
    for lang, run in runs.items():
        cols.append((f"MIRACL {lang} nDCG@10", lambda n, r=run: r["systems"].get(n, {}).get("buckets", {})
                     .get("all", {}).get("ndcg10"), True, "{:.3f}"))
    if "zh" in runs:
        z = runs["zh"]
        cols.append(("zh p50 ms", lambda n: z["systems"].get(n, {}).get("buckets", {}).get("all", {})
                     .get("p50_ms"), False, "{:.2f}"))
        cols.append(("zh index MB", lambda n: (z["systems"][n]["index_bytes"] / 1e6)
                     if n in z["systems"] else None, False, "{:.0f}"))

    lines = ["| system | " + " | ".join(c[0] for c in cols) + " |",
             "|---|" + "---|" * len(cols)]
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
    out = ["Best value per column in bold. n/a = not run (jieba segments Chinese only).", "", *lines]

    if runs:
        out += ["", f"Paired difference in nDCG@10 against `{BASELINE}` (95% bootstrap CI, randomization p):",
                "", "| system | " + " | ".join(runs) + " |", "|---|" + "---|" * len(runs)]
        for n in names:
            if n == BASELINE:
                continue
            cells = []
            for run in runs.values():
                if n not in run["systems"] or BASELINE not in run["systems"]:
                    cells.append("n/a")
                    continue
                r = _sig(run, n, BASELINE)
                lo, hi = r["ci95"]
                mark = "**" if (lo > 0 or hi < 0) else ""
                cells.append(f"{mark}{r['mean_diff']:+.3f}{mark} [{lo:+.3f}, {hi:+.3f}] p{'<0.0001' if r['p_value'] < 1.5e-4 else '=' + format(r['p_value'], '.3g')}")
            out.append(f"| `{n}` | " + " | ".join(cells) + " |")
        out += ["", "Bold = the 95% CI excludes zero (no multiple-comparison correction; see Limits)."]

    env = []
    for label, src in [("law", law), *[(f"MIRACL {k}", v) for k, v in runs.items()]]:
        if src:
            m = src["metadata"]
            env.append(f"{label}: SQLite {m.get('sqlite_version')}, Python {m.get('python_version')}, "
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
    readme = re.sub(re.escape(START) + r".*?" + re.escape(END), START + "\n" + md + "\n" + END,
                    readme, flags=re.S)
    with open("README.md", "w", encoding="utf-8") as fh:
        fh.write(readme)
    print("README.md leaderboard updated")


if __name__ == "__main__":
    main()
