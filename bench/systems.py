"""Tokenizer setups compared by the benchmark.

Each System implements the interface described in CONTRIBUTING.md. Every system is implemented the way a typical
user would set it up; nothing is tuned for this benchmark.
"""
from __future__ import annotations

import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parent.parent / "ext" / "build"

# Han (Ext A, URO, compatibility, Ext B+), Hiragana, Katakana (+ext, half-width), Hangul.
CJK_CLASS = (
    "㐀-䶿一-鿿豈-﫿\U00020000-\U0003134f"
    "぀-ゟ゠-ヿㇰ-ㇿｦ-ﾟ"
    "가-힯ᄀ-ᇿ㄰-㆏"
)
CJK_RUN = re.compile(f"[{CJK_CLASS}]+")


def phrase(text: str) -> str:
    """Quote text as one FTS5 string/phrase, escaping embedded double quotes."""
    return '"' + text.replace('"', '""') + '"'


def strip_punct(text: str) -> str:
    """Replace Unicode punctuation and symbols with spaces (applied to every ranking query)."""
    cleaned = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in text)
    return " ".join(cleaned.split())


def drop_run_unigrams(tokens: list[str], query: str) -> list[str]:
    """Drop single-CJK-char tokens whose char only occurs inside CJK runs of length >= 2."""
    runs = CJK_RUN.findall(query)
    standalone = {r for r in runs if len(r) == 1}
    return [t for t in tokens if not (len(t) == 1 and CJK_RUN.fullmatch(t) and t not in standalone)]


# SQLite errors inside a system's search or ranking path are recorded here instead of being lost: a
# search still returns [] (systems never raise), and the runner stores the messages in the query's
# "error" field via take_errors().
_errors: list[str] = []


def record_error(e: Exception) -> None:
    _errors.append(f"{type(e).__name__}: {e}")


def take_errors() -> list[str]:
    """Return and clear the errors recorded since the last call."""
    out = list(_errors)
    _errors.clear()
    return out


