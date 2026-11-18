"""Benchmark runner.

  python -m bench.run law_substring --systems all --out results/law_substring.json
  python -m bench.run miracl --data-dir PATH --lang zh --max-docs 100000 --out results/miracl_zh.json

Systems come from `bench.systems.SYSTEMS` (override module with env BENCH_SYSTEMS_MODULE, used by tests).

Harness layout: the FTS table lives in the main temp db file; the raw table `{table}_raw` (original
text) lives in an ATTACHed second temp db file (schema "raw"), so the reported index size (size of the main
file after VACUUM) contains only what the system adds, not the raw copy. Unqualified `{table}_raw` still
resolves for systems that use it. Build time = prep_doc + FTS insert + commit (raw insert is untimed).
Queries with empty ground truth (possible with --limit-docs) are dropped for law_substring.
"""
import argparse
import datetime
import importlib
import json
import os
import platform
import sqlite3
import sys
import tempfile
import time
from collections import defaultdict

from . import data_law, metrics, queries as queries_mod
from .systems import take_errors

TABLE = "docs"
SEED = 42


def get_systems():
    mod = importlib.import_module(os.environ.get("BENCH_SYSTEMS_MODULE", "bench.systems"))
    return mod.SYSTEMS


def like_escape(q):
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def ground_truth(texts, qs):
    """{query: set(rowid)} via LIKE '%q%' ESCAPE '\\' on a plain raw table (in memory)."""
    conn = sqlite3.connect(":memory:")
    conn.execute(f"CREATE TABLE {TABLE}_raw(rowid INTEGER PRIMARY KEY, text TEXT)")
    conn.executemany(f"INSERT INTO {TABLE}_raw(rowid, text) VALUES (?,?)", enumerate(texts))
    out = {}
    for q in qs:
        out[q] = {r[0] for r in conn.execute(
            f"SELECT rowid FROM {TABLE}_raw WHERE text LIKE ? ESCAPE '\\'", ("%" + like_escape(q) + "%",))}
    conn.close()
    return out


def build_index(system, texts, tmpdir):
    """Returns (conn, build_seconds, index_bytes)."""
    path = os.path.join(tmpdir, f"{system.name}.db")
    conn = sqlite3.connect(path)
    conn.execute("ATTACH DATABASE ? AS raw", (os.path.join(tmpdir, f"{system.name}_raw.db"),))
    system.setup(conn)
    conn.execute(f"CREATE TABLE raw.{TABLE}_raw(rowid INTEGER PRIMARY KEY, text TEXT)")
    system.create_table(conn, TABLE)
    with conn:
        conn.executemany(f"INSERT INTO raw.{TABLE}_raw(rowid, text) VALUES (?,?)", enumerate(texts))
    t0 = time.perf_counter()
    with conn:
        conn.executemany(f"INSERT INTO {TABLE}(rowid, text) VALUES (?,?)",
                         ((i, system.prep_doc(t)) for i, t in enumerate(texts)))
    build = time.perf_counter() - t0
    conn.execute("VACUUM")
    conn.commit()
    size = os.path.getsize(path)
    return conn, build, size


def aggregate(rows, kind):
    """rows: per-query dicts. Macro means per bucket + 'all'."""
    by = defaultdict(list)
    for r in rows:
        by[r["bucket"]].append(r)
        by["all"].append(r)
    out = {}
    for b, rs in by.items():
        lat = [r["latency_ms"] for r in rs]
        d = {"n": len(rs), "p50_ms": metrics.percentile(lat, 50), "p95_ms": metrics.percentile(lat, 95),
             "errors": sum(1 for r in rs if r.get("error"))}
        mean = lambda key: sum(r[key] for r in rs) / len(rs)
        if kind == "substring":
            prec = [r["precision"] for r in rs if r["precision"] is not None]
            d.update(recall=mean("recall"), precision=sum(prec) / len(prec) if prec else None,
                     precision_n=len(prec),  # queries that returned something; precision is their mean
                     zero_result_rate=sum(1 for r in rs if r["zero_result"]) / len(rs))
        else:
            d.update(ndcg10=mean("ndcg10"), recall100=mean("recall100"))
        out[b] = d
    return out


def timed_search(system, conn, q, k, mode="search"):
    """Returns (rowids, ms, error). error joins exceptions that escaped the system (the contract says
    never raise) and SQLite errors the system recorded with bench.systems.record_error; None if none."""
    take_errors()
    t0 = time.perf_counter()
    errs = []
    try:
        fn = system.rank if mode == "rank" else system.search
        res = list(fn(conn, TABLE, q, k))
    except Exception as e:  # record instead of aborting the run
        res = []
        errs.append(f"{type(e).__name__}: {e}")
    ms = (time.perf_counter() - t0) * 1000
    errs = take_errors() + errs
    return res, ms, "; ".join(errs) if errs else None


def run_systems(names, texts, evaluate, kind, systems):
    result, skipped = {}, {}
    for name in names:
        s = systems[name]
        ok, why = s.available()
        if not ok:
            skipped[name] = why
            print(f"[skip] {name}: {why}", file=sys.stderr)
            continue
        print(f"[run] {name} ...", file=sys.stderr)
        with tempfile.TemporaryDirectory(prefix="cjkbench_") as td:
            conn, build, size = build_index(s, texts, td)
            rows = evaluate(s, conn)
            conn.close()
        result[name] = {"description": s.description, "build_seconds": build, "index_bytes": size,
                        "buckets": aggregate(rows, kind), "queries": rows}
        a = result[name]["buckets"]["all"]
        print(f"      build {build:.2f}s size {size/1e6:.1f}MB " +
              " ".join(f"{k}={a[k]:.3f}" for k in a if k in ("recall", "precision", "ndcg10", "recall100")),
              file=sys.stderr)
    return result, skipped


