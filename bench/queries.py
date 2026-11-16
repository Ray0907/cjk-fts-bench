"""Deterministic query generation for law_substring. Seed 42.

Queries are chosen independently of every system under test (an earlier version sampled words
from jieba's own segmentation, which favoured jieba and produced non-words such as 劃致).

- word2 / word3 / word4plus (100 each): headwords of the Ministry of Education's Revised Mandarin
  Chinese Dictionary (重編國語辭典修訂本, via g0v/moedict-data; CC BY-ND 3.0 TW, © Ministry of
  Education, R.O.C.) that are all-Han and appear in at least 3 law articles.
- char1 (50): distinct Han characters appearing in at least 3 articles.
- span_nonword (50): random 2-4 character all-Han spans from the corpus that are NOT headwords,
  i.e. partial strings a user might type that no dictionary would treat as a word.
"""
import json
import lzma
import os
import random
import re
import subprocess
from collections import Counter

from . import data_law

SEED = 42
HAN = re.compile(r"^[㐀-䶿一-鿿]+$")
N_WORD, N_CHAR, N_SPAN = 100, 50, 50
MAX_WORD_LEN = 8
DICT_REPO = "https://github.com/g0v/moedict-data"
DICT_DIR = os.path.join(data_law.DATA, "src", "moedict-data")
DICT_COMMIT = "a6dc997417507eb510fc29822bc514de2c92728c"
FREQ_CACHE = os.path.join(data_law.DATA, "law_dictfreq.json")
QUERIES = os.path.join(data_law.DATA, "law_queries.json")


def dictionary_words():
    """All-Han headwords of length 2..MAX_WORD_LEN from the MOE revised dictionary."""
    path = os.path.join(DICT_DIR, "dict-revised.json.xz")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(DICT_DIR), exist_ok=True)
        subprocess.run(["git", "clone", "-q", DICT_REPO, DICT_DIR], check=True)
        subprocess.run(["git", "-C", DICT_DIR, "checkout", "-q", DICT_COMMIT], check=True)
    entries = json.loads(lzma.open(path).read())
    return sorted({e["title"] for e in entries
                   if HAN.match(e.get("title", "")) and 2 <= len(e["title"]) <= MAX_WORD_LEN})


def word_doc_freq(articles, words):
    """Number of articles containing each dictionary word as a substring (cached)."""
    key = f"{len(articles)}|{data_law.commit_hash()}|{DICT_COMMIT}"
    if os.path.exists(FREQ_CACHE):
        with open(FREQ_CACHE, encoding="utf-8") as fh:
            cached = json.load(fh)
        if cached.get("key") == key:
            return Counter(cached["freq"])
    by_len = {}
    for w in words:
        by_len.setdefault(len(w), set()).add(w)
    freq = Counter()
    for a in articles:
        found = set()
        for L, pool in by_len.items():
            for i in range(len(a) - L + 1):
                g = a[i:i + L]
                if g in pool:
                    found.add(g)
        freq.update(found)
    with open(FREQ_CACHE, "w", encoding="utf-8") as fh:
        json.dump({"key": key, "freq": freq}, fh, ensure_ascii=False)
    return freq


def generate(articles, words, freq, seed=SEED):
    rng = random.Random(seed)
    common = sorted(w for w in words if freq.get(w, 0) >= 3)
    out = []
    for bucket, pred in (("word2", lambda w: len(w) == 2), ("word3", lambda w: len(w) == 3),
                         ("word4plus", lambda w: len(w) >= 4)):
        pool = [w for w in common if pred(w)]
        out += [{"query": q, "bucket": bucket} for q in rng.sample(pool, N_WORD)]
    cc = Counter(ch for a in articles for ch in set(a) if HAN.match(ch))
    chars = sorted(c for c, n in cc.items() if n >= 3)
    out += [{"query": q, "bucket": "char1"} for q in rng.sample(chars, N_CHAR)]
    wordset = set(words)
    seen, spans, tries = set(), [], 0
    while len(spans) < N_SPAN and tries < 100000:
        tries += 1
        a = articles[rng.randrange(len(articles))]
        L = rng.randint(2, 4)
        if len(a) < L:
            continue
        st = rng.randrange(len(a) - L + 1)
        sub = a[st:st + L]
        if not HAN.match(sub) or sub in seen or sub in wordset:
            continue
        seen.add(sub)
        spans.append(sub)
    out += [{"query": q, "bucket": "span_nonword"} for q in spans]
    return out


def load_queries():
    arts = data_law.load_articles()
    key = {"seed": SEED, "corpus_articles": len(arts), "commit": data_law.commit_hash(),
           "dictionary": f"g0v/moedict-data@{DICT_COMMIT}"}
    if os.path.exists(QUERIES):
        with open(QUERIES, encoding="utf-8") as fh:
            cached = json.load(fh)
        if all(cached.get(k) == v for k, v in key.items()):
            return cached["queries"]
    words = dictionary_words()
    qs = generate(arts, words, word_doc_freq(arts, words))
    with open(QUERIES, "w", encoding="utf-8") as fh:
        json.dump({**key, "queries": qs}, fh, ensure_ascii=False, indent=1)
    return qs


if __name__ == "__main__":
    qs = load_queries()
    print(Counter(q["bucket"] for q in qs))
