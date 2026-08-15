# -*- coding: utf-8 -*-
"""決定的レンダラ ―― **⑥のどこまで LLM 抜きで出せるか**（引き継ぎ書 第14版 §5 #5）。

`設計メモ-決定的レンダラ.md` の実装。**LLM を呼ばない。標準ライブラリだけ。**

    入力  decisions8_v13.json（決定表）＋ messages.json（塊の名）
    出力  ⑥の表3つ ＋ 定型文 ＋ 記入欄。散文の位置にはプレースホルダを残す
          そのまま `validate_copy` に通せる（`--check`）

**数字を作らない。**決定表に無い量は `【　　　】`（記入欄＝⊥）で出す。
`is_bottom` はこれを ⊥ と読むので、`R20_RETURN_MISSING` が正しく立つ。
**それが正しい振る舞いである** ―― 設計メモ §4「そのときは『不明』と書くのが正しい」。

    python3 render_slides.py                # 8セル分を組んで、被覆と字数を出す
    python3 render_slides.py --cell E1-P1    # 1セルの⑥を印字
    python3 render_slides.py --check         # 組んだ⑥を validate_copy に通す

測りたいのは一つ ―― **決定的に出せる塊はいくつか。**設計メモは「16のうち13」と見積もった。
"""
import argparse
import json
import sys
from datetime import date

import stamp

SLOT = "【　　　】"                    # 営業が埋める記入欄。**⊥ である**（`is_bottom`）
MSG = json.load(open("messages.json", encoding="utf-8"))
BLOCK_NAME = MSG["blocks"]


# ══════════════════════════════════════════════ 暦（決定表の値だけで閉じる）
# **暦の算術を書き直さない。**`sales_logic` の関数をそのまま使う。
# 書き直すと同じ計算の担体が二つになり、片方だけが古びる（型5・第14版 N₆ 追補）。
# 最初の実装は `add_months` を写して繁忙期を避けず、`A43_REALIZE_IN_BUSY` が 5/8 で立った。
from sales_logic import add_months, earliest_realize   # noqa: E402


def dates_of(rec):
    """決定・着手・実現の三段（A37）。**決定表に在る値からしか作らない。**"""
    dec = rec.get("decide_deadline")
    lt = rec.get("lt_months")
    omega = rec.get("omega")
    start = realize = None
    if dec and isinstance(lt, int):
        base = date.fromisoformat(dec)
        start = add_months(base, lt).isoformat()
        if isinstance(omega, int):
            # 繁忙期を避けるのは `earliest_realize` の仕事。ここでは呼ぶだけ（A43）
            realize = earliest_realize(base, lt, omega,
                                       rec.get("busy_months") or ()).isoformat()
    return dec, start, realize


# ══════════════════════════════════════════════ 表（完全に決定的）
def table_quantities(rec):
    """表1 座席ごとの量 ―― 列は N₄′ の六つ組そのもの。**列が在るので型1が起きない。**"""
    rows = []
    for seat, kappas, forms, origin in (rec.get("chain") or []):
        rows.append([seat, "／".join(kappas), SLOT, SLOT, SLOT, SLOT, SLOT])
    return (["座席", "基準", "払う", "単位", "戻る", "何あたり", "出所"], rows)


def table_coverage(rec):
    """表2 ④で数えた量のうち、本提案が消す部分の対応"""
    rows = []
    for name, val in (rec.get("buyer_quantities") or []):
        num, _, src = str(val).partition("／出所 ")
        rows.append([name, num.strip() or SLOT, SLOT, SLOT, src.strip() or SLOT])
    return (["④で数えた量", "いまの値", "本提案が消す分", "残る分", "出所"], rows)


def table_realize(rec):
    """表3 浮いた分を誰がいつどの費目で減らすか（A24 は三つ組を割ってある）"""
    _, start, realize = dates_of(rec)
    rows = []
    for actor, accounts in (rec.get("executors") or []):
        for acct in accounts:
            rows.append([actor, realize or SLOT, acct, SLOT])
    return (["誰が", "いつ", "どの費目", "同意の確認"], rows)


