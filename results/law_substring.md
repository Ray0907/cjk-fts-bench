# law_substring

- corpus: 46138 docs, queries: 400, seed 42
- SQLite 3.54.1, Python 3.15.2, run at 2026-11-16T04:59:17+00:00
- law_commit: 1e4ee426100b434db58262ed8bff6274d6558498
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 21.0.0

## Quality

| system | word2 recall / zero | word3 recall / zero | word4plus recall / zero | char1 recall / zero | span_nonword recall / zero | overall recall | overall precision |
|---|---|---|---|---|---|---|---|
| unicode61 | 4.1% / 67.0% | 8.6% / 51.0% | 6.6% / 46.0% | 0.4% / 68.0% | 0.0% / 96.0% | 4.9% | 100.0% |
| trigram | 0.0% / 100.0% | 100.0% / 0.0% | 100.0% / 0.0% | 0.0% / 100.0% | 76.0% / 24.0% | 59.5% | 100.0% |
| trigram_like | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% |
| app_bigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 87.1% / 0.0% | 100.0% / 0.0% | 98.4% | 100.0% |
| app_bigram_edge | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% |
| app_bigram_first | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 87.1% / 0.0% | 100.0% / 0.0% | 98.4% | 100.0% |
| jieba | 61.5% / 12.0% | 71.2% / 5.0% | 84.7% / 0.0% | 20.5% / 24.0% | 35.1% / 18.0% | 61.3% | 84.6% |
| icu_segmenter | 68.5% / 6.0% | 85.0% / 2.0% | 96.9% / 0.0% | 25.0% / 18.0% | 42.8% / 6.0% | 71.1% | 75.4% |
| better_trigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% |
| fts5_cjk | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% |
| fts5_cjk_unigram | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% / 0.0% | 100.0% | 100.0% |

Cells are macro means per bucket; 'zero' = share of queries with matches in ground truth but none returned.

## Cost

| system | build s | index MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|
| unicode61 | 0.54 | 32.1 | 0.02 | 0.04 | 0 |
| trigram | 1.66 | 48.0 | 0.05 | 0.24 | 0 |
| trigram_like | 1.58 | 48.0 | 0.16 | 21.65 | 0 |
| app_bigram | 1.54 | 57.7 | 0.11 | 0.76 | 0 |
| app_bigram_edge | 1.67 | 65.9 | 0.14 | 0.87 | 0 |
| app_bigram_first | 1.64 | 61.9 | 0.13 | 1.08 | 0 |
| jieba | 12.90 | 34.8 | 0.10 | 0.68 | 0 |
| icu_segmenter | 3.89 | 29.3 | 0.15 | 1.14 | 0 |
| better_trigram | 0.37 | 32.6 | 0.41 | 1.78 | 0 |
| fts5_cjk | 0.94 | 38.8 | 0.13 | 1.13 | 0 |
| fts5_cjk_unigram | 1.24 | 46.8 | 0.23 | 1.05 | 0 |

## Failure examples (3 worst queries per system)

**unicode61**

- `一時間` (word3): |G|=7 |S|=0 recall=0.000 precision=1.000
- `七條規定` (span_nonword): |G|=316 |S|=0 recall=0.000 precision=1.000
- `上同` (span_nonword): |G|=53 |S|=0 recall=0.000 precision=1.000

**trigram**

- `上同` (span_nonword): |G|=53 |S|=0 recall=0.000 precision=1.000
- `上次` (word2): |G|=7 |S|=0 recall=0.000 precision=1.000
- `且` (char1): |G|=1507 |S|=0 recall=0.000 precision=1.000

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

- `一時間` (word3): |G|=7 |S|=0 recall=0.000 precision=1.000
- `乳哺` (word2): |G|=4 |S|=0 recall=0.000 precision=1.000
- `但至遲不` (span_nonword): |G|=2 |S|=1 recall=0.000 precision=0.000

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

