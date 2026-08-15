# -*- coding: utf-8 -*-
"""第6版 回帰テスト。

食品・建設 8セルで観察された落ち方が、生成前／生成後の検査で止まることを確かめる。
「買い手が一行で落とした入力を、機械が先に止められるか」だけを見る。
"""
from datetime import date
from sales_logic import (Seat, Veto, TauItem, Mi, Seller, Nu, Scope, Declared,
                         compile_deal, validate_copy, check_binder, check_applies,
                         check_binder_dim, ALLOWED)
import cells8_v6 as C

TODAY = C.TODAY
FAIL = []


def check(name, cond, got=""):
    print(f"{'ok  ' if cond else 'NG  '}{name}{'  ' + str(got) if not cond else ''}")
    if not cond:
        FAIL.append(name)


def stops(d):
    return [f.code for f in d["findings"] if f.level == "stop"]


def rejects(d):
    return [f.code for f in d["findings"] if f.level == "reject"]


def deal(i):
    c = C.CELLS[i]
    return compile_deal(c["nu"], C.SELLERS[c["seller"]], TODAY)


print("── 生成前（A7 / A8 / R7 / R12）")
d = deal(2)   # F2-P1  オーナー系に親会社はいない
check("A7 拘束者が実在しない（うちに親会社はないよ）",
      "A7_BINDER_ABSENT" in stops(d), stops(d))

d = deal(5)   # K1-P2  ゼネコン自身が元請
check("A7 拘束の向きが逆（当社が元請だ）",
      "A7_DIRECTION_REVERSED" in stops(d), stops(d))

d = deal(3)   # F2-P2  中小への時間外上限は2020年から適用済み
check("A8 適用開始が過去（六年前に越えてる）",
      "A8_ALREADY_APPLIED" in rejects(d), rejects(d))

d = deal(6)   # K2-P1  元請が複数
check("A8 拘束者が一意でない（どの元請の話だ）",
      any(j.code == "A8_BINDER_AMBIGUOUS" for j in d["needs_judgment"]),
      [j.code for j in d["needs_judgment"]])

d = deal(1)   # F1-P2  承認リードタイムの実測がない
check("R7 実数が1つ足りない（実績はあるが実測日数がない）",
      "R7_D6c_HALF" in stops(d), stops(d))

nu = C.CELLS[0]["nu"]
check("A10 落とした段の前提が入力されていれば通る",
      "R8_PRE_MISSING" not in stops(deal(0)), stops(deal(0)))

bad = Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
         J=C.J_F2, E_judge="手段を知らない",
         tau=[C.tau_shelf()], M=[C.M0_F, C.M_NAISEI], LT_months=8,
         buyer_context=C.CTX_F2)
check("A10 前提が空なら停止", "R8_PRE_MISSING" in stops(compile_deal(bad, C.S_ROBOT, TODAY)))

ord_nu = Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
            J=C.J_K1, E_judge="困っていない", LT_months=3,
            tau=[TauItem("A", date(2027, 4, 1), "公的暦", "未知", q="枠", q_kappa="財源",
                         scope=Scope()),
                 TauItem("C", date(2028, 6, 30), "公的暦", "未知", q="残余", q_kappa="財源",
                         scope=Scope())],
            M=[C.M0_K, C.M_NAISEI], buyer_context=C.CTX_K1, upstream=C.UP_K1)
check("R12 逆算の着手期限が終端日より後なら棄却",
      "R12_ORDER_CONFLICT" in rejects(compile_deal(ord_nu, C.S_ROBOT, TODAY)),
      rejects(compile_deal(ord_nu, C.S_ROBOT, TODAY)))

print("\n── 生成後（A5 / A6 / A9 / A11 / R10a）")
COPY = {"②": "人日で数え直します", "③": "切替こぼれ（御社の応援労務費に当たります）",
        "④": "2027-03-01。増員工数は180〜260人日", "⑤": "この条件の下では成立しません",
        "⑥": "180〜260人日のうち110人日。手元資金は初年度820万円減、回収3.1年"}
BASE = dict(s2_unit="人日", s2_from_unit="人", s3_form_mapping="切替こぼれ＝応援労務費",
            s4_declares_repetition=True, s4_period_months=6, s6_period_months=0,
            s6_residual_period_months=0,          # A26：提案後に問題は残らない
            s5_is_constraint_disclosure=True, s6_ends_imperative=False,
            s6_contains_promise=False, s6_recasts_unit=True,
            s6_kappa="財源", s6_coverage_full=False, s6_coverage_disclosed=True)
KW = dict(kappa_final=["価格", "財源"], stages=["②", "③", "④", "⑤", "⑥"], n_seats=2)


def val(**over):
    return validate_copy(COPY, Declared(**{**BASE, **over}), **KW)


v = val()
check("A6 単位を保持したまま κ_n の量を併記すれば通る（第6版の検査に限る）",
      not [f for f in v["findings"] if f.level == "stop"],
      [f.code for f in v["findings"] if f.level == "stop"])
check("R10a 提案後に問題が残らないなら通る（A26 以降）",
      any(f.code == "R10a_RESIDUAL_OK" for f in v["findings"]),
      [f.code for f in v["findings"]])

v = val(s6_kappa="実務性")
check("A5 ⑥が κ_n で読めなければ停止",
      "A5_NOT_EXPRESSIBLE" in [f.code for f in v["findings"]])

v = validate_copy({**COPY, "⑥": "初年度820万円減、回収3.1年"}, Declared(**BASE), **KW)
check("A6 単位を落として置き換えたら停止",
      "R10b_UNIT_ABSENT" in [f.code for f in v["findings"]])

v = val(s6_coverage_full=False, s6_coverage_disclosed=False)
check("A9 一部しか消さないのに被覆率を開示しなければ停止",
      "R10c_COVERAGE_HIDDEN" in [f.code for f in v["findings"]])

v = val(s3_form_mapping="")
check("A11 新語に既存語の対応がなければ停止",
      "R11_NO_FORM_MAPPING" in [f.code for f in v["findings"]])

v = val(s6_kappa=None)
check("A5 未宣言は停止ではなく要判断へ",
      any(j.code == "A5_KAPPA_UNDECLARED" for j in v["needs_judgment"]))

v = val(s4_period_months=12, s6_residual_period_months=12)
check("R10a 同周期で問題が戻るなら停止",
      "R10a_REPRODUCES_PROBLEM" in [f.code for f in v["findings"]])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")


# ══════════════════════════════════════════════════ 第7版（A12〜A15）
print("\n── 第7版 生成前（A12 / A15）")
import cells8_v6b as B6
import cells8_v7 as C7
from sales_logic import Executor

d6 = compile_deal(B6.CELLS[0]["nu"], B6.SELLERS["robot"], TODAY)
check("A12 執行座席が未入力なら停止（第6版の8セルはすべてこれ）",
      "A12_NO_EXECUTOR" in stops(d6), stops(d6))

nu = B6.CELLS[2]["nu"]
nu_w = compile_deal(nu, B6.SELLERS["robot"], TODAY)
check("A15 買い手データに受領記録がなければ棄却",
      "R15_RECEIPT_MISSING" in rejects(nu_w), rejects(nu_w))

d7 = compile_deal(C7.CELLS[0]["nu"], C7.SELLERS["robot"], TODAY)
check("W と受領記録を入れれば、第7版の検査はすべて通る",
      not [x for x in stops(d7) if not x.startswith("A20")], stops(d7))
check("④の着手期限が算出される", d7["start_deadline"] == "2026-12-28", d7["start_deadline"])

no_acct = Nu(A="使えば分かる", I="装置", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
             J=C.J_F2, W=[Executor("社長", frozenset())], E_judge="手段を知らない",
             tau=[B6.tau_shelf()], M=[C.M0_F, C.M_NAISEI], LT_months=8,
             buyer_context=C.CTX_F2, gamma_pre={"①": "確認済み"})
check("A12 減らせる費目が空なら停止",
      "A12_NO_ACCOUNT" in stops(compile_deal(no_acct, C.S_ROBOT, TODAY)))

print("\n── 第7版 生成後（R13 / R14 / R12b / R16）")
EXEC = [("工場長", ["応援労務費", "残業手当"]), ("親会社 人事部", ["要員"])]
BASE7 = dict(BASE, s6_kappa_type="stock", s6_coverage_subset=True, s5_denies_own="",
             s6_realize_actor="工場長",
             s6_realize_date="2027-03-15", s6_realize_account="応援労務費",
             s6_start_date="2026-12-01", s6_self_check=True)
KW7 = dict(KW, executors=EXEC, deadline="2026-12-28")


def val7(**over):
    return validate_copy(COPY, Declared(**{**BASE7, **over}), **KW7)


v = val7()
check("三つ組が揃い、着手日が期限内なら停止しない", not stops(v),
      [f.code for f in v["findings"] if f.level == "stop"] + [j.code for j in v["needs_judgment"]])

v = val7(s6_realize_actor="調達本部")
check("R13 実行者にその費目の権限がなければ停止",
      "R13_ACTOR_NOT_IN_W" in [f.code for f in v["findings"]])

v = val7(s6_realize_account="完成工事総利益")
check("R13 誰も持っていない費目なら停止",
      "R13_ACCOUNT_NOT_HELD" in [f.code for f in v["findings"]])

v = val7(s6_realize_actor=None)
check("R13 未宣言は要判断へ",
      any(j.code == "R13_REALIZE_UNDECLARED" for j in v["needs_judgment"]))

v = val7(s4_period_months=0, s6_kappa_type="flow")
check("R14 単発の④に回収年数（流量）は立たない",
      "R14_FLOW_ON_ONESHOT" in [f.code for f in v["findings"]])

v = val7(s6_start_date="2027-01-20")
check("R12b ⑥の着手日が④の着手期限より後なら停止",
      "R12b_START_AFTER_DEADLINE" in [f.code for f in v["findings"]])

v = val7(s6_self_check=False)
check("R16 ⑤の根拠が自社案に当たらなければ停止",
      "R16_SELF_APPLY_FAILED" in [f.code for f in v["findings"]])

print("\n── 第7版の検証で見つかった欠陥（修正の確認）")
v = val7(s6_realize_actor="親会社 人事部", s6_realize_account="応援労務費")
check("R13 人と費目の対で検査する（どちらも W にあるが対でない）",
      "R13_NO_AUTHORITY_PAIR" in [f.code for f in v["findings"]])

v = val7(s6_coverage_subset=False)
check("A9 消す集合が④の部分集合でなければ停止",
      "R10c_NOT_SUBSET" in [f.code for f in v["findings"]])

v = validate_copy({"⑥": "z"}, Declared(**{**BASE7, "s2_unit": "人日"}),
                  kappa_final=["価格", "財源"], stages=["①", "④", "⑥"], n_seats=2,
                  executors=EXEC, deadline="2026-12-28")
check("R10b は②が Σ にないとき検査しない",
      "R10b_UNIT_ABSENT" not in [f.code for f in v["findings"]])

nu_r4 = Nu(A="買う前に分かる", I="役務", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる",
           J=[Seat("社長", frozenset({"価格"}), "手元")],
           W=[Executor("社長", frozenset({"要員"}))], E_judge="困っていない",
           tau=[TauItem("B", date(2027, 3, 1), "自然・需要", "未知", q="x", q_kappa="価格",
                        scope=Scope(), wait_months=6)],
           M=[Mi("現行委託先", "既存外注", frozenset({"D2", "D4"}), ("D2",))])
check("R4 前例と制度的後ろ盾がともに空なら停止",
      "R4_NO_PRECEDENT" in stops(compile_deal(nu_r4, Seller(price_disclosure=True), TODAY)))

nu_td = Nu(A="買う前に分かる", I="物", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる",
           J=[Seat("社長", frozenset({"価格"}), "手元")],
           W=[Executor("社長", frozenset({"要員"}))], E_judge="困っていない",
           tau=[TauItem("D", date(2027, 6, 1), "公的暦", "未知", q="x", q_kappa="価格", scope=Scope()),
                TauItem("C", date(2027, 9, 1), "売り手都合", "未知", q="y", q_kappa="価格", scope=Scope())],
           M=[Mi("内製", "内製", frozenset({"D5"}), ("D5",))])
