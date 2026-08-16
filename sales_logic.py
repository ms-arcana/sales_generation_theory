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
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

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
    busy_months: Tuple[int, ...] = ()          # A43：買い手の繁忙期（月の番号）。空＝未聞取り（⊥）


@dataclass
class Declared:
    """生成器（LLM）に宣言させる値。Python は推論しない。
    None は **未定義**（その段を書いていない等）であって 0 でも空文字でもない（A10）"""
    s2_unit: Optional[str] = None
    s2_from_unit: Optional[str] = None
    s3_form_mapping: Optional[str] = None        # A11：新語 ↔ κ_n 側の既存語
    s4_declares_repetition: Optional[bool] = None
    s4_period_months: Optional[int] = None
    s6_period_months: Optional[int] = None        # ⑥の課金・工数の周期。A26 以降 R10a では使わない
    # A26（第12.3版）：R10a が比べるべきは課金周期ではなく〈提案後に④の問題が残る周期〉である。
    # 第12.2版の再走行で、8体中6体が課金周期ではなくこちらで答えていた。機械だけが課金周期を見ていた。
    #   偽陰性：単発（課金 0）と申告すれば比較対象外になり、翌年問題が戻るかを一切検査しない
    #   偽陽性：毎年止め続けるサービスは課金が年額というだけで停止する
    # 仕組み・様式・型が買い手側に残って再発しないなら 0。
    s6_residual_period_months: Optional[int] = None
    s5_is_constraint_disclosure: Optional[bool] = None
    s6_ends_imperative: Optional[bool] = None
    s6_contains_promise: Optional[bool] = None
    s6_recasts_unit: Optional[bool] = None
    # A5：⑥に置いた量の基準。第12.5b版に**欄を割った** ―― 最終裁定点の κ_n は2つありうるのに
    # 欄が単数で、指示文が「価格・財源」と連結表示していた（型1・A24/A25/A25c と同じ形の4例目）。
    # 配列で申告させる。文字列も受ける（as-run の走行データが文字列だから）。
    s6_kappa: Optional[object] = None
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
    # A37（第13.5版）：`s6_start_date` は **二つの担体を持っていた** ――
    # 〈決定が締まる日〉と〈実際に動き出す日〉。生成器自身が両方の意味で書いている
    # （R2-P2 は「2026年9月28日に着手し」と書き、同じ枚で「2026年9月28日は決定の締切である」とも書いた）。
    # 買い手は二つを分けて読む ――「9月28日に決めても、動き出すのは2027年3月末だ」。
    # 一つの欄が二つのものを指す ＝ 型1 と同じ形。**欄を割る。**
    s6_decide_date: Optional[str] = None    # 決定が締まる日（④の着手期限と比べる）
    s6_start_date: Optional[str] = None     # 実際に動き出す日（決定日 ＋ LT 以降）           # A14：⑥が示す着手日（ISO）
    s6_self_check: Optional[bool] = None          # A14：⑤の根拠を自社案にも当てたか
    s5_denies_own: Optional[str] = None           # R17：⑤が否定している買い手の既承認（無ければ空文字）
    s6_kappa_by_seat: Optional[Dict[str, str]] = None   # A23：座席名 → その座席で読める量の基準
    # A27（第12.3版）：提示仕様は両立しない二つの要求を持っていた。
    #   必須要素の集合（⑥に10〜11個）は **導出**（Π と規則から blocks_on が出す）
    #   字数上限 200〜450字は **較正**（「そのままスライドに貼れる」という、観測されていない前提）
    # 優先順位が書かれていないので、生成器が毎回自分で決めていた。第12.2版の実測では
    # 8体中5体が「収まらない」と訴え、3体が「どちらを優先するかの規定がない」と名指しした。
    # 較正台帳の規律（導出表と較正表を分け、較正の側が譲る）に従い、**要素を優先し字数を破る**を規定する。
    # そのうえで、それでも落とした要素は隠さず出させる ―― 落とすこと自体が仕様違反だから。
    s6_omitted_blocks: Optional[Tuple[str, ...]] = None   # 書けなかった必須要素（ブロックのコード）
    # A28（第12.4版）：④の量には出所（q_source）と受領記録（q_receipt）を要求し、
    # 買い手データを名乗って記録が無ければ棄却する（R15）。ところが **⑥の量には出所欄が一つも無い**。
    # 金額が出てくるのは⑥のほうである。しかも A23 が「読む座席の数だけ量を置け」と要求し、
    # 売り手が実績を持つ座席は普通ひとつなので、**仕様が構造的に量の捏造を誘っていた**。
    #   「根拠のない量を置いてよいのか、置かずに座席要件を欠くべきか」（R2-P1・8体中5体が同じ訴え）
    # 第12.2版の走行では 7/8 が自発的に「実測」「見込み」「概算」を入れていた。機械は一つも読んでいない。
    #
    # 処置は A22（適用対象に出所を要求する）と同型。ただし**試算を禁じない**——
    # 売り手が実績を持たない座席は現実に存在する。禁じる代わりに、
    #   ・試算なら、試算と分かるように書かせる
    #   ・確定できないなら、**営業が埋める記入欄**にして、営業への申し送りに載せる
    # 機械は決められないものを needs_judgment へ回せるのに、**生成器にはその出口が無かった**。
    # 出口が無いから、作るか落とすかの二択になっていた。A28 は三つ目の出口を作る。
    s6_quantity_sources: Optional[Dict[str, str]] = None   # 座席名 → その座席へ置いた量の出所
    s6_to_sales: Optional[Tuple[str, ...]] = None          # 営業に算出・判断を仰ぐ項目
    # A45／A45b／A45c（第13.8版）：層(i) の算術。**売り手の数字だけで閉じる。**
    # 25業界21件で 20〜21/21 が挙げた三つで、買い手は現に検算して落としている。
    s6_price_low: Optional[str] = None            # 提示金額の下限
    s6_price_high: Optional[str] = None           # 提示金額の上限（単一なら下限と同値）
    s6_price_unit: Optional[str] = None           # 円／万円 など
    s6_price_items: Optional[Tuple[Dict[str, object], ...]] = None   # 内訳 ⟨name, amount, unit⟩
    s6_price_tiers: Optional[Tuple[Dict[str, object], ...]] = None   # 階層 ⟨label, qty, qty_unit, amount⟩
    # A47（第13.9版）：②の問いは、買い手の保有ではなく単位に向ける（25業界 8/21）
    s2_asks_possession: Optional[bool] = None
    # A46（第13.9版）：同じ断りは1回まで。二度言うと否定になる（25業界 7/21）
    s5_disclaimers: Optional[Tuple[str, ...]] = None   # 何について断ったか（対象。文言ではない）
    # N₄′（第13.5b版）：**量は〈単位〉だけでなく〈比較の相手〉を持つ。**
    # N₄ は「量は単位を持つ」としか言っていない。だから s6_kappa_by_seat は
    # 〈座席 → 基準〉の二つ組で足りているように見えた。ところが座席は基準を読むのではなく、
    # **払うものと戻るものを、同じ単位で並べて**決める。単位が違えば並べられない。
    # 第13版・第13.5版で買い手が繰り返し言ったのはこれである ――
    #   「出ていく額だけ決まっていて、戻る額が全部空欄だ」（R2-P2／社長）
    #   「時間の数字はうちの会議には載りません」（R1-P2／商品本部バイヤー）
    # s6_kappa_by_seat（座席→基準）を s6_quantities（座席→五つ組）へ広げる。
    #   ⟨基準, 払う, 戻る, 分母, 出所⟩
    # 旧欄は残す（旧走行との突合のため）。新欄があればそちらを正とする。
    s6_quantities: Optional[Tuple[Dict[str, object], ...]] = None
    # 形式（第13.4版）：⑥は散文である必要が無い。生成ゴールはスライドである。
    # 字数上限は**散文の部分にだけ**掛ける。表に入れた分は数えない。
    s6_table_rows: Optional[int] = None        # ⑥に置いた表の行数（表を使っていなければ 0）


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
# A25c（第12.1版）：`\b` は **日本語の隣で境界にならない**。Python の \w は日本語も含むので、
# 「御社のD5について」は \bD[1-7]\b に一致しない。設計語の記号は日本語の地の文に埋めて
# 書かれるのだから、この書き方では **一度も検査していなかった**（R9 の 0/36 の一部が空振り）。
# 実本文への漏洩は 24枚を緩い正規表現で走査しても 0件だったので、実害は出ていない。
# 境界は ASCII で取る。
V0_RE = [r"(?<!法)消去(?!法)", r"M_[0-9i]|Mᵢ",
         r"(?<![0-9A-Za-z])D[1-7][a-d]?(?![0-9A-Za-z])", r"T-[A-E]"]

# 第12.5b版：正規表現は生成器に見せられないので、人間語の言い換えを対にして持つ。
# 順序は V0_RE と一対一。
V0_RE_PLAIN = ["消去", "M_0・M_i のような記号", "D1〜D7 のような記号", "T-A〜T-E のような記号"]


def ban_words() -> List[str]:
    """生成器に渡す禁止語彙。**`V0` ∪ `V0_RE` から機械的に導く。**

    第12.5b版。ここは手書きの表が二つあった ―― 検査する `V0` と、指示文に載せる `BAN`。
    二つを人が別々に保つ限り必ず離れる。実際、**検査する語のうち4つが生成器に渡っていなかった**
    （`warrant`・`承認を積`・`資本として`・`消去対象`）。渡していない語で落とすのは、
    仕様のほうが不備である（A27・A28 と同じ形 ―― 機械が要求していることを生成器が知らない）。

    配管の刻みと同じ処置：**片方をもう片方から導く。**離れようがなくなる。
    """
    seen, out = set(), []
    for w in list(V0) + V0_RE_PLAIN:
        if w not in seen:
            seen.add(w); out.append(w)
    return out


# ══════════════════════════════════════════════════════════════════ 層1

def sigma_prod(n: Nu, uncal: bool = False) -> Tuple[Set[str], bool]:
    """商材側の Σ 縮退。**これは較正表である。**

    第12.5版：SPEC §12.2 は「S1・S2・S3 は削除した」と書いたが、削除されていなかった。
    参照はここ一箇所だけで、8セルでは一度も発火しないので、削除されたように見えていた。
    しかし 25業界へ広げれば発火する（低額×高頻度は対象外、低額×低頻度は ①④⑥ へ縮退）。

    削除できない理由は、SPEC §6 X1 が自認している ――
    「σ_prod の閾値（100万・四半期・年次）は **Γ^pre の存在を予測する経験的ヒューリスティック**」。
    根拠は無いが働いてはいる。だから**削除ではなく、較正表として台帳へ載せるのが正しい**。
    そして較正台帳の規律に従い、**未較正の業界では縮退させない**（知らない業界で機械が断定しない）。
    """
    if uncal:
        return set(STAGES), False
    if n.S3:
        return set(STAGES), False
    small = n.S1 in ("〜10万", "10〜100万")
    if small and n.S2 in ("四半期〜月次", "週次以上"):
        return {"①", "⑥"}, True
    if small and n.S2 in ("単発", "年次以下"):
        return {"①", "④", "⑥"}, False
    return set(STAGES), False


def trial_of(n: Nu) -> bool:
    """B_trial（試せる仕掛け）を、C_move ではなく ⟨ν, θ⟩ から出す。

    第12.5版：`C_move` は ν と同じ二重の真実だった。SPEC §12.2 は θ を「旧 C_move の一半」、
    σp を「もう一半」と書いたが、**合成規則を与えていない**——だから直せない、とされていた。

    ところが合成規則は要らなかった。**C_move が駆動しているブロックは2つだけで、
    その2つが、ちょうど半分ずつに対応している。** 合成された値を使う場所が無いのだから、
    合成規則も要らない。各ブロックを、それを実際に決めている座標へ繋ぎ直せばよい。

      試させるか  ← ν（経験財なら、試させないと分からない）∨ θ（そもそも試せるか）
      移行支援が要るか ← σp（乗り換えの手続コスト）∨ θ（段階を踏めないなら一度に移る）

    8セルすべてで現行の点灯を再現する。
    """
    if n.prod is None:
        return n.A == "使えば分かる" or n.C_move == "すぐ試せる"
    return nu_of(n) == "使えば分かる" or n.prod.theta in ("完全分割", "段階分割")


def migration_of(n: Nu) -> bool:
    """B_migration（段階導入と移行支援）を、C_move ではなく ⟨θ, σp⟩ から出す（→ trial_of）"""
    if n.prod is None:
        return n.C_move == "大仕事"
    return n.prod.sigma_p == "高" or n.prod.theta == "不可分"


def j_star(n: Nu) -> Seat:
    readers = [s for s in n.J if s.reads]
    return readers[-1] if readers else n.J[-1]


def kappa_n(n: Nu) -> frozenset:
    return n.J[-1].kappa if n.J else frozenset({"実務性"})


def form_n(n: Nu) -> frozenset:
    return n.J[-1].form if n.J else frozenset()


def talk_guide(n: Nu, S: List[str], uncal: bool = False) -> List[str]:
    """対面で飛ばしてよい段。読み手の状態で縮退した分（§6 の出力3）"""
    if uncal:
        return []
    reader = set(STAGES[START.get(n.E_reader, 0):])
    return [s for s in S if s not in reader]


def is_suffix(S: Sequence[str]) -> bool:
    """Σ が STAGES の接尾辞であること ＝ **Π₁ 第2式（cost 単調性）の実質**。

    第12.5版。文字どおりの第2式 `max_{φ∈Γ_s} cost(φ) ≤ max_{φ∈Γ_s'} cost(φ) (s<s')` は、
    **第1式（Γ が単調に積む）の系である** ―― Γ_s ⊆ Γ_s' なら上限は自動的に非減少。
    だから「検査対象を持たない」のは欠落ではなく、そう書いたことの帰結だった
    （第8版 §6「Π でも解消しない唯一の残件」は、存在しない対象を探していた）。

    第10版 §12.3 は `eliminable(M_i) ⟺ cost(M_i)>0 ∨ σ_p+τ ≥ 2` で「閉じた」と書いたが、
    **これは別の cost である。** Π₁ の cost(φ) は〈承認の値段〉、A19 の cost(M_i) は
    〈対抗手段が買い手に掛ける費用〉。同じ名前の二つの関数を取り違えていた。

    実質はここにある。段の順序は cost の順序そのもの（無料で始まり有料で終わる）。
    Σ から落ちる段は「資料の外で既に承認済み」（＝Γ^pre）という**断定**である。
    承認は cost の順に積むのだから、**高い段を承認済みにして安い段を残すことはできない。**
    ゆえに落ちる段は前置部、Σ は接尾辞。これは検査できる。
    """
    S = list(S)
    return S == list(STAGES[len(STAGES) - len(S):]) if S else False


