# -*- coding: utf-8 -*-
"""第12.9版 ―― 8体を揃えて A26・A27・A28 を測る（層3.5）。

生成物の出どころは3つに分かれるが、**指示文はバイト一致であることを確認済み**。

    E1-P1   pair12/out_E1-P1.json      第12.6版の走行
    R1-P1   pair12b/out_R1-P1.json     第12.8版の走行
    残り6体  run12b/out_<ID>.json       第12.9版の走行

決定表は `decisions8_v12.json`（指示文を組んだのと同じ表）。
予測は `predict_v12_3.md`（A26・A27／走行前）と `第12.4版-A28設計.md` §6（A28／走行前）、
そして `predict_v12_4.md`（6体分／走行前）。

  python3 validate8_v13.py
"""
import json
import sys
from collections import Counter

from sales_logic import Product
from stamp import load as unwrap, dump_stamped, stamp_of
from validate8_v12 import score

IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
SRC = {"E1-P1": "pair12/out_E1-P1.json", "R1-P1": "pair12b/out_R1-P1.json"}
GROUNDED = ("買い手データ", "公開統計", "売り手の実績")
OUT = "verified8_v13.json"

# ── 走る前に置いた予測。範囲はタプル、確定値はスカラー
P_A26 = {"REPRODUCES": (0, 1), "RESIDUAL_UNDECLARED": 0, "RESIDUAL_OK": 6, "CHARGE_PERIODIC": 2}
P_A27 = {"BLOCK_OMITTED": (0, 1), "NO_OMISSION": (7, 8), "OMISSION_UNDECLARED": 0}
P_A28 = {"SOURCE_UNDECLARED": 0, "裏づけ無しの座席": tuple(range(6, 11)),
         "ESTIMATE_UNMARKED": (0, 1, 2), "SLOT_ABSENT": (0, 1),
         "to_sales 非空のセル": (6, 7, 8), "TO_SALES_EMPTY": (0, 1, 2)}
P_ALL = {"stop 合計": (0, 1), "A16": 0, "R10b": 0, "A23紙側": 0,
         "座席申告": 8, "取り違え・欠落": 0, "KAPPA_MERGED": 0}


def hit(pred, got):
    return got in pred if isinstance(pred, tuple) else got == pred


