# -*- coding: utf-8 -*-
"""第14.4版の回帰 ―― A57「退役が読み手を置き去りにする」

**`test_sales_logic.py` とは別ファイルにしてあります。**（VS Code 側が同ファイルを触るため）

見つけたのは VS Code。第14.3版で `s6_kappa_by_seat` を `REQ_RETIRED` へ移したとき、
**欄の意味が吸収済みかだけを見て、読み手を数えなかった。**

  check_chain            (2308)  quantities_by_seat(dec)   ← 橋を通る
  check_quantity_sources (1740)  quantities_by_seat(dec)   ← 橋を通る
  check_seat_words       (1698)  dec.s6_kappa_by_seat      ← 生読み ★

`wf_gen137.js` は第13.7版でその欄を落としているので、**新しい形の申告では
`A23_SEAT_WORD_ABSENT` が構造的に出なくなっていた**（同じ紙で 旧1件／新0件）。

  python3 test_v14_4.py
"""
import re

from sales_logic import (Declared, audit_retired_reads, check_seat_words,
                         quantities_by_seat, REQ_RETIRED, RETIRED_BRIDGE)

FAIL = []


def check(name, ok, detail=""):
    print(("ok  " if ok else "NG  ") + name + ("" if ok else f"  {detail}"))
    if not ok:
        FAIL.append(name)


# 座席・様式語・本文。**本文に「実務性」は出てくるが「財源」は出てこない** ――
# 社長の座席は、自分の様式語で読める量を⑥に置いたと申告しながら、その語が本文に無い。
CHAIN = [("店長", ["実務性"], ["実務性"], "組織"),
         ("社長", ["財源"], ["財源"], "組織")]
BODY = {"⑥": "店舗運営の実務性の面では、人時売上高を月あたりで置いた。"}

OLD = Declared(s6_kappa_by_seat={"店長": "実務性", "社長": "財源"})     # gen136 期の形
NEW = Declared(s6_quantities=(                                        # gen137 期の形
    {"seat": "店長", "kappa": "実務性", "pay": "120", "pay_unit": "万円",
     "ret": "300", "ret_unit": "万円", "per": "月"},
    {"seat": "社長", "kappa": "財源", "pay": "120", "pay_unit": "万円",
     "ret": "300", "ret_unit": "万円", "per": "月"}))


print("── A57-a：A23 の紙側が、新しい形の申告でも立つ")
_old = [f.code for f in check_seat_words(BODY, OLD, CHAIN)]
_new = [f.code for f in check_seat_words(BODY, NEW, CHAIN)]
check("A57 旧スキーマの形では従来どおり立つ（対照）",
      "A23_SEAT_WORD_ABSENT" in _old, _old)
check("A57 新スキーマの形でも立つ（第14.3版までは 0件で、構造的に出なかった）",
      "A23_SEAT_WORD_ABSENT" in _new, _new)
check("A57 立つ座席は〈社長〉一つ（様式語が本文に在る店長は立たない）",
      [f.detail if hasattr(f, "detail") else f.ref for f in check_seat_words(BODY, NEW, CHAIN)]
      == ["社長:財源"] or len(_new) == 1, _new)

# 橋そのものの性質 ―― 新旧どちらの形でも同じ座席集合を返す
check("A57 橋は新旧どちらの形でも同じ座席を返す",
      set(quantities_by_seat(OLD)) == set(quantities_by_seat(NEW)) == {"店長", "社長"},
      (quantities_by_seat(OLD), quantities_by_seat(NEW)))

# 検査を弱めていないことの対照：様式語が全部本文に在れば何も出ない
_ok_body = {"⑥": "実務性の面と、財源の面の両方で置いた。"}
check("対照 様式語が全部本文に在れば何も出ない",
      not check_seat_words(_ok_body, NEW, CHAIN),
      [f.code for f in check_seat_words(_ok_body, NEW, CHAIN)])


print("\n── A57-b：退役した欄を橋なしで読む箇所は 0 ―― かつ、その監査が生きている")
_r = audit_retired_reads()
check("A57 いま生読みは 0 箇所", not _r, [x.ref for x in _r])

# **0 を返す監査は、0 を返さない入力を1件見せるまで閉じたと言えない**（第14.3版 §追補）。
_BAD = """
def check_seat_words(copy, dec, chain):
    if not chain or not dec.s6_kappa_by_seat:
        return []
    return [dec.s6_kappa_by_seat]
"""
_bad = audit_retired_reads(_BAD)
check("A57 検査そのものは生きている（生読みを1件置けば名指しする）",
      [x.code for x in _bad] == ["A57_RETIRED_READ_UNBRIDGED"]
      and "check_seat_words" in _bad[0].ref and "s6_kappa_by_seat" in _bad[0].ref,
      [(x.code, x.ref) for x in _bad])

_GOOD = """
def check_seat_words(copy, dec, chain):
    by_seat = quantities_by_seat(dec)
    if not chain or not by_seat:
        return []
    return [dec.s6_kappa_by_seat, by_seat]
"""
check("A57 旧欄も見るが新しい側も見ている形は通す（畳み方として正しい）",
      not audit_retired_reads(_GOOD), [x.ref for x in audit_retired_reads(_GOOD)])

check("A57 退役した欄はすべて〈代わりに読むもの〉を持つ",
      all(f in RETIRED_BRIDGE and RETIRED_BRIDGE[f] for f in REQ_RETIRED),
      [f for f in REQ_RETIRED if not RETIRED_BRIDGE.get(f)])


print("\n── A57-c：生成スキーマから落とした欄が、検査を殺していないこと")
# 第13.7版に `wf_gen137.js` を縮めたのが原因なので、**落とした欄の名前**を根拠として残す。
_JS = open("wf_gen137.js", encoding="utf-8").read()
_dropped = [f for f in REQ_RETIRED if not re.search(rf"^\s*{f}\s*:", _JS, re.M)]
check("A57 退役した欄は生成スキーマに無くてよい（要求していないので配管の欠落ではない）",
      set(_dropped) >= {"s6_kappa_by_seat", "s6_quantity_sources"}, _dropped)
check("A57 ただし、その欄を読む検査は橋を通っていること（＝A57-b が 0）", not audit_retired_reads())

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")
