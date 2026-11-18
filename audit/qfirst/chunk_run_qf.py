"""Chunked driver around the repo's own harness (bench.run / bench.data_miracl), for a shell that
kills every process after 180 s. It does exactly what `bench.run miracl` does, split into steps:

  prep   : data_miracl.load(...) once (repo loader, unchanged) -> pickle cache
  build  : run.build_index(system, texts, persistent_dir)       -> {sys}.db + {sys}_raw.db + build.json
  query  : reopen the db, evaluate queries in order with run.timed_search + the same row code as
           run.task_miracl.evaluate, until a time budget is used; append rows to rows.jsonl (resumable)
  merge  : write a results JSON in the same format as bench.run (metadata via run.metadata,
           buckets via run.aggregate)
  status : progress per system
Usage: CJK_REPO=~/qfrun CJK_WORK=~/qfwork QF_SYSTEMS="..." python chunk_run_qf.py <cmd> --lang zh --split train [--system NAME] [--budget 140]
"""
import argparse, json, os, pickle, sqlite3, sys, time

REPO = os.environ.get("CJK_REPO", os.path.expanduser("~/cjkrun"))
sys.path.insert(0, REPO)
os.chdir(REPO)
from bench import run, metrics, data_miracl  # noqa: E402
from bench.systems import SYSTEMS  # noqa: E402

DATA = os.environ.get("CJK_DATA", "data/miracl")  # was the VM path of the audit run; otherwise unmodified
WORK = os.path.expanduser(os.environ.get("CJK_WORK", "~/cjkwork"))


def cache_path(lang, split):
    return os.path.join(WORK, f"sample_{lang}_{split}.pkl")


def sysdir(lang, split, name):
    d = os.path.join(WORK, f"{lang}_{split}", name)
    os.makedirs(d, exist_ok=True)
    return d


def load_cache(lang, split):
    with open(cache_path(lang, split), "rb") as fh:
        return pickle.load(fh)


def cmd_prep(a):
    os.makedirs(WORK, exist_ok=True)
    t0 = time.time()
    d = data_miracl.load(DATA, a.lang, a.split, a.max_docs)
    with open(cache_path(a.lang, a.split), "wb") as fh:
        pickle.dump(d, fh, protocol=pickle.HIGHEST_PROTOCOL)
    judged = {doc for q in d["qrels"].values() for doc in q}
    kept = judged & set(d["docids"])
    info = {"lang": a.lang, "split": a.split, "max_docs": a.max_docs, "corpus_size": len(d["texts"]),
            "n_queries": len(d["queries"]), "judged_passages_in_qrels": len(judged),
            "judged_passages_retained": len(kept),
            "positive_judgements": sum(1 for q in d["qrels"].values() for r in q.values() if r > 0),
            "load_seconds": time.time() - t0}
    json.dump(info, open(os.path.join(WORK, f"sample_{a.lang}_{a.split}.json"), "w"), indent=1)
    print(json.dumps(info))


def cmd_build(a):
    d = load_cache(a.lang, a.split)
    s = SYSTEMS[a.system]
    ok, why = s.available()
    if not ok:
        print(f"[skip] {a.system}: {why}")
        json.dump({"skipped": why}, open(os.path.join(sysdir(a.lang, a.split, a.system), "build.json"), "w"))
        return
    sd = sysdir(a.lang, a.split, a.system)
    for f in os.listdir(sd):
        os.remove(os.path.join(sd, f))
    t0 = time.time()
    conn, build, size = run.build_index(s, d["texts"], sd)
    conn.close()
    json.dump({"build_seconds": build, "index_bytes": size, "wall": time.time() - t0},
              open(os.path.join(sd, "build.json"), "w"))
    print(f"{a.lang} {a.split} {a.system} build {build:.1f}s size {size/1e6:.1f}MB")


