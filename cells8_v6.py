# -*- coding: utf-8 -*-
"""第6版コアの回帰 ―― 食品・建設 8セルを、今回文言を生成したのと同じ設定のまま当てる。

目的はひとつ。**買い手が一行で落とした入力を、機械が生成前に止められるか。**
値は第5版の走行と同じもの（誤りもそのまま）。第6版で新設したフィールドだけを埋める。
"""
import json
from datetime import date
from sales_logic import (Seat, Veto, TauItem, Mi, Seller, Nu, Scope, compile_deal)

TODAY = date(2026, 8, 6)

# ───────────────────────────────────────────── 売り手マスタ
S_ROBOT = Seller(
    registrations={"ISO10218/ISO_TS15066 適合宣言書", "食品機械の衛生設計 適合証明"},
    registration_expiry=None,                 # ← 有効期限を持っていない（R7 D6a の実数②）
    channel_total=0.0, funnel_present=False, funnel_yield=None,
    upstream_approvals=3, upstream_lead_days=(45, 90),
    named_cases=[
        {"実名": "○○デリカ株式会社 第二工場", "業態": "惣菜・日配", "規模": "300〜999名", "商圏": "関東"},
        {"実名": "△△建設株式会社 ××作業所", "業態": "総合建設", "規模": "300〜999名", "商圏": "関東"},
    ],
    liability_scope=True, price_disclosure=False,
)
S_CONSULT = Seller(
    registrations=set(), registration_expiry=None,
    channel_total=0.0, funnel_present=False, funnel_yield=None,
    upstream_approvals=1, upstream_lead_days=None,   # ← 実測がない（R7 D6c の実数②）
    named_cases=[
        {"実名": "□□食品株式会社", "業態": "惣菜・日配", "規模": "100〜299名", "商圏": "関東"},
        {"実名": "◇◇工業株式会社", "業態": "専門工事", "規模": "100〜299名", "商圏": "関東"},
    ],
    liability_scope=False, price_disclosure=True,
)

# ───────────────────────────────────────────── 座席（form＝その座席の様式にある語）
J_F1 = [
    Seat("工場長", frozenset({"実務性"}), "現場の再現性", "単独", "社内", True,
         frozenset({"段取り工数", "応援伝票", "歩留まり"})),
    Seat("親会社 生産技術部", frozenset({"実務性", "説明可能性"}), "標準化との整合", "合議", "社外", True,
         frozenset({"標準作業", "製造間接費", "応援労務費"})),
    Seat("親会社 調達本部", frozenset({"価格"}), "相見積の規程", "合議", "社外", False,
         frozenset({"見積総額", "回収年数", "単価"})),
]
J_F2 = [
    Seat("製造部長", frozenset({"実務性"}), "現場の再現性", "単独", "社内", True,
         frozenset({"段取り", "歩留まり"})),
    Seat("社長", frozenset({"財源", "価格"}), "手元資金", "単独", "社内", True,
         frozenset({"手元資金", "支払", "借入"})),
]
J_K1 = [
    Seat("作業所長", frozenset({"実務性"}), "施工計画との整合", "単独", "社内", True,
         frozenset({"施工計画", "歩掛", "人工"})),
    Seat("本社 工務部", frozenset({"実務性", "説明可能性"}), "安全衛生・積算の整合", "合議", "社内", True,
         frozenset({"実行予算", "人工", "外注費"})),
    Seat("常務会", frozenset({"財源", "説明可能性"}), "完成工事総利益", "合議", "社内", False,
         frozenset({"完成工事総利益", "実行予算", "投資回収"})),
]
J_K2 = [
    Seat("工事課長", frozenset({"実務性"}), "常用の手間", "単独", "社内", True,
         frozenset({"出面", "常用"})),
    Seat("社長", frozenset({"価格"}), "常用単価と手元資金", "単独", "社内", True,
         frozenset({"常用単価", "手元資金", "人工"})),
]
V_K2 = [Veto("元請の安全衛生管理責任者")]

CTX_F1 = {"業態": "惣菜・日配", "規模": "300〜999名", "商圏": "関東", "系列": "大手食品グループ"}
CTX_F2 = {"業態": "惣菜・日配", "規模": "100〜299名", "商圏": "関東"}
CTX_K1 = {"業態": "総合建設", "規模": "300〜999名", "商圏": "関東", "所轄庁": "国土交通大臣許可"}
CTX_K2 = {"業態": "専門工事", "規模": "100〜299名", "商圏": "関東", "所轄庁": "都道府県知事許可"}