def compute_sigma(n: Nu, uncal: bool = False) -> Tuple[List[str], str, bool, List[Judgment]]:
    """Σ の決定。**縮退に使う表は二つとも較正表である**（sigma_prod と START）。

    第12.5版で二つ直した。

    (1) 較正台帳の規律が Σ に掛かっていなかった。`apply_calibration(sigma_note=True)` は
        `SIGMA_UNCALIBRATED` を申し送るだけで、**Σ 自体は縮んだまま**だった。
        縮退は「その段は資料の外で既に成立している」という断定である。
        未較正の業界でそれを断定する根拠は無いので、縮退させない。
        安全な向きに倒れる（段が増えるだけ。A10 の停止も出なくなる）。

    (2) `sigma_prod` の {①,④,⑥} は **Π₁ 第2式に反する**（→ `is_suffix`）。
        ②③⑤ を承認済みとし、より安い ②③ を残らせている。
        〈導出 > 較正〉の規律により、**原理が勝ち、較正表が譲る** ―― 縮退を採らず申し送る。
        SPEC §6 X1 が「根拠なし」と自認していた表は、根拠が無いだけでなく原理と衝突していた。
    """
    j: List[Judgment] = []
    sp, oos = sigma_prod(n, uncal)
    cand = [s for s in STAGES if s in sp]
    if oos:                                  # 低関与＝そもそも生成しない。Σ は使われない
        return cand, "sigma_prod", True, j
    if sp != set(STAGES):
        if is_suffix(cand):
            return cand, "sigma_prod", False, j
        j.append(Judgment("PI1_SIGMA_NOT_SUFFIX", f"sigma_prod={''.join(cand)} を採らない"))
    if uncal:
        return list(STAGES), "sigma_full_uncalibrated", False, j
    S = set(STAGES[START.get(n.E_judge, 0):])
    return [s for s in STAGES if s in S], "sigma_read", False, j


def check_staircase(S: List[str]) -> List[Finding]:
    """Π₁ 第2式の実行時検査（→ `is_suffix`）。Σ を作る経路が増えたときの番人。

    いまの二経路（`sigma_read` は構成上つねに接尾辞／`sigma_prod` は上で拒否済み）では
    発火しない。**発火しないことが正しい状態**であり、これは経路が増えたときに鳴る。
    """
    return [] if is_suffix(S) else [Finding("PI1_STAIRCASE_BROKEN", "stop", "".join(S))]


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
#                       ／ sigma_prod（第12.5版に台帳へ追加。SPEC §12.2 は「削除した」と
#                          書いたが削除されておらず、参照が一箇所で8セルでは発火しないので
#                          消えたように見えていただけ。根拠の無い表は捨てるのではなく載せる）
#
# 第12.5版：**この台帳は Σ に掛かっていなかった。** `apply_calibration` は判定を降格するが、
# Σ の縮退（START と sigma_prod）は素通りしていた。縮退は「その段は資料の外で承認済み」
# という断定なので、未較正の業界ではしない（→ `compute_sigma(uncal=True)`）。
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
    # A45（第13.8版）：幅の比の閾値。**実測は二点しかない**（2.3倍で 20/21 が拒否／1.8倍は未検証）。
    # 内訳の欠落（A45b）と単価の逆行（A45c）は算術なので降格しない ―― 較正値を含まない。
    "A45_RANGE_TOO_WIDE": "PRICE_RATIO_MAX",
    # A46（第13.9版）：断りの回数の上限。実測は段あたり 0〜7 で、閾値3 は較正値。
    # **整合性チェックで登録漏れが出た**（本文で「較正」と書いたのに表に無かった）。
    "A46_DISCLAIMER_MANY": "DISCLAIM_MAX",
    "A2_C_NOT_SINGLETON": "ISO_KEYS",     # 所轄庁・系列は規制産業の語。非規制業界では常に空
}


def apply_calibration(findings: List[Finding], judgments: List[Judgment],
                      industry: Optional[str],
                      sigma_note: bool = True) -> Tuple[List[Finding], List[Judgment]]:
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
    if sigma_note:            # Σ の縮退は生成前の話。生成後検査から呼ぶときは付けない
        judgments = judgments + [Judgment("SIGMA_UNCALIBRATED", industry)]
    return out, judgments


def nu_of(n: Nu) -> str:
    """検証時点 ν。SPEC §12.2 は「ν は旧 A そのものである」と言っている（Nelson / Darby-Karni）。

    ところが第10版は `Product.nu` を足しただけで `Nu.A` を残し、照合をどこにも置かなかった。
    R1-P1・R2-P1 では現に食い違っており（A=使っても分からない／prod.nu=使えば分かる）、
    `blocks_on` が古い側を引くので「数字入りの導入事例」が落ち、
    「仕組みの開示」「認証・お墨付き」が立っていた。**座標があるほうを正とする。**
    """
    return n.prod.nu if n.prod else n.A


# 表引きの定義域。N2 は「⊥ は X のいかなる値とも比較できない」と言っているのに、
# 表引きだけが `.get(key, 既定値)` で **未定義を黙って値に変えていた**。
# START.get("比較検討中 ") は 0（＝Σ が①〜⑥に変わる）、
# ACQUIRE.get("買い手のデータ") は 0（＝実効LTが縮み R6b が緩む）。誤字が判定を変える。
AXIS_DOMAIN: Dict[str, Set[str]] = {
    "E_judge": set(START), "E_reader": set(START),
    "q_source": set(ACQUIRE_CALIBRATED),
    "nu": {"買う前に分かる", "使えば分かる", "使っても分からない"},
    "theta": {"不可分", "段階分割", "完全分割"},
    "sigma_p": {"低", "中", "高"},
    "alpha": {"低", "高"},
    "beta1_hard": {"固定", "変動"},
    "beta1_cap": {"資産計上", "費用処理"},
    "origin": {"制度", "組織", "個人"},
    "mtype": set(ALLOWED),
    "form": set(M0_KILL),
    "src": {"法令", "公的暦", "自然・需要", "契約", "売り手都合"},
}

# A51（第13.10版）：**入力に ⊥ を書く場所が無かった。**
# `Product` は全成分に既定値を持つので、**聞き取っていない欄が黙って特定の値になる**
# （`nu="使えば分かる"`・`theta="段階分割"`…）。型2 そのもの ―― 未定義を既定値と読む。
# 全部の定義域に「不明」を足し、**⊥ を明示できるようにする**。値としては使わせない
# （`check_axis_values` が要判断へ回す）。
BOTTOM_TOKEN = "不明"      # A51：入力に ⊥ を書く場所。既定値と未聞取りを区別する
AXIS_DOMAIN = {k: (v | {BOTTOM_TOKEN}) for k, v in AXIS_DOMAIN.items()}


def check_axis_values(n: Nu) -> List[Judgment]:
    """入力 ν の列挙値が、表の定義域に入っているか（N2 を表引きへ適用する）。

    値が定義域の外なら、既定値へ黙って落ちる前に申し送る。
    加えて、`Nu.A` と `prod.nu` の二重の真実もここで捕まえる。
    """
    j: List[Judgment] = []

    def chk(axis: str, val, where: str):
        if val is None:
            # A51（第13.10版）：**None も ⊥ である。**黙って通してはいけない。
            j.append(Judgment("A51_AXIS_UNDECLARED", where))
            return
        if val == BOTTOM_TOKEN:
            # ⊥ を明示できるようになった。値としては使わせず、人へ回す
            j.append(Judgment("A51_AXIS_BOTTOM", where))
            return
        if val not in AXIS_DOMAIN[axis]:
            j.append(Judgment("AXIS_VALUE_UNKNOWN", f"{where}={val!r}"))

    chk("E_judge", n.E_judge, "E_judge"); chk("E_reader", n.E_reader, "E_reader")
    for t in n.tau:
        chk("q_source", t.q_source, f"{t.form}:{t.d} q_source")
        chk("form", t.form, f"τ.form"); chk("src", t.src, f"{t.form}:{t.d} src")
    for s in n.J:
        chk("origin", s.origin, f"座席 {s.name} origin")
    for m in n.M:
        chk("mtype", m.mtype, f"手段 {m.name} mtype")
    p = n.prod
    if p:
        chk("nu", p.nu, "prod.nu"); chk("theta", p.theta, "prod.theta")
        chk("sigma_p", p.sigma_p, "prod.sigma_p")
        chk("alpha", p.alpha_m, "prod.alpha_m"); chk("alpha", p.alpha_c, "prod.alpha_c")
        chk("beta1_hard", p.beta1_hard, "prod.beta1_hard")
        chk("beta1_cap", p.beta1_cap, "prod.beta1_cap")
        if p.nu != n.A:
            j.append(Judgment("NU_AXIS_CONFLICT", f"Nu.A={n.A!r} prod.nu={p.nu!r}"))
        # 第12.5版：C_move も ν と同じ二重の真実。合成規則は要らなかった（→ trial_of）が、
        # 古い側が黙って捨てられるのは ν のときと同じ形なので、同じように申し送る。
        old_t = (n.A == "使えば分かる" or n.C_move == "すぐ試せる")
        old_m = (n.C_move == "大仕事")
        if old_t != trial_of(n) or old_m != migration_of(n):
            j.append(Judgment("C_MOVE_AXIS_CONFLICT",
                              f"C_move={n.C_move!r} θ={p.theta!r} σp={p.sigma_p!r} "
                              f"試用 {old_t}->{trial_of(n)} 移行 {old_m}->{migration_of(n)}"))
    return j


def audit_axis_types() -> List[Judgment]:
    """A48（第13.10版）：**「軸」は二種類の対象を指していた。**

    ν・τ・J・Σ は記法が型を与えている（N₂・N₃・N₅・N₁）ので、型検査が効く。
    ところが **λ・ε と商材座標の7成分は、記法を通らない** ―― Π₃ と既存研究が
    値域そのものを列挙している。**この群には型検査が無く、`check_axis_values` の
    列挙照合だけ**である。新しい λ を足したくなったとき、それが本当に所在なのかを機械は言えない。

    ここで棚卸しして、**人の承認が要る箇所として明示する**（`audit_requirements` と同じ位置づけ）。
    """
    untyped = {
        "λ 所在": "Π₃ が8値を列挙", "ε 様式": "Π₃ が2値を列挙",
        "ν 検証時点": "Nelson / Darby-Karni", "θ 分割試用": "Rogers",
        "σp 切替コスト": "Burnham ら", "ω 発現ラグ": "MMM の carryover",
        "α 帰属可能性": "Selviaridis", "β₁ 会計分類": "会計基準 / cost stickiness",
        "β₂ 予算内外": "稟議の実証",
    }
    return [Judgment("A48_AXIS_NO_TYPE_CHECK", f"{k}（{v}）") for k, v in sorted(untyped.items())]


def buyer_quantities(n: Nu) -> List[Tuple[str, str]]:
    """A52：**入力に在る〈買い手の量〉。**⑥の〈戻る〉の式が掛ける相手はここから採る。

    第13.6版以降、⑥の量の〈戻る〉は 17行中13行が記入欄だった。A44（21/21）。
    第13.8版で〈式〉の出口を作ったが、**式が掛ける相手が入力に在るとは限らない** ――
    第13.7版の走行では、3座席のうち1つ（理事会の「予算科目『広報外注費』の年間執行額」）が
    **入力のどこにも無い量**だった。生成器が発明している。

    在るのは τ の量である（`q` / `q_low`〜`q_high` / `q_source`）。
    **決定表と指示文に出していなかったから、生成器は発明するしかなかった。**
    """
    out = []
    for t in n.tau:
        if t.q:
            rng = (f"{t.q_low}〜{t.q_high}" if t.q_low is not None else "")
            out.append((str(t.q), f"{rng}／出所 {t.q_source or '⊥'}"))
    return out


def check_basis_in_input(dec: Declared, basis_names: Sequence[str]) -> List[Judgment]:
    """A52 の紙側：⑥の式が掛ける相手が、入力に在る買い手の量と照合できるか。

    機械は真偽を見られない（A22）ので**要判断**。照合は部分一致ではなく、
    入力側の量の名前が式の担体に**含まれるか**で見る（名前は長いので完全一致は取れない）。
    """
    out = []
    for q in (dec.s6_quantities or ()):
        b = q.get("ret_basis")
        if is_bottom(b):
            continue
        bs = str(b)
        if not any(nm and (nm in bs or bs in nm) for nm in basis_names):
            out.append(Judgment("A52_BASIS_NOT_IN_INPUT",
                                f"{_q_seat(q)}：{bs[:40]} は入力の量に無い"))
    return out


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
    A = nu_of(n)                       # 第12.1版：商材座標があるならそちらが正（SPEC §12.2）
    cand = [
        ("B_visualize", E == "困っていない", "①"),
        ("B_what_is_it", E in ("困っていない", "手段を知らない"), "③"),
        ("B_form_mapping", len(n.J) >= 2, "③"),                     # A11
        ("B_compare_current", E in ("比較検討中", "うちも知っている"), "⑤"),
        ("B_spec_table", A == "買う前に分かる", "⑤"),
        ("B_case_numbers", A == "使えば分かる", "⑤"),
        ("B_precedent", "D4" in dims, "⑤"),
        ("B_mechanism", A == "使っても分からない", "⑤"),
        ("B_certification", A == "使っても分からない", "⑤"),
        ("B_trial", trial_of(n), "⑥"),                              # 第12.5版：C_move → ⟨ν,θ⟩
        ("B_migration", migration_of(n), "⑥"),                      # 第12.5版：C_move → ⟨θ,σp⟩
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


def iso_date(s: Optional[str]) -> Optional[date]:
    """ISO の日付として読めるなら date、読めなければ None（＝比較の定義域に入れない）"""
    if not s or not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s.strip())
    except ValueError:
        return None


def sub_months(d: date, m: int) -> date:
    y, mo = d.year, d.month - m
    while mo <= 0:
        mo += 12; y -= 1
    return date(y, mo, min(d.day, 28))


def add_months(d: date, m: int) -> date:
    y, mo = d.year, d.month + m
    while mo > 12:
        mo -= 12; y += 1
    return date(y, mo, min(d.day, 28))


def decision_gates(n: Nu, today: date) -> List[TauItem]:
    """A41（第13.5b版）：**④から落とした日付が、⑥の決定日をまだ縛る。**

    A8 は「〈今やる理由〉の日付は、買い手より**上位**の当事者が握っていなければならない」
    と言う。学内の入試委員会・購買委員会のような**買い手の内側**の座席が握る日は落ちる。
    規則としては正しい。内側の委員会は外からの圧力を作らないからである。

    ところが `persona12.py` は買い手に**生の τ をそのまま**渡すので、買い手はその日を知っている。
    第13.5版で E1 の 4/4 が、この日を**決定的な**棄却理由に挙げた。

      「学内の入試委員会が握る年1回の 2027-05-31 を18日過ぎて逃す
        （**この日は資料に一言も出てこない**）」 ―― E1-P2／入試広報課長

    **④から落とすことと、⑥で無視してよいことは別である。**
    落とした日付は「なぜ今か」には使えないが、「いつなら決められるか」は依然として縛る。
    A37・A37b と同じ形（一つの担体に二つの役）の三例目。

    決定の窓とみなす条件：拘束者が居り、その誰もが上位に居らず、かつ決定が締まる日であること。
    拘束者が空（＝誰も握っていない）ものは窓ではない。
    """
    out = []
    for t in n.tau:
        if t.d is None or t.d <= today:
            continue
        if not t.binders or any(b in n.upstream for b in t.binders):
            continue
        if t.decision is False:          # 結果が現れる日であって決定の日ではない（A18）
            continue
        out.append(t)
    return sorted(out, key=lambda t: t.d)


