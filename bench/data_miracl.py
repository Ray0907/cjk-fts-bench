"""MIRACL loader from local files (nothing is downloaded by this code).

Files the user needs (Hugging Face; download manually, e.g. with `huggingface-cli download`):

  From https://huggingface.co/datasets/miracl/miracl  (repo layout miracl-v1.0-<lang>/...):
    miracl-v1.0-zh/topics/topics.miracl-v1.0-zh-dev.tsv     topics, `qid<TAB>query`
    miracl-v1.0-zh/qrels/qrels.miracl-v1.0-zh-dev.tsv       qrels, `qid Q0 docid rel` (tab/space separated)
  From https://huggingface.co/datasets/miracl/miracl-corpus  (repo layout miracl-corpus-v1.0-<lang>/...):
    miracl-corpus-v1.0-zh/docs-0.jsonl.gz ... docs-N.jsonl.gz   corpus, JSONL {"docid","title","text"}
    (gzipped or plain, single file or sharded)

Put them anywhere below --data-dir; files are discovered recursively: topics = *topics*<lang>*<split>*.tsv,
qrels = *qrels*<lang>*<split>*.tsv, corpus = *.jsonl / *.jsonl.gz whose path contains "corpus" (and the
language code if possible). Split defaults to "dev" (dev has public qrels; test has none).

A document is title + " " + text. rowid = position in the loaded doc list (docs sorted by docid). With
max_docs, ALL judged docs are kept plus random distractors (reservoir sampling, seed 42) up to max_docs.
"""
import glob
import gzip
import json
import os
import random
import re

SEED = 42


def _natkey(p):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p)]


def _find(data_dir, kind, lang, split):
    hits = [p for p in glob.glob(os.path.join(data_dir, "**", "*.tsv"), recursive=True)
            if kind in os.path.basename(p) and lang in os.path.basename(p)
            and split in os.path.basename(p)]
    if not hits:
        raise FileNotFoundError(f"no {kind} tsv for lang={lang} split={split} under {data_dir}")
    return sorted(hits)[0]


def find_corpus_files(data_dir, lang):
    allj = [p for p in glob.glob(os.path.join(data_dir, "**", "*.jsonl*"), recursive=True)
            if p.endswith((".jsonl", ".jsonl.gz"))]
    corp = [p for p in allj if "corpus" in p.lower()]
    sel = [p for p in corp if f"-{lang}" in p or f"/{lang}/" in p] or corp or allj
    if not sel:
        raise FileNotFoundError(f"no corpus jsonl[.gz] under {data_dir}")
    return sorted(sel, key=_natkey)


def _open(p):
    return gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")


def load_topics(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            qid, _, q = line.partition("\t")
            out[qid.strip()] = q.strip()
    return out


def load_qrels(path):
    """{qid: {docid: rel}}"""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 4:
                out.setdefault(p[0], {})[p[2]] = int(p[3])
    return out


def iter_corpus(files):
    for f in files:
        with _open(f) as fh:
            for line in fh:
                if line.strip():
                    d = json.loads(line)
                    yield d["docid"], ((d.get("title") or "") + " " + (d.get("text") or "")).strip()


def load_corpus(files, judged, max_docs=None, seed=SEED):
    """Returns (docids, texts), sorted by docid. Keeps every doc in `judged`; with max_docs adds a
    uniform random sample of the other docs so that the total is <= max_docs (one streaming pass)."""
    rng = random.Random(seed)
    keep, res, n_other = [], [], 0
    for docid, text in iter_corpus(files):
        if docid in judged:
            keep.append((docid, text))
        elif max_docs is None:
            res.append((docid, text))
        else:  # reservoir of size max_docs (>= room); trimmed uniformly below
            n_other += 1
            if len(res) < max_docs:
                res.append((docid, text))
            else:
                j = rng.randrange(n_other)
                if j < max_docs:
                    res[j] = (docid, text)
    if max_docs is not None:
        room = max(0, max_docs - len(keep))
        if len(res) > room:
            res = rng.sample(res, room)
    docs = sorted(keep + res, key=lambda x: x[0])
    return [d for d, _ in docs], [t for _, t in docs]


def load(data_dir, lang="zh", split="dev", max_docs=None):
    """Returns dict: docids, texts, queries [(qid, text)], qrels {qid:{docid:rel}}."""
    topics = load_topics(_find(data_dir, "topics", lang, split))
    qrels = load_qrels(_find(data_dir, "qrels", lang, split))
    qids = sorted(q for q in topics if q in qrels and any(r > 0 for r in qrels[q].values()))
    judged = {d for q in qids for d in qrels[q]}
    docids, texts = load_corpus(find_corpus_files(data_dir, lang), judged, max_docs)
    return {"docids": docids, "texts": texts,
            "queries": [(q, topics[q]) for q in qids],
            "qrels": {q: qrels[q] for q in qids}}
