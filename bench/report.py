"""results JSON -> markdown.  python -m bench.report results/law_substring.json > results/law_substring.md"""
import json
import sys


def _pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def _prec(b):
    """Precision cell: mean over the queries that returned something, with their count when known."""
    if "precision_n" not in b:
        return _pct(b["precision"])
    return f"{_pct(b['precision'])} (n={b['precision_n']})"


def render(res):
    md, systems = res["metadata"], res["systems"]
    task = md["task"]
    out = [f"# {task}", ""]
    out.append(f"- corpus: {md['corpus_size']} docs, queries: {md.get('n_queries')}, seed {md['seed']}")
    out.append(f"- SQLite {md['sqlite_version']}, Python {md['python_version']}, run at {md['timestamp']}")
    for k in ("law_commit",):
        if md.get(k):
            out.append(f"- {k}: {md[k]}")
    for v in md.get("ext_versions", []):
        out.append(f"- {v}")
    if md.get("tool_versions"):
        out.append("- " + ", ".join(f"{k} {v}" for k, v in md["tool_versions"].items()))
    if md.get("limit_docs") or md.get("limit_queries"):
        out.append(f"- WARNING: smoke run (limit_docs={md.get('limit_docs')}, limit_queries={md.get('limit_queries')})")
    out.append("")
    if not systems:
        out.append("No systems ran.")
    else:
        buckets = [b for b in next(iter(systems.values()))["buckets"] if b != "all"]
        out += ["## Quality", ""]
        if task == "law_substring":
            hdr = ["system"] + [f"{b} recall / zero" for b in buckets] + ["overall recall", "overall precision"]
            out += ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
            for n, s in systems.items():
                cells = [n] + [f"{_pct(s['buckets'][b]['recall'])} / {_pct(s['buckets'][b]['zero_result_rate'])}"
                               for b in buckets]
                a = s["buckets"]["all"]
                cells += [_pct(a["recall"]), _prec(a)]
                out.append("| " + " | ".join(cells) + " |")
        else:
            hdr = ["system", "nDCG@10", "Recall@100"]
            out += ["| " + " | ".join(hdr) + " |", "|---|---|---|"]
            for n, s in systems.items():
                a = s["buckets"]["all"]
                out.append(f"| {n} | {a['ndcg10']:.4f} | {a['recall100']:.4f} |")
        out += ["", "Cells are macro means per bucket; 'zero' = share of queries with matches in ground truth "
                "but none returned. Precision is undefined for a query that returns nothing, so it is the mean over "
                "the n queries that returned at least one article." if task == "law_substring" else "", "",
                "## Cost", "",
                "| system | build s | index MB | p50 ms | p95 ms | search errors |", "|---|---|---|---|---|---|"]
        for n, s in systems.items():
            a = s["buckets"]["all"]
            out.append(f"| {n} | {s['build_seconds']:.2f} | {s['index_bytes'] / 1e6:.1f} | "
                       f"{a['p50_ms']:.2f} | {a['p95_ms']:.2f} | {a['errors']} |")
        out += ["", "## Failure examples (3 worst queries per system)", ""]
        for n, s in systems.items():
            key = "recall" if task == "law_substring" else "ndcg10"
            worst = sorted(s["queries"], key=lambda r: (r[key], r["query"]))[:3]
            out.append(f"**{n}**")
            out.append("")
            for r in worst:
                if task == "law_substring":
                    p = "n/a" if r["precision"] is None else f"{r['precision']:.3f}"
                    out.append(f"- `{r['query']}` ({r['bucket']}): |G|={r['g']} |S|={r['s']} "
                               f"recall={r['recall']:.3f} precision={p}")
                else:
                    out.append(f"- `{r['query']}`: relevant={r['g']} returned={r['s']} nDCG@10={r['ndcg10']:.3f}")
            out.append("")
    if res.get("skipped"):
        out += ["## Skipped systems", ""] + [f"- {n}: {why}" for n, why in res["skipped"].items()] + [""]
    return "\n".join(out)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    print(render(json.load(open(argv[0], encoding="utf-8"))))


if __name__ == "__main__":
    main()
