# -*- coding: utf-8 -*-
"""第12.6版 ―― 交絡を解く2体。

8セルの設計では、三つの因子が完全に交絡していた。

    終端が資料を読まない ─ 3座席 ─ κ_n 単数（財源）      E1, R1
    終端が自分で読む    ─ 2座席 ─ κ_n 複数（価格・財源）  E2, R2

「座席列が難しい」と読んできたものが、実は「基準が複数だから難しい」かもしれない。
8セルの中では切り分けられない。**因子を一つだけ動かした対にする。**

    E1-P1   私立大学 × ad × 理事会は資料を読まない（現行）
    E1-P1R  私立大学 × ad × **理事会も資料を読む**（唯一の差）

決定表は Σ・ブロック・規則・停止のすべてが同一で、変わるのは
**読む座席 2 → 3** と **j\\* 学部長会 → 理事会** だけ（確認済み）。

なぜ E1 の理事会か。この座席は **origin=制度・|κ|=1・Form が閉じている**（予算科目／
学生生徒等納付金／帰属収支差額 の3語しかない）。新たに読み手になる座席として最も厳しい ――
Π₂ の通関を、語彙の閉じた座席まで通さなければならなくなる。

  python3 pair12.py     → decisions12_pair.json / prompts12_pair.json / pair12/in_*.json
"""
import copy
import json
import pathlib
from dataclasses import replace

import cells8_v10 as C
import prompts8_v11 as P
from sales_logic import compile_deal
from stamp import dump_stamped, load as _load, assert_fresh

BASE_ID = "E1-P1"
ARM = 1


def make_cells():
    base = next(x for x in C.CELLS if x["id"] == BASE_ID)
    var = dict(base)
    nu = copy.deepcopy(base["nu"])
    nu.J = list(nu.J)
    nu.J[-1] = replace(nu.J[-1], reads=True)     # ← 動かす因子はこれ一つだけ
    var["nu"] = nu
    var["id"] = BASE_ID + "R"
    var["セグメント"] = base["セグメント"] + "／理事会も資料を読む"
    return [base, var]


def rec_of(cell):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    d = compile_deal(cell["nu"], C.SELLERS[cell["seller"]], C.TODAY)
    rec = {k: cell[k] for k in ("id", "業界", "セグメント", "商材")}
    rec.update({k: d.get(k) for k in
                ("generate", "sigma", "j_star", "kappa_n", "form_n", "tau_ok", "delta",
                 "five_mentions", "d7_basis", "blocks", "rules", "executors",
                 "start_deadline", "chain", "talk_guide")})
    rec["findings"] = [{"code": f.code, "level": f.level, "ref": f.ref,
                        "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]]
    rec["needs_judgment"] = [{"code": x.code, "ref": x.ref,
                              "msg": msgs["judgments"].get(x.code, x.code)}
                             for x in d["needs_judgment"]]
    rec["seats"] = [{"name": s.name, "kappa": sorted(s.kappa), "chi": s.chi, "gamma": s.gamma,
                     "reads": s.reads, "form": sorted(s.form), "origin": s.origin}
                    for s in cell["nu"].J]
    rec["veto"] = [v.name for v in cell["nu"].V]
    rec["gamma_own"] = cell["nu"].gamma_pre
    rec["prod"] = vars(cell["nu"].prod)
    return rec


def main():
    cells = make_cells()
    recs = [rec_of(c) for c in cells]
    dump_stamped(recs, "decisions12_pair.json")
    assert_fresh("decisions12_pair.json")

    print("══ 決定表：因子を一つだけ動かせているか")
    a, b = recs
    same = [k for k in ("sigma", "blocks", "rules", "kappa_n", "form_n", "talk_guide")
            if a[k] == b[k]]
    diff = [k for k in a if a[k] != b[k]]
    print(f"   同一の欄  {same}")
    print(f"   異なる欄  {sorted(diff)}")
    for r in recs:
        st = [f["code"] for f in r["findings"] if f["level"] == "stop"]
        print(f"   {r['id']:8s} Σ={''.join(r['sigma'])} 読む座席={len(r['chain'])} "
              f"j*={r['j_star']} κ_n={r['kappa_n']} 生成可={r['generate']} 停止={st or '無'}")

    built = [{"id": r["id"], "sigma": r["sigma"], "arm": ARM,
              "persona": P.PERSONA[BASE_ID[:2]], "prompt": P.build(r, c, ARM)}
             for r, c in zip(recs, cells)]
    dump_stamped(built, "prompts12_pair.json")

    d = pathlib.Path("pair12"); d.mkdir(exist_ok=True)
    for x in built:
        dump_stamped(x, str(d / f"in_{x['id']}.json"))

    print("\n══ 指示文への到達（走行前に確認する ―― 第12版で踏んだ配管の罠）")
    for x in built:
        p = x["prompt"]
        seats = [ln for ln in p.split("\n") if "に向けて：" in ln]
        stray = [ln for ln in p.split("\n") if "価格・財源" in ln and "書かない" not in ln]
        print(f"   {x['id']:8s} 座席ごとの量の指示={len(seats)}行  "
              f"A26={'その事象が再発するか' in p}  A27={'要素を落としてはならない' in p}  "
              f"A28={'どこから来たのかを本文に添える' in p}  "
              f"κ配列欄={'s6_kappa** は、**最後に決める座席が見る基準**を**配列**' in p}  "
              f"連結表示の残り={len(stray)}")
        for ln in seats:
            print(f"        {ln.strip()}")


if __name__ == "__main__":
    main()
