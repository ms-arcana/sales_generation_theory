# -*- coding: utf-8 -*-
"""営業資料生成モデル 第4/5版 ―― 決定的コア

論理式のうち LLM を要さない部分（Σ, on(b), allowed, R1〜R8, θ_auto）を素の Python で実装する。
numpy は使っていない。行列演算ではなく集合演算・表引き・条件分岐・日付演算だからである。
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

STAGES = ["①", "②", "③", "④", "⑤", "⑥"]

# ---------------------------------------------------------------- 型

@dataclass(frozen=True)
class Seat:                      # j_k = (κ, χ, γ, ω)
    name: str
    kappa: str                   # 実務性 / 財源 / 説明可能性 / 価格
    chi: str                     # 従う制度暦
    gamma: str                   # 単独 / 合議
    omega: str                   # 社内 / 社外
    reads: bool = True           # 資料を読むか

@dataclass(frozen=True)
class TauItem:                   # τ の元 = (形式, 日付, 出典階層, 既知度)
    form: str                    # A / B / C / D / Ea / Eb / Ec / Ed
    d: Optional[date]
    src: str                     # 法令 / 公的暦 / 自然・需要 / 契約 / 売り手都合
    known: str                   # 未知 / 既知
    q_uncomputed: Optional[str] = None   # 買い手がまだ計算していない量
    q_kappa: Optional[str] = None        # その量が表現できる基準（A1 の検査用）

@dataclass(frozen=True)
class Mi:
    name: str
    mtype: str                   # M0 / 内製 / 既存外注 / 競合 / 取引上位者の指定
    delta: Optional[str] = None  # D1..D5 / D6a / D6b / D6c

@dataclass
class Nu:
    # 商材軸
    A: str; I: str; S1: str; S2: str; S3: bool; C_move: str
    # 顧客軸
    J: List[Seat]; procedural: bool; downward: bool; segment: str; industry: str; product: str
    # 商談軸
    E_reader: str; E_judge: str
    tau: List[TauItem]
    M: List[Mi]
    LT_months: int               # 提案の最短リードタイム

# ---------------------------------------------------------------- 表

ALLOWED: Dict[str, Set[str]] = {          # M_i 類型 → 使用可能な δ
    "M0":            set(),                # ⑤で扱わない
    "内製":           {"D5", "D2", "D6b"},
    "既存外注":        {"D2", "D6c", "D4"},
    "競合":           {"D1", "D2", "D3", "D4", "D6a", "D6b", "D6c"},
    "取引上位者の指定":  {"D6c"},
}
PRIMARY_ONLY = {"内製": {"D5"}, "既存外注": {"D2", "D6c"}, "取引上位者の指定": {"D6c"}}

RHO = {  # R5：T-E 型別のクロージング置換表
    "Ea": "申請／計画認定／交付決定待ち",
    "Eb": "発注は今・稼働日を窓に固定",
    "Ec": "承認申請の共同作成＋次の窓の枠取り",
    "Ed": "不成立通知（この買い手にこの商材は売れない）",
}

M0_KILL = {"A": "不可逆", "B": "機会喪失", "C": "機会喪失", "D": "コスト逓増のみ",
           "Ea": "不可逆", "Eb": "不可逆", "Ec": "不可逆", "Ed": "―"}

# harm（誤った既定の損害）。θ_auto = 1 − u_ask/(u+harm)
HARM = {"delta": 100.0, "transport": 2.0, "tau": 50.0}
U, U_ASK = 1.0, 0.3

# ---------------------------------------------------------------- 縮退

def sigma_prod(n: Nu) -> Set[str]:
    if n.S3:
        return set(STAGES)
    small = n.S1 in ("〜10万", "10〜100万")
    if small and n.S2 in ("四半期〜月次", "週次以上"):
        return {"①", "⑥"}
    if small and n.S2 in ("単発", "年次以下"):
        return {"①", "④", "⑥"}
    return set(STAGES)

START = {"困っていない": 0, "手段を知らない": 1, "比較検討中": 4, "うちも知っている": 4}

def sigma_read(e_judge: str) -> Set[str]:
    return set(STAGES[START.get(e_judge, 0):])

def Sigma(n: Nu) -> Tuple[Set[str], str]:
    sp = sigma_prod(n)
    if sp != set(STAGES):
        return sp, "σ_prod（商材側が縮退を発火）"
    return sigma_read(n.E_judge), "σ_read（商材側は full、読み手側が決定）"

# ---------------------------------------------------------------- 検査

def theta_auto(kind: str) -> float:
    return 1.0 - U_ASK / (U + HARM[kind])

def segment_action(kind: str, c: float, n_cand: int) -> str:
    if n_cand > 3:
        return "生成停止（2問で確定）"
    return "自動採用" if c >= theta_auto(kind) else "候補提示（営業が2問で確定）"

def kappa_n(n: Nu) -> str:
    return n.J[-1].kappa if n.J else "実務性"

def check_R6(n: Nu, today: date) -> Tuple[List[TauItem], List[str]]:
    """R6a 未来性 / R6b リードタイム整合 / 出典階層 / 既知度 / T-D単独禁止 / A1 両替可能性"""
    ok, msgs = [], []
    forms = {t.form for t in n.tau}
    for t in n.tau:
        if t.src == "売り手都合":
            msgs.append(f"棄却[出典階層] {t.form}:{t.d} は売り手都合"); continue
        if t.form == "Ed":
            msgs.append("R5d 恒常禁制 → 不成立通知。④の材料から外す"); continue
        if t.d is None:
            msgs.append(f"棄却[空欄] {t.form} に日付がない"); continue
        if t.d <= today:
            msgs.append(f"棄却[R6a] {t.form}:{t.d} は過去日 → ①（既に非適合）の材料へ"); continue
        months = (t.d.year - today.year) * 12 + (t.d.month - today.month)
        # R6b は「終端日」型（A/C）にのみ適用する。B は窓の開閉＝既に行動期限、
        # E は解禁日であり、いずれも LT を再度差し引くと二重計上になる。
        if t.form in ("A", "C") and months - n.LT_months < 0:
            msgs.append(f"棄却[R6b] {t.form}:{t.d} まで{months}か月 < LT {n.LT_months}か月 → 次の窓へ繰上げ"); continue
        if t.form == "B" and months < 0:
            msgs.append(f"棄却[R6b'] {t.form}:{t.d} の窓は既に閉じている"); continue
        if t.known == "既知" and not t.q_uncomputed:
            msgs.append(f"棄却[既知度] {t.form}:{t.d} は既知の暦。まだ計算していない量が要る"); continue
        if t.q_uncomputed and t.q_kappa and t.q_kappa != kappa_n(n):
            msgs.append(f"警告[A1] 量『{t.q_uncomputed}』は κ={t.q_kappa} でしか表現できず、"
                        f"最終裁定点の κ={kappa_n(n)} に両替できない")
        if t.form == "D" and not (forms & {"B", "C"}):
            msgs.append("棄却[T-D単独禁止] T-D は B または C と重ねること"); continue
        ok.append(t)
    if not ok:
        msgs.append("★R6 停止：④を供給する τ の元がゼロ")
    return ok, msgs

def check_delta(n: Nu) -> Tuple[List[Mi], List[str]]:
    live, msgs = [], []
    for m in n.M:
        if m.mtype == "M0":
            msgs.append(f"{m.name}：M_0 は⑤の量化域から除外（消すのは④の日付）"); continue
        if m.delta is None:
            msgs.append(f"★{m.name}：δ 未選択。D軸は既定を持たない → 生成停止"); continue
        if m.delta not in ALLOWED[m.mtype]:
            msgs.append(f"★{m.name}：δ={m.delta} は類型『{m.mtype}』で禁止（侮辱または原理的不成立）"); continue
        po = PRIMARY_ONLY.get(m.mtype)
        if po and m.delta not in po:
            msgs.append(f"{m.name}：δ={m.delta} は従次元のみ")
        live.append(m)
    if not live:
        msgs.append("★⑤生成不能：使用可能な δ を持つ M_i が存在しない")
    return live, msgs

def fire_rules(n: Nu, tau_ok: List[TauItem], M_live: List[Mi]) -> List[str]:
    r, ds = [], {m.delta for m in M_live}
    if "D5" in ds:
        r.append("R1 充足" if tau_ok else "★R1 違反：D5 に時限がない（「外注しませんか」に落ちる）")
    if "D2" in ds: r.append("R2：責任分界表[20]を必須点灯、当該ブロック内で性能訴求を減格")
    if "D3" in ds: r.append("R3：判断権の所在[21]を必須点灯、精度訴求を禁止")
    if "D4" in ds: r.append("R4：前例[5b]を必須点灯（同型性×実名開示で判定）")
    for t in tau_ok:
        if t.form.startswith("E"): r.append(f"R5{t.form[1]}：⑥のクロージング → {RHO[t.form]}")
    if ds & {"D6a", "D6b", "D6c"}:
        r.append("R7：自己適用検査＋自社側の同一指標の実数を⑥に必須（第5版 A3）")
    if any(s.kappa == "価格" for s in n.J):
        r.append("B1：⑤の残余を購買様式へ二重出力。⑥に『カテゴリ内で自社が残る根拠』必須（第5版 A2）")
    if len(n.J) >= 2: r.append(f"n={len(n.J)} ≥ 2 ⟹ ⑥でエンテュメーメ不可。結論文・金額・期日・想定反論を書き切る")
    else: r.append("n=1 ⟹ ⑥で一寸を残してよい（命令法では締めない）")
    if any(s.gamma == "合議" for s in n.J): r.append("γ=合議 ⟹ ⊢ は成員の交叉。最も保守的な一人に合わせる")
    if n.procedural: r.append("procedural ⟹ 層A（固有名なし）／層B の分離出力")
    if n.downward: r.append("downward ⟹ 下向き説明資料[18]（上向きと論理が反転するので流用不可）")
    return r

def blocks_on(n: Nu, S: Set[str], M_live: List[Mi], tau_ok: List[TauItem]) -> List[str]:
    ds = {m.delta for m in M_live}
    fs = {t.form for t in tau_ok}
    cand = [
        ("1 困りごとの見える化", n.E_judge == "困っていない", "①"),
        ("2 そもそも何かの説明", n.E_judge in ("困っていない", "手段を知らない"), "③"),
        ("3 今のやり方との比較", n.E_judge in ("比較検討中", "うちも知っている"), "⑤"),
        ("4 仕様一覧・比較表", n.A == "買う前に分かる", "⑤"),
        ("5 数字入りの導入事例", n.A == "使えば分かる", "⑤"),
        ("5b 前例・実績", "D4" in ds, "⑤"),
        ("6 仕組みの開示", n.A == "使っても分からない", "⑤"),
        ("7 認証・お墨付き", n.A == "使っても分からない", "⑤"),
        ("8 試せる仕掛け", n.A == "使えば分かる" or n.C_move == "すぐ試せる", "⑥"),
        ("9 段階導入と移行支援", n.C_move == "大仕事", "⑥"),
        ("11 期限の明示", bool(fs & {"A", "B", "C", "D"}), "④"),
        ("14 今すぐやる理由", bool(fs - {"D"}), "④"),
        ("15a 起案理由文", len(n.J) >= 2, "⑥"),
        ("16 要件記述（層A）", n.procedural, "⑥"),
        ("17 人間記入スロット", len(n.J) >= 2, "⑥"),
        ("18 下向き説明資料", n.downward, "⑥"),
        ("19 禁制の明示", any(f in ("Ea", "Eb", "Ec") for f in fs), "④"),
        ("20 責任分界表", "D2" in ds, "⑤"),
        ("21 判断権の所在", "D3" in ds, "⑤"),
        ("22 機会費用", "D5" in ds, "⑤"),
        ("23 第三者拘束の実際", bool(ds & {"D6a", "D6b", "D6c"}), "⑤"),
    ]
    return [b for b, phi, st in cand if phi and st in S]   # on(b) ≡ Φ_b ∧ stage(b)∈Σ

# ---------------------------------------------------------------- 実行

def compile_deal(n: Nu, today: date) -> dict:
    S, why = Sigma(n)
    tau_ok, tmsg = check_R6(n, today)
    M_live, dmsg = check_delta(n)
    stop = [m for m in tmsg + dmsg if m.startswith("★")]
    return {
        "Sigma": [s for s in STAGES if s in S], "Sigma_by": why,
        "tau_ok": [(t.form, str(t.d), t.src, t.known) for t in tau_ok], "tau_msg": tmsg,
        "delta": [(m.name, m.mtype, m.delta) for m in M_live], "delta_msg": dmsg,
        "rules": fire_rules(n, tau_ok, M_live),
        "blocks": blocks_on(n, S, M_live, tau_ok),
        "M0_kill": [M0_KILL[t.form] for t in tau_ok],
        "stop": stop,
        "generate": len(stop) == 0,
        "llm_calls_needed": 0 if stop else 1 + len([s for s in STAGES if s in S]),
    }