def md_table(head, rows):
    if not rows:
        return f"| {' | '.join(head)} |\n|{'---|' * len(head)}\n| {' | '.join([SLOT] * len(head))} |"
    out = [f"| {' | '.join(head)} |", "|" + "---|" * len(head)]
    out += [f"| {' | '.join(str(c) for c in r)} |" for r in rows]
    return "\n".join(out)


# ══════════════════════════════════════════════ 定型文（差し込み。作文ではない）
def fixed_blocks(rec):
    """塊コード → 本文。**決定表に値が無ければ作らず、記入欄で出す。**"""
    dec, start, realize = dates_of(rec)
    out = {}

    out["B_deadline"] = (
        f"【期日】決定が締まる日は {dec or SLOT}。本紙で決定の期限はこの一つです。"
        f"決めてから動き出すまで {rec.get('lt_months', SLOT)}か月かかるため、着手は {start or SLOT}。"
        f"効果が数字に出るのは着手から {rec.get('omega', SLOT)}か月後です。")

    gates = rec.get("decision_gates") or []
    if gates:
        g = "、".join(f"{d}（{who}）" for d, who, _ in gates)
        out["B_authority"] = f"【判断権の所在】この決定は {g} を通った後でなければ動けません。"

    tau = rec.get("tau_ok") or []
    if tau:
        parts = [f"{d} は{src}が握る期日で、効く相手は限られます（出所：{src}）"
                 for _, d, src, _ in tau]
        out["B_third_party"] = "【第三者拘束の実際】" + "。".join(parts) + "。"
        out["B_scope_of_date"] = (
            "【その日付が誰に効くか】" + "、".join(f"{d} は{src}由来" for _, d, src, _ in tau)
            + f"。{SLOT} に該当する場合に効きます。")

    if rec.get("busy_months"):
        bm = "・".join(f"{m}月" for m in rec["busy_months"])
        out["B_why_now"] = (f"【今すぐやる理由】{bm} は貴組織の繁忙のため着手できません。"
                            f"逆算すると決定は {dec or SLOT} までです。")

    out["B_trial"] = (f"【試せる仕掛け】着手から {rec.get('omega', SLOT)}か月を試行区間とし、"
                      f"範囲は {SLOT} に絞ります。ここで止めれば {SLOT} で終わります。"
                      f"試行区間は自動では続きません。")
    out["B_migration"] = (f"【段階導入】第1段階は {start or SLOT} から "
                          f"{rec.get('omega', SLOT)}か月、範囲は {SLOT}。"
                          f"第2段階は {realize or SLOT} から、範囲を {SLOT} へ。")

    fm = [(s, f) for s, _, f, _ in (rec.get("chain") or [])]
    if fm:
        out["B_form_mapping"] = "【呼び名と科目名の対応】" + "、".join(
            f"{s} では「{'・'.join(forms)}」" for s, forms in fm) + f"。本提案の呼び名は {SLOT}。"

    five = rec.get("five_mentions") or []
    if five:
        out["B_opportunity_cost"] = ("【機会費用】この予算を使わない場合、"
                                     + "、".join(f"「{x}」" for x in five)
                                     + f" という選び方があります。その場合の負担は {SLOT}、"
                                       f"止まるのは {SLOT} です。")
    delta = rec.get("delta") or []
    if delta:
        out["B_intra_category"] = ("【カテゴリ内で残る根拠】" + "、".join(
            f"「{n}」は{k}" for n, k, _, _ in delta) + f" として扱いました。残る根拠は {SLOT}。")

    out["B_draft_reason"] = (f"【起案理由文】{SLOT} までに整えるべき {SLOT} のうち "
                             f"{SLOT} を、{SLOT} するため。")
    out["B_summary_sheet"] = ("【上申用サマリ】予算科目：" + "／".join(
        a for _, accts in (rec.get("executors") or []) for a in accts) or SLOT) + \
        f"／金額：{SLOT}／回収年数：{SLOT}"
    out["B_human_slot"] = (f"【営業が埋める欄】上の表の {SLOT} は、"
                           f"聞き取りで埋めてから出すこと。埋めずに出さない。")
    out["B_prohibition"] = f"【禁制】本紙が引き受けないのは {SLOT} です。"
    out["B_liability_matrix"] = f"【責任分界】{SLOT} は貴組織、{SLOT} は当社が持ちます。"
    out["B_certification"] = f"【認証・お墨付き】{SLOT}"
    # **設計語を紙に出さない**（R9）。最初の実装は括弧内に `拘束の所在` と書いて
    # `R9_V0` が 6/8 で立った。**テンプレートからも漏れる** ―― 設計メモ §1 の警告そのもの。
    out["B_case_numbers"] = f"【数字入りの事例】{SLOT}（同じ決まり方をしている先の実名と数字）"
    out["B_precedent"] = f"【前例】{SLOT}"
    out["B_spec_table"] = f"【仕様一覧】{SLOT}"
    out["B_mechanism"] = f"【仕組み】{SLOT}"
    out["B_what_is_it"] = f"【そもそも何か】{SLOT}"
    out["B_visualize"] = f"【困りごとの見える化】{SLOT}"
    out["B_kappa_quantity"] = "【最終裁定点の基準で読める量】上の表1のとおり。"
    out["B_coverage_table"] = "【数えた量と消す部分の対応】上の表2のとおり。"
    out["B_realize"] = "【誰がいつどの費目で減らすか】上の表3のとおり。"
    # 表1が担うもの ―― 座席ごとに一行なので、**塊としては表そのもの**（型1が起きない形）
    out["B_seat_quantities"] = ("【読む座席ごとに一つずつ置いた量】上の表1のとおり。"
                                "座席ごとに一行で、連結していません。")
    # 期日の塊は担体で割れている（A37b）。決定の締切であることを明示する
    out["B_decision_date"] = (f"【この日付は決定の締切です】{dec or SLOT} は"
                             f"〈決定が締まる日〉であって〈着手日〉ではありません。"
                             f"着手は {start or SLOT}、効果が出るのは {realize or SLOT} です。")
    if fm := [(s, f) for s, _, f, _ in (rec.get("chain") or [])]:
        out["B_chain_form"] = ("【中間座席の様式語との対応】" + "、".join(
            f"{s} は「{'・'.join(forms)}」で読みます" for s, forms in fm) + "。")
    return out


