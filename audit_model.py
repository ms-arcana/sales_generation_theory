# -*- coding: utf-8 -*-
"""モデルの整合性チェック ―― **番号が増えすぎたので、機械で棚卸しする。**

第8版は、7つの中心命題・16の依存規則・15のアノマリー由来条件を
**3つの原理と5つの記法**へ畳んだ。そのとき効いたのは「畳めるかどうか」ではなく
**被覆グリッドで穴を見た**ことだった（SPEC8 §5）。同じことをもう一度やる。

ここで見るのは六つ。**どれも人の記憶ではなく、コードと台帳の突き合わせで出す。**

  (1) 台帳 ↔ 理由コード      台帳に在ってコードに無い／コードに在って台帳に無い
  (2) 理由コード ↔ 表示文    `messages.json` に文が無いコード／使われていない文
  (3) 決定表の配管（V3）     compile_deal の鍵 ↔ cells8 の白名簿 ↔ 指示文が読む鍵
  (4) 申告欄の配管           Declared の欄 ↔ REQS ↔ to_declared
  (5) 較正の棚卸し（V5）     CALIBRATED_CODES ↔ 実在する理由コード
  (6) 発火していない検査      8セル＋既存走行で一度も出ていないコード

  python3 audit_model.py
"""
import ast
import glob
import json
import re
from collections import Counter

SRC = open("sales_logic.py", encoding="utf-8").read()
MSG = json.load(open("messages.json", encoding="utf-8"))
LEDGER = open("アノマリー台帳.md", encoding="utf-8").read()

# **この正規表現そのものが、浅い一致を踏みかけた（8件目・未然）。**
# `[A-Z][A-Z0-9]*` は `R6b` の小文字 b を拾えず、`R6b_LT_SHORT` を「実在しないコード」と
# 報告しかけた。**監査の道具にも同じ型の誤りが出る。**
CODE_RE = re.compile(r'"([A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)"')
NUM_RE = re.compile(r"\bA(\d+)([a-z]?)\b")


def codes_in_source():
    return sorted(set(CODE_RE.findall(SRC)))


def ledger_numbers():
    """台帳の表の行から番号を拾う（`| **A50** |` の形）"""
    out = set()
    for line in LEDGER.splitlines():
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip().strip("*")
        for m in NUM_RE.finditer(cell):
            out.add(f"A{int(m.group(1))}{m.group(2)}")
        if "〜" in cell or "－" in cell:      # A1〜A23 のような範囲
            ms = NUM_RE.findall(cell)
            if len(ms) == 2:
                for i in range(int(ms[0][0]), int(ms[1][0]) + 1):
                    out.add(f"A{i}")
    return out


def numbers_in_codes(codes):
    out = set()
    for c in codes:
        m = re.match(r"^A(\d+)([A-Z]?)_", c)
        if m:
            out.add(f"A{int(m.group(1))}{m.group(2).lower()}")
    return out


def whitelist_keys():
    """cells8_v10.run() の白名簿（rec.update の tuple）"""
    s = open("cells8_v10.py", encoding="utf-8").read()
    m = re.search(r"rec\.update\(\{k: d\.get\(k\) for k in\s*\((.*?)\)\}\)", s, re.S)
    return set(re.findall(r'"([a-z0-9_]+)"', m.group(1))) if m else set()


