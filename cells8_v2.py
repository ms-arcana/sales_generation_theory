# -*- coding: utf-8 -*-
"""第5版 形式系の実運用 ―― 新業界8セル

業界   F: 食品メーカー（惣菜・日配）      K: 建設・設備工事
セグ   1: 大手グループの生産子会社/中堅ゼネコン   2: オーナー系中堅/専門工事業（下請）
商材   P1: 協働ロボット＋ロボットハンド（省人化装置）   P2: 業務改革コンサルティング
"""
import json
from datetime import date
from sales_logic import (Seat, Veto, TauItem, Mi, Seller, Nu, compile_deal)

TODAY = date(2026, 8, 6)

# ───────────────────────────────────────────── 売り手マスタ
S_ROBOT = Seller(
    registrations={"ISO10218/ISO_TS15066 適合宣言書", "食品機械の衛生設計 適合証明"},
    channel_total=0.0, funnel_present=False,
    upstream_approvals=3,
    named_cases=[
        {"実名": "○○デリカ株式会社 第二工場", "業態": "惣菜・日配", "規模": "300〜999名", "商圏": "関東"},
        {"実名": "△△建設株式会社 ××作業所", "業態": "総合建設", "規模": "300〜999名", "商圏": "関東"},
    ],
    liability_scope=True, price_disclosure=False,
)
S_CONSULT = Seller(
    registrations=set(),
    channel_total=0.0, funnel_present=False,
    upstream_approvals=1,
    named_cases=[
        {"実名": "□□食品株式会社", "業態": "惣菜・日配", "規模": "100〜299名", "商圏": "関東"},
        {"実名": "◇◇工業株式会社", "業態": "専門工事", "規模": "100〜299名", "商圏": "関東"},
    ],
    liability_scope=False, price_disclosure=True,
)

# ───────────────────────────────────────────── 座席（J）
J_F1 = [  # 大手食品グループの生産子会社
    Seat("工場長", frozenset({"実務性"}), chi="現場の再現性", gamma="単独", omega="社内", reads=True),
    Seat("親会社 生産技術部", frozenset({"実務性", "説明可能性"}), chi="標準化との整合", gamma="合議", omega="社外", reads=True),
    Seat("親会社 調達本部", frozenset({"価格"}), chi="相見積の規程", gamma="合議", omega="社外", reads=False),
]
J_F2 = [  # オーナー系中堅食品
    Seat("製造部長", frozenset({"実務性"}), chi="現場の再現性", gamma="単独", omega="社内", reads=True),
    Seat("社長", frozenset({"財源", "価格"}), chi="手元資金", gamma="単独", omega="社内", reads=True),
]
J_K1 = [  # 中堅ゼネコン
    Seat("作業所長", frozenset({"実務性"}), chi="施工計画との整合", gamma="単独", omega="社内", reads=True),
    Seat("本社 工務部", frozenset({"実務性", "説明可能性"}), chi="安全衛生・積算の整合", gamma="合議", omega="社内", reads=True),
    Seat("常務会", frozenset({"財源", "説明可能性"}), chi="完成工事総利益", gamma="合議", omega="社内", reads=False),
]
J_K2 = [  # 専門工事業（下請）
    Seat("工事課長", frozenset({"実務性"}), chi="常用の手間", gamma="単独", omega="社内", reads=True),
    Seat("社長", frozenset({"価格"}), chi="常用単価と手元資金", gamma="単独", omega="社内", reads=True),
]
V_K2 = [Veto("元請の安全衛生管理責任者")]

CTX_F1 = {"業態": "惣菜・日配", "規模": "300〜999名", "商圏": "関東", "系列": "大手食品グループ"}
CTX_F2 = {"業態": "惣菜・日配", "規模": "100〜299名", "商圏": "関東"}
CTX_K1 = {"業態": "総合建設", "規模": "300〜999名", "商圏": "関東", "所轄庁": "国土交通大臣許可"}
CTX_K2 = {"業態": "専門工事", "規模": "100〜299名", "商圏": "関東", "所轄庁": "都道府県知事許可"}

# ───────────────────────────────────────────── τ（T軸）
def tau_food_shelf(recast: bool):
    """量販店の棚替え＝開扉。次の窓まで6か月待つ"""
    return TauItem("B", date(2027, 3, 1), "自然・需要", "既知",
                   q="切替時に発生する増員工数（人日）", q_kappa="実務性", q_recast=recast,
                   q_source="買い手データ", q_low=180, q_high=260, wait_months=6)

TAU_HOJO = TauItem("A", date(2027, 6, 30), "公的暦", "未知",
                   q="申請可能な設備投資の枠（円）", q_kappa="財源",
                   q_source="公開統計", q_low=6_000_000, q_high=10_000_000)

TAU_KOUKI_NG = TauItem("A", date(2027, 3, 31), "契約", "未知",
                       q="年度内に消化できない工期（日）", q_kappa="実務性",
                       q_source="公開統計")          # ← R6b で落ちる想定
TAU_SHUNKO = TauItem("C", date(2027, 6, 30), "契約", "未知",
                     q="竣工から逆算した着手期限までの残余（日）", q_kappa="実務性", q_recast=True,
                     q_source="買い手データ", q_low=40, q_high=70)
