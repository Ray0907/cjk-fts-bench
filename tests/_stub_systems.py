"""Private stub implementing unicode61 + trigram with the System interface (for harness tests)."""
import sqlite3

from bench.systems import System as _Real


def _q(query):
    return '"' + query.replace('"', '""') + '"'


class _Base:
    name = ""
    description = ""
    tok = ""

    def available(self):
        return True, ""

    def setup(self, conn):
        pass

    def create_table(self, conn, table, contentless=False):
        opt = ", content=''" if contentless else ""
        conn.execute(f"CREATE VIRTUAL TABLE {table} USING fts5(text, tokenize='{self.tok}'{opt})")

    def prep_doc(self, text):
        return text

    @property
    def tokenize(self):
        return self.tok

    # Ranking path is shared with the real systems, so harness tests exercise the real rule.
    rank_drop_run_unigrams = False
    query_tokens = _Real.query_tokens
    rank = _Real.rank

    def search(self, conn, table, query, k):
        sql = f"SELECT rowid FROM {table} WHERE {table} MATCH ? ORDER BY bm25({table})"
        args = [_q(query)]
        if k is not None:
            sql += " LIMIT ?"
            args.append(k)
        try:
            return [r[0] for r in conn.execute(sql, args)]
        except sqlite3.Error:
            return []


class Unicode61(_Base):
    name, description, tok = "unicode61", "stub default", "unicode61"


class Trigram(_Base):
    name, description, tok = "trigram", "stub trigram", "trigram"


class Missing(_Base):
    name, description = "missing", "always unavailable"

    def available(self):
        return False, "stub: not installed"


SYSTEMS = {s.name: s for s in (Unicode61(), Trigram(), Missing())}