UP_F1 = frozenset({"親会社 生産技術部", "親会社 調達本部"})
UP_F2 = frozenset()                                   # オーナー系。上位者はいない
UP_K1 = frozenset({"発注者（官公庁）"})
UP_K2 = frozenset({"元請の安全衛生管理責任者", "元請"})
DOWN_K1 = frozenset({"協力会社", "元請"})              # ゼネコンは自らが元請

# ───────────────────────────────────────────── τ
SCOPE_SHELF = Scope(keys=(("業態", "惣菜・日配"),), applied_from=None)
SCOPE_HOJO = Scope(keys=(), applied_from=None)
SCOPE_KOUKI = Scope(keys=(), applied_from=None)
# ↓ 第5版の走行で使った「時間外の上限」。適用開始が過去である事実を初めて欄に書く
SCOPE_JOGEN_F = Scope(keys=(("業態", "惣菜・日配"),), applied_from=date(2020, 4, 1))
SCOPE_JOGEN_K = Scope(keys=(("業態", "総合建設"),), applied_from=date(2024, 4, 1))
SCOPE_JOGEN_K2 = Scope(keys=(("業態", "専門工事"),), applied_from=date(2024, 4, 1))


def tau_shelf(recast=True):
    return TauItem("B", date(2027, 3, 1), "自然・需要", "既知",
                   q="切替時に発生する増員工数（人日）", q_kappa="実務性", q_recast=recast,
                   q_source="買い手データ", q_low=180, q_high=260, wait_months=6,
                   scope=SCOPE_SHELF)


TAU_HOJO = TauItem("A", date(2027, 6, 30), "公的暦", "未知",
                   q="申請可能な設備投資の枠（円）", q_kappa="財源",
                   q_source="公開統計", q_low=6_000_000, q_high=10_000_000, scope=SCOPE_HOJO)
TAU_KOUKI_NG = TauItem("A", date(2027, 3, 31), "契約", "未知",
                       q="年度内に消化できない工期（日）", q_kappa="実務性",
                       q_source="公開統計", scope=SCOPE_KOUKI, binders=("発注者（官公庁）",))
TAU_SHUNKO = TauItem("C", date(2027, 6, 30), "契約", "未知",
                     q="竣工から逆算した着手期限までの残余（日）", q_kappa="実務性", q_recast=True,
                     q_source="買い手データ", q_low=40, q_high=70,
                     scope=SCOPE_KOUKI, binders=("発注者（官公庁）",))
TAU_SHUNKO_K2 = TauItem("C", date(2027, 6, 30), "契約", "未知",
                        q="竣工から逆算した着手期限までの残余（日）", q_kappa="実務性", q_recast=True,
                        q_source="買い手データ", q_low=40, q_high=70,
                        scope=SCOPE_KOUKI, binders=("元請",))
TAU_KOUREIKA = TauItem("D", date(2027, 4, 1), "公的暦", "既知",
                       q="55歳以上が占める登録技能者の割合（％）", q_kappa="実務性", q_recast=True,
                       q_source="公開統計", q_low=36, q_high=42, scope=Scope())
TAU_MOTOUKE = TauItem("Ec", date(2027, 1, 15), "契約", "未知",
                      q="元請の安全審査を通すまでの実測日数（日）", q_kappa="実務性", q_recast=True,
                      q_source="売り手データ", q_low=45, q_high=90,
                      scope=Scope(), binders=("元請", "元請の安全衛生管理責任者"))


def tau_jogen(scope):
    return TauItem("A", date(2027, 4, 1), "法令", "既知",
                   q="上限に達するまでに残っている時間外の枠（時間）", q_kappa="実務性", q_recast=True,
                   q_source="買い手データ", q_low=120, q_high=190, scope=scope)


# ───────────────────────────────────────────── M（拘束者つき）
M0_F = Mi("現状のまま人手で回す", "M0")
M0_K = Mi("現状のまま常用でしのぐ", "M0")
M_NAISEI = Mi("自社で増員して内製する", "内製", frozenset({"D5"}), ("D5",))
M_GAICHU_F1 = Mi("既存の人材派遣会社に増員を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",),
                 binder="親会社 調達本部")
M_GAICHU_F2 = Mi("既存の人材派遣会社に増員を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",),
                 binder="親会社")                      # ← F2 に親会社は実在しない