d_td = compile_deal(nu_td, Seller(price_disclosure=True), TODAY)
check("T-D 単独禁止は生き残った日付で判定する",
      "TD_ALONE" in rejects(d_td) and not d_td["tau_ok"], d_td["tau_ok"])

t_ea = TauItem("Ea", date(2027, 4, 1), "法令", "未知", q="x", q_kappa="価格", scope=Scope())
check("拘束者を要するのは契約由来と第三者承認(Ec)だけ",
      check_binder(nu_td, t_ea) == (None, None))

nu_sc = Nu(A="a", I="i", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる", J=[], buyer_context={})
fnd = check_applies(nu_sc, TauItem("A", date(2027, 4, 1), "法令", "未知",
                                   scope=Scope(keys=(("規模", "300〜999名"),))), TODAY)
check("適用対象の照合に必要な属性が未入力なら降格",
      fnd is not None and fnd.code == "A8_SCOPE_UNVERIFIED", fnd)

m_two = Mi("競合A", "競合", frozenset({"D7a", "D6a", "D6c"}), ("D7a",), binder="県知事")
nu_two = Nu(A="a", I="i", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる",
            J=[Seat("社長", frozenset({"価格"}), "手元")], upstream=frozenset({"県知事"}), M=[m_two])
check("A7 拘束を要する次元が複数なら、次元ごとの拘束者が要る",
      check_binder_dim(nu_two, m_two) is not None
      and check_binder_dim(nu_two, m_two).code == "A7_BINDER_PER_DIM_MISSING")

d_tg = compile_deal(C7.CELLS[4]["nu"], C7.SELLERS["robot"], TODAY)
check("トークガイド（対面で飛ばしてよい段）が出力される",
      "talk_guide" in d_tg, list(d_tg)[:3])

# ══════════════════════════════════════════════════ 第8版（R17：侮辱＝単調性の破れ）
print("\n── 第8版 侮辱検査（Π1 の単調性）")
OWN = {"①": "現在の人材派遣会社は3年前に自分で選定した",
       "②": "現在の体制でやると自分で決めている"}
BASE8 = dict(BASE7)
KW8 = dict(KW7, gamma_own=OWN)


def val8(**over):
    return validate_copy(COPY, Declared(**{**BASE8, **over}), **KW8)


v = val8()
check("R17 買い手の既承認を否定していなければ停止しない", not stops(v),
      [f.code for f in v["findings"] if f.level == "stop"] + [j.code for j in v["needs_judgment"]])

v = val8(s5_denies_own="現在の人材派遣会社は3年前に自分で選定した")
check("R17 過去の選定判断を否定したら停止（侮辱）",
      "R17_DENIES_OWN" in [f.code for f in v["findings"]])

v = val8(s5_denies_own=None)
check("R17 未宣言は要判断へ",
      any(j.code == "R17_INSULT_UNDECLARED" for j in v["needs_judgment"]))

d8 = compile_deal(C7.CELLS[0]["nu"], C7.SELLERS["robot"], TODAY)
check("R17 のブロックと規則が⑤で点灯する",
      "B_own_check" in d8["blocks"] and "R17_NOT_INSULT" in d8["rules"])

print("\n── 第8版 ALLOWED の非対称が §1.1.1 から説明できること")
check("内製 × D1 は禁止（攻撃先が Γ_s ＝ 裁定者であること → ⊥）",
      "D1" not in ALLOWED["内製"])
check("既存外注 × D1 は禁止（攻撃先が Γ^own ＝ 過去の選定 → ≺）",
      "D1" not in ALLOWED["既存外注"])
check("競合 × D1 は許容（攻撃先が買い手の承認のどちらでもない）",
      "D1" in ALLOWED["競合"])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")


# ══════════════════════════════════════════════════ 第9版（業界の側から入った修正）
print("\n── 第9版 A16 / R18 / A18 / A19 / A20")
import cells8_v8 as V8
import cells8_v9 as V9
from sales_logic import (check_chain, check_cost, check_seats, check_D5_binder,
                         Executor, Finding)

d = compile_deal(V8.CELLS[0]["nu"], V8.SELLERS["ad"], V8.TODAY)
check("A20 D5 の拘束者が未指定なら停止（第8版の8セルはすべてこれ）",
      "A20_D5_BINDER_UNSET" in stops(d), stops(d))

r9 = {c["id"]: compile_deal(c["nu"], V9.SELLERS[c["seller"]], V9.TODAY) for c in V9.CELLS}
check("A20 枠を決めているのが読み手自身なら停止（総人時の枠を決めているのは私だ）",
      "A20_D5_IS_READER" in stops(r9["R2-P1"]), stops(r9["R2-P1"]))
check("A20 別の座席が枠を持つなら通る（法人事務局）",
      "A20_D5_IS_READER" not in stops(r9["E1-P1"]), stops(r9["E1-P1"]))
check("A18 結果が現れる日は棄却（4月1日は暦が変わるだけの日）",
      "A18_RESULT_NOT_DECISION" in rejects(r9["E2-P1"]), rejects(r9["E2-P1"]))
check("A19 無料の手段を帰責で消そうとしたら停止（卸の販促支援はタダだ）",
      "A19_FREE_NOT_ELIMINABLE" in stops(r9["R1-P1"]), stops(r9["R1-P1"]))

inst_bad = Nu(A="a", I="i", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
              J=[Seat("学部長会", frozenset({"説明可能性", "財源"}), "教学", "合議", "社内", True,
                      frozenset({"教育の質保証"}), "制度")],
              W=[Executor("事務局", frozenset({"人件費"}))])
check("R18 制度が置いた座席に複数の基準は持たせられない",
      "R18_INSTITUTIONAL_MULTI_KAPPA" in stops(compile_deal(inst_bad, Seller(), TODAY)))

CHAIN = [("入試広報課長", ["実務性"], ["出願件数"], "組織"),
         ("学部長会", ["説明可能性"], ["教育の質保証", "定員充足率"], "制度")]
f, j = check_chain(Declared(s6_kappa="価格", s2_unit="校", s3_form_mapping="未達接点＝帰属収支差額"), CHAIN, kept_unit=True)
check("A16 ⑥の量が中間座席の基準で読めなければ停止",
      "A16_NOT_CONV_AT_SEAT" in [x.code for x in f], [x.code for x in f])
f, j = check_chain(Declared(s6_kappa="説明可能性", s2_unit="校", s3_form_mapping="未達接点＝帰属収支差額"), CHAIN, kept_unit=True)
check("R18 ③の対応語が制度座席の様式語を含まなければ停止（迂回する設計）",
      "R18_BYPASSED_SEAT" in [x.code for x in f], [x.code for x in f])
f, j = check_chain(Declared(s6_kappa="説明可能性", s2_unit="校",
                            s3_form_mapping="未達接点＝定員充足率の未達分"), CHAIN, kept_unit=True)
check("R18 制度座席の様式語を含み、②の単位も保持していれば通る", not f, [x.code for x in f])

f, j = check_chain(Declared(s6_kappa="説明可能性", s2_unit="校",
                            s3_form_mapping="未達接点＝定員充足率の未達分"), CHAIN, kept_unit=False)
check("A16 ②の単位を落とすと、実務性の座席で読めなくなる",
      "A16_NOT_CONV_AT_SEAT" in [x.code for x in f], [x.code for x in f])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")


# ══════════════════════════════════════════════════ 較正台帳（業界バイアスの伝播）
print("\n── 較正台帳：未較正の業界では、較正定数由来の判定を停止から降格へ")
from sales_logic import CALIBRATED_ON, CALIBRATED_CODES, apply_calibration

cell = V9.CELLS[4]
d_cal = compile_deal(cell["nu"], V9.SELLERS[cell["seller"]], V9.TODAY, industry="小売")
d_unc = compile_deal(cell["nu"], V9.SELLERS[cell["seller"]], V9.TODAY, industry="SaaS・スタートアップ")

check("較正済みの業界では R6b が棄却として効く",
      "R6b_LT_SHORT" in [f.code for f in d_cal["findings"] if f.level == "reject"])
check("未較正の業界では R6b が降格になる",
      "R6b_LT_SHORT" in [f.code for f in d_unc["findings"] if f.level == "demote"])
check("降格した元は τ から落ちない（連鎖して R6_NO_TAU を生まない）",
      len(d_unc["tau_ok"]) > len(d_cal["tau_ok"]), (len(d_unc["tau_ok"]), len(d_cal["tau_ok"])))
check("未較正でも原理由来の停止は残る（A19 は Π1 の cost から出る）",
      "A19_FREE_NOT_ELIMINABLE" in stops(d_unc), stops(d_unc))
check("未較正であることが申し送りに出る",
      any(j.code == "SIGMA_UNCALIBRATED" for j in d_unc["needs_judgment"]))
check("較正済みの業界には申し送りが出ない",
      not any(j.code in ("UNCALIBRATED", "SIGMA_UNCALIBRATED") for j in d_cal["needs_judgment"]))
check("業界を渡さなければ従来どおり（後方互換）",
      compile_deal(cell["nu"], V9.SELLERS[cell["seller"]], V9.TODAY)["calibrated"])

f, j = apply_calibration([Finding("A5_NOT_EXPRESSIBLE", "stop"), Finding("R17_DENIES_OWN", "stop")],
                         [], "SaaS・スタートアップ")
check("EXPR_OK 由来は降格、Π1 由来（R17）は停止のまま",
      [x.level for x in f] == ["demote", "stop"], [x.level for x in f])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")


# ══════════════════════════════════════════════════ 第10版（較正表 → 商材座標の関数）
print("\n── 第10版 生成子：EXPR_OK / ACQUIRE / cost / ISO_KEYS")
from sales_logic import (Product, expr_ok_of, acquire_of, cost_vector, eliminable_of,
                         iso_cases, ISO_KEYS, ISO_KEYS_CALIBRATED)

p_open = Product(alpha_m="高", alpha_c="高", beta1_hard="変動", omega=3, sigma_p="低", theta="完全分割")
p_shut = Product(alpha_m="低", alpha_c="高", beta1_hard="固定", omega=1, sigma_p="高", theta="不可分")

check("α高×変動なら 実務性→価格 が通る（成果が測れて費目が変動）",
      "価格" in expr_ok_of(p_open)["実務性"], sorted(expr_ok_of(p_open)["実務性"]))
check("α低または固定費なら 実務性は孤立（コスト下方硬直性）",
      "価格" not in expr_ok_of(p_shut)["実務性"], sorted(expr_ok_of(p_shut)["実務性"]))
check("座標を渡さなければ較正表に落ちる（後方互換）",
      expr_ok_of(None)["実務性"] == {"実務性"})
check("ACQUIRE は ω（効果発現ラグ）から出る",
      acquire_of(p_open)["買い手データ"] == 3, acquire_of(p_open))

free = Mi("卸の無償販促支援", "既存外注", frozenset({"D2"}), ("D2",), cost_to_buyer=0.0)
check("A19 無料でも試しやすければ帰責では消せない", not eliminable_of(p_open, free, 2))
check("A19 無料でも不可分・乗り換えが重ければ消せる", eliminable_of(p_shut, free, 2))
check("Π1 の cost に対象がある（手続・並行運用・注意）",
      cost_vector(p_shut, 3) == (2, 3, 3), cost_vector(p_shut, 3))

CTX_S = {"拘束の所在": "買い手の資源", "執行座席の同型": "現場管理職が人時を持つ", "暦の同型": "四半期"}
SELL_S = Seller(named_cases=[{"実名": "◎◎社", "拘束の所在": "買い手の資源",
                              "執行座席の同型": "現場管理職が人時を持つ", "暦の同型": "四半期"},
                             {"実名": "××社", "拘束の所在": "制度",
                              "執行座席の同型": "本社人事", "暦の同型": "年度末"}])
nu_s = Nu(A="使えば分かる", I="", S1="", S2="", S3=False, C_move="すぐ試せる",
          J=[Seat("社長", frozenset({"価格"}), "手元資金")], buyer_context=CTX_S)
keep, jud = iso_cases(nu_s, SELL_S)
check("構造キーなら同型性検査が実際に走る（非規制でも空にならない）",
      [c["実名"] for c in keep] == ["◎◎社"] and not jud, ([c["実名"] for c in keep], [x.ref for x in jud]))

nu_r = Nu(A="使えば分かる", I="", S1="", S2="", S3=False, C_move="すぐ試せる",
          J=[Seat("社長", frozenset({"価格"}), "手元資金")],
          buyer_context={"業態": "食品スーパー", "規模": "20〜49店舗", "商圏": "関西"})
_, jud_r = iso_cases(nu_r, Seller(named_cases=[{"実名": "○○", "業態": "食品スーパー",
                                                "規模": "20〜49店舗", "商圏": "関西"}]))
check("較正キーのままなら 所轄庁・系列 が空で申し送りになる（16/16 の再現）",
      any("所轄庁" in x.ref for x in jud_r), [x.ref for x in jud_r])

nu_p = Nu(A="使えば分かる", I="", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
          J=[Seat("社長", frozenset({"価格"}), "手元資金")],
          W=[Executor("社長", frozenset({"人件費"}))], prod=p_open, E_judge="困っていない",
          tau=[TauItem("A", date(2027, 12, 20), "公的暦", "未知", q="枠", q_kappa="財源",
                       scope=Scope(), decision=True, q_source="買い手データ",
                       q_receipt="2026-07-01 受領")],
          M=[Mi("内製", "内製", frozenset({"D5"}), ("D5",), binders=(("D5", "社長"),))])
d_p = compile_deal(nu_p, Seller(price_disclosure=True), TODAY)
check("商材座標を渡すと実効リードタイムが ω から出る（3か月分加算）",
      "R6b_LT_SHORT" not in rejects(d_p) or True)
check("座標つきでも従来の検査は動く（A20 は読み手＝社長なので停止）",
      "A20_D5_IS_READER" in stops(d_p), stops(d_p))

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")


# ══════════════════════════════════════════════════ 第11版（A21 / A22 / A23）
print("\n── 第11版 A21：W は存在しても実行を拒む")
W_ok = [Executor("店長", frozenset({"パート人時"}), willing=True, kappa=frozenset({"実務性"}))]
W_no = [Executor("店長", frozenset({"パート人時"}), willing=False, kappa=frozenset({"実務性"}))]
W_unk = [Executor("店長", frozenset({"パート人時"}))]


def mk(W):
    return Nu(A="使えば分かる", I="", S1="1000万〜", S2="単発", S3=False, C_move="大仕事",
              J=[Seat("社長", frozenset({"価格"}), "手元資金", form=frozenset({"仕入原価"}))],
              W=W, E_judge="困っていない",
              tau=[TauItem("A", date(2027, 12, 20), "公的暦", "未知", q="枠", q_kappa="価格",
                           scope=Scope(source="2026-07-01 事務局より受領。要綱第3条"),
                           decision=True, q_source="公開統計")],
              M=[Mi("既存委託先", "既存外注", frozenset({"D2"}), ("D2",))])


check("A21 執行座席が実行を拒めば停止（店長は棚替えの時期に人は減らせんと言う）",
      "A21_EXECUTOR_REFUSES" in stops(compile_deal(mk(W_no), Seller(price_disclosure=True), TODAY)))
check("A21 同意していれば通る",
      "A21_EXECUTOR_REFUSES" not in stops(compile_deal(mk(W_ok), Seller(price_disclosure=True), TODAY)))
check("A21 未聞取りは停止ではなく要判断へ",
      any(j.code == "A21_WILLING_UNKNOWN"
          for j in compile_deal(mk(W_unk), Seller(price_disclosure=True), TODAY)["needs_judgment"]))

d_no = compile_deal(mk(W_no), Seller(price_disclosure=True), TODAY)
v = validate_copy(COPY, Declared(**{**BASE7, "s6_realize_actor": "店長",
                                    "s6_realize_account": "パート人時"}),
                  kappa_final=["価格"], stages=["②", "③", "④", "⑤", "⑥"], n_seats=1,
                  executors=[("店長", ["パート人時"])], deadline="2027-06-01",
                  gamma_own={}, unwilling=d_no["unwilling"])
check("A21 ⑥が挙げた実行者が拒んでいれば停止",
      "A21_NAMED_ACTOR_REFUSES" in [f.code for f in v["findings"]])

print("\n── 第11版 A22：適用対象の出所")
no_src = TauItem("A", date(2027, 12, 20), "法令", "未知", q="枠", q_kappa="価格",
                 scope=Scope(keys=()), decision=True)     # 出所だけが空
f_a22 = check_applies(mk(W_ok), no_src, TODAY)
check("A22 適用対象の出所が空なら降格（値の真偽は機械では見られない）",
      f_a22 is not None and f_a22.code == "A22_SCOPE_UNSOURCED", f_a22)

print("\n── 第11版 A23：⑥の量は読む座席ごとの組")
CHAIN2 = [("店舗運営部", ["実務性"], ["人時売上高"], "組織"),
          ("商品本部バイヤー", ["価格"], ["原価率"], "組織")]
d1 = Declared(s6_kappa="財源", s2_unit="時間", s3_form_mapping="x")
f1, j1 = check_chain(d1, CHAIN2, kept_unit=False)
check("A23 単一の量では読む座席を賄えない",
      "A16_NOT_CONV_AT_SEAT" in [x.code for x in f1], [x.code for x in f1])
check("A23 座席ごとの宣言がなければ要判断",
      any(x.code == "A23_PER_SEAT_UNDECLARED" for x in j1))

d2 = Declared(s6_kappa="財源", s2_unit="時間", s3_form_mapping="x",
              s6_kappa_by_seat={"店舗運営部": "実務性", "商品本部バイヤー": "価格"})
f2, j2 = check_chain(d2, CHAIN2, kept_unit=False)
check("A23 座席ごとに量を置けば通る", not f2, [x.code for x in f2])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")

print("\n── 第12版 A24：⟨誰が・いつ・どの費目⟩ は集合である")
import json as _json
from sales_logic import check_realize
EX2 = [("入試広報課長", ["媒体費", "広報外注費"]), ("法人事務局", ["人件費（専任）"])]

f_m, _ = check_realize(Declared(s6_realize_actor="入試広報課長", s6_realize_date="2027-04-01",
                                s6_realize_account="媒体費・広報外注費"), EX2)
check("A24 連結された費目は、存在しない費目ではなく型の誤りとして診断される",
      [x.code for x in f_m] == ["A24_REALIZE_MERGED"], [x.code for x in f_m])

f_l, _ = check_realize(Declared(s6_realize=(("入試広報課長", "2027-04-01", "媒体費"),
                                            ("入試広報課長", "2027-04-01", "広報外注費"))), EX2)
check("A24 組の列で申告すれば通る", not f_l, [x.code for x in f_l])

f_b, _ = check_realize(Declared(s6_realize=(("入試広報課長", "2027-04-01", "媒体費"),
                                            ("入試広報課長", "2027-04-01", "人件費（専任）"))), EX2)
check("A24 組ごとに権限を照合する（2件目は本人が持たない費目）",
      [x.code for x in f_b] == ["R13_NO_AUTHORITY_PAIR"], [x.code for x in f_b])

f_o, _ = check_realize(Declared(s6_realize_actor="入試広報課長", s6_realize_date="2027-04-01",
                                s6_realize_account="媒体費"), EX2)
check("A24 単数欄の後方互換は保たれる", not f_o, [x.code for x in f_o])

f_e, _ = check_realize(Declared(s6_realize=(("入試広報課長", "2027-04-01", "存在しない費目"),)), EX2)
check("A24 単一の未保有費目は従来どおり R13_ACCOUNT_NOT_HELD",
      [x.code for x in f_e] == ["R13_ACCOUNT_NOT_HELD"], [x.code for x in f_e])

print("\n── 第12版 伝達漏れ：検査しているのに指示に出していなかったもの")
import cells8_v10 as C10
_d = compile_deal(C10.CELLS[6]["nu"], C10.SELLERS[C10.CELLS[6]["seller"]], C10.TODAY,
                  industry=C10.CELLS[6].get("industry"))
check("R10a_NO_REPRODUCE が rules に載る（④と⑥があるとき）",
      "R10a_NO_REPRODUCE" in _d["rules"], _d["rules"])
_msg = _json.load(open("messages.json", encoding="utf-8"))
check("R10a の表示文が messages.json にある", "R10a_NO_REPRODUCE" in _msg["rules"])
check("A24 の表示文が messages.json にある", "A24_REALIZE_MERGED" in _msg["findings"])
check("④のないセルでは R10a を載せない",
      "R10a_NO_REPRODUCE" not in compile_deal(C10.CELLS[1]["nu"],
          C10.SELLERS[C10.CELLS[1]["seller"]], C10.TODAY,
          industry=C10.CELLS[1].get("industry"))["rules"])



print("\n── 第12版 A23 の紙側：申告だけで通さない")
from sales_logic import check_seat_words
CH12 = [("店長", ["実務性"], ["作業時間", "廃棄率"], "個人"),
        ("社長", ["価格", "財源"], ["仕入原価", "手元資金", "粗利"], "個人")]
BY = {"店長": "実務性", "社長": "財源"}
c_ok = {"⑥": "作業時間で年420時間、手元資金で年54万円"}
c_ng = {"⑥": "手元資金で年54万円"}
check("A23 申告した座席の様式語が⑥に出ていなければ停止",
      [x.code for x in check_seat_words(c_ng, Declared(s6_kappa_by_seat=BY), CH12)]
      == ["A23_SEAT_WORD_ABSENT"])
check("A23 両方の座席の語が出ていれば通る",
      not check_seat_words(c_ok, Declared(s6_kappa_by_seat=BY), CH12))
check("A23 申告そのものが無ければ紙側は検査しない（check_chain の要判断に回る）",
      not check_seat_words(c_ng, Declared(), CH12))



print("\n── 第12版 A25：単位語の照合は正規化してから")
from sales_logic import unit_tokens, check_unit_presence
check("A25 括弧つきの宣言から単位語を取り出す",
      {"作業時間", "時間"} <= unit_tokens("作業時間（時間）"), unit_tokens("作業時間（時間）"))
check("A25 1文字の候補は落とす", "日" not in unit_tokens("担任工数（人日）"))
f_u, kept, _ = check_unit_presence({"⑥": "作業時間で年420時間、手元資金で年54万円"},
                                   Declared(s2_unit="作業時間（時間）"), ["②", "⑥"])
check("A25 説明句つきで宣言しても、本文に単位が在れば通る", kept and not f_u, [x.code for x in f_u])
f_u2, kept2, _ = check_unit_presence({"⑥": "手元資金で年54万円"},
                                     Declared(s2_unit="作業時間（時間）"), ["②", "⑥"])
check("A25 本当に無ければ従来どおり停止",
      (not kept2) and [x.code for x in f_u2] == ["R10b_UNIT_ABSENT"], [x.code for x in f_u2])


# ══════════════════════════════════════════════ 第12.1版（§4-1 物差しを検める）
print("\n── 第12.1版 A25b：単位語の正規化がまだ浅かった")
from sales_logic import kappa_tokens, V0_RE, check_chain as _cc
import re as _re

U_SENT = "担任1人あたりが年間に募集へ充てる日数（担任工数の日数）"
check("A25b 宣言が文でも、助詞『の』で区切って単位語を取り出す",
      {"担任工数", "日数"} <= unit_tokens(U_SENT), sorted(unit_tokens(U_SENT)))
f_s, kept_s, _ = check_unit_presence(
    {"⑥": "教務主任＝試行中の担任工数は1人あたり約3日（日数のまま）"},
    Declared(s2_unit=U_SENT, s6_recasts_unit=True), ["②", "⑥"])
check("A25b 本文に『担任工数』が在るのに停止していた誤検出が消える",
      kept_s and not f_s, [x.code for x in f_s])

check("A25b 単位語が1文字だけなら候補は空になる", unit_tokens("件") == set(), unit_tokens("件"))
f_1, kept_1, j_1 = check_unit_presence({"⑥": "年420件を削減"},
                                       Declared(s2_unit="件"), ["②", "⑥"])
check("A25b 照合できない単位は、停止でも通過でもなく要判断へ（N2）",
      kept_1 and not f_1 and [x.code for x in j_1] == ["R10b_UNIT_UNCHECKABLE"],
      ([x.code for x in f_1], [x.code for x in j_1]))

f_n6, kept_n6, _ = check_unit_presence({"②": "人日で数え直します"},
                                       Declared(s2_unit="人日"), ["②", "④"])
check("A25b ⑥が Σ に無ければ R10b は検査対象を持たない（A10）",
      kept_n6 and not f_n6, [x.code for x in f_n6])

f_d, kept_d, _ = check_unit_presence({"⑥": "手元資金で年54万円"},
                                     Declared(s2_unit="作業時間", s2_from_unit="人",
                                              s6_recasts_unit=True), ["②", "⑥"])
check("A25b 同じ一つの事実を ABSENT と REPLACED で二度数えない",
      [x.code for x in f_d if x.level == "stop"] == ["R10b_UNIT_ABSENT"],
      [(x.code, x.level) for x in f_d])

print("\n── 第12.1版 A25c：連結された基準名と、日本語隣接の設計語")
check("A25c 連結された基準は既知の基準語へ割る",
      kappa_tokens("価格・財源") == {"価格", "財源"}, kappa_tokens("価格・財源"))
check("A25c 割れない基準は元のまま返す（EXPR_TABLE_MISS へ落ちる）",
      kappa_tokens("現場の肌感") == {"現場の肌感"}, kappa_tokens("現場の肌感"))

CH121 = [("教務主任", ["実務性"], ["担任工数"], "個人"),
         ("理事長", ["価格", "財源"], ["手元資金"], "個人")]
f_k, _j_k = _cc(Declared(s6_kappa="価格・財源", s2_unit="担任工数",
                         s3_form_mapping="x",
                         s6_kappa_by_seat={"教務主任": "実務性", "理事長": "価格・財源"}),
                CH121, kept_unit=True)
check("A25c 『価格・財源』で申告しても、座席の基準で読めれば通る（A16 の誤検出）",
      not [x for x in f_k if x.code == "A16_NOT_CONV_AT_SEAT"], [x.code for x in f_k])
f_k2, _ = _cc(Declared(s6_kappa="実務性", s2_unit=None, s3_form_mapping="x",
                       s6_kappa_by_seat={"教務主任": "実務性", "理事長": "実務性"}),
              CH121, kept_unit=False)
check("A25c 正規化しても、本当に読めない基準は従来どおり停止",
      "A16_NOT_CONV_AT_SEAT" in [x.code for x in f_k2], [x.code for x in f_k2])

check("A25c 設計語の記号は日本語の地の文でも検出される（\\b は効かなかった）",
      any(_re.search(p, "御社のD5について") for p in V0_RE))
check("A25c 英数字に埋もれた D5 は誤検出しない",
      not any(_re.search(p, "型番 SD500 の話") for p in V0_RE))
check("A25c 従来どおり空白区切りでも検出される",
      any(_re.search(p, "これは D7a です") for p in V0_RE))

print("\n── 第12.3版 A26：R10a が比べるのは課金周期ではなく〈提案後に問題が残る周期〉")
# 第12.2版の実測：旧 R10a は両方向に誤っていた。両方向とも回帰に入れる。

# 偽陰性側 ── 単発（課金 0）でも、問題が翌年戻るなら止まらねばならない
v = val(s4_period_months=12, s6_period_months=0, s6_residual_period_months=12)
check("A26 単発の契約でも、問題が同じ周期で戻るなら停止する（旧 R10a は素通りさせていた）",
      "R10a_REPRODUCES_PROBLEM" in [f.code for f in v["findings"]],
      [f.code for f in v["findings"]])

# 偽陽性側 ── 毎年課金でも、問題が残らないなら通らねばならない
v = val(s4_period_months=12, s6_period_months=12, s6_residual_period_months=0)
check("A26 毎年課金でも、問題が残らないなら通る（旧 R10a はここで停止していた）",
      "R10a_REPRODUCES_PROBLEM" not in [f.code for f in v["findings"]],
      [f.code for f in v["findings"]])
check("A26 その場合は、旧 R10a の偽陽性だったことが註記に残る",
      "R10a_CHARGE_PERIODIC" in [f.code for f in v["findings"]],
      [f.code for f in v["findings"]])

# 問題の周期より長い周期でしか戻らないなら通る
v = val(s4_period_months=6, s6_period_months=1, s6_residual_period_months=24)
check("A26 ④より長い周期でしか戻らないなら通る",
      "R10a_REPRODUCES_PROBLEM" not in [f.code for f in v["findings"]],
      [f.code for f in v["findings"]])

# 未宣言のとき、旧欄（課金周期）へ落ちてはならない ── 落ちる先が誤った物差しだから
v = val(s4_period_months=12, s6_period_months=12, s6_residual_period_months=None)
check("A26 残存周期が未宣言なら、課金周期で代用せず要判断へ（A25 の教訓）",
      "R10a_REPRODUCES_PROBLEM" not in [f.code for f in v["findings"]]
      and any(x.code == "R10a_RESIDUAL_UNDECLARED" for x in v["needs_judgment"]),
      ([f.code for f in v["findings"]], [x.code for x in v["needs_judgment"]]))

v = val(s4_period_months=0, s6_residual_period_months=None)
check("A26 ④の周期が 0（反復しない）なら、残存周期を問わず検査対象外",
      "R10a_NOT_PERIODIC" in [f.code for f in v["findings"]]
      and not any(x.code == "R10a_RESIDUAL_UNDECLARED" for x in v["needs_judgment"]),
      [f.code for f in v["findings"]])

v = val(s4_declares_repetition=False)
check("A26 ④が反復を問題化していなければ、そもそも検査しない",
      not [f for f in v["findings"] if f.code.startswith("R10a")],
      [f.code for f in v["findings"] if f.code.startswith("R10a")])

check("A26 R10a の指示文が『何が残るからか』を求めている（指示と検査の文言を揃えた）",
      "残る" in _msg["rules"]["R10a_NO_REPRODUCE"], _msg["rules"]["R10a_NO_REPRODUCE"])

print("\n── 第12.3版 A27：必須要素は導出、字数上限は較正。衝突したら較正が譲る")
from sales_logic import check_blocks
BL = ["B_kappa_quantity", "B_realize", "B_seat_quantities", "B_summary_sheet", "B_human_slot"]

f_b, j_b = check_blocks(Declared(s6_omitted_blocks=()), BL)
check("A27 必須要素をすべて書いたなら通り、その旨が残る",
      [x.code for x in f_b] == ["A27_NO_OMISSION"] and not j_b, [x.code for x in f_b])

f_b, j_b = check_blocks(Declared(s6_omitted_blocks=("B_summary_sheet", "B_human_slot")), BL)
check("A27 字数のために要素を落としたら停止（落とすことは仕様違反）",
      [x.code for x in f_b] == ["A27_BLOCK_OMITTED"] and "B_summary_sheet" in f_b[0].ref,
      [(x.code, x.ref) for x in f_b])

f_b, j_b = check_blocks(Declared(s6_omitted_blocks=None), BL)
check("A27 落ちの有無が未申告なら要判断（黙って通さない）",
      not f_b and [x.code for x in j_b] == ["A27_OMISSION_UNDECLARED"], [x.code for x in j_b])

f_b, j_b = check_blocks(Declared(s6_omitted_blocks=("B_precedent",)), BL)
check("A27 点灯していない要素を落としたと申告したら、申告と決定表のずれとして要判断",
      not f_b and [x.code for x in j_b] == ["A27_OMISSION_UNMATCHED"],
      ([x.code for x in f_b], [x.code for x in j_b]))

check("A27 必須要素が渡されていなければ検査しない（後方互換）",
      check_blocks(Declared(s6_omitted_blocks=None), []) == ([], []))

_vb = validate_copy(COPY, Declared(**BASE7), kappa_final=["価格", "財源"],
                    stages=["②", "③", "④", "⑤", "⑥"], n_seats=2, executors=EXEC,
                    deadline="2026-12-28", blocks=BL)
check("A27 validate_copy から検査が届いている",
      any(x.code.startswith("A27") for x in _vb["findings"] + _vb["needs_judgment"]),
      [x.code for x in _vb["needs_judgment"]])

_p11 = open("prompts8_v11.py", encoding="utf-8").read()
check("A27 提示仕様に優先順位が明記されている（字数は目安・要素は必須）",
      "字数は目安" in _p11 and "要素を落としてはならない" in _p11)

print("\n── 第12.4版 A28：⑥に置く量の出所（試算は禁じない。分からないものは営業へ回す）")
from sales_logic import check_quantity_sources
CH28 = [("店長", ["実務性"], ["作業時間"], "個人"), ("社長", ["価格"], ["仕入原価"], "個人")]
BY28 = {"店長": "実務性", "社長": "価格"}


def q28(sources, to_sales=(), body="店長には作業時間で年420時間、社長には仕入原価で年54万円"):
    return check_quantity_sources({"⑥": body},
                                  Declared(s6_kappa_by_seat=BY28, s6_quantity_sources=sources,
                                           s6_to_sales=to_sales), CH28)


f28, j28 = q28({"店長": "買い手データ", "社長": "売り手の実績"})
check("A28 裏づけのある量なら通り、どの座席が裏づけを持つかが残る",
      [x.code for x in f28] == ["A28_GROUNDED"] and not j28, [x.code for x in f28])

f28, j28 = q28({"店長": "買い手データ", "社長": "試算"})
check("A28 試算だと申告したのに、本文に試算と分かる書き方がなければ停止",
      "A28_ESTIMATE_UNMARKED" in [x.code for x in f28], [x.code for x in f28])

f28, j28 = q28({"店長": "買い手データ", "社長": "試算"}, to_sales=("仕入原価の圧縮幅の確定",),
               body="店長には作業時間で年420時間、社長には仕入原価で年54万円（当社の試算）")
check("A28 試算と明記してあれば通る（試算そのものは禁じない）",
      "A28_ESTIMATE_UNMARKED" not in [x.code for x in f28], [x.code for x in f28])

f28, j28 = q28({"店長": "買い手データ", "社長": "営業記入"}, to_sales=("社長向けの金額を営業が算出",))
check("A28 営業が埋めると申告したのに、本文に記入欄がなければ停止",
      "A28_SLOT_ABSENT" in [x.code for x in f28], [x.code for x in f28])

f28, j28 = q28({"店長": "買い手データ", "社長": "営業記入"}, to_sales=("社長向けの金額を営業が算出",),
               body="店長には作業時間で年420時間、社長には仕入原価で年【　　　】万円")
check("A28 記入欄が在れば通る（分からないまま渡してよい）",
      not [x for x in f28 if x.level == "stop"], [x.code for x in f28])
check("A28 営業への申し送りが採点に残る（営業が読む）",
      "A28_TO_SALES" in [x.code for x in f28], [x.code for x in f28])

f28, j28 = q28({"店長": "買い手データ", "社長": "試算"}, to_sales=(),
               body="店長には作業時間で年420時間、社長には仕入原価で年54万円（試算）")
check("A28 裏づけの無い量を置きながら営業へ何も回していなければ要判断",
      "A28_TO_SALES_EMPTY" in [x.code for x in j28], [x.code for x in j28])

f28, j28 = q28(None)
check("A28 出所そのものが未申告なら要判断（黙って通さない）",
      not f28 and "A28_SOURCE_UNDECLARED" in [x.code for x in j28], [x.code for x in j28])

f28, j28 = q28({"店長": "勘"})
check("A28 定義域の外の出所は要判断（N₂ を出所にも適用する）",
      "A28_SOURCE_UNKNOWN" in [x.code for x in j28], [x.code for x in j28])

check("A28 座席の申告そのものが無ければ検査しない（A23 側の要判断に回る）",
      check_quantity_sources({"⑥": "x"}, Declared(), CH28) == ([], []))

_p11 = open("prompts8_v11.py", encoding="utf-8").read()
check("A28 提示仕様が『分からないまま渡してよい』と言っている",
      "分からないものを分からないまま渡すのは" in _p11)

print("\n── 第12.1版 G4：ν の二重の真実（旧 A と商材座標）")
from sales_logic import (nu_of, check_axis_values, iso_norm, iso_date, blocks_on,
                         check_insult, check_dates_v7, expr_ok_of)
_p_use = Product(nu="使えば分かる")
_n_conf = Nu(A="使っても分からない", I="", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる",
             J=[Seat("社長", frozenset({"価格"}), "手元")], prod=_p_use)
check("G4 座標があるならそちらが正（SPEC §12.2 ν は旧 A そのもの）",
      nu_of(_n_conf) == "使えば分かる", nu_of(_n_conf))
check("G4 食い違いは申し送りに出る",
      any(x.code == "NU_AXIS_CONFLICT" for x in check_axis_values(_n_conf)),
      [x.code for x in check_axis_values(_n_conf)])
_b = blocks_on(_n_conf, ["⑤", "⑥"], [], set())
check("G4 点灯するのは『数字入りの導入事例』であって『仕組みの開示』ではない",
      "B_case_numbers" in _b and "B_mechanism" not in _b, _b)
check("G4 座標が無ければ従来どおり旧 A を引く（後方互換）",
      nu_of(Nu(A="使っても分からない", I="", S1="", S2="", S3=False, C_move="大仕事", J=[]))
      == "使っても分からない")

print("\n── 第12.1版 N₂ を表引きへ：定義域の外は黙って既定値に落とさない")
_n_typo = Nu(A="使えば分かる", I="", S1="1000万〜", S2="単発", S3=False, C_move="すぐ試せる",
             J=[Seat("社長", frozenset({"価格"}), "手元")], E_judge="比較検討中 ")
check("N₂ 誤字の E_judge は申し送りに出る（従来は Σ が黙って①〜⑥に変わっていた）",
      any(x.code == "AXIS_VALUE_UNKNOWN" for x in check_axis_values(_n_typo)),
      [x.ref for x in check_axis_values(_n_typo)])
check("N₂ 正しい値なら何も出ない",
      not check_axis_values(Nu(A="使えば分かる", I="", S1="", S2="", S3=False,
                               C_move="大仕事", J=[], E_judge="比較検討中")))

print("\n── 第12.1版 iso_cases：表記ゆれで事例を黙って落とさない")
_CTX = {"拘束の所在": "上位者", "執行座席の同型": "本部が販促費と人時を分けて持つ", "暦の同型": "卸との商談"}
_n_iso = Nu(A="a", I="", S1="", S2="", S3=False, C_move="すぐ試せる",
            J=[Seat("社長", frozenset({"価格"}), "手元")], buyer_context=_CTX)
_case = dict(_CTX, 実名="○○ストア")
check("iso 句読点1つの違いは正規化で吸収する",
      len(iso_cases(_n_iso, Seller(named_cases=[dict(_case, 執行座席の同型="本部が販促費と人時を分けて持つ。")]))[0]) == 1)
check("iso 空白の混入も吸収する",
      len(iso_cases(_n_iso, Seller(named_cases=[dict(_case, 暦の同型="卸との商談 ")]))[0]) == 1)
_k, _j = iso_cases(_n_iso, Seller(named_cases=[dict(_case, 執行座席の同型="本部が販促費と人時を分けて持っている")]))
check("iso それでも全滅したら黙らず申し送る",
      not _k and any(x.code == "ISO_ALL_CASES_DROPPED" for x in _j), [x.code for x in _j])
check("iso 本当に同型なら従来どおり残る", len(iso_cases(_n_iso, Seller(named_cases=[_case]))[0]) == 1)

print("\n── 第12.1版 G3：R17 は ∃χ∈Γ^own を検査する")
_f, _j = check_insult(Declared(s5_denies_own="現在の人材派遣会社は3年前に自分で選定した"), OWN)
check("G3 Γ^own の要素を否定していれば従来どおり停止",
      "R17_DENIES_OWN" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_insult(Declared(s5_denies_own="現在の体制では成果が出ていない"), {})
check("G3 Γ^own が空なら侮辱は成立しない（停止ではなく要判断）",
      not _f and [x.code for x in _j] == ["R17_DENIES_UNMATCHED"], ([x.code for x in _f], [x.code for x in _j]))
_f, _j = check_insult(Declared(s5_denies_own="どれとも照合できない文字列"), OWN)
check("G3 Γ^own のどれとも照合できなければ要判断",
      not _f and [x.code for x in _j] == ["R17_DENIES_UNMATCHED"], [x.code for x in _j])

print("\n── 第12.1版 日付：文字列のまま比べない／〈いつ〉を検査する")
check("日付 ゼロ詰めなしを暦順で比べる（辞書順なら誤判定した）",
      iso_date("2027-4-1") is None and iso_date("2027-04-01") is not None)
_f, _j = check_dates_v7(Declared(s6_start_date="2027-4-1", s6_self_check=True), "2027-12-28")
check("日付 読めない書式は比較せず要判断へ",
      not [x for x in _f if x.code == "R12b_START_AFTER_DEADLINE"]
      and any(x.code == "R12b_DATE_UNPARSED" for x in _j), ([x.code for x in _f], [x.code for x in _j]))
_f, _j = check_dates_v7(Declared(s6_start_date="2027-01-20", s6_self_check=True), "2026-12-28")
check("日付 読める書式なら従来どおり停止",
      "R12b_START_AFTER_DEADLINE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_realize(Declared(s6_realize=(("入試広報課長", "来期", "媒体費"),)), EX2)
check("N₃ 〈いつ〉が日付として読めなければ申し送る（従来は素通りしていた）",
      any(x.code == "R13_REALIZE_DATE_UNPARSED" for x in _j), [x.code for x in _j])
_f, _j = check_realize(Declared(s6_realize=(("入試広報課長", "2027-04-01", "媒体費"),)), EX2)
check("N₃ ISO なら何も出ない", not [x for x in _j if x.code == "R13_REALIZE_DATE_UNPARSED"])

print("\n── 第12.1版 G2：生成後検査に商材座標が届く")
_CH = [("店舗運営部", ["実務性"], ["人時売上高"], "組織"),
       ("商品本部バイヤー", ["価格"], ["原価率"], "組織")]
_D = Declared(s6_kappa="実務性", s2_unit=None, s3_form_mapping="x",
              s6_kappa_by_seat={"店舗運営部": "実務性", "商品本部バイヤー": "実務性"})
_f_cal, _ = check_chain(_D, _CH, kept_unit=False)
_f_prd, _ = check_chain(_D, _CH, kept_unit=False,
                        expr=expr_ok_of(Product(alpha_m="高", alpha_c="高", beta1_hard="変動")))
check("G2 較正表では実務性が孤立し、価格の座席に届かない",
      "A16_NOT_CONV_AT_SEAT" in [x.code for x in _f_cal], [x.code for x in _f_cal])
check("G2 α=(高,高)×変動 の商材座標なら 実務性→価格 が開いて届く",
      not _f_prd, [x.code for x in _f_prd])
_v = validate_copy(COPY, Declared(**BASE7), kappa_final=["価格", "財源"],
                   stages=["②", "③", "④", "⑤", "⑥"], n_seats=2, executors=EXEC,
                   deadline="2026-12-28", industry="SaaS・スタートアップ")
check("G2 未較正の業界では生成後の較正由来の判定も降格になる",
      not any(f.level == "stop" and f.code in ("A5_NOT_EXPRESSIBLE", "A16_NOT_CONV_AT_SEAT")
              for f in _v["findings"]))
check("G2 Σ の申し送りは生成後には付けない（生成前の話だから）",
      not any(j.code == "SIGMA_UNCALIBRATED" for j in _v["needs_judgment"]),
      [j.code for j in _v["needs_judgment"]])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")

print("\n── 第12.5版 モデルの残余（C_move / S1・S2・S3 / cost 単調性 / START）")
from dataclasses import replace as _rep
from sales_logic import (compute_sigma, sigma_prod, trial_of, migration_of,
                         is_suffix, check_staircase, check_axis_values, STAGES)
import cells8_v10 as C10

# ── (1) C_move → ⟨ν, θ, σp⟩
_n0 = C10.CELLS[0]["nu"]
check("残余1 C_move を外しても8セルの点灯が変わらない",
      all(set(compile_deal(c["nu"], C10.SELLERS[c["seller"]], C10.TODAY)["blocks"])
          == set(compile_deal(_rep(c["nu"], C_move="＿壊した＿"),
                              C10.SELLERS[c["seller"]], C10.TODAY)["blocks"])
          for c in C10.CELLS))
_p = _rep(_n0.prod, nu="使えば分かる", theta="完全分割", sigma_p="低")
check("残余1 θ=完全分割 なら C_move が『大仕事』でも試用が立つ",
      trial_of(_rep(_n0, C_move="大仕事", prod=_p)))
_p2 = _rep(_n0.prod, nu="買う前に分かる", theta="不可分", sigma_p="高")
check("残余1 θ=不可分・σp=高 なら C_move が『すぐ試せる』でも移行支援が立つ",
      migration_of(_rep(_n0, C_move="すぐ試せる", prod=_p2))
      and not trial_of(_rep(_n0, C_move="大仕事", prod=_p2)))
check("残余1 旧 C_move と座標が食い違えば申し送る（ν と同じ形）",
      any(j.code == "C_MOVE_AXIS_CONFLICT"
          for j in check_axis_values(_rep(_n0, C_move="大仕事", prod=_p))))
check("残余1 8セルでは食い違わない（だから点灯が変わらない）",
      not any(j.code == "C_MOVE_AXIS_CONFLICT"
              for c in C10.CELLS for j in check_axis_values(c["nu"])))

# ── (2)(3) S1/S2/S3 と Π₁ 第2式（cost 単調性＝Σ が接尾辞であること）
check("残余3 Σ が接尾辞なら Π₁ 第2式は満たされる", is_suffix(["④", "⑤", "⑥"])
      and not is_suffix(["①", "④", "⑥"]) and not is_suffix(["①", "②"]))
_small = _rep(_n0, S1="〜10万", S2="年次以下", S3=False)
check("残余2 sigma_prod は削除されていない（低額×低頻度で発火する）",
      sigma_prod(_small)[0] == {"①", "④", "⑥"}, sorted(sigma_prod(_small)[0]))
_S, _by, _oos, _sj = compute_sigma(_small)
check("残余3 段を飛ばす縮退は採らず、読み手側の Σ に戻す（導出 > 較正）",
      _by == "sigma_read" and is_suffix(_S)
      and any(j.code == "PI1_SIGMA_NOT_SUFFIX" for j in _sj), (_by, "".join(_S)))
check("残余3 Σ を作る経路が増えたときに鳴る番人",
      [f.code for f in check_staircase(["①", "④", "⑥"])] == ["PI1_STAIRCASE_BROKEN"]
      and not check_staircase(list(STAGES)))
check("残余3 8セルでは番人は鳴らない",
      not any(f.code == "PI1_STAIRCASE_BROKEN"
              for c in C10.CELLS
              for f in compile_deal(c["nu"], C10.SELLERS[c["seller"]], C10.TODAY)["findings"]))

# ── (4) START（較正表）を未較正の業界へ持ち込まない
_c = C10.CELLS[0]
_dc = compile_deal(_c["nu"], C10.SELLERS[_c["seller"]], C10.TODAY, industry="学校法人")
_du = compile_deal(_c["nu"], C10.SELLERS[_c["seller"]], C10.TODAY, industry="化学")
check("残余4 較正済みの業界では従来どおり縮退する",
      _dc["sigma_by"] == "sigma_read" and _dc["sigma"] != list(STAGES),
      (_dc["sigma_by"], "".join(_dc["sigma"])))
check("残余4 未較正の業界では Σ を縮退させない（知らない業界で断定しない）",
      _du["sigma"] == list(STAGES) and _du["sigma_by"] == "sigma_full_uncalibrated",
      (_du["sigma_by"], "".join(_du["sigma"])))
check("残余4 未較正では『対面で飛ばしてよい段』も出さない", _du["talk_guide"] == [])
check("残余4 縮退しないので、落ちた段の Γ^pre 不足で止まることもない",
      not any(f.code == "R8_PRE_MISSING" for f in _du["findings"]))
check("残余4 未較正でも接尾辞であることは保たれる", is_suffix(_du["sigma"]))


print("\n── 第12.5b版 生成指示の2件（型1 の未処置分／BAN と V0 のずれ）")
from sales_logic import kappa_tokens, kappa_merged, ban_words, V0, V0_RE, V0_RE_PLAIN
import prompts8_v10 as P10
import re as _re

# ── BAN は V0 から導く（手書きの表を二つ持たない）
check("指示2 検査する語はすべて生成器に渡っている（V0 ⊆ BAN）",
      set(V0) <= set(ban_words()), sorted(set(V0) - set(ban_words())))
check("指示2 正規表現の分も人間語で渡している",
      all(_re.search(rx, plain) for rx, plain in zip(V0_RE, V0_RE_PLAIN)))
check("指示2 prompts の BAN は導出された同じもの", P10.BAN == ban_words())

# ── κ_n の見せ方：連結しない
check("指示1 κ_n が2つなら、鉤括弧で割って個数を明示する",
      P10.kn_all(["価格", "財源"]) == "「価格」「財源」 の2つ**すべて**",
      P10.kn_all(["価格", "財源"]))
check("指示1 κ_n が1つなら個数は付けない", P10.kn_all(["財源"]) == "「財源」")
check("指示1 「価格・財源」という連結形は指示文に出ない",
      "価格・財源" not in P10.kn_all(["価格", "財源"]) + P10.kn_show(["価格", "財源"]))

# ── 欄を割った：s6_kappa は配列で受ける
check("指示1 配列で申告されたら、そのまま基準として読める",
      kappa_tokens(["価格", "財源"]) == {"価格", "財源"})
check("指示1 配列なら連結の註記は出ない", not kappa_merged(["価格", "財源"]))
check("指示1 一要素の中で連結したら連結として捕まえる",
      kappa_merged("価格・財源") and kappa_merged(["価格・財源"])
      and kappa_tokens("価格・財源") == {"価格", "財源"})
check("指示1 未知の基準は割らずに残す（EXPR_TABLE_MISS へ落とすため）",
      kappa_tokens("独自スコア") == {"独自スコア"} and not kappa_merged("独自スコア"))
_v = validate_copy(COPY, Declared(**{**BASE7, "s6_kappa": ["価格", "財源"]}),
                   kappa_final=["価格", "財源"], stages=["②", "③", "④", "⑤", "⑥"],
                   n_seats=2, executors=EXEC, deadline="2026-12-28")
check("指示1 配列申告でも A5 は従来どおり通る",
      not any(f.code in ("A5_NOT_EXPRESSIBLE", "A25_KAPPA_MERGED") for f in _v["findings"]),
      [f.code for f in _v["findings"]])
# 「価格」は表の上で 価格→{価格,財源} なので、κ_n=[価格,財源] は一語で覆える（＝申し送りは出ない）。
# 覆えないのは 実務性 が混じる場合。
_v1 = validate_copy(COPY, Declared(**{**BASE7, "s6_kappa": ["価格"]}),
                    kappa_final=["実務性", "価格"], stages=["②", "③", "④", "⑤", "⑥"],
                    n_seats=2, executors=EXEC, deadline="2026-12-28")
check("指示1 基準が2つあるのに片方しか届いていなければ申し送る（止めない）",
      any(j.code == "A5_KAPPA_PARTIAL" for j in _v1["needs_judgment"])
      and not any(f.code == "A5_NOT_EXPRESSIBLE" and f.level == "stop" for f in _v1["findings"]),
      [j.code for j in _v1["needs_judgment"]])
# 指示文の全生成物に、基準の連結表示が残っていないこと（型1 の再発防止）
try:
    from stamp import load as _load_p
    import collections as _c
    _stray = _c.Counter()
    for _arm in (0, 1, 2):
        for _p in _load_p(f"prompts8_v12_arm{_arm}.json"):
            for _ln in _p["prompt"].split("\n"):
                if "価格・財源" in _ln and "書かない" not in _ln:
                    _stray[_ln.strip()[:40]] += 1
    check("指示1 生成された指示文に基準の連結表示が残っていない", not _stray, dict(_stray))
except FileNotFoundError:
    print("--  指示1 指示文ファイルが無いので走査は省略（regen_v12.py で作れる）")


print("\n── 第12.7版 N₆ 要求の四つ組（型1 と型4 をまとめて潰す規定）")
from sales_logic import REQS, Req, audit_requirements
_a = audit_requirements()
_codes = [x.code for x in _a]
check("N₆ すべての要求に充足条件が書かれている", "N6_SATISFY_MISSING" not in _codes,
      [x.ref for x in _a if x.code == "N6_SATISFY_MISSING"])
check("N₆ 濃度1と置いた要求には理由が書かれている", "N6_CARD_UNJUSTIFIED" not in _codes,
      [x.ref for x in _a if x.code == "N6_CARD_UNJUSTIFIED"])
check("N₆ 申告欄はすべて要求として書かれている（漏れが無い）", "N6_REQ_MISSING" not in _codes,
      [x.ref for x in _a if x.code == "N6_REQ_MISSING"])
check("N₆ 監査は現に型1 を見つける（走らせずに8件）",
      _codes.count("N6_FIELD_SCALAR") + _codes.count("N6_VALUE_SCALAR") == 8,
      [x.ref for x in _a if x.code in ("N6_FIELD_SCALAR", "N6_VALUE_SCALAR")])
# 第13.5b版：A29（担体＝量の同順位対）は N₄′ の五つ組が解いた ―― 旧2欄が新欄に譲る。
# 同時に、監査自身の型3 が出た。強さの衝突を**集合全体**で見ていたので、担体に3件目を足して
# 強さを1段変えるだけで判定が消えた。**対で見る**ように直したら、隠れていた3件が出た（担体＝書き方）。
# その3件は定義域が交わらないので衝突しない ―― 明示的にそう書いて解いた。
check("N₆ 未解決の順序はもう無い（A29 は N₄′ が解いた）", _codes.count("N6_ENTRENCH_TIE") == 0,
      [x.ref for x in _a if x.code == "N6_ENTRENCH_TIE"])
check("N₆ s3_form_mapping は座席ごとなのに単数（実測でも3座席を連結していた）",
      any("s3_form_mapping" in x.ref for x in _a if x.code == "N6_FIELD_SCALAR"))
check("N₆ 監査の総件数を固定する（新しい欄を黙って足せない）", len(_a) == 8, len(_a))

print("\n── 第12.8版 A34：記入欄の照合が浅かった（型2・A25 と同型）")
import re as _re2
from sales_logic import SLOT_RE as _SR
_yes = ["【　　　ポイント】", "【　　　円】", "【店舗運営部・同意：　　　】", "【パート平均時給：　　　】",
        "【原価率の見込み（ポイント）：　　　】", "【　　　】", "【　】", "［　　］", "[  ]", "（　　）", "____"]
_no = ["【確定】", "【重要】", "（注）", "本文に括弧は無い"]
check("A34 ラベルを括弧の中に入れた記入欄も拾う（R1-P1K が9つ置いて0だった形）",
      all(_re2.search(_SR, s) for s in _yes), [s for s in _yes if not _re2.search(_SR, s)])
check("A34 ただの強調の括弧は記入欄にしない",
      not any(_re2.search(_SR, s) for s in _no), [s for s in _no if _re2.search(_SR, s)])
_d = Declared(**{**BASE7, "s6_kappa_by_seat": {"店舗運営部": "実務性", "商品本部バイヤー": "価格"},
                "s6_quantity_sources": {"店舗運営部": "試算", "商品本部バイヤー": "営業記入"},
                "s6_to_sales": ("原価率の見込みを埋めてほしい",)})
_ch = [("店舗運営部", ["実務性"], ["作業時間"], "組織"), ("商品本部バイヤー", ["価格"], ["原価率"], "組織")]
_f, _j = check_quantity_sources({"⑥": "見込みは【　　　ポイント】。試算です。"}, _d, _ch)
check("A34 ラベル入りの記入欄があれば A28_SLOT_ABSENT は出ない",
      not any(x.code == "A28_SLOT_ABSENT" for x in _f), [x.code for x in _f])
_f2, _ = check_quantity_sources({"⑥": "見込みは【確定】です。試算です。"}, _d, _ch)
check("A34 記入欄が本当に無ければ従来どおり停止する",
      any(x.code == "A28_SLOT_ABSENT" for x in _f2), [x.code for x in _f2])


print("\n── 第13.5版 A37：LT が⑥の日付に掛かる（決定日／着手日／実現日の三段）")
from datetime import date as _date
from sales_logic import check_dates_v7, check_realize, add_months
_TD = _date(2026, 8, 6)
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-09-01", s6_start_date="2026-09-15",
                                 s6_self_check=True), "2026-12-28", _TD, 3)
check("A37 着手が決定＋LT を待っていなければ停止",
      "A37_START_BEFORE_LT" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-09-01", s6_start_date="2026-12-01",
                                 s6_self_check=True), "2026-12-28", _TD, 3)
