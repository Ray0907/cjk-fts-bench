"""Add the contentless index size to MIRACL train results produced before the harness measured it.

The zh and ja train runs (2026-11-18) used the harness of commit ee3f11b, which recorded only index_bytes. Their
index sizes without the stored text were measured on the same 100,000-passage samples by audit/sizes.py
(results in audit/sizes.jsonl). That script builds each table the way bench.run does (page size 4096, one insert
transaction, VACUUM) as content='' for the contentless size; its "default" column is the benchmark's
index_bytes, and this script refuses to merge unless that column equals index_bytes byte for byte for every
system. Systems whose table is another system's table (trigram_like is the trigram table; fts5_cjk_qfirst and
fts5_cjk_qedge are the fts5_cjk table, identical MD5) take that system's measurement, under the same check.

  python audit/merge_train_sizes.py results/miracl_zh_train.json zh_train
"""
import json
import sys

SAME_INDEX_AS = {"trigram_like": "trigram", "fts5_cjk_qfirst": "fts5_cjk", "fts5_cjk_qedge": "fts5_cjk"}


def main(path, corpus, sizes="audit/sizes.jsonl"):
    recs = [json.loads(line) for line in open(sizes, encoding="utf-8")]
    by = {r["system"]: r for r in recs if r["corpus"] == corpus}
    with open(path, encoding="utf-8") as fh:
        res = json.load(fh)
    for name, s in res["systems"].items():
        src = SAME_INDEX_AS.get(name, name)
        r = by[src]
        if r["default"] != s["index_bytes"]:
            raise SystemExit(f"{name}: audit default {r['default']} != index_bytes {s['index_bytes']}")
        s["index_bytes_contentless"] = r["contentless"]
    md = res["metadata"]
    md["raw_table_bytes"] = by["_raw_table"]["raw_table_db_bytes"]
    md["index_bytes_contentless_source"] = (
        f"audit/sizes.jsonl corpus {corpus} (audit/sizes.py, same sample; its 'default' equals index_bytes "
        "for every system)")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(f"{path}: merged contentless sizes for {len(res['systems'])} systems")


if __name__ == "__main__":
    main(*sys.argv[1:])
