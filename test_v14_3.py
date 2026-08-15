# -*- coding: utf-8 -*-
"""第14.3版の回帰 ―― A55「⊥ を決める述語は一つ／⊥ を別の欄で代用しない」

**`test_sales_logic.py` とは別ファイルにしてあります。**
VS Code 側が同ファイルを編集しているので、突き合わせの衝突を避けるためです。
統合するときは、この節を `test_sales_logic.py` の末尾へ移してください。

第14.1版（VS Code）の §10・§12 が挙げた二つを、型として一つに畳んだものが A55 です。

  #2  `check_dates_v7` の `dcd = s6_decide_date or s6_start_date`  … ⊥ を別の欄で代用した
  #3  `check_decidable` の4箇所の生 `in UNIT_UNKNOWN`              … ⊥ の述語が二つあった

  python3 test_v14_3.py
"""
import inspect
import re

from sales_logic import (Declared, check_dates_v7, check_decidable, check_gates,
                         is_bottom)

FAIL = []


def check(name, ok, detail=""):
    print(("ok  " if ok else "NG  ") + name + ("" if ok else f"  {detail}"))
    if not ok:
        FAIL.append(name)


SLOT = "【　　　】"          # 営業が埋める記入欄。**これは値ではなく ⊥ である**
CHAIN = [("工場長", ["実務性"], ["応援労務費"], "組織")]


def q(**over):
    base = dict(seat="工場長", kappa="人時", pay="120", pay_unit="万円",
                ret="300", ret_unit="万円", per="月", pay_source="買い手データ",
                ret_source="売り手の実績")
    base.update(over)
    return base


def dec_q(**over):
    return Declared(s6_quantities=(q(**over),))


def codes(pair):
    f, j = pair
    return [x.code for x in f], [x.code for x in j]


# ═══════════════════════════════════════ #2 ⊥ を別の欄で代用しない（N₂／型5 の述語版）
print("── A55-a：決定日が ⊥ のとき、着手日を決定日の代理にしない")

# 第14.1版の反例そのもの。決定日が無く、着手日だけが在る紙。
_D = Declared(s6_start_date="2027-01-20", s6_self_check=True)
_f, _j = check_dates_v7(_D, "2026-12-28")
check("A55 決定日が ⊥ なら R12b は停止しない（誤停止 3/9・うち2件は買い手が進めた）",
      "R12b_START_AFTER_DEADLINE" not in [x.code for x in _f], codes((_f, _j)))
check("A55 受け皿は R12b_START_UNDECLARED（黙って通さない）",
      "R12b_START_UNDECLARED" in [x.code for x in _j], codes((_f, _j)))
check("A55 決定日そのものが未申告であることも申し送る",
      "A37_DECIDE_UNDECLARED" in [x.code for x in _j], codes((_f, _j)))

# 決定日を書けば、従来どおり停止する（検査を弱めたのではない）
_f, _j = check_dates_v7(Declared(s6_decide_date="2027-01-20", s6_self_check=True), "2026-12-28")
check("A55 決定日を書けば従来どおり停止（検査を消したのではない）",
      "R12b_START_AFTER_DEADLINE" in [x.code for x in _f], codes((_f, _j)))

# 記入欄も ⊥ である（`is None` ではなく `is_bottom` で見ていること）
_f, _j = check_dates_v7(Declared(s6_decide_date=SLOT, s6_start_date="2027-01-20",
                                 s6_self_check=True), "2026-12-28")
check("A55 決定日が記入欄でも ⊥ として扱う（`is None` では拾えない）",
      "R12b_START_AFTER_DEADLINE" not in [x.code for x in _f]
      and "R12b_START_UNDECLARED" in [x.code for x in _j], codes((_f, _j)))

print("\n── A55-b：同じ代用が `check_gates`（A41）にも在った ―― VS Code の報告に無い2箇所目")
# 窓を越えたかは〈決定日〉についての述語。着手日はその代理にならない。
_G = (("2026-11-30", "予算委員会", 6),)
_f, _j = check_gates(Declared(s6_start_date="2026-12-20"), _G)
check("A55 決定日が ⊥ なら A41 は停止しない",
      "A41_DECIDE_AFTER_GATE" not in [x.code for x in _f], codes((_f, _j)))
check("A55 受け皿は A41_GATE_UNCHECKED",
      "A41_GATE_UNCHECKED" in [x.code for x in _j], codes((_f, _j)))
check("A55 着手日は着手日として別に縛られる（A41b は生きている）",
      "A41B_START_BEFORE_GATE" not in [x.code for x in _f], codes((_f, _j)))
_f, _j = check_gates(Declared(s6_decide_date="2026-12-20"), _G)
check("A55 決定日を書けば従来どおり停止",
      "A41_DECIDE_AFTER_GATE" in [x.code for x in _f], codes((_f, _j)))