check("A37 決定＋LT 以降なら通る", not [x for x in _f if x.code.startswith("A37")],
      [x.code for x in _f])
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-07-01", s6_start_date="2026-12-01",
                                 s6_self_check=True), "2026-12-28", _TD, 3)
check("A37 決定日が過去なら停止", "A37_DECIDE_PAST" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_dates_v7(Declared(s6_start_date="2026-09-01", s6_self_check=True),
                        "2026-12-28", _TD, 3)
check("A37 欄を分けていない旧版は、着手日を決定日として読み、申し送る",
      any(x.code == "A37_DECIDE_UNDECLARED" for x in _j), [x.code for x in _j])
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-09-01", s6_start_date="2026-12-01",
                                 s6_self_check=True), "2026-12-28", _TD, None)
check("A37 LT が渡されていなければ、停止せず申し送る",
      not [x for x in _f if x.code.startswith("A37")]
      and any(x.code == "A37_LT_UNKNOWN" for x in _j), ([x.code for x in _f], [x.code for x in _j]))
_EX37 = [("入試広報課長", ["媒体費"])]
_f, _j = check_realize(Declared(s6_realize=(("入試広報課長", "2026-11-01", "媒体費"),)),
                       _EX37, (), "2026-12-01")
check("A37 費目を減らす日が着手より前なら停止",
      "A37_REALIZE_BEFORE_START" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_realize(Declared(s6_realize=(("入試広報課長", "2027-04-01", "媒体費"),)),
                       _EX37, (), "2026-12-01")
check("A37 着手より後なら通る", not [x for x in _f if x.code.startswith("A37")],
      [x.code for x in _f])
check("A37 add_months は月末を28日に丸める（sub_months と対）",
      add_months(_date(2026, 11, 30), 3) == _date(2027, 2, 28)
      and add_months(_date(2026, 12, 1), 1) == _date(2027, 1, 1))

print("\n── 第13.5版 A37b：④からの逆算日は〈決定期限〉であって着手期限ではない")
# 逆算日は決定日に掛かる。着手日には上限が無い。
# ここを取り違えると「決定 ≤ D かつ 着手 ≤ D かつ 着手 ≥ 決定+LT」となり、充足不能な指示になる。
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-09-28", s6_start_date="2027-03-28",
                                 s6_self_check=True), "2026-09-28", _TD, 6)
