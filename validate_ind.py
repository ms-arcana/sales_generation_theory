# -*- coding: utf-8 -*-
"""25業界走行（16業界分）の採点。

    python3 validate_ind.py     → verified_ind.json ＋ 予測との突合

採点本体は validate8_v12.score を共有する（第12.2版以来の物差し）。
予測は predict_ind.md に走行前に置いてある。**書き換えないこと。**
"""
import collections
import glob
import json
import os

from stamp import load as unwrap, dump_stamped
from validate8_v12 import score

# ── predict_ind.md（走行前にコミット済み）。書き換えない
PREDICT = {
    "A27_BLOCK_OMITTED_件数":      (">=", 5),      # §1-1 本命
    "A23_SEAT_WORD_ABSENT_件数":   (">=", 8),      # §1-2
    "s6_to_sales_あり_セル数":      (">=", 15),     # §1-3
    "商材間の1件あたりstop差":       ("<=", 1.0),    # §2
    "A16_未較正での停止":           ("==", 0),      # §3
    "R9_設計語の漏洩":              ("==", 0),      # §4
    "A25_KAPPA_MERGED":            ("==", 0),      # §4
    "s6_kappaが配列のセル数":        ("==", 21),     # §4
    "A5_KAPPA_PARTIAL":            ("<=", 2),      # §4
    "取り違え":                     ("==", 0),      # §4
}


