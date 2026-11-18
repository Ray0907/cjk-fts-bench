"""Run `bench.run miracl` in resumable steps, for shells that kill every process after a few minutes.

The MIRACL train results in results/miracl_*_train.json were produced with this driver in a Linux VM whose
tool calls end after 180 s. It runs exactly the steps of `bench.run miracl`, split across calls:

  prep   : bench.data_miracl.load(...) once -> pickle cache; also measures raw_table_bytes
  build  : run.build_index(system, texts, dir) and run.contentless_index_bytes(...) -> {system}.db, build.json
  query  : reopen the index and evaluate queries in order with run.timed_search and the same row code as
           run.task_miracl, until --budget seconds are used; rows are appended to rows.jsonl (resumable)
  merge  : write a results JSON in bench.run's format (run.aggregate, run.metadata)
  status : progress per system

Ranking metrics are deterministic, so they equal a single `bench.run` (checked per query on ko train).
Latency is not comparable with a single run: the index is reopened between chunks and other work may share
the machine.

  python audit/chunk_run.py prep  --data-dir data/miracl --lang ko --split train --work /tmp/w
  python audit/chunk_run.py build --lang ko --system app_bigram --work /tmp/w
  python audit/chunk_run.py query --lang ko --system app_bigram --work /tmp/w --budget 140
  python audit/chunk_run.py merge --lang ko --work /tmp/w --out results/miracl_ko_train.json
"""
import argparse
import json
import os
import pickle
import sqlite3
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from bench import data_miracl, metrics, run  # noqa: E402
from bench.systems import SYSTEMS  # noqa: E402


def paths(a):
    return (os.path.join(a.work, f"sample_{a.lang}_{a.split}.pkl"),
            os.path.join(a.work, f"sample_{a.lang}_{a.split}.json"))


def sysdir(a, name):
    d = os.path.join(a.work, f"{a.lang}_{a.split}", name)
    os.makedirs(d, exist_ok=True)
    return d


def load(a):
    with open(paths(a)[0], "rb") as fh:
        return pickle.load(fh)


def cmd_prep(a):
    os.makedirs(a.work, exist_ok=True)
    t0 = time.time()
    d = data_miracl.load(a.data_dir, a.lang, a.split, a.max_docs)
    with open(paths(a)[0], "wb") as fh:
        pickle.dump(d, fh, protocol=pickle.HIGHEST_PROTOCOL)
    judged = {doc for q in d["qrels"].values() for doc in q}
    with tempfile.TemporaryDirectory(dir=a.work) as td:
        raw = run.raw_table_bytes(d["texts"], td)
    info = {"lang": a.lang, "split": a.split, "max_docs": a.max_docs, "corpus_size": len(d["texts"]),
            "n_queries": len(d["queries"]), "judged_passages_in_qrels": len(judged),
            "judged_passages_retained": len(judged & set(d["docids"])), "raw_table_bytes": raw,
            "data_dir": a.data_dir, "load_seconds": time.time() - t0}
    with open(paths(a)[1], "w") as fh:
        json.dump(info, fh, indent=1)
    print(json.dumps(info))


def cmd_build(a):
    d = load(a)
    s = SYSTEMS[a.system]
    sd = sysdir(a, a.system)
    for f in os.listdir(sd):
        os.remove(os.path.join(sd, f))
    ok, why = s.available()
    if not ok:
        json.dump({"skipped": why}, open(os.path.join(sd, "build.json"), "w"))
        print(f"[skip] {a.system}: {why}")
        return
    conn, build, size = run.build_index(s, d["texts"], sd)
    conn.close()
    size_cl = run.contentless_index_bytes(s, d["texts"], sd)
    json.dump({"build_seconds": build, "index_bytes": size, "index_bytes_contentless": size_cl},
              open(os.path.join(sd, "build.json"), "w"))
    print(f"{a.lang} {a.split} {a.system} build {build:.1f}s index {size / 1e6:.1f} MB, contentless {size_cl / 1e6:.1f} MB")


