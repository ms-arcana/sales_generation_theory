# -*- coding: utf-8 -*-
"""アノマリー A1/A2/A4 の実装

A1 now(Q) に expressible(q, κ_n) ―― 層2。生成前。警告ではなく修復要求にする
A2 ⑥のカテゴリ内差別化   ―― 層1。生成前。売り手マスタが要る
A4 R10 整合検査          ―― 層3。生成後。②と⑥に宣言させれば厳密に判定できる
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# ============================================================ A1（層2・生成前）
# κ の互換：ある基準で表現された量が、別の基準で表現できるか
EXPR_OK = {
    "実務性":     {"実務性"},
    "財源":       {"財源", "価格"},
    "説明可能性":  {"説明可能性", "財源", "価格"},   # 金額は説明可能性の語彙で通る
    "価格":       {"価格", "財源"},
}
def a1_check(q_kappa: str, kappa_n: str, recast_path: Optional[str]) -> str:
    """④の量が最終裁定点の基準へ両替できるか。できないなら修復（両替経路）を要求する"""
    if kappa_n in EXPR_OK.get(q_kappa, set()):
        return f"充足 量は κ={q_kappa} で書かれ、最終裁定点 κ={kappa_n} で表現できる"
    if recast_path:
        return (f"修復済み κ={q_kappa} → κ={kappa_n} は不通。両替経路を同枚に明記：「{recast_path}」")
    return (f"★停止[A1] 量は κ={q_kappa} でしか表現できず、最終裁定点 κ={kappa_n} に届かない。"
            f"両替経路（誰の何が減るのか）を同じ枚に書くこと。"
            f"書けないなら別の量を選ぶ")

# ============================================================ A2（層1・生成前）
@dataclass
class SellerDiff:
    """B1 が立つとき⑥に必要な『カテゴリ内で自社が残る根拠』"""
    named: Dict[str, str] = field(default_factory=dict)   # 根拠の型 → 実体

DIFF_TYPES = ["同型の実名事例", "認定・登録の非対称", "移行実績・稼働実績の数値",
              "責任分界の引き受け範囲", "価格構造（総額と逓増の開示）"]

def a2_check(B1: bool, sd: SellerDiff) -> str:
    if not B1:
        return "非該当 B1 が立たないため⑥のカテゴリ内差別化は不要"
    have = [k for k in DIFF_TYPES if sd.named.get(k)]
    if not have:
        return ("★停止[A2] 購買部門の独立審査が挟まるのに、カテゴリ内で自社が残る根拠が空。"
                "『御社じゃなくても成り立つ話だよね』で⑥が落ちる。"
                f"次のいずれかを登録してから生成すること：{DIFF_TYPES}")
    return f"充足[A2] ブロック24を点灯。根拠={have}"

# ============================================================ A4（層3・生成後）
REPEAT = re.compile(r"毎年|毎月|毎期|都度|その都度|반복|反復|繰り返|継続的に")
PERIODS = {"毎年": 12, "毎月": 1, "毎期": 3, "都度": 0, "その都度": 0}

@dataclass
class Declared:
    """生成器に宣言させる。推論しようとするから曖昧になるので、出させる"""
    s2_unit: Optional[str] = None        # ②で導入した単位（例「枠」）
    s2_from_unit: Optional[str] = None   # 元の単位（例「床」）
    s4_period_months: Optional[int] = None   # ④で立てた問題の反復周期
    s6_period_months: Optional[int] = None   # ⑥の課金・工数の周期

def r10a(s4: str, dec: Declared) -> str:
    """⑥が④で立てた問題を反復させていないか"""
    m = REPEAT.search(s4 or "")
    if not m:
        return "非該当[R10a] ④に反復性の語がない"
    if dec.s4_period_months is None or dec.s6_period_months is None:
        return "★停止[R10a] ④が反復性を問題化しているのに、④と⑥の周期が宣言されていない"
    if dec.s6_period_months and dec.s4_period_months and dec.s6_period_months <= dec.s4_period_months:
        return (f"★棄却[R10a] ④は『{m.group()}』発生する手続を問題として立てているのに、"
                f"⑥の課金が{dec.s6_period_months}か月周期で同じ頻度以上に反復する。"
                f"指さした問題を、自分の商品が最も高い単価で反復させる構造")
    return f"充足[R10a] ④の周期{dec.s4_period_months}か月 > ⑥の周期{dec.s6_period_months}か月"

def r10b(s6: str, dec: Declared) -> str:
    """②で導入した単位が⑥で保持されているか。

    元の単位が現れること自体は正常（『12床で部分再開すると夜勤帯は124枠のまま必要』）。
    棄却すべきは **比例換算** ―― 新単位を旧単位の比で割り戻す操作である。
    """
    if not dec.s2_unit:
        return "非該当[R10b] ②が単位の置き換えを行っていない"
    if dec.s2_unit not in (s6 or ""):
        return f"★棄却[R10b] ②で導入した単位『{dec.s2_unit}』が⑥に一度も現れない"
    if dec.s2_from_unit:
        RATIO = r"%|％|割|比例|按分|に応じて|相当|換算"
        for sent in re.split(r"[。\n]", s6 or ""):
            if dec.s2_unit in sent and dec.s2_from_unit in sent and re.search(RATIO, sent):
                return (f"★棄却[R10b] ②で『{dec.s2_from_unit}』から『{dec.s2_unit}』へ数え直したのに、"
                        f"⑥で比例換算して戻している：「{sent.strip()}」")
    return f"充足[R10b] 単位『{dec.s2_unit}』が⑥まで保持されている"

def r10(s4: str, s6: str, dec: Declared) -> List[str]:
    return [r10a(s4, dec), r10b(s6, dec)]
