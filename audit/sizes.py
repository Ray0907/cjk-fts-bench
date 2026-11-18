"""Task B: index size with and without FTS5's stored text copy (approach of the earlier audit's size.py).

python sizes.py --corpus ko_train --system app_bigram     -> appends one JSON line to ~/cjkwork/sizes.jsonl
python sizes.py --corpus law --system app_bigram
python sizes.py --corpus ko_train --raw                   -> size of one plain raw-text table

For each system the documents are transformed with the system's own prep_doc, then inserted in one
transaction (as bench.run does) into four fresh databases, all with page_size 4096 (SQLite default):
  default         : fts5(text, tokenize=...)                 then VACUUM           (= what the benchmark reports)
  default_opt     : same, then INSERT INTO t(t) VALUES('optimize'), then VACUUM
  contentless     : fts5(text, tokenize=..., content='')     then VACUUM           (inverted index + docsize only)
  contentless_opt : same, then 'optimize', then VACUUM
stored_text_bytes = UTF-8 bytes of what the system stores (transformed text for app-level systems, raw
for tokenizer-level ones); raw_text_bytes = UTF-8 bytes of the original text.
"""
import argparse, json, os, pickle, sqlite3, sys, tempfile, time

REPO = os.path.expanduser("~/cjkrun")
sys.path.insert(0, REPO)
os.chdir(REPO)
from bench.systems import SYSTEMS  # noqa: E402

WORK = os.path.expanduser("~/cjkwork")
OUT = os.path.join(WORK, "sizes.jsonl")


def load_texts(corpus):
    if corpus == "law":
        from bench import data_law
        return data_law.load_articles()
    with open(os.path.join(WORK, f"sample_{corpus}.pkl"), "rb") as fh:
        return pickle.load(fh)["texts"]


def one(s, docs, contentless, optimize, td):
    p = os.path.join(td, "x.db")
    if os.path.exists(p):
        os.remove(p)
    c = sqlite3.connect(p)
    c.execute("PRAGMA page_size=4096")
    s.setup(c)
    opt = ", content=''" if contentless else ""
    c.execute(f"CREATE VIRTUAL TABLE docs USING fts5(text, tokenize={s.tokenize!r}{opt})")
    with c:
        c.executemany("INSERT INTO docs(rowid,text) VALUES (?,?)", enumerate(docs))
    if optimize:
        with c:
            c.execute("INSERT INTO docs(docs) VALUES('optimize')")
    c.execute("VACUUM")
    ps = c.execute("PRAGMA page_size").fetchone()[0]
    c.close()
    return os.path.getsize(p), ps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--system")
    ap.add_argument("--raw", action="store_true")
    a = ap.parse_args()
    texts = load_texts(a.corpus)
    raw_bytes = sum(len(t.encode("utf-8")) for t in texts)
    tdroot = os.path.expanduser("~/cjktmp")
    if a.raw:
        with tempfile.TemporaryDirectory(dir=tdroot) as td:
            p = os.path.join(td, "raw.db")
            c = sqlite3.connect(p)
            c.execute("PRAGMA page_size=4096")
            c.execute("CREATE TABLE docs_raw(rowid INTEGER PRIMARY KEY, text TEXT)")
            with c:
                c.executemany("INSERT INTO docs_raw(rowid,text) VALUES (?,?)", enumerate(texts))
            c.execute("VACUUM")
            c.close()
            rec = {"corpus": a.corpus, "system": "_raw_table", "n_docs": len(texts), "raw_text_bytes": raw_bytes,
                   "raw_table_db_bytes": os.path.getsize(p), "sqlite": sqlite3.sqlite_version}
    else:
        s = SYSTEMS[a.system]
        ok, why = s.available()
        if not ok:
            raise SystemExit(f"{a.system} unavailable: {why}")
        t0 = time.time()
        docs = [s.prep_doc(t) for t in texts]
        rec = {"corpus": a.corpus, "system": a.system, "n_docs": len(texts), "raw_text_bytes": raw_bytes,
               "stored_text_bytes": sum(len(d.encode("utf-8")) for d in docs), "sqlite": sqlite3.sqlite_version}
        with tempfile.TemporaryDirectory(dir=tdroot) as td:
            for name, cl, op in (("default", 0, 0), ("default_opt", 0, 1), ("contentless", 1, 0), ("contentless_opt", 1, 1)):
                rec[name], rec["page_size"] = one(s, docs, cl, op, td)
        rec["seconds"] = time.time() - t0
    with open(OUT, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
