# -*- coding: utf-8 -*-
"""第8版 ―― 新業界8セル。学校法人／小売チェーン。

設計の狙いがひとつある。第8版 §5 は次のアノマリーの位置を予測している——
「$j_n$ には通ったが中間座席で止まった」型が、$\\mathrm{rk}(\\kappa_k)$ が非単調な $J$ で選択的に出る。
E1（私立大学）の座席は 実務性(0) → 説明可能性(3) → 財源(2) で**非単調**にしてある。
R1・R2・E2 は単調（0→1→2 など）で対照になる。予測が外れれば §5 は反証される。

業界   E: 学校法人      R: 小売（食品スーパー）
セグ   1: 大規模・合議  2: オーナー系・単独決裁
商材   P1: 広告・募集／販促支援      P2: ITソリューション（需要予測・要員配置）
"""
import json
from datetime import date
from sales_logic import (Seat, Veto, Executor, TauItem, Mi, Seller, Nu, Scope, compile_deal)

TODAY = date(2026, 8, 6)

# ───────────────────────────────────────────── 売り手
S_AD = Seller(
    registrations=set(), registration_expiry=None,
    channel_total=0.0, funnel_present=False, funnel_yield=None,
    upstream_approvals=2, upstream_lead_days=(20, 45),
    named_cases=[
        {"実名": "△△学院大学", "業態": "私立大学", "規模": "学生3000〜8000名", "商圏": "関西"},
        {"実名": "○○ストア株式会社", "業態": "食品スーパー", "規模": "20〜49店舗", "商圏": "関西"},
    ],
    liability_scope=False, price_disclosure=True,
)
S_IT = Seller(
    registrations={"ISMS認証（ISO/IEC27001）", "個人情報保護の第三者認証"},
    registration_expiry=date(2028, 3, 31),
    channel_total=0.0, funnel_present=False, funnel_yield=None,
    upstream_approvals=4, upstream_lead_days=(30, 75),
    named_cases=[
        {"実名": "□□女子大学", "業態": "私立大学", "規模": "学生3000〜8000名", "商圏": "関西"},
        {"実名": "◇◇フーズ株式会社", "業態": "食品スーパー", "規模": "20〜49店舗", "商圏": "関西"},
    ],
    liability_scope=True, price_disclosure=False,
)

# ───────────────────────────────────────────── 座席（form は κ_n 側の様式にある語）
# E1：実務性(0) → 説明可能性(3) → 財源(2)  ← 非単調。ここが今回の試験対象
J_E1 = [
    Seat("入試広報課長", frozenset({"実務性"}), "現場で回るか", "単独", "社内", True,
         frozenset({"出願件数", "オープンキャンパス動員", "広報予算執行"})),
    Seat("学部長会", frozenset({"説明可能性"}), "教学の理念と整合するか", "合議", "社内", True,
         frozenset({"教育の質保証", "アドミッションポリシー", "定員充足率"})),
    Seat("理事会", frozenset({"財源"}), "帰属収支差額", "合議", "社内", False,
         frozenset({"帰属収支差額", "学生生徒等納付金", "予算科目"})),
]
# E2：実務性(0) → 財源(2)・価格(1)  ← 単調
J_E2 = [
    Seat("教務主任", frozenset({"実務性"}), "現場で回るか", "単独", "社内", True,
         frozenset({"担任工数", "募集説明会"})),
    Seat("理事長", frozenset({"財源", "価格"}), "手元資金", "単独", "社内", True,
         frozenset({"納付金収入", "手元資金", "支払"})),
]
# R1：実務性(0) → 価格(1) → 財源(2)  ← 単調
J_R1 = [
    Seat("店舗運営部", frozenset({"実務性"}), "店で回るか", "単独", "社内", True,
         frozenset({"人時売上高", "作業時間", "発注精度"})),
    Seat("商品本部バイヤー", frozenset({"価格"}), "原価と条件", "単独", "社内", True,
         frozenset({"原価率", "粗利率", "取引条件"})),
    Seat("社長", frozenset({"財源"}), "営業利益", "単独", "社内", False,
         frozenset({"営業利益", "販管費", "設備投資枠"})),
]
# R2：実務性(0) → 価格(1)・財源(2)  ← 単調
J_R2 = [
    Seat("店長", frozenset({"実務性"}), "店で回るか", "単独", "社内", True,
         frozenset({"作業時間", "廃棄率"})),
    Seat("社長", frozenset({"価格", "財源"}), "手元資金", "単独", "社内", True,
         frozenset({"仕入原価", "手元資金", "粗利"})),
]
V_R1 = [Veto("労働組合")]

