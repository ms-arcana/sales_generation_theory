# -*- coding: utf-8 -*-
"""第13.6版 ―― 機械側の採点（層3.5）。予測は `predict_v13_6.md` §2（走行前）。

    gen136/out_<ID>.json   … 今回の生成物
    decisions8_v12.json    … 指示文を組んだのと同じ表

  python3 validate136.py
"""
import json
import re
import sys

from stamp import load as unwrap, dump_stamped
from sales_logic import iso_date
from validate8_v12 import score

IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
OUT = "verified136.json"

PRED = {
    "M1 s6_quantities を埋めた":        (8,),
    "M2 座席の数だけ置いた":              tuple(range(6, 9)),
    "M3 R20_RETURN_MISSING のセル":     tuple(range(0, 4)),
    "M4 R20_UNIT_MISMATCH のセル":      tuple(range(1, 5)),
    "M5 A43_REALIZE_BEFORE_EFFECT":   tuple(range(0, 3)),
    "M6 A43_REALIZE_IN_BUSY":         tuple(range(0, 3)),
    "M7 A41_DECIDE_AFTER_GATE（E1の2）": (0,),
    "M8 A41_GATE_IN_S4（E1の2）":       (0, 1),
    "M9 停止したセル":                  tuple(range(2, 6)),
    "M11 s6_table_rows ≥ 6 のセル":     (7, 8),
}
# 表の行（｜や罫線で始まる行）は字数から外す ―― 形式変更の趣旨（第13.4版）
TABLE_LINE = re.compile(r"^\s*[｜|│┃・]?\s*[^\n]*[｜|│┃]\s*[^\n]*$")


def prose_len(text: str) -> int:
    return sum(len(ln) for ln in (text or "").split("\n") if not TABLE_LINE.match(ln))


def hit(p, g):
    return g in p


def main():
    dec = {r["id"]: r for r in unwrap("decisions8_v12.json")}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    rows, out = [], []
    for cid in IDS:
        try:
            g = unwrap(f"gen136/out_{cid}.json")
        except FileNotFoundError:
            print(f"★ gen136/out_{cid}.json が無い"); sys.exit(1)
        d = dec[cid]
        copy, D, v = score(d, g)
        codes = [f.code for f in v["findings"]]
        jc = [x.code for x in v["needs_judgment"]]
        qs = D.s6_quantities or ()
        body6 = copy.get("⑥", "")
        rows.append({
            "id": cid, "商材": d["商材"],
            "量の組": len(qs), "座席": len(d["chain"]),
            "窓": [x[0] for x in (d.get("decision_gates") or [])],
            "決定日": D.s6_decide_date, "着手日": D.s6_start_date,
            "実現日": [str(x[1]) for x in (D.s6_realize or ())],
            "表行": D.s6_table_rows,
            "⑥全体": len(body6), "⑥文章": prose_len(body6),
            "stop": sum(1 for f in v["findings"] if f.level == "stop"),
            "stops": [f"{f.code}({f.ref})" for f in v["findings"] if f.level == "stop"],
            "R20": [c for c in codes if c.startswith("R20")] + [c for c in jc if c.startswith("R20")],
            "A41": [c for c in codes if c.startswith("A41")] + [c for c in jc if c.startswith("A41")],
            "A43": [c for c in codes if c.startswith("A43")] + [c for c in jc if c.startswith("A43")],
            "A42": [c for c in (x["code"] for x in d["needs_judgment"]) if c.startswith("A42")],
            "pass": v["pass"],
        })
        out.append({"id": cid, "row": rows[-1], "declared": g.get("declared"),
                    "self_report": g.get("self_report"), "copy": copy,
                    "findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                                  "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
                    "needs_judgment": [{"code": x.code, "ref": x.ref,
                                        "msg": msgs["judgments"].get(x.code, x.code)}
                                       for x in v["needs_judgment"]]})
    dump_stamped(out, OUT)

    print("══ 第13.6版 8体")
    hdr = ("id", "量の組", "座席", "決定日", "着手日", "表行", "⑥全体", "⑥文章", "stop")
    print("  " + "".join(f"{h:>11s}" for h in hdr))
    for r in rows:
        print("  " + "".join(f"{str(r[h]):>11s}" for h in hdr))
    for r in rows:
        if r["窓"]:
            print(f"     {r['id']} 窓 {r['窓']} → 決定 {r['決定日']}")
        if r["実現日"]:
            print(f"     {r['id']} 実現 {r['実現日']}")
        for k in ("R20", "A41", "A43", "A42"):
            if r[k]:
                print(f"     {r['id']} {k}: {r[k]}")
        if r["stops"]:
            print(f"     {r['id']} 停止 {r['stops']}")

    def n(key, code):
        return sum(1 for r in rows if any(c == code for c in r[key]))

    got = {
        "M1 s6_quantities を埋めた": sum(1 for r in rows if r["量の組"]),
        "M2 座席の数だけ置いた": sum(1 for r in rows if r["量の組"] >= r["座席"]),
        "M3 R20_RETURN_MISSING のセル": n("R20", "R20_RETURN_MISSING"),
        "M4 R20_UNIT_MISMATCH のセル": n("R20", "R20_UNIT_MISMATCH"),
        "M5 A43_REALIZE_BEFORE_EFFECT": n("A43", "A43_REALIZE_BEFORE_EFFECT"),
        "M6 A43_REALIZE_IN_BUSY": n("A43", "A43_REALIZE_IN_BUSY"),
        "M7 A41_DECIDE_AFTER_GATE（E1の2）": n("A41", "A41_DECIDE_AFTER_GATE"),
        "M8 A41_GATE_IN_S4（E1の2）": n("A41", "A41_GATE_IN_S4"),
        "M9 停止したセル": sum(1 for r in rows if r["stop"]),
        "M11 s6_table_rows ≥ 6 のセル": sum(1 for r in rows if (r["表行"] or 0) >= 6),
    }
    print("\n══ 走行前の予測との突合（predict_v13_6.md §2）")
    k_hit = 0
    for k, p in PRED.items():
        ok = hit(p, got[k]); k_hit += ok
        print(f"  {'当' if ok else '外'}  {k:34s} 予測 {min(p)}〜{max(p):<3d} 実測 {got[k]}")
    print(f"  ―― {k_hit}/{len(PRED)}")
    m10 = [r["⑥文章"] for r in rows]
    print(f"\n  M10 ⑥の文章の字数 {min(m10)}〜{max(m10)}（予測 600〜1100）"
          f"　第13.5版は {'—'}")
    print(f"  停止 {sum(r['stop'] for r in rows)} 件／pass {sum(1 for r in rows if r['pass'])}/8")
    print(f"  書き出し：{OUT}")
    return rows


if __name__ == "__main__":
    main()