def check_gates(dec: Declared, gates: Sequence[Tuple[str, str, int]],
                s4_text: str = "") -> Tuple[List[Finding], List[Judgment]]:
    """A41：決定日が、買い手の内側の窓を越えていないか。④に持ち出していないか。

    gates … (日付, 拘束者, 逃したときの待ち月数) の列。compile_deal が並べる。
    """
    f, j = [], []
    if not gates:
        return f, j
    # A55（第14.3版）：**⊥ を別の欄で代用しない。**ここは以前
    # `dcd = dec.s6_decide_date or dec.s6_start_date` と書いてあった ――
    # 決定日が ⊥ のとき着手日を読み替える形で、**一つの記号が二つの担体を指す**（型5）。
    # 窓を越えたかは〈決定日〉についての述語であって、着手日はその代理にならない。
    # 決定日が ⊥ なら比べない（N₂）。受け皿は A41_GATE_UNCHECKED。
    d0 = None if is_bottom(dec.s6_decide_date) else iso_date(dec.s6_decide_date)
    first = min(iso_date(g[0]) for g in gates if iso_date(g[0]))
    if d0 is None:
        j.append(Judgment("A41_GATE_UNCHECKED", f"窓{first} 決定日の申告なし"))
    elif d0 > first:
        f.append(Finding("A41_DECIDE_AFTER_GATE", "stop", f"決定{d0} > 窓{first}"))
    # A41b（第13.7版）：**窓は決定日だけでなく着手日も縛る。**
    # 第13.6版で E1 の買い手が言った ――
    #   「着手 2027-03-01 が、根拠に置いた一巡の締め 2027-05-31 より前に来ていて順序が逆」
    # 委員会が開かれる前に動き出すことはできない。決定は窓を通って初めて締まるのだから、
    # 着手はその窓以降である。`着手 ≥ 決定＋LT` と両立するかは走行前に総当たりで確かめる
    # （`feasible136.py`。着手には上限が無いので、両方の下限の max を取れば必ず解が在る）。
    d1 = iso_date(dec.s6_start_date) if dec.s6_start_date else None
    if d1 and d1 < first:
        f.append(Finding("A41B_START_BEFORE_GATE", "stop", f"着手{d1} < 窓{first}"))
    # ④に出してはならない（〈今やる理由〉の担体ではない）。出ていれば A8 の趣旨を破る
    for gd, gb, _w in gates:
        if s4_text and (gd in s4_text or (gb and gb in s4_text)):
            f.append(Finding("A41_GATE_IN_S4", "stop", f"{gd}/{gb}"))
    return f, j


# A41b：④に出てよい日付を、日付の文字列そのもので数える。
# 第13.6版 §4-3 の教訓 ―― 版をまたいで比べるなら、**語彙に依存しない物差し**を使う。
S4_DATE_RE = re.compile(r"(20\d{2})\s*[-/年]\s*(\d{1,2})\s*[-/月]\s*(\d{1,2})\s*日?")


def dates_in(text: str) -> List[str]:
    """本文に現れる〈日まで特定した日付〉を ISO へ正規化して返す（年月だけの記述は取らない）"""
    return sorted({f"{y}-{int(m):02d}-{int(d):02d}" for y, m, d in S4_DATE_RE.findall(text or "")})


def check_s4_dates(copy: Dict[str, str],
                   tau_ok_dates: Sequence[str],
                   decide_deadline_tau: Optional[str]
                   ) -> Tuple[List[Finding], List[Judgment]]:
    """A41b：**④に出てよい日付は〈使える日付〉と〈逆算由来の決定期限〉だけ。**

    第13.6版の「三か月ずれている」は、生成器が④で**機械の知らない日付**を作ったから起きた。
    ⑤⑥には機械が知らない日付が正当に出る（決定日・着手日・実現日・段階導入の時期）ので、
    **本文全体に当てると 8/8 が誤検出になる**。④だけに限ると第13版 as-run で 0/8 だった
    （検分済み。回帰に固定してある）。

    窓由来の決定期限をここに渡してはならない ―― 窓は買い手の内側なので④に出せない（A41）。
    したがって呼び手は `decide_deadline` ではなく `decide_deadline_tau` を渡す。
    """
    f, j = [], []
    s4 = copy.get("④") if copy else None
    if not s4:
        return f, j
    if not tau_ok_dates:
        # 許可集合そのものが ⊥。N₂ ―― ⊥ はいかなる値とも比較できない。
        # ここを空集合として比べると「全部が外来」になる（浅い一致の6件目になるところだった）。
        if dates_in(s4):
            j.append(Judgment("A41B_S4_DATES_UNCHECKED", "使える日付が渡っていない"))
        return f, j
    allowed = set(tau_ok_dates) | ({decide_deadline_tau} if decide_deadline_tau else set())
    extra = [d for d in dates_in(s4) if d not in allowed]
    for d in extra:
        f.append(Finding("A41B_S4_FOREIGN_DATE", "stop", f"④{d} は機械が知らない日付"))
    return f, j


def audit_tau_forms(n: Nu) -> List[Judgment]:
    """A42（第13.5b版）：**D（γ＝斜・逓増）と置いた項が、実は〈段・再来〉ではないか。**

    D は境界が無い（費用がなだらかに増えるだけ）。だから単独では「なぜ今か」を作れず、
    `TD_ALONE` で落ちる。規則としては正しい。

    ところが第13.5版で、R の 2027-04-01（D 形）を買い手 4/4 が**年1回の硬い窓**として扱った。

      「5月28日という締切は、私が以前から知っている **4月1日の窓を一年分越えている**」

    春の定番改訂は逓増ではない。落としたら次は一年後である。
    境界が無いはずのものに〈決定が締まる日〉や〈逃したときの待ち月数〉が付いていたら、
    それは γ＝斜ではなく〈段・再来〉＝ B/C である。**入力側の型ずれ。**
    機械は真偽を見られないので（A22）、停止ではなく要判断で出す。
    """
    out = []
    for t in n.tau:
        if t.form != "D":
            continue
        ref = f"D:{t.d}"
        if t.decision:
            out.append(Judgment("A42_D_WITH_DECISION", ref))
        if t.wait_months is not None:
            out.append(Judgment("A42_D_WITH_WAIT", f"{ref} 待ち{t.wait_months}m"))
        if t.windows and t.windows > 1:
            out.append(Judgment("A42_D_WITH_WINDOWS", f"{ref} x{t.windows}"))
    return out


def start_deadline(ok: List[TauItem], lt: int) -> Optional[date]:
    """④が示す**決定期限日**。A/C の終端日から実効リードタイムを引いた最小値。

    A37b（第13.5版）：**この量はずっと「着手期限」と呼ばれていたが、算術は決定期限である。**
    `effective_LT = LT_months + acquire`。`acquire` は「着手してから1周期分のデータが
    たまるまで」だから、`LT_months` を〈着手→境界〉と読むと同じ区間を二度数える。
    〈決定→着手〉と読んだときだけ、二つは連続した区間として足せる。
    したがって `d − effective_LT` は〈決定が締まっていなければならない日〉である。
    関数名と鍵名（`start_deadline`）は旧走行との突合のために残す。**表示名は決定期限。**
    """
    ds = [sub_months(t.d, lt) for t in ok if t.form in ("A", "C") and t.d]
    return min(ds) if ds else None


def effective_decide_deadline(tau_deadline: Optional[date],
                              gates: Sequence[Tuple[str, str, Optional[int]]]
                              ) -> Optional[date]:
    """A41b（第13.7版）：**同じ資料に、決定期限が二つ出てはならない。**

    第13.6版で買い手が言った ――

      「⑥の決定 2026-09-30 と、**④の逆算 2026-12-30 が三か月ずれている**」 ―― E1-P1

    調べたら、**どちらの日付も機械は知らなかった**。E1 は `tau_ok` に A/C 型が無いので
    `start_deadline` が ⊥ になり、**決定期限が一つも指示文へ渡っていなかった**。
    生成器は仕方なく自分で 2026-12-30 を作り、⑥では別の日を書いた。
    **欠落が二つの期限を生んだ**のであって、生成器が勝手をしたのではない。

    実効の決定期限は、④からの逆算と〈決定の窓〉の**早いほう**である。
    片方が ⊥ ならもう一方。両方 ⊥ なら ⊥（N₂：⊥ は値ではない。既定値に落とさない）。

    **④に書いてよいのは逆算由来のものだけ**である（窓は買い手の内側なので A41）。
    そのため呼び手は二つを別の鍵で持つ ―― `decide_deadline`（実効・⑥用）と
    `decide_deadline_tau`（逆算のみ・④用）。
    """
    cands = [x for x in [tau_deadline] if x]
    cands += [d for d in (iso_date(g[0]) for g in gates) if d]
    return min(cands) if cands else None


def earliest_realize(today: date, lt: int, omega: int,
                     busy: Sequence[int] = (), gate: Optional[date] = None) -> date:
    """今日から数えて、**最も早くても費目が減るのはいつか**。

    決定は今日でもよい／着手は決定＋LT かつ〈決定の窓〉以降／実現は着手＋ω かつ繁忙期を避ける。
    A50 で「④の境界日に間に合うか」を見るための下限である。
    """
    s = add_months(today, lt)
    if gate and s < gate:
        s = gate
    r = add_months(s, omega or 0)
    for _ in range(24):
        if r.month not in set(busy or ()):
            break
        r = add_months(r, 1)
    return r


def check_bound_reachable(n: Nu, ok: List[TauItem], today: date,
                          gates: Sequence[TauItem] = ()) -> List[Judgment]:
    """A50（第13.10版）：**④で「なぜ今か」に据えた日に、提案は間に合っているか。**

    第13.9版の逆方向 oracle で、A/B 両版・2/2 座席が decisive に挙げた唯一の項目 ――

      「④で急ぐ理由に据えた 2027-06-30 の三か月後に着手 2027-09-01 が置かれており、
        **提案自身がその日に間に合っていない**」 ―― 学部長会
      「④が言う〈様式と定義が固まらないまま受審の年に入る〉という損失を、
        本提案の日程が**そのまま起こす**」

    `start_deadline` は τ の **A/C 形からしか逆算しない**。E1 の境界日は `Ec`（解禁日）なので、
    **何も縛っていなかった。**A41b は〈窓〉を締めたが、境界日と⑥の日程の関係は空いていた。

    **停止にはしない。**8セルに当てると **4/8 が充足不能**になる ―― 売り手のリードタイムと
    買い手の窓では、その期日に物理的に間に合わない。機械は「間に合わなくてもその日を
    根拠に使ってよいか」を決められない（A22 と同型：機械は照合しかできない）。
    落とさず**申し送り、指示文に明記させる**。
    """
    out = []
    lo = min((t.d for t in gates if t.d), default=None)
    e = earliest_realize(today, effective_LT(n), (n.prod.omega if n.prod else 0),
                         n.busy_months, lo)
    for t in ok:
        if t.d and e > t.d:
            out.append(Judgment("A50_BOUND_UNREACHABLE",
                                f"{t.d}（{t.form}）に最速の実現 {e} が間に合わない"))
    return out