W_E1 = [Executor("入試広報課長", frozenset({"広報外注費", "媒体費"})),
        Executor("法人事務局", frozenset({"人件費（専任）", "業務委託費"}))]
W_E2 = [Executor("理事長", frozenset({"人件費（専任）", "業務委託費", "媒体費"}))]
W_R1 = [Executor("店舗運営部", frozenset({"パート人時", "販促費"})),
        Executor("商品本部バイヤー", frozenset({"仕入原価", "廃棄"}))]
W_R2 = [Executor("社長", frozenset({"パート人時", "仕入原価", "販促費", "廃棄"}))]

CTX_E1 = {"業態": "私立大学", "規模": "学生3000〜8000名", "商圏": "関西", "所轄庁": "文部科学大臣"}
CTX_E2 = {"業態": "専修学校", "規模": "学生300〜999名", "商圏": "関西", "所轄庁": "都道府県知事"}
CTX_R1 = {"業態": "食品スーパー", "規模": "20〜49店舗", "商圏": "関西"}
CTX_R2 = {"業態": "食品スーパー", "規模": "1〜9店舗", "商圏": "関西"}

UP_E1 = frozenset({"文部科学省", "認証評価機関"})
UP_E2 = frozenset({"都道府県私学担当課"})
UP_R1 = frozenset({"主要卸（一次問屋）"})
UP_R2 = frozenset({"主要卸（一次問屋）", "ボランタリーチェーン本部"})

# ───────────────────────────────────────────── τ
SC_UNIV = Scope(keys=(("業態", "私立大学"),))
SC_SENSHU = Scope(keys=(("業態", "専修学校"),))
SC_SUPER = Scope(keys=(("業態", "食品スーパー"),))
SC_ANY = Scope()

TAU_NYUSHI = TauItem("A", date(2027, 11, 1), "自然・需要", "既知",
                     q="出願受付開始までに接触できていない高校の数", q_kappa="実務性", q_recast=True,
                     q_source="買い手データ", q_low=40, q_high=70, scope=SC_UNIV,
                     q_receipt="2026-07-15 入試広報課より受領。高校訪問記録（2025年度）から未接触校を抽出")
TAU_HYOKA = TauItem("Ec", date(2027, 6, 30), "契約", "未知",
                    q="認証評価の受審までに整えるべき根拠資料の点数", q_kappa="説明可能性", q_recast=True,
                    q_source="買い手データ", q_low=90, q_high=140, scope=SC_UNIV,
                    binders=("認証評価機関",),
                    q_receipt="2026-07-15 法人事務局より受領。前回受審時の指摘事項一覧")
TAU_SENSHU = TauItem("A", date(2027, 4, 1), "公的暦", "未知",
                     q="次年度の募集で埋まっていない定員", q_kappa="財源",
                     q_source="公開統計", q_low=30, q_high=60, scope=SC_SENSHU)
TAU_TANA = TauItem("B", date(2027, 3, 1), "自然・需要", "既知",
                   q="棚替え時に発生する売場の作業時間", q_kappa="実務性", q_recast=True,
                   q_source="買い手データ", q_low=900, q_high=1400, wait_months=6, scope=SC_SUPER,
                   q_receipt="2026-07-28 店舗運営部より受領。全店の作業割当表（直近2回の棚替え週）")
TAU_KEIYAKU = TauItem("A", date(2027, 9, 30), "契約", "未知",
                      q="現行の帳合契約で固定されている取引条件の項目数", q_kappa="価格", q_recast=True,
                      q_source="買い手データ", q_low=12, q_high=20, scope=SC_SUPER,
                      binders=("主要卸（一次問屋）",),
                      q_receipt="2026-07-28 商品本部より受領。帳合契約書の条件一覧")
TAU_KOUREI = TauItem("D", date(2027, 4, 1), "公的暦", "既知",
                     q="商圏人口に占める65歳以上の割合（％）", q_kappa="実務性", q_recast=True,
                     q_source="公開統計", q_low=31, q_high=37, scope=SC_ANY)

