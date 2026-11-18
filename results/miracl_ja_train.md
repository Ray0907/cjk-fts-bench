# miracl

- corpus: 100000 docs, queries: 3477, seed 42
- SQLite 3.53.1, Python 3.13.18, run at 2026-11-18T10:19:55+00:00
- fts5-cjk 79c52dafec1d403ab69e28f89e8c493a8e5ff02b
- sqlite-better-trigram 851f99f3e14f9dc0606edf40423406d1a2ea2b89
- sqlite (for fts5_unicode2.c) version-3.53.1 ccd445d76a9362c63add000354fac84ba9022176
- gcc 11

## Quality

| system | nDCG@10 | Recall@100 |
|---|---|---|
| unicode61 | 0.1262 | 0.2571 |
| trigram | 0.4372 | 0.8762 |
| trigram_like | 0.4372 | 0.8762 |
| app_bigram | 0.5204 | 0.9440 |
| app_bigram_edge | 0.5462 | 0.9592 |
| app_bigram_first | 0.5467 | 0.9590 |
| icu_segmenter | 0.5615 | 0.9580 |
| better_trigram | 0.4262 | 0.8583 |
| fts5_cjk | 0.5190 | 0.9454 |
| fts5_cjk_unigram | 0.5202 | 0.9453 |
| fts5_cjk_qfirst | 0.5398 | 0.9596 |
| fts5_cjk_qedge | 0.5404 | 0.9591 |



## Cost

| system | build s | index MB (default) | index only MB | index + raw MB | p50 ms | p95 ms | search errors |
|---|---|---|---|---|---|---|---|
| unicode61 | 1.97 | 107.8 | 46.9 | 107.8 | 0.07 | 0.44 | 0 |
| trigram | 17.31 | 171.0 | 110.1 | 171.0 | 3.99 | 25.28 | 0 |
| trigram_like | 11.21 | 171.0 | 110.1 | 171.0 | 3.66 | 22.60 | 0 |
| app_bigram | 7.73 | 191.0 | 55.8 | 116.6 | 27.58 | 58.99 | 0 |
| app_bigram_edge | 7.60 | 213.2 | 63.8 | 124.6 | 46.03 | 84.43 | 0 |
| app_bigram_first | 7.71 | 201.7 | 59.6 | 120.5 | 31.04 | 64.47 | 0 |
| icu_segmenter | 13.77 | 95.5 | 28.3 | 89.2 | 64.32 | 95.66 | 0 |
| better_trigram | 1.84 | 103.7 | 42.9 | 103.8 | 134.74 | 246.35 | 0 |
| fts5_cjk | 4.99 | 125.1 | 64.3 | 125.1 | 24.81 | 51.51 | 0 |
| fts5_cjk_unigram | 5.62 | 152.5 | 91.7 | 152.5 | 38.54 | 81.93 | 0 |
| fts5_cjk_qfirst | 4.42 | 125.1 | 64.3 | 125.1 | 28.79 | 56.84 | 0 |
| fts5_cjk_qedge | 4.37 | 125.1 | 64.3 | 125.1 | 42.79 | 73.22 | 0 |

Index size, MB = 10^6 bytes, after VACUUM. default = the FTS5 table with its stored copy of what the system indexes (transformed text for app-level systems, original text otherwise). index only = the same table with content=''. index + raw = index only plus one plain table holding the original text (60.9 MB).

## Failure examples (3 worst queries per system)

**unicode61**

- `1755年のリスボン地震で津波は併発した？`: relevant=5 returned=0 nDCG@10=0.000
- `17世紀イギリス・プリマスから出航した清教徒を乗せた船の名前はなんですか？`: relevant=1 returned=0 nDCG@10=0.000
- `1992年ウィンザー城火災の火災の原因は何？`: relevant=1 returned=0 nDCG@10=0.000

**trigram**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**trigram_like**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_edge**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**app_bigram_first**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**icu_segmenter**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』の監督は誰`: relevant=1 returned=100 nDCG@10=0.000

**better_trigram**

- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』の監督は誰`: relevant=1 returned=100 nDCG@10=0.000
- `B-CASが導入されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_unigram**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_qfirst**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

**fts5_cjk_qedge**

- `2019年、アメリカ合衆国の大統領は誰ですか？`: relevant=2 returned=100 nDCG@10=0.000
- `2024年夏季オリンピックの開催地はどこ`: relevant=3 returned=100 nDCG@10=0.000
- `ABCのテレビシリーズ『LOST』が最初に放送されたのはいつ`: relevant=1 returned=100 nDCG@10=0.000

