import math
from bench.metrics import substring_metrics, ndcg_at_k, recall_at_k, percentile


def test_substring_basic():
    m = substring_metrics([1, 2, 5], [1, 2, 3, 4])
    assert m["recall"] == 0.5 and abs(m["precision"] - 2 / 3) < 1e-12
    assert not m["zero_result"] and m["g"] == 4 and m["s"] == 3


def test_substring_empty_S():
    m = substring_metrics([], [1])
    assert m["recall"] == 0 and m["precision"] == 1.0 and m["zero_result"] is True


def test_substring_empty_both():
    m = substring_metrics([], [])
    assert m["zero_result"] is False and m["precision"] == 1.0


def test_ndcg_hand():
    # ranked a,b,c ; rels a=0, b=2, c=1 ; ideal order 2,1
    q = {"b": 2, "c": 1, "z": 0}
    dcg = 2 / math.log2(3) + 1 / math.log2(4)
    idcg = 2 / math.log2(2) + 1 / math.log2(3)
    assert abs(ndcg_at_k(["a", "b", "c"], q) - dcg / idcg) < 1e-12


def test_ndcg_perfect_and_none():
    assert ndcg_at_k(["x", "y"], {"x": 1, "y": 1}) == 1.0
    assert ndcg_at_k(["x"], {}) == 0.0
    assert ndcg_at_k([], {"x": 1}) == 0.0


def test_ndcg_cutoff():
    q = {"d11": 1}
    assert ndcg_at_k([f"d{i}" for i in range(1, 12)], q, k=10) == 0.0


def test_recall_at_k():
    q = {"a": 1, "b": 2, "c": 0, "d": 1}
    assert abs(recall_at_k(["a", "x", "b"], q, 100) - 2 / 3) < 1e-12
    assert recall_at_k(["a", "x", "b"], q, 1) == 1 / 3
    assert recall_at_k(["a"], {}, 100) == 0.0


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert abs(percentile([1, 2, 3, 4], 95) - 3.85) < 1e-12