def like_pattern(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def fts_match(conn: sqlite3.Connection, table: str, expr: str, k: int | None) -> list[int]:
    sql = f"SELECT rowid FROM {table} WHERE {table} MATCH ? ORDER BY rank"
    params: tuple = (expr,)
    if k is not None:
        sql += " LIMIT ?"
        params = (expr, k)
    try:
        return [r[0] for r in conn.execute(sql, params)]
    except sqlite3.Error as e:
        record_error(e)
        return []


def like_match(conn: sqlite3.Connection, table: str, q: str, k: int | None) -> list[int]:
    sql = f"SELECT rowid FROM {table}_raw WHERE text LIKE ? ESCAPE '\\' ORDER BY rowid"
    params: tuple = (like_pattern(q),)
    if k is not None:
        sql += " LIMIT ?"
        params = (like_pattern(q), k)
    try:
        return [r[0] for r in conn.execute(sql, params)]
    except sqlite3.Error as e:
        record_error(e)
        return []


class System:
    name = ""
    description = ""
    tokenize = "unicode61"
    # MIRACL languages `--systems all` runs this system on; None = every language.
    miracl_langs: tuple[str, ...] | None = None

    def available(self) -> tuple[bool, str]:
        return True, ""

    def setup(self, conn: sqlite3.Connection) -> None:
        pass

    def create_table(self, conn: sqlite3.Connection, table: str, contentless: bool = False) -> None:
        # contentless=True (content='') keeps only the inverted index; used to measure index size.
        opt = ", content=''" if contentless else ""
        conn.execute(f"CREATE VIRTUAL TABLE {table} USING fts5(text, tokenize={self.tokenize!r}{opt})")

    def prep_doc(self, text: str) -> str:
        return text

    def search(self, conn: sqlite3.Connection, table: str, query: str, k: int | None) -> list[int]:
        return fts_match(conn, table, phrase(query), k)

    # --- ranking path (MIRACL): one rule for every system -------------------------------------
    # The query goes through the same transformation as documents (prep_doc) and is then tokenized
    # by the system's OWN FTS5 tokenizer (read back via fts5vocab). The distinct tokens are OR-ed
    # and results ordered by bm25. No system gets hand-written query logic here.

    # Tokenizers that add extra single-char tokens in DOCUMENT mode only (not when FTS5 tokenizes a
    # MATCH query) set this, so the ranking query matches what a real MATCH would see.
    rank_drop_run_unigrams = False

    def query_tokens(self, conn: sqlite3.Connection, query: str) -> list[str]:
        query = strip_punct(query)
        qt = f"qtok_{self.name}"
        try:
            exists = conn.execute(
                "SELECT 1 FROM temp.sqlite_master WHERE name = ?", (qt,)
            ).fetchone()
            if not exists:
                conn.execute(
                    f"CREATE VIRTUAL TABLE temp.{qt} USING fts5(text, tokenize={self.tokenize!r})"
                )
                conn.execute(f"CREATE VIRTUAL TABLE temp.{qt}_v USING fts5vocab(temp, {qt}, instance)")
            conn.execute(f"DELETE FROM temp.{qt}")
            conn.execute(f"INSERT INTO temp.{qt}(rowid, text) VALUES (1, ?)", (self.prep_doc(query),))
            rows = conn.execute(f"SELECT term FROM temp.{qt}_v ORDER BY offset").fetchall()
        except sqlite3.Error as e:
            record_error(e)
            return []
        seen: dict[str, None] = {}
        for (term,) in rows:
            seen.setdefault(term, None)
        tokens = list(seen)
        if self.rank_drop_run_unigrams:
            tokens = drop_run_unigrams(tokens, query)
        return tokens

    def rank(self, conn: sqlite3.Connection, table: str, query: str, k: int | None) -> list[int]:
        tokens = self.query_tokens(conn, query)
        if not tokens:
            return []
        return fts_match(conn, table, " OR ".join(phrase(t) for t in tokens), k)


class Unicode61(System):
    name = "unicode61"
    description = "FTS5 default tokenizer; a whole CJK run becomes one token."
    tokenize = "unicode61"


class Trigram(System):
    name = "trigram"
    description = "Built-in trigram tokenizer; queries under 3 characters match nothing."
    tokenize = "trigram"


class TrigramLike(System):
    name = "trigram_like"
    description = "Trigram, falling back to LIKE scan when the query has <3 chars or FTS finds nothing."
    tokenize = "trigram"

    def search(self, conn, table, query, k):
        hits = fts_match(conn, table, phrase(query), k) if len(query) >= 3 else []
        if not hits:
            hits = like_match(conn, table, query, k)
        return hits


def bigramize(text: str) -> str:
    """Rewrite each CJK run as space-separated overlapping bigrams (1-char runs kept as-is)."""

    def repl(m: re.Match) -> str:
        run = m.group(0)
        if len(run) == 1:
            return f" {run} "
        return " " + " ".join(run[i : i + 2] for i in range(len(run) - 1)) + " "

    return CJK_RUN.sub(repl, text)


class AppBigram(System):
    name = "app_bigram"
    description = (
        "App-level overlapping CJK bigrams + unicode61 (the common 'few-line fix'). "
        "Single-char queries use a bigram prefix query, so a char at the end of a run is missed."
    )
    tokenize = "unicode61"

    def prep_doc(self, text):
        return bigramize(text)

    def search(self, conn, table, query, k):
        if len(query) == 1 and CJK_RUN.fullmatch(query):
            return fts_match(conn, table, f"{phrase(query)}* OR {phrase(query)}", k)
        tokens = bigramize(query).split()
        if not tokens:
            return []
        return fts_match(conn, table, phrase(" ".join(tokens)), k)


def bigramize_edge(text: str, last: bool = True) -> str:
    """Like bigramize, plus the first (and, by default, last) char of every multi-char CJK run."""

    def repl(m: re.Match) -> str:
        run = m.group(0)
        if len(run) == 1:
            return f" {run} "
        grams = [run[i : i + 2] for i in range(len(run) - 1)]
        return " " + " ".join([run[0], *grams, *([run[-1]] if last else [])]) + " "

    return CJK_RUN.sub(repl, text)


class AppBigramEdge(AppBigram):
    name = "app_bigram_edge"
    description = (
        "app_bigram plus the first and last char of each CJK run as extra tokens (documents and "
        "ranking queries). Isolates the edge-unigram technique fts5-cjk uses at index time."
    )

    def prep_doc(self, text):
        return bigramize_edge(text)


class AppBigramFirst(AppBigram):
    name = "app_bigram_first"
    description = (
        "app_bigram plus the first char of each CJK run as an extra token (documents and ranking "
        "queries). Added after an ablation of app_bigram_edge showed the last char adds cost, not quality."
    )

    def prep_doc(self, text):
        return bigramize_edge(text, last=False)


class Jieba(System):
    name = "jieba"
    description = (
        "App-level jieba segmentation: cut_for_search on documents, accurate cut on the query, "
        "query tokens combined with AND; unicode61."
    )
    tokenize = "unicode61"
    miracl_langs: tuple[str, ...] | None = ("zh",)  # jieba segments Chinese only

    def __init__(self):
        self._jieba = None

    def _j(self):
        if self._jieba is None:
            import jieba

            jieba.setLogLevel(logging.WARNING)
            self._jieba = jieba
        return self._jieba

    def available(self):
        try:
            self._j()
            return True, ""
        except Exception as e:  # noqa: BLE001
            return False, f"jieba not importable: {e}"

    def prep_doc(self, text):
        return " ".join(t for t in self._j().cut_for_search(text) if t.strip())

    def search(self, conn, table, query, k):
        tokens = [t for t in self._j().cut(query) if t.strip()]
        if not tokens:
            return []
        return fts_match(conn, table, " AND ".join(phrase(t) for t in tokens), k)


JIEBA_REPO = "https://github.com/fxsjy/jieba"
JIEBA_COMMIT = "67fa2e36e72f69d9134b8a1037b83fbb070b9775"  # master on 2020-02-15, the v0.42.1 release
JIEBA_BIG_SHA256 = "b16011275c42955ccd81fc1adecc93a59dbb7926af69d93fc95d4943d40f6aad"
JIEBA_BIG = Path(__file__).resolve().parent.parent / "data" / "src" / "jieba" / "extra_dict" / "dict.txt.big"


def fetch_jieba_big() -> Path:
    """jieba's dictionary for Traditional Chinese (extra_dict/dict.txt.big), fetched with git at a pinned
    commit and checked against its SHA-256. jieba's README: "a bigger dictionary that has better support for
    traditional Chinese (繁體)"; download it and call jieba.set_dictionary(...)."""
    import hashlib
    import subprocess

    if not JIEBA_BIG.exists():
        repo = JIEBA_BIG.parent.parent
        repo.parent.mkdir(parents=True, exist_ok=True)
        if not (repo / ".git").exists():
            subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", JIEBA_REPO, str(repo)],
                           check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", JIEBA_COMMIT, "--", "extra_dict/dict.txt.big"],
                       check=True)
    digest = hashlib.sha256(JIEBA_BIG.read_bytes()).hexdigest()
    if digest != JIEBA_BIG_SHA256:
        raise RuntimeError(f"{JIEBA_BIG}: sha256 {digest}, expected {JIEBA_BIG_SHA256}")
    return JIEBA_BIG


