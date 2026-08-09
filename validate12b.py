# -*- coding: utf-8 -*-
"""第12.8版 ―― 交絡をさらに二本割った3体の採点。

読むのは**構造的な遵守だけ**（各条件 n=1 なので、揺らぎと区別できるのはほぼ決定的な遵守だけ）。
⑥字数は A27 の決定どおり根拠にしない。

  検証1  R1-P1 ↔ R1-P1K   |κ_n| 1 → 2
  検証2  E1-P1 ↔ E1-P1G   終端 γ 合議 → 単独（E1-P1 は第12.6版の走行を対照に使う）

  python3 validate12b.py
"""
import json

from stamp import load as unwrap, dump_stamped
from validate8_v12 import score

GROUNDED = ("買い手データ", "公開統計", "売り手の実績")

PREDICT = {   # predict_v12b.md（走行前に置いたもの）
    "R1-P1":  {"MERGED": 0, "PARTIAL": 0, "NOT_EXPR": 0, "by_seat": 2, "stop": 0},
    "R1-P1K": {"MERGED": 0, "PARTIAL": 0, "NOT_EXPR": 0, "by_seat": 2, "stop": 0},
    "E1-P1G": {"MERGED": 0, "PARTIAL": 0, "NOT_EXPR": 0, "by_seat": 2, "stop": 0,
               "出所_合計": 3, "OMITTED": 0},
}


def row_of(cid, d, g):
    copy, D, v = score(d, g)
    codes = [f.code for f in v["findings"]]
    jc = [x.code for x in v["needs_judgment"]]
    qs = D.s6_quantity_sources or {}
    return {
        "id": cid,
        "κ_n": "・".join(d["kappa_n"]),
        "s6_kappa": D.s6_kappa,
        "配列か": not isinstance(D.s6_kappa, str),
        "MERGED": codes.count("A25_KAPPA_MERGED"),
        "PARTIAL": jc.count("A5_KAPPA_PARTIAL"),
        "NOT_EXPR": codes.count("A5_NOT_EXPRESSIBLE"),
        "by_seat": len(D.s6_kappa_by_seat or {}),
        "出所_合計": len(qs),
        "出所_裏づけ無し": sum(1 for s in qs.values() if s not in GROUNDED),
        "OMITTED": codes.count("A27_BLOCK_OMITTED"),
        "SEATWORD": codes.count("A23_SEAT_WORD_ABSENT"),
        "A16": codes.count("A16_NOT_CONV_AT_SEAT"),
        "stop": sum(1 for f in v["findings"] if f.level == "stop"),
        "stops": [f"{f.code}({f.ref})" for f in v["findings"] if f.level == "stop"],
        "判断": jc,
        "⑥字数": len(copy.get("⑥", "")),
    }, v, copy, D


def main():
    dec = {r["id"]: r for r in unwrap("decisions12b.json")}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    rows, out = [], []

    for cid in ("R1-P1", "R1-P1K", "E1-P1G"):
        g = unwrap(f"pair12b/out_{cid}.json")
        r, v, copy, D = row_of(cid, dec[cid], g)
        rows.append(r)
        out.append({"id": cid, "row": r, "declared": g.get("declared"),
                    "self_report": g.get("self_report"), "copy": copy,
                    "findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                                  "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
                    "needs_judgment": [{"code": x.code, "ref": x.ref,
                                        "msg": msgs["judgments"].get(x.code, x.code)}
                                       for x in v["needs_judgment"]]})

    # 第12.6版の E1-P1 を対照として読み込む（指示文がバイト一致であることを確認済み）
    e1 = next(x for x in unwrap("verified12_pair.json") if x["id"] == "E1-P1")["row"]

    dump_stamped(out, "verified12b.json")

    hdr = ("id", "κ_n", "配列か", "MERGED", "PARTIAL", "NOT_EXPR", "by_seat",
           "出所_合計", "OMITTED", "SEATWORD", "A16", "stop")
    print("══ 構造的な遵守")
    print("  " + "".join(f"{h:>11s}" for h in hdr))
    for r in rows:
        print("  " + "".join(f"{str(r.get(h)):>11s}" for h in hdr))
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
            ok = r.get(k) == want
            print(f"  {'○' if ok else '×'} {cid:8s} {k:12s} 予測={want} 実測={r.get(k)}")
            if not ok:
                miss.append((cid, k, want, r.get(k)))

    a = next(x for x in rows if x["id"] == "R1-P1")
    b = next(x for x in rows if x["id"] == "R1-P1K")
    g = next(x for x in rows if x["id"] == "E1-P1G")
    print("\n══ 検証1（|κ_n| 1 → 2）の読み")
    if b["MERGED"] == 0 and b["stop"] == a["stop"] and b["配列か"]:
        print("  → κ_n が2つでも連結せず、停止も増えなかった。**κ_n の複数性も効いていない。**")
        print("     第12.6版の〈終端が読むか〉と合わせて、座席列の束のうち2本が帰無。")
        print("     残る候補は downward・M本数・W数・座席数。")
    else:
        print("  → κ_n の複数性が現に効いた。**8セルの差はここに帰属する。**")
        print(f"     R1-P1K: MERGED={b['MERGED']} stop={b['stops']} s6_kappa={b['s6_kappa']}")

    print("\n══ 検証2（終端 γ 合議 → 単独）の読み")
    same = all(g[k] == e1.get(k) for k in ("by_seat", "stop", "SEATWORD", "A16", "OMITTED"))
    if same:
        print("  → B3 が消えても構造的な遵守は変わらなかった。")
        print("     **γ（合議/単独）は生成に効いていない** ―― 「合議だから止まる」は人格の話で、")
        print("     モデルが働かせている因子ではない。B3 は一行の書き方指示にすぎない。")
    else:
        print("  → B3 一行が現に効いた。**規則一本の効果を分離して観測した。**")
        for k in ("by_seat", "stop", "SEATWORD", "A16", "OMITTED", "出所_合計"):
            if g[k] != e1.get(k):
                print(f"     {k}: E1-P1={e1.get(k)} → E1-P1G={g[k]}")

    print(f"\n  ⑥字数（読み物・根拠にしない）  "
          f"R1-P1 {a['⑥字数']} / R1-P1K {b['⑥字数']} / E1-P1 {e1['⑥字数']} / E1-P1G {g['⑥字数']}")
    print(f"\n{'予測はすべて的中' if not miss else '外れ: ' + str(miss)}")


if __name__ == "__main__":
    main()