def check_realize_bound(dec: Declared, tau_ok_dates: Sequence[str]) -> List[Judgment]:
    """A50 の紙側 ―― ⑥の実現日が、④の境界日を越えていないか（申告だけで通さない）"""
    out = []
    if not tau_ok_dates or not dec.s6_realize:
        return out
    b = min(d for d in (iso_date(x) for x in tau_ok_dates) if d)
    for tri in dec.s6_realize:
        d = iso_date(tri[1]) if len(tri) > 1 else None
        if d and d > b:
            out.append(Judgment("A50_REALIZE_AFTER_BOUND", f"実現{d} > ④の境界{b}"))
    return out


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

    第12.1版：照合は **正規化してから** 行い、**全部落ちたことは黙らせない**。
    構造キーの値は「本部が販促費と人時を分けて持つ」のような自由文である。それを完全一致で
    比べているので、句読点1つ・空白1つで事例が消え、$D_{7a}$ が立たなくなる。
    第10版の「16/16 → 0/8」が成立しているのは、`cells8_v10.py` が買い手側と事例側を
    **同じファイルで同じ文字列に書いた**からであって、営業が入力すれば一致しない。
    表記ゆれは正規化で吸収し、それでも全滅したときは申し送る（型2：照合できないことを「無い」と読まない）。
    """
    keep, j = [], []
    keys = ISO_KEYS if any(n.buyer_context.get(k) for k in ISO_KEYS) else ISO_KEYS_CALIBRATED
    missing = [k for k in keys if not n.buyer_context.get(k)]
    if missing and seller.named_cases:
        j.append(Judgment("ISO_CONTEXT_MISSING", ",".join(missing)))
    dropped = []
    for c in seller.named_cases:
        if not c.get("実名"):
            continue
        bad = [k for k in keys if n.buyer_context.get(k)
               and iso_norm(c.get(k)) != iso_norm(n.buyer_context.get(k))]
        if bad:
            dropped.append(f"{c['実名']}:{','.join(bad)}")
            continue
        keep.append(c)
    if not keep and dropped:
        j.append(Judgment("ISO_ALL_CASES_DROPPED", " / ".join(dropped)))
    return keep, j


def iso_norm(s: Optional[str]) -> str:
    """構造キーの値の表記ゆれを落とす。空白・句読点・全半角のみ（意味判定はしない）"""
    if not s:
        return ""
    import unicodedata
    t = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s。、,.，．・]+", "", t)


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
    uncal = not (industry is None or industry in CALIBRATED_ON)
    S, by, oos, sj = compute_sigma(n, uncal)  # 第12.5版：Σ の縮退も較正台帳と Π₁ に従わせる
    if oos:
        return {"generate": False, "out_of_scope": True, "sigma": S, "sigma_by": by,
                "findings": [Finding("OUT_OF_SCOPE_LOW_INVOLVEMENT", "stop")],
                "needs_judgment": [], "llm_calls": 0}
    wf, wj = check_W(n)
    pre = check_gamma_pre(n, S) + wf + check_seats(n) + check_staircase(S)
    tau_ok, tf, tj = check_tau(n, today, uncal)
    live, df = check_delta(n)
    cf, d7 = check_C_singleton(n, seller)
    r7 = check_R7(live, seller) + check_R4(n, live, seller)
    _, ij = iso_cases(n, seller)
    findings = pre + tf + df + [cf] + r7 + check_cost(n, live) + check_D5_binder(n, live)
    judgments = (tj + ij + wj + sj + check_axis_values(n)   # 第12.1版：表引きの定義域と ν の二重の真実
                 + audit_tau_forms(n))                     # A42：D と置いた項の型ずれ
    findings, judgments = apply_calibration(findings, judgments, industry)
    stop = [x for x in findings if x.level == "stop"]
    # A41b：逆算由来（④へ渡してよい）と実効値（⑥を縛る）を分けて持つ
    _gates = [(t.d.isoformat(), "／".join(t.binders), t.wait_months)
              for t in decision_gates(n, today)]
    _dl_tau = start_deadline(tau_ok, effective_LT(n))
    _dl_eff = effective_decide_deadline(_dl_tau, _gates)
    # A50（第13.10版）：④の境界日に、提案が物理的に間に合うか
    judgments = judgments + check_bound_reachable(n, tau_ok, today, decision_gates(n, today))
    _bq = buyer_quantities(n)      # A52：⑥の式が掛ける相手に使える〈買い手の量〉
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
        # A37b：鍵名は旧走行との突合のために据え置く。担体は〈決定期限〉であって着手期限ではない。
        "start_deadline": (_dl_tau.isoformat() if _dl_tau else None),
        # A41b（第13.7版）：⑥に渡す実効の決定期限＝ min(逆算, 決定の窓)。
        # ④へ渡してよいのは逆算由来のほうだけなので、二つの鍵に分ける。
        "decide_deadline": (_dl_eff.isoformat() if _dl_eff else None),
        "decide_deadline_tau": (_dl_tau.isoformat() if _dl_tau else None),
        "lt_months": n.LT_months,          # A37：⑥の日付に掛ける（買い手が決めてから動くまで）
        "today": today.isoformat(),
        # A41：④から落とした〈買い手の内側の窓〉。④には出さず、⑥の決定日を縛る
        "decision_gates": _gates,
        "buyer_quantities": _bq,          # A52：⑥の〈戻る〉の式が掛ける相手
        "omega": n.prod.omega if n.prod else None,        # A43：効果発現ラグ（導出）
        "busy_months": list(n.busy_months),               # A43：買い手の繁忙期（入力・空＝⊥）
        "talk_guide": talk_guide(n, S, uncal),
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
                       stages: Sequence[str] = STAGES
                       ) -> Tuple[List[Finding], bool, List[Judgment]]:
    """②で導入した単位が⑥に出現するか。A6：出現していれば『併記』であって置換ではない。
    ②が Σ にないときは s2_unit は未定義であって、検査対象ではない（A10）

    A25（第12版）：**照合は正規化した単位語で行う。**
    N4 は Qty = ⟨数, 単位, 基準⟩ と定めているが、宣言欄は文字列なので、生成器は
    「作業時間（時間）」のように単位に説明句を付けて申告してくる。第12版の走行では
    R10b_UNIT_ABSENT 15件のうち **14件が、本文に単位が在るのに完全一致で外した誤検出**
    だった。宣言の型が緩いなら、照合の側が正規化する（A24 と同じ型の混同）。

    A25b（第12.1版）：A25 の正規化はまだ浅かった。
    ・宣言が**文**になると照合語が取れない。E2-P2 は「担任1人あたりが年間に募集へ充てる
      日数（担任工数の日数）」と申告し、⑥に「担任工数」も「日数」も在るのに外していた。
      → 助詞「の」でも区切る。
    ・候補が**空集合**になる場合（単位語が1文字：件・人・日・円…）、現行は必ず停止する。
      日本語の単位は1文字が普通なので、25業界へ広げれば確実に踏む。
      照合できないことは「無い」ことではない。N2 に従い、停止でも通過でもなく**要判断**へ。
    ・⑥が Σ に無ければ、そもそも照合対象がない（A10 の未定義）。
    ・R10b_UNIT_REPLACED は同じ一つの事実の二度目の呼び名だった（ABSENT と必ず同時に立つ）。
      停止は ABSENT 一本に寄せ、REPLACED は註記（info）へ落とす。
    """
    if "②" not in stages or "⑥" not in stages or not dec.s2_unit:
        return [], True, []
    cand = unit_tokens(dec.s2_unit)
    if not cand:
        return [], True, [Judgment("R10b_UNIT_UNCHECKABLE", dec.s2_unit)]
    kept = any(c in copy.get("⑥", "") for c in cand)
    if kept:
        return [], True, []
    f = [Finding("R10b_UNIT_ABSENT", "stop", dec.s2_unit)]
    if dec.s6_recasts_unit:
        f.append(Finding("R10b_UNIT_REPLACED", "info", f"{dec.s2_from_unit}->{dec.s2_unit}"))
    return f, False, []


def unit_tokens(u: str) -> Set[str]:
    """宣言された単位文字列から、照合に使える単位語の候補を取り出す（A25 / A25b）。

    「作業時間（時間）」→ {作業時間（時間）, 作業時間, 時間}
    「時間（売場に張り付くパート人時）」→ {…, 時間, 売場に張り付くパート人時}
    「担任1人あたりが年間に募集へ充てる日数（担任工数の日数）」→ {…, 担任工数, 日数}
    1文字の候補は落とす（「日」「件」単独では地の文に埋もれて照合にならない）。
    **全部落ちて空集合になったら、それは「単位が無い」ではなく「照合できない」である**
    ―― 判定は呼び側が要判断へ回す。
    """
    out = {u.strip()}
    m = re.match(r"^(.*?)[（(](.*?)[)）]\s*$", u.strip())
    if m:
        out |= {m.group(1).strip(), m.group(2).strip()}
    for part in re.split(r"[（()）／・、,/]", u):
        if part.strip():
            out.add(part.strip())
    for part in list(out):                    # A25b：助詞「の」でも区切る
        if "の" in part:
            out |= {x.strip() for x in part.split("の") if x.strip()}
    return {c for c in out if len(c) >= 2}


def kappa_tokens(k) -> Set[Kappa]:
    """宣言された基準（κ）の文字列から、照合に使える基準語を取り出す。

    A24（費目の連結）・A25（単位の説明句）と**まったく同じ型の第3例**である。
    κ_n が2つある座席（理事長＝価格・財源、社長＝価格・財源）では、指示文が
    「価格・財源」という連結形で4回書いているのに、申告欄は単数の文字列だった。
    生成器は指示の見せ方をそのまま写して `s6_kappa="価格・財源"` と申告し、
    機械は「そんな基準は無い」と読んで A16 を出していた（第12版 arm0 の A16 2件の正体）。

    宣言の型が緩いなら、照合の側が正規化する。既知の基準名に割れなければ元の文字列を返す
    （割れない＝本当に未知の基準なので、従来どおり EXPR_TABLE_MISS へ落ちる）。

    第12.5b版：**欄を割った**（`s6_kappa` は配列で申告させる）ので、ここは配列も受ける。
    照合側の正規化は残す ―― 直したのは指示の側で、古い走行データは文字列のままだから。
    """
    if not k:
        return set()
    parts = [k] if isinstance(k, str) else [str(x) for x in k if str(x).strip()]
    ks: Set[str] = set()
    for p in parts:
        ks |= {x.strip() for x in re.split(r"[・、,／/＋+]|と", p) if x.strip()}
    known = {x for x in ks if x in RK}
    return known if known else {p.strip() for p in parts}


def kappa_merged(k) -> bool:
    """申告の**一要素の中に**既知の基準が2つ以上入っているか（＝連結して書いた）。

    欄を配列にしたので、`["価格", "財源"]` は正常、`["価格・財源"]` と `"価格・財源"` が連結である。
    """
    if not k:
        return False
    parts = [k] if isinstance(k, str) else [str(x) for x in k]
    for p in parts:
        toks = {x.strip() for x in re.split(r"[・、,／/＋+]|と", p) if x.strip()}
        if len({x for x in toks if x in RK}) > 1:
            return True
    return False


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

    **A57（第14.4版）――ここは旧欄 `s6_kappa_by_seat` を生で読んでいた。**
    第13.7版に `wf_gen137.js` のスキーマを縮めたとき、その欄を落としている。
    隣の `check_chain`・`check_quantity_sources` は橋 `quantities_by_seat()` を通っていたが、
    **この関数だけ移し忘れていた。**結果、gen137 の走行物13件すべてで欄が不在になり、
    `A23_SEAT_WORD_ABSENT` が**構造的に出なくなっていた**（同じ紙で 旧スキーマ→1件／新スキーマ→0件）。
    第14.2版に直した A49（A28 の橋が旧 `source` しか読んでいなかった）と同型で、隣の関数の取りこぼし。
    """
    f: List[Finding] = []
    by_seat = quantities_by_seat(dec)          # A57：橋を通す（新旧どちらの形でも立つ）
    if not chain or not by_seat:
        return f
    body = copy.get("⑥", "")
    for name, _kappa, form, _origin in chain:
        if name not in by_seat or not form:
            continue
        if not any(w and w in body for w in form):
            f.append(Finding("A23_SEAT_WORD_ABSENT", "stop", f"{name}:{'/'.join(form)}"))
    return f


Q_SRC = ("買い手データ", "公開統計", "売り手の実績", "試算", "営業記入")
Q_SRC_GROUNDED = ("買い手データ", "公開統計", "売り手の実績")
# 「試算である」と読める語／営業が埋める記入欄の印。A25 の教訓に従い、
# 候補を並べて **どれか一つでも在れば通す**（完全一致では照合にならない）。
EST_MARKS = ("試算", "見込み", "概算", "推定", "想定", "仮に", "と置くと")
# A34（第12.8版）：記入欄の照合が **「括弧の中は空白だけ」** を仮定していた。
# 生成器はラベルを括弧の**中**に入れる ―― 【　　　ポイント】【パート平均時給：　　　】。
# R1-P1K は記入欄を9つ置いていたのに一つも当たらず、A28_SLOT_ABSENT で**偽の停止**を出した。
# A25（単位の説明句）とまったく同じ型で、処置も同じ ―― 照合の側を緩める。
# 括弧の中に **2つ以上連続した空白** があれば記入欄とみなす（空の括弧も従来どおり通す）。
_BR = [("【", "】"), ("［", "］"), (r"\[", r"\]"), ("（", "）"), (r"\(", r"\)")]
SLOT_RE = "|".join([r"[＿_]{2,}"] + [
    rf"{o}[^{c.strip(chr(92))}]{{0,60}}[\s　]{{2,}}[^{c.strip(chr(92))}]{{0,60}}{c}"
    for o, c in _BR] + [rf"{o}[\s　]*{c}" for o, c in _BR])


def check_quantity_sources(copy: Dict[str, str], dec: Declared,
                           chain: Sequence[Tuple[str, Sequence[Kappa], Sequence[str], str]]
                           ) -> Tuple[List[Finding], List[Judgment]]:
    """A28（第12.4版）：⑥に置いた量の出所を要求する。A22 と同型。

    **試算を禁じない。**禁じると A23（座席の数だけ量を置け）と正面から衝突し、
    売り手が実績を持たない座席で生成不能になる。代わりに二つだけ要求する。

      試算    → 本文に **試算と分かる語** が在ること（買い手が実測と取り違えないため）
      営業記入 → 本文に **記入欄** が在り、営業への申し送りに載っていること

    どちらも生成器には安い。安くないのは、根拠のない数字が実測の顔をして⑥に載ることである。
    """
    f, j = [], []
    body = copy.get("⑥", "")
    seats = list(quantities_by_seat(dec))   # N₄′：同上
    if not chain or not seats:
        return f, j                      # A23 側で既に要判断へ積まれている
    # 第14.2版：**A49 で `source` を割ったとき、この橋を直し忘れていた。**
    # 旧 `source` しか見ていないので、`pay_source`/`ret_source` で申告されると
    # 出所が一つも読めず `A28_SOURCE_UNDECLARED` が出る。**A49 の実装漏れ。**
    # 座席あたりの出所は**集合**である（払う側と戻る側で別々でよい）。
    srcs: Dict[str, List[str]] = {}
    if dec.s6_quantity_sources:                # 旧欄（走行データとの突合のため残す）
        for k, v in dec.s6_quantity_sources.items():
            if str(v).strip():
                srcs.setdefault(k, []).append(str(v).strip())
    for q in (dec.s6_quantities or ()):        # N₄′ の五つ組（A49 で割った二欄を含む）
        nm = _q_seat(q)
        if not nm:
            continue
        for key in ("pay_source", "ret_source", "source"):
            v = str(q.get(key, "")).strip()
            if v and v not in srcs.get(nm, []):
                srcs.setdefault(nm, []).append(v)
    if not srcs:
        j.append(Judgment("A28_SOURCE_UNDECLARED", ",".join(seats)))
        return f, j
    needs_sales = []
    for name in seats:
        vals = srcs.get(name)
        if not vals:
            j.append(Judgment("A28_SOURCE_MISSING", name)); continue
        for s in vals:
            if s not in Q_SRC:
                j.append(Judgment("A28_SOURCE_UNKNOWN", f"{name}={s}")); continue
            if s == "試算":
                needs_sales.append(name)
                if not any(w in body for w in EST_MARKS):
                    f.append(Finding("A28_ESTIMATE_UNMARKED", "stop", f"{name}:{s}"))
            elif s == "営業記入":
                needs_sales.append(name)
                if not re.search(SLOT_RE, body):
                    f.append(Finding("A28_SLOT_ABSENT", "stop", f"{name}:{s}"))
    grounded = [n for n in seats if any(v in Q_SRC_GROUNDED for v in srcs.get(n, []))]
    if grounded:
        f.append(Finding("A28_GROUNDED", "info", ",".join(grounded)))

    # 営業への申し送り ―― 生成器が「自分では確定できなかった」と言うための出口
    if dec.s6_to_sales is None:
        j.append(Judgment("A28_TO_SALES_UNDECLARED"))
    elif needs_sales and not [x for x in dec.s6_to_sales if x]:
        # 裏づけの無い量を置いておきながら、営業へ何も回していない
        j.append(Judgment("A28_TO_SALES_EMPTY", ",".join(needs_sales)))
    elif dec.s6_to_sales:
        f.append(Finding("A28_TO_SALES", "info", " / ".join(x for x in dec.s6_to_sales if x)))
    return f, j


def check_blocks(dec: Declared, blocks: Sequence[str]) -> Tuple[List[Finding], List[Judgment]]:
    """A27（第12.3版）：必須要素は導出、字数上限は較正。衝突したら較正の側が譲る。

    第12.2版まで、⑥の必須要素が本文に在るかは**一度も検査していなかった**。
    ⑥には10〜11個の要素が点灯するのに上限は450字（1要素あたり41字）で、
    生成器は毎回どちらかを破っていた——上限を守った2セルは自己申告で
    「別紙とするにとどめた」「量を落とした」と書いている。**落ちは self_report にしか出ていなかった。**

    処置は A23 の紙側・A24 と同じ型：**欄を作る**（Arm 0 の実測で、欄そのものが指示として働く）。
    落とした要素を申告させ、非空なら停止する。字数を破ることは仕様違反ではないが、
    要素を落とすことは仕様違反である——この非対称が、規定されていなかった優先順位そのものである。
    """
    f, j = [], []
    if not blocks:
        return f, j
    if dec.s6_omitted_blocks is None:
        j.append(Judgment("A27_OMISSION_UNDECLARED", f"必須要素{len(blocks)}個"))
        return f, j
    omitted = [b for b in dec.s6_omitted_blocks if b]
    if not omitted:
        f.append(Finding("A27_NO_OMISSION", "info", f"必須要素{len(blocks)}個すべて記載"))
        return f, j
    known = [b for b in omitted if b in set(blocks)]
    unknown = [b for b in omitted if b not in set(blocks)]
    if known:
        f.append(Finding("A27_BLOCK_OMITTED", "stop", ",".join(known)))
    if unknown:
        # 点灯していない要素を「落とした」と申告している＝申告と決定表がずれている
        j.append(Judgment("A27_OMISSION_UNMATCHED", ",".join(unknown)))
    return f, j