# 散文が要る塊 ―― **ここだけ LLM。**設計メモ §2(c)
#   比較・否定していない確認・下向き資料・自社案への自己適用。いずれも
#   〈買い手の語とこちらの新語のあいだの写像〉か〈論理の向きの反転〉で、差し込みでは書けない。
PROSE_BLOCKS = {"B_compare_current", "B_own_check", "B_downward", "B_self_check", "B_layer_a"}


def render_s6(rec):
    """⑥を組む。返り値は (本文, 決定的に出した塊, 散文へ回した塊)"""
    need = list(rec.get("blocks") or [])
    fixed = fixed_blocks(rec)
    body, done, prose = [], [], []

    body.append("〔表1 座席ごとの量〕")
    body.append(md_table(*table_quantities(rec)))
    body.append("\n〔表2 ④で数えた量のうち本提案が消す分〕")
    body.append(md_table(*table_coverage(rec)))
    body.append("\n〔表3 浮いた分を誰がいつどの費目で減らすか〕")
    body.append(md_table(*table_realize(rec)))
    body.append("")

    for b in need:
        if b in PROSE_BLOCKS:
            prose.append(b)
            body.append(f"〔散文：{BLOCK_NAME.get(b, b)}〕")
        elif b in fixed:
            done.append(b)
            body.append(fixed[b])
        else:
            prose.append(b)
            body.append(f"〔散文：{BLOCK_NAME.get(b, b)}〕")
    return "\n".join(body), done, prose