class JiebaBig(Jieba):
    """jieba with extra_dict/dict.txt.big, the dictionary jieba documents for Traditional Chinese.

    A separate jieba.Tokenizer(dictionary=...) is used rather than jieba.set_dictionary(...), which would
    switch the default tokenizer that the `jieba` system uses in the same process; jieba's README documents
    Tokenizer(dictionary=...) for using different dictionaries at the same time. Run on the Traditional
    Chinese law task only: for Simplified text (MIRACL zh) the default dictionary is the documented choice.
    """

    name = "jieba_big"
    description = (
        "jieba with its Traditional Chinese dictionary (extra_dict/dict.txt.big, pinned commit and SHA-256); "
        "otherwise the same as jieba. Law task only."
    )
    miracl_langs: tuple[str, ...] = ()

    def available(self):
        try:
            fetch_jieba_big()
        except Exception as e:  # noqa: BLE001
            return False, f"jieba dict.txt.big unavailable: {e}"
        return super().available()

    def _j(self):
        if self._jieba is None:
            import jieba

            jieba.setLogLevel(logging.WARNING)
            self._jieba = jieba.Tokenizer(dictionary=str(fetch_jieba_big()))
        return self._jieba


class IcuSegmenter(System):
    """ICU word segmentation via Node's Intl.Segmenter, then unicode61.

    SQLite's FTS5 has no official ICU tokenizer (SQLite's ICU extension targets FTS3/4), so ICU
    word breaking is applied at the application level, like jieba. Intl.Segmenter in Node/V8 and
    browsers is ICU's word-break iterator, so this one system covers both.
    """

    name = "icu_segmenter"
    description = (
        "App-level ICU word segmentation (Intl.Segmenter, CJK dictionary) + unicode61; "
        "query words combined with AND."
    )
    tokenize = "unicode61"
    script = Path(__file__).resolve().parent / "icu_segment.mjs"

    def __init__(self):
        self._proc = None

    def available(self):
        import shutil

        node = shutil.which("node")
        if not node:
            return False, "Node.js not found (needed for Intl.Segmenter)"
        try:
            self._words("測試")
            return True, ""
        except Exception as e:  # noqa: BLE001
            return False, f"Intl.Segmenter unavailable: {e}"

    def _words(self, text: str) -> list[str]:
        import json
        import subprocess

        if self._proc is None or self._proc.poll() is not None:
            self._proc = subprocess.Popen(
                ["node", str(self.script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        # ASCII-escape so U+2028/U+2029 cannot act as line breaks in Node's readline.
        self._proc.stdin.write(json.dumps(text) + "\n")
        self._proc.stdin.flush()
        return json.loads(self._proc.stdout.readline())

    def prep_doc(self, text):
        return " ".join(self._words(text))

    def search(self, conn, table, query, k):
        words = self._words(query)
        if not words:
            return []
        return fts_match(conn, table, " AND ".join(phrase(w) for w in words), k)


class CExtension(System):
    """A tokenizer shipped as a loadable SQLite extension in ext/build/."""

    so_name = ""
    entrypoint: str | None = None

    @property
    def path(self) -> Path:
        return EXT_DIR / self.so_name

    def available(self):
        if not self.path.exists():
            return False, (
                f"{self.so_name} not built. Building third-party C code needs explicit approval "
                "in this environment; see README 'C extensions'."
            )
        try:
            conn = sqlite3.connect(":memory:")
            self.setup(conn)
            self.create_table(conn, "probe")
            conn.close()
            return True, ""
        except (sqlite3.Error, TypeError) as e:
            return False, f"failed to load {self.so_name}: {e}"

    def setup(self, conn):
        conn.enable_load_extension(True)
        if self.entrypoint:
            conn.load_extension(str(self.path), entrypoint=self.entrypoint)
        else:
            conn.load_extension(str(self.path))
        conn.enable_load_extension(False)


class BetterTrigram(CExtension):
    name = "better_trigram"
    description = "streetwriters/sqlite-better-trigram: trigram, with each CJK char as its own token."
    tokenize = "better_trigram"
    so_name = "better_trigram.so"
    entrypoint = "sqlite3_bettertrigram_init"


class Fts5Cjk(CExtension):
    name = "fts5_cjk"
    description = (
        "Ray0907/fts5-cjk: overlapping CJK bigrams in the tokenizer; queries go through its "
        "documented cjk_query() helper (adds * to single CJK chars)."
    )
    tokenize = "cjk"
    so_name = "fts5_cjk.so"
    entrypoint = "sqlite3_cjk_init"
    # fts5-cjk emits run-edge unigrams only when indexing documents; a pure-CJK MATCH query stays a
    # chain of bigrams (its README). Ranking queries are built from document-mode tokens, so drop them.
    rank_drop_run_unigrams = True

    def search(self, conn, table, query, k):
        sql = f"SELECT rowid FROM {table} WHERE {table} MATCH cjk_query(?) ORDER BY rank"
        params: tuple = (query,)
        if k is not None:
            sql += " LIMIT ?"
            params = (query, k)
        try:
            return [r[0] for r in conn.execute(sql, params)]
        except sqlite3.Error as e:
            record_error(e)
            return []


class Fts5CjkUnigram(Fts5Cjk):
    name = "fts5_cjk_unigram"
    description = "fts5-cjk with its documented 'unigram 1' option: also indexes every single CJK char."
    tokenize = "cjk unigram 1"


SYSTEMS: dict[str, System] = {
    s.name: s
    for s in (Unicode61(), Trigram(), TrigramLike(), AppBigram(), AppBigramEdge(), AppBigramFirst(), Jieba(), JiebaBig(), IcuSegmenter(), BetterTrigram(), Fts5Cjk(), Fts5CjkUnigram())
}