def check_realize(dec: Declared, executors: Sequence[Tuple[str, Sequence[str]]],
                  unwilling: Sequence[str] = (),
                  start: Optional[str] = None,
                  omega: Optional[int] = None,
                  busy_months: Sequence[int] = ()) -> Tuple[List[Finding], List[Judgment]]:
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
    # 第12.1版：三つ組の〈いつ〉は一度も検査されていなかった。
    # "昨年度中" "来期" "2027/4/1" がどれも通っていた（空文字だけが落ちる）。
    # N3 は act⟨w,d,o⟩ を型として立てているのに、d だけ検査対象を持っていなかった。
    for _a, d_, _c in acts:
        if iso_date(d_) is None:
            j.append(Judgment("R13_REALIZE_DATE_UNPARSED", str(d_)))
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
    # A37（第13.5版）：費目は着手より前には減らない。N₃ の〈いつ〉に因果の下限を与える。
    # A43（第13.5b版）：**順序を入れても、季節を入れていなかった。**
    # 第13.5版で順序は 8/8 満たしたが、置かれた日は「お盆直前」「秋の繁忙期の直前」
    # 「効果が出る前」だった。4体が挙げた。下限は二つある。
    #
    #   (a) 効果発現ラグ ω … 着手してから数字に出るまで。**導出**（prod.omega）。
    #       出ていない効果の分を先に減らすことはできない。
    #   (b) 買い手の繁忙期 … **入力**（busy_months）。空なら未聞取り（⊥）で判定しない。
    s0 = iso_date(start) if start else None
    if s0:
        need = add_months(s0, omega) if omega is not None else None
        for _a, d_, c_ in acts:
            dd = iso_date(str(d_))
            if dd is None:
                continue
            if dd < s0:
                f.append(Finding("A37_REALIZE_BEFORE_START", "stop", f"{c_} {dd} < 着手{s0}"))
            elif need and dd < need:
                f.append(Finding("A43_REALIZE_BEFORE_EFFECT", "stop",
                                 f"{c_} {dd} < 着手{s0}+ω{omega}m={need}"))
    if omega is None:
        j.append(Judgment("A43_OMEGA_UNKNOWN", "効果発現ラグが渡されていない"))
    if busy_months:
        for _a, d_, c_ in acts:
            dd = iso_date(str(d_))
            if dd and dd.month in set(busy_months):
                f.append(Finding("A43_REALIZE_IN_BUSY", "stop", f"{c_} {dd}（繁忙期）"))
    else:
        j.append(Judgment("A43_BUSY_UNKNOWN", "買い手の繁忙期が聞き取られていない"))
    return f, j


# A55（第14.3版）：**この表を直接引かないこと。**⊥ かどうかを決める述語は `is_bottom` 一つ。
# この表は語の一覧にすぎず、記入欄【　　　】を含まない。生で引くと記入欄が漏れる。
UNIT_UNKNOWN = ("", "―", "-", "未定", "不明", "⊥", "None", "null")
# A28／A49：量の出所の列挙。**払うと戻るは別の出所を持つ**（A49・第13.10版）
SOURCE_KINDS = ("買い手データ", "公開統計", "売り手の実績", "試算", "営業記入")
# 単位の語。**値の文字列の中に**単位が混ざっていると、宣言された単位と食い違っていても
# 文字列比較では見えない（第13.6版の実測：pay="180万〜900万" / pay_unit="円"）。
UNIT_TOKENS = ("億円", "万円", "千円", "人時", "人月", "時間", "円", "点", "件", "名",
               "％", "%", "日", "月", "億", "万", "千")   # 長いものから見る（万円 と 万 を取り違えない）


def is_bottom(v) -> bool:
    """⊥ か。**記入欄は ⊥ である。**

    第13.6版：R20 を入れた最初の実装は、`【　　　】`（営業が埋める記入欄）を
    「値が在る」と読んでいた。17行のうち13行が記入欄で、それでも停止 0 件だった。
    ところが買い手が第13版から一貫して言っているのは、まさにこの形である ――
    「出ていく額だけ決まっていて、**戻る額が全部空欄だ**」。
    N₂ は「⊥ はいかなる値とも比較できない」と言う。記入欄は ⊥ であって値ではない。
    **A28 の三つ目の出口（営業記入）は、営業が出す前に埋めるための出口であって、
    穴の空いた紙を出してよいという意味ではない。**
    """
    s = str(v).strip() if v is not None else ""
    if s in UNIT_UNKNOWN:
        return True
    return bool(re.search(SLOT_RE, s))


def unit_in_value(v, declared: str) -> Optional[str]:
    """値の文字列に、宣言された単位と食い違う単位語が混ざっていないか。

    第13.6版の実測：`pay="180万〜900万"` に対し `pay_unit="円"`。
    単位欄どうしの比較では見えない（どちらも「円」系ではある）が、**桁が二重になる**。
    長い語から見る ―― 「万円」を「万」と取り違えないため。最初に見つかった一つで判定する。
    """
    s = str(v) if v is not None else ""
    d = declared.strip()
    for u in UNIT_TOKENS:
        if u in s:
            return None if (u in d or d in u) else u
    return None


def _q_seat(q: Dict[str, object]) -> str:
    return str(q.get("seat", "")).strip()


# 第14.1版：`×`（U+00D7）が二度入っていた。`any(m in s …)` なので**振る舞いは変わらない**が、
# 表の傷は物差しの傷になる（`audit_matchers.py` (4)）。重複を落とす。**語は一つも減らしていない。**
EXPR_MARKS = ("×", "✕", "＊", "*", "掛ける")


def is_expr(v) -> bool:
    """その欄は〈式〉か。**式は値ではない。**（第13.7版の走行で出た）

    R20 の三状態（値／式／⊥）を `is_bottom` の二分岐で書いていたため、
    生成器が式を `ret` の欄に直接書いたとき「値が在る」と読み、
    **式の検査が一度も走らなかった**（`R20_RETURN_AS_EXPR` が 0 件）。
    走行前に「M1 が減って M2 が立たなければ、まず検査を疑う」と書いておいたので出た。
    **浅い一致の6件目。**値と ⊥ の二分では足りず、状態は三つある。
    """
    if v is None:
        return False
    s = str(v)
    return any(m in s for m in EXPR_MARKS)


# ══════════════════════════════════════════════════════════ A45／A45b／A45c 層(i) の算術
# 25業界21件で、買い手が挙げた理由の上位に並んだ三つ。**どれも売り手の数字だけで閉じる。**
#   「1,400万から3,200万は2.3倍の開き、これは見積ではなく相場表だ」            20/21
#   「媒体費・制作費・人月単価の内訳が無い。予算科目に立てられない」            21/21
#   「180万÷3か月＝月60万、900万÷12か月＝月75万。長く頼むほど月額が上がる」     実測
# 買い手が現に**検算して**落としている。機械で落とせるのに落としていなかった。
_SCALE = (("億円", 1e8), ("万円", 1e4), ("千円", 1e3), ("億", 1e8), ("万", 1e4),
          ("千", 1e3), ("円", 1.0))
AMOUNT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(億円|万円|千円|億|万|千|円)?")


def parse_amount(v, declared_unit: str = "") -> Optional[float]:
    """「1,400万」「3,200万円」「1.5億」を円に直す。**読めなければ ⊥ を返す（0 にしない）。**

    N₂ ―― ⊥ を 0 に落とすと、内訳の和も幅の比も黙って成立してしまう。
    値の中に単位が無ければ、申告された単位の倍率を使う（`R20_UNIT_IN_VALUE` と対になる）。
    """
    if v is None:
        return None
    s = str(v).strip()
    if is_bottom(s):
        return None
    m = AMOUNT_RE.search(s)
    if not m:
        return None
    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    tok = m.group(2)
    if not tok:
        for u, k in _SCALE:
            if u in (declared_unit or ""):
                return num * k
        return num
    return num * dict(_SCALE)[tok]


# 較正値。**実測は二点しかない** ―― 2.3倍で 20/21 が拒否、1.8倍は未検証。
# したがってこれは導出ではなく較正であり、未較正の業界では降格する（`CALIBRATED_CODES`）。
PRICE_RATIO_MAX = 2.0


def check_price(dec: Declared, industry: Optional[str] = None
                ) -> Tuple[List[Finding], List[Judgment]]:
    """A45 幅の比／A45b 内訳／A45c 単価の単調性。**層(i)＝算術の層。**

    層(ii) 構造（式の形）と層(iii) 係数（効果量）は別。ここは**四則演算だけ**で閉じる。
    だから最も安く、最も確実で、しかも買い手が必ず検算する。
    """
    f, j = [], []
    lo = parse_amount(dec.s6_price_low, dec.s6_price_unit or "")
    hi = parse_amount(dec.s6_price_high, dec.s6_price_unit or "")
    if lo is None and hi is None:
        j.append(Judgment("A45_PRICE_UNDECLARED"))
        return f, j
    if lo is None or hi is None:
        j.append(Judgment("A45_RANGE_HALF_MISSING", f"下限={dec.s6_price_low} 上限={dec.s6_price_high}"))
    elif lo > 0 and hi / lo > PRICE_RATIO_MAX:
        f.append(Finding("A45_RANGE_TOO_WIDE", "stop", f"{hi/lo:.2f}倍 > {PRICE_RATIO_MAX}倍"))
    # A45b：内訳
    items = dec.s6_price_items
    if not items:
        f.append(Finding("A45B_BREAKDOWN_MISSING", "stop", "価格の内訳が ⊥"))
    else:
        vals = [parse_amount(it.get("amount"), str(it.get("unit", dec.s6_price_unit or "")))
                for it in items]
        if any(v is None for v in vals):
            j.append(Judgment("A45B_ITEM_UNPARSED",
                              "／".join(str(it.get("name")) for it, v in zip(items, vals)
                                        if v is None)))
        else:
            tot = sum(vals)
            base_lo, base_hi = (lo if lo is not None else hi), (hi if hi is not None else lo)
            if base_lo is not None and not (base_lo * 0.995 <= tot <= base_hi * 1.005):
                f.append(Finding("A45B_BREAKDOWN_MISMATCH", "stop",
                                 f"内訳の和={tot:.0f} 総額={base_lo:.0f}〜{base_hi:.0f}"))
    # A45c：単価の単調性
    tiers = dec.s6_price_tiers or ()
    pts = []
    for t in tiers:
        q = t.get("qty")
        a = parse_amount(t.get("amount"), str(t.get("unit", dec.s6_price_unit or "")))
        try:
            qv = float(q)
        except (TypeError, ValueError):
            qv = None
        if qv and a is not None and qv > 0:
            pts.append((qv, a / qv, str(t.get("label", ""))))
    pts.sort()
    for (q0, u0, l0), (q1, u1, l1) in zip(pts, pts[1:]):
        if u1 > u0 * 1.005:
            f.append(Finding("A45C_UNIT_PRICE_NOT_MONOTONE", "stop",
                             f"{l0}={u0:.0f}/単位 → {l1}={u1:.0f}/単位"))
    return apply_calibration(f, j, industry, sigma_note=False)


def quantities_by_seat(dec: Declared) -> Dict[str, str]:
    """N₄′ の新欄から、旧 `s6_kappa_by_seat`（座席→基準）を作る。

    A16・A23 の既存検査を書き換えずに済ませるための橋。新欄が無ければ旧欄をそのまま返す。
    """
    if not dec.s6_quantities:
        return dec.s6_kappa_by_seat or {}
    out = dict(dec.s6_kappa_by_seat or {})
    for q in dec.s6_quantities:
        s = _q_seat(q)
        if s:
            out.setdefault(s, str(q.get("kappa", "")))
    return out


def check_decidable(dec: Declared, chain: Sequence[Tuple[str, Sequence[str], Sequence[str], str]]
                    ) -> Tuple[List[Finding], List[Judgment]]:
    """R20（第13.5b版）：**その座席は、この紙だけで決められるか。**

    N₄′ から直に出る。座席が決めるとは〈払う〉と〈戻る〉を**同じ単位で**並べて、
    どちらが大きいかを言うことである。したがって決定可能であるためには

      (1) 払う・戻るの両方が在る（どちらかが ⊥ なら比べられない ―― N₂）
      (2) 二つの単位が一致する（違えば並べられない ―― N₄′）
      (3) 分母が在る（「何あたり」が無ければ量ではなく数字である）

    第13版・第13.5版で買い手が最も多く言ったのは (1) である。
    「出ていく額だけ決まっていて、戻る額が全部空欄だ」。
    機械はそれを一度も見ていなかった ―― **戻る額の欄が無かった**から。
    """
    f, j = [], []
    if dec.s6_quantities is None:
        j.append(Judgment("R20_QUANTITIES_UNDECLARED"))
        return f, j
    seats = {c[0] for c in chain}
    got = [_q_seat(q) for q in dec.s6_quantities]
    for name in sorted(seats - set(got)):
        f.append(Finding("R20_SEAT_NO_QUANTITY", "stop", name))
    for name in sorted({x for x in got if got.count(x) > 1}):
        f.append(Finding("R20_SEAT_DUPLICATED", "stop", name))   # 座席は一行（N₄′）
    for q in dec.s6_quantities:
        s = _q_seat(q) or "(座席なし)"
        pay, ret = q.get("pay"), q.get("ret")
        pu, ru = str(q.get("pay_unit", "")).strip(), str(q.get("ret_unit", "")).strip()
        den = str(q.get("per", "")).strip()
        if is_bottom(pay):
            f.append(Finding("R20_PAY_MISSING", "stop", f"{s}={str(pay).strip()[:20]}"))
        # 三状態（値／式／⊥）。第13.7版の走行で、生成器が式を `ret` の欄に直接書き、
        # `is_bottom` が「値が在る」と読んで式の検査を素通りした。**状態は三つある。**
        has_expr_fields = not all(is_bottom(q.get(k)) for k in
                                  ("ret_expr", "ret_basis", "ret_coef", "coef_source"))
        ret_is_expr = has_expr_fields or is_expr(ret)
        if ret_is_expr and not has_expr_fields:
            f.append(Finding("R20_EXPR_IN_VALUE", "stop",
                             f"{s} 戻る欄に式が書かれているが成分の欄が ⊥"))
        if ret_is_expr:
            # A44 の出口（第13.8版）：**戻る額は、値でなくても〈式〉なら決められる。**
            # 25業界 21/21 が「営業へ回した空欄が資料を殺す」と言い、機械側も 8/8 で停止した。
            # だが 17行のうち13行は記入欄で、これは生成器の出来ではなく
            # **売り手が買い手の数字を持っていない**という入力側の欠落だった。
            # 買い手の側で決定可能であるために、値そのものは要らない ――
            # 〈買い手の量 × 売り手の係数〉と**係数の出所**が在れば、買い手が自分で埋められる。
            # 係数に出所を要求するのは A28 と同型（出所のない量は置けない）。
            basis, coef, csrc = q.get("ret_basis"), q.get("ret_coef"), q.get("coef_source")
            if has_expr_fields:
                if is_bottom(basis):
                    f.append(Finding("R20_EXPR_NO_BASIS", "stop", f"{s} 掛ける相手が ⊥"))
                if is_bottom(coef):
                    f.append(Finding("R20_EXPR_NO_COEF", "stop", f"{s} 係数が ⊥"))
                if is_bottom(csrc):
                    f.append(Finding("R20_EXPR_COEF_UNSOURCED", "stop", f"{s} 係数の出所が ⊥"))
                if not any(is_bottom(x) for x in (basis, coef, csrc)):
                    j.append(Judgment("R20_RETURN_AS_EXPR",
                                      f"{s} {str(basis).strip()[:28]} × {str(coef).strip()[:16]}"))
        elif is_bottom(ret):
            f.append(Finding("R20_RETURN_MISSING", "stop", f"{s}={str(ret).strip()[:20]}"))
        # A55（第14.3版）：**⊥ を決める述語は一つ。**ここは `pu in UNIT_UNKNOWN` と
        # 生で書いてあり、`is_bottom` が見る記入欄【　　　】を落としていた。
        # 単位欄が記入欄のとき、片方だけなら R20_UNIT_MISMATCH（停止）が誤って立ち、
        # 両方なら**何も出ずに素通り**していた。R20 の値側で一度直した型を、単位側で再発させた形。
        if is_bottom(pu) or is_bottom(ru):
            j.append(Judgment("R20_UNIT_UNDECLARED", f"{s} 払う={pu or '⊥'} 戻る={ru or '⊥'}"))
        elif pu != ru:
            f.append(Finding("R20_UNIT_MISMATCH", "stop", f"{s} {pu} vs {ru}"))
        # 値の中に混ざった単位（"180万〜900万" と書いて単位欄は "円"）
        for lab, v, u in (("払う", pay, pu), ("戻る", ret, ru)):
            # 式の文字列に単位語が混ざるのは正常（「× 1.0（円／円）」）。値のときだけ見る。
            if lab == "戻る" and ret_is_expr:
                continue
            bad = unit_in_value(v, u) if not is_bottom(v) else None
            if bad:
                f.append(Finding("R20_UNIT_IN_VALUE", "stop", f"{s} {lab}「{bad}」≠単位欄「{u}」"))
        if is_bottom(den):          # A55：分母が記入欄でも「在る」と読んでいた
            j.append(Judgment("R20_DENOMINATOR_MISSING", s))
        # A49（第13.10版）：**〈出所〉の欄が二つの担体を持っていた。**
        # 第13.7版の走行で、生成器が「払う＝自社の運用手順に基づく試算／戻る＝式（係数は…）」と
        # **連結して**申告し、列挙値と一致しないので `A28_SOURCE_UNKNOWN` が 3/3 座席で立った。
        # A37／A37b／A41／A48／A48b に続く**6件目の〈一つの語／欄が二つの担体〉**。欄を割る。
        psrc = str(q.get("pay_source", "")).strip()
        rsrc = str(q.get("ret_source", "")).strip()
        legacy = str(q.get("source", "")).strip()
        if not psrc and not rsrc:
            if is_bottom(legacy):   # A55：出所欄が記入欄なら〈連結〉ではなく〈未申告〉
                j.append(Judgment("R20_SOURCE_UNDECLARED", s))
            elif legacy not in SOURCE_KINDS:
                # 旧欄に二つ分を連結して書いた形。**これが A49 の現れ方そのもの**
                j.append(Judgment("A49_SOURCE_MERGED", f"{s}={legacy[:40]}"))
        else:
            for lab, v in (("払う", psrc), ("戻る", rsrc)):
                if is_bottom(v):    # A55
                    j.append(Judgment("R20_SOURCE_UNDECLARED", f"{s}／{lab}"))
                elif v not in SOURCE_KINDS:
                    j.append(Judgment("A28_SOURCE_UNKNOWN", f"{s}／{lab}={v[:30]}"))
    return f, j