def tool_versions():
    """Versions of the tools app-level systems depend on: jieba, and Node.js with its ICU and Unicode data
    (icu_segmenter's segmentation depends on ICU's dictionary, which changes between ICU releases)."""
    import json
    import shutil
    import subprocess
    v = {}
    try:
        import jieba
        v["jieba"] = jieba.__version__
    except Exception:  # noqa: BLE001
        pass
    node = shutil.which("node")
    if node:
        js = "JSON.stringify({node: process.version, icu: process.versions.icu, unicode: process.versions.unicode})"
        try:
            out = subprocess.run([node, "-p", js], capture_output=True, text=True, timeout=30, check=True)
            v.update(json.loads(out.stdout))
        except Exception:  # noqa: BLE001
            pass
    return v


def metadata(task, n_docs, extra):
    md = {"task": task, "sqlite_version": sqlite3.sqlite_version, "python_version": platform.python_version(),
          "platform": platform.platform(), "corpus_size": n_docs, "seed": SEED,
          "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
          "tool_versions": tool_versions()}
    vf = os.path.join(data_law.ROOT, "ext", "build", "VERSIONS.txt")
    if os.path.exists(vf):  # written by ext/build_ext.sh
        md["ext_versions"] = open(vf, encoding="utf-8").read().strip().splitlines()
    md.update(extra)
    return md


def pick_systems(arg, systems):
    if arg == "all":
        return list(systems)
    names = [n for n in arg.split(",") if n]
    bad = [n for n in names if n not in systems]
    if bad:
        raise SystemExit(f"unknown systems: {bad}; known: {list(systems)}")
    return names


def round_robin(qs, n):
    """Deterministic subset of n queries spread across buckets."""
    buckets = defaultdict(list)
    for q in qs:
        buckets[q["bucket"]].append(q)
    out, i = [], 0
    while len(out) < n and any(i < len(v) for v in buckets.values()):
        out += [v[i] for v in buckets.values() if i < len(v)]
        i += 1
    return out[:n]


def task_law(args, systems):
    texts = data_law.load_articles()
    if args.limit_docs:
        texts = texts[:args.limit_docs]
    qs = queries_mod.load_queries()
    gt = ground_truth(texts, sorted({q["query"] for q in qs}))
    dropped = sum(1 for q in qs if not gt[q["query"]])
    qs = [q for q in qs if gt[q["query"]]]
    if args.limit_queries:
        qs = round_robin(qs, args.limit_queries)

    def evaluate(s, conn):
        rows = []
        for q in qs:
            G = gt[q["query"]]
            res, ms, err = timed_search(s, conn, q["query"], None)
            m = metrics.substring_metrics(res, G)
            row = {"query": q["query"], "bucket": q["bucket"], "g": m["g"], "s": m["s"],
                   "recall": m["recall"], "precision": m["precision"], "zero_result": m["zero_result"],
                   "latency_ms": ms}
            if err:
                row["error"] = err
            rows.append(row)
        return rows

    names = pick_systems(args.systems, systems)
    result, skipped = run_systems(names, texts, evaluate, "substring", systems)
    md = metadata("law_substring", len(texts), {
        "law_source": data_law.REPO, "law_commit": data_law.commit_hash(), "n_queries": len(qs),
        "queries_dropped_empty_ground_truth": dropped,
        "limit_docs": args.limit_docs, "limit_queries": args.limit_queries})
    return {"metadata": md, "systems": result, "skipped": skipped}


def task_miracl(args, systems):
    from . import data_miracl
    d = data_miracl.load(args.data_dir, args.lang, args.split, args.max_docs)
    texts, docids = d["texts"], d["docids"]
    qs = d["queries"][:args.limit_queries] if args.limit_queries else d["queries"]

    def evaluate(s, conn):
        rows = []
        for qid, text in qs:
            res, ms, err = timed_search(s, conn, text, 100, mode="rank")
            ranked = [docids[r] for r in res if 0 <= r < len(docids)]
            qr = d["qrels"][qid]
            row = {"query": text, "qid": qid, "bucket": "miracl", "g": sum(1 for r in qr.values() if r > 0),
                   "s": len(res), "ndcg10": metrics.ndcg_at_k(ranked, qr, 10),
                   "recall100": metrics.recall_at_k(ranked, qr, 100), "latency_ms": ms}
            if err:
                row["error"] = err
            rows.append(row)
        return rows

    names = pick_systems(args.systems, systems)
    result, skipped = run_systems(names, texts, evaluate, "miracl", systems)
    md = metadata("miracl", len(texts), {"lang": args.lang, "split": args.split, "max_docs": args.max_docs,
                                         "n_queries": len(qs), "data_dir": args.data_dir})
    return {"metadata": md, "systems": result, "skipped": skipped}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bench.run")
    ap.add_argument("task", choices=["law_substring", "miracl"])
    ap.add_argument("--systems", default="all", help="'all' or comma-separated names")
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-dir")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--max-docs", type=int)
    ap.add_argument("--limit-queries", type=int)
    ap.add_argument("--limit-docs", type=int)
    args = ap.parse_args(argv)
    systems = get_systems()
    if args.task == "miracl":
        if not args.data_dir:
            ap.error("miracl requires --data-dir")
        res = task_miracl(args, systems)
    else:
        res = task_law(args, systems)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