def main():
    dec = {r["id"]: r for r in unwrap("decisions_ind.json") if not r.get("_error")}
    rows, out = [], []
    bad_id = 0
    for fp in sorted(glob.glob("ind_run/out_*.json")):
        cid = os.path.basename(fp)[4:-5]
        try:
            g = unwrap(fp)
        except Exception as e:
            print(f"   ✗ {cid} 読めない: {e}")
            continue
        if g.get("cell_id") and g["cell_id"] != cid:
            bad_id += 1
            print(f"   ✗ 取り違え {fp} cell_id={g['cell_id']}")
        d = dec.get(cid)
        if not d:
            print(f"   ✗ {cid} の決定表が無い"); continue
        copy, D, v = score(d, g)
        codes = collections.Counter(f.code for f in v["findings"] if f.level == "stop")
        dem = collections.Counter(f.code for f in v["findings"] if f.level == "demote")
        row = {
            "id": cid, "業界": d["業界"], "商材": d["商材"],
            "較正": bool(d.get("calibrated")),
            "読む座席": len(d.get("chain") or []), "ブロック": len(d.get("blocks") or []),
            "stop": sum(codes.values()), "stops": dict(codes), "demote": dict(dem),
            "pass": v["pass"], "判断": len(v["needs_judgment"]),
            "OMITTED": codes.get("A27_BLOCK_OMITTED", 0) + dem.get("A27_BLOCK_OMITTED", 0),
            "SEATWORD": codes.get("A23_SEAT_WORD_ABSENT", 0) + dem.get("A23_SEAT_WORD_ABSENT", 0),
            "A16": codes.get("A16_NOT_CONV_AT_SEAT", 0),
            "MERGED": codes.get("A25_KAPPA_MERGED", 0) + dem.get("A25_KAPPA_MERGED", 0),
            "PARTIAL": len([x for x in v["needs_judgment"] if x.code == "A5_KAPPA_PARTIAL"]),
            "R9": codes.get("R9_DESIGN_VOCAB", 0) + len([f for f in v["findings"]
                                                         if f.code.startswith("R9")]),
            "kappa配列": isinstance(D.s6_kappa, (list, tuple)),
            "by_seat": len(D.s6_kappa_by_seat or {}),
            "to_sales": len(D.s6_to_sales or ()),
            "omitted_declared": len(D.s6_omitted_blocks or ()),
            "出所": len(D.s6_quantity_sources or {}),
            "⑥字数": len(copy.get("⑥", "")),
        }
        rows.append(row)
        out.append({**row, "declared": vars(D), "copy": copy,
                    "self_report": g.get("self_report", ""),
                    "findings": [{"code": f.code, "level": f.level, "ref": f.ref}
                                 for f in v["findings"]],
                    "needs_judgment": [{"code": x.code, "ref": x.ref}
                                       for x in v["needs_judgment"]]})
    dump_stamped(out, "verified_ind.json")

    print(f"\n══ 採点 {len(rows)}件")
    print(f"{'id':9s} {'較正':4s} {'座':2s} {'ブ':2s} {'stop':4s} {'通':2s} "
          f"{'落':2s} {'座語':3s} {'営業':3s} {'出所':3s} {'⑥字':5s} 停止コード")
    for r in rows:
        print(f"{r['id']:9s} {'較' if r['較正'] else '未':4s} {r['読む座席']:<2d} {r['ブロック']:<2d} "
              f"{r['stop']:<4d} {'○' if r['pass'] else '×':2s} {r['OMITTED']:<2d} "
              f"{r['SEATWORD']:<3d} {r['to_sales']:<3d} {r['出所']:<3d} {r['⑥字数']:<5d} "
              f"{','.join(r['stops']) or '無'}")

    it = [r for r in rows if r["id"].endswith("-IT")]
    cs = [r for r in rows if r["id"].endswith("-CS")]
    s_it = sum(r["stop"] for r in it) / len(it) if it else 0
    s_cs = sum(r["stop"] for r in cs) / len(cs) if cs else 0

    got = {
        "A27_BLOCK_OMITTED_件数": sum(1 for r in rows if r["OMITTED"]),
        "A23_SEAT_WORD_ABSENT_件数": sum(1 for r in rows if r["SEATWORD"]),
        "s6_to_sales_あり_セル数": sum(1 for r in rows if r["to_sales"]),
        "商材間の1件あたりstop差": round(abs(s_it - s_cs), 2),
        "A16_未較正での停止": sum(r["A16"] for r in rows if not r["較正"]),
        "R9_設計語の漏洩": sum(r["R9"] for r in rows),
        "A25_KAPPA_MERGED": sum(r["MERGED"] for r in rows),
        "s6_kappaが配列のセル数": sum(1 for r in rows if r["kappa配列"]),
        "A5_KAPPA_PARTIAL": sum(r["PARTIAL"] for r in rows),
        "取り違え": bad_id,
    }
    print("\n══ 予測との突合（predict_ind.md ―― 走行前に置いたもの）")
    hit = 0
    for k, (op, want) in PREDICT.items():
        v = got[k]
        okk = {">=": v >= want, "<=": v <= want, "==": v == want}[op]
        hit += okk
        print(f"   {'○' if okk else '●'} {k:28s} 予測 {op}{want:<5} 実測 {v}")
    print(f"\n   的中 {hit}/{len(PREDICT)}")

    print("\n══ 商材別")
    for nm, g in (("IT", it), ("コンサル", cs)):
        if not g:
            continue
        print(f"   {nm:6s} n={len(g):2d}  通過 {sum(1 for r in g if r['pass'])}/{len(g)}  "
              f"stop/件 {sum(r['stop'] for r in g)/len(g):.2f}  "
              f"落とし {sum(r['OMITTED'] for r in g)}  座語 {sum(r['SEATWORD'] for r in g)}  "
              f"⑥字数 {sum(r['⑥字数'] for r in g)//len(g)}")

    print("\n══ 読む座席の数別")
    for n in sorted({r["読む座席"] for r in rows}):
        g = [r for r in rows if r["読む座席"] == n]
        print(f"   座席{n}  n={len(g):2d}  通過 {sum(1 for r in g if r['pass'])}/{len(g)}  "
              f"落とし {sum(r['OMITTED'] for r in g)}  座語 {sum(r['SEATWORD'] for r in g)}  "
              f"営業へ {sum(1 for r in g if r['to_sales'])}/{len(g)}")

    print("\n══ 較正／未較正")
    for lab, g in (("較正", [r for r in rows if r["較正"]]), ("未較正", [r for r in rows if not r["較正"]])):
        if not g:
            continue
        print(f"   {lab:5s} n={len(g):2d}  通過 {sum(1 for r in g if r['pass'])}/{len(g)}  "
              f"stop/件 {sum(r['stop'] for r in g)/len(g):.2f}  ⑥字数 {sum(r['⑥字数'] for r in g)//len(g)}")

    c = collections.Counter(k for r in rows for k in r["stops"])
    print("\n══ 停止コードの内訳", dict(c))


if __name__ == "__main__":
    main()
