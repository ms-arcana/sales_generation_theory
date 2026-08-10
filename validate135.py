# -*- coding: utf-8 -*-
"""第13.5版 ―― A37（決定日／着手日／実現日）だけを直した8体を、機械側で採点する（層3.5）。

    gen135/out_<ID>.json   … 今回の生成物
    decisions8_v12.json    … 指示文を組んだのと同じ表（decide_deadline / lt_months / today を持つ）
    predict_v13_5.md       … 走行前に置いた予測（P4〜P7 がここの対象）

  python3 validate135.py
"""
import json
import sys
from collections import Counter

from stamp import load as unwrap, dump_stamped
from sales_logic import iso_date, add_months
from validate8_v12 import score

IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
OUT = "verified135.json"

# 走行前に置いた予測（predict_v13_5.md §2）。範囲はタプル
PRED = {
    "P4 機械側の停止（セル数）": (0, 1, 2),
    "P5 s6_decide_date を埋めた": 8,
    "P6 着手 ≥ 決定＋LT": (6, 7, 8),
    "P7 realize の〈いつ〉が着手以降": (5, 6, 7, 8),
}


def hit(pred, got):
    return got in pred if isinstance(pred, tuple) else got == pred


def main():
    dec = {r["id"]: r for r in unwrap("decisions8_v12.json")}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    rows, out = [], []

    for cid in IDS:
        path = f"gen135/out_{cid}.json"
        try:
            g = unwrap(path)
        except FileNotFoundError:
            print(f"★ {path} が無い"); sys.exit(1)
        d = dec[cid]
        copy, D, v = score(d, g)
        codes = [f.code for f in v["findings"]]
        jc = [x.code for x in v["needs_judgment"]]

        dd = d.get("decide_deadline") or d.get("start_deadline")
        lt = d["lt_months"]
        d0, d1 = iso_date(D.s6_decide_date or ""), iso_date(D.s6_start_date or "")
        # 三段が実際に並んでいるか（機械の検査とは別に、ここでも直に見る）
        gap_ok = bool(d0 and d1 and d1 >= add_months(d0, lt))
        rz = [iso_date(str(x[1])) for x in (D.s6_realize or ())]
        rz_ok = bool(d1) and all(x and x >= d1 for x in rz) and bool(rz)

        row = {
            "id": cid, "商材": d["商材"], "LT": lt, "決定期限": dd,
            "決定日": D.s6_decide_date, "着手日": D.s6_start_date,
            "必要着手": add_months(d0, lt).isoformat() if d0 else None,
            "実現日": [str(x[1]) for x in (D.s6_realize or ())],
            "gap_ok": gap_ok, "rz_ok": rz_ok,
            "stop": sum(1 for f in v["findings"] if f.level == "stop"),
            "stops": [f"{f.code}({f.ref})" for f in v["findings"] if f.level == "stop"],
            "A37": [c for c in codes if c.startswith("A37")] + [c for c in jc if c.startswith("A37")],
            "R12b": [c for c in codes if c.startswith("R12b")] + [c for c in jc if c.startswith("R12b")],
            "⑥字数": len(copy.get("⑥", "")),
            "pass": v["pass"],
        }
        rows.append(row)
        out.append({"id": cid, "row": row, "declared": g.get("declared"),
                    "self_report": g.get("self_report"), "copy": copy,
                    "findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                                  "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
                    "needs_judgment": [{"code": x.code, "ref": x.ref,
                                        "msg": msgs["judgments"].get(x.code, x.code)}
                                       for x in v["needs_judgment"]]})
    dump_stamped(out, OUT)

    print("══ 第13.5版 8体：日付の三段")
    hdr = ("id", "LT", "決定期限", "決定日", "着手日", "必要着手", "gap_ok", "rz_ok", "stop")
    print("  " + "".join(f"{h:>12s}" for h in hdr))
    for r in rows:
        print("  " + "".join(f"{str(r[h]):>12s}" for h in hdr))
    for r in rows:
        if r["実現日"]:
            print(f"     {r['id']} 実現日 {r['実現日']}")
        if r["stops"]:
            print(f"     {r['id']} 停止 {r['stops']}")
        if r["A37"] or r["R12b"]:
            print(f"     {r['id']} 日付判定 {r['A37'] + r['R12b']}")

    got = {
        "P4 機械側の停止（セル数）": sum(1 for r in rows if r["stop"]),
        "P5 s6_decide_date を埋めた": sum(1 for r in rows if r["決定日"]),
        "P6 着手 ≥ 決定＋LT": sum(1 for r in rows if r["gap_ok"]),
        "P7 realize の〈いつ〉が着手以降": sum(1 for r in rows if r["rz_ok"]),
    }
    print("\n══ 走行前の予測との突合（predict_v13_5.md §2）")
    n_hit = 0
    for k, p in PRED.items():
        ok = hit(p, got[k])
        n_hit += ok
        print(f"  {'当' if ok else '外'}  {k:34s} 予測 {str(p):16s} 実測 {got[k]}")
    print(f"  ―― {n_hit}/{len(PRED)}")

    print(f"\n  停止 {sum(r['stop'] for r in rows)} 件 ／ pass {sum(1 for r in rows if r['pass'])}/8")
    print(f"  書き出し：{OUT}")
    return rows


if __name__ == "__main__":
    main()
