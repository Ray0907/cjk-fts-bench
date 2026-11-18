# miracl

- corpus: 100000 docs, queries: 1312, seed 42
- SQLite 3.53.1, Python 3.13.18, run at 2026-11-18T10:08:44+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 11

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.0151 | 0.0276 |
| trigram | 0.2476 | 0.6232 |
| trigram_like | 0.2476 | 0.6232 |
| app_bigram | 0.3475 | 0.8307 |
| app_bigram_edge | 0.3887 | 0.8638 |
| app_bigram_first | 0.3816 | 0.8658 |
| jieba | 0.3743 | 0.8276 |
| icu_segmenter | 0.3909 | 0.8280 |
| better_trigram | 0.4006 | 0.8730 |
| fts5_cjk | 0.3435 | 0.8326 |
| fts5_cjk_unigram | 0.3462 | 0.8327 |



## Cost

| system | build s | index MB (default) | index only MB | index + raw MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|---|---|
| unicode61 | 1.43 | 71.7 | 32.6 | 71.7 | 0.05 | 0.23 | 0 |
| trigram | 12.14 | 135.2 | 96.1 | 135.2 | 0.64 | 2.82 | 0 |
| trigram_like | 9.34 | 135.2 | 96.1 | 135.2 | 0.55 | 2.39 | 0 |
| app_bigram | 7.72 | 122.3 | 43.0 | 82.0 | 2.76 | 9.52 | 0 |
| app_bigram_edge | 7.25 | 142.3 | 50.5 | 89.6 | 5.38 | 19.97 | 0 |
| app_bigram_first | 6.75 | 131.6 | 46.2 | 85.2 | 3.82 | 18.17 | 0 |
| jieba | 29.25 | 80.0 | 26.6 | 65.6 | 11.81 | 53.27 | 0 |
| icu_segmenter | 12.31 | 65.6 | 23.0 | 62.0 | 11.96 | 49.20 | 0 |
| better_trigram | 1.24 | 71.2 | 32.1 | 71.2 | 46.36 | 79.80 | 0 |
| fts5_cjk | 5.72 | 89.6 | 50.5 | 89.6 | 2.16 | 7.63 | 0 |
| fts5_cjk_unigram | 6.41 | 107.2 | 68.1 | 107.2 | 3.80 | 10.69 | 0 |

Index size, MB = 10^6 bytes, after VACUUM. default = the FTS5 table with its stored copy of what the system indexes (transformed text for app-level systems, original text otherwise). index only = the same table with content=''. index + raw = index only plus one plain table holding the original text (39.1 MB).

## Failure examples (3 worst queries per system)

**unicode61**

- `1995年美国在任总统是谁？`: relevant=1 returned=0 nDCG@10=0.000
- `2000夏季奥运会在哪里举办？`: relevant=4 returned=0 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=0 nDCG@10=0.000

**trigram**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**trigram_like**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_first**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**jieba**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年澳洲羽毛球公开赛奖金多少？`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000
- `AKB48组合2010年举办过多少场巡演？`: relevant=1 returned=100 nDCG@10=0.000
- `CLAMP创作了哪些漫画？`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000
- `DC漫画有哪些电影化了?`: relevant=1 returned=100 nDCG@10=0.000
- `DNA有哪些主要类别？`: relevant=4 returned=100 nDCG@10=0.000

**fts5_cjk**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `1995年美国在任总统是谁？`: relevant=1 returned=100 nDCG@10=0.000
- `2008年北京奥运会获得金牌数最多的国家是哪个？`: relevant=1 returned=100 nDCG@10=0.000
- `2012年夏季奥运会在哪里举办？`: relevant=1 returned=100 nDCG@10=0.000