def compile_keys():
    """compile_deal が返す dict の鍵（AST で取る。実行しない）"""
    tree = ast.parse(SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "compile_deal":
            for n in ast.walk(node):
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
                    ks = {k.value for k in n.value.keys
                          if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                    if len(ks) > 8:
                        return ks
    return set()


def prompt_keys():
    """指示文が決定表から読む鍵"""
    s = open("prompts8_v11.py", encoding="utf-8").read()
    return set(re.findall(r'rec\.get\("([a-z0-9_]+)"\)', s)) | set(
        re.findall(r'rec\["([a-z0-9_]+)"\]', s))


def declared_fields():
    tree = ast.parse(SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Declared":
            return {n.target.id for n in node.body if isinstance(n, ast.AnnAssign)}
    return set()


def to_declared_fields():
    s = open("validate8_v12.py", encoding="utf-8").read()
    m = re.search(r"return Declared\((.*?)\n    \)", s, re.S)
    return set(re.findall(r"^\s*([a-z0-9_]+)=", m.group(1), re.M)) if m else set()


def req_fields():
    return set(re.findall(r'Req\("([a-z0-9_]+)"', SRC))


def fired_codes():
    """8セルの決定表と、手元の走行物で一度でも出たコード"""
    seen = Counter()
    for f in glob.glob("decisions8_v1*.json") + glob.glob("verified*.json"):
        try:
            txt = open(f, encoding="utf-8").read()
        except Exception:
            continue
        for c in CODE_RE.findall(txt):
            seen[c] += 1
    return seen


def main():
    codes = codes_in_source()
    msg_codes = set(MSG["findings"]) | set(MSG["judgments"])
    print(f"══ モデル整合性チェック   理由コード {len(codes)} ／ 表示文 {len(msg_codes)}\n")

    # (1) 台帳 ↔ 理由コード
    led, incode = ledger_numbers(), numbers_in_codes(codes)
    only_led = sorted(led - incode, key=lambda x: (int(re.sub(r"\D", "", x)), x))
    only_code = sorted(incode - led, key=lambda x: (int(re.sub(r"\D", "", x)), x))
    print(f"(1) 台帳の番号 {len(led)} ／ 理由コードに現れる番号 {len(incode)}")
    print(f"    台帳に在ってコードに無い（設計のみ・吸収済み・未着手）: {len(only_led)}")
    print(f"      {only_led}")
    print(f"    ★コードに在って台帳に無い: {only_code or 'なし'}\n")

    # (2) 理由コード ↔ 表示文
    no_msg = sorted(set(codes) - msg_codes)
    no_code = sorted(msg_codes - set(codes))
    print(f"(2) 表示文が無いコード {len(no_msg)}  {no_msg[:8]}")
    print(f"    コードに無い表示文 {len(no_code)}  {no_code[:8]}\n")

    # (3) 決定表の配管（V3）
    ck, wl, pk = compile_keys(), whitelist_keys(), prompt_keys()
    drop = sorted((ck & pk) - wl)
    unused = sorted(wl - ck)
    print(f"(3) compile_deal の鍵 {len(ck)} ／ 白名簿 {len(wl)} ／ 指示文が読む鍵 {len(pk)}")
    print(f"    ★計算しているのに白名簿に無く、指示文が読もうとする鍵: {drop or 'なし'}")
    print(f"    白名簿に在るが compile_deal に無い: {unused or 'なし'}\n")

    # (4) 申告欄の配管
    df, td, rf = declared_fields(), to_declared_fields(), req_fields()
    print(f"(4) Declared の欄 {len(df)} ／ REQS {len(rf)} ／ to_declared {len(td)}")
    from sales_logic import REQ_RETIRED as _RR
    print(f"    ★REQS に無い欄: {sorted(df - rf - set(_RR)) or 'なし'}")
    from sales_logic import REQ_RETIRED
    print(f"    ★to_declared が渡していない欄: {sorted(df - td - set(REQ_RETIRED)) or 'なし'}\n")

    # (5) 較正の棚卸し（V5）
    from sales_logic import CALIBRATED_CODES
    ghost = sorted(set(CALIBRATED_CODES) - set(codes))
    print(f"(5) 較正由来の判定 {len(CALIBRATED_CODES)} 件")
    for k, v in sorted(CALIBRATED_CODES.items()):
        print(f"      {k:28} ← {v}")
    print(f"    ★実在しないコードを較正表が指している: {ghost or 'なし'}\n")

    # (6) 発火していない検査
    fired = fired_codes()
    never = sorted(set(codes) - set(fired))
    print(f"(6) 一度でも出たコード {len(set(codes) & set(fired))} ／ 一度も出ていない {len(never)}")
    print(f"    （出るはずがない・出るはずなのに出ていない・配線されていない の仕分けが要る）")
    for c in never[:24]:
        print(f"      {c}")
    if len(never) > 24:
        print(f"      … 他 {len(never)-24} 件")


if __name__ == "__main__":
    main()
