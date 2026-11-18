# miracl

- corpus: 100000 docs, queries: 868, seed 42
- SQLite 3.53.1, Python 3.13.18, run at 2026-11-18T12:45:03+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 11
- jieba 0.42.1, node v22.23.5, icu 78.3, unicode 17.0

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.3462 | 0.6421 |
| trigram | 0.4588 | 0.8319 |
| trigram_like | 0.4588 | 0.8319 |
| app_bigram | 0.4885 | 0.9122 |
| app_bigram_edge | 0.5059 | 0.9230 |
| app_bigram_first | 0.5105 | 0.9236 |
| icu_segmenter | 0.3546 | 0.6601 |
| better_trigram | 0.3993 | 0.8188 |
| fts5_cjk | 0.4835 | 0.9125 |
| fts5_cjk_unigram | 0.4830 | 0.9118 |
| fts5_cjk_qfirst | 0.5028 | 0.9239 |
| fts5_cjk_qedge | 0.5059 | 0.9230 |



## Cost

| system | build s | index MB (default) | index only MB | index + raw MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|---|---|
| unicode61 | 1.75 | 75.1 | 26.0 | 75.1 | 0.47 | 5.68 | 0 |
| trigram | 6.56 | 133.2 | 84.0 | 133.2 | 6.29 | 40.12 | 0 |
| trigram_like | 6.26 | 133.2 | 84.0 | 133.2 | 6.33 | 40.13 | 0 |
| app_bigram | 4.00 | 115.2 | 32.6 | 81.8 | 7.63 | 40.13 | 0 |
| app_bigram_edge | 5.13 | 173.7 | 52.3 | 101.4 | 82.98 | 191.20 | 0 |
| app_bigram_first | 4.71 | 145.0 | 43.2 | 92.4 | 34.62 | 89.87 | 0 |
| icu_segmenter | 11.35 | 74.4 | 25.7 | 74.9 | 0.80 | 11.13 | 0 |
| better_trigram | 2.75 | 88.8 | 39.6 | 88.8 | 1.22 | 8.15 | 0 |
| fts5_cjk | 2.69 | 101.4 | 52.3 | 101.5 | 9.24 | 54.06 | 0 |
| fts5_cjk_unigram | 3.60 | 109.2 | 60.0 | 109.2 | 15.42 | 71.62 | 0 |
| fts5_cjk_qfirst | 3.27 | 101.4 | 52.3 | 101.5 | 43.22 | 100.37 | 0 |
| fts5_cjk_qedge | 3.28 | 101.4 | 52.3 | 101.5 | 83.09 | 194.08 | 0 |

Index size, MB = 10^6 bytes, after VACUUM. default = the FTS5 table with its stored copy of what the system indexes (transformed text for app-level systems, original text otherwise). index only = the same table with content=''. index + raw = index only plus one plain table holding the original text (49.2 MB).

## Failure examples (3 worst queries per system)

**unicode61**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2018년 중국에서 가장 높은 건물은 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**trigram**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2018년 중국에서 가장 높은 건물은 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

**trigram_like**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2018년 중국에서 가장 높은 건물은 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계대전은 몇 년도에 일어났는가?`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_first**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2018년 중국에서 가장 높은 건물은 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `1865년 일본 천황은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계대전은 몇 년도에 일어났는가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계대전은 몇 년도에 일어났는가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_qfirst**

- `1865년 일본 천황은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_qedge**

- `1987년 미국 대통령은 누구인가요?`: relevant=1 returned=100 nDCG@10=0.000
- `2019년 미국의 대통령은 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `2차 세계 대전에 참전했던 동아시아 국가는 무엇인가?`: relevant=1 returned=100 nDCG@10=0.000

