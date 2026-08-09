# -*- coding: utf-8 -*-
"""第6版 ―― 修正入力。

第6版コアが止めた箇所を、モデルの言うとおりに直したもの。直し方は3種類しかない。
  A7 … 拘束者が実在しない／向きが逆 → その次元を使わない
  A8 … 適用開始が過去／拘束者が一意でない → 別の日付にする／当事者を同定する
  R7 … 売り手が実数を2つ持たない → その次元を使わない
「売り手が持っていないものは使えない」が、そのまま入力の制約になる。
"""
import json
from datetime import date
from sales_logic import (Seat, Veto, TauItem, Mi, Seller, Nu, Scope, compile_deal)
from cells8_v6 import (S_ROBOT, S_CONSULT, J_F1, J_F2, J_K1, J_K2, V_K2,
                       CTX_F1, CTX_F2, CTX_K1, CTX_K2, TODAY,
                       M0_F, M0_K, M_NAISEI, M_KYOUGOU_ROBOT, M_KYOUGOU_CONSULT)

# ───────────────────────────────────────────── 上位者・下位者
UP_F1 = frozenset({"親会社 生産技術部", "親会社 調達本部", "第三者認証機関"})
UP_F2 = frozenset()                                   # オーナー系。上位者はいない
UP_K1 = frozenset({"発注者（官公庁）"})
UP_K2 = frozenset({"元請A社", "元請A社の安全衛生管理責任者"})
DOWN_K1 = frozenset({"協力会社", "元請"})

# ───────────────────────────────────────────── τ（適用対象・拘束者つき）
SC_SHELF = Scope(keys=(("業態", "惣菜・日配"),))
SC_NONE = Scope()
SC_CERT = Scope(keys=(("業態", "惣菜・日配"), ("規模", "300〜999名")))
SC_KOUJI = Scope(keys=(("業態", "総合建設"),))
SC_SENMON = Scope(keys=(("業態", "専門工事"),))


def tau_shelf():
    """量販店の棚替え。年2回の窓。逃せば6か月待つ"""
    return TauItem("B", date(2027, 3, 1), "自然・需要", "既知",
                   q="切替時に発生する増員工数（人日）", q_kappa="実務性", q_recast=True,
                   q_source="買い手データ", q_low=180, q_high=260, wait_months=6, scope=SC_SHELF)


TAU_CERT = TauItem("A", date(2027, 9, 30), "契約", "未知",
                   q="再認証審査までに標準作業書を改訂すべき工程数", q_kappa="実務性", q_recast=True,
                   q_source="買い手データ", q_low=11, q_high=18,
                   scope=SC_CERT, binders=("第三者認証機関",))
TAU_HOJO = TauItem("A", date(2027, 6, 30), "公的暦", "未知",
                   q="申請可能な設備投資の枠（円）", q_kappa="財源",
                   q_source="公開統計", q_low=6_000_000, q_high=10_000_000, scope=SC_NONE)
TAU_NENDO = TauItem("A", date(2027, 3, 31), "契約", "未知",
                    q="年度内に消化できない工期（日）", q_kappa="実務性", q_recast=True,
                    q_source="買い手データ", q_low=18, q_high=32,
                    scope=SC_KOUJI, binders=("発注者（官公庁）",))
TAU_SHUNKO = TauItem("C", date(2027, 12, 20), "契約", "未知",
                     q="竣工から逆算した着手期限までの残余（日）", q_kappa="実務性", q_recast=True,
                     q_source="買い手データ", q_low=40, q_high=70,
                     scope=SC_KOUJI, binders=("発注者（官公庁）",))
TAU_KOUREIKA = TauItem("D", date(2027, 4, 1), "公的暦", "既知",
                       q="55歳以上が占める登録技能者の割合（％）", q_kappa="実務性", q_recast=True,
                       q_source="公開統計", q_low=36, q_high=42, scope=SC_NONE)
TAU_MOTOUKE = TauItem("Ec", date(2027, 1, 15), "契約", "未知",
                      q="元請A社の安全審査を通すまでの実測日数（日）", q_kappa="実務性", q_recast=True,
                      q_source="売り手データ", q_low=45, q_high=90,
                      scope=SC_SENMON, binders=("元請A社",))
TAU_SHUNKO_K2 = TauItem("C", date(2027, 12, 20), "契約", "未知",
                        q="竣工から逆算した着手期限までの残余（日）", q_kappa="実務性", q_recast=True,
                        q_source="買い手データ", q_low=40, q_high=70,
                        scope=SC_SENMON, binders=("元請A社",))

# ───────────────────────────────────────────── M
# 上位者が実在する F1 だけ D6c を使える。F2・K1 は D2 のみ。
M_HAKEN_F1 = Mi("既存の人材派遣会社に増員を頼む", "既存外注", frozenset({"D2", "D6c"}), ("D2",),
                binder="親会社 調達本部")
