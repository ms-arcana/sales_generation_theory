# -*- coding: utf-8 -*-
"""営業資料生成モデル 第11版 ―― 決定的コア

方針
    このモジュールは **真偽が入力から一意に決まるものだけ** を扱う。
    - 返すのは記号（コード）と構造化データのみ。表示用の日本語は持たない → messages.json
    - 意味の判定（列挙否定形か／反復を問題化しているか／比例換算か）は行わない。
      needs_judgment に積んで LLM または営業へ回す。
    - 文言は一切生成しない。

境界
    決定的  ： 集合演算・表引き・日付演算・算術・文字列の完全一致
    要判断  ： 意味・程度・言い換えの可否

第6版の変更（食品・建設 8セルのアノマリー A5〜A11）
    A5  ⑥に expressible(P, κ_n)                → check_declared / EXPR_OK
    A6  R10b は「置換」だけを禁じ「併記」は禁じない → check_unit_presence と連動
    A7  δ に拘束者を持たせ、向きを検査          → Mi.binder / Nu.upstream・downstream
    A8  τ に適用対象と拘束者を持たせる          → TauItem.scope / TauItem.binders
    A9  ⑥が消す集合 ⊆ ④で数えた集合            → R10c（被覆率の宣言）
    A10 縮退で落とした段の Γ を外から与える      → Nu.gamma_pre、宣言の値域に「未定義」
    A11 ③の新語に既存語の対応を併記            → R11
    実装の穴：R10a の 0 扱い／R7 の実数2つ／R12 τ 項間の順序

第7版の変更（再走行のアノマリー A12〜A15）
    A12 両替できることと両替されることは別 → Nu.W（執行座席）／R13
    A13 ④の周期と⑥の量の型（stock/flow）  → R14
    A14 ⑤で他手段に課した期限を⑥が破る    → R12b・R16（自己適用）
    A15 「買い手データ」の受領記録         → TauItem.q_receipt／R15

第8版（3原理への再公理化。SPEC8.md）
    内容の変更は一点だけ ―― 侮辱 ≺ に対象を与えた（Π1 単調性の破れ）。
    insult(φ) ⟺ ∃χ ∈ Γ^own. Γ ∪ {φ} ⊢ ¬χ
    攻撃先が Γ_s なら ⊥（全額失効）、Γ^own なら ≺ 上の後退（侮辱）。
    Γ^own は A10 の Γ^pre と同じ集合である（買い手が資料の外で自分で積んだもの）。
    → R17 として実装。他の規則は第7版のまま（SPEC8.md §7 が導出元を示す）。

第9版（学校法人・小売 8セル。業界の側から入った修正。SPEC8.md §10）
    A16 中間座席の通関。Π2 は「各リンクで」と書いてあるのに実装が終端一点だった → check_chain
    R18 制度由来の座席は飛ばせない。|κ|=1 で Form が閉じている        → Seat.origin
    A18 日付は「決定が締まる日」であって「結果が現れる日」ではない      → TauItem.decision / windows
    A19 無料の手段は帰責・手続・権限・資源では消せない（cost に対象）    → Mi.cost_to_buyer
    A20 D5 の拘束者は W に属し、読み手自身であってはならない          → check_D5_binder

第10版（較正表を商材座標の関数へ。統合検討-既存理論と本モデル.md）
    較正表は業界の関数ではなく **商材座標の関数** だった。座標を与えれば表は導出され、
    与えなければ従来の較正表に落ちる（そのときだけ業界の較正が問われる）。
      ν  検証時点        Nelson 1970 / Darby-Karni 1973 / Dulleck-Kerschbamer 2006（旧 A）
      θ  分割試用可能性  Rogers（旧 C_move の一半）
      σp 手続切替コスト  Burnham-Frels-Mahajan 2003（旧 C_move のもう一半）
      ω  効果発現ラグ    MMM の adstock/carryover
      α  帰属可能性      Selviaridis & Norrman 2014（測定可能性 × 統制可能性）
      β1 会計分類        ASU 2018-15 / IFRIC / ABJ 2003（資産計上か × 固定か変動か）
      β2 予算内外        稟議・予算の実証
    削除：I（装置/役務。参照0）／S1・S2・S3（σ_prod にしか繋がらず、その σ_prod は根拠なしと自認済み）

第11版（第8版との対照実験から。学校法人・小売 8セル再走行）
    A21 W は存在しても実行を拒む。V と同じ拒否構造が W にもあった → Executor.willing / κ
    A22 適用対象は値の真偽を検査できない。境界を明示する        → Scope.source（A15 と同型）
    A23 ⑥に置く量は単一ではなく、読む座席ごとの組である        → Declared.s6_kappa_by_seat
        （Π2 の ∀k から直に出るのに、実装が単数だった。N4 の適用漏れ）

依存は標準ライブラリのみ。
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence, Set, Tuple

STAGES = ("①", "②", "③", "④", "⑤", "⑥")
Kappa = str
Dim = str


# ══════════════════════════════════════════════════════════════════ 型

@dataclass(frozen=True)
class Seat:
    name: str
    kappa: frozenset                   # κ は集合
    chi: str
    gamma: str = "単独"
    omega: str = "社内"
    reads: bool = True
    form: frozenset = frozenset()      # その座席の文書様式に既にある語（A11）
    origin: str = "個人"               # 制度 / 組織 / 個人（第9版・R18）


@dataclass(frozen=True)
class Veto:
    name: str


@dataclass(frozen=True)
class Executor:
    """W：決めないが動かす座席（A12）。費目を実際に減らす権限を持つ。

    第11版：権限があっても実行を拒むことがある（A21）。
    「それを削るのは店長で、店長は棚替えの時期に人は減らせんと言う」——
    V（決裁権はないが止められる）とまったく同じ構造が W にもあった。
    """
    name: str
    accounts: frozenset = frozenset()
    willing: Optional[bool] = None     # A21：実行に同意しているか。None は未聞取り
    kappa: frozenset = frozenset()     # A21：その座席が何で判断するか（拒否の理由が読める）


@dataclass(frozen=True)
class Product:
    """商材座標（第10版）。商談前に観測でき、業界に依存しない。

    較正表はこの座標の関数である。座標を与えなければ従来の較正表に落ちる。
    """
    nu: str = "使えば分かる"        # 買う前に分かる / 使えば分かる / 使っても分からない
    theta: str = "段階分割"          # 不可分 / 段階分割 / 完全分割
    sigma_p: str = "中"              # 手続切替コスト 低 / 中 / 高
    omega: int = 1                   # 効果が数字に出るまでの月数
    alpha_m: str = "高"              # 成果の測定可能性 低 / 高
    alpha_c: str = "高"              # 供給者の統制可能性 低 / 高
    beta1_cap: str = "費用処理"      # 資産計上 / 費用処理
    beta1_hard: str = "変動"         # 固定 / 変動（＝費目の下方硬直性）
    beta2: str = "予算計上済"        # 予算計上済 / 予算外


@dataclass(frozen=True)
class Scope:
    """T軸の適用対象（A8）。出典階層とは別の軸。

    第11版：機械は照合しかできず、値そのものの真偽は見られない（A22）。
    「認証評価は国公私立すべての大学に課される。設置形態で区分される制度ではない」——
    scope の値が誤っていても、買い手属性と一致すれば通ってしまう。
    修正できる欠陥ではないので、A15 と同型の出所記録を要求して境界を明示する。
    """
    keys: Tuple[Tuple[str, str], ...] = ()   # 買い手属性との完全一致で判定
    applied_from: Optional[date] = None      # 当該区分への適用開始日
    source: Optional[str] = None             # A22：誰がいつどの条文から取ったか


@dataclass(frozen=True)
class TauItem:
    form: str                          # A B C D Ea Eb Ec Ed
    d: Optional[date]
    src: str                           # 法令 公的暦 自然・需要 契約 売り手都合
    known: str                         # 未知 / 既知
    q: Optional[str] = None
    q_kappa: Optional[Kappa] = None
    q_recast: bool = False             # κ_n への両替経路を同枚に書いたか（真偽）
    q_source: str = "公開統計"
    q_low: Optional[float] = None
    q_high: Optional[float] = None
    confirmed: bool = True
    wait_months: Optional[int] = None
    scope: Optional[Scope] = None      # A8：空なら棄却
    binders: Tuple[str, ...] = ()      # A8：契約・第三者承認由来の日付を握る当事者
    q_receipt: Optional[str] = None    # A15：買い手データを名乗るときの受領記録
    decision: Optional[bool] = None    # A18：決定が締まる日か（結果が現れる日ではないか）
    windows: int = 1                   # A18：同じ拘束者が持つ並行する窓の数


@dataclass(frozen=True)
class Mi:
    name: str
    mtype: str                         # M0 内製 既存外注 競合 取引上位者の指定
    dims: frozenset = frozenset()
    order: Tuple[Dim, ...] = ()
    binder: Optional[str] = None       # A7：拘束者（次元が1つのときの略記）
    binders: Tuple[Tuple[Dim, str], ...] = ()   # A7：〈次元, 拘束者〉の対
    cost_to_buyer: Optional[float] = None       # A19：買い手にとっての費用。0 なら D6 系でしか消せない


@dataclass
class Seller:
    """売り手マスタ。真偽と数だけを持つ（説明文は持たない）"""
    registrations: Set[str] = field(default_factory=set)
    registration_expiry: Optional[date] = None        # R7 D6a の実数②
    channel_total: float = 0.0
    funnel_present: bool = False
    funnel_yield: Optional[float] = None              # R7 D6b の実数②
    upstream_approvals: int = 0
    upstream_lead_days: Optional[Tuple[int, int]] = None   # R7 D6c の実数②
    named_cases: List[Dict[str, str]] = field(default_factory=list)
    liability_scope: bool = False
    price_disclosure: bool = False


@dataclass
class Nu:
    A: str; I: str; S1: str; S2: str; S3: bool; C_move: str
    J: Sequence[Seat]
    prod: Optional[Product] = None             # 第10版：商材座標。None なら較正表へ落ちる
    V: Sequence[Veto] = ()
    W: Sequence[Executor] = ()                 # A12：執行座席。空なら κ_n は動かない
    procedural: bool = False
    downward: bool = False
    E_reader: str = "困っていない"
    E_judge: str = "困っていない"
    tau: Sequence[TauItem] = ()
    M: Sequence[Mi] = ()
    LT_months: int = 6
    buyer_context: Dict[str, str] = field(default_factory=dict)
    upstream: frozenset = frozenset()          # A7：買い手の上位にいる当事者
    downstream: frozenset = frozenset()        # A7：買い手が上位に立つ相手
    gamma_pre: Dict[str, str] = field(default_factory=dict)   # A10：資料の外で成立済みの段


@dataclass
class Declared:
    """生成器（LLM）に宣言させる値。Python は推論しない。
    None は **未定義**（その段を書いていない等）であって 0 でも空文字でもない（A10）"""
    s2_unit: Optional[str] = None
    s2_from_unit: Optional[str] = None
    s3_form_mapping: Optional[str] = None        # A11：新語 ↔ κ_n 側の既存語
    s4_declares_repetition: Optional[bool] = None
    s4_period_months: Optional[int] = None
    s6_period_months: Optional[int] = None
    s5_is_constraint_disclosure: Optional[bool] = None
    s6_ends_imperative: Optional[bool] = None
    s6_contains_promise: Optional[bool] = None
    s6_recasts_unit: Optional[bool] = None
    s6_kappa: Optional[Kappa] = None             # A5：⑥に置いた量の基準
    s6_coverage_disclosed: Optional[bool] = None  # A9：被覆率を開示したか
    s6_coverage_full: Optional[bool] = None       # A9：covered(P) = Q か
    s6_coverage_subset: Optional[bool] = None     # A9：covered(P) ⊆ Q か（門）
    s6_kappa_type: Optional[str] = None           # A13：stock / flow
    s6_realize_actor: Optional[str] = None        # A12：誰が（単数。A24 以前の形）
    s6_realize_date: Optional[str] = None         # A12：いつ（ISO）
    s6_realize_account: Optional[str] = None      # A12：どの費目を
    # A24（第12版）：act⟨w,d,o⟩ は集合である。減らす費目が2つなら行為も2つ。
    # 単数の欄しか無かったため、生成器は「媒体費・広報外注費」と連結して申告し、
    # そんな費目は存在しないと判定されていた（第10版 R13_ACCOUNT_NOT_HELD 2件）。
    s6_realize: Optional[Tuple[Tuple[str, str, str], ...]] = None   # ⟨誰が, いつ, どの費目⟩ の組
    s6_start_date: Optional[str] = None           # A14：⑥が示す着手日（ISO）
    s6_self_check: Optional[bool] = None          # A14：⑤の根拠を自社案にも当てたか
    s5_denies_own: Optional[str] = None           # R17：⑤が否定している買い手の既承認（無ければ空文字）
    s6_kappa_by_seat: Optional[Dict[str, str]] = None   # A23：座席名 → その座席で読める量の基準


@dataclass(frozen=True)
class Finding:
    code: str                          # 機械可読。表示文は messages.json
    level: str                         # stop / reject / demote / info
    ref: str = ""


@dataclass(frozen=True)
class Judgment:
    """Python が決められないもの。LLM または営業へ回す"""
    code: str
    ref: str = ""


# ══════════════════════════════════════════════════════════════════ 表

ALLOWED: Dict[str, Set[Dim]] = {
    "M0": set(),
    "内製": {"D5", "D2", "D6b"},
    "既存外注": {"D2", "D6c", "D4", "D6b"},
    "競合": {"D7a", "D7b", "D7c", "D7d", "D1", "D2", "D3", "D4", "D6a", "D6b", "D6c"},
    "取引上位者の指定": {"D6c"},
}
PRIMARY: Dict[str, Set[Dim]] = {
    "内製": {"D5"}, "既存外注": {"D2", "D6c"},
    "競合": {"D7a", "D7b", "D7c", "D7d"}, "取引上位者の指定": {"D6c"},
}
EXPR_OK_CALIBRATED: Dict[Kappa, Set[Kappa]] = {
    "実務性": {"実務性"},
    "財源": {"財源", "価格", "説明可能性"},
    "説明可能性": {"説明可能性", "財源", "価格", "政治的可視性"},
    "価格": {"価格", "財源"},
    "政治的可視性": {"政治的可視性", "説明可能性"},
}
M0_KILL = {"A": "不可逆", "B": "機会喪失", "C": "機会喪失", "D": "逓増",
           "Ea": "不可逆", "Eb": "不可逆", "Ec": "不可逆", "Ed": "―"}
KILL_ORDER = {"不可逆": 0, "機会喪失": 1, "逓増": 2, "―": 3}
R7_DIMS = {"D6a", "D6b", "D6c"}
BINDER_REQUIRED = {"D6a": True, "D6b": False, "D6c": True}   # A7：D6b の拘束者は市場＝⊥
D7_DIMS = {"D7a", "D7b", "D7c", "D7d"}
ACQUIRE_CALIBRATED = {"買い手データ": 1, "公開統計": 0, "売り手データ": 0}
EXPR_OK = EXPR_OK_CALIBRATED          # 後方互換の別名（座標を渡さないとき）
ACQUIRE = ACQUIRE_CALIBRATED
START = {"困っていない": 0, "手段を知らない": 1, "比較検討中": 4, "うちも知っている": 4}
# ISO_KEYS：Π3 の同所律から導く（第10版）。所轄庁・系列は λ の粗い代理変数だった。
# 事例が効くのは拘束と同じ所在に属するときだけであり、Cartwright の support factors は W である。
ISO_KEYS = ("拘束の所在", "執行座席の同型", "暦の同型")
ISO_KEYS_CALIBRATED = ("所轄庁", "規模", "業態", "商圏", "系列")
BINDER_SRC = {"契約"}                    # A8：拘束者の同定が要る出典
HARM = {"delta": 100.0, "transport": 2.0}
U, U_ASK = 1.0, 0.3

# V0 = Vocab(層1) ∪ Vocab(層2)。完全一致で検出できるものだけ扱う
V0 = ["消去対象", "残余", "カテゴリC", "様相", "必然化", "問題化", "内在的否定",
      "措定", "実然", "warrant", "前提化", "承認を積", "資本として", "共著者",
      "蝶番", "縮退", "拘束の所在", "エンテュメーメ", "省略三段論法", "外延", "被覆率"]
V0_RE = [r"(?<!法)消去(?!法)", r"M_[0-9i]|Mᵢ", r"\bD[1-7][a-d]?\b", r"T-[A-E]"]


# ══════════════════════════════════════════════════════════════════ 層1

def sigma_prod(n: Nu) -> Tuple[Set[str], bool]:
    if n.S3:
        return set(STAGES), False
    small = n.S1 in ("〜10万", "10〜100万")
    if small and n.S2 in ("四半期〜月次", "週次以上"):
        return {"①", "⑥"}, True
    if small and n.S2 in ("単発", "年次以下"):
        return {"①", "④", "⑥"}, False
    return set(STAGES), False


def j_star(n: Nu) -> Seat:
    readers = [s for s in n.J if s.reads]
    return readers[-1] if readers else n.J[-1]


def kappa_n(n: Nu) -> frozenset:
    return n.J[-1].kappa if n.J else frozenset({"実務性"})


def form_n(n: Nu) -> frozenset:
    return n.J[-1].form if n.J else frozenset()


def talk_guide(n: Nu, S: List[str]) -> List[str]:
    """対面で飛ばしてよい段。読み手の状態で縮退した分（§6 の出力3）"""
    reader = set(STAGES[START.get(n.E_reader, 0):])
    return [s for s in S if s not in reader]


def compute_sigma(n: Nu) -> Tuple[List[str], str, bool]:
    sp, oos = sigma_prod(n)
    if sp != set(STAGES):
        return [s for s in STAGES if s in sp], "sigma_prod", oos
    S = set(STAGES[START.get(n.E_judge, 0):])
    return [s for s in STAGES if s in S], "sigma_read", oos


ELIMINABLE_IF_FREE = {"D6a", "D6b", "D6c"}       # A19：無料の手段を消せる次元


# ══════════════════════════════════════════════════════════════════ 較正台帳
# 表には二種類ある。原理から導出されたものと、観測した業界で較正したもの。
# 前者は業界を越えるが、後者は越えない。**どちらかを区別せずに使うと、
# ある業界の事情が別の業界の資料を黙って殺す。**
#
#   導出（業界非依存）: M0_KILL / KILL_ORDER（T軸4座標）／ALLOWED・PRIMARY（λ×ε と同所律）
#                       R7_DIMS・D7_DIMS・BINDER_REQUIRED（λ の定義）
#                       ELIMINABLE_IF_FREE（Π1 の cost）／V0（層1∪層2の語彙）
#   較正（業界依存）  : EXPR_OK ／ START ／ ACQUIRE ／ ISO_KEYS ／ BINDER_SRC
CALIBRATED_ON = frozenset({"医療", "物流", "食品", "建設", "学校法人", "小売"})


# ══════════════════════════════════════════════════════════════════ 生成子（第10版）
# 較正表は業界の関数ではなく商材座標の関数である。座標を与えれば表は導出される。

RK = {"実務性": 0, "価格": 1, "財源": 2, "説明可能性": 3, "政治的可視性": 4}


def expr_ok_of(p: Optional[Product]) -> Dict[Kappa, Set[Kappa]]:
    """EXPR_OK を α（帰属可能性）と β1（費目の硬さ）から導く。

    階数の隣接則（|rk 差| <= 1）が骨格。実務性(0) が孤立していたのは
    「物量→金額の両替は執行を要する」からで、これは α と β1 の関数である。
      α = 〈測定可能性 高, 統制可能性 高〉かつ 費目が変動 → 実務性↔価格 が通る
      それ以外（成果が測れない／統制できない／固定費）      → 通らない
    後者が Anderson-Banker-Janakiraman (2003) のコスト下方硬直性にあたる。
    """
    if p is None:
        return EXPR_OK_CALIBRATED
    out: Dict[Kappa, Set[Kappa]] = {}
    open_zero = (p.alpha_m == "高" and p.alpha_c == "高" and p.beta1_hard == "変動")
    for a, ra in RK.items():
        s_ = set()
        for b, rb in RK.items():
            if abs(ra - rb) > 1:
                continue
            if (ra == 0) ^ (rb == 0):
                if not open_zero:
                    continue
            s_.add(b)
        out[a] = s_
    out["説明可能性"].add("価格")      # 実測の残渣（24/25 の外れ1マス）
    out["財源"].add("説明可能性")
    return out


def acquire_of(p: Optional[Product]) -> Dict[str, int]:
    """買い手データの取得月数を ω（効果発現ラグ）から導く。1周期分たまるまで待つ。"""
    if p is None:
        return ACQUIRE_CALIBRATED
    return {"買い手データ": max(1, int(p.omega)), "公開統計": 0, "売り手データ": 0}


def cost_vector(p: Optional[Product], n_seats: int) -> Tuple[int, int, int]:
    """Π1 の cost に初めて対象を与える（第10版）。金額ではなく組織的コスト。

    〈手続切替コスト, 並行運用月数, 注意（承認座席数）〉
    """
    if p is None:
        return (1, 1, n_seats)
    sp = {"低": 0, "中": 1, "高": 2}.get(p.sigma_p, 1)
    par = {"完全分割": 0, "段階分割": 1, "不可分": 3}.get(p.theta, 1)
    return (sp, par, n_seats)


def eliminable_of(p: Optional[Product], m: "Mi", n_seats: int) -> bool:
    """A19 の判定を「無料か」から「試せるか × 乗り換えの手続コスト」へ（第10版）。

    金額ゼロでも、組織的コストが正なら消去の刃は立つ。
    逆に組織的コストもゼロなら、失うものがないので D6 系でしか消えない。
    """
    if m.cost_to_buyer is None or m.cost_to_buyer > 0:
        return True
    if p is None:
        return False              # 座標がなければ組織的コストを測れない。第9版の判定へ落ちる
    sp, par, _ = cost_vector(p, n_seats)     # 注意はどの選択肢にも等しく掛かるので差にならない
    return sp + par >= 2

CALIBRATED_CODES: Dict[str, str] = {
    "A1_NOT_EXPRESSIBLE": "EXPR_OK",      # 基準の階数と隣接則。6業界で較正
    "A5_NOT_EXPRESSIBLE": "EXPR_OK",
    "A16_NOT_CONV_AT_SEAT": "EXPR_OK",
    "R6b_LT_SHORT": "ACQUIRE",            # 買い手データの取得月数。POS のある業界では過剰
    "A8_BINDER_EMPTY": "BINDER_SRC",      # 拘束者の同定が要る出典。規制当局は法令由来で漏れる
    "A8_BINDER_NOT_ABOVE": "BINDER_SRC",
    "A2_C_NOT_SINGLETON": "ISO_KEYS",     # 所轄庁・系列は規制産業の語。非規制業界では常に空
}


def apply_calibration(findings: List[Finding], judgments: List[Judgment],
                      industry: Optional[str]) -> Tuple[List[Finding], List[Judgment]]:
    """未較正の業界では、較正定数に依存する判定を **停止から降格へ落とす**。

    原理由来の判定はそのまま止める。較正由来の判定は「この業界では確かめていない」
    と申し送って人間へ回す。知らない業界で機械が黙って断定しないための規律である。
    """
    if industry is None or industry in CALIBRATED_ON:
        return findings, judgments
    out: List[Finding] = []
    for f in findings:
        t = CALIBRATED_CODES.get(f.code)
        if t and f.level in ("stop", "reject"):
            out.append(Finding(f.code, "demote", f.ref))
            judgments = judgments + [Judgment("UNCALIBRATED", f"{f.code}<-{t}@{industry}")]
        else:
            out.append(f)
    judgments = judgments + [Judgment("SIGMA_UNCALIBRATED", industry)]
    return out, judgments


def check_seats(n: Nu) -> List[Finding]:
    """R18（第9版）：制度が置いた座席は所掌が定義されているので、複数の基準を持てない"""
    out = []
    for j in n.J:
        if j.origin == "制度" and len(j.kappa) != 1:
            out.append(Finding("R18_INSTITUTIONAL_MULTI_KAPPA", "stop",
                               f"{j.name} {sorted(j.kappa)}"))
        if j.origin == "制度" and j.reads and not j.form:
            out.append(Finding("R18_FORM_EMPTY", "stop", j.name))
    return out


def check_cost(n: Nu, live: List[Mi]) -> List[Finding]:
    """A19（第9版）：買い手にとって無料の手段は、帰責・手続・権限・資源では消せない"""
    out = []
    for m in live:
        if m.cost_to_buyer is None:
            continue
        if m.cost_to_buyer > 0:
            continue
        if eliminable_of(n.prod, m, len(n.J)):
            out.append(Finding("A19_ORG_COST_POSITIVE", "info", m.name)); continue
        prim = m.order[0] if m.order else sorted(m.dims)[0]
        if prim not in ELIMINABLE_IF_FREE:
            out.append(Finding("A19_FREE_NOT_ELIMINABLE", "stop",
                               f"{m.name} 主位置={prim}"))
    return out


def check_D5_binder(n: Nu, live: List[Mi]) -> List[Finding]:
    """A20（第9版）：資源配分の枠を決める権限が読み手自身にあれば、それは拘束ではなく選択"""
    out = []
    if not any("D5" in m.dims for m in live):
        return out
    reader = j_star(n).name
    wnames = {w.name for w in n.W}
    for m in live:
        if "D5" not in m.dims:
            continue
        a = dict(m.binders).get("D5") or (m.binder if m.dims == {"D5"} else None)
        if not a:
            out.append(Finding("A20_D5_BINDER_UNSET", "stop", m.name)); continue
        if a not in wnames:
            out.append(Finding("A20_D5_NOT_IN_W", "stop", f"{m.name} {a}")); continue
        if a == reader:
            out.append(Finding("A20_D5_IS_READER", "stop", f"{m.name} {a}"))
    return out


def check_gamma_pre(n: Nu, S: List[str]) -> List[Finding]:
    """A10：Σ から落ちた段は「資料の外で成立済み」として明示的に与える"""
    dropped = [s for s in STAGES if s not in S and STAGES.index(s) < STAGES.index(S[-1])]
    out = []
    for s in dropped:
        if not n.gamma_pre.get(s):
            out.append(Finding("R8_PRE_MISSING", "stop", s))
    return out


def blocks_on(n: Nu, S: List[str], live: List[Mi], forms: Set[str]) -> List[str]:
    dims = {d for m in live for d in m.dims}
    E = n.E_judge
    cand = [
        ("B_visualize", E == "困っていない", "①"),
        ("B_what_is_it", E in ("困っていない", "手段を知らない"), "③"),
        ("B_form_mapping", len(n.J) >= 2, "③"),                     # A11
        ("B_compare_current", E in ("比較検討中", "うちも知っている"), "⑤"),
        ("B_spec_table", n.A == "買う前に分かる", "⑤"),
        ("B_case_numbers", n.A == "使えば分かる", "⑤"),
        ("B_precedent", "D4" in dims, "⑤"),
        ("B_mechanism", n.A == "使っても分からない", "⑤"),
        ("B_certification", n.A == "使っても分からない", "⑤"),
        ("B_trial", n.A == "使えば分かる" or n.C_move == "すぐ試せる", "⑥"),
        ("B_migration", n.C_move == "大仕事", "⑥"),
        ("B_deadline", bool(forms & {"A", "B", "C", "D"}), "④"),
        ("B_why_now", bool(forms - {"D"}), "④"),
        ("B_scope_of_date", bool(forms), "④"),                      # A8
        ("B_prohibition", bool(forms & {"Ea", "Eb", "Ec"}), "④"),
        ("B_liability_matrix", "D2" in dims, "⑤"),
        ("B_authority", "D3" in dims, "⑤"),
        ("B_opportunity_cost", "D5" in dims, "⑤"),
        ("B_third_party", bool(dims & R7_DIMS), "⑤"),
        ("B_intra_category", bool(dims & D7_DIMS), "⑥"),
        ("B_kappa_quantity", True, "⑥"),                            # A5
        ("B_realize", True, "⑥"),                                   # A12
        ("B_self_check", "⑤" in S, "⑥"),                            # A14
        ("B_own_check", "⑤" in S, "⑤"),                              # R17（第8版）
        ("B_chain_form", any(j.origin == "制度" and j.reads for j in n.J), "③"),   # R18
        ("B_decision_date", bool(forms), "④"),                       # A18
        ("B_seat_quantities", len([x for x in n.J if x.reads]) >= 2, "⑥"),   # A23
        ("B_coverage_table", "④" in S, "⑥"),                        # A9
        ("B_draft_reason", len(n.J) >= 2, "⑥"),
        ("B_summary_sheet", len(n.J) >= 2, "⑥"),
        ("B_human_slot", len(n.J) >= 2, "⑥"),
        ("B_layer_a", n.procedural, "⑥"),
        ("B_downward", n.downward, "⑥"),
    ]
    return [b for b, phi, st in cand if phi and st in S]


# ══════════════════════════════════════════════════════════════════ 層2

def effective_LT(n: Nu) -> int:
    acq = acquire_of(n.prod)
    return n.LT_months + max([acq.get(t.q_source, 0) for t in n.tau] + [0])


def check_applies(n: Nu, t: TauItem, today: date) -> Optional[Finding]:
    """A8：その日付が当該買い手に効くか。出典階層とは別の軸"""
    if t.scope is None:
        return Finding("A8_SCOPE_EMPTY", "reject", f"{t.form}:{t.d}")
    for k, v in t.scope.keys:
        got = n.buyer_context.get(k)
        if got is None:
            return Finding("A8_SCOPE_UNVERIFIED", "demote", f"{t.form}:{t.d} {k}")
        if got != v:
            return Finding("A8_SCOPE_MISMATCH", "reject", f"{t.form}:{t.d} {k}={v}≠{got}")
    if t.scope.applied_from is not None and t.scope.applied_from <= today:
        return Finding("A8_ALREADY_APPLIED", "reject",
                       f"{t.form}:{t.d} from={t.scope.applied_from.isoformat()}")
    if not t.scope.source:
        # A22：値の真偽は機械では見られない。出所がなければ主位置に使えないだけで、元は落とさない
        return Finding("A22_SCOPE_UNSOURCED", "demote", f"{t.form}:{t.d}")
    return None


def check_binder(n: Nu, t: TauItem) -> Tuple[Optional[Finding], Optional[Judgment]]:
    """A8：契約・第三者承認由来の日付は、拘束者が一意でなければ立たない"""
    if t.src not in BINDER_SRC and t.form != "Ec":
        return None, None
    up = [b for b in t.binders if b in n.upstream]
    if not t.binders:
        return Finding("A8_BINDER_EMPTY", "reject", f"{t.form}:{t.d}"), None
    if not up:
        return Finding("A8_BINDER_NOT_ABOVE", "reject",
                       f"{t.form}:{t.d} {','.join(t.binders)}"), None
    if len(up) > 1:
        return None, Judgment("A8_BINDER_AMBIGUOUS", f"{t.form}:{t.d} {','.join(up)}")
    return None, None


def check_tau(n: Nu, today: date, uncal: bool = False
              ) -> Tuple[List[TauItem], List[Finding], List[Judgment]]:
    ok: List[TauItem] = []
    f: List[Finding] = []
    j: List[Judgment] = []
    forms = {t.form for t in n.tau}
    kn, lt = kappa_n(n), effective_LT(n)
    ex = expr_ok_of(n.prod)
    for t in n.tau:
        ref = f"{t.form}:{t.d}"
        if t.src == "売り手都合":
            f.append(Finding("SRC_SELLER", "reject", ref)); continue
        if t.form == "Ed":
            f.append(Finding("R5d_PERPETUAL_BAN", "stop", ref)); continue
        if t.d is None:
            f.append(Finding("DATE_EMPTY", "reject", ref)); continue
        if t.d <= today:
            f.append(Finding("R6a_PAST", "reject", ref)); continue
        ap = check_applies(n, t, today)
        if ap:
            f.append(ap)
            if ap.level in ("reject", "stop"):
                continue
        bf, bj = check_binder(n, t)
        if bf:
            if uncal and bf.code in CALIBRATED_CODES:
                f.append(Finding(bf.code, "demote", bf.ref))
            else:
                f.append(bf); continue
        if bj:
            j.append(bj)
        months = (t.d.year - today.year) * 12 + (t.d.month - today.month)
        if t.form in ("A", "C") and months - lt < 0:
            f.append(Finding("R6b_LT_SHORT", "demote" if uncal else "reject",
                             f"{ref} {months}m<{lt}m"))
            if not uncal:
                continue
        if t.form == "B" and t.wait_months is None:
            f.append(Finding("WAIT_UNKNOWN", "demote", ref))
        if not t.confirmed and M0_KILL[t.form] == "不可逆":
            f.append(Finding("UNCONFIRMED_PRIMARY", "stop", ref)); continue
        if t.known == "既知" and not t.q:
            f.append(Finding("KNOWN_WITHOUT_Q", "reject", ref)); continue
        if t.q:
            if t.q_kappa is None:
                j.append(Judgment("Q_KAPPA_UNSET", ref))
            elif t.q_kappa not in ex:
                j.append(Judgment("EXPR_TABLE_MISS", f"{ref} k={t.q_kappa}"))
            elif not (ex[t.q_kappa] & set(kn)):
                if t.q_recast:
                    f.append(Finding("A1_RECAST_DECLARED", "info", ref))
                else:
                    f.append(Finding("A1_NOT_EXPRESSIBLE", "stop",
                                     f"{ref} {t.q_kappa}->{sorted(kn)}")); continue
        if t.decision is None:
            j.append(Judgment("A18_DECISION_UNDECLARED", ref))
        elif not t.decision:
            f.append(Finding("A18_RESULT_NOT_DECISION", "reject", ref)); continue
        if t.windows > 1:
            f.append(Finding("A18_MULTIPLE_WINDOWS", "demote", f"{ref} x{t.windows}"))
        if t.q and t.q_source == "買い手データ" and not t.q_receipt:
            f.append(Finding("R15_RECEIPT_MISSING", "reject", ref)); continue
        if t.q_low is not None and t.q_high is not None and t.q_low <= 0:
            f.append(Finding("Q_RANGE_CROSSES_ZERO", "stop", ref)); continue
        ok.append(t)
    live_forms = {t.form for t in ok}
    if "D" in live_forms and not (live_forms & {"B", "C"}):
        ok = [t for t in ok if t.form != "D"]
        f.append(Finding("TD_ALONE", "reject", "D"))
    f += check_tau_order(ok, lt)
    if not ok:
        f.append(Finding("R6_NO_TAU", "stop"))
    ok.sort(key=lambda t: KILL_ORDER[M0_KILL[t.form]])
    return ok, f, j


def sub_months(d: date, m: int) -> date:
    y, mo = d.year, d.month - m
    while mo <= 0:
        mo += 12; y -= 1
    return date(y, mo, min(d.day, 28))


def start_deadline(ok: List[TauItem], lt: int) -> Optional[date]:
    """④が示す着手期限日。A/C の終端日から実効リードタイムを引いた最小値"""
    ds = [sub_months(t.d, lt) for t in ok if t.form in ("A", "C") and t.d]
    return min(ds) if ds else None


def check_tau_order(ok: List[TauItem], lt: int) -> List[Finding]:
    """R12：C の着手期限日が、同一 τ 内の A の終端日より後にあってはならない"""
    out = []
    a_dates = [t.d for t in ok if t.form == "A" and t.d]
    if not a_dates:
        return out
    a_min = min(a_dates)
    for t in ok:
        if t.form != "C" or t.d is None:
            continue
        start = sub_months(t.d, lt)
        if start > a_min:
            out.append(Finding("R12_ORDER_CONFLICT", "reject",
                               f"C着手{start.isoformat()}>A終端{a_min.isoformat()}"))
    return out


def check_delta(n: Nu) -> Tuple[List[Mi], List[Finding]]:
    live, f = [], []
    for m in n.M:
        if m.mtype == "M0":
            f.append(Finding("M0_EXCLUDED", "info", m.name)); continue
        if not m.dims:
            f.append(Finding("DELTA_UNSET", "stop", m.name)); continue
        bad = sorted(d for d in m.dims if d not in ALLOWED.get(m.mtype, set()))
        if bad:
            f.append(Finding("ALLOWED_VIOLATION", "stop", f"{m.name} {m.mtype}x{bad}")); continue
        a7 = check_binder_dim(n, m)
        if a7:
            f.append(a7); continue
        prim = m.order[0] if m.order else sorted(m.dims)[0]
        if prim not in PRIMARY.get(m.mtype, set()):
            f.append(Finding("PRIMARY_MISMATCH", "demote", f"{m.name} {prim}"))
        live.append(m)
    if not live:
        f.append(Finding("NO_ELIMINABLE_MI", "stop"))
    return live, f


def check_W(n: Nu) -> Tuple[List[Finding], List[Judgment]]:
    """A12：承認されても、費目を減らす座席がいなければ κ_n は動かない。
    A21（第11版）：権限があっても、その座席が実行を拒めば同じことである。"""
    if not n.W:
        return [Finding("A12_NO_EXECUTOR", "stop")], []
    if not any(w.accounts for w in n.W):
        return [Finding("A12_NO_ACCOUNT", "stop", ",".join(w.name for w in n.W))], []
    f, j = [], []
    for w in n.W:
        if w.willing is None:
            j.append(Judgment("A21_WILLING_UNKNOWN", w.name))
        elif w.willing is False:
            f.append(Finding("A21_EXECUTOR_REFUSES", "stop",
                             f"{w.name}({'・'.join(sorted(w.kappa)) or '理由未入力'})"))
    if f and not any(w.willing for w in n.W):
        f.append(Finding("A21_NO_WILLING_EXECUTOR", "stop"))
    return f, j


def check_binder_dim(n: Nu, m: Mi) -> Optional[Finding]:
    """A7：拘束者が実在し、かつ向きが買い手より上であること"""
    need = sorted(d for d in m.dims if BINDER_REQUIRED.get(d))
    if not need:
        return None
    table = dict(m.binders)
    if not table:
        if len(need) > 1:
            return Finding("A7_BINDER_PER_DIM_MISSING", "stop", f"{m.name} {need}")
        table = {need[0]: m.binder} if m.binder else {}
    known = set(n.upstream) | {s.name for s in n.J} | {v.name for v in n.V}
    for d in need:
        a = table.get(d)
        if not a:
            return Finding("A7_BINDER_UNSET", "stop", f"{m.name} {d}")
        if a in n.downstream:
            return Finding("A7_DIRECTION_REVERSED", "stop", f"{m.name} {d}:{a}")
        if a not in known:
            return Finding("A7_BINDER_ABSENT", "stop", f"{m.name} {d}:{a}")
        if a not in n.upstream:
            return Finding("A7_NOT_ABOVE", "stop", f"{m.name} {d}:{a}")
    return None


def pick_two(live: List[Mi]) -> List[str]:
    order = {"既存外注": 0, "取引上位者の指定": 1, "内製": 2, "競合": 3}
    return [m.name for m in sorted(live, key=lambda m: order.get(m.mtype, 9))[:2]]


def iso_cases(n: Nu, seller: Seller) -> Tuple[List[Dict[str, str]], List[Judgment]]:
    """事例の同型性。第10版で鍵を Π3 由来の構造キーへ置換した。

    所轄庁・系列は λ（拘束の所在）の粗い代理変数であり、非規制の買い手では常に空になる。
    実際、第6〜8版の全16セルで ISO_CONTEXT_MISSING が発火し、同型性検査は一度も走っていない。
    """
    keep, j = [], []
    keys = ISO_KEYS if any(n.buyer_context.get(k) for k in ISO_KEYS) else ISO_KEYS_CALIBRATED
    missing = [k for k in keys if not n.buyer_context.get(k)]
    if missing and seller.named_cases:
        j.append(Judgment("ISO_CONTEXT_MISSING", ",".join(missing)))
    for c in seller.named_cases:
        if not c.get("実名"):
            continue
        if any(n.buyer_context.get(k) and c.get(k) != n.buyer_context.get(k) for k in keys):
            continue
        keep.append(c)
    return keep, j


def check_C_singleton(n: Nu, seller: Seller) -> Tuple[Finding, List[str]]:
    B1 = any("価格" in s.kappa for s in n.J)
    comparing = n.E_judge in ("比較検討中", "うちも知っている")
    if not B1 and not comparing:
        return Finding("A2_NOT_REQUIRED", "info"), []
    have = []
    if iso_cases(n, seller)[0]: have.append("D7a")
    if seller.registrations: have.append("D7b")
    if seller.liability_scope: have.append("D7c")
    if seller.price_disclosure: have.append("D7d")
    if not have:
        return Finding("A2_C_NOT_SINGLETON", "stop"), []
    return Finding("A2_SATISFIED", "info", ",".join(have)), have


def check_R4(n: Nu, live: List[Mi], seller: Seller) -> List[Finding]:
    """R4：D4 は前例を要求する。他社事例と制度的後ろ盾がともに空なら停止"""
    if not any("D4" in m.dims for m in live):
        return []
    if iso_cases(n, seller)[0] or seller.registrations:
        return [Finding("R4_PRECEDENT_OK", "info")]
    return [Finding("R4_NO_PRECEDENT", "stop")]


def check_R7(live: List[Mi], seller: Seller) -> List[Finding]:
    """第6版：次元ごとに実数を **2つ** 要求する"""
    pairs = {
        "D6a": (bool(seller.registrations), seller.registration_expiry is not None),
        "D6b": (seller.channel_total > 0 and seller.funnel_present,
                seller.funnel_yield is not None),
        "D6c": (seller.upstream_approvals > 0, seller.upstream_lead_days is not None),
    }
    out = []
    for m in live:
        for d in sorted(m.dims & R7_DIMS):
            a, b = pairs[d]
            if a and b:
                out.append(Finding(f"R7_{d}_OK", "info", m.name))
            elif a and not b:
                out.append(Finding(f"R7_{d}_HALF", "stop", m.name))
            else:
                out.append(Finding(f"R7_{d}_MISSING", "stop", m.name))
    return out


def fire_rules(n: Nu, tau_ok: List[TauItem], live: List[Mi], S: List[str]) -> List[str]:
    dims = {d for m in live for d in m.dims}
    r = []
    if "D5" in dims: r.append("R1_OK" if tau_ok else "R1_VIOLATION")
    if "D2" in dims: r.append("R2")
    if "D3" in dims: r.append("R3")
    if "D4" in dims: r.append("R4")
    for t in tau_ok:
        if t.form.startswith("E"):
            r.append(f"R5{t.form[1]}")
    if dims & R7_DIMS: r.append("R7")
    if dims & D7_DIMS: r.append("A2")
    r.append("N1_ENTHYMEME_OK" if len(n.J) == 1 else "N2_WRITE_CONCLUSION")
    if any(s.gamma == "合議" for s in n.J): r.append("GAMMA_COLLEGIAL")
    if any("価格" in s.kappa for s in n.J): r.append("B1")
    if n.J and any(s.chi != n.J[0].chi for s in n.J): r.append("B2")
    if n.J and (n.J[-1].gamma == "合議" or n.J[-1].omega == "社外"): r.append("B3")
    if n.procedural: r.append("PROCEDURAL")
    if n.downward: r.append("DOWNWARD")
    r.append("A5_KAPPA_QUANTITY")
    r.append("R13_REALIZE")
    if "④" in S: r.append("R14_TYPE")
    # 伝達漏れの修正（第12版）：R10a は生成後に検査していたのに、
    # 生成前の指示に一度も出していなかった（第10版 5/8 で発火）。
    if "④" in S and "⑥" in S: r.append("R10a_NO_REPRODUCE")
    if "⑤" in S: r.append("R16_SELF_APPLY")
    if "⑤" in S: r.append("R17_NOT_INSULT")
    if len([x for x in n.J if x.reads]) >= 2: r.append("A16_CHAIN")
    if any(x.origin == "制度" and x.reads for x in n.J): r.append("R18_INSTITUTIONAL")
    if len([x for x in n.J if x.reads]) >= 2: r.append("A23_PER_SEAT")
    if n.W: r.append("A21_WILLING")
    if "③" in S and len(n.J) >= 2: r.append("R11_FORM_MAPPING")
    if "④" in S: r.append("R10c_COVERAGE")
    for v in n.V:
        r.append(f"VETO:{v.name}")
    return r


def theta_auto(kind: str) -> float:
    return 1.0 - U_ASK / (U + HARM[kind])


def segment_action(kind: str, c: float, n_cand: int) -> str:
    if n_cand > 3:
        return "STOP"
    return "AUTO" if c >= theta_auto(kind) else "OFFER_CANDIDATES"


# ══════════════════════════════════════════════════════════════════ 生成前

def compile_deal(n: Nu, seller: Seller, today: date,
                 industry: Optional[str] = None) -> dict:
    S, by, oos = compute_sigma(n)
    if oos:
        return {"generate": False, "out_of_scope": True, "sigma": S, "sigma_by": by,
                "findings": [Finding("OUT_OF_SCOPE_LOW_INVOLVEMENT", "stop")],
                "needs_judgment": [], "llm_calls": 0}
    wf, wj = check_W(n)
    pre = check_gamma_pre(n, S) + wf + check_seats(n)
    uncal = not (industry is None or industry in CALIBRATED_ON)
    tau_ok, tf, tj = check_tau(n, today, uncal)
    live, df = check_delta(n)
    cf, d7 = check_C_singleton(n, seller)
    r7 = check_R7(live, seller) + check_R4(n, live, seller)
    _, ij = iso_cases(n, seller)
    findings = pre + tf + df + [cf] + r7 + check_cost(n, live) + check_D5_binder(n, live)
    judgments = tj + ij + wj
    findings, judgments = apply_calibration(findings, judgments, industry)
    stop = [x for x in findings if x.level == "stop"]
    return {
        "sigma": S, "sigma_by": by, "out_of_scope": False,
        "industry": industry, "calibrated": industry is None or industry in CALIBRATED_ON,
        "j_star": j_star(n).name, "kappa_n": sorted(kappa_n(n)),
        "form_n": sorted(form_n(n)),
        "tau_ok": [(t.form, t.d.isoformat(), t.src, t.known) for t in tau_ok],
        "delta": [(m.name, m.mtype, sorted(m.dims),
                   dict(m.binders) or ({sorted(m.dims & set(BINDER_REQUIRED))[0]: m.binder}
                                       if m.binder and (m.dims & set(BINDER_REQUIRED)) else {}))
                  for m in live],
        "five_mentions": pick_two(live),
        "d7_basis": d7,
        "executors": [(w.name, sorted(w.accounts)) for w in n.W],
        "unwilling": [w.name for w in n.W if w.willing is False],
        "chain": [(j.name, sorted(j.kappa), sorted(j.form), j.origin)
                  for j in n.J if j.reads],
        "start_deadline": (start_deadline(tau_ok, effective_LT(n)).isoformat()
                           if start_deadline(tau_ok, effective_LT(n)) else None),
        "talk_guide": talk_guide(n, S),
        "blocks": blocks_on(n, S, live, {t.form for t in tau_ok}),
        "rules": fire_rules(n, tau_ok, live, S),
        "findings": findings,
        "needs_judgment": judgments,
        "generate": not stop,
        "llm_calls": 0 if stop else 1 + len(S),
    }


# ══════════════════════════════════════════════════════════════════ 生成後（層3.5）

def check_v0(copy: Dict[str, str]) -> List[Finding]:
    """禁止語彙の完全一致。ここは決定的"""
    out = []
    for st, w in copy.items():
        if not w:
            continue
        for v in V0:
            if v in w:
                out.append(Finding("R9_V0", "stop", f"{st}:{v}"))
        for p in V0_RE:
            if re.search(p, w):
                out.append(Finding("R9_V0_RE", "stop", f"{st}:{p}"))
    return out


def check_unit_presence(copy: Dict[str, str], dec: Declared,
                       stages: Sequence[str] = STAGES) -> Tuple[List[Finding], bool]:
    """②で導入した単位が⑥に出現するか。A6：出現していれば『併記』であって置換ではない。
    ②が Σ にないときは s2_unit は未定義であって、検査対象ではない（A10）

    A25（第12版）：**照合は正規化した単位語で行う。**
    N4 は Qty = ⟨数, 単位, 基準⟩ と定めているが、宣言欄は文字列なので、生成器は
    「作業時間（時間）」のように単位に説明句を付けて申告してくる。第12版の走行では
    R10b_UNIT_ABSENT 15件のうち **14件が、本文に単位が在るのに完全一致で外した誤検出**
    だった。宣言の型が緩いなら、照合の側が正規化する（A24 と同じ型の混同）。
    """
    if "②" not in stages or not dec.s2_unit:
        return [], True
    kept = any(c in copy.get("⑥", "") for c in unit_tokens(dec.s2_unit))
    return ([] if kept else [Finding("R10b_UNIT_ABSENT", "stop", dec.s2_unit)]), kept


def unit_tokens(u: str) -> Set[str]:
    """宣言された単位文字列から、照合に使える単位語の候補を取り出す（A25）。

    「作業時間（時間）」→ {作業時間（時間）, 作業時間, 時間}
    「時間（売場に張り付くパート人時）」→ {…, 時間, 売場に張り付くパート人時}
    1文字の候補は落とす（「日」「件」単独では地の文に埋もれて照合にならない）。
    """
    out = {u.strip()}
    m = re.match(r"^(.*?)[（(](.*?)[)）]\s*$", u.strip())
    if m:
        out |= {m.group(1).strip(), m.group(2).strip()}
    for part in re.split(r"[（()）／・、,/]", u):
        if part.strip():
            out.add(part.strip())
    return {c for c in out if len(c) >= 2}


def check_seat_words(copy: Dict[str, str], dec: Declared,
                     chain: Sequence[Tuple[str, Sequence[Kappa], Sequence[str], str]]
                     ) -> List[Finding]:
    """A23 の紙側（第12版）。

    check_chain は s6_kappa_by_seat の**申告**だけを見る。申告さえすれば通ってしまうと、
    「座席ごとに量を置いた」と書くだけで A16 が消える。それは Π2 の検査ではない。
    R10b が②の単位について既にやっているのと同じことを、座席の様式語についてもやる：
    その座席の基準で読める量を⑥に置いたと申告したなら、
    **その座席の様式語のどれかが⑥の本文に出現していなければならない。**
    様式語が未登録の座席は照合対象を持たないので飛ばす（N2：⊥ は比較できない）。
    """
    f: List[Finding] = []
    if not chain or not dec.s6_kappa_by_seat:
        return f
    body = copy.get("⑥", "")
    for name, _kappa, form, _origin in chain:
        if name not in dec.s6_kappa_by_seat or not form:
            continue
        if not any(w and w in body for w in form):
            f.append(Finding("A23_SEAT_WORD_ABSENT", "stop", f"{name}:{'/'.join(form)}"))
    return f


def check_realize(dec: Declared, executors: Sequence[Tuple[str, Sequence[str]]],
                  unwilling: Sequence[str] = ()) -> Tuple[List[Finding], List[Judgment]]:
    """R13（A12）：〈誰が・いつ・どの費目を〉の三つ組。両替は写像ではなく行為である。

    A24（第12版）：三つ組は**集合**である。単数の欄しか無かったので、
    生成器は複数費目を「媒体費・広報外注費」と連結して申告するしかなかった。
    s6_realize（組の列）があればそちらを、無ければ従来の単数欄を1件として扱う。
    """
    f, j = [], []
    if dec.s6_realize:
        acts = [tuple(str(x) if x is not None else None for x in a) for a in dec.s6_realize]
        if not acts:
            j.append(Judgment("R13_REALIZE_UNDECLARED")); return f, j
    else:
        trio = (dec.s6_realize_actor, dec.s6_realize_date, dec.s6_realize_account)
        if any(x is None for x in trio):
            j.append(Judgment("R13_REALIZE_UNDECLARED"))
            return f, j
        acts = [trio]
    for a in acts:
        if len(a) != 3 or any(x is None or not str(x).strip() for x in a):
            f.append(Finding("R13_REALIZE_EMPTY", "stop")); return f, j
    if not executors:
        j.append(Judgment("R13_W_UNKNOWN")); return f, j
    names = {a for a, _ in executors}
    accts = {c for _, cs in executors for c in cs}
    held = {(a, c) for a, cs in executors for c in cs}      # authority(w, a) は対である
    for actor, _d, account in acts:
        if actor not in names:
            f.append(Finding("R13_ACTOR_NOT_IN_W", "stop", actor))
        elif account not in accts:
            # A24 の診断：連結された費目か、そもそも存在しない費目か
            parts = [p.strip() for p in re.split(r"[・、,／/＋+]", account) if p.strip()]
            if len(parts) > 1 and all(p in accts for p in parts):
                f.append(Finding("A24_REALIZE_MERGED", "stop", account))
            else:
                f.append(Finding("R13_ACCOUNT_NOT_HELD", "stop", account))
        elif (actor, account) not in held:
            f.append(Finding("R13_NO_AUTHORITY_PAIR", "stop", f"{actor}×{account}"))
        elif actor in set(unwilling):
            f.append(Finding("A21_NAMED_ACTOR_REFUSES", "stop", actor))
    return f, j


def check_insult(dec: Declared, gamma_own: Dict[str, str]) -> Tuple[List[Finding], List[Judgment]]:
    """R17（第8版）：侮辱は単調性の破れである。

    買い手が資料の外で自分で積んだ承認 Γ^own の要素を、⑤が否定していないか。
    否定していれば、それを受け入れるには買い手が自分の資本を減らさねばならない。
    偽なる主張ではないので ⊥ ではなく、Π1 の第1式（単調な追加）で追加できない。
    どの要素を否定しているかは意味判断なので、生成器に申告させる（Python は照合のみ）。
    """
    f, j = [], []
    if dec.s5_denies_own is None:
        j.append(Judgment("R17_INSULT_UNDECLARED")); return f, j
    d = dec.s5_denies_own.strip()
    if not d:
        return [Finding("R17_NO_INSULT", "info")], j
    hit = [k for k, v in gamma_own.items() if d in v or v in d] if gamma_own else []
    f.append(Finding("R17_DENIES_OWN", "stop", f"{d}{'@' + ','.join(hit) if hit else ''}"))
    return f, j


def check_chain(dec: Declared,
                chain: Sequence[Tuple[str, Sequence[Kappa], Sequence[str], str]],
                kept_unit: bool = False) -> Tuple[List[Finding], List[Judgment]]:
    """A16（第9版）：Π2 は「各リンクで濾す」と言っている。終端の座席だけ見てはならない。

    資料を読む座席すべてについて
      ・⑥に置いた量が、その座席の基準で読めること
      ・制度由来の座席については、③の対応語がその座席の様式語を含むこと
    """
    f, j = [], []
    if not chain:
        return f, j
    if dec.s6_kappa is None:
        return f, j                      # A5 側で要判断に積まれている
    # A23（第11版）：⑥に置く量は単一ではなく、読む座席ごとの組である。
    # Π2 の ∀k から直に出るのに、第10版までの実装は s6_kappa 一つで全座席を賄おうとしていた。
    by_seat = dec.s6_kappa_by_seat or {}
    if chain and not by_seat:
        j.append(Judgment("A23_PER_SEAT_UNDECLARED", ",".join(c[0] for c in chain)))
    # ⑥に既に在る基準（②の単位を保持していれば実務性も在る＝A6 の併記）
    bases = {dec.s6_kappa}
    if kept_unit and dec.s2_unit:
        bases.add("実務性")
    for name, kappa, form, origin in chain:
        own = by_seat.get(name)
        cand = bases | ({own} if own else set())
        ok = any(b in EXPR_OK and (EXPR_OK[b] & set(kappa)) for b in cand)
        if not ok:
            f.append(Finding("A16_NOT_CONV_AT_SEAT", "stop",
                             f"{name}:{sorted(cand)}->{sorted(kappa)}"))
        if origin == "制度" and form:
            m = dec.s3_form_mapping
            if m is None:
                j.append(Judgment("A16_MAPPING_UNDECLARED", name))
            elif not any(w in m for w in form):
                f.append(Finding("R18_BYPASSED_SEAT", "stop",
                                 f"{name}:{'/'.join(form)}"))
    return f, j


def check_dates_v7(dec: Declared, deadline: Optional[str]) -> Tuple[List[Finding], List[Judgment]]:
    """R12b / R16（A14）：⑤で他手段に課した期限は、自社案にも当たる"""
    f, j = [], []
    if deadline and dec.s6_start_date:
        if dec.s6_start_date > deadline:
            f.append(Finding("R12b_START_AFTER_DEADLINE", "stop",
                             f"⑥{dec.s6_start_date}>④{deadline}"))
    elif deadline and dec.s6_start_date is None:
        j.append(Judgment("R12b_START_UNDECLARED", deadline))
    if dec.s6_self_check is None:
        j.append(Judgment("R16_SELF_APPLY_UNDECLARED"))
    elif dec.s6_self_check is False:
        f.append(Finding("R16_SELF_APPLY_FAILED", "stop"))
    return f, j


def check_declared(dec: Declared, kn: Set[Kappa], kept_unit: bool,
                   stages: Sequence[str], n_seats: int) -> Tuple[List[Finding], List[Judgment]]:
    """宣言された値の比較のみ。意味判定はしない。None は未定義（A10）"""
    f, j = [], []
    has4, has2, has3 = "④" in stages, "②" in stages, "③" in stages

    # R10a 反復の再生産（0 は「反復しない」。比較の定義域に入れない）
    if has4:
        if dec.s4_declares_repetition is None:
            j.append(Judgment("S4_REPETITION_UNDECLARED"))
        elif dec.s4_declares_repetition:
            if dec.s4_period_months is None or dec.s6_period_months is None:
                f.append(Finding("R10a_PERIOD_UNDECLARED", "stop"))
            elif dec.s6_period_months == 0 or dec.s4_period_months == 0:
                f.append(Finding("R10a_NOT_PERIODIC", "info",
                                 f"s4={dec.s4_period_months}m s6={dec.s6_period_months}m"))
            elif dec.s6_period_months <= dec.s4_period_months:
                f.append(Finding("R10a_REPRODUCES_PROBLEM", "stop",
                                 f"s4={dec.s4_period_months}m s6={dec.s6_period_months}m"))

    # R10b 単位。A6：禁じるのは置換であって併記ではない
    if has2 and dec.s2_unit:
        if dec.s6_recasts_unit is None:
            j.append(Judgment("S6_UNIT_RECAST_UNDECLARED", dec.s2_unit))
        elif dec.s6_recasts_unit and not kept_unit:
            f.append(Finding("R10b_UNIT_REPLACED", "stop",
                             f"{dec.s2_from_unit}->{dec.s2_unit}"))
        elif dec.s6_recasts_unit and kept_unit:
            f.append(Finding("R10b_UNIT_JUXTAPOSED", "info", dec.s2_unit))

    # A5 ⑥が κ_n で読めるか
    if dec.s6_kappa is None:
        j.append(Judgment("A5_KAPPA_UNDECLARED"))
    elif dec.s6_kappa not in EXPR_OK:
        j.append(Judgment("EXPR_TABLE_MISS", f"⑥ k={dec.s6_kappa}"))
    elif not (EXPR_OK[dec.s6_kappa] & set(kn)):
        f.append(Finding("A5_NOT_EXPRESSIBLE", "stop",
                         f"{dec.s6_kappa}->{sorted(kn)}"))

    # R14 量の型（A13）。単発の④に flow 型の量は立たない
    if dec.s6_kappa_type is None:
        j.append(Judgment("R14_TYPE_UNDECLARED"))
    elif dec.s6_kappa_type not in ("stock", "flow"):
        j.append(Judgment("R14_TYPE_UNKNOWN", str(dec.s6_kappa_type)))
    elif has4 and dec.s6_kappa_type == "flow" and dec.s4_period_months == 0:
        f.append(Finding("R14_FLOW_ON_ONESHOT", "stop"))

    # A9 外延
    if has4:
        if dec.s6_coverage_subset is None:
            j.append(Judgment("A9_SUBSET_UNDECLARED"))
        elif not dec.s6_coverage_subset:
            f.append(Finding("R10c_NOT_SUBSET", "stop"))
        if dec.s6_coverage_full is None:
            j.append(Judgment("A9_COVERAGE_UNDECLARED"))
        elif not dec.s6_coverage_full:
            if dec.s6_coverage_disclosed is None:
                j.append(Judgment("A9_DISCLOSURE_UNDECLARED"))
            elif not dec.s6_coverage_disclosed:
                f.append(Finding("R10c_COVERAGE_HIDDEN", "stop"))

    # A11 名づけの移送
    if has3 and n_seats >= 2:
        if dec.s3_form_mapping is None:
            j.append(Judgment("R11_MAPPING_UNDECLARED"))
        elif not dec.s3_form_mapping.strip():
            f.append(Finding("R11_NO_FORM_MAPPING", "stop"))

    if dec.s5_is_constraint_disclosure is None:
        j.append(Judgment("S5_FORM_UNDECLARED"))
    elif dec.s5_is_constraint_disclosure is False:
        f.append(Finding("R9_S5_NOT_CONSTRAINT", "stop"))
    if dec.s6_ends_imperative is None:
        j.append(Judgment("S6_IMPERATIVE_UNDECLARED"))
    elif dec.s6_ends_imperative:
        f.append(Finding("R9_S6_IMPERATIVE", "stop"))
    if dec.s6_contains_promise is None:
        j.append(Judgment("S6_PROMISE_UNDECLARED"))
    elif dec.s6_contains_promise:
        f.append(Finding("R9_S6_PROMISE", "stop"))
    return f, j


def validate_copy(copy: Dict[str, str], dec: Declared,
                  kappa_final: Sequence[Kappa] = ("実務性",),
                  stages: Sequence[str] = STAGES, n_seats: int = 2,
                  executors: Sequence[Tuple[str, Sequence[str]]] = (),
                  deadline: Optional[str] = None,
                  gamma_own: Optional[Dict[str, str]] = None,
                  chain: Sequence[Tuple[str, Sequence[Kappa], Sequence[str], str]] = (),
                  unwilling: Sequence[str] = ()) -> dict:
    uf, kept = check_unit_presence(copy, dec, stages)
    f = check_v0(copy) + uf
    f2, j = check_declared(dec, set(kappa_final), kept, stages, n_seats)
    f += f2
    f3, j3 = check_realize(dec, executors, unwilling); f += f3; j += j3
    f4, j4 = check_dates_v7(dec, deadline); f += f4; j += j4
    f5, j5 = check_insult(dec, gamma_own or {}); f += f5; j += j5
    f6, j6 = check_chain(dec, chain, kept); f += f6; j += j6
    f += check_seat_words(copy, dec, chain)      # A23 の紙側（申告だけで通さない）
    stop = [x for x in f if x.level == "stop"]
    return {"findings": f, "needs_judgment": j, "pass": not stop and not j}
