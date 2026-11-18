# cjk-fts-bench

Which SQLite FTS5 setup should you use for Chinese, Japanese and Korean text?

SQLite's default full-text tokenizer barely works for CJK, and projects keep shipping their own fixes:
trigram, `LIKE` fallbacks, bigram rewrites, jieba, `Intl.Segmenter`. This benchmark runs the common
setups on the same data and reports where each one breaks, with paired significance tests instead
of a single average.

Write-up of the results: [SQLite FTS5 for Chinese, Japanese, Korean: 11 tokenizers tested](https://raytien.me/writing/cjk-fts-bench/)
([繁體中文](https://raytien.me/writing/cjk-fts-bench/zh/)).

- **12 setups**, from the FTS5 defaults to C extensions and app-level segmenters, plus two
  ranking-query variants of fts5-cjk
- **2 tasks**: exact substring search over 46,138 Taiwan law articles (Traditional Chinese), and
  ranking on [MIRACL](https://github.com/project-miracl/miracl) with human relevance labels in
  Chinese, Japanese and Korean (100,000 passages each), on the dev queries the benchmark was built
  with and on held-out train queries
- Every number in the tables is generated from `results/*.json` by `python -m bench.leaderboard`;
  the statistics behind the text are in [`results/stats.md`](results/stats.md) (`python -m bench.stats`),
  and [`docs/claims-audit.md`](docs/claims-audit.md) traces each statement below to its source

> **Disclosure.** The maintainer of this benchmark also wrote one of the systems,
> [fts5-cjk](https://github.com/Ray0907/fts5-cjk). It does not win. Problems found during
> development and by an independent audit, two of which favoured fts5-cjk, are documented in
> [Corrections](#corrections). Reviews from other tokenizer authors are welcome.

## Which setup should I use?

The ranking advice rests on two sets of queries: MIRACL **dev**, which the benchmark was developed on
(`app_bigram_first` was chosen after looking at it), and MIRACL **train**, held out and added after an
independent audit (2026-11). Where the two disagree, the held-out result decides. "Within ±0.01" below
means the 90% confidence interval of the difference lies inside ±0.01 nDCG@10; a difference that is
merely not significant is not called a tie.

- **Don't use the defaults for CJK.** `unicode61` treats a whole run of Han characters as one
  token (nDCG@10 0.008 on Chinese dev, 0.015 on train). The built-in `trigram` tokenizer returns
  nothing for queries under 3 characters, and most Chinese words are 2 characters (85% of the
  dictionary headwords that occur in at least 3 law articles).
- **No setup ranks best in all three languages.** On the held-out queries the top system is
  `better_trigram` in Chinese (0.401), `icu_segmenter` in Japanese (0.562) and `app_bigram_first`
  in Korean (0.511). The Chinese lead is not clear-cut: `icu_segmenter`, `app_bigram_edge`,
  `fts5_cjk_qedge` and `app_bigram_first` are not significantly below `better_trigram` after Holm
  correction. In Japanese,
  ICU is significantly above every other system.
- **One setup for all three languages: bigrams plus each CJK run's first character, added to
  documents and to queries (`app_bigram_first`).** It was chosen on dev, and its gain over plain
  bigrams holds on the held-out queries: +0.034 (zh), +0.026 (ja), +0.022 (ko), each 95% interval
  above zero. It is the top system only in Korean: in Chinese it is 0.019 below `better_trigram`
  (p=0.019, 0.075 after Holm correction) and in Japanese 0.015 below ICU (significant). Cost over
  plain bigrams: inverted index +7% (zh), +7% (ja), +33% (ko) on the train samples, or +4%, +3%,
  +13% counting one raw copy of the text; ranking queries p50 zh 3.3 vs 2.0 ms, ja 32 vs 26 ms,
  ko 38 vs 8 ms (dev, one run). Like plain bigrams, it misses a single character that occurs only
  at the end of a run (law recall 87.1% for single-character queries, 98.4% overall).
- **Also the last character (`app_bigram_edge`):** finds every exact match. Its ranking is within
  ±0.01 of `app_bigram_first` in Japanese and Korean (held out) and slightly ahead in Chinese
  (+0.007, p=0.025 uncorrected). Cost over plain bigrams: inverted index +18% (zh), +14% (ja),
  +60% (ko), or +9%, +7%, +24% with a raw copy; p50 zh 5.0 ms, ja 48 ms, ko 96 ms (dev). Choose
  it if you need exact single-character matches, or for Chinese.
- **Japanese only:** ICU word segmentation (`Intl.Segmenter`) has the highest Japanese score on
  both query sets (0.569 dev, 0.562 train) and the smallest index. Cost: it needs Node.js and
  ranking queries are slow (p50 73 ms on ja vs 26 ms for plain bigrams). Don't use it for Korean:
  it splits hangul only at spaces, so 검색을 never matches 검색.
- **Every exact match, little code:** `trigram` plus a `LIKE` fallback for short queries finds
  everything, but the fallback is a full scan, so it should slow down as data grows (p95 32 ms on
  46k articles in the latest run; scaling was not measured). Its ranking is poor (nDCG@10 0.251 on
  zh, same as `trigram`). fts5-cjk and better-trigram also find everything, without the scan.
- **No application code:** a C tokenizer. fts5-cjk's ranking is within ±0.01 of app-level bigrams
  in every language on the held-out queries, slightly below them (−0.004 zh, −0.001 ja, −0.005 ko);
  on dev it is within ±0.01 in zh and ja, and the Korean interval is too wide to tell. Its inverted
  index is larger than app-level bigrams' (+18% zh, +15% ja, +60% ko, +20% law), because it also
  indexes each run's first and last character; with one raw copy of the text the difference is
  +9%, +7%, +24%, +9%. (The benchmark used to report it as smaller: its old size measure counted
  the bigram-rewritten text that app-level tables store.) Unlike app-level bigrams, `highlight()` and
  `snippet()` return the original text. Ranking was measured with the benchmark's common query rule,
  which leaves out the run-edge characters fts5-cjk indexes. A ranking query that also sends each
  run's first character (`fts5_cjk_qfirst`, what the `cjk_rank_query()` helper proposed for fts5-cjk
  produces) adds +0.033 (zh), +0.021 (ja), +0.019 (ko) on held-out queries with the same index. That
  leaves it 0.005 to 0.008 below `app_bigram_first`: significant, but inside the ±0.015 bound set
  before the test. It costs query time (p50 ×1.7 zh, ×1.2 ja, ×5.0 ko against fts5_cjk). better-trigram ranks at the top in Chinese but is slow (p50 50 ms on
  zh) and falls behind in Japanese and Korean.

## Leaderboard

<!-- LEADERBOARD:START -->
MIRACL columns are nDCG@10. **dev** = the MIRACL dev queries the benchmark was developed on (`app_bigram_first` was chosen after looking at them); **train** = MIRACL train queries, held out: never used to choose or tune a system. Absolute values are not comparable across splits (different queries and a different 100,000-passage sample); compare systems within a column. Best value per column in bold. n/a = not run: jieba segments Chinese only; `jieba_big` uses jieba's Traditional Chinese dictionary and runs on the law task only; systems added after the dev run have no dev numbers; `fts5_cjk_qfirst`/`_qedge` change only fts5_cjk's ranking query, so their substring results are fts5_cjk's. Latency is from one run (see Limits).

| system | Law substring recall | MIRACL zh dev | MIRACL zh train | MIRACL ja dev | MIRACL ja train | MIRACL ko dev | MIRACL ko train | zh dev p50 ms |
|---|---|---|---|---|---|---|---|---|
| `unicode61` | 4.9% | 0.008 | 0.015 | 0.128 | 0.126 | 0.352 | 0.346 | **0.04** |
| `trigram` | 59.5% | 0.251 | 0.248 | 0.465 | 0.437 | 0.473 | 0.459 | 0.46 |
| `trigram_like` | **100.0%** | 0.251 | 0.248 | 0.465 | 0.437 | 0.473 | 0.459 | 0.42 |
| `app_bigram` | 98.4% | 0.379 | 0.348 | 0.536 | 0.520 | 0.510 | 0.489 | 2.03 |
| `app_bigram_edge` | **100.0%** | **0.429** | 0.389 | 0.557 | 0.546 | 0.547 | 0.506 | 5.02 |
| `app_bigram_first` | 98.4% | 0.423 | 0.382 | 0.560 | 0.547 | **0.549** | **0.511** | 3.31 |
| `jieba` | 61.3% | 0.374 | 0.374 | n/a | n/a | n/a | n/a | 11.35 |
| `jieba_big` | 71.6% | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `icu_segmenter` | 71.1% | 0.406 | 0.391 | **0.569** | **0.562** | 0.359 | 0.355 | 12.40 |
| `better_trigram` | **100.0%** | 0.419 | **0.401** | 0.457 | 0.426 | 0.403 | 0.399 | 50.36 |
| `fts5_cjk` | **100.0%** | 0.378 | 0.343 | 0.535 | 0.519 | 0.506 | 0.484 | 2.02 |
| `fts5_cjk_unigram` | **100.0%** | 0.377 | 0.346 | 0.536 | 0.520 | 0.507 | 0.483 | 3.76 |
| `fts5_cjk_qfirst` | n/a | n/a | 0.377 | n/a | 0.540 | n/a | 0.503 | n/a |
| `fts5_cjk_qedge` | n/a | n/a | 0.389 | n/a | 0.540 | n/a | 0.506 | n/a |

Law substring recall by query type. The overall figure depends on this mix: 162 of the 400 queries (40.5%) are one or two characters long.

| system | 1 char (n=50) | 2-char words (n=100) | 3-char words (n=100) | 4+ char words (n=100) | non-word spans (n=50) | all (n=400) |
|---|---|---|---|---|---|---|
| `unicode61` | 0.4% | 4.1% | 8.6% | 6.6% | 0.0% | 4.9% |
| `trigram` | 0.0% | 0.0% | **100.0%** | **100.0%** | 76.0% | 59.5% |
| `trigram_like` | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| `app_bigram` | 87.1% | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 98.4% |
| `app_bigram_edge` | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| `app_bigram_first` | 87.1% | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 98.4% |
| `jieba` | 20.5% | 61.5% | 71.2% | 84.7% | 35.1% | 61.3% |
| `jieba_big` | 13.0% | 70.9% | 91.6% | 95.1% | 44.6% | 71.6% |
| `icu_segmenter` | 25.0% | 68.5% | 85.0% | 96.9% | 42.8% | 71.1% |
| `better_trigram` | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| `fts5_cjk` | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| `fts5_cjk_unigram` | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |

Paired difference in nDCG@10 against `app_bigram`, MIRACL **dev** (95% bootstrap CI, randomization p):

| system | zh | ja | ko |
|---|---|---|---|
| `unicode61` | **-0.370** [-0.403, -0.339] p≤0.0001 | **-0.408** [-0.432, -0.382] p≤0.0001 | **-0.158** [-0.197, -0.120] p≤0.0001 |
| `trigram` | **-0.127** [-0.151, -0.104] p≤0.0001 | **-0.070** [-0.086, -0.055] p≤0.0001 | **-0.037** [-0.065, -0.007] p=0.0147 |
| `app_bigram_edge` | **+0.050** [+0.034, +0.067] p≤0.0001 | **+0.021** [+0.013, +0.030] p≤0.0001 | **+0.037** [+0.023, +0.053] p≤0.0001 |
| `app_bigram_first` | **+0.045** [+0.030, +0.059] p≤0.0001 | **+0.024** [+0.016, +0.032] p≤0.0001 | **+0.039** [+0.023, +0.055] p≤0.0001 |
| `jieba` | -0.005 [-0.025, +0.015] p=0.64 | n/a | n/a |
| `icu_segmenter` | **+0.028** [+0.006, +0.051] p=0.014 | **+0.033** [+0.018, +0.048] p=0.0002 | **-0.151** [-0.189, -0.113] p≤0.0001 |
| `better_trigram` | **+0.041** [+0.013, +0.068] p=0.0031 | **-0.079** [-0.102, -0.056] p≤0.0001 | **-0.107** [-0.135, -0.079] p≤0.0001 |
| `fts5_cjk` | -0.001 [-0.006, +0.004] p=0.727 | -0.001 [-0.005, +0.003] p=0.719 | -0.004 [-0.013, +0.004] p=0.315 |
| `fts5_cjk_unigram` | -0.002 [-0.007, +0.002] p=0.397 | +0.000 [-0.003, +0.004] p=0.824 | -0.003 [-0.010, +0.005] p=0.506 |

Paired difference in nDCG@10 against `app_bigram`, MIRACL **train** (95% bootstrap CI, randomization p):

| system | zh | ja | ko |
|---|---|---|---|
| `unicode61` | **-0.332** [-0.350, -0.315] p≤0.0001 | **-0.394** [-0.406, -0.382] p≤0.0001 | **-0.142** [-0.161, -0.123] p≤0.0001 |
| `trigram` | **-0.100** [-0.111, -0.089] p≤0.0001 | **-0.083** [-0.091, -0.076] p≤0.0001 | **-0.030** [-0.044, -0.016] p≤0.0001 |
| `app_bigram_edge` | **+0.041** [+0.033, +0.050] p≤0.0001 | **+0.026** [+0.022, +0.030] p≤0.0001 | **+0.017** [+0.008, +0.027] p=0.0006 |
| `app_bigram_first` | **+0.034** [+0.027, +0.042] p≤0.0001 | **+0.026** [+0.022, +0.030] p≤0.0001 | **+0.022** [+0.013, +0.031] p≤0.0001 |
| `jieba` | **+0.027** [+0.014, +0.040] p≤0.0001 | n/a | n/a |
| `icu_segmenter` | **+0.043** [+0.030, +0.057] p≤0.0001 | **+0.041** [+0.033, +0.049] p≤0.0001 | **-0.134** [-0.153, -0.115] p≤0.0001 |
| `better_trigram` | **+0.053** [+0.037, +0.069] p≤0.0001 | **-0.094** [-0.106, -0.083] p≤0.0001 | **-0.089** [-0.104, -0.075] p≤0.0001 |
| `fts5_cjk` | **-0.004** [-0.007, -0.001] p=0.0144 | -0.001 [-0.003, +0.001] p=0.179 | **-0.005** [-0.010, -0.000] p=0.0597 |
| `fts5_cjk_unigram` | -0.001 [-0.004, +0.001] p=0.269 | -0.000 [-0.002, +0.001] p=0.808 | **-0.006** [-0.011, -0.001] p=0.0285 |
| `fts5_cjk_qfirst` | **+0.029** [+0.022, +0.037] p≤0.0001 | **+0.019** [+0.015, +0.024] p≤0.0001 | **+0.014** [+0.006, +0.023] p=0.0004 |
| `fts5_cjk_qedge` | **+0.041** [+0.033, +0.050] p≤0.0001 | **+0.020** [+0.016, +0.024] p≤0.0001 | **+0.017** [+0.008, +0.027] p=0.0006 |

Bold = the 95% CI excludes zero (no multiple-comparison correction; see Limits). `trigram_like` ranks exactly like `trigram` (same ranking path) and is not repeated.

Index size in MB (10^6 bytes) after VACUUM: **index only** (FTS5 `content=''`) / **index + one raw copy** of the original text / **default** (the FTS5 table with its stored copy of what the system indexes: transformed text for app-level systems, original text otherwise; the measure used before 2026-11). Only the first two compare like with like.

| system | law | zh train | ja train | ko train |
|---|---|---|---|---|
| `unicode61` | 12.4 / 32.1 / 32.1 | 32.6 / 71.7 / 71.7 | 46.9 / 107.8 / 107.8 | 26.0 / 75.1 / 75.1 |
| `trigram` | 28.4 / 48.0 / 48.0 | 96.1 / 135.2 / 135.2 | 110.1 / 171.0 / 171.0 | 84.0 / 133.2 / 133.2 |
| `trigram_like` | 28.4 / 48.0 / 48.0 | 96.1 / 135.2 / 135.2 | 110.1 / 171.0 / 171.0 | 84.0 / 133.2 / 133.2 |
| `app_bigram` | 16.0 / 35.7 / 57.7 | 43.0 / 82.0 / 122.3 | 55.8 / 116.6 / 191.0 | 32.6 / 81.8 / 115.2 |
| `app_bigram_edge` | 19.1 / 38.8 / 65.9 | 50.5 / 89.6 / 142.3 | 63.8 / 124.6 / 213.2 | 52.3 / 101.4 / 173.7 |
| `app_bigram_first` | 17.6 / 37.3 / 61.9 | 46.2 / 85.2 / 131.6 | 59.6 / 120.5 / 201.7 | 43.2 / 92.4 / 145.0 |
| `jieba` | 9.3 / 28.9 / 34.8 | 26.6 / 65.6 / 80.0 | n/a | n/a |
| `jieba_big` | 9.6 / 29.3 / 38.6 | n/a | n/a | n/a |
| `icu_segmenter` | 8.3 / 27.9 / 29.3 | 23.0 / 62.0 / 65.6 | 28.3 / 89.2 / 95.5 | 25.7 / 74.9 / 74.4 |
| `better_trigram` | 12.9 / 32.6 / 32.6 | 32.1 / 71.2 / 71.2 | 42.9 / 103.8 / 103.7 | 39.6 / 88.8 / 88.8 |
| `fts5_cjk` | 19.1 / 38.8 / 38.8 | 50.5 / 89.6 / 89.6 | 64.3 / 125.1 / 125.1 | 52.3 / 101.5 / 101.4 |
| `fts5_cjk_unigram` | 27.2 / 46.8 / 46.8 | 68.1 / 107.2 / 107.2 | 91.7 / 152.5 / 152.5 | 60.0 / 109.2 / 109.2 |
| `fts5_cjk_qfirst` | n/a | 50.5 / 89.6 / 89.6 | 64.3 / 125.1 / 125.1 | 52.3 / 101.5 / 101.4 |
| `fts5_cjk_qedge` | n/a | 50.5 / 89.6 / 89.6 | 64.3 / 125.1 / 125.1 | 52.3 / 101.5 / 101.4 |

Run environments: law: SQLite 3.53.1, Python 3.13.18, Node v22.23.5 (ICU 78.3), Linux-6.18.44-fc-v595-x86_64-with-glibc2.39; MIRACL zh dev: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O; MIRACL zh train: SQLite 3.53.1, Python 3.13.18, Linux-6.8.0-149-generic-aarch64-with-glibc2.35; MIRACL ja dev: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O; MIRACL ja train: SQLite 3.53.1, Python 3.13.18, Linux-6.8.0-149-generic-aarch64-with-glibc2.35; MIRACL ko dev: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O; MIRACL ko train: SQLite 3.53.1, Python 3.13.18, Node v22.23.5 (ICU 78.3), Linux-6.8.0-149-generic-aarch64-with-glibc2.35.
<!-- LEADERBOARD:END -->

## Findings

1. **The first character of each CJK run helps in every language, and the gain holds on held-out
   queries.** Adding it as an extra term, in documents and in queries (`app_bigram_first`), improves
   nDCG@10 over plain bigrams by +0.045 (zh), +0.024 (ja), +0.039 (ko) on dev and +0.034, +0.026,
   +0.022 on the held-out train queries, all p≤0.0001. It was found on Chinese dev queries and chosen
   after looking at them; no decision used the train queries. Adding the last character as well
   (`app_bigram_edge`) adds little: on train it is within ±0.01 of `app_bigram_first` in Japanese and
   Korean and 0.007 ahead in Chinese (p=0.025 uncorrected), while costing more index and query time,
   most of all in Korean (p50 96 ms against 38 ms for `app_bigram_first` and 8 ms for plain bigrams).
   The last character on its own was not tested. The gain needs the query-side terms: fts5-cjk indexes
   the first and last characters, but under the common query rule its queries do not send them, and it
   ranks within ±0.01 of plain bigrams. Sending them from fts5-cjk's unchanged index recovers the gain,
   in a test whose decision rule was fixed before it ran on the held-out queries: with the first character
   (`fts5_cjk_qfirst`) it comes within 0.005 to 0.008 of `app_bigram_first`, and with both
   (`fts5_cjk_qedge`) it reproduces `app_bigram_edge` (identical on all 868 Korean queries, within 0.006
   elsewhere).
2. **What helps Chinese can hurt Japanese and Korean.** better-trigram makes each Han and kana
   character its own token and splits other text, Hangul included, into trigrams (its README and the
   token test in `tests/test_systems.py`). Against plain bigrams it gains in Chinese (+0.041 dev,
   +0.053 train) and loses in Japanese (−0.079, −0.094), where single characters replace bigrams, and
   in Korean (−0.107, −0.089), where trigrams replace bigrams, as with the built-in `trigram` (−0.037,
   −0.030). A plausible reason for Japanese, not tested: a Han character carries meaning, while a kana
   character is mostly a sound. Testing Chinese alone and calling it "CJK" would give the wrong answer.
3. **Dictionary segmenters depend on the language and the dictionary.** ICU beats plain bigrams in
   Japanese (+0.033 dev, +0.041 train) and in Chinese (+0.028, p=0.014 on dev; +0.043, p≤0.0001 on
   train), and is close to the default in Korean. jieba on Simplified Chinese (MIRACL) shows no
   detectable difference from plain bigrams on dev (−0.005, interval about ±0.02) but is ahead on the
   held-out queries (+0.027 [+0.014, +0.040]). On Traditional Chinese (law), jieba with its default
   dictionary finds 61.3% of exact matches; with the dictionary jieba documents for Traditional Chinese,
   `extra_dict/dict.txt.big` (`jieba_big`), it finds 71.6% against ICU's 71.1%, ahead on two- and
   three-character words and non-word spans, behind on single characters (13.0% vs 25.0%) and words of
   four or more characters (95.1% vs 96.9%).
4. **Word segmenters miss words inside longer words** in exact search: 民國 inside 中華民國. Part of
   that is by design (a segmenter should not match 中國 inside 發展中國家), so the substring task
   favours n-gram approaches and the ranking task gives the fairer picture for segmenters.

## Systems

| id | what it is |
|---|---|
| `unicode61` | FTS5 default. A whole CJK run becomes one token. |
| `trigram` | Built-in trigram tokenizer. Queries under 3 characters match nothing. |
| `trigram_like` | Trigram, falling back to a `LIKE` scan for queries under 3 characters or when FTS finds nothing (the fix several agent-memory projects shipped). Ranks exactly like `trigram`. |
| `app_bigram` | App-level overlapping CJK bigrams + unicode61, the common "few-line fix". |
| `app_bigram_edge` | `app_bigram` plus each CJK run's first and last character as extra tokens. |
| `app_bigram_first` | `app_bigram` plus each CJK run's first character only. Added after an ablation of `app_bigram_edge` on the dev queries (Finding 1). |
| `jieba` | App-level [jieba](https://github.com/fxsjy/jieba) segmentation + unicode61, default dictionary. Chinese only. |
| `jieba_big` | `jieba` with `extra_dict/dict.txt.big`, the dictionary jieba's README offers for Traditional Chinese (pinned commit and SHA-256). Law task only: MIRACL zh is Simplified, for which the default dictionary is the documented choice. |
| `icu_segmenter` | App-level ICU word segmentation through Node's `Intl.Segmenter` + unicode61. FTS5 has no official ICU tokenizer (SQLite's ICU extension targets FTS3/4), and `Intl.Segmenter` is ICU's word-break iterator, so this covers both. Needs Node.js. |
| `better_trigram` | [streetwriters/sqlite-better-trigram](https://github.com/streetwriters/sqlite-better-trigram) C extension: space-bounded trigrams, with each Han or kana character as its own token. Its CJK ranges do not include Hangul, so Korean gets trigrams. |
| `fts5_cjk` | [Ray0907/fts5-cjk](https://github.com/Ray0907/fts5-cjk) C extension: bigrams inside the tokenizer. Substring queries use its documented `cjk_query()` helper. |
| `fts5_cjk_unigram` | fts5-cjk with its documented `unigram 1` option. |
| `fts5_cjk_qfirst` | `fts5_cjk`'s table and substring search; its ranking query also sends each CJK run's first character, which fts5-cjk indexes on its own. What the proposed `cjk_rank_query(text, 'first')` produces. Held-out (train) results only. |
| `fts5_cjk_qedge` | Same, sending each run's first and last character (`cjk_rank_query(text, 'edge')`). Held-out results only. |

Each system is set up the way its own documentation describes. Not run yet:
[Lindera](https://github.com/lindera/lindera) (a Japanese/Korean morphological analyser, the most
important missing system for ja and ko) and Signal's tokenizer.

## Method

### Task 1: exact substring search (Taiwan law)

46,138 articles of Taiwan's laws (法律, Traditional Chinese, deleted articles removed) from the
Ministry of Justice open data, via the GitHub mirror kong0107/mojLawSplitJSON. Ground truth for a
query is every article where `text LIKE '%query%'`, so the task measures **whether a setup finds
every exact occurrence**: the search-box and agent-memory case.

400 queries, seed 42, chosen independently of every system:

- 2-, 3- and 4+-character words (100 each): headwords of the Ministry of Education's Revised
  Mandarin Chinese Dictionary (重編國語辭典修訂本) that appear in at least 3 articles
- single characters (50)
- non-word spans (50): random 2-4 character spans of the text that are not dictionary words

Metrics: recall, precision and zero-result rate per query type. Full tables with failure examples:
[`results/law_substring.md`](results/law_substring.md).

### Task 2: ranking (MIRACL zh, ja, ko)

MIRACL dev queries (zh 393, ja 860, ko 213) over 100,000 passages per language: every judged
passage plus random distractors (seed 42). Metrics: nDCG@10 and Recall@100.

The benchmark was developed on the dev queries, and `app_bigram_first` was added after looking at
them. As a held-out check, every system was also run on the MIRACL **train** queries (zh 1,312,
ja 3,477, ko 868; `--split train`), which no decision used. The train sample is drawn the same way
(every judged train passage plus seeded distractors to 100,000), so its passages differ from dev's and
absolute scores are not comparable across the splits; compare systems within a split. The train runs
were driven in resumable steps by [`audit/chunk_run.py`](audit/chunk_run.py), which calls the same
harness functions; a Korean re-run with the current code matched the earlier run on every query.

MIRACL queries are full questions (中国俄罗斯族有多少人？), so ranking uses **one rule for every
system**: strip punctuation; apply the same transformation the system applies to documents;
tokenize with the system's **own** FTS5 tokenizer (read back through `fts5vocab`); OR the distinct
tokens; order by bm25. No system gets hand-written query logic. Tokenizers that add tokens only when
indexing documents (fts5-cjk's run-edge characters) have those removed so the query matches what a
real `MATCH` would see. A test checks that fts5-cjk and `app_bigram` send identical tokens for Han
sentences; they differ, and the tests record it, where fts5-cjk folds what `app_bigram` does not
(14 Han variants, half-width kana, full-width ASCII) or counts 々〆〇 as part of a CJK run.

Comparisons use a paired bootstrap 95% confidence interval and a paired randomization test over the
same queries (`python -m bench.compare`). "Within ±0.01" means the 90% bootstrap interval of the
difference lies inside ±0.01 (equivalence by two one-sided tests at 5%); distances to the top system
use Holm's correction over all comparisons with it. Ranking results are deterministic: a full re-run
gave identical per-query scores (dev), and so did the Korean train re-run.

Index size is measured three ways: the inverted index alone (FTS5 `content=''`), that plus one plain
table holding the original text, and the FTS5 table with its own stored copy, which is what earlier
versions reported. The last one is not comparable across kinds of system: an app-level table stores
its transformed text (bigram rewriting makes it 1.6 to 2.0 times the original bytes), a
tokenizer-level table the original.

### Limits

- One run per task and split: dev on one macOS machine, the law task re-run in a Linux container,
  train in a Linux VM in resumable steps. Latency is indicative and depends on the machine; it was
  not repeated, and the train latencies are not comparable with a single run (languages partly ran in
  parallel and the index was reopened between steps). The leaderboard's latency comes from dev.
- MIRACL passages come from Wikipedia; other domains (chat logs, code, legal text) may rank differently.
- The 100,000-passage sample keeps every judged passage, so it is easier than the full corpus;
  differences may change at full size.
- MIRACL zh is Simplified Chinese. There is no Traditional Chinese ranking data; Traditional is
  covered only by the substring task.
- Query latency reflects the common rule (OR all tokens, order by bm25), not a tuned production
  query. Systems that emit many tokens per query (better-trigram, edge terms) pay for it most.
- Law recall is an average over a fixed mix of query types; 162 of the 400 queries are one or two
  characters long. Read the per-type table, not only the overall figure.
- The leaderboard reports 56 paired comparisons (25 dev, 31 train) with no multiple-comparison
  correction (Bonferroni threshold about 0.0009). Results with p between 0.01 and 0.05 should be treated as
  suggestive. `p≤0.0001` is the smallest p that 10,000 sign flips can give (1/10001): no flip was as
  extreme as the observed difference.
- ko dev has only 213 queries, so its confidence intervals are wider; ko train has 868.

## Corrections

Problems found while building the benchmark, kept here so the results can be judged with them in mind:

1. **All-zero ranking scores (harness bug).** The first MIRACL run sent full-sentence questions
   through the exact-phrase path, so no system returned anything. The fixture test only checked that
   scores were between 0 and 1. Fixed with a separate ranking path; the test now fails on an
   all-empty run.
2. **Ranking favoured fts5-cjk (found by an independent review).** Query tokens were read back in
   *document* mode, where fts5-cjk adds each run's first and last character. fts5-cjk therefore sent
   extra OR terms no other bigram system got, and appeared to lead `app_bigram` by 0.05 nDCG@10.
   Removing those terms erased the lead; adding them to `app_bigram` reproduced it exactly. The
   technique is now measured on its own as `app_bigram_edge`.
3. **Substring queries favoured jieba.** Query words were first sampled from jieba's own
   segmentation, so jieba always saw its own tokens, and the set included non-words such as 劃致.
   Adding the ICU segmenter exposed it. Words now come from the Ministry of Education dictionary.
4. **2026-11-18: claims corrected after an independent audit and a held-out re-run.**
   - *Index size.* "fts5-cjk has a smaller index than app-level bigrams" came from what each table
     stores, not what it indexes: app-level tables stored their bigram-rewritten text. fts5-cjk's
     inverted index is larger (+15% to +60%). Sizes are now measured three ways.
   - *Korean explanation.* Finding 2 explained better-trigram's Korean loss by single-character tokens.
     better-trigram does not treat Hangul as CJK; it makes trigrams of it. The finding now says so.
   - *jieba's dictionary.* jieba ran on Traditional Chinese with its default dictionary although its
     README offers `dict.txt.big` for Traditional text. With it (`jieba_big`), law recall is 71.6%,
     not 61.3%, and slightly above ICU's 71.1%.
   - *"Tied-best".* `app_bigram_first` was called best or tied-best in all three languages, and
     several systems "the same", on the basis of non-significant differences on the dev queries it
     was chosen on. On held-out queries it is the top system only in Korean. "Tied" is replaced by an
     equivalence test (90% interval inside ±0.01) or by the actual difference.
   - *Held-out validation.* Every system was run on the MIRACL train queries. The first-character
     gain holds; "jieba does no better than bigrams on Simplified Chinese" does not (+0.027).
   - *fts5-cjk's ranking query.* The common rule leaves fts5-cjk's run-edge characters out of its
     queries, so the benchmark measured only half of what its index offers. Two ranking variants that
     send them, `fts5_cjk_qfirst` and `fts5_cjk_qedge`, were added under a decision rule fixed before
     the held-out run; they correspond to a `cjk_rank_query()` helper proposed for fts5-cjk.
   - *Smaller fixes.* Law precision counted a query that returned nothing as 100% precise; it is now
     undefined for such a query. SQLite errors are recorded instead of being silently turned into
     empty results (none occurred). The p-value floor is written p≤0.0001. `trigram_like` is no longer
     counted twice in the ranking statistics. The jieba, Node.js and ICU versions are recorded. The
     claim that a test checks identical tokens is limited to what the test covers.

   These came from an independent audit, which reproduced the law task and recomputed the published
   statistics from the committed results, and from a re-run on held-out queries. Dev results could not be re-run (the dev data was not available
   to the audit), so changes that would alter them, such as aligning `app_bigram`'s CJK character
   class with fts5-cjk's, are listed as open issues rather than made.

## Reproduce

With [uv](https://docs.astral.sh/uv/), which installs the pinned Python and dependencies from
`uv.lock` (its Python can load SQLite extensions, including on macOS):

```sh
./ext/build_ext.sh                 # clones both C tokenizers at pinned commits and compiles them
uv run python -m pytest -q tests

uv run python -m bench.run law_substring --systems all --out results/law_substring.json
uv run python -m bench.report results/law_substring.json > results/law_substring.md
```

MIRACL data comes from Hugging Face (you may need to accept the dataset terms and log in first).
For MIRACL, `--systems all` leaves out jieba for ja and ko (it segments Chinese only) and `jieba_big`
everywhere (its dictionary is for Traditional Chinese; MIRACL zh is Simplified):

```sh
for lang in zh ja ko; do
  uv run --group data hf download miracl/miracl --repo-type dataset --include "miracl-v1.0-$lang/*" --local-dir data/miracl
  uv run --group data hf download miracl/miracl-corpus --repo-type dataset --include "miracl-corpus-v1.0-$lang/*" --local-dir data/miracl
  uv run python -m bench.run miracl --data-dir data/miracl --lang $lang --max-docs 100000 --systems all --out results/miracl_$lang.json
  uv run python -m bench.report results/miracl_$lang.json > results/miracl_$lang.md
  # held-out check: the same run on the train queries
  uv run python -m bench.run miracl --data-dir data/miracl --lang $lang --split train --max-docs 100000 --systems all --out results/miracl_${lang}_train.json
  uv run python -m bench.report results/miracl_${lang}_train.json > results/miracl_${lang}_train.md
done
uv run python -m bench.leaderboard --update-readme
uv run python -m bench.stats > results/stats.md
```

On a machine that cannot keep one process running for the whole run, `audit/chunk_run.py` runs the
same steps in resumable chunks (see its docstring); the train results were produced that way.

`icu_segmenter` needs Node.js. Without uv: `pip install -r requirements.txt` and run the same
commands without `uv run`, using a Python whose `sqlite3` can load extensions (Homebrew's can;
Apple's system Python cannot). The published results were run with the uv-pinned Python. Versions
of SQLite, Python and every dependency are recorded in the results metadata.

To add a tokenizer, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Data and licences

Code: MIT ([LICENSE](LICENSE)). Data is downloaded at run time, not redistributed:

- Taiwan laws: Ministry of Justice open data, Open Government Data License, version 1.0
- Dictionary headwords for query selection: 重編國語辭典修訂本, © Ministry of Education, R.O.C.,
  CC BY-ND 3.0 TW, via [g0v/moedict-data](https://github.com/g0v/moedict-data)
- MIRACL: Apache 2.0 ([dataset card](https://huggingface.co/datasets/miracl/miracl))
- The C tokenizers keep their own licences.