def build(rec):
    """⑥だけ差し替えた copy と、**組んだものと矛盾しない** declared を返す"""
    s6, done, prose = render_s6(rec)
    sigma = rec.get("sigma") or ["②", "③", "④", "⑤", "⑥"]
    copy = {s: (s6 if s == "⑥" else f"〔散文：{s}〕") for s in sigma}
    dec_d, start, realize = dates_of(rec)
    _, rows = table_quantities(rec)
    declared = {
        "s6_decide_date": dec_d, "s6_start_date": start,
        "s6_kappa": sorted({k for _, ks, _, _ in (rec.get("chain") or []) for k in ks}),
        "s6_kappa_type": "flow",
        "s6_ends_imperative": False, "s6_contains_promise": False,
        "s5_is_constraint_disclosure": True,
        "s6_table_rows": sum(len(t[1]) for t in
                             (table_quantities(rec), table_coverage(rec), table_realize(rec))),
        "s6_omitted_blocks": [], "s2_asks_possession": False, "s5_disclaimers": [],
        # **数字を作らない。**量は記入欄のまま申告する（⊥ を ⊥ として出す）
        "s6_quantities": [{"seat": r[0], "kappa": r[1], "pay": SLOT, "pay_unit": SLOT,
                           "ret": SLOT, "ret_unit": SLOT, "per": SLOT,
                           "pay_source": SLOT, "ret_source": SLOT} for r in rows],
        "s6_realize": [{"actor": a, "date": realize or SLOT, "account": acct}
                       for a, accts in (rec.get("executors") or []) for acct in accts],
    }
    return copy, declared, done, prose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dec", default="decisions8_v13.json")
    a = ap.parse_args()

    recs = stamp.load(a.dec)
    if a.cell:
        recs = [r for r in recs if r["id"] == a.cell] or sys.exit(f"{a.cell} が無い")

    print(f"══ 決定的レンダラ ―― ⑥を決定表から組む（LLM を呼ばない）  表：{a.dec}\n")
    if a.cell:
        copy, _, done, prose = build(recs[0])
        print(copy["⑥"])
        print(f"\n── 決定的 {len(done)} 塊／散文へ {len(prose)} 塊："
              f"{[BLOCK_NAME.get(b, b) for b in prose]}")
        return

    print(f"{'cell':8}{'要る塊':>6}{'決定的':>7}{'散文':>6}{'⑥字数':>8}{'表の行':>7}  散文へ回した塊")
    t_need = t_done = 0
    for r in recs:
        copy, decl, done, prose = build(r)
        t_need += len(done) + len(prose)
        t_done += len(done)
        print(f"{r['id']:8}{len(done)+len(prose):>6}{len(done):>7}{len(prose):>6}"
              f"{len(copy['⑥']):>8}{decl['s6_table_rows']:>7}  "
              f"{'／'.join(BLOCK_NAME.get(b, b) for b in prose)}")
    print(f"\n  合計 {t_done}/{t_need} 塊が決定的に出せる"
          f"（{100*t_done//max(t_need,1)}%）。設計メモの見積りは 16 中 13＝81%")

    if a.check:
        import validate8_v12 as V
        print("\n── 組んだ⑥を validate_copy に通す（⑥由来のものだけ数える）")
        for r in recs:
            copy, decl, _, _ = build(r)
            _, _, v = V.score(r, {"cell_id": r["id"],
                                  "slides": [{"stage": s, "text": t} for s, t in copy.items()],
                                  "declared": decl})
            stops = sorted({f.code for f in v["findings"] if f.level == "stop"})
            print(f"  {r['id']:8} 停止 {len(stops):2}  {stops}")
        print("\n  ※ `R20_*` が立つのは**正しい**。決定表に〈払う〉〈戻る〉が無いからで、")
        print("     生成の失敗ではなく**入力の欠落**である（設計メモ §4 の三つ目の切り分け）。")


if __name__ == "__main__":
    main()
