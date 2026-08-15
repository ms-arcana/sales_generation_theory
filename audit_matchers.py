# -*- coding: utf-8 -*-
"""V1 物差しの全数検分 ―― **文字列に触っている全箇所を、実データに当て直す。**

引き継ぎ書 第14版 §5 #3。A54（浅い一致）は8件で、うち2件は未然だった。
**当たっているように見えて当たっていない**物差しを、当てて数えて見つける。

見るのは四つ。

  (1) 死んでいる物差し   実データに一度も当たらない。前の版の語彙で較正されたまま
  (2) 境界を取らない一致  部分一致で、より長い語の一部に当たっている
  (3) ⊥ の取りこぼし     ⊥ の語彙表が、実データに出る空値を覆えていない
  (4) 表そのものの傷     重複・包含（短い項が長い項を食う）／順序に依存する表の並び
  (5) ⊥ を生の表で判定    `x in UNIT_UNKNOWN` と書いた箇所。**`is_bottom` を通っていない**

    python3 audit_matchers.py

実データは手元にあるもの全部 ―― 8セル×各版の生成物、25業界21件（bundle があれば）、
買い手の逐語。**外部ネットワークを使わない。**
"""
import glob
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter

import sales_logic as SL


# ────────────────────────────────────────────────── 実データを集める
def corpus():
    """(出所, 段, 本文) の並び。売り手の紙だけ ―― 物差しはこれに当てる設計"""
    out = []
    for path in sorted(glob.glob("gen13*/out_*.json")) + sorted(glob.glob("run12*/out_*.json")) \
            + sorted(glob.glob("pair12*/out_*.json")) + sorted(glob.glob("oracle137/out_*.json")):
        try:
            g = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for s in (g.get("slides") or []):
            out.append((os.path.basename(path), str(s.get("stage", "?")), s.get("text") or ""))
    # 25業界21件（別枝。取り込んでいれば読む）
    r = subprocess.run(["git", "show", "bundle/industry23:verified_ind.json"],
                       capture_output=True, text=True)
    if not r.returncode:
        d = json.loads(r.stdout)
        for rec in (d.get("data") if isinstance(d, dict) else d):
            for st, tx in (rec.get("copy") or {}).items():
                out.append((f"ind:{rec['id']}", st, tx or ""))
    return out


def buyer_words():
    """買い手の逐語。**売り手の物差しを当てる先ではない** ―― 誤検出の下限を見るのに使う"""
    try:
        d = json.load(open("ind25_data.json", encoding="utf-8"))
    except Exception:
        return []
    out = []
    for r in d:
        for k in ("逐語", "侮辱"):
            if isinstance(r.get(k), str):
                out.append((r["id"], k, r[k]))
    return out


# ────────────────────────────────────────────────── 物差しの一覧
def matchers():
    """(名前, 種別, 項の並び, 当てる先) ―― `sales_logic` の実体を参照する。写さない。"""
    return [
        ("V0",               "substr", SL.V0,               "散文（R9 設計語の漏洩）"),
        ("V0_RE",            "regex",  SL.V0_RE,            "散文（R9 設計語の漏洩）"),
        ("POSSESSION_WORDS", "substr", SL.POSSESSION_WORDS, "②の疑問文（A47）"),
        ("EST_MARKS",        "substr", SL.EST_MARKS,        "量の申告（A28 試算の印）"),
        ("UNIT_TOKENS",      "substr", SL.UNIT_TOKENS,      "値の中の単位（R10b・R20）"),
        ("UNIT_UNKNOWN",     "exact",  SL.UNIT_UNKNOWN,     "単位の ⊥ 語彙"),
        ("SOURCE_KINDS",     "substr", SL.SOURCE_KINDS,     "出所の語彙（A28・A49）"),
        ("EXPR_MARKS",       "substr", SL.EXPR_MARKS,       "式の印（R20）"),
        ("Q_SRC",            "exact",  SL.Q_SRC,            "量の出所（N₄′）"),
        ("DISCLAIM_RE",      "regex",  [SL.DISCLAIM_RE.pattern], "断り書き（A46）"),
        ("S2_QUESTION_RE",   "regex",  [SL.S2_QUESTION_RE.pattern], "②の疑問文（A47）"),
        ("S4_DATE_RE",       "regex",  [SL.S4_DATE_RE.pattern], "④の日付（A41b）"),
        ("AMOUNT_RE",        "regex",  [SL.AMOUNT_RE.pattern], "金額（A45）"),
        ("SLOT_RE",          "regex",  [SL.SLOT_RE],        "記入欄（A28・R20）"),
    ]