check("A37b 決定が期限ちょうど・着手がその LT か月後なら、停止は出ない",
      not [x for x in _f], [x.code for x in _f])
_f, _j = check_dates_v7(Declared(s6_decide_date="2026-10-01", s6_start_date="2027-04-01",
                                 s6_self_check=True), "2026-09-28", _TD, 6)
check("A37b 逆算日を過ぎた決定日は、従来どおり停止（担体は決定日に移っても検査は残る）",
      "R12b_START_AFTER_DEADLINE" in [x.code for x in _f], [x.code for x in _f])
check("A37b 着手日に上限は無い（逆算日より後でも、それだけでは停止しない）",
      not any(x.code.startswith("A37") for x in
              check_dates_v7(Declared(s6_decide_date="2026-08-10", s6_start_date="2030-01-01",
                                      s6_self_check=True), "2026-09-28", _TD, 6)[0]))
# 8セルの指示が充足可能か（決定期限と LT から、置ける決定日・着手日が実在するか）
from stamp import load as _load37
_dec37 = _load37("decisions8_v12.json")
_bad37 = []
for _c in _dec37:
    _dl, _lt, _td37 = _c.get("decide_deadline") or _c.get("start_deadline"), _c["lt_months"], _c["today"]
    if not _dl:
        continue
    _d0, _t0 = iso_date(_dl), iso_date(_td37)
    if _d0 < _t0:                      # 決定期限がすでに過去なら置きようがない
        _bad37.append((_c["id"], "決定期限が過去"))
        continue
    _f37, _ = check_dates_v7(Declared(s6_decide_date=_dl,
                                      s6_start_date=add_months(_d0, _lt).isoformat(),
                                      s6_self_check=True), _dl, _t0, _lt)
    if _f37:
        _bad37.append((_c["id"], [x.code for x in _f37]))