# ══════════════════════════════════════════════ A47 ②の問いの向き／A46 断りの回数
# どちらも **検査を足して直る話ではなく、生成の指示側の制約**である。
# A47 は②の設計そのものへの反証で、A46 は R17 への過剰適応。
S2_QUESTION_RE = re.compile(r"[^。！？\n]*(?:か[。？]|？)")
POSSESSION_WORDS = ("お手元", "手元", "お持ち", "ありますか", "把握", "持っていますか",
                    "集計され", "残っていますか", "どなた", "お分かり")
# 断り書きの定型。**語彙ではなく回数で数える**（版をまたいで比べられる物差し）。
DISCLAIM_RE = re.compile(r"(?:ではありません|ではない。|ておりません|ていません|しません。|ものではありません)")
DISCLAIM_MAX = 3          # 較正値。実測は段あたり 0〜7（8セル×3走行）


def check_s2_form(dec: Declared, copy: Dict[str, str]) -> Tuple[List[Finding], List[Judgment]]:
    """A47：**②の問いは、買い手の保有ではなく単位に向ける。**

    ②は「①の事実を別の単位で数え直して驚きを作る」段である（異化）。
    ところがその**問いの形**が、買い手には「あなたは数えていない」という決めつけとして届いた。

      「三十年そうやって回してきた宿に向かって、**どなたの手元にあるでしょうか、はない**」
      ―― 観光・旅行・宿泊／社長。**25業界で 8/21**

    モデルは τ に `known ∈ {既知, 未知}` を既に持っている。
    **既知の量に「持っていますか」と問うのは、規則違反であるはず**だった。

    ```
    いまの②  「その数字は、どなたの手元にありますか」   → 買い手の不作為を問う形
    あるべき② 「同じ数字を、この単位で見るとこうなります」 → 単位を問う形
    ```

    紙側でも照合する（A23 の紙側と同型 ―― **申告だけで通さない**）。
    検分：8セル×3走行の②本文17件に当てて、保有を問う疑問文は **1件**（E2-P1・第13.6版）。
    25業界データの中の当該一文も取れる。**誤検出 0。**
    """
    f, j = [], []
    s2 = (copy or {}).get("②", "")
    qs = [m.group(0).strip() for m in S2_QUESTION_RE.finditer(s2)] if s2 else []
    pos = [q for q in qs if any(w in q for w in POSSESSION_WORDS)]
    if dec.s2_asks_possession is None:
        j.append(Judgment("A47_S2_FORM_UNDECLARED"))
    elif dec.s2_asks_possession is True:
        f.append(Finding("A47_S2_ASKS_POSSESSION", "stop", "②が買い手の保有を問うている（申告）"))
    for q in pos:
        f.append(Finding("A47_S2_POSSESSION_QUESTION", "stop", q[:60]))
    if qs and not pos:
        j.append(Judgment("A47_S2_QUESTION", f"②に疑問文 {len(qs)}件"))
    return f, j


def check_disclaimers(dec: Declared, copy: Dict[str, str]
                      ) -> Tuple[List[Finding], List[Judgment]]:
    """A46：**同じ断りは1回まで。二度言うと否定になる。**

    R17（侮辱検査）を守ろうとした**過剰適応**である。25業界で 7/21。
    断り書きは〈この紙が言っていないこと〉についてのメタな言明であり、
    二度繰り返すと「あなたはそう読むだろうが違う、本当に違う」という形になって、
    **買い手の読み方そのものへの否定**に転じる。

    回数で数えるので**版をまたいで比べられる**（語彙に較正されない）。
    検分：8セル×3走行で段あたり 0〜7件。**第13.7版の E1-P1 の⑥が7件で最多**だった。
    """
    f, j = [], []
    ds = dec.s5_disclaimers
    if ds is None:
        j.append(Judgment("A46_DISCLAIMER_UNDECLARED"))
    else:
        norm = [str(x).strip() for x in ds if str(x).strip()]
        for t in sorted({x for x in norm if norm.count(x) > 1}):
            f.append(Finding("A46_DISCLAIMER_REPEATED", "stop", t[:50]))
    for st, txt in (copy or {}).items():
        n = len(DISCLAIM_RE.findall(txt or ""))
        if n > DISCLAIM_MAX:
            j.append(Judgment("A46_DISCLAIMER_MANY", f"{st} に断りの文 {n}件（上限 {DISCLAIM_MAX}）"))
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
    # 第12.1版：∃χ∈Γ^own を実際に検査する。
    # 従来は hit を計算して **捨てて** いたので、Γ^own に無い文字列でも、Γ^own が空でも停止した。
    # SPEC §1.1.1 は insult(φ) ⟺ ∃χ ∈ Γ^own. Γ∪{φ} ⊢ ¬χ である。Γ^own = ∅ なら侮辱は成立しない。
    # 照合できないときに停止させるのは、A25 で最も高くついた誤りと同じ型なので、要判断へ回す。
    hit = [k for k, v in gamma_own.items() if d in v or v in d] if gamma_own else []
    if hit:
        f.append(Finding("R17_DENIES_OWN", "stop", f"{d}@{','.join(hit)}"))
    else:
        j.append(Judgment("R17_DENIES_UNMATCHED",
                          f"{d} / Γ^own={'空' if not gamma_own else ','.join(gamma_own)}"))
    return f, j


def check_chain(dec: Declared,
                chain: Sequence[Tuple[str, Sequence[Kappa], Sequence[str], str]],
                kept_unit: bool = False,
                expr: Optional[Dict[Kappa, Set[Kappa]]] = None
                ) -> Tuple[List[Finding], List[Judgment]]:
    """A16（第9版）：Π2 は「各リンクで濾す」と言っている。終端の座席だけ見てはならない。

    資料を読む座席すべてについて
      ・⑥に置いた量が、その座席の基準で読めること
      ・制度由来の座席については、③の対応語がその座席の様式語を含むこと
    """
    f, j = [], []
    ex = expr if expr is not None else EXPR_OK       # 第12.1版：商材座標の表を受け取れる
    if not chain:
        return f, j
    if dec.s6_kappa is None:
        return f, j                      # A5 側で要判断に積まれている
    # A23（第11版）：⑥に置く量は単一ではなく、読む座席ごとの組である。
    # Π2 の ∀k から直に出るのに、第10版までの実装は s6_kappa 一つで全座席を賄おうとしていた。
    by_seat = quantities_by_seat(dec)      # N₄′：新欄があればそちらを正とする
    if chain and not by_seat:
        j.append(Judgment("A23_PER_SEAT_UNDECLARED", ",".join(c[0] for c in chain)))
    # ⑥に既に在る基準（②の単位を保持していれば実務性も在る＝A6 の併記）
    bases = kappa_tokens(dec.s6_kappa)
    if kept_unit and dec.s2_unit:
        bases.add("実務性")
    for name, kappa, form, origin in chain:
        own = by_seat.get(name)
        cand = bases | kappa_tokens(own)
        ok = any(b in ex and (ex[b] & set(kappa)) for b in cand)
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


def check_dates_v7(dec: Declared, deadline: Optional[str],
                   today: Optional[date] = None,
                   lt_months: Optional[int] = None) -> Tuple[List[Finding], List[Judgment]]:
    """R12b / R16（A14）：⑤で他手段に課した期限は、自社案にも当たる。

    A37（第13.5版）：**`LT_months` が⑥の日付に一度も掛かっていなかった。**
    買い手が決めてから実際に動き出すまでの月数は `start_deadline` の逆算にしか使われず、
    ⑥に書く日付は素通りだった。第13版で 12/15、第13.3版では**版によらず 4/4** が指摘した。

      「うちは決めてから実際に動き出すまで**半年**かかる。2026年9月28日に決めても
        動き出すのは2027年3月末だ。ところが『2027年2月28日にパート人時を落とす』と書いてある」

    A37b：その実装中に、**`LT_months` が二つの担体を持っていた**ことが出た。
    `persona12.py` は〈決定→着手〉として買い手に渡し、`effective_LT` は〈着手→境界〉として
    足していた。前者で読むときだけ `acquire` と連続区間になる（→ `start_deadline`）。
    よって④からの逆算日は**決定期限**であり、⑥の着手日に上限を課すものではない。
    ここを直さずに走らせると 8セル中6セルで**充足不能な指示**になっていた
    （例 R1-P2：決定 ≤ 2026-09-28 かつ 着手 ≤ 2026-09-28 かつ 着手 ≥ 決定+6か月）。

    三段で見る。
      決定日  today ≤ decide ≤ **決定期限**（④からの逆算・従来の R12b）
      着手日  start ≥ decide ＋ LT_months        （上限は無い）
      実現日  s6_realize の各〈いつ〉 ≥ start     （→ check_realize）
    """
    f, j = [], []
    # A55（第14.3版）：**⊥ は ⊥ のまま。代用しない。**（N₂／型5 の述語版）
    # ここは `dcd = dec.s6_decide_date or dec.s6_start_date` と書いてあった。
    # 旧走行に欄が一つしかなかったことへの手当てだったが、その結果 R12b が
    # **決定日の代わりに着手日**を④の期限と比べていた。25業界の採点で停止 9 件のうち 3 件が
    # この形で、うち 2 件は買い手が「進める」と答えた紙だった（＝誤停止）。
    # 欄が無いことは「別の欄で埋める」ことではない。受け皿は R12b_START_UNDECLARED。
    dcd = None if is_bottom(dec.s6_decide_date) else dec.s6_decide_date
    if is_bottom(dec.s6_decide_date) and not is_bottom(dec.s6_start_date):
        j.append(Judgment("A37_DECIDE_UNDECLARED", str(dec.s6_start_date)))
    if deadline and dcd:
        # 第12.1版：文字列のまま比べていた。"2027-4-1"（ゼロ詰めなし）や "2027/4/1" で
        # 辞書順が暦順と食い違う。日付として読めないなら、比較せず要判断へ（N2）。
        a, b = iso_date(dcd), iso_date(deadline)
        if a is None or b is None:
            j.append(Judgment("R12b_DATE_UNPARSED", f"⑥{dcd} / ④{deadline}"))
        elif a > b:
            f.append(Finding("R12b_START_AFTER_DEADLINE", "stop", f"⑥{dcd}>④{deadline}"))
    elif deadline and dcd is None:
        j.append(Judgment("R12b_START_UNDECLARED", deadline))
    # ── A37：決定日が過去でないか／着手日が決定日＋LT 以降か
    d0 = iso_date(dcd) if dcd else None
    d1 = iso_date(dec.s6_start_date) if dec.s6_start_date else None
    if today and d0 and d0 < today:
        f.append(Finding("A37_DECIDE_PAST", "stop", f"決定{d0} < 今日{today}"))
    if lt_months is None:
        if d1:
            j.append(Judgment("A37_LT_UNKNOWN", "買い手のリードタイムが渡されていない"))
    elif d0 and d1:
        need = add_months(d0, lt_months)
        if d1 < need:
            f.append(Finding("A37_START_BEFORE_LT", "stop",
                             f"着手{d1} < 決定{d0}+{lt_months}m={need}"))
    elif d0 and d1 is None:
        j.append(Judgment("A37_START_UNDECLARED", str(d0)))
    if dec.s6_self_check is None:
        j.append(Judgment("R16_SELF_APPLY_UNDECLARED"))
    elif dec.s6_self_check is False:
        f.append(Finding("R16_SELF_APPLY_FAILED", "stop"))
    return f, j


