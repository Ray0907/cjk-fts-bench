# miracl

- corpus: 100000 docs, queries: 213, seed 42
- SQLite 3.50.4, Python 3.13.11, run at 2026-11-16T06:07:34+00:00
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
| unicode61 | 2.01 | 71.8 | 0.56 | 6.52 | 0 |
| trigram | 6.24 | 127.0 | 6.68 | 49.24 | 0 |
| trigram_like | 6.34 | 127.0 | 6.55 | 50.73 | 0 |
| app_bigram | 4.54 | 110.0 | 8.24 | 41.41 | 0 |
| app_bigram_edge | 5.89 | 165.7 | 96.15 | 176.52 | 0 |
| app_bigram_first | 4.89 | 138.7 | 37.81 | 88.77 | 0 |
| icu_segmenter | 9.71 | 71.2 | 0.77 | 9.69 | 0 |
| better_trigram | 2.57 | 85.3 | 1.14 | 6.44 | 0 |
| fts5_cjk | 2.84 | 97.1 | 8.25 | 53.31 | 0 |
| fts5_cjk_unigram | 2.96 | 104.7 | 14.45 | 74.35 | 0 |

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