def main():
    dec = {r["id"]: r for r in unwrap("decisions8_v12.json")}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    rows, out, bad = [], [], []

    for cid in IDS:
        path = SRC.get(cid, f"run12b/out_{cid}.json")
        try:
            g = unwrap(path)
        except FileNotFoundError:
            print(f"★ {path} が無い"); sys.exit(1)
        if g.get("cell_id") != cid:
            bad.append(f"取り違え {path}: {g.get('cell_id')}")
        d = dec[cid]
        copy, D, v = score(d, g)
        codes = [f.code for f in v["findings"]]
        jc = [x.code for x in v["needs_judgment"]]
        qs = D.s6_quantity_sources or {}
        row = {
            "id": cid, "商材": d["商材"], "Σ": "".join(d["sigma"]),
            "stop": sum(1 for f in v["findings"] if f.level == "stop"),
            "stops": [f"{f.code}({f.ref})" for f in v["findings"] if f.level == "stop"],
            "R10a": [c for c in codes if c.startswith("R10a")] + [c for c in jc if c.startswith("R10a")],
            "残存/課金": f"{D.s6_residual_period_months}/{D.s6_period_months}",
            "A27": [c for c in codes if c.startswith("A27")] + [c for c in jc if c.startswith("A27")],
            "A28": [c for c in codes if c.startswith("A28")] + [c for c in jc if c.startswith("A28")],
            "出所": {k: s for k, s in qs.items()},
            "裏づけ無し": sum(1 for s in qs.values() if s not in GROUNDED),
            "to_sales": len(D.s6_to_sales or ()),
            "by_seat": len(D.s6_kappa_by_seat or {}),
            "KAPPA_MERGED": codes.count("A25_KAPPA_MERGED"),
            "A16": codes.count("A16_NOT_CONV_AT_SEAT"),
            "R10b": codes.count("R10b_UNIT_ABSENT"),
            "SEATWORD": codes.count("A23_SEAT_WORD_ABSENT"),
            "PARTIAL": jc.count("A5_KAPPA_PARTIAL"),
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

    print("══ 8体（Arm 1・v12.8）")
    hdr = ("id", "商材", "Σ", "stop", "残存/課金", "by_seat", "裏づけ無し",
           "to_sales", "KAPPA_MERGED", "A16", "SEATWORD", "⑥字数")
    print("  " + "".join(f"{h:>12s}" for h in hdr))
    for r in rows:
        print("  " + "".join(f"{str(r[h]):>12s}" for h in hdr))
    for r in rows:
        if r["stops"]:
            print(f"     {r['id']} 停止 {r['stops']}")

    def cnt(key, code):
        return sum(1 for r in rows if any(c.endswith(code) or c == code for c in r[key]))

    got = {
        "A26": {"REPRODUCES": cnt("R10a", "R10a_REPRODUCES_PROBLEM"),
                "RESIDUAL_UNDECLARED": cnt("R10a", "R10a_RESIDUAL_UNDECLARED"),
                "RESIDUAL_OK": cnt("R10a", "R10a_RESIDUAL_OK"),
                "CHARGE_PERIODIC": cnt("R10a", "R10a_CHARGE_PERIODIC")},
        "A27": {"BLOCK_OMITTED": cnt("A27", "A27_BLOCK_OMITTED"),
                "NO_OMISSION": cnt("A27", "A27_NO_OMISSION"),
                "OMISSION_UNDECLARED": cnt("A27", "A27_OMISSION_UNDECLARED")},
        "A28": {"SOURCE_UNDECLARED": cnt("A28", "A28_SOURCE_UNDECLARED"),
                "裏づけ無しの座席": sum(r["裏づけ無し"] for r in rows),
                "ESTIMATE_UNMARKED": cnt("A28", "A28_ESTIMATE_UNMARKED"),
                "SLOT_ABSENT": cnt("A28", "A28_SLOT_ABSENT"),
                "to_sales 非空のセル": sum(1 for r in rows if r["to_sales"] > 0),
                "TO_SALES_EMPTY": cnt("A28", "A28_TO_SALES_EMPTY")},
        "全体": {"stop 合計": sum(r["stop"] for r in rows),
                 "A16": sum(r["A16"] for r in rows), "R10b": sum(r["R10b"] for r in rows),
                 "A23紙側": sum(r["SEATWORD"] for r in rows),
                 "座席申告": sum(1 for r in rows if r["by_seat"] >= 2),
                 "取り違え・欠落": len(bad),
                 "KAPPA_MERGED": sum(r["KAPPA_MERGED"] for r in rows)},
    }
    print("\n══ 予測との突合（すべて走行前に置いたもの）")
    miss = []
    for name, pred in (("A26", P_A26), ("A27", P_A27), ("A28", P_A28), ("全体", P_ALL)):
        print(f"  ── {name}")
        for k, want in pred.items():
            g = got[name][k]
            ok = hit(want, g)
            w = f"{min(want)}〜{max(want)}" if isinstance(want, tuple) else want
            print(f"     {'○' if ok else '×'} {k:22s} 予測={str(w):8s} 実測={g}")
            if not ok:
                miss.append((name, k, w, g))

    lens = [r["⑥字数"] for r in rows]
    print(f"\n  ⑥字数（根拠にしない）平均 {sum(lens)//len(lens)} 最大 {max(lens)} 最小 {min(lens)}"
          f"   ／ 予測は 平均900〜1100・最大1200〜1600")
    print(f"  pass {sum(1 for r in rows if r['pass'])}/8   ／ 予測は 5〜7/8")
    if bad:
        print("  ★", bad)
    print(f"\n{'予測はすべて的中' if not miss else '外れ ' + str(len(miss)) + '件: ' + str(miss)}")


if __name__ == "__main__":
    main()
