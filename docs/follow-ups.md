# Follow-ups

Changes the 2026-11 audit identified but did not make, because they would alter published numbers that cannot be
regenerated yet, or because they need data or decisions outside this repository.

## Needs a dev re-run (MIRACL dev topics/qrels were not available)

1. **Align `app_bigram`'s CJK class with fts5-cjk's.** `CJK_CLASS` in `bench/systems.py` leaves out 々〆〇 and does not
   fold half-width kana or full-width ASCII, so `app_bigram`, `app_bigram_first` and `app_bigram_edge` split runs
   that fts5-cjk keeps whole. The same class drives `drop_run_unigrams` and `run_first_unigrams`, which is why
   `fts5_cjk_qfirst` keeps a run-final 々 on 2 of 3,477 ja train queries where fts5-cjk's own
   `cjk_rank_query(..., 'first')` does not (`audit/rank_query_validation/summary.md`). The strict-xfail cases in
   `tests/test_systems.py::test_bigram_systems_rank_with_same_tokens_beyond_han` turn into passes once fixed.
   It changes app-level tokens, so dev zh/ja/ko and all train results must be re-run.
2. **Run `fts5_cjk_qfirst` / `fts5_cjk_qedge` on dev**, and confirm or change the default mode of fts5-cjk's
   `cjk_rank_query()` (`'first'` is provisional; `'edge'` was +0.012 over `'first'` in zh train, p=0.0002,
   and not significantly different in ja and ko). Then pin a fts5-cjk commit that has the function and
   measure it directly instead of through the Python equivalent.
3. **Re-run dev with the current harness** to record errors, tool versions and contentless sizes for dev too. Dev
   index sizes now exist only in the old default measure.

## Measurement

4. **Latency**: repeat runs on one idle machine and report spread. Today every latency is one run, and the train
   latencies come from chunked runs that reopened the index between chunks.
5. **zh train ranking at the top**: `app_bigram_first` vs `better_trigram` is borderline (p≈0.02 unadjusted; Holm
   0.056 without and 0.075 with the two fts5-cjk variants in the family; with 10,000 sign flips the
   adjusted value also moves with Monte Carlo error). More queries or the full corpus would settle it.
6. **`unigram 1` tables with the run-first ranking query**: untested; a one-character term there matches every
   occurrence.
7. **Missing systems**: Lindera (Japanese/Korean morphological analysis) and Signal's tokenizer.
