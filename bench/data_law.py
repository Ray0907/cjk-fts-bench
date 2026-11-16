"""Taiwan law corpus loader (kong0107/mojLawSplitJSON, MOJ Open Government Data License v1.0).

Structure: FalVMingLing/<PCode>.json, key "法規性質" in {憲法, 法律, 命令}; "法規內容" is a
list of items, those with "條文內容" are articles. We keep 法律 only (excludes 命令 and 憲法),
skip empty and "（刪除）" articles, and only strip whitespace.
Data is untrusted: it is only parsed as JSON, never executed.
"""
import glob
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SRC = os.path.join(DATA, "src", "mojLawSplitJSON")
CACHE = os.path.join(DATA, "law_articles.jsonl")
VERSION = os.path.join(DATA, "law_VERSION.txt")
REPO = "https://github.com/kong0107/mojLawSplitJSON"
KIND = "法律"


def _clone():
    if os.path.isdir(os.path.join(SRC, "FalVMingLing")):
        return
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", REPO, SRC], check=True)


def _commit():
    out = subprocess.run(["git", "-C", SRC, "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip()


def _is_deleted(t):
    return t in ("（刪除）", "(刪除)", "刪除")


def build_cache():
    _clone()
    arts = []
    for f in sorted(glob.glob(os.path.join(SRC, "FalVMingLing", "*.json"))):
        with open(f, encoding="utf-8-sig") as fh:
            d = json.load(fh)
        if d.get("法規性質") != KIND:
            continue
        for a in d.get("法規內容", []):
            t = (a.get("條文內容") or "").strip()
            if t and not _is_deleted(t):
                arts.append(t)
    os.makedirs(DATA, exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        for t in arts:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(VERSION, "w") as fh:
        fh.write(f"{REPO}\ncommit {_commit()}\nkind {KIND}\narticles {len(arts)}\n")
    return arts


def load_articles():
    """List of article texts; index in list == doc rowid (0-based)."""
    if os.path.exists(CACHE) and os.path.exists(VERSION):
        with open(CACHE, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh]
    return build_cache()


def commit_hash():
    if os.path.exists(VERSION):
        for l in open(VERSION):
            if l.startswith("commit "):
                return l.split()[1]
    return ""


if __name__ == "__main__":
    a = load_articles()
    print(len(a), commit_hash())
