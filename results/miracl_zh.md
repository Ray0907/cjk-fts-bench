# miracl

- corpus: 100000 docs, queries: 393, seed 42
- SQLite 3.54.1, Python 3.15.2, run at 2026-11-16T05:01:43+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 21.0.0

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.0081 | 0.0182 |
| trigram | 0.2514 | 0.6285 |
| trigram_like | 0.2514 | 0.6285 |
| app_bigram | 0.3786 | 0.8521 |
| app_bigram_edge | 0.4287 | 0.8910 |
| app_bigram_first | 0.4231 | 0.8796 |
| jieba | 0.3738 | 0.8390 |
| icu_segmenter | 0.4064 | 0.8346 |
| better_trigram | 0.4192 | 0.8959 |
| fts5_cjk | 0.3777 | 0.8534 |
| fts5_cjk_unigram | 0.3766 | 0.8534 |



## Cost

| system | build s | index MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|
| unicode61 | 1.27 | 68.9 | 0.06 | 0.15 | 0 |
| trigram | 6.47 | 129.7 | 0.52 | 1.50 | 0 |
| trigram_like | 6.76 | 129.7 | 0.53 | 1.60 | 0 |
| app_bigram | 5.32 | 118.4 | 2.25 | 7.60 | 0 |
| app_bigram_edge | 5.76 | 136.4 | 5.35 | 21.00 | 0 |
| app_bigram_first | 5.51 | 127.2 | 3.42 | 15.35 | 0 |
| jieba | 24.98 | 76.6 | 11.46 | 56.81 | 0 |
| icu_segmenter | 9.62 | 63.1 | 11.71 | 53.99 | 0 |
| better_trigram | 1.28 | 68.4 | 50.36 | 84.01 | 0 |
| fts5_cjk | 4.37 | 86.2 | 2.15 | 7.61 | 0 |
| fts5_cjk_unigram | 5.22 | 103.8 | 3.84 | 10.97 | 0 |

## Failure examples (3 worst queries per system)

**unicode61**

- `2008年奥运会在哪一国家举办？`: relevant=3 returned=0 nDCG@10=0.000
- `2020年瑞典羽毛球公开赛奖金多少？`: relevant=1 returned=0 nDCG@10=0.000
- `2022年冬奥会举办城市是哪里？`: relevant=4 returned=0 nDCG@10=0.000

**trigram**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=28 nDCG@10=0.000
- `《圣经》是哪些宗教的经典？`: relevant=5 returned=98 nDCG@10=0.000

**trigram_like**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=28 nDCG@10=0.000
- `《圣经》是哪些宗教的经典？`: relevant=5 returned=98 nDCG@10=0.000

**app_bigram**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `Corsair旗下有哪些产品？`: relevant=1 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `Corsair旗下有哪些产品？`: relevant=1 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_first**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `Corsair旗下有哪些产品？`: relevant=1 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000

**jieba**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000
- `《春秋谷梁传》作者是谁？`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000
- `上海有哪些剧院？`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000
- `上海有哪些大学？`: relevant=3 returned=100 nDCG@10=0.000

**fts5_cjk**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `Corsair旗下有哪些产品？`: relevant=1 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `21世纪美国诞生了哪些著名的女模特？`: relevant=2 returned=100 nDCG@10=0.000
- `Corsair旗下有哪些产品？`: relevant=1 returned=100 nDCG@10=0.000
- `“牛头不对马嘴”是什么意思`: relevant=1 returned=100 nDCG@10=0.000