def cmd_query(a):
    d = load_cache(a.lang, a.split)
    s = SYSTEMS[a.system]
    sd = sysdir(a.lang, a.split, a.system)
    rows_path = os.path.join(sd, "rows.jsonl")
    done = 0
    if os.path.exists(rows_path):
        raw = open(rows_path, "rb").read()
        if raw and not raw.endswith(b"\n"):  # process killed mid-write: drop the partial row
            raw = raw[: raw.rfind(b"\n") + 1]
            open(rows_path, "wb").write(raw)
        lines = raw.decode("utf-8").splitlines()
        for i, l in enumerate(lines):
            assert json.loads(l)["qid"] == d["queries"][i][0]
        done = len(lines)
    qs = d["queries"]
    if done >= len(qs):
        print("already done", done)
        return
    conn = sqlite3.connect(os.path.join(sd, f"{s.name}.db"))
    conn.execute("ATTACH DATABASE ? AS raw", (os.path.join(sd, f"{s.name}_raw.db"),))
    s.setup(conn)
    docids = d["docids"]
    t_start = time.time()
    n = 0
    with open(rows_path, "a", encoding="utf-8") as out:
        for qid, text in qs[done:]:
            # identical to run.task_miracl.evaluate
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
            if time.time() - t_start > a.budget:
                break
    conn.close()
    print(f"{a.system}: {done + n}/{len(qs)}")


def sys_order(lang):
    if os.environ.get("QF_SYSTEMS"):  # qfirst run: only the systems of this experiment
        return os.environ["QF_SYSTEMS"].split()
    return [n for n in SYSTEMS if not (n == "jieba" and lang != "zh")]


def cmd_status(a):
    d = json.load(open(os.path.join(WORK, f"sample_{a.lang}_{a.split}.json")))
    for name in sys_order(a.lang):
        sd = os.path.join(WORK, f"{a.lang}_{a.split}", name)
        b = os.path.exists(os.path.join(sd, "build.json"))
        rp = os.path.join(sd, "rows.jsonl")
        n = sum(1 for _ in open(rp)) if os.path.exists(rp) else 0
        print(f"{name:18s} built={b} rows={n}/{d['n_queries']}")


def cmd_merge(a):
    info = json.load(open(os.path.join(WORK, f"sample_{a.lang}_{a.split}.json")))
    result, skipped = {}, {}
    for name in sys_order(a.lang):
        sd = os.path.join(WORK, f"{a.lang}_{a.split}", name)
        bj = json.load(open(os.path.join(sd, "build.json")))
        if "skipped" in bj:
            skipped[name] = bj["skipped"]
            continue
        rows = [json.loads(l) for l in open(os.path.join(sd, "rows.jsonl"), encoding="utf-8")]
        assert len(rows) == info["n_queries"], (name, len(rows))
        result[name] = {"description": SYSTEMS[name].description, "build_seconds": bj["build_seconds"],
                        "index_bytes": bj["index_bytes"], "buckets": run.aggregate(rows, "miracl"),
                        "queries": rows}
    md = run.metadata("miracl", info["corpus_size"], {
        "lang": a.lang, "split": a.split, "max_docs": info["max_docs"], "n_queries": info["n_queries"],
        "data_dir": DATA, "judged_passages_retained": info["judged_passages_retained"],
        "driver": "audit chunk_run_qf.py (copy of chunk_run.py; QF_SYSTEMS subset) (bench.run steps split across calls; index reopened between query chunks)"})
    out = a.out or os.path.join(WORK, f"miracl_{a.lang}_{a.split}.json")
    json.dump({"metadata": md, "systems": result, "skipped": skipped}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "build", "query", "merge", "status"])
    ap.add_argument("--lang", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--system")
    ap.add_argument("--max-docs", type=int, default=100000)
    ap.add_argument("--budget", type=float, default=140)
    ap.add_argument("--out")
    a = ap.parse_args()
    globals()["cmd_" + a.cmd](a)