# ───────────────────────────────────────────── M
M0_E = Mi("現状のまま自前の広報でしのぐ", "M0")
M0_R = Mi("現状のまま人海戦術でしのぐ", "M0")
M_NAISEI_E = Mi("職員を増やして内製する", "内製", frozenset({"D5"}), ("D5",))
M_NAISEI_R = Mi("パートを増やして内製する", "内製", frozenset({"D5"}), ("D5",))
M_GAICHU_E = Mi("現在の広告代理店に追加発注する", "既存外注", frozenset({"D2"}), ("D2",))
M_GAICHU_R = Mi("現在の卸の販促支援を使う", "既存外注", frozenset({"D2", "D6c"}), ("D2",),
                binders=(("D6c", "主要卸（一次問屋）"),))
M_KYOU_AD = Mi("他社の広告会社", "競合", frozenset({"D7a", "D7d"}), ("D7a",))
M_KYOU_IT = Mi("他社のシステム", "競合", frozenset({"D7a", "D7b", "D7c"}), ("D7a",))

PRE_1 = {"①": "訪問時のヒアリングで、現在の体制・件数・工数は既に双方で確認済み"}
PRE_4 = {"①": "訪問時のヒアリングで、現在の体制・件数・工数は既に双方で確認済み",
         "②": "買い手自身が『今の数え方では出てこない負荷がある』と先に述べている",
         "③": "買い手がその現象を自社の言葉で既に名指ししている",
         "④": "買い手は他社の提案も受けており、今期中に決める必要を既に認めている"}

CELLS = [
    dict(id="E1-P1", 業界="学校法人", セグメント="私立大学（合議・非単調な座席列）", 商材="広告・募集支援",
         seller="ad", nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="年次以下",
             S3=False, C_move="すぐ試せる", J=J_E1, V=(), W=W_E1, procedural=False, downward=True,
             E_reader="手段を知らない", E_judge="手段を知らない",
             tau=[TAU_NYUSHI, TAU_HYOKA], M=[M0_E, M_NAISEI_E, M_GAICHU_E, M_KYOU_AD],
             LT_months=3, buyer_context=CTX_E1, upstream=UP_E1, gamma_pre=PRE_1)),
    dict(id="E1-P2", 業界="学校法人", セグメント="私立大学（合議・非単調な座席列）", 商材="ITソリューション",
         seller="it", nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発",
             S3=False, C_move="大仕事", J=J_E1, V=(), W=W_E1, procedural=False, downward=True,
             E_reader="比較検討中", E_judge="比較検討中",
             tau=[TAU_HYOKA, TAU_NYUSHI], M=[M0_E, M_NAISEI_E, M_GAICHU_E, M_KYOU_IT],
             LT_months=6, buyer_context=CTX_E1, upstream=UP_E1, gamma_pre=PRE_4)),
    dict(id="E2-P1", 業界="学校法人", セグメント="専修学校（オーナー系・単独決裁）", 商材="広告・募集支援",
         seller="ad", nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="年次以下",
             S3=False, C_move="すぐ試せる", J=J_E2, V=(), W=W_E2, procedural=False, downward=False,
             E_reader="困っていない", E_judge="困っていない",
             tau=[TAU_SENSHU], M=[M0_E, M_NAISEI_E, M_GAICHU_E, M_KYOU_AD],
             LT_months=3, buyer_context=CTX_E2, upstream=UP_E2)),
    dict(id="E2-P2", 業界="学校法人", セグメント="専修学校（オーナー系・単独決裁）", 商材="ITソリューション",
         seller="it", nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発",
             S3=False, C_move="大仕事", J=J_E2, V=(), W=W_E2, procedural=False, downward=False,
             E_reader="手段を知らない", E_judge="手段を知らない",
             tau=[TAU_SENSHU], M=[M0_E, M_NAISEI_E, M_GAICHU_E, M_KYOU_IT],
             LT_months=6, buyer_context=CTX_E2, upstream=UP_E2, gamma_pre=PRE_1)),
    dict(id="R1-P1", 業界="小売（食品スーパー）", セグメント="チェーン本部（分業・単調な座席列）", 商材="広告・販促支援",
         seller="ad", nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="四半期〜月次",
             S3=False, C_move="すぐ試せる", J=J_R1, V=V_R1, W=W_R1, procedural=False, downward=True,
             E_reader="手段を知らない", E_judge="手段を知らない",
             tau=[TAU_TANA, TAU_KOUREI], M=[M0_R, M_NAISEI_R, M_GAICHU_R, M_KYOU_AD],
             LT_months=3, buyer_context=CTX_R1, upstream=UP_R1, gamma_pre=PRE_1)),
    dict(id="R1-P2", 業界="小売（食品スーパー）", セグメント="チェーン本部（分業・単調な座席列）", 商材="ITソリューション",
         seller="it", nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発",
             S3=False, C_move="大仕事", J=J_R1, V=V_R1, W=W_R1, procedural=False, downward=True,
             E_reader="比較検討中", E_judge="比較検討中",
             tau=[TAU_KEIYAKU, TAU_TANA, TAU_KOUREI], M=[M0_R, M_NAISEI_R, M_GAICHU_R, M_KYOU_IT],
             LT_months=6, buyer_context=CTX_R1, upstream=UP_R1, gamma_pre=PRE_4)),
    dict(id="R2-P1", 業界="小売（食品スーパー）", セグメント="地場単独店（社長直轄）", 商材="広告・販促支援",
         seller="ad", nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="四半期〜月次",
             S3=False, C_move="すぐ試せる", J=J_R2, V=(), W=W_R2, procedural=False, downward=False,
             E_reader="困っていない", E_judge="困っていない",
             tau=[TAU_TANA, TAU_KOUREI], M=[M0_R, M_NAISEI_R, M_GAICHU_R, M_KYOU_AD],
             LT_months=3, buyer_context=CTX_R2, upstream=UP_R2)),
    dict(id="R2-P2", 業界="小売（食品スーパー）", セグメント="地場単独店（社長直轄）", 商材="ITソリューション",
         seller="it", nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発",
             S3=False, C_move="大仕事", J=J_R2, V=(), W=W_R2, procedural=False, downward=False,
             E_reader="手段を知らない", E_judge="手段を知らない",
             tau=[TAU_TANA, TAU_KOUREI], M=[M0_R, M_NAISEI_R, M_GAICHU_R, M_KYOU_IT],
             LT_months=6, buyer_context=CTX_R2, upstream=UP_R2, gamma_pre=PRE_1)),
]
SELLERS = {"ad": S_AD, "it": S_IT}

