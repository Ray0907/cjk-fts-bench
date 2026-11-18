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


def test_jieba_big_uses_the_pinned_traditional_dictionary():
    """jieba_big loads jieba's documented Traditional Chinese dictionary (pinned commit, checked SHA-256) in
    its own Tokenizer, so the default `jieba` system keeps the default dictionary in the same process."""
    import hashlib

    from bench.systems import JIEBA_BIG_SHA256, fetch_jieba_big

    big, default = SYSTEMS["jieba_big"], SYSTEMS["jieba"]
    ok, why = big.available()
    if not ok:
        pytest.skip(why)
    assert hashlib.sha256(fetch_jieba_big().read_bytes()).hexdigest() == JIEBA_BIG_SHA256
    assert list(big._j().cut("南投縣魚池鄉")) == ["南投縣", "魚池", "鄉"]
    assert list(default._j().cut("南投縣魚池鄉")) == ["南投", "縣魚", "池鄉"]
    assert big.miracl_langs == () and default.miracl_langs == ("zh",)



def _doc_tokens(name, text):
    """Tokens a system indexes for text (after its prep_doc), in order."""
    system = SYSTEMS[name]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    conn = sqlite3.connect(":memory:")
    system.setup(conn)
    system.create_table(conn, "d")
    conn.execute("INSERT INTO d(rowid, text) VALUES (1, ?)", (system.prep_doc(text),))
    conn.execute("CREATE VIRTUAL TABLE dv USING fts5vocab(d, instance)")
    return [t for (t,) in conn.execute("SELECT term FROM dv ORDER BY offset")]


def test_better_trigram_splits_han_and_kana_but_not_hangul():
    """better-trigram's README: 'treating each CJK character as its own token'. Its CJK ranges cover Han, kana
    and full-width forms but not Hangul, so Korean words get trigrams like Latin words (shorter words stay whole)."""
    assert _doc_tokens("better_trigram", "東京スカ") == ["東", "京", "ス", "カ"]
    assert _doc_tokens("better_trigram", "검색엔진을") == ["검색엔", "색엔진", "엔진을"]
    assert _doc_tokens("better_trigram", "한국어 검색") == ["한국어", "검색"]


def test_highlight_returns_original_text_only_for_tokenizer_level_systems():
    """fts5-cjk's token offsets point into the original text, so highlight() marks the original. An app-level
    table stores and therefore returns its transformed (bigram-rewritten) text."""
    text = "台北市立圖書館今天休館"

    def hl(name, match):
        system = SYSTEMS[name]
        ok, why = system.available()
        if not ok:
            pytest.skip(why)
        conn = build(system)
        conn.execute("INSERT INTO t(rowid, text) VALUES (99, ?)", (system.prep_doc(text),))
        return conn.execute("SELECT highlight(t, 0, '[', ']') FROM t WHERE rowid = 99 AND t MATCH ?",
                            (match,)).fetchone()[0]

    assert hl("fts5_cjk", '"圖書"') == "台北市立[圖書]館今天休館"
    assert hl("app_bigram", '"圖書"').split() == ["台北", "北市", "市立", "立圖", "[圖書]", "書館", "館今", "今天", "天休", "休館"]


# app_bigram's CJK class (CJK_CLASS) is the benchmark's own; fts5-cjk counts 々〆〇 as CJK and folds half-width
# kana and full-width ASCII. Where they differ, the two do not send the same ranking tokens. Changing CJK_CLASS
# would change app_bigram's dev results, which cannot be re-run here, so the differences are recorded instead.
@pytest.mark.parametrize("q", [
    pytest.param("佐々木さんの話", marks=pytest.mark.xfail(reason="々 is CJK for fts5-cjk, not for app_bigram", strict=True)),
    pytest.param("〆切は金曜", marks=pytest.mark.xfail(reason="〆 is CJK for fts5-cjk, not for app_bigram", strict=True)),
    pytest.param("ｶﾀｶﾅの本", marks=pytest.mark.xfail(reason="fts5-cjk folds half-width kana", strict=True)),
    pytest.param("ＳＱＬｉｔｅの本", marks=pytest.mark.xfail(reason="fts5-cjk folds full-width ASCII", strict=True)),
    "東京の大学",
])
def test_bigram_systems_rank_with_same_tokens_beyond_han(q):
    fold = str.maketrans("臺裡羣峯綫衞爲眞敎册祕啓淸靑", "台裏群峰線衛為真教冊秘啟清青")
    assert _toks("fts5_cjk", q) == [t.translate(fold) for t in _toks("app_bigram", q)]


def test_icu_segmenter_splits_hangul_only_at_spaces():
    """ICU keeps a Korean word with its particle as one word, so 검색을 is never the token 검색."""
    system = SYSTEMS["icu_segmenter"]
    ok, why = system.available()
    if not ok:
        pytest.skip(why)
    assert system.prep_doc("검색을 하다").split() == ["검색을", "하다"]


@pytest.mark.parametrize("q", ["中国俄罗斯族有多少人？", "臺灣最高的山是哪一座", "台北 101 有多高?", "魚池鄉 abc 鄉"])
def test_fts5_cjk_query_variants_send_the_app_level_tokens(q):
    """fts5_cjk_qfirst / _qedge only add the run-edge unigrams fts5-cjk already indexes to the ranking query,
    so they send the same tokens as app_bigram_first / app_bigram_edge (up to fts5-cjk's variant folding)."""
    fold = str.maketrans("臺裡羣峯綫衞爲眞敎册祕啓淸靑", "台裏群峰線衛為真教冊秘啟清青")
    # Order can differ (a char that ends one run and stands alone later); OR-ed tokens are a set.
    assert sorted(_toks("fts5_cjk_qfirst", q)) == sorted(t.translate(fold) for t in _toks("app_bigram_first", q))
    assert sorted(_toks("fts5_cjk_qedge", q)) == sorted(t.translate(fold) for t in _toks("app_bigram_edge", q))


def test_fts5_cjk_query_variants_keep_the_search_path():
    """Only ranking queries change; the substring task still goes through cjk_query()."""
    for name in ("fts5_cjk_qfirst", "fts5_cjk_qedge"):
        assert type(SYSTEMS[name]).search is type(SYSTEMS["fts5_cjk"]).search
        assert SYSTEMS[name].tokenize == SYSTEMS["fts5_cjk"].tokenize


def test_ranking_only_variants_skip_the_law_task_but_not_miracl():
    from bench.run import pick_systems

    law, ko = pick_systems("all", SYSTEMS), pick_systems("all", SYSTEMS, lang="ko")
    assert "fts5_cjk_qfirst" not in law and "fts5_cjk_qedge" not in law and "fts5_cjk" in law
    assert "fts5_cjk_qfirst" in ko and "fts5_cjk_qedge" in ko and "jieba" not in ko
