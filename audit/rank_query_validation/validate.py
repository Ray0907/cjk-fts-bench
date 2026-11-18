"""Top-100 identity check: MATCH cjk_rank_query(strip_punct(q), mode) from the patched fts5-cjk vs the
benchmark variant fts5_cjk_qfirst / fts5_cjk_qedge (Python rule) on the same fts5_cjk index.
Resumable: python validate.py build LANG | run LANG MODE [budget_s] | summary
Index built by the benchmark's run.build_index with the pinned fts5-cjk 79c52da (ext/build/fts5_cjk.so).

As run in the audit VM: REPO is a scratch copy of the bench with the variant systems (audit/qfirst/
systems_with_variants.py), the samples come from audit/original/chunk_run.py's prep step (~/cjkwork), and
~/rp/fts5_cjk_rq.so is fts5-cjk's cjk.c at commit ec39d0c built with gcc -O2. Adjust the paths to rerun."""
import hashlib, json, os, pickle, sqlite3, sys, time
REPO = os.path.expanduser("~/qfrun"); sys.path.insert(0, REPO); os.chdir(REPO)
from bench import run  # noqa: E402
from bench.systems import SYSTEMS, strip_punct  # noqa: E402
RP = os.path.expanduser("~/rp")
SO = os.path.join(RP, "fts5_cjk_rq.so")
cmd, args = sys.argv[1], sys.argv[2:]

def sample(lang):
    return pickle.load(open(os.path.expanduser(f"~/cjkwork/sample_{lang}_train.pkl"), "rb"))

if cmd == "build":
    lang = args[0]; d = sample(lang); wd = os.path.join(RP, lang); os.makedirs(wd, exist_ok=True)
    conn, b, size = run.build_index(SYSTEMS["fts5_cjk"], d["texts"], wd); conn.close()
    md5 = hashlib.md5(open(os.path.join(wd, "fts5_cjk.db"), "rb").read()).hexdigest()
    json.dump({"index_bytes": size, "md5": md5}, open(os.path.join(wd, "build.json"), "w"))
    print(lang, size, md5)
elif cmd == "run":
    lang, mode = args[0], args[1]; budget = float(args[2]) if len(args) > 2 else 140
    t0 = time.time(); d = sample(lang); wd = os.path.join(RP, lang); dbp = os.path.join(wd, "fts5_cjk.db")
    out = os.path.join(wd, f"val_{mode}.jsonl")
    done = sum(1 for _ in open(out)) if os.path.exists(out) else 0
    v = SYSTEMS["fts5_cjk_qfirst" if mode == "first" else "fts5_cjk_qedge"]
    A = sqlite3.connect(dbp); v.setup(A)
    B = sqlite3.connect(dbp); B.enable_load_extension(True); B.load_extension(SO, entrypoint="sqlite3_cjk_init")
    n = 0
    with open(out, "a") as fh:
        for i, (qid, q) in enumerate(d["queries"]):
            if i < done:
                continue
            if time.time() - t0 > budget:
                break
            ra = v.rank(A, "docs", q, 100)
            toks = v.query_tokens(A, q)
            expr = B.execute("SELECT cjk_rank_query(?, ?)", (strip_punct(q), mode)).fetchone()[0]
            terms = [t[1:-1].replace('""', '"') for t in expr.split(" OR ")] if expr != '""' else []
            rb = [r[0] for r in B.execute("SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 100", (expr,))]
            fh.write(json.dumps({"i": i, "qid": qid, "same_top100": ra == rb, "same_terms": sorted(terms) == sorted(toks),
                                 "n_terms": len(terms), "n_bench": len(toks),
                                 **({} if ra == rb else {"q": q, "bench": toks, "c": terms, "a10": ra[:10], "b10": rb[:10]})},
                                ensure_ascii=False) + "\n")
            n += 1
    print(lang, mode, "done", done + n, "/", len(d["queries"]))
elif cmd == "summary":
    res = {}
    for lang in ("zh", "ja", "ko"):
        for mode in ("first", "edge"):
            p = os.path.join(RP, lang, f"val_{mode}.jsonl")
            if not os.path.exists(p):
                continue
            rows = [json.loads(l) for l in open(p)]
            res[f"{lang}_{mode}"] = {"n": len(rows), "identical_top100": sum(r["same_top100"] for r in rows),
                                     "identical_term_set": sum(r["same_terms"] for r in rows),
                                     "max_terms": max(r["n_terms"] for r in rows),
                                     "different": [{k: r[k] for k in ("qid", "q", "bench", "c", "a10", "b10") if k in r}
                                                   for r in rows if not r["same_top100"]][:20]}
    b = {l: json.load(open(os.path.join(RP, l, "build.json"))) for l in ("zh", "ja", "ko") if os.path.exists(os.path.join(RP, l, "build.json"))}
    json.dump({"builds": b, "results": res}, open(os.path.join(RP, "validation_summary.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "different"} for k, v in res.items()}, indent=1), b)
