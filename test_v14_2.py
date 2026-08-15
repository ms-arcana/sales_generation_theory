# -*- coding: utf-8 -*-
"""第14.2版の回帰 ―― VS Code の第14.1版報告を受けた修正。

**`test_sales_logic.py` とは別ファイルにしてあります。**
第14.1版で VS Code 側が同ファイルを編集しているので、突き合わせの衝突を避けるためです。
統合するときは、この節を `test_sales_logic.py` の末尾へ移してください。

  python3 test_v14_2.py
"""
import json
import re

from sales_logic import Declared, check_quantity_sources

FAIL = []


def check(name, ok, detail=""):
    print(("ok  " if ok else "NG  ") + name + ("" if ok else f"  {detail}"))
    if not ok:
        FAIL.append(name)


print("── A49 の実装漏れ：〈出所〉を割ったとき、A28 の橋を直し忘れていた")
# 第13.10版で source を pay_source / ret_source に割ったが、check_quantity_sources は
# 旧 source しか読んでいなかった。新欄で申告すると出所が一つも読めず、
# A28_SOURCE_UNDECLARED が出る（＝出所を書いたのに「書いていない」と言われる）。
_CH = (("店長", ["財源"], ["粗利"], "現場"),)
_BODY = {"⑥": "本文。試算の語も記入欄【　　　】も置いてある。"}


def q(**kw):
    d = {"seat": "店長", "kappa": "財源", "pay": "180", "pay_unit": "万円",
         "ret": "240", "ret_unit": "万円", "per": "月あたり"}
    d.update(kw)
    return d


_f, _j = check_quantity_sources(_BODY, Declared(
    s6_quantities=(q(pay_source="試算", ret_source="売り手の実績"),),
    s6_to_sales=("戻る額の確認",)), _CH)
check("A28 割った欄（pay_source / ret_source）から出所を読む",
      not any(x.code == "A28_SOURCE_UNDECLARED" for x in _j), [x.code for x in _j])
check("A28 割った出所は集合として扱う（片方が試算なら試算の要求が掛かる）",
      not any(x.code == "A28_SOURCE_MISSING" for x in _j), [x.code for x in _j])
# 本文そのものに「試算」と書くと自分で当たってしまう（浅い一致は自分の試験にも湧く）
_f, _j = check_quantity_sources({"⑥": "本文。裏づけの語はどこにも置いていない。"}, Declared(
    s6_quantities=(q(pay_source="試算", ret_source="売り手の実績"),),
    s6_to_sales=("戻る額の確認",)), _CH)
check("A28 片方が試算なら、本文に試算の語が無いと停止する",
      any(x.code == "A28_ESTIMATE_UNMARKED" for x in _f), [x.code for x in _f])
_f, _j = check_quantity_sources(_BODY, Declared(
    s6_quantities=(q(source="売り手の実績"),), s6_to_sales=()), _CH)
check("A28 旧 source だけでも従来どおり読める（走行データとの突合）",
      not any(x.code == "A28_SOURCE_UNDECLARED" for x in _j), [x.code for x in _j])
_f, _j = check_quantity_sources(_BODY, Declared(s6_quantities=(q(),), s6_to_sales=()), _CH)
check("A28 出所をどこにも書いていなければ申し送る",
      any(x.code == "A28_SOURCE_UNDECLARED" for x in _j), [x.code for x in _j])


print("\n── A53b：指示文が要求している申告欄が、生成スキーマに在ること")
# 第14.1版に VS Code が検出。指示文は 3/3 arm で頼んでいたのに答える欄が無く、
# 36件の生成物すべてで鍵すら現れなかった（0/36）。A46・A47 の申告側は原理的に出られなかった。
_JS = open("wf_gen137.js", encoding="utf-8").read()
for _fld in ("s2_asks_possession", "s5_disclaimers", "pay_source", "ret_source"):
    check(f"A53b GEN_SCHEMA に {_fld} が在る", f"{_fld}:" in _JS)
_req = re.search(r"required:\s*\['s5_is_constraint_disclosure'(.*?)\]", _JS, re.S)
check("A53b s2_asks_possession と s5_disclaimers は required（答えないことを選ばせない）",
      _req and "s2_asks_possession" in _req.group(1) and "s5_disclaimers" in _req.group(1))
# 指示文の側が現に頼んでいること（片側だけ直して満足しないため）
_P = open("prompts8_v11.py", encoding="utf-8").read()
check("A53b 指示文の側も、その二つを日本語で頼んでいる",
      "s2_asks_possession" in _P and "s5_disclaimers" in _P)


print("\n── 表示文のずれ（第14.1版の (2) が挙げた2件）")
_M = json.load(open("messages.json", encoding="utf-8"))
_all = set(_M["findings"]) | set(_M["judgments"])
check("A19_ORG_COST_POSITIVE に表示文が付いた", "A19_ORG_COST_POSITIVE" in _M["findings"])
check("R10b_UNIT_REVERTED は退役（第12.1版に R10b_UNIT_REPLACED へ統合済み）",
      "R10b_UNIT_REVERTED" not in _all)

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")