M_GAICHU_K1 = Mi("既存の協力会社に応援を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",),
                 binder="元請")                        # ← K1 自身が元請（向きが逆）
M_KYOUGOU_ROBOT = Mi("他社の省人化装置", "競合", frozenset({"D7a", "D7b"}), ("D7a",))
M_KYOUGOU_CONSULT = Mi("大手コンサルティングファーム", "競合", frozenset({"D7a", "D7d"}), ("D7a",))
M_MOTOUKE = Mi("元請が指定する工法・体制", "取引上位者の指定", frozenset({"D6c"}), ("D6c",),
               binder="元請")

PRE = {"①": "買い手は既に自社の要員・工数の実数を把握している（営業が聞き取り済み）"}

CELLS = [
    dict(id="F1-P1", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_shelf(), tau_jogen(SCOPE_JOGEN_F)],
               M=[M0_F, M_NAISEI, M_GAICHU_F1, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F1, upstream=UP_F1, gamma_pre=PRE)),
    dict(id="F1-P2", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="困っていない", E_judge="困っていない",
               tau=[tau_jogen(SCOPE_JOGEN_F), tau_shelf()],
               M=[M0_F, M_NAISEI, M_GAICHU_F1, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F1, upstream=UP_F1)),
    dict(id="F2-P1", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_F2, V=(), procedural=True, downward=False,
               E_reader="困っていない", E_judge="困っていない",
               tau=[TAU_HOJO, tau_shelf()],
               M=[M0_F, M_NAISEI, M_GAICHU_F2, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F2, upstream=UP_F2)),
    dict(id="F2-P2", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F2, V=(), procedural=False, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_jogen(SCOPE_JOGEN_F), tau_shelf()],
               M=[M0_F, M_NAISEI, M_GAICHU_F2, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F2, upstream=UP_F2, gamma_pre=PRE)),
    dict(id="K1-P1", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[TAU_KOUKI_NG, TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_GAICHU_K1, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K1, upstream=UP_K1, downstream=DOWN_K1,
               gamma_pre={s: "比較検討中のため、①〜④は既に成立している" for s in "①②③④"})),
    dict(id="K1-P2", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_jogen(SCOPE_JOGEN_K), TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_GAICHU_K1, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K1, upstream=UP_K1, downstream=DOWN_K1,
               gamma_pre=PRE)),
    dict(id="K2-P1", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_K2, V=V_K2, procedural=True, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_MOTOUKE, TAU_SHUNKO_K2, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_MOTOUKE, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K2, upstream=UP_K2, gamma_pre=PRE)),
    dict(id="K2-P2", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K2, V=V_K2, procedural=False, downward=False,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[tau_jogen(SCOPE_JOGEN_K2), TAU_MOTOUKE, TAU_SHUNKO_K2],
               M=[M0_K, M_NAISEI, M_MOTOUKE, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K2, upstream=UP_K2,
               gamma_pre={s: "比較検討中のため、①〜④は既に成立している" for s in "①②③④"})),
]
SELLERS = {"robot": S_ROBOT, "consult": S_CONSULT}


def run(dump="decisions8_v6.json"):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id", "業界", "セグメント", "商材")}
        rec.update({k: d.get(k) for k in
                    ("generate", "sigma", "sigma_by", "j_star", "kappa_n", "form_n",
                     "tau_ok", "delta", "five_mentions", "d7_basis", "blocks", "rules", "llm_calls")})
        rec["findings"] = [{"code": f.code, "level": f.level, "ref": f.ref,
                            "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]]
        rec["needs_judgment"] = [{"code": j.code, "ref": j.ref,
                                  "msg": msgs["judgments"].get(j.code, j.code)} for j in d["needs_judgment"]]
        out.append(rec)
    json.dump(out, open(dump, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in out:
        stops = [f"{f['code']}({f['ref']})" for f in r["findings"] if f["level"] == "stop"]
        rej = [f"{f['code']}" for f in r["findings"] if f["level"] == "reject"]
        print(f"{r['id']:7s} {'生成可' if r['generate'] else '★不成立'}  "
              f"Σ={''.join(r['sigma'] or [])}")
        if stops: print(f"          停止 {stops}")
        if rej:   print(f"          棄却 {rej}")
    print()
    print(f"生成可 {sum(1 for r in out if r['generate'])}/{len(out)}")
    return out


if __name__ == "__main__":
    run()
