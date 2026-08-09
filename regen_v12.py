# -*- coding: utf-8 -*-
"""第12.1版 ―― 決定表と指示文を、いまのコードで作り直して差分だけ見る（走らせない）。

第12版のアーム実験では、`fire_rules` に足した `R10a_NO_REPRODUCE` が
`decisions8_v10.json`（第11版で再計算されたまま）に入っておらず、
`prompts8_v11.py` はその古い決定表を読むので、**指示文に一度も載らなかった**。

    decisions8_v10.json  … アーム実験に実際に使われた決定表（as-run）。**上書きしない**
    decisions8_v12.json  … いまのコードで計算し直したもの（版を刻む）
    prompts8_v12_arm*.json … 新しい決定表から組み直した指示文（走らせない）

  python3 regen_v12.py
"""
import json
import difflib

import cells8_v10 as C
from stamp import version


def main():
    # ── 決定表を作り直す
    out = C.run("decisions8_v12.json")
    dec_new = json.load(open("decisions8_v12.json", encoding="utf-8"))
    dec_old = json.load(open("decisions8_v10.json", encoding="utf-8"))

    print("\n══ 決定表の差分（as-run → いまのコード）")
    fields = set()
    for a, b in zip(dec_old, dec_new):
        for k in a:
            if a[k] != b.get(k):
                fields.add(k)
    if not fields:
        print("   差分なし")
    for k in sorted(fields):
        print(f"  ── 欄 {k}")
        for a, b in zip(dec_old, dec_new):
            if a.get(k) == b.get(k):
                continue
            ao, bo = a.get(k), b.get(k)
            if isinstance(ao, list) and all(not isinstance(x, (dict, list)) for x in ao):
                add = [x for x in bo if x not in ao]
                rem = [x for x in ao if x not in bo]
                print(f"     {a['id']}: 追加={add} 削除={rem}")
            else:
                print(f"     {a['id']}: {json.dumps(ao, ensure_ascii=False)[:120]}"
                      f"  →  {json.dumps(bo, ensure_ascii=False)[:120]}")

    # ── 指示文を新しい決定表から組み直す
    import prompts8_v11 as P
    P.DEC = dec_new
    for arm in P.ARMS:
        built = []
        for rec, cell in zip(dec_new, C.CELLS):
            assert rec["id"] == cell["id"]
            built.append({"id": rec["id"], "sigma": rec["sigma"], "arm": arm,
                          "persona": P.PERSONA[rec["id"][:2]],
                          "prompt": P.build(rec, cell, arm)})
        json.dump(built, open(f"prompts8_v12_arm{arm}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    print("\n══ 指示文の差分（arm ごと・全8セルの行単位）")
    for arm in P.ARMS:
        old = {p["id"]: p["prompt"] for p in
               json.load(open(f"prompts8_v11_arm{arm}.json", encoding="utf-8"))}
        new = {p["id"]: p["prompt"] for p in
               json.load(open(f"prompts8_v12_arm{arm}.json", encoding="utf-8"))}
        added, removed, cells = [], [], 0
        for cid in old:
            d = list(difflib.unified_diff(old[cid].splitlines(), new[cid].splitlines(), n=0))
            a = [x[1:] for x in d if x.startswith("+") and not x.startswith("+++")]
            r = [x[1:] for x in d if x.startswith("-") and not x.startswith("---")]
            if a or r:
                cells += 1
            added += a
            removed += r
        print(f"  arm{arm}: {cells}/8 セルで変化")
        for line in sorted(set(added)):
            print(f"      ＋ {line.strip()}")
        for line in sorted(set(removed)):
            print(f"      － {line.strip()}")

    v = version()
    for path in ["decisions8_v12.json"] + [f"prompts8_v12_arm{a}.json" for a in P.ARMS]:
        d = json.load(open(path, encoding="utf-8"))
        json.dump({"_stamp": v, "data": d}, open(path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"\n══ 版を刻んだ： {v}")
    print("   ※ 走らせていない。生成物は run8_v11.json（as-run の指示文で作られたもの）のまま。")


if __name__ == "__main__":
    main()
