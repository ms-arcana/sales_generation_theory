# -*- coding: utf-8 -*-
"""第13.7版 ―― A41b を入れた決定表と指示文を作り直し、**走らせる前に差分を読む**。

    decisions8_v12.json / prompts8_v12_arm*.json … 第13.6版の as-run。**上書きしない**
    decisions8_v13.json / prompts8_v13_arm*.json … A41b 入りで作り直したもの

第13.5版の教訓（A37b）：**走らせる前に指示文を読む。**
読まずに走らせていたら、8セル中6セルが充足不能な指示だった。

  python3 regen_v13.py
"""
import difflib
import json

import cells8_v10 as C
from stamp import load as _load, dump_stamped


def main():
    C.run("decisions8_v13.json")
    dec_new = _load("decisions8_v13.json")
    dec_old = _load("decisions8_v12.json")

    print("\n══ 決定表の差分（第13.6版 as-run → A41b 入り）")
    fields = set()
    for a, b in zip(dec_old, dec_new):
        for k in set(a) | set(b):
            if a.get(k) != b.get(k):
                fields.add(k)
    if not fields:
        print("   差分なし")
    for k in sorted(fields):
        print(f"  ── 欄 {k}")
        for a, b in zip(dec_old, dec_new):
            if a.get(k) == b.get(k):
                continue
            print(f"     {a['id']}: {json.dumps(a.get(k), ensure_ascii=False)[:90]}"
                  f"  →  {json.dumps(b.get(k), ensure_ascii=False)[:90]}")

    import prompts8_v11 as P
    P.DEC = dec_new
    for arm in P.ARMS:
        built = []
        for rec, cell in zip(dec_new, C.CELLS):
            assert rec["id"] == cell["id"]
            built.append({"id": rec["id"], "sigma": rec["sigma"], "arm": arm,
                          "persona": P.PERSONA[rec["id"][:2]],
                          "prompt": P.build(rec, cell, arm)})
        dump_stamped(built, f"prompts8_v13_arm{arm}.json")

    print("\n══ 指示文の差分（arm ごと・全8セルの行単位）")
    for arm in P.ARMS:
        old = {p["id"]: p["prompt"] for p in _load(f"prompts8_v12_arm{arm}.json")}
        new = {p["id"]: p["prompt"] for p in _load(f"prompts8_v13_arm{arm}.json")}
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
            print(f"      ＋ {line.strip()[:180]}")
        for line in sorted(set(removed)):
            print(f"      － {line.strip()[:180]}")
    print("\n   ※ 走らせていない。")


if __name__ == "__main__":
    main()
