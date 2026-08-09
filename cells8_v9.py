# -*- coding: utf-8 -*-
"""第9版 ―― 業界の側から入った修正を入力に反映したもの。

第8版の8セルとの差は4点だけで、いずれも**業界を調べないと埋まらない欄**である。
  座席の由来      学部長会は学校教育法が置いた座席／バイヤーはチェーンの組織設計
  決定が締まる日  出願開始日ではなく募集要項の確定日／棚替え日ではなく定番改訂の商談日
  窓の多重度      入試は総合型・学校推薦型・一般選抜の3経路が並行する
  無料の手段      卸・メーカーの販促支援は小売では無償が慣行
  D5 の拘束者     枠を決めているのが読み手自身なら、資源配分では消せない
"""
import copy, json
from dataclasses import replace
from sales_logic import Seat, TauItem, Mi, Scope, compile_deal
import cells8_v8 as B

TODAY = B.TODAY

ORIGIN = {
    "学部長会": "制度",            # 学校教育法93条（教授会）・私立学校法
    "理事会": "制度",
    "商品本部バイヤー": "組織",     # チェーンオペレーション上の分業
    "店舗運営部": "組織",
    "入試広報課長": "組織", "教務主任": "個人", "理事長": "個人",
    "社長": "個人", "店長": "個人",
}
# 制度由来の座席は |κ|=1。学部長会＝説明可能性、理事会＝財源（第8版の入力で既に単一）

# ── 決定が締まる日（A18）。業界の取引慣行を調べて初めて分かる欄
TAU_YOKO = TauItem("A", date_ := __import__("datetime").date(2027, 5, 31), "契約", "未知",
                   q="募集要項の確定までに接触できていない高校の数", q_kappa="実務性", q_recast=True,
                   q_source="買い手データ", q_low=40, q_high=70, scope=B.SC_UNIV,
                   q_receipt="2026-07-15 入試広報課より受領。高校訪問記録から未接触校を抽出",
                   decision=True, windows=1, binders=("学内の入試委員会",))
TAU_SHODAN = TauItem("A", __import__("datetime").date(2026, 11, 30), "契約", "未知",
                     q="定番改訂の商談までに確定していない売場の作業時間", q_kappa="実務性", q_recast=True,
                     q_source="買い手データ", q_low=900, q_high=1400, scope=B.SC_SUPER,
                     q_receipt="2026-07-28 店舗運営部より受領。全店の作業割当表",
                     decision=True, windows=1, binders=("主要卸（一次問屋）",))

FIX_TAU = {"E1": [TAU_YOKO, replace(B.TAU_HYOKA, decision=True, windows=1)],
           "E2": [replace(B.TAU_SENSHU, decision=False, windows=3)],   # ← 4/1 は結果が出る日
           "R1": [TAU_SHODAN, replace(B.TAU_KOUREI, decision=True, windows=1)],
           "R2": [replace(B.TAU_TANA, decision=False, windows=1),      # ← 単独店では自分で動かせる
                  replace(B.TAU_KOUREI, decision=True, windows=1)]}

D5_BINDER = {"E1": "法人事務局", "E2": "理事長", "R1": "店舗運営部", "R2": "社長"}

CELLS = []
for c0 in B.CELLS:
    c = dict(c0); nu = copy.deepcopy(c0["nu"]); seg = c["id"][:2]
    nu.J = [replace(j, origin=ORIGIN.get(j.name, "個人")) for j in nu.J]
    nu.tau = FIX_TAU[seg]
    nu.M = [replace(m, binders=(("D5", D5_BINDER[seg]),)) if "D5" in m.dims else
            (replace(m, cost_to_buyer=0.0) if "卸" in m.name else m) for m in nu.M]
    c["nu"] = nu; CELLS.append(c)
SELLERS = B.SELLERS


def run(dump="decisions8_v9.json"):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id", "業界", "セグメント", "商材")}
        rec.update({k: d.get(k) for k in ("generate", "sigma", "kappa_n", "chain",
                                          "tau_ok", "blocks", "rules", "executors")})
        rec["findings"] = [{"code": f.code, "level": f.level, "ref": f.ref,
                            "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]]
        out.append(rec)
    json.dump(out, open(dump, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in out:
        st = [f"{f['code']}({f['ref']})" for f in r["findings"] if f["level"] == "stop"]
        rj = [f"{f['code']}" for f in r["findings"] if f["level"] in ("reject", "demote")]
        print(f"{r['id']:6s} {'生成可' if r['generate'] else '★不成立'}  " +
              (f"停止{st} " if st else "") + (f"棄却/降格{rj}" if rj else ""))
    print(f"\n生成可 {sum(1 for r in out if r['generate'])}/{len(out)}")
    return out


if __name__ == "__main__":
    run()
