# cjk_rank_query() against the benchmark's Python rule: top-100 identity

`fts5_cjk_qfirst` and `fts5_cjk_qedge` were measured with the benchmark's Python rule
(`rank_keep_run_first` / `rank_drop_run_unigrams = False` in `bench/systems.py`). This check asks whether
fts5-cjk's own C function gives the same ranking: on the same fts5_cjk index, does
`MATCH cjk_rank_query(strip_punct(q), mode)` return the same top-100 rowids, in the same order, as the
Python rule (`'first'` ↔ `fts5_cjk_qfirst`, `'edge'` ↔ `fts5_cjk_qedge`)?

- C function: fts5-cjk `cjk.c` at commit ec39d0c (sha256 `4bb2fe2f…a925dc`; later commits change only a
  comment and tests), built with gcc -O2 in the Linux VM used for the train runs.
- Index: `bench.run.build_index` with the pinned fts5-cjk 79c52da. Its MD5 equals the variant experiment's
  (`audit/qfirst/index_md5.txt`).
- Queries: every query of the MIRACL train samples (zh 1,312, ja 3,477, ko 868).
- Script: `validate.py`; summary with the differing queries: `validation_summary.json`.

| language | mode | queries | identical top-100 | identical term set | most terms in one query |
|---|---|---|---|---|---|
| zh | first | 1,312 | 1,312 | 1,312 | 22 |
| zh | edge | 1,312 | 1,312 | 1,312 | 24 |
| ja | first | 3,477 | **3,475** | 3,475 | 40 |
| ja | edge | 3,477 | 3,477 | 3,477 | 45 |
| ko | first | 868 | 868 | 868 | 76 |
| ko | edge | 868 | 868 | 868 | 97 |
| all | first | 5,657 | 5,655 | 5,655 | |
| all | edge | 5,657 | 5,657 | 5,657 | |

The two `'first'` differences (ja qid 303 and 386, both about 『日本の熱い日々 謀殺・下山事件』) come from the
benchmark side. Its CJK class (`CJK_CLASS`) leaves out 々〆〇, so `drop_run_unigrams` treats the run-final 々 of
日本の熱い日々 as a run of its own and keeps it. fts5-cjk counts 々 as part of the run, so for the tokenizer it is
that run's last character, and `cjk_rank_query(..., 'first')` leaves it out. Both queries return the same top-10
set (for qid 386 the order differs at ranks 3 and 4). Fixing the class would change `app_bigram`'s dev results, which cannot be re-run here
(`docs/follow-ups.md`).

The 128-term cap in `cjk_rank_query()` was sized from these queries: a first build with a cap of 64 truncated
7 Korean `'first'` and 16 `'edge'` queries (up to 97 distinct terms). The table above is from the 128 build.
