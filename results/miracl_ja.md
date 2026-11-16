# miracl

- corpus: 100000 docs, queries: 860, seed 42
- SQLite 3.54.1, Python 3.15.2, run at 2026-11-16T05:09:29+00:00
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
| unicode61 | 1.56 | 88.2 | 0.06 | 0.34 | 0 |
| trigram | 7.36 | 139.4 | 3.32 | 20.64 | 0 |
| trigram_like | 7.50 | 139.4 | 3.28 | 20.58 | 0 |
| app_bigram | 5.71 | 155.3 | 26.62 | 63.08 | 0 |
| app_bigram_edge | 6.15 | 174.1 | 51.40 | 92.73 | 0 |
| app_bigram_first | 5.77 | 164.9 | 31.43 | 69.84 | 0 |
| icu_segmenter | 10.77 | 78.4 | 73.10 | 112.54 | 0 |
| better_trigram | 1.35 | 85.6 | 158.79 | 278.20 | 0 |
| fts5_cjk | 4.08 | 103.8 | 27.50 | 65.09 | 0 |
| fts5_cjk_unigram | 5.38 | 125.4 | 40.79 | 93.53 | 0 |

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

