"""Behavioural checks for each tokenizer setup. Known limitations are xfail, not hidden."""
import sqlite3
import warnings

import pytest

warnings.filterwarnings("ignore", category=SyntaxWarning)

from bench.systems import SYSTEMS  # noqa: E402

DOCS = [
    "南投縣魚池鄉",
    "發展中國家",
    "SQLite 全文搜尋 powerful",
    "東京スカパラダイス",
    "한국어 검색 테스트",
    "中華民國憲法第一條",
]

# (query, expected doc index)
CASES = [
    ("魚池", 0),
    ("魚池鄉", 0),
    ("鄉", 0),
    ("全文", 2),
    ("powerful", 2),
    ("スカ", 3),
    ("검색", 4),
    ("民國", 5),
]

KNOWN_LIMITS = {
    ("unicode61", q) for q, _ in CASES if q not in ("powerful", "검색")
} | {
    ("trigram", "魚池"), ("trigram", "鄉"), ("trigram", "全文"), ("trigram", "スカ"),
    ("trigram", "검색"), ("trigram", "民國"),
    ("app_bigram", "鄉"),  # run-final single char is not a bigram prefix
    ("app_bigram_first", "鄉"),  # same: only the run's first char is indexed on its own
    ("jieba", "魚池"), ("jieba", "魚池鄉"), ("jieba", "鄉"), ("jieba", "民國"),  # simplified-Chinese dictionary
    ("icu_segmenter", "民國"),  # ICU keeps 中華民國 as one word
}


def build(system):
    conn = sqlite3.connect(":memory:")
    system.setup(conn)
    conn.execute("CREATE TABLE t_raw(rowid INTEGER PRIMARY KEY, text TEXT)")
    system.create_table(conn, "t")
    for i, d in enumerate(DOCS):
        conn.execute("INSERT INTO t_raw VALUES (?, ?)", (i, d))
        conn.execute("INSERT INTO t(rowid, text) VALUES (?, ?)", (i, system.prep_doc(d)))
    return conn


PARAMS = []
for name in SYSTEMS:
    for q, want in CASES:
        marks = []
        if (name, q) in KNOWN_LIMITS:
            marks.append(pytest.mark.xfail(reason="known limitation of this setup", strict=True))
        PARAMS.append(pytest.param(name, q, want, marks=marks, id=f"{name}-{q}"))


@pytest.mark.parametrize("name,query,want", PARAMS)
def test_finds_expected_doc(name, query, want):
    system = SYSTEMS[name]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    conn = build(system)
    assert want in system.search(conn, "t", query, None)


@pytest.mark.parametrize("name", list(SYSTEMS))
def test_odd_input_never_raises(name):
    system = SYSTEMS[name]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    conn = build(system)
    for q in ['"', 'a"b', "NEAR(", "*", "", "%_", "OR", "中\"文"]:
        assert isinstance(system.search(conn, "t", q, 5), list)


@pytest.mark.parametrize("name", list(SYSTEMS))
def test_rank_handles_sentence_queries(name):
    """Ranking path: a full-sentence question must retrieve the relevant doc (or be a documented miss)."""
    system = SYSTEMS[name]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    conn = build(system)
    res = system.rank(conn, "t", "南投的魚池鄉在哪裡？", 10)
    if name == "unicode61":
        pytest.xfail("unicode61 keeps the whole CJK run as one token")
    assert res and res[0] == 0


def _toks(name, q):
    system = SYSTEMS[name]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    conn = sqlite3.connect(":memory:")
    system.setup(conn)
    return system.query_tokens(conn, q)


@pytest.mark.parametrize("q", ["中国俄罗斯族有多少人？", "臺灣最高的山是哪一座", "台北 101 有多高?"])
def test_bigram_systems_rank_with_same_tokens(q):
    """Fairness: both bigram setups must send the same ranking tokens (fts5-cjk's index-time edge
    unigrams must not leak into its query); the edge technique is credited to app_bigram_edge."""
    # fts5-cjk folds 14 documented variants (README); that is a feature, not token leakage.
    fold = str.maketrans("臺裡羣峯綫衞爲眞敎册祕啓淸靑", "台裏群峰線衛為真教冊秘啟清青")
    expected = [t.translate(fold) for t in _toks("app_bigram", q)]
    assert _toks("fts5_cjk", q) == expected
    assert _toks("fts5_cjk_unigram", q) == expected


def test_ranking_tokens_have_no_punctuation():
    for name in SYSTEMS:
        for t in _toks(name, "中国俄罗斯族有多少人？"):
            assert "？" not in t and not t.endswith(" "), (name, t)


def test_icu_segmenter_handles_unicode_line_separators():
    """Regression: a MIRACL ko passage containing U+2028 broke the Node pipe protocol."""
    system = SYSTEMS["icu_segmenter"]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    assert system.prep_doc("한국어\u2028검색\u2029테스트\r\n中文\n") .split() == ["한국어", "검색", "테스트", "中文"]
    assert system.prep_doc("after") == "after"  # protocol still in sync


def test_app_bigram_first_adds_only_the_first_char():
    """The run's first char is an extra token in documents and ranking queries; the last is not."""
    system = SYSTEMS["app_bigram_first"]
    assert system.prep_doc("魚池鄉 abc 鄉").split() == ["魚", "魚池", "池鄉", "abc", "鄉"]
    assert _toks("app_bigram_first", "魚池鄉在哪？")[:2] == ["魚", "魚池"]
    assert "哪" not in _toks("app_bigram_first", "魚池鄉在哪？")
