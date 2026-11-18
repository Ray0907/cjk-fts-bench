# Claims audit of the README

Every quantitative or comparative statement in `README.md` outside the generated leaderboard block, with the file and
field it comes from. The leaderboard block itself is written by `python -m bench.leaderboard` from `results/*.json`
(checked: the README block is byte-identical to the generator's output). `stats.md` below is `results/stats.md`,
written by `python -m bench.stats`. "dev" = `results/miracl_<lang>.json`, "train" = `results/miracl_<lang>_train.json`,
"law" = `results/law_substring.json`. A field path such as `systems.X.buckets.all.ndcg10` refers to those files.
Percentages of size are relative differences computed in `stats.md` § Index size.

Statements that are not measurements (descriptions of how a system works, design intent) are listed with the
document or test that shows them. A statement for which no source could be given was removed or rewritten.

## Introduction

| # | statement | source |
|---|---|---|
| 1 | 12 setups plus two ranking-query variants of fts5-cjk | `bench/systems.py` `SYSTEMS` (14 entries; `fts5_cjk_qfirst`, `fts5_cjk_qedge` are `ranking_only`) |
| 2 | 46,138 Taiwan law articles | law `metadata.corpus_size` = 46138 |
| 3 | 100,000 passages each | dev and train `metadata.corpus_size` = 100000 |
| 4 | "two of which favoured fts5-cjk"; the 2026-11 audit was AI-assisted (Claude, run at the author's request), no third-party review yet | Corrections 2 (ranking) and 4 (index size measure); statement of fact by the author |

## Which setup should I use?

| # | statement | source |
|---|---|---|
| 5 | unicode61 nDCG@10 0.008 zh dev, 0.015 train | dev zh / train zh `systems.unicode61.buckets.all.ndcg10` = 0.0081 / 0.0151 |
| 6 | trigram returns nothing for queries under 3 characters | law `systems.trigram.buckets.char1/word2` zero-result rate 100%; `tests/test_systems.py` KNOWN_LIMITS |
| 7 | 85% of dictionary headwords in ≥3 law articles are 2 characters | `bench/queries.py` `word_doc_freq()` cache `data/law_dictfreq.json` (not committed; rebuilt by `bench.queries`): 10,167 of 11,975 headwords with freq ≥ 3 have length 2 (84.9%) |
| 8 | held-out top: better_trigram zh 0.401, icu ja 0.562, app_bigram_first ko 0.511 | `stats.md` § Top system: zh train 0.4006, ja train 0.5615, ko train 0.5105 |
| 9 | zh: icu, edge, fts5_cjk_qedge not significantly below better_trigram after Holm; app_bigram_first borderline | `stats.md` zh train: Holm p 0.3825, 0.3825, 0.3825; app_bigram_first 0.0752 (0.0564 without the ranking-only variants) |
| 10 | ja: ICU significantly above every other system (also after correction) | `stats.md` ja train: every Holm p ≤ 0.0010 |
| 11 | first − app_bigram on train +0.034 / +0.026 / +0.022, 95% CI above zero | `stats.md` pairs: +0.0341 [+0.0266, +0.0416], +0.0263 [+0.0224, +0.0303], +0.0220 [+0.0135, +0.0307] |
| 12 | first is top only in ko; zh 0.019 below better_trigram, 95% CI of the leader's advantage +0.004 to +0.034, p≈0.02 unadjusted, Holm-adjusted 0.056 to 0.075 depending on the family (borderline); ja 0.015 below ICU (significant after correction) | `stats.md` § Top system zh train: +0.0190 [+0.0035, +0.0344], p=0.0188, Holm 0.0752 (family of 11 with the two fts5-cjk variants) and 0.0564 (without them); ja +0.0149, Holm 0.0010; ko top = app_bigram_first |
| 13 | first vs app_bigram index only +7% zh, +7% ja, +33% ko; with raw +4%, +3%, +13% | `stats.md` § Index size: +7.4 / +6.9 / +32.5%; +3.9 / +3.3 / +13.0% |
| 14 | p50 first vs app_bigram: zh 3.3 vs 2.0, ja 32 vs 26, ko 38 vs 8 ms (dev) | dev `systems.{app_bigram_first,app_bigram}.buckets.all.p50_ms`: 3.31/2.03, 31.8/25.5, 37.8/8.2 |
| 15 | first misses run-final single characters: law 87.1% char1, 98.4% overall | law `systems.app_bigram_first.buckets.char1.recall` = 0.871, `.all.recall` = 0.984; KNOWN_LIMITS (app_bigram_first, 鄉) |
| 16 | edge finds every exact match | law `systems.app_bigram_edge.buckets.all.recall` = 1.0 |
| 17 | edge within ±0.01 of first in ja and ko (train); +0.007 in zh, p=0.025 uncorrected | `stats.md` pairs first − edge train: ja yes, ko yes; zh −0.0072, p=0.0253 |
| 18 | edge vs app_bigram index only +18 / +14 / +60%; with raw +9 / +7 / +24% | `stats.md`: +17.6 / +14.3 / +60.3%; +9.2 / +6.8 / +24.0% |
| 19 | edge p50 zh 5.0, ja 48, ko 96 ms (dev) | dev `systems.app_bigram_edge.buckets.all.p50_ms`: 5.02, 48.1, 96.2 |
| 20 | ICU highest Japanese score, 0.569 dev, 0.562 train | `stats.md` § Top system ja dev 0.5686, ja train 0.5615 |
| 21 | ICU smallest index (Japanese) | `stats.md` smallest per measure, ja train: icu_segmenter under all three |
| 22 | ICU p50 73 ms on ja vs 26 ms plain bigrams | dev ja `p50_ms`: 72.8 / 25.5 |
| 23 | ICU splits hangul only at spaces; 검색을 never matches 검색 | `tests/test_systems.py::test_icu_segmenter_splits_hangul_only_at_spaces` |
| 24 | trigram + LIKE finds everything; p95 32 ms on 46k articles (latest run) | law `systems.trigram_like.buckets.all.recall` = 1.0, `.p95_ms` = 31.66 (Linux container run) |
| 25 | its ranking: nDCG@10 0.251 zh, same as trigram | dev zh `systems.trigram_like/trigram.buckets.all.ndcg10` = 0.2514 both |
| 26 | fts5-cjk and better-trigram find everything | law `.all.recall` = 1.0 for both |
| 27 | fts5-cjk within ±0.01 of app_bigram in every language (train); −0.004 / −0.001 / −0.005 | `stats.md` pairs fts5_cjk − app_bigram train: yes ×3; −0.0040, −0.0014, −0.0050 |
| 28 | dev: within ±0.01 in zh and ja; ko interval too wide | `stats.md` dev: zh yes, ja yes, ko no (90% CI [−0.0115, +0.0026]) |
| 29 | index only: fts5-cjk +18% zh, +15% ja, +60% ko, +20% law; with one raw copy for both +9 / +7 / +24 / +9% | `stats.md` § Index size: +17.6 / +15.2 / +60.3 / +19.7%; +9.2 / +7.3 / +24.1 / +8.8% |
| 30 | because it also indexes each run's first and last character | contentless sizes: fts5_cjk equals app_bigram_edge in zh (50.5 MB) and ko (52.3 MB), law 19.1 MB both; ja 64.3 vs 63.8 MB |
| 31 | as usually deployed: fts5-cjk's table 27% / 35% / 12% / 33% smaller than the app-level table alone (12–35% in Corrections), 38% to 50% smaller than the app-level table plus a raw copy | `stats.md` § Index size, default column −26.8 / −34.5 / −11.9 / −32.8%; as deployed column −44.5 / −50.3 / −38.3 / −49.9% (zh / ja / ko train, law) |
| 32 | highlight()/snippet() return the original text for fts5-cjk, bigram text for app-level | `tests/test_systems.py::test_highlight_returns_original_text_only_for_tokenizer_level_systems` (highlight; snippet uses the same offsets, see the audit's `highlight_snippet_examples.txt`) |
| 33 | better-trigram top in Chinese; p50 50 ms zh; behind in ja and ko | `stats.md` zh train top; dev zh `p50_ms` 50.36; pairs better_trigram − app_bigram ja/ko negative |

## Findings

| # | statement | source |
|---|---|---|
| 34 | first − app_bigram dev +0.045 / +0.024 / +0.039; train +0.034 / +0.026 / +0.022; all p≤0.0001 | `stats.md` pairs |
| 35 | found on Chinese dev and chosen after looking at it; no decision used train | Corrections 2; `bench/systems.py` AppBigramFirst description; train results added in this release |
| 36 | edge within ±0.01 of first in ja/ko, +0.007 zh p=0.025 | as #17 |
| 37 | ko p50 96 / 38 / 8 ms (edge / first / app_bigram) | dev ko `p50_ms` 96.2 / 37.8 / 8.2 |
| 38 | last character alone not tested | no such system in `SYSTEMS` |
| 39 | fts5-cjk indexes first/last chars but its ranking queries do not send them; within ±0.01 of bigrams | `bench/systems.py` `Fts5Cjk.rank_drop_run_unigrams`; `tests/test_systems.py::test_bigram_systems_rank_with_same_tokens`; #27 |
| 40 | better-trigram: each Han and kana character its own token; Hangul trigrams | better-trigram README (single CJK characters) and `tokenizer.c` CJK ranges at 851f99f (no Hangul); `tests/test_systems.py::test_better_trigram_splits_han_and_kana_but_not_hangul` |
| 41 | better_trigram − app_bigram: zh +0.041 / +0.053, ja −0.079 / −0.094, ko −0.107 / −0.089 | `stats.md` pairs |
| 42 | trigram − app_bigram ko −0.037 dev, −0.030 train | leaderboard paired tables (generated) |
| 43 | ICU − app_bigram: ja +0.033 / +0.041; zh +0.028 (p=0.014) / +0.043 (p≤0.0001) | `stats.md` pairs |
| 44 | ICU close to the default in Korean | dev ko icu 0.3594 vs unicode61 0.3518; train 0.3546 vs 0.3462 (`buckets.all.ndcg10`) |
| 45 | jieba − app_bigram zh: dev −0.005 (interval about ±0.02), train +0.027 [+0.014, +0.040] | `stats.md` pairs: −0.0048 [−0.0249, +0.0155]; +0.0268 [+0.0141, +0.0398] |
| 46 | law recall jieba 61.3%, jieba_big 71.6%, ICU 71.1% | law `systems.{jieba,jieba_big,icu_segmenter}.buckets.all.recall` = 0.613, 0.716, 0.711 |
| 47 | jieba_big ahead of ICU on 2-, 3-char words and spans; behind on single chars 13.0 vs 25.0% and 4+ 95.1 vs 96.9% | law `buckets.{word2,word3,span_nonword,char1,word4plus}.recall`: 70.9/68.5, 91.6/85.0, 44.6/42.8, 13.0/25.0, 95.1/96.9 |
| 48 | segmenters miss 民國 inside 中華民國 | `tests/test_systems.py` KNOWN_LIMITS (icu_segmenter, 民國) |

## fts5-cjk ranking-query variants

| # | statement | source |
|---|---|---|
| 64 | qfirst − fts5_cjk +0.033 / +0.021 / +0.019 (train), same index | `stats.md` pairs: +0.0332, +0.0208, +0.0193, all p≤0.0001; identical index: `audit/qfirst/index_md5.txt`, equal `index_bytes` in train files |
| 65 | qfirst vs app_bigram_first: within ±0.01 in zh and ja (0.005, 0.007 lower); ko 0.008 lower, 90% CI −0.012 to −0.004, outside ±0.01; the earlier written rule allowed ±0.015 and was not publicly timestamped | `stats.md` pairs: −0.0049 [90% −0.0075, −0.0023] yes; −0.0068 [−0.0089, −0.0048] yes; −0.0077 [−0.0116, −0.0039] no; the ±0.015 rule is in `audit/qfirst/qf_stats.py` |
| 66 | qedge vs app_bigram_edge: identical on all 868 ko queries, indistinguishable in zh (−0.0001), 0.006 lower in ja (p≤0.0001) | `stats.md` pairs: ko 0/868/0 W/T/L; zh −0.0001 p=0.528; ja −0.0058 p≤0.0001 |
| 67 | p50 ratio ×1.7 zh, ×1.2 ja, ×5.0 ko against fts5_cjk (one VM run) | `audit/qfirst/cost.md` (from `audit/qfirst/qfirst_miracl_*_train.json`, one run): ×1.72, ×1.17, ×5.00 |
| 68 | Python equivalent of `cjk_rank_query()`; top-100 identical on all but 2 of 5,657 train queries ('first'; all 5,657 in 'edge') | `audit/rank_query_validation/summary.md` and `validation_summary.json`: zh 1312/1312 both modes, ja 3475/3477 first and 3477/3477 edge, ko 868/868 both |
| 69 | likely reason for the qfirst gap (run-final character under the same term): stated as untested | no test; mechanism described in `audit/qfirst/` experiment notes only |
| 70 | Holm family: comparisons of the top with every other system in that language and split, per-query duplicates counted once (`trigram_like` = `trigram`; `fts5_cjk_qedge` = `app_bigram_edge` on ko train) | `bench/stats.py` docstring and the "Family:" line under each table in `stats.md` |
| 71 | provenance of zh/ja train (audit driver on ee3f11b) and ko (re-run with the final code, per-query identical for 12 systems) | `metadata.provenance` in `results/miracl_*_train.json`; `audit/original/chunk_run.py`, `audit/chunk_run.py` |
| 72 | MIRACL is Apache 2.0; jieba (incl. dict.txt.big) is MIT, © 2013 Sun Junyi | MIRACL GitHub repository `LICENSE` (Apache 2.0) and its dataset card as cited on main; jieba repository `LICENSE` at 67fa2e3 |
| 73 | result files contain query strings and ids but no passage text | `results/*.json` rows: fields `query`, `qid`, metrics only |
| 74 | latency quoted in the recommendations: absolute p50 from the dev run on macOS; ratios for train-only systems from one VM run | dev `metadata.platform`; `audit/qfirst/cost.md` |

## Systems, Method, Limits, Corrections

| # | statement | source |
|---|---|---|
| 49 | trigram_like ranks exactly like trigram | `bench/systems.py`: TrigramLike overrides `search` only; identical `ndcg10` per query in every MIRACL file |
| 50 | jieba_big: dict.txt.big, pinned commit and SHA-256; jieba documents it for Traditional | `bench/systems.py` JIEBA_COMMIT / JIEBA_BIG_SHA256; jieba README "Using Other Dictionaries"; law `metadata.jieba_big_dictionary` |
| 51 | 400 law queries; 100 / 100 / 100 / 50 / 50 per type | law `metadata.n_queries`; `bench/queries.py` |
| 52 | dev queries zh 393, ja 860, ko 213; train 1,312 / 3,477 / 868 | `metadata.n_queries` in each file |
| 53 | Korean train re-run with the current code matched the earlier run on every query | release notes; per-query comparison of `results/miracl_ko_train.json` with the earlier run (868/868 for all 10 systems, equal index sizes) |
| 54 | tokens identical for Han sentences; differ for variants, half-width kana, full-width ASCII, 々〆〇 | `tests/test_systems.py::test_bigram_systems_rank_with_same_tokens` and `::test_bigram_systems_rank_with_same_tokens_beyond_han` (strict xfail) |
| 55 | bigram rewriting makes stored text 1.6 to 2.0 times the original | `audit/sizes.jsonl` app_bigram `stored_text_bytes / raw_text_bytes`: ko 1.61, zh 1.92, ja 2.04, law 2.01 |
| 56 | full re-run gave identical per-query scores (dev) | author's re-run, commit 6c92441 ("quality scores are unchanged"); not re-verified (dev data unavailable) |
| 57 | 162 of 400 law queries are one or two characters | law `queries[].query` lengths (generated in the leaderboard note) |
| 58 | 56 paired comparisons, 25 dev and 31 train; Bonferroni about 0.0009 | leaderboard paired tables: 8 systems × 3 languages + jieba (zh) per split, plus the two variants × 3 languages on train; 0.05 / 56 |
| 59 | p≤0.0001 is the floor of 10,000 sign flips (1/10001) | `bench/compare.py` `p_value = (extreme + 1) / (n_boot + 1)` |
| 60 | Corrections 4: fts5-cjk inverted index +15% to +60% | #29 (zh 17.6, ja 15.2, ko 60.3, law 19.7%) |
| 61 | Corrections 4: jieba_big 71.6% vs 61.3%, comparable to ICU's 71.1% | #46 (0.5 points on 400 queries, not tested for significance) |
| 62 | Corrections 4: jieba vs bigrams on Simplified +0.027 (train) | #45 |
| 63 | Corrections 4: no SQLite errors occurred | law and ko train `buckets.all.errors` = 0 for every system |

Pre-existing sentences left for the maintainer (on main before this series): "(found by an independent review)" in
Correction 2 (who did that review is not recorded here) and "(the fix several agent-memory projects shipped)" in the
`trigram_like` row (no source in the repository).

Removed or rewritten because no source supported them as written: "best or tied-best on zh, ja and ko"; "ranks the
same as plain bigrams" (now: within ±0.01, with the intervals); "the last character alone adds nothing measurable"
(never tested alone); "in Korean the last character is usually a particle found in 52–79% of passages" (no committed
measurement); "a smaller index" for fts5-cjk without saying which deployment; "jieba shows no detectable difference … on Simplified Chinese"
(true on dev only); the Korean single-character explanation in Finding 2; "a test checks that fts5-cjk and
`app_bigram` send identical tokens" (true for Han sentences only); "inside the ±0.015 bound set before the test" and "pre-registered" for the fts5-cjk variants (now
reported under the ±0.01 standard); "not significant after Holm" for app_bigram_first vs better_trigram in zh
(borderline); "independent audit" for the AI-assisted 2026-11 audit; "slightly above ICU" (comparable); "reproduces
app_bigram_edge" for qedge in Japanese (0.006 lower).