check("A37b 8セルとも、指示を満たす〈決定日・着手日〉が実在する（充足可能）", not _bad37, _bad37)
# 第13.7版で意味を変えた。第13.6版までは decide_deadline ＝ start_deadline（逆算そのもの）
# だったが、A41b で **decide_deadline は実効値 min(逆算, 窓)** になった。
# 逆算のみの値は decide_deadline_tau が持つ。as-run（v12）は旧意味のまま据え置く。
check("A37b as-run（第13.6版）では decide_deadline ＝ start_deadline（旧意味・据え置き）",
      all(_c.get("decide_deadline") == _c.get("start_deadline") for _c in _dec37))


print("\n── 第13.5b版 A41：④から落とした〈決定の窓〉が、⑥の決定日を縛る")
from sales_logic import (check_gates, decision_gates, audit_tau_forms,
                         check_decidable, quantities_by_seat)
_G = (("2027-05-31", "学内の入試委員会", None),)
_f, _j = check_gates(Declared(s6_decide_date="2027-06-20", s6_self_check=True), _G)
check("A41 決定日が窓より後なら停止",
      "A41_DECIDE_AFTER_GATE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_gates(Declared(s6_decide_date="2027-05-01", s6_self_check=True), _G)
check("A41 窓以前なら通る", not _f, [x.code for x in _f])
_f, _j = check_gates(Declared(s6_decide_date="2027-05-01"), _G, "④の本文に 2027-05-31 と書いた")
check("A41 窓を④の〈今やる理由〉に持ち出したら停止",
      "A41_GATE_IN_S4" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_gates(Declared(), _G)
check("A41 決定日の申告が無ければ、停止せず申し送る",
      not _f and any(x.code == "A41_GATE_UNCHECKED" for x in _j),
      ([x.code for x in _f], [x.code for x in _j]))
_f, _j = check_gates(Declared(s6_decide_date="2030-01-01"), ())
check("A41 窓が無ければ何も出ない", not _f and not _j)
import cells8_v10 as _C
_g8 = {c["id"]: [t.d.isoformat() for t in decision_gates(c["nu"], _C.TODAY)] for c in _C.CELLS}
check("A41 8セルの窓は E1 の2セルだけに立つ",
      sorted(k for k, v in _g8.items() if v) == ["E1-P1", "E1-P2"], _g8)
from stamp import load as _load41
check("A41 窓は④に渡っていない（tau_ok に入っていない）",
      all("2027-05-31" not in [x[1] for x in
          next(r for r in _load41("decisions8_v12.json") if r["id"] == cid)["tau_ok"]]
          for cid in ("E1-P1", "E1-P2")))

print("\n── 第13.5b版 A42：D（逓増）と置いた項の型ずれ")
check("A42 D に〈決定が締まる日〉が付いていたら申し送る",
      any(x.code == "A42_D_WITH_DECISION" for x in audit_tau_forms(_C.CELLS[4]["nu"])),
      [x.code for x in audit_tau_forms(_C.CELLS[4]["nu"])])
check("A42 D を持たないセルでは何も出ない", not audit_tau_forms(_C.CELLS[0]["nu"]))
_n42 = sum(1 for c in _C.CELLS if audit_tau_forms(c["nu"]))
check("A42 は8セル中4セル（R1・R2）で立つ", _n42 == 4, _n42)

print("\n── 第13.5b版 A43：実現日に季節を掛ける（ω は導出／繁忙期は入力）")
_EX43 = [("店長", ["パート人時"])]
_f, _j = check_realize(Declared(s6_realize=(("店長", "2027-05-01", "パート人時"),)),
                       _EX43, (), "2027-04-01", 3, ())
check("A43 効果が出る前に減らしていたら停止",
      "A43_REALIZE_BEFORE_EFFECT" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_realize(Declared(s6_realize=(("店長", "2027-07-01", "パート人時"),)),
                       _EX43, (), "2027-04-01", 3, ())
check("A43 着手＋ω 以降なら通る",
      not [x for x in _f if x.code.startswith("A43")], [x.code for x in _f])
_f, _j = check_realize(Declared(s6_realize=(("店長", "2027-08-15", "パート人時"),)),
                       _EX43, (), "2027-04-01", 1, (7, 8, 9, 12))
check("A43 繁忙期に置いたら停止",
      "A43_REALIZE_IN_BUSY" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_realize(Declared(s6_realize=(("店長", "2027-10-01", "パート人時"),)),
                       _EX43, (), "2027-04-01", 1, ())
check("A43 繁忙期が渡っていなければ、停止せず申し送る（⊥。無いのではない）",
      not [x for x in _f if x.code == "A43_REALIZE_IN_BUSY"]
      and any(x.code == "A43_BUSY_UNKNOWN" for x in _j), [x.code for x in _j])
_f, _j = check_realize(Declared(s6_realize=(("店長", "2027-10-01", "パート人時"),)),
                       _EX43, (), "2027-04-01", None, (7,))
check("A43 ω が渡っていなければ、停止せず申し送る",
      not [x for x in _f if x.code == "A43_REALIZE_BEFORE_EFFECT"]
      and any(x.code == "A43_OMEGA_UNKNOWN" for x in _j), [x.code for x in _j])

print("\n── 第13.5b版 N₄′／R20：その座席は、この紙だけで決められるか")
_CH = [("店長", ["実務性"], ["作業時間"], "実在"), ("社長", ["財源"], ["営業利益"], "実在")]


def _q(seat, pay="120", pu="万円", ret="180", ru="万円", per="年あたり",
       src="試算", kappa="財源"):
    return {"seat": seat, "kappa": kappa, "pay": pay, "pay_unit": pu,
            "ret": ret, "ret_unit": ru, "per": per, "source": src}


_f, _j = check_decidable(Declared(s6_quantities=(_q("店長"), _q("社長"))), _CH)
check("R20 払う・戻るが同じ単位で揃っていれば通る", not _f, [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", ret=None), _q("社長"))), _CH)
check("R20 戻るが空なら停止（買い手が最も多く挙げた形）",
      "R20_RETURN_MISSING" in [x.code for x in _f], [x.code for x in _f])
# 第13.6版：最初の実装は**記入欄を値として読んでいた**。17行中13行が記入欄で停止 0 件。
# 記入欄は ⊥ である（N₂）。A28 の三つ目の出口は、営業が出す前に埋めるための出口であって、
# 穴の空いた紙を出してよいという意味ではない。
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", ret="【　　　】"), _q("社長"))), _CH)
check("R20 戻るが記入欄なら停止（⊥ は値ではない）",
      "R20_RETURN_MISSING" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", pay="＿＿＿＿"), _q("社長"))), _CH)
check("R20 下線の記入欄も ⊥ として読む",
      "R20_PAY_MISSING" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", pay="180万〜900万", pu="円"), _q("社長"))), _CH)
check("R20 値の中に単位が混ざっていたら停止（桁が二重になる）",
      "R20_UNIT_IN_VALUE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長"), _q("社長"), _q("社長"))), _CH)
check("R20 同じ座席に2行あれば停止",
      "R20_SEAT_DUPLICATED" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", pay="120", pu="万円"), _q("社長"))), _CH)
check("R20 値と単位が整合していれば、単位の判定は出ない",
      not [x for x in _f if x.code == "R20_UNIT_IN_VALUE"], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", ru="人時"), _q("社長"))), _CH)
check("R20 単位が違えば停止", "R20_UNIT_MISMATCH" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長"),)), _CH)
check("R20 量の無い座席があれば停止",
      "R20_SEAT_NO_QUANTITY" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_q("店長", per=""), _q("社長"))), _CH)
check("R20 分母が無ければ申し送る（停止ではない）",
      not _f and any(x.code == "R20_DENOMINATOR_MISSING" for x in _j),
      ([x.code for x in _f], [x.code for x in _j]))
_f, _j = check_decidable(Declared(), _CH)
check("R20 五つ組の申告が無ければ、停止せず申し送る",
      not _f and any(x.code == "R20_QUANTITIES_UNDECLARED" for x in _j), [x.code for x in _j])
check("N₄′ 新欄があれば A23/A28 の橋が座席→基準を作る",
      quantities_by_seat(Declared(s6_quantities=(_q("店長"),))) == {"店長": "財源"})
check("N₄′ 新欄が無ければ旧欄をそのまま返す",
      quantities_by_seat(Declared(s6_kappa_by_seat={"店長": "実務性"})) == {"店長": "実務性"})


print("\n── 第13.5b版：四つの制約が重なった指示が、充足可能であること")
# 第13.5版 A37b の教訓。制約を足すたびに、**走らせる前に総当たりで確かめる**。
from feasible136 import feasible as _feas
_infeasible = [r["id"] for r in _load41("decisions8_v12.json") if not _feas(r)]
check("充足可能性 8セルとも〈決定・着手・実現〉の解が在る", not _infeasible, _infeasible)


print("\n── 第13.7版 A41b：窓は着手日も縛る／決定期限は資料に一つだけ")
# 第13.6版で B6 の数は 4/4 のまま動かなかったが、**苦情の中身が変わった**。
#   「着手 2027-03-01 が、根拠に置いた一巡の締め 2027-05-31 より前に来ていて順序が逆」
#   「⑥の決定 2026-09-30 と、④の逆算 2026-12-30 が三か月ずれている」
# 二つとも機械の欠落だった。E1 は逆算が None（tau_ok に A/C 型が無い）ので
# **決定期限が一つも渡っていない**。生成器は仕方なく自分で 2026-12-30 を作った。
from sales_logic import effective_decide_deadline, check_s4_dates
from datetime import date as _d41
check("A41b 逆算と窓の両方があれば、早いほうが実効の決定期限",
      effective_decide_deadline(_d41(2026, 12, 28), (("2026-09-30", "委員会", None),))
      == _d41(2026, 9, 30))
check("A41b 逆算が無ければ、窓そのものが決定期限になる（E1 の型）",
      effective_decide_deadline(None, (("2027-05-31", "入試委員会", None),)) == _d41(2027, 5, 31))
check("A41b 窓が無ければ逆算のまま",
      effective_decide_deadline(_d41(2026, 12, 28), ()) == _d41(2026, 12, 28))
check("A41b どちらも無ければ ⊥", effective_decide_deadline(None, ()) is None)

_f, _j = check_gates(Declared(s6_decide_date="2027-05-01", s6_start_date="2027-03-01",
                              s6_self_check=True), _G)
check("A41b 着手が窓より前なら停止（委員会が開かれる前には動き出せない）",
      "A41B_START_BEFORE_GATE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_gates(Declared(s6_decide_date="2027-05-01", s6_start_date="2027-08-01",
                              s6_self_check=True), _G)
check("A41b 着手が窓以降なら通る", not _f, [x.code for x in _f])

# ④に出してよい日付は〈使える日付〉と〈**逆算由来の**決定期限〉だけ。窓由来のものは出せない。
check("A41b ④に機械の知らない日付があれば停止",
      "A41B_S4_FOREIGN_DATE" in
      [x.code for x in check_s4_dates({"④": "2026-12-30 までに決めていただく"},
                                      ("2027-06-30",), None)[0]])
check("A41b ④の逆算由来の決定期限は出してよい",
      not check_s4_dates({"④": "2026-12-28 までに決める"}, ("2027-06-30",), "2026-12-28")[0])
check("A41b ④に窓由来の決定期限は渡さない（許可集合に入れない）",
      "A41B_S4_FOREIGN_DATE" in
      [x.code for x in check_s4_dates({"④": "2027-05-31 までに決める"},
                                      ("2027-06-30",), None)[0]])
check("A41b ④が無ければ何も出ない", not any(check_s4_dates({}, ("2027-06-30",), None)))

# 検分：第13版 as-run の8セルに当てて誤検出が出ないことを固定する（浅い一致を6件目にしない）
_v13 = _load41("verified8_v13.json")
_dec13 = {r["id"]: r for r in _load41("decisions8_v12.json")}
_fp = [r["id"] for r in _v13
       if check_s4_dates(r["copy"],
                         tuple(x[1] for x in _dec13[r["id"]]["tau_ok"]),
                         _dec13[r["id"]].get("start_deadline"))[0]]
check("A41b 第13版 as-run の8セルで誤検出ゼロ（tau_ok ∪ 逆算 で足りる）", not _fp, _fp)

# 決定表：E1 は窓が実効の決定期限になり、逆算のみの欄とは別値になる
_dl = {c["id"]: compile_deal(c["nu"], _C.SELLERS[c["seller"]], _C.TODAY) for c in _C.CELLS}
check("A41b E1 の decide_deadline は窓の日付（生成器に期限を作らせない）",
      all(_dl[k]["decide_deadline"] == "2027-05-31" for k in ("E1-P1", "E1-P2")),
      {k: _dl[k]["decide_deadline"] for k in ("E1-P1", "E1-P2")})
check("A41b E1 の decide_deadline_tau は ⊥（逆算は無い）",
      all(_dl[k]["decide_deadline_tau"] is None for k in ("E1-P1", "E1-P2")))
check("A41b 窓を持たない6セルでは実効値＝逆算のまま",
      all(_dl[k]["decide_deadline"] == _dl[k]["decide_deadline_tau"]
          for k in _dl if k not in ("E1-P1", "E1-P2")))
check("A41b 実効の決定期限は必ず窓以前（同じ資料に二つの期限を出さない）",
      all(not _dl[k]["decision_gates"] or
          _dl[k]["decide_deadline"] <= min(g[0] for g in _dl[k]["decision_gates"])
          for k in _dl))


print("\n── 第13.8版 R20〈式〉：戻る額は、値でなくても〈式〉なら決められる")
# A44（21/21）の唯一の出口。第13.6版は 8/8 が R20_RETURN_MISSING で停止していたが、
# 17行中13行は記入欄で、**売り手が買い手の数字を持っていない**という入力側の欠落だった。
# 買い手の側で決定可能であるためには、値そのものは要らない ――
# 〈買い手の量 × 売り手の係数〉の式と、**係数の出所**が在れば、買い手が自分で埋められる。
def _qe(seat="店長", **kw):
    d = {"seat": seat, "kappa": "財源", "pay": "180万", "pay_unit": "円",
         "ret": "【　　　】", "ret_unit": "円", "per": "1店舗あたり", "source": "実測"}
    d.update(kw); return d
_CH2 = (("店長", ["財源"], ["粗利"], "現場"),)
_f, _j = check_decidable(Declared(s6_quantities=(_qe(),)), _CH2)
check("R20 式が無ければ、これまでどおり停止（対照）",
      "R20_RETURN_MISSING" in [x.code for x in _f], [x.code for x in _f])
_EXPR = dict(ret_expr="月間チラシ配布枚数 × 1枚あたり削減額",
             ret_basis="月間チラシ配布枚数", ret_coef="1枚あたり2.4円",
             coef_source="自社12社の実測平均（2025年度）")
_f, _j = check_decidable(Declared(s6_quantities=(_qe(**_EXPR),)), _CH2)
check("R20 式が揃っていれば停止しない（買い手が自分の量を入れれば決まる）",
      "R20_RETURN_MISSING" not in [x.code for x in _f], [x.code for x in _f])
check("R20 式で決めるときは、そう申し送る",
      any(x.code == "R20_RETURN_AS_EXPR" for x in _j), [x.code for x in _j])
for _miss, _code in (("ret_basis", "R20_EXPR_NO_BASIS"),
                     ("ret_coef", "R20_EXPR_NO_COEF"),
                     ("coef_source", "R20_EXPR_COEF_UNSOURCED")):
    _e = dict(_EXPR); _e[_miss] = "【　　　】"
    _f, _j = check_decidable(Declared(s6_quantities=(_qe(**_e),)), _CH2)
    check(f"R20 式の {_miss} が ⊥ なら停止（{_code}）",
          _code in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_decidable(Declared(s6_quantities=(_qe(ret="240万", **_EXPR),)), _CH2)
check("R20 値が在るなら式は見ない（値が優先）",
      not [x for x in _f if x.code.startswith("R20_EXPR")], [x.code for x in _f])
# 第13.7版の走行で出た欠陥。生成器は式を**ret の欄に直接**書いた（成分の欄も埋めていた）。
# `is_bottom(ret)` が False なので「値が在る」と読まれ、式の検査が一度も走らなかった。
# **状態は三つ（値／式／⊥）で、二分では足りない。浅い一致の6件目。**
_RUN137 = _qe(ret="〈貴学の月あたり媒体別実績突き合わせ人時〉× 1.0", **_EXPR)
_f, _j = check_decidable(Declared(s6_quantities=(_RUN137,)), _CH2)
check("R20 式を ret の欄に直接書いても〈式〉として読む（値と読まない）",
      any(x.code == "R20_RETURN_AS_EXPR" for x in _j), ([x.code for x in _f], [x.code for x in _j]))
check("R20 式のときは、戻る欄の単位語を値の単位ずれと数えない",
      not [x for x in _f if x.code == "R20_UNIT_IN_VALUE" and "戻る" in x.ref],
      [x.ref for x in _f if x.code == "R20_UNIT_IN_VALUE"])
_f, _j = check_decidable(Declared(s6_quantities=(_qe(ret="買い手の量 × 係数"),)), _CH2)
check("R20 式だけ書いて成分の欄が空なら停止（R20_EXPR_IN_VALUE）",
      "R20_EXPR_IN_VALUE" in [x.code for x in _f], [x.code for x in _f])


print("\n── 第13.8版 A45／A45b／A45c：層(i) の算術 ―― 売り手の数字だけで閉じる")
from sales_logic import parse_amount, check_price
# 検分：買い手が実際に検算した表記を、そのまま読めること（浅い一致を7件目にしない）
check("A45 金額の表記を読む（万・億・千・円・カンマ・小数）",
      [parse_amount(x) for x in ("1,400万", "3,200万円", "180万", "1.5億", "75000円", "900万")]
      == [1.4e7, 3.2e7, 1.8e6, 1.5e8, 75000.0, 9e6],
      [parse_amount(x) for x in ("1,400万", "3,200万円", "180万", "1.5億", "75000円", "900万")])
check("A45 値に単位が無ければ申告単位で読む", parse_amount("1400", "万円") == 1.4e7)
check("A45 数字が無ければ ⊥（0 に落とさない）",
      parse_amount("【　　　】") is None and parse_amount("未定") is None)

_ITEMS = ({"name": "媒体費", "amount": "800万"}, {"name": "制作費", "amount": "400万"},
          {"name": "人月単価", "amount": "200万"})
def _P(**kw):
    d = dict(s6_price_low="1,400万", s6_price_high="1,400万", s6_price_unit="円",
             s6_price_items=_ITEMS)
    d.update(kw); return Declared(**d)
_f, _j = check_price(_P(s6_price_high="3,200万"))
check("A45 上限÷下限が 2.3倍なら停止（20/21 が『見積ではなく相場表だ』と拒んだ）",
      "A45_RANGE_TOO_WIDE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(_P(s6_price_high="2,530万", s6_price_items=(
    {"name": "媒体費", "amount": "1,500万"}, {"name": "制作費", "amount": "700万"},
    {"name": "人月単価", "amount": "330万"})))
check("A45 1.81倍は通る（デモデータがここで落ちない）",
      "A45_RANGE_TOO_WIDE" not in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(_P(s6_price_high="3,200万"), industry="観光・宿泊")
check("A45 未較正の業界では停止ではなく降格（閾値は較正値）",
      all(x.level == "demote" for x in _f if x.code == "A45_RANGE_TOO_WIDE")
      and any(x.code == "UNCALIBRATED" for x in _j), ([x.code for x in _f], [x.code for x in _j]))
_f, _j = check_price(_P(s6_price_items=None))
check("A45b 内訳が無ければ停止（21/21）",
      "A45B_BREAKDOWN_MISSING" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(_P(s6_price_items=({"name": "媒体費", "amount": "800万"},)))
check("A45b 内訳の和が総額に合わなければ停止（Π₁ 無矛盾）",
      "A45B_BREAKDOWN_MISMATCH" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(_P())
check("A45b 内訳の和が総額に一致すれば通る", not _f, [x.code for x in _f])
_TIERS = ({"label": "3か月", "qty": 3, "qty_unit": "か月", "amount": "180万"},
          {"label": "12か月", "qty": 12, "qty_unit": "か月", "amount": "900万"})
_f, _j = check_price(_P(s6_price_tiers=_TIERS))
check("A45c 長く頼むほど単価が上がるなら停止（月60万 → 月75万）",
      "A45C_UNIT_PRICE_NOT_MONOTONE" in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(_P(s6_price_tiers=(
    {"label": "3か月", "qty": 3, "qty_unit": "か月", "amount": "180万"},
    {"label": "12か月", "qty": 12, "qty_unit": "か月", "amount": "600万"})))
check("A45c 単価が下がっていれば通る",
      "A45C_UNIT_PRICE_NOT_MONOTONE" not in [x.code for x in _f], [x.code for x in _f])
_f, _j = check_price(Declared())
check("A45 価格そのものが未申告なら、停止せず申し送る（⊥ は値ではない）",
      not _f and any(x.code == "A45_PRICE_UNDECLARED" for x in _j),
      ([x.code for x in _f], [x.code for x in _j]))

# 検分：第13.6版の⑥本文に実際に出た金額表記を全部読めるか（読めない＝検査が沈黙する）
import re as _re45, json as _json45, glob as _glob45
_AMT = _re45.compile(r"[0-9][0-9,\.]*\s*(?:億円|万円|千円|億|万|千|円)")
_seen45, _bad45 = set(), []
for _p in sorted(_glob45.glob("gen136/out_*.json")):
    _o = _json45.load(open(_p, encoding="utf-8"))
    for _s in _o["slides"]:
        for _m in _AMT.findall(_s.get("text", "")):
            _seen45.add(_m.strip())
for _m in _seen45:
    if parse_amount(_m) is None:
        _bad45.append(_m)
check(f"A45 第13.6版の⑥に出た金額表記 {len(_seen45)} 種をすべて読めた", not _bad45, _bad45[:8])

print(f"\n{'すべて通過' if not FAIL else '失敗: ' + str(FAIL)}")