def hits(kind, terms, text):
    got = []
    for t in terms:
        if kind == "regex":
            got += [(t, m.group(0), m.start()) for m in re.finditer(t, text)]
        elif kind == "substr":
            i = text.find(t)
            while i >= 0:
                got.append((t, t, i))
                i = text.find(t, i + 1)
        else:                                   # exact
            if text.strip() == t:
                got.append((t, t, 0))
    return got


# ────────────────────────────────────────────────── (4) 表そのものの傷
def table_faults(name, kind, terms):
    out = []
    seen = Counter(terms)
    dup = [t for t, n in seen.items() if n > 1]
    if dup:
        out.append(f"重複した項 {dup}")
    # 正規化して同じになる別表記（全角/半角・互換文字）
    norm = {}
    for t in terms:
        k = unicodedata.normalize("NFKC", t)
        norm.setdefault(k, []).append(t)
    for k, v in norm.items():
        if len(set(v)) > 1:
            out.append(f"NFKC で同一になる別表記 {sorted(set(v))}")
    if kind == "substr":
        # 短い項が長い項を食う（先に当たると長いほうが取れない）
        eat = [(a, b) for a in terms for b in terms
               if a != b and a in b and len(a) < len(b)]
        if eat:
            out.append(f"短い項が長い項を含む（順序に依存）{eat[:4]}")
    return out