def cmd_query(a):
    d = load(a)
    s = SYSTEMS[a.system]
    sd = sysdir(a, a.system)
    rows_path = os.path.join(sd, "rows.jsonl")
    done = 0
    if os.path.exists(rows_path):
        raw = open(rows_path, "rb").read()
        if raw and not raw.endswith(b"\n"):  # killed mid-write: drop the partial row
            raw = raw[: raw.rfind(b"\n") + 1]
            open(rows_path, "wb").write(raw)
        lines = raw.decode("utf-8").splitlines()
        for i, line in enumerate(lines):
            assert json.loads(line)["qid"] == d["queries"][i][0]
        done = len(lines)
    qs = d["queries"]
    if done >= len(qs):
        print(f"{a.system}: done {done}/{len(qs)}")
        return
    conn = sqlite3.connect(os.path.join(sd, f"{s.name}.db"))
    conn.execute("ATTACH DATABASE ? AS raw", (os.path.join(sd, f"{s.name}_raw.db"),))
    s.setup(conn)
    docids, t0, n = d["docids"], time.time(), 0
    with open(rows_path, "a", encoding="utf-8") as out:
        for qid, text in qs[done:]:
            # same as run.task_miracl's evaluate()
            res, ms, err = run.timed_search(s, conn, text, 100, mode="rank")
            ranked = [docids[r] for r in res if 0 <= r < len(docids)]
            qr = d["qrels"][qid]
            row = {"query": text, "qid": qid, "bucket": "miracl", "g": sum(1 for r in qr.values() if r > 0),
                   "s": len(res), "ndcg10": metrics.ndcg_at_k(ranked, qr, 10),
                   "recall100": metrics.recall_at_k(ranked, qr, 100), "latency_ms": ms}
            if err:
                row["error"] = err
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            if time.time() - t0 > a.budget:
                break
    conn.close()
    print(f"{a.system}: {done + n}/{len(qs)}")


def names(a):
    return run.pick_systems(a.systems, SYSTEMS, lang=a.lang)


def cmd_status(a):
    info = json.load(open(paths(a)[1]))
    for name in names(a):
        sd = os.path.join(a.work, f"{a.lang}_{a.split}", name)
        rp = os.path.join(sd, "rows.jsonl")
        n = sum(1 for _ in open(rp)) if os.path.exists(rp) else 0
        print(f"{name:18s} built={os.path.exists(os.path.join(sd, 'build.json'))} rows={n}/{info['n_queries']}")


def cmd_merge(a):
    info = json.load(open(paths(a)[1]))
    result, skipped = {}, {}
    for name in names(a):
        sd = os.path.join(a.work, f"{a.lang}_{a.split}", name)
        bj = json.load(open(os.path.join(sd, "build.json")))
        if "skipped" in bj:
            skipped[name] = bj["skipped"]
            continue
        rows = [json.loads(line) for line in open(os.path.join(sd, "rows.jsonl"), encoding="utf-8")]
        assert len(rows) == info["n_queries"], (name, len(rows))
        result[name] = {"description": SYSTEMS[name].description, "build_seconds": bj["build_seconds"],
                        "index_bytes": bj["index_bytes"], "index_bytes_contentless": bj["index_bytes_contentless"],
                        "buckets": run.aggregate(rows, "miracl"), "queries": rows}
    md = run.metadata("miracl", info["corpus_size"], {
        "lang": a.lang, "split": a.split, "max_docs": info["max_docs"], "n_queries": info["n_queries"],
        "data_dir": info["data_dir"], "raw_table_bytes": info["raw_table_bytes"],
        "judged_passages_retained": info["judged_passages_retained"],
        "driver": "audit/chunk_run.py (bench.run steps split across calls; index reopened between query chunks)"})
    out = a.out or os.path.join(a.work, f"miracl_{a.lang}_{a.split}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"metadata": md, "systems": result, "skipped": skipped}, fh, ensure_ascii=False, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "build", "query", "merge", "status"])
    ap.add_argument("--lang", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--data-dir", default="data/miracl")
    ap.add_argument("--work", default=os.environ.get("CJK_WORK", "work"))
    ap.add_argument("--system")
    ap.add_argument("--systems", default="all", help="for status/merge: 'all' or comma-separated names")
    ap.add_argument("--max-docs", type=int, default=100000)
    ap.add_argument("--budget", type=float, default=140)
    ap.add_argument("--out")
    a = ap.parse_args()
    globals()["cmd_" + a.cmd](a)