TAU_KOUREIKA = TauItem("D", date(2027, 4, 1), "公的暦", "既知",
                       q="55歳以上が占める登録技能者の割合（％）", q_kappa="実務性", q_recast=True,
                       q_source="公開統計", q_low=36, q_high=42)
TAU_MOTOUKE = TauItem("Ec", date(2027, 1, 15), "契約", "未知",
                      q="元請の安全審査を通すまでの実測日数（日）", q_kappa="実務性", q_recast=True,
                      q_source="売り手データ", q_low=45, q_high=90)
TAU_JOGEN = TauItem("A", date(2027, 4, 1), "法令", "既知",
                    q="上限に達するまでに残っている時間外の枠（時間）", q_kappa="実務性", q_recast=True,
                    q_source="買い手データ", q_low=120, q_high=190)

# ───────────────────────────────────────────── M（消去次元）
M0_F = Mi("現状のまま人手で回す", "M0")
M0_K = Mi("現状のまま常用でしのぐ", "M0")
M_NAISEI = Mi("自社で増員して内製する", "内製", frozenset({"D5"}), ("D5",))
M_GAICHU_F = Mi("既存の人材派遣会社に増員を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",))
M_GAICHU_K = Mi("既存の協力会社に応援を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",))
M_KYOUGOU_ROBOT = Mi("他社の省人化装置", "競合", frozenset({"D7a", "D7b"}), ("D7a",))
M_KYOUGOU_CONSULT = Mi("大手コンサルティングファーム", "競合", frozenset({"D7a", "D7d"}), ("D7a",))
M_MOTOUKE = Mi("元請が指定する工法・体制", "取引上位者の指定", frozenset({"D6c"}), ("D6c",))

# ───────────────────────────────────────────── 8セル
CELLS = [
    dict(id="F1-P1", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_food_shelf(True), TAU_JOGEN],
               M=[M0_F, M_NAISEI, M_GAICHU_F, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F1)),
    dict(id="F1-P2", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="困っていない", E_judge="困っていない",
               tau=[TAU_JOGEN, tau_food_shelf(True)],
               M=[M0_F, M_NAISEI, M_GAICHU_F, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F1)),
    dict(id="F2-P1", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_F2, V=(), procedural=True, downward=False,
               E_reader="困っていない", E_judge="困っていない",
               tau=[TAU_HOJO, tau_food_shelf(True)],
               M=[M0_F, M_NAISEI, M_GAICHU_F, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F2)),
    dict(id="F2-P2", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F2, V=(), procedural=False, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_JOGEN, tau_food_shelf(True)],
               M=[M0_F, M_NAISEI, M_GAICHU_F, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F2)),
    dict(id="K1-P1", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[TAU_KOUKI_NG, TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_GAICHU_K, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K1)),
    dict(id="K1-P2", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_JOGEN, TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_GAICHU_K, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K1)),
    dict(id="K2-P1", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_K2, V=V_K2, procedural=True, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_MOTOUKE, TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_MOTOUKE, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K2)),
    dict(id="K2-P2", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K2, V=V_K2, procedural=False, downward=False,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[TAU_JOGEN, TAU_MOTOUKE, TAU_SHUNKO],
               M=[M0_K, M_NAISEI, M_MOTOUKE, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K2)),
]

SELLERS = {"robot": S_ROBOT, "consult": S_CONSULT}


def run():
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id", "業界", "セグメント", "商材")}
        rec.update({
            "generate": d["generate"], "sigma": d["sigma"], "sigma_by": d["sigma_by"],
            "j_star": d.get("j_star"), "kappa_n": d.get("kappa_n"),
            "tau_ok": d.get("tau_ok"), "delta": d.get("delta"),
            "five_mentions": d.get("five_mentions"), "d7_basis": d.get("d7_basis"),
            "blocks": d.get("blocks"), "rules": d.get("rules"),
            "llm_calls": d["llm_calls"],
            "findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                          "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]],
            "needs_judgment": [{"code": j.code, "ref": j.ref,
                                "msg": msgs["judgments"].get(j.code, j.code)} for j in d["needs_judgment"]],
            "seats": [{"name": s.name, "kappa": sorted(s.kappa), "chi": s.chi,
                       "gamma": s.gamma, "omega": s.omega, "reads": s.reads} for s in c["nu"].J],
            "veto": [v.name for v in c["nu"].V],
            "block_msgs": [msgs["blocks"].get(b, b) for b in d.get("blocks", [])],
            "rule_msgs": [msgs["rules"].get(r.split(":")[0], r) for r in d.get("rules", [])],
        })
        out.append(rec)
    json.dump(out, open("decisions8_v2.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for r in out:
        st = "生成可" if r["generate"] else "★不成立"
        print(f"{r['id']:7s} {st}  Σ={''.join(r['sigma'])}({r['sigma_by']})  "
              f"κ_n={r['kappa_n']}  j*={r['j_star']}  "
              f"stop={[f['code'] for f in r['findings'] if f['level']=='stop']}")
    return out


if __name__ == "__main__":
    run()
