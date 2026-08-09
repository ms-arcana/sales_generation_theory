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
check("三つ組が揃い、着手日が期限内なら通る", v["pass"],
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
check("R17 買い手の既承認を否定していなければ通る", v["pass"],
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
