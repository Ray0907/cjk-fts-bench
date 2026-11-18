# cjk-fts-bench

Which SQLite FTS5 setup should you use for Chinese, Japanese and Korean text?

SQLite's default full-text tokenizer barely works for CJK, and projects keep shipping their own fixes:
trigram, `LIKE` fallbacks, bigram rewrites, jieba, `Intl.Segmenter`. This benchmark runs the common
setups on the same data and reports where each one breaks, with paired significance tests instead
of a single average.

Write-up of the results: [SQLite FTS5 for Chinese, Japanese, Korean: 11 tokenizers tested](https://raytien.me/writing/cjk-fts-bench/)
([繁體中文](https://raytien.me/writing/cjk-fts-bench/zh/)).

- **11 setups**, from the FTS5 defaults to C extensions and app-level segmenters
- **2 tasks**: exact substring search over 46,138 Taiwan law articles (Traditional Chinese), and
  ranking on [MIRACL](https://github.com/project-miracl/miracl) with human relevance labels in
  Chinese, Japanese and Korean (100,000 passages each)
- Every number in the tables is generated from `results/*.json` by `python -m bench.leaderboard`

> **Disclosure.** The maintainer of this benchmark also wrote one of the systems,
> [fts5-cjk](https://github.com/Ray0907/fts5-cjk). It does not win. Three problems found during
> development, one of which favoured fts5-cjk, are documented in [Corrections](#corrections).
> Reviews from other tokenizer authors are welcome.

## Which setup should I use?

- **Don't use the defaults for CJK.** `unicode61` treats a whole run of Han characters as one
  token (nDCG@10 0.008 on Chinese). The built-in `trigram` tokenizer returns nothing for queries
  under 3 characters, and most Chinese words are 2 characters.
- **One setup for all three languages, best ranking:** overlapping bigrams plus each CJK run's
  first character as an extra token, **added to documents and to queries** (`app_bigram_first`).
  It is best or tied-best on zh, ja and ko. Adding the token to documents only does nothing: that
  is what fts5-cjk does, and it ranks the same as plain bigrams. Cost over plain bigrams: a larger
  index (+8% zh, +6% ja, +26% ko) and slower ranking queries (p50 zh 3.3 vs 2.0 ms, ja 32 vs 26 ms,
  ko 38 vs 8 ms). Like plain bigrams, it misses a single-character query that only occurs at the
  end of a run (98.4% substring recall).
- **Also the last character (`app_bigram_edge`):** ranks the same as `app_bigram_first` (no
  significant difference in any language) and finds every exact match, but costs more: index +15%
  zh, +12% ja, +51% ko and p50 zh 5.0 ms, ja 48 ms, ko 96 ms. Choose it only if you need exact
  single-character matches.
- **Japanese only:** ICU word segmentation (`Intl.Segmenter`) has the highest Japanese score
  (statistically tied with `app_bigram_edge`) and the smallest index. Cost: it needs Node.js and
  ranking queries are slow (p50 73 ms on ja vs 26 ms for plain bigrams). Don't use it for Korean:
  it splits hangul only at spaces, so 검색을 never matches 검색.
- **Every exact match, little code:** `trigram` plus a `LIKE` fallback for short queries finds
  everything, but the fallback is a full scan, so it should slow down as data grows (p95 17 ms on
  46k articles; scaling was not measured). Its ranking is poor (nDCG@10 0.251 on zh, same as
  `trigram`). fts5-cjk and better-trigram also find everything, without the scan.
- **No application code:** a C tokenizer. fts5-cjk ranks the same as app-level bigrams
  (no significant difference in any language) with a smaller index. Ranking was measured with the
  benchmark's common query rule, not fts5-cjk's `cjk_query()` helper, so the helper's ranking is
  not covered. better-trigram ranks well
  in Chinese but is slow (p50 50 ms on zh) and falls behind on Japanese and Korean.

## Leaderboard

<!-- LEADERBOARD:START -->
Best value per column in bold. n/a = not run (jieba segments Chinese only; `jieba_big` uses jieba's Traditional Chinese dictionary and runs on the law task only).

| system | Law substring recall | MIRACL zh nDCG@10 | MIRACL ja nDCG@10 | MIRACL ko nDCG@10 | zh p50 ms | zh index MB |
|---|---|---|---|---|---|---|
| `unicode61` | 4.9% | 0.008 | 0.128 | 0.352 | **0.04** | 69 |
| `trigram` | 59.5% | 0.251 | 0.465 | 0.473 | 0.46 | 130 |
| `trigram_like` | **100.0%** | 0.251 | 0.465 | 0.473 | 0.42 | 130 |
| `app_bigram` | 98.4% | 0.379 | 0.536 | 0.510 | 2.03 | 118 |
| `app_bigram_edge` | **100.0%** | **0.429** | 0.557 | 0.547 | 5.02 | 136 |
| `app_bigram_first` | 98.4% | 0.423 | 0.560 | **0.549** | 3.31 | 127 |
| `jieba` | 61.3% | 0.374 | n/a | n/a | 11.35 | 77 |
| `jieba_big` | 71.6% | n/a | n/a | n/a | n/a | n/a |
| `icu_segmenter` | 71.1% | 0.406 | **0.569** | 0.359 | 12.40 | **63** |
| `better_trigram` | **100.0%** | 0.419 | 0.457 | 0.403 | 50.36 | 68 |
| `fts5_cjk` | **100.0%** | 0.378 | 0.535 | 0.506 | 2.02 | 86 |
| `fts5_cjk_unigram` | **100.0%** | 0.377 | 0.536 | 0.507 | 3.76 | 104 |

Paired difference in nDCG@10 against `app_bigram` (95% bootstrap CI, randomization p):

| system | zh | ja | ko |
|---|---|---|---|
| `unicode61` | **-0.370** [-0.403, -0.339] p<0.0001 | **-0.408** [-0.432, -0.382] p<0.0001 | **-0.158** [-0.197, -0.120] p<0.0001 |
| `trigram` | **-0.127** [-0.151, -0.104] p<0.0001 | **-0.070** [-0.086, -0.055] p<0.0001 | **-0.037** [-0.065, -0.007] p=0.0147 |
| `trigram_like` | **-0.127** [-0.151, -0.104] p<0.0001 | **-0.070** [-0.086, -0.055] p<0.0001 | **-0.037** [-0.065, -0.007] p=0.0147 |
| `app_bigram_edge` | **+0.050** [+0.034, +0.067] p<0.0001 | **+0.021** [+0.013, +0.030] p<0.0001 | **+0.037** [+0.023, +0.053] p<0.0001 |
| `app_bigram_first` | **+0.045** [+0.030, +0.059] p<0.0001 | **+0.024** [+0.016, +0.032] p<0.0001 | **+0.039** [+0.023, +0.055] p<0.0001 |
| `jieba` | -0.005 [-0.025, +0.015] p=0.64 | n/a | n/a |
| `jieba_big` | n/a | n/a | n/a |
| `icu_segmenter` | **+0.028** [+0.006, +0.051] p=0.014 | **+0.033** [+0.018, +0.048] p=0.0002 | **-0.151** [-0.189, -0.113] p<0.0001 |
| `better_trigram` | **+0.041** [+0.013, +0.068] p=0.0031 | **-0.079** [-0.102, -0.056] p<0.0001 | **-0.107** [-0.135, -0.079] p<0.0001 |
| `fts5_cjk` | -0.001 [-0.006, +0.004] p=0.727 | -0.001 [-0.005, +0.003] p=0.719 | -0.004 [-0.013, +0.004] p=0.315 |
| `fts5_cjk_unigram` | -0.002 [-0.007, +0.002] p=0.397 | +0.000 [-0.003, +0.004] p=0.824 | -0.003 [-0.010, +0.005] p=0.506 |

Bold = the 95% CI excludes zero (no multiple-comparison correction; see Limits).

Run environments: law: SQLite 3.53.1, Python 3.13.18, Linux-6.18.44-fc-v595-x86_64-with-glibc2.39; MIRACL zh: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O; MIRACL ja: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O; MIRACL ko: SQLite 3.50.4, Python 3.13.11, macOS-27.0.1-arm64-arm-64bit-Mach-O.
<!-- LEADERBOARD:END -->

## Findings

1. **Edge unigrams are the one change that helps everywhere.** Adding each CJK run's first and last
   character as extra terms, in documents and in queries, improves nDCG@10 by +0.050 (zh), +0.021
   (ja) and +0.037 (ko), all p<0.0001. It was found on Chinese; Japanese and Korean, analysed
   afterwards, confirm it. **The gain comes from the first character alone**: `app_bigram_first`
   ranks the same as `app_bigram_edge` (difference −0.006 zh, +0.003 ja, +0.002 ko, none
   significant), while the last character alone adds nothing measurable and most of the cost. In
   Korean the last character of a word is usually a particle (는, 의, 가, 은) found in 52–79% of
   passages, which is why `app_bigram_edge` queries take 96 ms there against 8 ms for plain
   bigrams. This ablation was done after seeing the dev-set results, on the same queries, so it is
   not held out. The gain needs the query-side terms: fts5-cjk adds them to documents
   only and gains nothing. It costs index size and query time, most of all in Korean.
2. **What helps Chinese can hurt Japanese and Korean.** Single-character tokens (better-trigram)
   beat plain bigrams in Chinese (+0.041, one of ~30 comparisons, see Limits) but lose clearly in
   Japanese (−0.079) and Korean (−0.107).
   A plausible reason, not tested: a Han character carries meaning, while a kana or hangul
   character is mostly a sound. Testing Chinese alone and calling it "CJK" would give the wrong answer.
3. **Dictionary segmenters depend on the language and the dictionary.** ICU beats plain bigrams in
   Japanese (+0.033) and, less certainly, in Chinese (+0.028, p=0.014, not robust to the multiple
   comparisons below). It has the highest Japanese score (0.569; not significantly above
   `app_bigram_edge`, p=0.12), but is close to the default in Korean.
   jieba shows no detectable difference from plain bigrams on Simplified Chinese (MIRACL; the
   interval is about ±0.02) and falls behind ICU on Traditional
   Chinese (law: 61.3% vs 71.1% recall); its dictionary is Simplified.
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
| `app_bigram_first` | `app_bigram` plus each CJK run's first character only. Added after an ablation of `app_bigram_edge` (Finding 1). |
| `jieba` | App-level [jieba](https://github.com/fxsjy/jieba) segmentation + unicode61. Chinese only. |
| `icu_segmenter` | App-level ICU word segmentation through Node's `Intl.Segmenter` + unicode61. FTS5 has no official ICU tokenizer (SQLite's ICU extension targets FTS3/4), and `Intl.Segmenter` is ICU's word-break iterator, so this covers both. Needs Node.js. |
| `better_trigram` | [streetwriters/sqlite-better-trigram](https://github.com/streetwriters/sqlite-better-trigram) C extension: trigrams, with each CJK character as its own token. |
| `fts5_cjk` | [Ray0907/fts5-cjk](https://github.com/Ray0907/fts5-cjk) C extension: bigrams inside the tokenizer. Substring queries use its documented `cjk_query()` helper. |
| `fts5_cjk_unigram` | fts5-cjk with its documented `unigram 1` option. |

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

MIRACL queries are full questions (中国俄罗斯族有多少人？), so ranking uses **one rule for every
system**: strip punctuation; apply the same transformation the system applies to documents;
tokenize with the system's **own** FTS5 tokenizer (read back through `fts5vocab`); OR the distinct
tokens; order by bm25. No system gets hand-written query logic. Tokenizers that add tokens only when
indexing documents (fts5-cjk's run-edge characters) have those removed so the query matches what a
real `MATCH` would see; a test checks that fts5-cjk and `app_bigram` send identical tokens.

Comparisons use a paired bootstrap 95% confidence interval and a paired randomization test over the
same queries (`python -m bench.compare`). Ranking results are deterministic: a full re-run gave
identical per-query scores.

### Limits

- One run per task, all on one macOS machine. Latency and index size
  are indicative and depend on the machine; index size includes FTS5's stored copy of the text,
  so compare systems relative to each other.
- MIRACL passages come from Wikipedia; other domains (chat logs, code, legal text) may rank differently.
- The 100,000-passage sample keeps every judged passage, so it is easier than the full corpus;
  differences may change at full size.
- MIRACL zh is Simplified Chinese. There is no Traditional Chinese ranking data; Traditional is
  covered only by the substring task.
- Query latency reflects the common rule (OR all tokens, order by bm25), not a tuned production
  query. Systems that emit many tokens per query (better-trigram, edge terms) pay for it most.
- About 30 paired comparisons are reported with no multiple-comparison correction (Bonferroni
  threshold about 0.002). Results with p near 0.01 to 0.05 (trigram on ko, ICU on zh,
  better-trigram on zh) should be treated as suggestive. `p<0.0001` means no resample in 10,000
  was as extreme.
- ko has only 213 queries, so its confidence intervals are wider.

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
done
uv run python -m bench.leaderboard --update-readme
```

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