def check_declared(dec: Declared, kn: Set[Kappa], kept_unit: bool,
                   stages: Sequence[str], n_seats: int,
                   expr: Optional[Dict[Kappa, Set[Kappa]]] = None
                   ) -> Tuple[List[Finding], List[Judgment]]:
    """宣言された値の比較のみ。意味判定はしない。None は未定義（A10）"""
    f, j = [], []
    EXPR = expr if expr is not None else EXPR_OK      # 第12.1版：商材座標の表を受け取れる
    has4, has2, has3 = "④" in stages, "②" in stages, "③" in stages

    # R10a 反復の再生産（A26：比較対象は課金周期ではなく〈提案後に問題が残る周期〉）
    #
    # 旧実装は s6_period_months（課金周期）と s4_period_months を比べていた。
    # 課金周期は「問題が残るか」と直交しているので、両方向に誤った。第12.2版の実測：
    #   ・単発と申告した4件は比較対象外（info）になり、問題の再発は一切検査されなかった
    #   ・E2-P2・R2-P2 は本文で「翌年以降に同じ手数を積み直しません」と書いているのに停止した
    # 指示文（「同じ周期で同じ問題を作り直さない」）のほうが正しかったので、直すのは検査側である。
    if has4:
        if dec.s4_declares_repetition is None:
            j.append(Judgment("S4_REPETITION_UNDECLARED"))
        elif dec.s4_declares_repetition:
            s4p, res = dec.s4_period_months, dec.s6_residual_period_months
            if s4p is None:
                f.append(Finding("R10a_PERIOD_UNDECLARED", "stop"))
            elif s4p == 0:
                # ④が反復を宣言しているのに周期が 0＝反復しない。矛盾ではなく未定義（N2）
                f.append(Finding("R10a_NOT_PERIODIC", "info", f"s4={s4p}m"))
            elif res is None:
                # 旧欄（課金周期）へは落とさない。落ちる先が誤った物差しだから（A25 の教訓）
                j.append(Judgment("R10a_RESIDUAL_UNDECLARED", f"s4={s4p}m"))
            elif res == 0 or res > s4p:
                f.append(Finding("R10a_RESIDUAL_OK", "info", f"s4={s4p}m 残存={res}m"))
                # 旧 R10a なら止まっていた形＝偽陽性の正体。数えられるように残す
                s6p = dec.s6_period_months
                if s6p is not None and 0 < s6p <= s4p:
                    f.append(Finding("R10a_CHARGE_PERIODIC", "info",
                                     f"課金={s6p}m ≤ s4={s4p}m だが残存={res}m"))
            else:
                f.append(Finding("R10a_REPRODUCES_PROBLEM", "stop",
                                 f"s4={s4p}m 残存={res}m"))

    # R10b 単位。A6：禁じるのは置換であって併記ではない
    # A25b：「⑥に単位が無い」の停止は check_unit_presence 側の ABSENT 一本に寄せた。
    # ここは併記（正しい両替）の註記だけを残す。二つのコードで同じ事実を二度数えない。
    if has2 and dec.s2_unit:
        if dec.s6_recasts_unit is None:
            j.append(Judgment("S6_UNIT_RECAST_UNDECLARED", dec.s2_unit))
        elif dec.s6_recasts_unit and kept_unit:
            f.append(Finding("R10b_UNIT_JUXTAPOSED", "info", dec.s2_unit))

    # A5 ⑥が κ_n で読めるか（A25c：連結された基準名は正規化してから引く）
    if dec.s6_kappa is None:
        j.append(Judgment("A5_KAPPA_UNDECLARED"))
    else:
        ks = kappa_tokens(dec.s6_kappa)
        if kappa_merged(dec.s6_kappa):
            f.append(Finding("A25_KAPPA_MERGED", "info",
                             f"{dec.s6_kappa}->{sorted(ks)}"))
        known = {x for x in ks if x in EXPR}
        if not known:
            j.append(Judgment("EXPR_TABLE_MISS", f"⑥ k={dec.s6_kappa}"))
        elif not any(EXPR[x] & set(kn) for x in known):
            f.append(Finding("A5_NOT_EXPRESSIBLE", "stop",
                             f"{sorted(known)}->{sorted(kn)}"))
        # 第12.5b版：κ_n が2つある座席で、申告が一方しか覆っていないことを見えるようにする。
        # A5 は ∃（どれか一つが届けばよい）のままにしてある ―― ∀ にするのはモデルの変更で、
        # Π₂ の ∀k は A23（座席ごと）で受けている。**断定せず、申し送るだけ。**
        if len(kn) > 1 and known:
            reach = {t for x in known for t in (EXPR[x] & set(kn))}
            if reach and reach != set(kn):
                j.append(Judgment("A5_KAPPA_PARTIAL",
                                  f"κ_n={sorted(kn)} 届いた={sorted(reach)}"))

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
                  unwilling: Sequence[str] = (),
                  prod: Optional[Product] = None,
                  industry: Optional[str] = None,
                  blocks: Sequence[str] = (),
                  today: Optional[date] = None,
                  lt_months: Optional[int] = None,
                  gates: Sequence[Tuple[str, str, int]] = (),
                  omega: Optional[int] = None,
                  busy_months: Sequence[int] = (),
                  tau_ok_dates: Sequence[str] = (),
                  decide_deadline_tau: Optional[str] = None,
                  basis_names: Sequence[str] = ()) -> dict:
    """第12.1版：商材座標と業界を受け取れるようにした。

    第10版は「較正表は業界の関数ではなく商材座標の関数である」と言い、`expr_ok_of` を入れたが、
    それが使われていたのは `check_tau`（生成前）だけだった。生成後検査はグローバルの
    `EXPR_OK`（＝較正表）を引き、`apply_calibration` も一度も掛からない状態にあった。
    R1-P1・R2-P1 は α=(高,高)・費目が変動なので、座標では 実務性↔価格 が開く。表が現に食い違っていた。
    """
    ex = expr_ok_of(prod)
    uf, kept, uj = check_unit_presence(copy, dec, stages)
    f = check_v0(copy) + uf
    f2, j = check_declared(dec, set(kappa_final), kept, stages, n_seats, ex)
    f += f2; j += uj
    f3, j3 = check_realize(dec, executors, unwilling, dec.s6_start_date,
                           omega, busy_months); f += f3; j += j3   # A37・A43
    f4, j4 = check_dates_v7(dec, deadline, today, lt_months); f += f4; j += j4   # A37
    fg, jg = check_gates(dec, gates, copy.get("④", "")); f += fg; j += jg        # A41
    fs, js = check_s4_dates(copy, tau_ok_dates, decide_deadline_tau)             # A41b
    f += fs; j += js
    fq, jq = check_decidable(dec, chain); f += fq; j += jq                       # R20 / N₄′
    fp, jp = check_price(dec, industry); f += fp; j += jp                        # A45/A45b/A45c
    f2s, j2s = check_s2_form(dec, copy); f += f2s; j += j2s                      # A47
    fd, jd = check_disclaimers(dec, copy); f += fd; j += jd                      # A46
    j += check_realize_bound(dec, tau_ok_dates)                                 # A50
    j += check_basis_in_input(dec, basis_names)                                 # A52
    f5, j5 = check_insult(dec, gamma_own or {}); f += f5; j += j5
    f6, j6 = check_chain(dec, chain, kept, ex); f += f6; j += j6
    f += check_seat_words(copy, dec, chain)      # A23 の紙側（申告だけで通さない）
    f7, j7 = check_blocks(dec, blocks); f += f7; j += j7   # A27：要素の落ちを隠させない
    f8, j8 = check_quantity_sources(copy, dec, chain); f += f8; j += j8   # A28：⑥の量の出所
    f, j = apply_calibration(f, j, industry, sigma_note=False)
    stop = [x for x in f if x.level == "stop"]
    return {"findings": f, "needs_judgment": j, "pass": not stop and not j}


# ══════════════════════════════════════════════════════════════════ N₆ 要求の四つ組
# 第12.7版。**アノマリーの個数は増えているが、種類は増えていない。**
# 第12.6版までに記録した29件のうち、新しいものは全部この二つのどちらかだった。
#
#   型1  指示が複数を誘うのに欄が単数     A24 費目 / A25 単位 / A25c 基準 / κ_n / A30 出所
#   型4  衝突する要求に順序が無い・範囲が無い  A27 / A28 / A29 / A31 / A32 / A33
#
# 一件ずつ足すのをやめて、**両方をまとめて潰す規定**を置く。
#
# ── 型1 の正体は、量化子の潰れである。
# Π₂ の通関律は「∀k」と書いてある。∀ が立っている担体は集合であって、単数ではない。
# ところが宣言欄は毎回スカラーで作られてきた。生成器は指示の見せ方をそのまま写すので、
# 集合を一つの文字列に連結する。**論理式が ∀ を持つのに、欄が濃度1を仮定している**
# ―― これが5回繰り返された同じ一つの誤りである。
#
# ── 型4 の正体は、要求の指定不足である。
# 要求は「何を書け」だけでは足りない。A27 は〈衝突したときどちらが譲るか〉が無く、
# A29・A32 は〈どの集合の上を走るのか〉が無く、A31 は〈何をもって満たしたとするか〉が無かった。
#
# ── したがって、要求はこの四つ組で書かれねばならない。
#
#     R = ⟨ 担体, 定義域, 充足条件, 強さ ⟩
#
#   担体      何についての要求か（量・費目・座席・基準・日付・語）。N₄ の「量は単位を持つ」を要求へ広げる
#   定義域    ∀ が走る集合。**明示する。** N₂ を定義域へ適用する ―― 未定義の定義域は ⊥ であって、
#             「たぶん一つ」ではない。濃度1と置くなら、なぜ1でよいかを書く
#   充足条件  何をもって満たしたとするか。「無いことの明示」が充足に当たるかを含む（A31）
#   強さ      衝突したときに譲るか。較正台帳の〈導出 > 較正〉をすべての要求へ広げる（A27 の一般化）
#
# 監査は機械で回せる（→ `audit_requirements`）。**規定に対象を与える** ―― 対象のない規定は
# 規定ではない、というのは cost 単調性（第12.5版）で学んだことである。

REQ_FIELDS = ("field", "carrier", "domain", "card", "why1", "value_card",
              "satisfy", "entrench", "yields_to")


class Req(NamedTuple):
    field: Optional[str]      # 対応する Declared の欄（無ければ None）
    carrier: str              # 担体
    domain: str               # ∀ が走る集合
    card: str                 # "1" か "n"
    why1: str                 # card=="1" のとき、なぜ1でよいか（空なら監査が落とす）
    value_card: str           # 写像欄のとき、値の側の濃度（"-" は写像でない）
    satisfy: str              # 充足条件
    entrench: str             # "導出" か "較正"（衝突したとき較正が譲る）
    yields_to: str = ""       # 同じ担体の他の要求と衝突したときの順序、または衝突しない理由


REQS: Tuple[Req, ...] = (
    Req("s2_unit", "単位", "②が①を数え直すのに使った単位", "1",
        "②は①の事実を一つ別の単位で数え直す段であり、単位が2つなら②が2段になる（Σ は Π₁ の階段）",
        "-", "その単位語が⑥の本文に残っていること（説明句つきでも候補が一つ当たれば可・A25b）", "導出"),
    Req("s2_from_unit", "単位", "②が置き換える前の単位", "1",
        "s2_unit と対になる一つ", "-", "申告のみ（本文照合はしない）", "導出", "s2_unit と対（置き換え前と後であって、競合しない）"),
    Req("s3_form_mapping", "様式語の対応", "資料を読む座席 ∪ {最終裁定点}", "n", "",
        "-", "③の新語が、各座席の様式語のどれに当たるかを座席ごとに書くこと", "導出"),
    Req("s4_declares_repetition", "反復の宣言", "④が問題化した事象", "1",
        "④は一つの事象を必然化する段（M₀ は単一）", "-", "真偽の申告", "導出", "④の周期が基準。s6_period（課金）とも s6_residual（残存）とも別の担体である"),
    Req("s4_period_months", "周期", "④が問題化した事象", "1", "同上", "-", "月数の申告", "導出", "R10a の比較の基準side。残存周期と比べる（A26）"),
    Req("s6_period_months", "周期", "本提案の課金", "1", "契約は一つ", "-", "月数の申告", "導出", "R10a では使わない。R10a_CHARGE_PERIODIC の註記にだけ使う（A26）"),
    Req("s6_residual_period_months", "周期", "④の事象が提案後に再発する周期", "1",
        "④の事象が一つだから（A26）", "-", "月数の申告。0 は再発しない", "導出", "R10a の比較対象。課金周期には落とさない（A26）"),
    Req("s5_is_constraint_disclosure", "書き方", "⑤の本文", "1", "⑤全体に掛かる一つの述語",
        "-", "能力の否定でなく条件下の不成立の形か", "導出",
        "衝突しない（定義域が交わらない。第13.5b版に対で見るようにして出てきた三つ）"),
    Req("s6_ends_imperative", "書き方", "⑥の本文", "1", "⑥全体に掛かる一つの述語",
        "-", "命令法で締めていないこと", "較正"),
    Req("s6_contains_promise", "書き方", "⑥の本文", "1", "同上", "-", "約束法を使っていないこと", "較正"),
    Req("s6_recasts_unit", "書き方", "⑥における②の単位の扱い", "1", "単位が一つだから（s2_unit）",
        "-", "換算したかの申告。併記でも真", "導出",
        "衝突しない（定義域が交わらない。第13.5b版に対で見るようにして出てきた三つ）"),
    Req("s6_kappa", "基準", "最終裁定点の κ_n", "n", "", "-",
        "κ_n に挙がっている基準を、その数だけ配列で挙げること（第12.5b版）", "導出"),
    Req("s6_coverage_full", "被覆", "④で数えた量", "n", "", "-",
        "④の量ごとに、提案が全部消すかを申告", "導出"),
    Req("s6_coverage_disclosed", "被覆", "④で数えた量", "n", "", "-",
        "全部でないなら、どこまでかを数で書いたか", "導出"),
    Req("s6_coverage_subset", "被覆", "④で数えた量", "n", "", "-",
        "消す集合が④の集合に含まれるか", "導出"),
    Req("s6_kappa_type", "量の型", "⑥に置いた量", "n", "", "-",
        "量ごとに stock か flow か（R14 は④の周期と突き合わせる）", "導出"),
    Req("s6_realize", "行為", "浮いた分を減らす費目", "n", "", "-",
        "〈誰が・いつ・どの費目〉の三つ組を、費目の数だけ（A24・N₃）", "導出"),
    Req("s6_decide_date", "日付", "⑥が示す決定が締まる日", "1",
        "決定は一点（④からの逆算＝決定期限と比べる。A37b）", "-",
        "ISO 形式で、今日以降かつ決定期限以前であること（A37）", "導出",
        "着手日と対（決定→LT→着手の順で、競合しない）"),
    Req("s6_start_date", "日付", "⑥が示す着手日", "1",
        "着手は一点。決定日とは別の担体である（A37。旧版は一つの欄が両方を指していた）",
        "-", "ISO 形式で、決定日 ＋ LT_months 以降であること（A37）", "導出",
        "決定日と対（決定→LT→着手の順で、競合しない）"),
    Req("s6_self_check", "書き方", "⑤で他手段を落とした条件", "1",
        "⑤の条件集合全体に掛かる一つの述語（A14）", "-", "自社案にも当てて確かめたか", "導出",
        "衝突しない（定義域が交わらない。第13.5b版に対で見るようにして出てきた三つ）"),
    Req("s5_denies_own", "買い手の既承認", "Γ^own", "n", "", "-",
        "⑤が否定してしまっている既承認を挙げる。無ければ空（R17 の ∃）", "導出"),
    # 第14.3版：`s6_kappa_by_seat` と `s6_quantity_sources` の Req をここから外した。
    # **欄は消していない**（`Declared` に残り、旧走行の突合で現に読む）。外したのは
    # 「生成器に要求する」という位置づけだけで、`s6_quantities` の五つ組が両方を含む。
    # 残していたために (a) `N6_VALUE_SCALAR` が2件出続け、(b) `reqs_not_in_gen_schema` が
    # 「スキーマに無い」と名指しし続けていた ―― どちらも**吸収済みの欄への誤報**である。
    # → `REQ_RETIRED` へ。VS Code 第14.1版 §17 #4 の答え。
    Req("s6_omitted_blocks", "必須要素", "⑥に点灯した必須要素", "n", "", "-",
        "書けなかった要素を挙げる。空なら全部書いた（A27）", "導出"),
    Req("s6_to_sales", "申し送り", "自分で確定できなかった数字と判断", "n", "", "-",
        "営業が読んで動ける言葉で列挙。無ければ空（A28）", "導出"),
    # N₄′（第13.5b版）。s6_kappa_by_seat の担体を広げたもの。両方が同じ担体に掛かるので、
    # 強さは新欄を上に置く（衝突したら五つ組が勝つ）＝ N6_ENTRENCH_TIE を出させないため。
    Req("s6_quantities", "量", "資料を読む座席", "n", "", "n",
        "座席ごとに〈基準・払う・戻る・分母・出所〉を置く。"
        "払うと戻るは同じ単位でなければ並べられない（N₄′・R20）", "導出＋"),
    Req("s6_table_rows", "形式", "⑥に置いた表", "1",
        "表の行数は一つの数である（表そのものは列で分かれているので連結が起きない）",
        "-", "字数の判定から表を外すための数。表を使わなければ 0（第13.4版）", "較正"),
    # A45／A45b／A45c（第13.8版）：層(i) の算術。担体は〈価格〉で、量とは別に立てる ――
    # 量（s6_quantities）は**座席ごと**に走るが、価格は提案に一つしかない。
    Req("s6_price_low", "価格", "本提案", "1",
        "一つの提案が提示する金額の下限は一つ（複数あるなら提案が複数）",
        "-", "金額として読める文字列。⊥ なら A45_PRICE_UNDECLARED", "導出"),
    Req("s6_price_high", "価格", "本提案", "1",
        "同上。単一価格なら下限と同値を置く", "-",
        "上限÷下限が閾値以内（A45）。閾値は較正値なので未較正業界では降格", "較正",
        "下限が先に決まる。上限は下限との比でしか判定されない"),
    Req("s6_price_unit", "価格", "本提案", "1",
        "金額の単位は提案に一つ（内訳が別単位なら内訳側で申告する）",
        "-", "値の中に単位が混ざっていないこと（N₄′・R20_UNIT_IN_VALUE と同型）", "導出",
        "単位は下限・上限の読み方を決めるので、両者より先に効く"),
    Req("s6_price_items", "価格", "価格を構成する費目", "n", "", "-",
        "内訳が在り、和が総額に一致する（A45b。一致しないのは Π₁ の無矛盾に反する）", "導出＋"),
    Req("s2_asks_possession", "問いの向き", "②の問い", "1",
        "②は①を別の単位で数え直す一つの段であり、問いの向きも一つ（A47）",
        "-", "False であること。買い手の保有ではなく単位に向ける", "導出"),
    Req("s5_disclaimers", "断り", "この紙が否定しないと断った対象", "n", "", "-",
        "同じ対象への断りは1回まで。二度言うと否定になる（A46・R17 への過剰適応）", "導出"),
    Req("s6_price_tiers", "価格", "価格の階層（期間・数量）", "n", "", "-",
        "単位あたり価格が数量に対して単調非増加（A45c）。逆行は買い手が必ず検算する", "導出",
        "本提案の金額（s6_price_low/high）とは衝突しない。**階層は選択肢の一覧であって "
        "本提案の金額ではない** ―― 提示するのは階層のうち一つで、その一つが下限・上限になる。"
        "監査が同順位の対として拾ったので、衝突しない理由をここに書く（第13.8版）"),
)

