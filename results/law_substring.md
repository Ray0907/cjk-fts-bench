# law_substring

- corpus: 46138 docs, queries: 400, seed 42
- SQLite 3.53.1, Python 3.13.18, run at 2026-11-18T12:24:37+00:00
- law_commit: 1e4ee426100b434db58262ed8bff6274d6558498
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 13
- jieba 0.42.1, node v22.23.5, icu 78.3, unicode 17.0

## Quality

| system | word2 recall / zero | word3 recall / zero | word4plus recall / zero | char1 recall / zero | span_nonword recall / zero | overall recall | overall precision |
|---|---|---|---|---|---|---|---|
| unicode61 | 4.1% / 67.0% | 8.6% / 51.0% | 6.6% / 46.0% | 0.4% / 68.0% | 0.0% / 96.0% | 4.9% | 100.0% (n=154) |
| trigram | 0.0% / 100.0% | 100.0% / 0.0% | 100.0% / 0.0% | 0.0% / 100.0% | 76.0% / 24.0% | 59.5% | 100.0% (n=238) |
| trigram_like | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% (n=400) |
| app_bigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 87.1% / 0.0% | 100.0% / 0.0% | 98.4% | 100.0% (n=400) |
| app_bigram_edge | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% (n=400) |
| app_bigram_first | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 87.1% / 0.0% | 100.0% / 0.0% | 98.4% | 100.0% (n=400) |
| jieba | 61.5% / 12.0% | 71.2% / 5.0% | 84.7% / 0.0% | 20.5% / 24.0% | 35.1% / 18.0% | 61.3% | 83.0% (n=362) |
| jieba_big | 70.9% / 14.0% | 91.6% / 3.0% | 95.1% / 1.0% | 13.0% / 38.0% | 44.6% / 14.0% | 71.6% | 87.5% (n=356) |
| icu_segmenter | 68.5% / 6.0% | 85.0% / 2.0% | 96.9% / 0.0% | 25.0% / 18.0% | 42.8% / 6.0% | 71.1% | 74.1% (n=380) |
| better_trigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% (n=400) |
| fts5_cjk | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% (n=400) |
| fts5_cjk_unigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% (n=400) |

Cells are macro means per bucket; 'zero' = share of queries with matches in ground truth but none returned. Precision is undefined for a query that returns nothing, so it is the mean over the n queries that returned at least one article.

## Cost

| system | build s | index MB (default) | index only MB | index + raw MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|---|---|
| unicode61 | 0.67 | 32.1 | 12.4 | 32.1 | 0.03 | 0.08 | 0 |
| trigram | 3.01 | 48.0 | 28.4 | 48.0 | 0.09 | 0.53 | 0 |
| trigram_like | 3.07 | 48.0 | 28.4 | 48.0 | 0.22 | 31.66 | 0 |
| app_bigram | 2.97 | 57.7 | 16.0 | 35.7 | 0.16 | 1.64 | 0 |
| app_bigram_edge | 2.71 | 65.9 | 19.1 | 38.8 | 0.26 | 2.00 | 0 |
| app_bigram_first | 2.69 | 61.9 | 17.6 | 37.3 | 0.16 | 1.26 | 0 |
| jieba | 22.90 | 34.8 | 9.3 | 28.9 | 0.18 | 1.03 | 0 |
| jieba_big | 17.30 | 38.6 | 9.6 | 29.3 | 0.13 | 1.10 | 0 |
| icu_segmenter | 9.45 | 29.3 | 8.3 | 27.9 | 0.25 | 2.22 | 0 |
| better_trigram | 0.70 | 32.6 | 12.9 | 32.6 | 0.72 | 3.68 | 0 |
| fts5_cjk | 2.13 | 38.8 | 19.1 | 38.8 | 0.19 | 1.44 | 0 |
| fts5_cjk_unigram | 2.78 | 46.8 | 27.2 | 46.8 | 0.36 | 1.92 | 0 |

Index size, MB = 10^6 bytes, after VACUUM. default = the FTS5 table with its stored copy of what the system indexes (transformed text for app-level systems, original text otherwise). index only = the same table with content=''. index + raw = index only plus one plain table holding the original text (19.7 MB).

## Failure examples (3 worst queries per system)

**unicode61**

- `一時間` (word3): |G|=7 |S|=0 recall=0.000 precision=n/a
- `七條規定` (span_nonword): |G|=316 |S|=0 recall=0.000 precision=n/a
- `上同` (span_nonword): |G|=53 |S|=0 recall=0.000 precision=n/a

**trigram**

- `上同` (span_nonword): |G|=53 |S|=0 recall=0.000 precision=n/a
- `上次` (word2): |G|=7 |S|=0 recall=0.000 precision=n/a
- `且` (char1): |G|=1507 |S|=0 recall=0.000 precision=n/a

**trigram_like**

- `一時間` (word3): |G|=7 |S|=7 recall=1.000 precision=1.000
- `一致性` (word3): |G|=11 |S|=11 recall=1.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=316 recall=1.000 precision=1.000

**app_bigram**

- `樑` (char1): |G|=50 |S|=20 recall=0.400 precision=1.000
- `勉` (char1): |G|=4 |S|=2 recall=0.500 precision=1.000
- `誼` (char1): |G|=8 |S|=4 recall=0.500 precision=1.000

**app_bigram_edge**

- `一時間` (word3): |G|=7 |S|=7 recall=1.000 precision=1.000
- `一致性` (word3): |G|=11 |S|=11 recall=1.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=316 recall=1.000 precision=1.000

**app_bigram_first**

- `樑` (char1): |G|=50 |S|=20 recall=0.400 precision=1.000
- `勉` (char1): |G|=4 |S|=2 recall=0.500 precision=1.000
- `誼` (char1): |G|=8 |S|=4 recall=0.500 precision=1.000

**jieba**

- `一時間` (word3): |G|=7 |S|=0 recall=0.000 precision=n/a
- `乳哺` (word2): |G|=4 |S|=0 recall=0.000 precision=n/a
- `但至遲不` (span_nonword): |G|=2 |S|=1 recall=0.000 precision=0.000

**jieba_big**

- `乳哺` (word2): |G|=4 |S|=0 recall=0.000 precision=n/a
- `但至遲不` (span_nonword): |G|=2 |S|=11 recall=0.000 precision=0.000
- `作保` (word2): |G|=7 |S|=0 recall=0.000 precision=n/a

**icu_segmenter**

- `人處以罰` (span_nonword): |G|=3 |S|=111 recall=0.000 precision=0.000
- `但至遲不` (span_nonword): |G|=2 |S|=10 recall=0.000 precision=0.000
- `作保` (word2): |G|=7 |S|=5 recall=0.000 precision=0.000

**better_trigram**

- `一時間` (word3): |G|=7 |S|=7 recall=1.000 precision=1.000
- `一致性` (word3): |G|=11 |S|=11 recall=1.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=316 recall=1.000 precision=1.000

**fts5_cjk**

- `一時間` (word3): |G|=7 |S|=7 recall=1.000 precision=1.000
- `一致性` (word3): |G|=11 |S|=11 recall=1.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=316 recall=1.000 precision=1.000

**fts5_cjk_unigram**

- `一時間` (word3): |G|=7 |S|=7 recall=1.000 precision=1.000
- `一致性` (word3): |G|=11 |S|=11 recall=1.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=316 recall=1.000 precision=1.000

