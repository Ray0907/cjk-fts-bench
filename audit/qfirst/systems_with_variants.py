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


def run_first_unigrams(terms: list[str]) -> set[str]:
    """Single-CJK-char terms that open a CJK run in a document-mode token stream.

    For a tokenizer that indexes "first char, bigrams..., last char" per run (fts5-cjk's default),
    a run's first char is exactly a 1-char CJK term followed by a bigram that starts with it.
    """
    return {
        t
        for t, nxt in zip(terms, terms[1:])
        if len(t) == 1 and CJK_RUN.fullmatch(t) and len(nxt) == 2 and nxt[0] == t and CJK_RUN.fullmatch(nxt)
    }


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
    except sqlite3.Error:
        return []


def like_match(conn: sqlite3.Connection, table: str, q: str, k: int | None) -> list[int]:
    sql = f"SELECT rowid FROM {table}_raw WHERE text LIKE ? ESCAPE '\\' ORDER BY rowid"
    params: tuple = (like_pattern(q),)
    if k is not None:
        sql += " LIMIT ?"
        params = (like_pattern(q), k)
    try:
        return [r[0] for r in conn.execute(sql, params)]
    except sqlite3.Error:
        return []


class System:
    name = ""
    description = ""
    tokenize = "unicode61"

    def available(self) -> tuple[bool, str]:
        return True, ""

    def setup(self, conn: sqlite3.Connection) -> None:
        pass

    def create_table(self, conn: sqlite3.Connection, table: str) -> None:
        conn.execute(f"CREATE VIRTUAL TABLE {table} USING fts5(text, tokenize={self.tokenize!r})")

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
    # With rank_drop_run_unigrams, keep the unigram that opens each CJK run (an indexed term).
    rank_keep_run_first = False

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
        except sqlite3.Error:
            return []
        seen: dict[str, None] = {}
        for (term,) in rows:
            seen.setdefault(term, None)
        tokens = list(seen)
        if self.rank_drop_run_unigrams:
            kept = set(drop_run_unigrams(tokens, query))
            if self.rank_keep_run_first:
                kept |= run_first_unigrams([term for (term,) in rows])
            tokens = [t for t in tokens if t in kept]
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
        except sqlite3.Error:
            return []


class Fts5CjkUnigram(Fts5Cjk):
    name = "fts5_cjk_unigram"
    description = "fts5-cjk with its documented 'unigram 1' option: also indexes every single CJK char."
    tokenize = "cjk unigram 1"


class Fts5CjkQFirst(Fts5Cjk):
    name = "fts5_cjk_qfirst"
    description = (
        "fts5_cjk (same index); ranking queries also keep the first char of each CJK run, a term "
        "fts5-cjk already indexes. Substring search unchanged (cjk_query())."
    )
    rank_keep_run_first = True


class Fts5CjkQEdge(Fts5Cjk):
    name = "fts5_cjk_qedge"
    description = (
        "fts5_cjk (same index); ranking queries keep the first and last char of each CJK run "
        "(all document-mode tokens). Substring search unchanged (cjk_query())."
    )
    rank_drop_run_unigrams = False


SYSTEMS: dict[str, System] = {
    s.name: s
    for s in (Unicode61(), Trigram(), TrigramLike(), AppBigram(), AppBigramEdge(), AppBigramFirst(), Jieba(), IcuSegmenter(), BetterTrigram(), Fts5Cjk(), Fts5CjkUnigram(), Fts5CjkQFirst(), Fts5CjkQEdge())
}
