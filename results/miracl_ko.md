# miracl

- corpus: 100000 docs, queries: 213, seed 42
- SQLite 3.54.1, Python 3.15.2, run at 2026-11-16T05:11:28+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 21.0.0

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.3518 | 0.6348 |
| trigram | 0.4733 | 0.8614 |
| trigram_like | 0.4733 | 0.8614 |
| app_bigram | 0.5100 | 0.9475 |
| app_bigram_edge | 0.5472 | 0.9573 |
| app_bigram_first | 0.5487 | 0.9701 |
| icu_segmenter | 0.3594 | 0.6594 |
| better_trigram | 0.4030 | 0.8329 |
| fts5_cjk | 0.5056 | 0.9459 |
| fts5_cjk_unigram | 0.5074 | 0.9463 |



## Cost

| system | build s | index MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|
| unicode61 | 2.20 | 71.8 | 0.63 | 6.49 | 0 |
| trigram | 7.06 | 127.0 | 8.20 | 61.88 | 0 |
| trigram_like | 7.02 | 127.0 | 6.76 | 53.96 | 0 |
| app_bigram | 5.09 | 110.0 | 8.06 | 47.03 | 0 |
| app_bigram_edge | 5.73 | 165.7 | 108.53 | 211.91 | 0 |
| app_bigram_first | 5.07 | 138.7 | 40.06 | 102.26 | 0 |
| icu_segmenter | 9.99 | 71.2 | 0.81 | 12.71 | 0 |
| better_trigram | 2.92 | 85.3 | 1.23 | 7.85 | 0 |
| fts5_cjk | 3.00 | 97.1 | 8.46 | 57.28 | 0 |
| fts5_cjk_unigram | 3.38 | 104.7 | 15.74 | 74.83 | 0 |

## Failure examples (3 worst queries per system)

**unicode61**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `ATP란?`: relevant=2 returned=0 nDCG@10=0.000
- `국회의사당이 있는 도시는?`: relevant=5 returned=100 nDCG@10=0.000

**trigram**

- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `기독교의 시작이 되는 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `나일 강의 길이는?`: relevant=1 returned=100 nDCG@10=0.000

**trigram_like**

- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `기독교의 시작이 되는 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `나일 강의 길이는?`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `나치를 만든 지도자는 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `나치를 만든 지도자는 누구인가?`: relevant=1 returned=100 nDCG@10=0.000
- `남북전쟁은 몇 년도에 일어났는가?`: relevant=5 returned=100 nDCG@10=0.000

**app_bigram_first**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `나치를 만든 지도자는 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `국회의사당이 있는 도시는?`: relevant=5 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `1945년 일본 천황은 누구인가요?`: relevant=3 returned=100 nDCG@10=0.000
- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `나치를 만든 지도자는 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `2차 세계전쟁이 시작된 나라는 어디인가?`: relevant=2 returned=100 nDCG@10=0.000
- `그리스 신화에 등장하는 신은 몇 명인가?`: relevant=1 returned=100 nDCG@10=0.000
- `나치를 만든 지도자는 누구인가?`: relevant=1 returned=100 nDCG@10=0.000