def main():
    corp, buyers = corpus(), buyer_words()
    n_txt = len(corp)
    print(f"══ V1 物差しの全数検分   売り手の本文 {n_txt}件 ／ 買い手の逐語 {len(buyers)}件\n")
    if not n_txt:
        sys.exit("★ 実データが無い。生成物のディレクトリを確認してください")

    print(f"{'物差し':20}{'種別':7}{'項':>4}{'当たった本文':>12}{'延べ':>7}  所見")
    dead, faults = [], {}
    for name, kind, terms, where in matchers():
        terms = list(terms)
        n_doc = tot = 0
        per_term = Counter()
        for src, st, tx in corp:
            h = hits(kind, terms, tx)
            if h:
                n_doc += 1
                tot += len(h)
                per_term.update(t for t, _, _ in h)
        f = table_faults(name, kind, terms)
        if f:
            faults[name] = f
        note = []
        if tot == 0:
            note.append("★一度も当たらない")
            dead.append(name)
        unused = [t for t in terms if not per_term[t]]
        if tot and unused and kind != "regex":
            note.append(f"死んだ項 {len(unused)}/{len(terms)}")
        if f:
            note.append("表に傷")
        print(f"{name:20}{kind:7}{len(terms):>4}{n_doc:>12}{tot:>7}  {'／'.join(note)}")

    if faults:
        print("\n=== (4) 表そのものの傷 ===")
        for k, v in faults.items():
            for x in v:
                print(f"  {k:20} {x}")

    # ── (2) 境界を取らない一致：部分一致の当たりが、より長い語の一部になっていないか
    print("\n=== (2) 境界を取らない一致の疑い（当たりの前後を見る）===")
    JOIN = re.compile(r"[\wぁ-んァ-ヴ一-龥ー]")
    found = False
    for name, kind, terms, where in matchers():
        if kind != "substr":
            continue
        bad = Counter()
        sample = {}
        for src, st, tx in corp:
            for t, got, i in hits(kind, list(terms), tx):
                left = tx[i - 1] if i else ""
                right = tx[i + len(got)] if i + len(got) < len(tx) else ""
                if JOIN.match(left or "") or JOIN.match(right or ""):
                    bad[t] += 1
                    sample.setdefault(t, tx[max(0, i - 12):i + len(got) + 12])
        if bad:
            found = True
            print(f"  {name}")
            for t, n in bad.most_common(6):
                print(f"      「{t}」{n:4}件  例: …{sample[t]}…")
    if not found:
        print("  なし")

    # ── (3) ⊥ の取りこぼし：単位欄・値欄に実際に入っている「空っぽ」の表記
    print("\n=== (3) ⊥ の取りこぼし ===")
    vals = Counter()
    for path in sorted(glob.glob("gen13*/out_*.json")) + sorted(glob.glob("run12*/out_*.json")) \
            + sorted(glob.glob("pair12*/out_*.json")):
        try:
            dd = (json.load(open(path, encoding="utf-8")).get("declared") or {})
        except Exception:
            continue
        for q in (dd.get("s6_quantities") or []):
            if isinstance(q, dict):
                for k, v in q.items():
                    if isinstance(v, str) and len(v.strip()) <= 6:
                        vals[v.strip()] += 1
    known = set(SL.UNIT_UNKNOWN)
    susp = {v: n for v, n in vals.items()
            if v not in known and (v == "" or SL.is_bottom(v)
                                   or re.fullmatch(r"[\s―ー\-－—–_＿・．.]*", v or ""))}
    if susp:
        for v, n in sorted(susp.items(), key=lambda x: -x[1]):
            print(f"  {'（空文字）' if v == '' else v!r:14} {n:4}件  is_bottom={SL.is_bottom(v)}  "
                  f"UNIT_UNKNOWN に{'在る' if v in known else '**無い**'}")
    else:
        print("  申告の値欄に、UNIT_UNKNOWN の外の空表記は出ていない")

    # ── (4b) 順序に依存する表：長い語が短い語より先に並んでいるか
    print("\n=== (4b) 順序に依存する表の並び（`unit_in_value` は最初の一致で判定する）===")
    U = list(SL.UNIT_TOKENS)
    wrong = [(a, i, b, j) for i, a in enumerate(U) for j, b in enumerate(U)
             if a != b and a in b and i < j]
    print(f"  UNIT_TOKENS: {'★短い語が先にある（長い語へ到達できない）: ' + str(wrong) if wrong else 'ならびは正しい（長い語が先）'}")

    # ── (5) ⊥ を生の表で判定している箇所
    print("\n=== (5) ⊥ を `is_bottom` を通さず、生の表で判定している箇所 ===")
    print("      `is_bottom` は UNIT_UNKNOWN ＋ SLOT_RE（記入欄）で判定する。")
    print("      生の表だけを引くと **記入欄【　　　】が ⊥ と読まれない**。")
    import ast
    src = open("sales_logic.py", encoding="utf-8").read()
    tree = ast.parse(src)
    lines = src.splitlines()
    raw = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        if fn.name == "is_bottom":
            continue                      # ここだけが表を引いてよい
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare) and any(
                    isinstance(o, (ast.In, ast.NotIn)) for o in n.ops):
                for c in n.comparators:
                    if isinstance(c, ast.Name) and c.id == "UNIT_UNKNOWN":
                        raw.append((n.lineno, fn.name, lines[n.lineno - 1].strip()))
    if raw:
        for ln, fn, text in sorted(set(raw)):
            print(f"  ★ sales_logic.py:{ln}  {fn}()")
            print(f"       {text[:96]}")
        print(f"\n  {len(set(raw))}箇所。**`is_bottom(x)` に置き換えるのが筋**"
              f"（検査の定義域なので、提案までにとどめる）。")
    else:
        print("  なし ―― ⊥ の判定はすべて `is_bottom` を通っている")

    if dead:
        print(f"\n=== (1) 実データに一度も当たらなかった物差し: {dead} ===")
        print("      **当たらない＝壊れている、ではない。**V0／V0_RE は R9（設計語の漏洩）で、")
        print("      0件は「漏れていない」という結果。当て先が本文でない表（exact）は対象外。")


if __name__ == "__main__":
    main()
