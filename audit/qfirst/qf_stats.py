"""Paired statistics for the qfirst experiment (pre-registered decision rule).

python qf_stats.py LANG [METRIC...] -> qf_stats_LANG.json
NEW  = this run (qfirst_miracl_LANG_train.json: fts5_cjk, fts5_cjk_qfirst, fts5_cjk_qedge, app_bigram_first re-run)
OLD  = earlier held-out run (~/cjkwork/miracl_LANG_train.json, same seeded sample), for app_bigram_edge and the leaders.
Paired bootstrap: 100k resamples of queries, numpy default_rng(20261118); 95% and 90% percentile intervals.
Randomisation p: 100k paired sign flips, two-sided, (ext+1)/(B+1). Paired-t 90% CI also reported.
"""
import json, os, sys
from math import sqrt
import numpy as np

lang = sys.argv[1]
metrics = sys.argv[2:] or ["ndcg10", "recall100"]
NEW = json.load(open(os.path.expanduser(f"~/qf/qfirst_miracl_{lang}_train.json"), encoding="utf-8"))
OLD = json.load(open(os.path.expanduser(f"~/cjkwork/miracl_{lang}_train.json"), encoding="utf-8"))
TOP = {"zh": "better_trigram", "ja": "icu_segmenter", "ko": "app_bigram_first"}[lang]


def rows(res, name):
    return {q["qid"]: q for q in res["systems"][name]["queries"]}


S = {n: rows(NEW, n) for n in NEW["systems"]}
O = {n: rows(OLD, n) for n in OLD["systems"]}
qids = [q["qid"] for q in NEW["systems"]["fts5_cjk"]["queries"]]
oq = [q["qid"] for q in OLD["systems"]["fts5_cjk"]["queries"]]
assert qids == oq, "query ids/order differ from the earlier run"

# reproducibility: same-run re-runs vs stored per-query results
repro = {}
for n in ["fts5_cjk", "app_bigram_first"]:
    for m in ["ndcg10", "recall100"]:
        diff = [abs(S[n][q][m] - O[n][q][m]) for q in qids]
        repro[f"{n} {m}"] = {"max_abs_diff": max(diff), "n_diff": sum(d > 1e-12 for d in diff)}

REF = {"fts5_cjk": S["fts5_cjk"], "app_bigram_first": O["app_bigram_first"], "app_bigram_edge": O["app_bigram_edge"],
       "app_bigram": O["app_bigram"], f"top:{TOP}": O[TOP]}


def paired(a, b, m, B=100000, seed=20261118):
    rng = np.random.default_rng(seed)
    d = np.array([a[q][m] - b[q][m] for q in qids])
    n = len(d)
    bm = np.empty(B)
    for i in range(0, B, 5000):
        idx = rng.integers(0, n, (5000, n), dtype=np.int32)
        bm[i:i + 5000] = d[idx].mean(1)
    ext = 0
    for i in range(0, B, 5000):
        s = rng.integers(0, 2, (5000, n), dtype=np.int8) * 2 - 1
        ext += int((np.abs((s * d).mean(1)) >= abs(d.mean()) - 1e-12).sum())
    se = d.std(ddof=1) / sqrt(n)
    return {"n": n, "mean": float(d.mean()), "ci95": [float(x) for x in np.percentile(bm, [2.5, 97.5])],
            "ci90": [float(x) for x in np.percentile(bm, [5, 95])],
            "ci90_t": [float(d.mean() - 1.645 * se), float(d.mean() + 1.645 * se)], "p": (ext + 1) / (B + 1),
            "wins": int((d > 1e-12).sum()), "ties": int((np.abs(d) <= 1e-12).sum()), "losses": int((d < -1e-12).sum())}


out_path = os.path.expanduser(f"~/qf/qf_stats_{lang}.json")
out = json.load(open(out_path)) if os.path.exists(out_path) else {}
out.update({"lang": lang, "top": TOP, "n_queries": len(qids), "reproducibility": repro})
mean = lambda R, m: sum(R[q][m] for q in qids) / len(qids)
out["means"] = {n: {m: mean(R, m) for m in ["ndcg10", "recall100"]} for n, R in
                {**{k: v for k, v in S.items()}, "app_bigram_edge (stored)": O["app_bigram_edge"],
                 "app_bigram (stored)": O["app_bigram"], f"{TOP} (stored)": O[TOP],
                 "fts5_cjk (stored)": O["fts5_cjk"], "app_bigram_first (stored)": O["app_bigram_first"]}.items()}
lat = {}
for n in NEW["systems"]:
    a = NEW["systems"][n]["buckets"]["all"]
    lat[n] = {"p50_ms": a["p50_ms"], "p95_ms": a["p95_ms"]}
base = lat["fts5_cjk"]
out["latency_same_run"] = {n: {**v, "p50_ratio_vs_fts5_cjk": v["p50_ms"] / base["p50_ms"],
                               "p95_ratio_vs_fts5_cjk": v["p95_ms"] / base["p95_ms"]} for n, v in lat.items()}
out["index_bytes"] = {n: NEW["systems"][n]["index_bytes"] for n in NEW["systems"]}
out.setdefault("pairs", {})
for v in ["fts5_cjk_qfirst", "fts5_cjk_qedge"]:
    for r, R in REF.items():
        for m in metrics:
            out["pairs"][f"{v} - {r} [{m}]"] = paired(S[v], R, m)
    print(lang, v, "done", flush=True)
# decision rule (pre-registered)
dec = {}
for v in ["fts5_cjk_qfirst", "fts5_cjk_qedge"]:
    a = out["pairs"].get(f"{v} - fts5_cjk [ndcg10]"); b = out["pairs"].get(f"{v} - app_bigram_first [ndcg10]")
    if a and b:
        c1 = a["mean"] > 0 and a["ci95"][0] > 0
        c2 = b["ci90"][0] >= -0.015 and b["ci90"][1] <= 0.015
        dec[v] = {"improves_over_fts5_cjk": c1, "equivalent_to_app_bigram_first_within_0.015": c2,
                  "verdict": "SUPPORTED" if c1 and c2 else ("PARTIALLY" if c1 else "NOT SUPPORTED")}
out["decision"] = dec
json.dump(out, open(out_path, "w"), indent=1)
print(json.dumps(dec), json.dumps(repro))
