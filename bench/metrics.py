"""Retrieval metrics."""
import math


def substring_metrics(S, G):
    """S: returned rowids (iterable), G: ground-truth rowids. Returns dict.

    precision is None (undefined) when nothing is returned: an empty answer is neither precise nor
    imprecise, and counting it as 1.0 made a setup that returns nothing look perfectly precise. Means
    over queries skip None; zero_result records those queries instead."""
    S, G = set(S), set(G)
    inter = len(S & G)
    return {
        "g": len(G), "s": len(S),
        "recall": (inter / len(G)) if G else 1.0,
        "precision": (inter / len(S)) if S else None,
        "zero_result": bool(G) and not S,
    }


def ndcg_at_k(ranked, qrels, k=10):
    """ranked: list of docids best-first; qrels: {docid: graded rel}. Standard
    DCG = sum rel_i / log2(i+1) (i from 1), ideal from sorted qrels. 0.0 if no relevant."""
    dcg = sum(qrels.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted((r for r in qrels.values() if r > 0), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(ranked, qrels, k=100):
    rel = {d for d, r in qrels.items() if r > 0}
    if not rel:
        return 0.0
    return len(rel & set(ranked[:k])) / len(rel)


def percentile(xs, p):
    """Linear-interpolation percentile, p in [0,100]."""
    if not xs:
        return 0.0
    xs = sorted(xs)
    pos = (len(xs) - 1) * p / 100
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)
