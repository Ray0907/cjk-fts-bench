import json
import os

import pytest

from bench import data_miracl, run, report

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "miracl_tiny")


@pytest.fixture(autouse=True)
def stub(monkeypatch):
    monkeypatch.setenv("BENCH_SYSTEMS_MODULE", "tests._stub_systems")


def test_loader_full():
    d = data_miracl.load(FIX, "zh")
    assert len(d["texts"]) == 20 and len(d["queries"]) == 5
    assert d["docids"] == sorted(d["docids"])
    assert d["qrels"]["101"]["4#0"] == 1 and d["qrels"]["101"]["2#0"] == 0
    assert d["texts"][d["docids"].index("4#0")].startswith("玉山 玉山主峰")


def test_loader_max_docs_keeps_judged_and_deterministic():
    a = data_miracl.load(FIX, "zh", max_docs=12)
    b = data_miracl.load(FIX, "zh", max_docs=12)
    assert a["docids"] == b["docids"] and len(a["docids"]) == 12
    judged = {d for q in a["qrels"].values() for d in q}
    assert judged <= set(a["docids"])
    c = data_miracl.load(FIX, "zh", max_docs=3)  # fewer than judged: all judged kept
    assert judged <= set(c["docids"])


def test_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        data_miracl.load(str(tmp_path), "zh")


def test_like_escape():
    assert run.like_escape("a%b_c\\") == "a\\%b\\_c\\\\"
    gt = run.ground_truth(["50%off", "50xoff", "a_b", "axb"], ["50%", "a_b"])
    assert gt["50%"] == {0} and gt["a_b"] == {2}


def test_end_to_end_miracl(tmp_path):
    out = tmp_path / "m.json"
    run.main(["miracl", "--data-dir", FIX, "--systems", "unicode61,trigram,missing", "--out", str(out)])
    r = json.loads(out.read_text())
    assert set(r["systems"]) == {"unicode61", "trigram"} and "missing" in r["skipped"]
    assert r["metadata"]["corpus_size"] == 20
    assert r["metadata"]["tool_versions"].get("jieba")  # tool versions are recorded with every run
    t = r["systems"]["trigram"]
    assert len(t["queries"]) == 5 and t["index_bytes"] > 0 and t["build_seconds"] > 0
    # Index size three ways: the contentless index is smaller than the table with its stored copy.
    assert 0 < t["index_bytes_contentless"] < t["index_bytes"] and r["metadata"]["raw_table_bytes"] > 0
    for s in r["systems"].values():
        assert 0 <= s["buckets"]["all"]["ndcg10"] <= 1
    # Sentence queries must actually retrieve something; an all-zero run is a harness bug.
    assert sum(q["s"] > 0 for q in t["queries"]) >= 3, "sentence queries retrieve nothing: harness bug"
    assert t["buckets"]["all"]["ndcg10"] > 0
    md = report.render(r)
    assert "nDCG@10" in md and "Skipped" in md and "index only MB" in md


def test_law_smoke(tmp_path):
    if not os.path.exists(os.path.join(run.data_law.DATA, "law_articles.jsonl")):
        pytest.skip("law corpus not downloaded")
    out = tmp_path / "l.json"
    run.main(["law_substring", "--systems", "trigram", "--limit-docs", "500", "--limit-queries", "10",
              "--out", str(out)])
    r = json.loads(out.read_text())
    rows = r["systems"]["trigram"]["queries"]
    assert len(rows) == 10
    # trigram substring is exact when it returns anything; precision is undefined when it returns nothing
    assert all(x["precision"] == 1.0 for x in rows if x["s"])
    assert all(x["precision"] is None for x in rows if not x["s"])
    assert "Failure examples" in report.render(r)


def test_sqlite_errors_are_recorded_not_lost():
    """A failing MATCH still returns [] (systems never raise), but the error reaches the result row."""
    import sqlite3

    from bench import systems

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE docs USING fts5(text)")
    conn.execute("INSERT INTO docs(rowid, text) VALUES (1, 'x')")
    systems.take_errors()
    assert systems.fts_match(conn, "no_such_table", '"x"', 5) == []
    errs = systems.take_errors()
    assert len(errs) == 1 and "no such table" in errs[0]

    class Broken:
        def search(self, conn, table, query, k):
            return systems.fts_match(conn, table, "NEAR(", k)  # FTS5 syntax error

    class Fine:
        def search(self, conn, table, query, k):
            return systems.fts_match(conn, table, systems.phrase(query), k)

    res, _, err = run.timed_search(Broken(), conn, "x", 5)
    assert res == [] and err and "syntax error" in err
    res, _, err = run.timed_search(Fine(), conn, "x", 5)
    assert res == [1] and err is None
    assert systems.take_errors() == []
