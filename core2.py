# -*- coding: utf-8 -*-
"""core.py への (A) 群パッチ ―― 未踏22件のうち、形式系を変えずに閉じられるもの"""
from dataclasses import dataclass, replace
from datetime import date
from typing import Dict, List, Optional, Set, Tuple
from core import (Nu, Seat, Mi, TauItem, STAGES, ALLOWED, PRIMARY_ONLY, RHO, M0_KILL,
                  Sigma, theta_auto, segment_action, kappa_n)

# ---- 拡張フィールド（元の frozen dataclass を壊さず脇に持つ）------------------
@dataclass
class TauX:
    item: TauItem
    confirmed: bool = True        # 項目2/20：日付が確定しているか
    q_low: Optional[float] = None # 項目11：量の推定幅
    q_high: Optional[float] = None
    q_source: str = "公開統計"     # 項目16：買い手データ / 公開統計 / 売り手データ
    for_seat: Optional[str] = None# 項目14：どの座席の χ に属するか

@dataclass
class SellerFacts:                # 項目21：売り手マスタ。R7 を決定的に閉じる
    registrations: Set[str]       # 登録・許可・認定の番号や区分
    channels: Dict[str, float]    # D6b 用：チャネル名 → 接触可能母数
    yields: Dict[str, str]        # D6b 用：直近の接触→面接→入社

DATA_LT = {"買い手データ": 1, "公開統計": 0, "売り手データ": 0}   # 取得に食う月数

# ---- 項目13：j* の定義（資料を読む最も遠い座席。最終裁定者ではない）------------
def j_star(n: Nu) -> Seat:
    readers = [s for s in n.J if s.reads]
    return readers[-1] if readers else n.J[-1]

# ---- 項目2/20：未確定フィールドの扱い ---------------------------------------
def tau_gate(txs: List[TauX]) -> Tuple[List[TauX], List[str]]:
    msgs, ok = [], []
    for tx in txs:
        kill = M0_KILL[tx.item.form]
        if not tx.confirmed:
            if kill == "不可逆":
                msgs.append(f"★停止[未確定] {tx.item.form}:{tx.item.d} は M_0 を不可逆に消す主位置。"
                            f"未確定のまま④を書けない（外れれば従属する量が全部ずれる）")
                continue
            msgs.append(f"許容[未確定] {tx.item.form}:{tx.item.d} は従位置。「要確認」を明示して通す")
        ok.append(tx)
    return ok, msgs

# ---- 項目11：量の感度。幅が M_0 消去力を反転させるなら停止 ---------------------
def q_sensitivity(tx: TauX, threshold: float) -> Optional[str]:
    if tx.q_low is None or tx.q_high is None:
        return None
    if tx.q_low < threshold <= tx.q_high:
        return (f"★停止[感度] 量の幅 {tx.q_low:,.0f}〜{tx.q_high:,.0f} が閾値 {threshold:,.0f} を跨ぐ。"
                f"下限では④が成立しない。桁が合っているだけでは足りない")
    if tx.q_high < threshold:
        return f"★停止[感度] 量の上限 {tx.q_high:,.0f} でも閾値 {threshold:,.0f} に届かない"
    return f"許容[感度] 幅 {tx.q_low:,.0f}〜{tx.q_high:,.0f} は下限でも閾値超え。幅を明示して通す"

# ---- 項目16：データ取得LTを LT(P) に加算（自己言及の解消）---------------------
def effective_LT(n: Nu, txs: List[TauX]) -> int:
    return n.LT_months + max([DATA_LT.get(t.q_source, 0) for t in txs] + [0])

# ---- 項目14：τ の座席割当と優先順位（M_0 消去力の強い順）----------------------
ORDER = {"不可逆": 0, "機会喪失": 1, "コスト逓増のみ": 2, "―": 3}
def tau_priority(txs: List[TauX]) -> List[TauX]:
    return sorted(txs, key=lambda t: ORDER[M0_KILL[t.item.form]])

# ---- 項目18：⑤の言及を2つに絞る選択規則 -------------------------------------
STRENGTH = {"既存外注": 0, "取引上位者の指定": 1, "内製": 2, "競合": 3}
def pick_two(M_live: List[Mi]) -> Tuple[List[Mi], str]:
    s = sorted(M_live, key=lambda m: STRENGTH.get(m.mtype, 9))
    return s[:2], ("買い手が最も強く抱いている対抗案から2つ（既存外注＞取引上位者＞内製＞競合）。"
                   "25業種検証で『最も強い対抗案が単一次元を無傷で通過する』と判明したため、必ず含める")

# ---- 項目3：δ の候補提示に使う2問を機械生成 ----------------------------------
Q1 = {"D2": "当局・顧客・監査に説明する義務が御社に残りますか",
      "D4": "この決定を後から書面で正当化する必要がありますか",
      "D6a": "この行為を行える主体が法令で限定されていますか",
      "D6c": "この決定に、御社の外の取引上位者の承認が要りますか"}
Q2 = {"D1": "その手段は量的に足りませんか",
      "D3": "その判断を行える資格者が別にいますか",
      "D5": "その手段を動かす人の時間が、いま別のことに使われていますか",
      "D6b": "そもそも市場にその供給が存在しませんか"}
def questions(cand: Set[str]) -> List[str]:
    qs = [f"Q1 {Q1[d]}（→ {d}）" for d in sorted(cand & set(Q1))]
    qs += [f"Q2 {Q2[d]}（→ {d}）" for d in sorted(cand & set(Q2))]
    return qs or ["候補が空。生成停止して営業に差し戻す"]

# ---- 項目12/23：R7 の充足証拠を、段と形式まで指定 -----------------------------
R7_EVIDENCE = {
  "D6a": ("⑥", "登録番号・許可番号・認定区分の実物（別紙可）"),
  "D6b": ("⑥", "接触可能母数の実数と、直近の 接触→面接→入社 の歩留まり"),
  "D6c": ("⑥", "当該上位者からの承認取得実績と、承認リードタイムの実測"),
}
def check_R7(M_live: List[Mi], sf: SellerFacts) -> List[str]:
    out = []
    for m in M_live:
        if m.delta not in R7_EVIDENCE: continue
        stage, form = R7_EVIDENCE[m.delta]
        if m.delta == "D6a":
            out.append(f"{m.name}：{stage}に {form}。保有={sorted(sf.registrations) or '★未登録 → ⑤後半が崩れる'}")
        elif m.delta == "D6b":
            tot = sum(sf.channels.values())
            out.append(f"{m.name}：{stage}に {form}。母数={tot:,.0f}（{sf.channels}）"
                       + ("" if tot > 0 else " ★ゼロ → ⑤がそのまま⑥を自己消去する"))
        else:
            out.append(f"{m.name}：{stage}に {form}")
    return out

# ---- 項目22：6次元に該当しない拘束 → 不成立通知 ------------------------------
def out_of_scope(reason: str) -> str:
    return (f"★不成立通知：拘束が買い手自身の条件設定にある（{reason}）。"
            f"D1〜D6 のいずれにも該当せず、⑥が『条件を変えてください』になり売り物がない。訪問しない")
