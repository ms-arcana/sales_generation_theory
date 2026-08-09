# -*- coding: utf-8 -*-
"""第12.6版 ―― 交絡を解く2体の採点。

読むのは**構造的な遵守だけ**にする。⑥字数は同じ指示で 450〜1506 に振れることが分かっているので
（第12.2版）、A27 の決定どおり採点の根拠にしない。各アーム n=1 なので、揺らぎと区別できるのは
「座席の数だけ量を置いたか」「様式語が本文に在るか」のような**ほぼ決定的な**遵守だけである。

  ・生成物は pair12/out_<ID>.json
  ・決定表は decisions12_pair.json（指示文を組んだのと同じ表）
  ・予測は predict_v12_pair.md（走る前に置いたもの）

  python3 validate12_pair.py
"""
import json
import sys
from collections import Counter

from sales_logic import Product
from stamp import load as unwrap, stamp_of, dump_stamped
from validate8_v12 import score          # 採点の入口は一本のまま（物差しを分けない）

DECFILE = "decisions12_pair.json"
OUT = "verified12_pair.json"

# 走る前に置いた予測（predict_v12_pair.md）。外れたものが次のアノマリー
PREDICT = {
    "E1-P1":  {"by_seat": 2, "stop": 0, "SEATWORD": 0, "A16": 0, "OMITTED": 0},
    "E1-P1R": {"by_seat": 3, "stop": (0, 1), "SEATWORD": (0, 1), "A16": 0, "OMITTED": (0, 1)},
}
GROUNDED = ("買い手データ", "公開統計", "売り手の実績")


def hit(pred, got):
    return got in pred if isinstance(pred, tuple) else got == pred


def main():
    dec = {r["id"]: r for r in unwrap(DECFILE)}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out, rows = [], []

    for cid in ("E1-P1", "E1-P1R"):
        try:
            g = unwrap(f"pair12/out_{cid}.json")
        except FileNotFoundError:
            print(f"★ pair12/out_{cid}.json が無い"); sys.exit(1)
        d = dec[cid]
        copy, D, v = score(d, g)
        codes = [f.code for f in v["findings"]]
        stops = [f"{f.code}({f.ref})" for f in v["findings"] if f.level == "stop"]
        qs = D.s6_quantity_sources or {}
        row = {
            "id": cid,
            "読む座席": len(d["chain"]),
            "by_seat": len(D.s6_kappa_by_seat or {}),
            "stop": len(stops),
            "stops": stops,
            "SEATWORD": codes.count("A23_SEAT_WORD_ABSENT"),
            "A16": codes.count("A16_NOT_CONV_AT_SEAT"),
            "OMITTED": codes.count("A27_BLOCK_OMITTED"),
            "出所_裏づけ無し": sum(1 for s in qs.values() if s not in GROUNDED),
            "出所_合計": len(qs),
            "to_sales": len(D.s6_to_sales or ()),
            "s6_kappa": D.s6_kappa,
            "s6_kappa_配列か": not isinstance(D.s6_kappa, str),
            "判断": [f"{x.code}({x.ref})" for x in v["needs_judgment"]],
            "⑥字数": len(copy.get("⑥", "")),          # 読み物。根拠にしない
        }
        rows.append(row)
        out.append({"id": cid, "declared": g.get("declared"), "self_report": g.get("self_report"),
                    "copy": copy, "row": row,
                    "findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                                  "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
                    "needs_judgment": [{"code": x.code, "ref": x.ref,
                                        "msg": msgs["judgments"].get(x.code, x.code)}
                                       for x in v["needs_judgment"]]})

    dump_stamped(out, OUT)

    print("══ 構造的な遵守（読むのはここだけ）")
    hdr = ("id", "読む座席", "by_seat", "stop", "SEATWORD", "A16", "OMITTED",
           "出所_裏づけ無し", "出所_合計", "to_sales", "s6_kappa_配列か")
    print("  " + "".join(f"{h:>12s}" for h in hdr))
    for r in rows:
        print("  " + "".join(f"{str(r[h]):>12s}" for h in hdr))
    for r in rows:
        if r["stops"]:
            print(f"     {r['id']} 停止 {r['stops']}")
        if r["判断"]:
            print(f"     {r['id']} 要判断 {r['判断']}")

    print("\n══ 予測との突合（走行前に置いたもの）")
    miss = []
    for cid, p in PREDICT.items():
        r = next(x for x in rows if x["id"] == cid)
        for k, want in p.items():
            ok = hit(want, r[k])
            print(f"  {'○' if ok else '×'} {cid:8s} {k:10s} 予測={want} 実測={r[k]}")
            if not ok:
                miss.append((cid, k, want, r[k]))

    print("\n══ 交絡の読み")
    a = next(x for x in rows if x["id"] == "E1-P1")
    b = next(x for x in rows if x["id"] == "E1-P1R")
    if b["by_seat"] == 3 and b["stop"] == a["stop"]:
        print("  → 座席が一つ増えても構造的な遵守は落ちなかった。")
        print("     **「座席列が難しい」は誤読**であり、8セルで座席列に帰属させてきた差は")
        print("     κ_n の複数性のほうに帰属し直す必要がある。")
    elif b["stop"] > a["stop"] or b["by_seat"] < 3:
        print("  → 読む座席が増えること自体が負荷だった。**座席列は独立の因子**である。")
        print(f"     落ちた場所：{b['stops'] or 'by_seat が足りない'}")
    else:
        print("  → 両方とも落ちた。座席数ではなく、この買い手・商材に固有の問題である。")

    print(f"\n  ⑥字数（読み物・根拠にしない）  E1-P1 {a['⑥字数']} / E1-P1R {b['⑥字数']}")
    print(f"\n{'予測はすべて的中' if not miss else '外れ: ' + str(miss)}")


if __name__ == "__main__":
    main()