RK = {"実務性": 0, "価格": 1, "財源": 2, "説明可能性": 3, "政治的可視性": 4}


def rank_path(nu):
    return [min(RK[k] for k in s.kappa) for s in nu.J]


def monotone(nu):
    p = rank_path(nu)
    return all(p[i] <= p[i + 1] for i in range(len(p) - 1))


def run(dump="decisions8_v8.json"):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id", "業界", "セグメント", "商材")}
        rec.update({k: d.get(k) for k in
                    ("generate", "sigma", "sigma_by", "j_star", "kappa_n", "form_n", "tau_ok",
                     "delta", "five_mentions", "d7_basis", "blocks", "rules", "executors",
                     "start_deadline", "talk_guide", "llm_calls")})
        rec["findings"] = [{"code": f.code, "level": f.level, "ref": f.ref,
                            "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]]
        rec["needs_judgment"] = [{"code": j.code, "ref": j.ref,
                                  "msg": msgs["judgments"].get(j.code, j.code)} for j in d["needs_judgment"]]
        rec["seats"] = [{"name": s.name, "kappa": sorted(s.kappa), "chi": s.chi, "gamma": s.gamma,
                         "reads": s.reads, "form": sorted(s.form)} for s in c["nu"].J]
        rec["veto"] = [v.name for v in c["nu"].V]
        rec["gamma_own"] = c["nu"].gamma_pre
        rec["rank_path"] = rank_path(c["nu"])
        rec["monotone"] = monotone(c["nu"])
        out.append(rec)
    json.dump(out, open(dump, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in out:
        st = [f"{f['code']}({f['ref']})" for f in r["findings"] if f["level"] == "stop"]
        rj = [f["code"] for f in r["findings"] if f["level"] in ("reject", "demote")]
        print(f"{r['id']:6s} {'生成可' if r['generate'] else '★不成立'} Σ={''.join(r['sigma'] or [])}"
              f" κ_n={r['kappa_n']} 階数={r['rank_path']}{'' if r['monotone'] else ' ←非単調'}"
              f" j*={r['j_star']}")
        if st: print("        停止", st)
        if rj: print("        棄却/降格", rj)
    print(f"\n生成可 {sum(1 for r in out if r['generate'])}/{len(out)}  "
          f"非単調セル {sum(1 for r in out if not r['monotone'])}/{len(out)}")
    return out


if __name__ == "__main__":
    run()
