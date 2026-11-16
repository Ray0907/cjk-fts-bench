#!/usr/bin/env bash
# Build the C tokenizers as loadable SQLite extensions into ext/build/.
# Repos are cloned into ext/src/ and compiled directly with gcc; no scripts from them are run.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p src build

FTS5_CJK_REF=${FTS5_CJK_REF:-79c52dafec1d403ab69e28f89e8c493a8e5ff02b}
BETTER_TRIGRAM_REF=${BETTER_TRIGRAM_REF:-851f99f3e14f9dc0606edf40423406d1a2ea2b89}
SQLITE_TAG=${SQLITE_TAG:-version-3.53.1}

fetch() {  # fetch <url> <dir> <ref>
  [ -d "$2/.git" ] || git clone -q "$1" "$2"
  git -C "$2" fetch -q --depth 1 origin "$3" 2>/dev/null || true
  git -C "$2" -c advice.detachedHead=false checkout -q "$3"
}

fetch https://github.com/Ray0907/fts5-cjk src/fts5-cjk "$FTS5_CJK_REF"
fetch https://github.com/streetwriters/sqlite-better-trigram src/better-trigram "$BETTER_TRIGRAM_REF"
if [ ! -f src/sqlite/ext/fts5/fts5_unicode2.c ]; then
  git clone -q --depth 1 --branch "$SQLITE_TAG" --filter=blob:none --sparse \
    https://github.com/sqlite/sqlite src/sqlite 2>/dev/null
  git -C src/sqlite sparse-checkout set ext/fts5
fi

# macOS needs SQLite symbols resolved at load time.
LDFLAGS_EXT=""
[ "$(uname)" = "Darwin" ] && LDFLAGS_EXT="-undefined dynamic_lookup"

# fts5-cjk ships its own sqlite3.h / sqlite3ext.h in include/.
gcc -O2 -Wall -fPIC -Isrc/fts5-cjk/include -shared $LDFLAGS_EXT -o build/fts5_cjk.so src/fts5-cjk/cjk.c
# better-trigram needs fts5_unicode2.c from the SQLite source tree. sqlite3ext.h comes from
# fts5-cjk/include, listed first: on macOS the SDK copy is older and the .so segfaults on load.
gcc -Os -Wall -fPIC -shared $LDFLAGS_EXT -Isrc/fts5-cjk/include -Isrc/sqlite/ext/fts5 -o build/better_trigram.so \
  src/better-trigram/better-trigram.c -lm

{
  echo "fts5-cjk $(git -C src/fts5-cjk rev-parse HEAD)"
  echo "sqlite-better-trigram $(git -C src/better-trigram rev-parse HEAD)"
  echo "sqlite (for fts5_unicode2.c) $SQLITE_TAG $(git -C src/sqlite rev-parse HEAD)"
  echo "gcc $(gcc -dumpversion)"
} > build/VERSIONS.txt
echo "built: $(ls build/*.so | tr '\n' ' ')"
