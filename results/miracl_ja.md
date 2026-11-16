# miracl

- corpus: 100000 docs, queries: 860, seed 42
- SQLite 3.50.4, Python 3.13.11, run at 2026-11-16T06:05:44+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 21.0.0

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.1277 | 0.2700 |
| trigram | 0.4655 | 0.8845 |
| trigram_like | 0.4655 | 0.8845 |
| app_bigram | 0.5357 | 0.9520 |
| app_bigram_edge | 0.5570 | 0.9640 |
| app_bigram_first | 0.5597 | 0.9657 |
| icu_segmenter | 0.5686 | 0.9544 |
| better_trigram | 0.4568 | 0.8808 |
| fts5_cjk | 0.5349 | 0.9530 |
| fts5_cjk_unigram | 0.5361 | 0.9553 |



## Cost

| system | build s | index MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|
| unicode61 | 1.55 | 88.2 | 0.04 | 0.25 | 0 |
| trigram | 6.69 | 139.4 | 2.84 | 18.37 | 0 |
| trigram_like | 6.67 | 139.4 | 2.92 | 18.25 | 0 |
| app_bigram | 5.38 | 155.3 | 25.53 | 57.81 | 0 |
| app_bigram_edge | 5.55 | 174.1 | 48.11 | 84.31 | 0 |
| app_bigram_first | 5.42 | 164.9 | 31.75 | 65.68 | 0 |
| icu_segmenter | 10.72 | 78.4 | 72.78 | 107.11 | 0 |
| better_trigram | 1.24 | 85.6 | 145.86 | 246.90 | 0 |
| fts5_cjk | 3.81 | 103.8 | 25.76 | 59.33 | 0 |
| fts5_cjk_unigram | 4.93 | 125.4 | 38.23 | 85.75 | 0 |

## Failure examples (3 worst queries per system)

**unicode61**

- `1755年のリスボン地震の震源地はどこ？`: relevant=1 returned=0 nDCG@10=0.000
- `2008年の中国雪害で死者は出た？`: relevant=1 returned=0 nDCG@10=0.000
- `4継の男子日本最速タイムは？`: relevant=1 returned=0 nDCG@10=0.000

**trigram**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**trigram_like**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_first**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000
- `CSS/USS アトランタの名称の由来は何`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000
- `CSS/USS アトランタの名称の由来は何`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `4継の男子日本最速タイムは？`: relevant=1 returned=100 nDCG@10=0.000
- `ANSIは企業？`: relevant=1 returned=100 nDCG@10=0.000
- `Billboard Hot 100が初めて掲載されたときの一位をとったシングルは何？`: relevant=1 returned=100 nDCG@10=0.000