M_HAKEN_PLAIN = Mi("既存の人材派遣会社に増員を頼む", "既存外注", frozenset({"D2"}), ("D2",))
M_KYORYOKU = Mi("既存の協力会社に応援を頼む", "既存外注", frozenset({"D2"}), ("D2",))
M_MOTOUKE = Mi("元請A社が指定する工法・体制", "取引上位者の指定", frozenset({"D6c"}), ("D6c",),
               binder="元請A社")

PRE_1 = {"①": "訪問時のヒアリングで、要員数・シフト・段取り替えの回数は既に双方で確認済み"}
PRE_4 = {s: v for s, v in [
    ("①", "訪問時のヒアリングで、要員数・工程・実行予算の枠は既に双方で確認済み"),
    ("②", "買い手自身が『今の数え方では出てこない工数がある』と先に述べている"),
    ("③", "買い手がその現象を自社の言葉で既に名指ししている"),
    ("④", "買い手は他社2社の提案を受けており、今期中に決める必要を既に認めている")]}

CELLS = [
    dict(id="F1-P1", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_shelf(), TAU_CERT],
               M=[M0_F, M_NAISEI, M_HAKEN_F1, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F1, upstream=UP_F1, gamma_pre=PRE_1)),
    dict(id="F1-P2", 業界="食品メーカー", セグメント="大手グループの生産子会社", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F1, V=(), procedural=False, downward=True,
               E_reader="困っていない", E_judge="困っていない",
               tau=[TAU_CERT, tau_shelf()],
               M=[M0_F, M_NAISEI, M_HAKEN_PLAIN, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F1, upstream=UP_F1)),
    dict(id="F2-P1", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_F2, V=(), procedural=True, downward=False,
               E_reader="困っていない", E_judge="困っていない",
               tau=[TAU_HOJO, tau_shelf()],
               M=[M0_F, M_NAISEI, M_HAKEN_PLAIN, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_F2, upstream=UP_F2)),
    dict(id="F2-P2", 業界="食品メーカー", セグメント="オーナー系中堅", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_F2, V=(), procedural=False, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[tau_shelf(), TAU_HOJO],
               M=[M0_F, M_NAISEI, M_HAKEN_PLAIN, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_F2, upstream=UP_F2, gamma_pre=PRE_1)),
    dict(id="K1-P1", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_KYORYOKU, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K1, upstream=UP_K1, downstream=DOWN_K1,
               gamma_pre=PRE_4)),
    dict(id="K1-P2", 業界="建設・設備工事", セグメント="中堅ゼネコン", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K1, V=(), procedural=False, downward=True,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_NENDO, TAU_SHUNKO, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_KYORYOKU, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K1, upstream=UP_K1, downstream=DOWN_K1,
               gamma_pre=PRE_1)),
    dict(id="K2-P1", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="協働ロボット＋ハンド",
         seller="robot",
         nu=Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
               J=J_K2, V=V_K2, procedural=True, downward=False,
               E_reader="手段を知らない", E_judge="手段を知らない",
               tau=[TAU_MOTOUKE, TAU_SHUNKO_K2, TAU_KOUREIKA],
               M=[M0_K, M_NAISEI, M_MOTOUKE, M_KYOUGOU_ROBOT],
               LT_months=8, buyer_context=CTX_K2, upstream=UP_K2, gamma_pre=PRE_1)),
    dict(id="K2-P2", 業界="建設・設備工事", セグメント="専門工事業（下請）", 商材="業務改革コンサル",
         seller="consult",
         nu=Nu(A="使っても分からない", I="役務", S1="100万〜1000万", S2="単発", S3=False, C_move="すぐ試せる",
               J=J_K2, V=V_K2, procedural=False, downward=False,
               E_reader="比較検討中", E_judge="比較検討中",
               tau=[TAU_MOTOUKE, TAU_SHUNKO_K2],
               M=[M0_K, M_NAISEI, M_KYORYOKU, M_KYOUGOU_CONSULT],
               LT_months=3, buyer_context=CTX_K2, upstream=UP_K2, gamma_pre=PRE_4)),
]
SELLERS = {"robot": S_ROBOT, "consult": S_CONSULT}


def run(dump="decisions8_v6b.json"):
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
        rec["seats"] = [{"name": s.name, "kappa": sorted(s.kappa), "chi": s.chi,
                         "gamma": s.gamma, "omega": s.omega, "reads": s.reads,
                         "form": sorted(s.form)} for s in c["nu"].J]
        rec["veto"] = [v.name for v in c["nu"].V]
        rec["gamma_pre"] = c["nu"].gamma_pre
        out.append(rec)
    json.dump(out, open(dump, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in out:
        st = [f"{f['code']}({f['ref']})" for f in r["findings"] if f["level"] == "stop"]
        rj = [f["code"] for f in r["findings"] if f["level"] == "reject"]
        print(f"{r['id']:7s} {'生成可' if r['generate'] else '★不成立'}  Σ={''.join(r['sigma'] or [])}"
              f"  κ_n={r['kappa_n']}  τ={len(r['tau_ok'] or [])}")
        if st: print("          停止", st)
        if rj: print("          棄却", rj)
    print(f"\n生成可 {sum(1 for r in out if r['generate'])}/{len(out)}")
    return out


if __name__ == "__main__":
    run()
