# -*- coding: utf-8 -*-
"""第12.8版 ―― 交絡をさらに二本割る。

第12.6版で〈終端が読むか〉を割ったら帰無だった。残る候補は κ_n の複数性と、終端の origin×γ。

  検証1  |κ_n| 1 → 2      R1-P1 / R1-P1K（社長の基準を 財源 → 価格・財源）
  検証2  終端 γ 合議 → 単独  E1-P1 / E1-P1G（理事会を合議 → 単独）

**検証1 を E1 で組めないことが、それ自体で一つの発見だった。**
E1 の終端は理事会（origin=制度）で、R18 が「制度が置いた座席は所掌が定義されているので
複数の基準を持てない」と言う。|κ|=2 にすると `R18_INSTITUTIONAL_MULTI_KAPPA` で停止する。
つまり **|κ_n| と origin は偶然の交絡ではなく、モデルが法として結びつけている** ――
8セルで κ_n が複数だった終端（理事長・社長）が両方とも origin=個人 だったのは、必然である。
非制度の終端でしか |κ_n|>1 は起きないので、検証1 は R1（社長＝個人）で組む。

検証2 は機械的には**規則 B3 が一本消えるだけ**である（「可搬層は最も保守的な一人の基準で」）。
`GAMMA_COLLEGIAL` は学部長会が合議のままなので残る。B3 一本の対照になる。

  python3 pair12b.py   → decisions12b.json / prompts12b.json / pair12b/in_*.json
"""
import copy
import pathlib
from dataclasses import replace

import cells8_v10 as C
import prompts8_v11 as P
from pair12 import rec_of
from stamp import dump_stamped, assert_fresh

ARM = 1
VARIANTS = [
    ("R1-P1",  "R1-P1",  None,                                     ""),
    ("R1-P1K", "R1-P1",  dict(kappa=frozenset({"価格", "財源"})),   "／社長は価格と財源の二つで見る"),
    ("E1-P1G", "E1-P1",  dict(gamma="単独"),                        "／理事会は単独決裁"),
]


def make_cells():
    out = []
    for new_id, base_id, kw, segsfx in VARIANTS:
        base = next(x for x in C.CELLS if x["id"] == base_id)
        c = dict(base)
        if kw:
            nu = copy.deepcopy(base["nu"]); nu.J = list(nu.J)
            nu.J[-1] = replace(nu.J[-1], **kw)
            c["nu"] = nu
        c["id"] = new_id
        c["セグメント"] = base["セグメント"] + segsfx
        out.append(c)
    return out


def main():
    cells = make_cells()
    recs = [rec_of(c) for c in cells]
    dump_stamped(recs, "decisions12b.json")
    assert_fresh("decisions12b.json")

    print("══ 決定表：因子を一つだけ動かせているか")
    by = {r["id"]: r for r in recs}
    for a, b in (("R1-P1", "R1-P1K"), (None, "E1-P1G")):
        pass
    base_r1 = by["R1-P1"]
    for cid in ("R1-P1K",):
        d = [k for k in base_r1 if base_r1[k] != by[cid][k]]
        print(f"   R1-P1 → {cid}  異なる欄 {sorted(d)}")
    print("   E1-P1 → E1-P1G   （E1-P1 は第12.6版の走行と指示文が同一であることを確認済み）")
    for r in recs:
        st = [f["code"] for f in r["findings"] if f["level"] == "stop"]
        print(f"   {r['id']:8s} Σ={''.join(r['sigma'])} 読む座席={len(r['chain'])} "
              f"j*={r['j_star']} κ_n={r['kappa_n']} 規則数={len(r['rules'])} "
              f"生成可={r['generate']} 停止={st or '無'}")
    print("   規則差 R1-P1→R1-P1K:", sorted(set(by['R1-P1K']['rules']) ^ set(base_r1['rules'])) or "無")
    e1 = next(x for x in C.CELLS if x["id"] == "E1-P1")
    from sales_logic import compile_deal
    d_e1 = compile_deal(e1["nu"], C.SELLERS[e1["seller"]], C.TODAY)
    print("   規則差 E1-P1→E1-P1G:",
          sorted(set(by['E1-P1G']['rules']) ^ set(d_e1['rules'])) or "無")

    built = [{"id": r["id"], "sigma": r["sigma"], "arm": ARM,
              "persona": P.PERSONA[r["id"][:2]], "prompt": P.build(r, c, ARM)}
             for r, c in zip(recs, cells)]
    dump_stamped(built, "prompts12b.json")
    d = pathlib.Path("pair12b"); d.mkdir(exist_ok=True)
    for x in built:
        dump_stamped(x, str(d / f"in_{x['id']}.json"))

    print("\n══ 指示文への到達")
    for x in built:
        p = x["prompt"]
        stray = [ln for ln in p.split("\n") if "価格・財源" in ln and "書かない" not in ln]
        kline = [ln for ln in p.split("\n") if "でしか物を見ない" in ln]
        print(f"   {x['id']:8s} A26={'その事象が再発するか' in p} "
              f"A27={'要素を落としてはならない' in p} A28={'どこから来たのかを本文に添える' in p} "
              f"連結表示の残り={len(stray)}")
        print(f"        {kline[0].strip() if kline else '(κ_n 行なし)'}")


if __name__ == "__main__":
    main()
