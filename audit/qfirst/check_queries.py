"""Unit-style checks of the variants' ranking-query tokens, plus a corpus-wide comparison with the
app-level systems' ranking-query tokens on every MIRACL train query (same samples)."""
import sys, os, sqlite3, pickle, json, collections
REPO = os.path.expanduser("~/qfrun"); sys.path.insert(0, REPO); os.chdir(REPO)
from bench.systems import SYSTEMS
S = SYSTEMS
conn = sqlite3.connect(":memory:"); S["fts5_cjk"].setup(conn)
def qt(name, q):
    c = conn if name.startswith("fts5") else sqlite3.connect(":memory:")
    return S[name].query_tokens(c, q)
cases = {
 "東京大学の研究": (["東京","京大","大学","学の","の研","研究"], ["東"], ["究"]),
 "iPhone手機殼":   (["iphone","手機","機殼"], ["手"], ["殼"]),
 "東京 大学":      (["東京","大学"], ["東","大"], ["京","学"]),
 "茶":             (["茶"], [], []),
 "紅茶 茶":        (["紅茶","茶"], ["紅"], []),
 "한국어 검색엔진":  (["한국","국어","검색","색엔","엔진"], ["한","검"], ["어","진"]),
 "第38條規定":     (["第","38","條規","規定"], ["條"], ["定"]),
 "哈哈":           (["哈哈"], ["哈"], ["哈"]),
}
ok = True
for q, (base, first, last) in cases.items():
    b, f, e = qt("fts5_cjk", q), qt("fts5_cjk_qfirst", q), qt("fts5_cjk_qedge", q)
    exp_f = set(base) | set(first); exp_e = set(base) | set(first) | set(last)
    good = set(b) == set(base) and set(f) == exp_f and set(e) == exp_e
    ok &= good
    print(("PASS" if good else "FAIL"), repr(q), "| fts5_cjk:", b, "| qfirst:", f, "| qedge:", e,
          "| app_bigram_first:", qt("app_bigram_first", q), "| app_bigram_edge:", qt("app_bigram_edge", q))
print("unit checks:", "ALL PASS" if ok else "FAILURES")
out = {"unit_checks_pass": bool(ok), "langs": {}}
for lang in ["zh", "ja", "ko"]:
    d = pickle.load(open(os.path.expanduser(f"~/cjkwork/sample_{lang}_train.pkl"), "rb"))
    st = collections.Counter(); ntok = collections.defaultdict(list)
    ex = []
    ac = sqlite3.connect(":memory:")
    for qid, q in d["queries"]:
        T = {n: S[n].query_tokens(conn if n.startswith("fts5") else ac, q)
             for n in ["fts5_cjk", "fts5_cjk_qfirst", "fts5_cjk_qedge", "app_bigram", "app_bigram_first", "app_bigram_edge"]}
        for n, t in T.items(): ntok[n].append(len(t))
        st["n"] += 1
        st["qfirst==app_bigram_first"] += set(T["fts5_cjk_qfirst"]) == set(T["app_bigram_first"])
        st["qedge==app_bigram_edge"] += set(T["fts5_cjk_qedge"]) == set(T["app_bigram_edge"])
        st["fts5_cjk==app_bigram"] += set(T["fts5_cjk"]) == set(T["app_bigram"])
        st["qfirst_adds_tokens"] += len(T["fts5_cjk_qfirst"]) > len(T["fts5_cjk"])
        st["qfirst_subset_qedge"] += set(T["fts5_cjk_qfirst"]) <= set(T["fts5_cjk_qedge"])
        if set(T["fts5_cjk_qfirst"]) != set(T["app_bigram_first"]) and len(ex) < 5:
            ex.append({"q": q, "qfirst": T["fts5_cjk_qfirst"], "app_bigram_first": T["app_bigram_first"]})
    mean = {n: sum(v)/len(v) for n, v in ntok.items()}
    out["langs"][lang] = {"counts": dict(st), "mean_query_tokens": mean, "mismatch_examples": ex}
    print(lang, dict(st), {k: round(v, 2) for k, v in mean.items()})
    for e in ex: print("   mismatch:", e)
json.dump(out, open(os.path.expanduser("~/qf/query_token_checks.json"), "w"), ensure_ascii=False, indent=1)
