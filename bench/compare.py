"""Paired comparison of two systems on the same queries.

  python -m bench.compare results/miracl_zh.json fts5_cjk app_bigram [--metric ndcg10]

Prints the mean difference (A - B), a 95% paired-bootstrap confidence interval, a two-sided paired
randomization (sign-flip) p-value, and per-query wins/ties/losses. Deterministic (seed 42).
"""
from __future__ import annotations

import argparse
import json
import random


def paired(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 42) -> dict:
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    mean = sum(d) / n
    rng = random.Random(seed)
    boots = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]
    extreme = 0
    for _ in range(n_boot):
        m = sum(x if rng.random() < 0.5 else -x for x in d) / n
        if abs(m) >= abs(mean) - 1e-12:
            extreme += 1
    return {
        "n": n,
        "mean_diff": mean,
        "ci95": (lo, hi),
        "p_value": (extreme + 1) / (n_boot + 1),
        "wins": sum(x > 1e-12 for x in d),
        "ties": sum(abs(x) <= 1e-12 for x in d),
        "losses": sum(x < -1e-12 for x in d),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--metric", default="ndcg10")
    args = ap.parse_args(argv)
    r = json.load(open(args.results, encoding="utf-8"))
    qa = {q.get("qid", q["query"]): q[args.metric] for q in r["systems"][args.a]["queries"]}
    qb = {q.get("qid", q["query"]): q[args.metric] for q in r["systems"][args.b]["queries"]}
    keys = sorted(set(qa) & set(qb))
    res = paired([qa[k] for k in keys], [qb[k] for k in keys])
    lo, hi = res["ci95"]
    print(f"{args.metric}: {args.a} - {args.b} over {res['n']} queries")
    print(f"  mean diff {res['mean_diff']:+.4f}, 95% CI [{lo:+.4f}, {hi:+.4f}], p = {res['p_value']:.4f}")
    print(f"  per query: {res['wins']} wins, {res['ties']} ties, {res['losses']} losses")


if __name__ == "__main__":
    main()
