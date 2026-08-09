# -*- coding: utf-8 -*-
"""第7版 ―― 執行座席 W と受領記録を入れた入力。

第6版の8セルは、W が空欄のまま生成された。8人全員がそこを突いた——
「浮いた分を、誰が、いつ、どの費目の支払い減として確定させるのか」。
W は顧客軸の必須入力になった。営業が最初に聞き取るべき三つ目の集合である。
"""
import copy
import json
from dataclasses import replace
from datetime import date
from sales_logic import Executor, compile_deal
import cells8_v6b as B

TODAY = B.TODAY

# ───────────────────────────────────────────── W：決めないが動かす座席
W = {
    "F1": [Executor("工場長", frozenset({"応援労務費", "残業手当"})),
           Executor("親会社 人事部", frozenset({"要員"}))],
    "F2": [Executor("社長", frozenset({"要員", "残業手当", "外注加工費"}))],
    "K1": [Executor("作業所長", frozenset({"常用の人工", "外注費"})),
           Executor("本社 工務部", frozenset({"実行予算"}))],
    "K2": [Executor("工事課長", frozenset({"出面"})),
           Executor("社長", frozenset({"常用の人工", "請求"}))],
}

# ───────────────────────────────────────────── 受領記録（A15）
RECEIPT = {
    "切替時に発生する増員工数（人日）":
        "2026-07-22 工場長より受領。第二工場の応援伝票（2025年4月〜2026年3月）を段取り替え日で抽出",
    "再認証審査までに標準作業書を改訂すべき工程数":
        "2026-07-22 生産技術部より受領。前回審査時の是正対象工程一覧",
    "竣工から逆算した着手期限までの残余（日）":
        "2026-07-30 作業所長より受領。当該工区の工程表（週間・月間）から手待ち日を集計",
    "年度内に消化できない工期（日）":
        "2026-07-30 工務部より受領。過去3年度の繰越工事一覧",
}


def fix_tau(t):
    if t.q_source != "買い手データ" or t.q_receipt:
        return t
    return replace(t, q_receipt=RECEIPT.get(t.q, ""))


CELLS = []
for c0 in B.CELLS:
    c = dict(c0)
    nu = copy.deepcopy(c0["nu"])          # 第6版の入力を壊さない（回帰テストで両方使う）
    nu.W = W[c["id"][:2]]
    nu.tau = [fix_tau(t) for t in nu.tau]
    c["nu"] = nu
    CELLS.append(c)

SELLERS = B.SELLERS


def run(dump="decisions8_v7.json"):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id", "業界", "セグメント", "商材")}
        rec.update({k: d.get(k) for k in
                    ("generate", "sigma", "sigma_by", "j_star", "kappa_n", "form_n",
                     "tau_ok", "delta", "five_mentions", "d7_basis", "blocks", "rules",
                     "executors", "start_deadline", "llm_calls")})
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
              f"  着手期限={r['start_deadline']}  W={len(r['executors'] or [])}")
        if st: print("          停止", st)
        if rj: print("          棄却", rj)
    print(f"\n生成可 {sum(1 for r in out if r['generate'])}/{len(out)}")
    return out


if __name__ == "__main__":
    run()
