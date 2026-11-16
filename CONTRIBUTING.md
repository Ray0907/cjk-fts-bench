# Contributing

The most useful contributions are new tokenizer setups and corrections to how an existing one is
configured. If you maintain one of the tokenizers here and it is set up wrong, please open an issue:
that is a bug in the benchmark.

## Adding a tokenizer

1. Add a class to `bench/systems.py` and register it in `SYSTEMS`. The interface:

   ```python
   class MySystem(System):
       name = "my_system"          # short id used in results and the leaderboard
       description = "one line"    # shown in reports
       tokenize = "unicode61"      # the FTS5 tokenize= argument

       def available(self): ...    # (True, "") or (False, reason); never raise
       def setup(self, conn): ...  # per-connection setup, e.g. load an extension
       def prep_doc(self, text): ...            # only for app-level pre-segmentation
       def search(self, conn, table, query, k): ...  # substring task; return rowids
   ```

   - Set it up **the way its own documentation says to use it**, the way a typical user would.
     Don't tune it to the benchmark.
   - Don't override `rank()` or `query_tokens()`. Ranking uses one rule for every system (see the
     README). If your tokenizer emits extra tokens only when indexing documents, set
     `rank_drop_run_unigrams` or explain in the PR why the shared rule is wrong for it.
   - A C extension goes into `ext/build_ext.sh`: pin a commit and compile with explicit flags.
     Don't run scripts from the cloned repo.

2. Add behavioural checks to `tests/test_systems.py`. Mark known limitations with
   `xfail(strict=True)` and a reason rather than leaving them out.

3. Run the tests and the benchmarks, then regenerate the leaderboard:

   ```sh
   python -m pytest -q tests
   python -m bench.run law_substring --systems all --out results/law_substring.json
   python -m bench.run miracl --data-dir data/miracl --lang zh --max-docs 100000 --out results/miracl_zh.json  # and ja, ko
   python -m bench.leaderboard --update-readme
   ```

   Commit the updated `results/` files with the PR. Don't edit numbers in the README by hand.

## Changing the method

Changes to queries, metrics or the ranking rule change every system's numbers. Open an issue first,
describe which systems the change affects and why it is fairer, and add an entry to the README's
Corrections section if it fixes a bias.