# 廃止した欄（A24 で三つ組へ畳んだ。監査の対象外）
# ══════════════════════════════════════════ N₆ 追補（第14版）：**担体は一つ**
# 第12版以降に出た52件を型で数えたら、**最大の型が「一つの語／欄が二つの担体を持つ」8件**だった
# （A37・A37b・A41・A41b・A47・A48・A48b・A49）。しかも直近5版で連続して出ている。
#
# 第8版の規律 ―― **同じ誤りが4回出たものは規則ではなく型である** ―― の二度目の適用。
# 命題を足しても再発する。**記法で書けなくする。**
#
#   N₆ の四つ組 ⟨担体, 定義域, 充足条件, 強さ⟩ に、次の一行を足す。
#   **一つの記号（欄名・語・記法）は、一つの担体しか指してはならない。**
#
# 二つ指すなら、**書き分けを明記する**（`distinct`）。空なら監査が落とす。
# `Req.yields_to`（同順位の衝突に順序を書く）とまったく同じ形である。

class Sym(NamedTuple):
    sym: str          # 記号・欄名・語
    means: str        # 何を指すか
    carrier: str      # 担体
    where: str        # どこで使うか
    distinct: str = ""   # 同じ記号が他にもあるときの書き分け。空なら監査が落とす


GLOSSARY: Tuple[Sym, ...] = (
    # ── 解決済み（欄を割った。8件の型5がここに畳まれる）
    Sym("s6_decide_date", "決定が締まる日", "日付", "⑥", "A37 で s6_start_date から割った"),
    Sym("s6_start_date", "実際に動き出す日", "日付", "⑥", "A37 で欄を割った"),
    Sym("LT_months", "決定→着手の月数", "期間", "ν",
        "A37b。〈着手→境界〉ではない。effective_LT と連続区間になるのはこの読みだけ"),
    Sym("decide_deadline", "実効の決定期限 min(逆算, 窓)", "日付", "決定表",
        "A41b で decide_deadline_tau と割った。⑥を縛るのはこちら"),
    Sym("decide_deadline_tau", "④からの逆算のみ", "日付", "決定表",
        "A41b。④に出してよいのはこちらだけ（窓は買い手の内側なので出せない）"),
    Sym("τ 項", "④の〈今やる理由〉の担体", "時間", "④",
        "A41。同じ項が〈決定の窓〉でもある場合は decision_gates が別に持つ"),
    Sym("decision_gates", "決定が物理的に締まりうる窓", "時間", "⑥",
        "A41。④には出さない。⑥の決定日と着手日を縛る"),
    Sym("②の問い", "単位の置き換え", "単位", "②",
        "A47。〈買い手の保有〉を問う形ではない。s2_asks_possession は False であること"),
    Sym("pay_source", "払う側の量の出所", "出所", "⑥",
        "A49 で source から割った"),
    Sym("ret_source", "戻る側の量の出所", "出所", "⑥",
        "A49 で割った。式なら coef_source が別に要る"),
    # ── A48b・A48：語が重なっていたので、書き分けを決めた（第14版）
    Sym("ν", "入力の記録そのもの（class Nu）", "入力", "全体",
        "A48b。**入力は ν と書く。**検証時点は ν_v と書き分ける。"
        "コードは後方互換のため `Nu` / `Product.nu` のままで、"
        "**読み口は `nu_of()` 一箇所に限る**（直接 `n.A` を読まない）"),
    Sym("ν_v", "検証時点（Nelson / Darby-Karni の三分類）", "商材座標", "商材",
        "A48b。旧 `Nu.A` と `Product.nu` の二重の真実は `nu_of()` が座標側を正として解いた"),
    Sym("軸", "記法が型を与えるもの（入力ν・τ・J・Σ）", "型経由", "資料",
        "A48。**〈軸〉と呼ぶのはこちらだけ。**型検査が効く"),
    Sym("座標", "原理／文献が値域を直接与えるもの（λ・ε・商材座標の7成分）", "直列挙", "資料",
        "A48。**〈座標〉と呼ぶ。**記法を通らないので型検査が効かず、列挙照合だけ"),
)


def audit_symbols() -> List[Judgment]:
    """N₆ 追補：**一つの記号は一つの担体しか指してはならない。**

    二つ指すなら書き分けを `distinct` に書く。書いていなければ落とす。
    **これで9件目の〈二つの担体〉が書けなくなる** ―― 記号を足すときに、
    既に在る記号と衝突していれば、書き分けを書くまで監査が通らない。
    """
    out: List[Judgment] = []
    by_sym: Dict[str, List[Sym]] = {}
    for x in GLOSSARY:
        by_sym.setdefault(x.sym, []).append(x)
    for sym, xs in sorted(by_sym.items()):
        if len(xs) < 2:
            continue
        carriers = sorted({x.carrier for x in xs})
        if any(not x.distinct.strip() for x in xs):
            out.append(Judgment("N6_SYMBOL_AMBIGUOUS",
                                f"{sym} が {len(xs)} つの担体を指す：{'／'.join(carriers)}"))
    return out


# 退役した申告欄 ―― **欄は `Declared` に残す**（旧走行を読むため）が、要求としては挙げない。
# 生成器に求めないので、生成スキーマ（`wf_gen*.js`）に無くても配管の欠落ではない。
#   s6_realize_*        → s6_realize（三つ組）が吸収（A24）
#   s6_kappa_by_seat    → s6_quantities の五つ組が基準を含む（N₄′・第13.5b版）
#   s6_quantity_sources → 同・出所を含む（A28／A49 で pay_source・ret_source に割った）
REQ_RETIRED = ("s6_realize_actor", "s6_realize_date", "s6_realize_account",
               "s6_kappa_by_seat", "s6_quantity_sources")

# A57（第14.4版）：**退役には前提条件がある。**
# 退役した欄の〈読み手〉が一つでも橋を通らずに残っていると、その検査は
# 新しい形の申告で**構造的に出なくなる**。欄の意味が吸収済みであることと、
# コードの読み手が全部移っていることは、別の事実である。
#   退役した欄 → その欄の代わりに読むべきもの（橋の関数名か、新しい欄名）
RETIRED_BRIDGE: Dict[str, Tuple[str, ...]] = {
    "s6_kappa_by_seat":    ("quantities_by_seat", "s6_quantities"),
    "s6_quantity_sources": ("quantities_by_seat", "s6_quantities"),
    "s6_realize_actor":    ("s6_realize",),
    "s6_realize_date":     ("s6_realize",),
    "s6_realize_account":  ("s6_realize",),
}
# 橋そのもの。ここは旧欄を生で読んでよい（読むのが仕事）
BRIDGE_FUNCS = ("quantities_by_seat", "audit_retired_reads")

SEQ_HINTS = ("Tuple", "Dict", "List", "Sequence", "object")


def audit_retired_reads(src: Optional[str] = None) -> List[Judgment]:
    """退役した欄を、橋を通さずに読んでいる関数を名指しする。**A57。**

    第14.3版で `s6_kappa_by_seat`／`s6_quantity_sources` を `REQ_RETIRED` へ移したとき、
    「欄の意味は `s6_quantities` に吸収済みか」だけを見て、**読み手を数えなかった。**
    3つの読み手のうち2つ（`check_chain`・`check_quantity_sources`）は橋を通っていたが、
    `check_seat_words` だけが旧欄を生で読んでいて、`A23_SEAT_WORD_ABSENT` が死んでいた。

    **見つけたのは VS Code で、二つの計器のどちらにも映らない位置にあった** ――
    `audit_model.py` (6) では旧走行で発火済みなので「出たコード」の側に入り、
    `triage_codes.py` では関数が呼ばれているので (c) にも (b) にも載らない。
    第14.3版に書いた「**その検査を通す入力を1件でも作れるか**」を当てて初めて出た。

    規律：**退役させる前に、この監査を 0 にすること。**順序は
    「読み手を全部橋へ移す → `REQ_RETIRED` へ入れる」であって、逆ではない。

    `src` に原文を渡せば、その原文を見る（**0 を返す監査は、0 を返さない入力を
    1件見せるまで閉じたと言えない** ―― 回帰で対照を作るための口）。
    """
    import ast
    import inspect
    import sys
    out: List[Judgment] = []
    try:
        tree = ast.parse(src if src is not None else inspect.getsource(sys.modules[__name__]))
    except (OSError, TypeError, SyntaxError):   # 対話環境などで原文が取れないとき
        return out
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        if fn.name in BRIDGE_FUNCS:
            continue
        names = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        for field in REQ_RETIRED:
            if field not in names:
                continue
            if any(b in names for b in RETIRED_BRIDGE.get(field, ())):
                continue                # 旧欄も見るが、新しい側も見ている＝正しく畳めている
            out.append(Judgment("A57_RETIRED_READ_UNBRIDGED", f"{fn.name} が {field} を生で読む"))
    return out


def audit_requirements() -> List[Judgment]:
    """要求の四つ組が埋まっているかを機械で見る。**型1 と型4 をまとめて捕まえる監査。**

    落ちるもの
      N6_CARD_UNJUSTIFIED   濃度1と置いたのに、なぜ1でよいかが書かれていない
      N6_FIELD_SCALAR       定義域の濃度が n なのに、宣言欄がスカラーで作られている（＝型1）
      N6_VALUE_SCALAR       写像欄の値が複数ありうるのに、値がスカラー（＝型1 の写像版・A30）
      N6_REQ_MISSING        Declared に欄があるのに、要求として書かれていない
      N6_SATISFY_MISSING    充足条件が空（＝A31 の形）
      N6_ENTRENCH_TIE       同じ担体に掛かる要求の強さが同じで、衝突時の順序が決まらない
    """
    import dataclasses
    j: List[Judgment] = []
    types = {f.name: (f.type if isinstance(f.type, str) else str(f.type))
             for f in dataclasses.fields(Declared)}
    seen = set()
    for r in REQS:
        if r.card not in ("1", "n"):
            j.append(Judgment("N6_CARD_UNKNOWN", f"{r.field}={r.card}")); continue
        if r.card == "1" and not r.why1.strip():
            j.append(Judgment("N6_CARD_UNJUSTIFIED", f"{r.field} 担体={r.carrier} 定義域={r.domain}"))
        if not r.satisfy.strip():
            j.append(Judgment("N6_SATISFY_MISSING", str(r.field)))
        if r.field:
            seen.add(r.field)
            t = types.get(r.field, "")
            is_seq = any(w in t for w in SEQ_HINTS)
            if r.card == "n" and not is_seq:
                j.append(Judgment("N6_FIELD_SCALAR", f"{r.field}:{t} 定義域={r.domain}"))
            if r.value_card == "n":
                inner = t[t.find("Dict[") + 5:t.rfind("]")] if "Dict[" in t else ""
                vt = inner.split(",", 1)[1].strip() if "," in inner else ""
                if not any(w in vt for w in SEQ_HINTS):
                    j.append(Judgment("N6_VALUE_SCALAR", f"{r.field} 値={vt or t} 担体={r.carrier}"))
    for name in types:
        if name not in seen and name not in REQ_RETIRED:
            j.append(Judgment("N6_REQ_MISSING", name))
    by_carrier: Dict[str, List[Req]] = {}
    for r in REQS:
        by_carrier.setdefault(r.carrier, []).append(r)
    # 第13.5b版：ここは**集合全体**を見ていたので、担体に3件目を足して強さを1段変えるだけで
    # 判定が消えた。同順位の**対**が残っていれば衝突は残っている。対で見る。
    # （N₄′ を足したとき、既にあった A29 の同順位対が黙って消えた ―― 監査自身の型3。）
    for carrier, rs in by_carrier.items():
        unresolved = [r for r in rs if not r.yields_to.strip()]
        for i, a in enumerate(unresolved):
            for b in unresolved[i + 1:]:
                if a.entrench == b.entrench and a.domain != b.domain:
                    j.append(Judgment("N6_ENTRENCH_TIE",
                                      f"担体={carrier} 強さ={a.entrench} "
                                      f"定義域={sorted((a.domain, b.domain))}"))
    return j