_f, _j = check_gates(Declared(s6_decide_date="2026-11-01", s6_start_date="2026-11-10"), _G)
check("A41b 着手が窓より前なら、決定日が正しくても停止",
      "A41B_START_BEFORE_GATE" in [x.code for x in _f], codes((_f, _j)))


# ═══════════════════════════════════════ #3 ⊥ を決める述語は一つ（`is_bottom`）
print("\n── A55-c：`check_decidable` の4箇所。記入欄を「値が在る」と読んでいた")

_f, _j = codes(check_decidable(dec_q(pay_unit=SLOT), CHAIN))
check("A55 単位欄の片方が記入欄 → 停止ではなく申し送り（旧：R20_UNIT_MISMATCH の誤停止）",
      "R20_UNIT_MISMATCH" not in _f and "R20_UNIT_UNDECLARED" in _j, (_f, _j))

_f, _j = codes(check_decidable(dec_q(pay_unit=SLOT, ret_unit=SLOT), CHAIN))
check("A55 単位欄の両方が記入欄 → 申し送る（旧：何も出ずに素通り）",
      "R20_UNIT_UNDECLARED" in _j, (_f, _j))

_f, _j = codes(check_decidable(dec_q(per=SLOT), CHAIN))
check("A55 分母が記入欄 → R20_DENOMINATOR_MISSING（旧：何も出ずに素通り）",
      "R20_DENOMINATOR_MISSING" in _j, (_f, _j))

_f, _j = codes(check_decidable(dec_q(pay_source="", ret_source="", source=SLOT), CHAIN))
check("A55 旧出所欄が記入欄 → 〈連結〉ではなく〈未申告〉（旧：A49_SOURCE_MERGED の誤診）",
      "R20_SOURCE_UNDECLARED" in _j and "A49_SOURCE_MERGED" not in _j, (_f, _j))

_f, _j = codes(check_decidable(dec_q(ret_source=SLOT), CHAIN))
check("A55 割った出所欄が記入欄 → R20_SOURCE_UNDECLARED（旧：A28_SOURCE_UNKNOWN の誤診）",
      "R20_SOURCE_UNDECLARED" in _j and "A28_SOURCE_UNKNOWN" not in _j, (_f, _j))

# 素通りしていないことの対照 ―― 正しく埋まっていれば何も出ない
_f, _j = codes(check_decidable(dec_q(), CHAIN))
check("対照 埋まっていれば単位・分母・出所は何も出ない",
      not {"R20_UNIT_UNDECLARED", "R20_DENOMINATOR_MISSING",
           "R20_SOURCE_UNDECLARED", "A49_SOURCE_MERGED", "A28_SOURCE_UNKNOWN"} & set(_j), (_f, _j))
# 連結の申告は、これまでどおり A49 として出る（A55 で潰していないこと）
_f, _j = codes(check_decidable(dec_q(pay_source="", ret_source="",
                                     source="自社の運用手順に基づく試算／戻るは式"), CHAIN))
check("対照 出所を連結して書いたら、これまでどおり A49_SOURCE_MERGED",
      "A49_SOURCE_MERGED" in _j, (_f, _j))


# ═══════════════════════════════════════ 述語が一つであることを、源で固定する
print("\n── A55-d：⊥ の述語は `is_bottom` 一つ。生の `in UNIT_UNKNOWN` を増やさない")
def raw_uses(src):
    """生で `in UNIT_UNKNOWN` を引いている**コード行**だけ数える。

    A54（型7 浅い一致）の13件目：最初この関数は註釈行も数えていた。
    直した箇所に「ここは `pu in UNIT_UNKNOWN` と書いてあった」と註を残したので、
    **註釈が自分の回帰を落とした。**物差しは境界を取らなければならない。
    """
    return [ln.strip() for ln in src.splitlines()
            if re.search(r"\bin\s+UNIT_UNKNOWN\b", ln) and not ln.strip().startswith("#")]


_SRC = inspect.getsource(check_decidable)
check("A55 `check_decidable` に生の `in UNIT_UNKNOWN` は0箇所（第14.1版の回帰は4箇所で固定していた）",
      not raw_uses(_SRC), raw_uses(_SRC))

import sales_logic as _SL
_ALL = inspect.getsource(_SL)
_uses = raw_uses(_ALL)
check("A55 モジュール全体でも、生で引いているのは `is_bottom` の中の1箇所だけ",
      len(_uses) == 1, _uses)

check("A55 記入欄は ⊥ である（述語そのものの確認）", is_bottom(SLOT) and is_bottom("不明")
      and is_bottom(None) and not is_bottom("300"))

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")
