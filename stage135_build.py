# -*- coding: utf-8 -*-
"""第13.5版 ―― 盲検買い手16体の入力を作る。

第13版の第2段と**同じペルソナ・同じ座席・同じ組み方**を使う。
違うのは資料の中身だけ（A37 を直した指示文で生成し直したもの）。
予測器は今回は立てない（第13版の走行そのものが対照になるため。predict_v13_5.md §5）。

突合は配列のインデックスで行う。エージェントが返す文字列 id は信用しない。
"""
import pathlib
from stamp import load as _load, dump_stamped

V = {r["id"]: r for r in _load("verified135.json")}
DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
PER = _load("persona12.json")
d = pathlib.Path("stage135"); d.mkdir(exist_ok=True)


def body_of(cid):
    r = V[cid]; sigma = DEC[cid]["sigma"]
    return "\n\n".join(f"── {s} 枚目 ──\n{r['copy'].get(s,'')}" for s in sigma)


n = 0
for p in PER:
    cid, seat = p["id"], p["seat"]
    dump_stamped({"id": cid, "seat": seat, "sigma": DEC[cid]["sigma"],
                  "persona": p["persona"], "body": body_of(cid)},
                 str(d / f"in_buyer_{cid}__{seat}.json")); n += 1
print(f"買い手 {n}")

# 第13版の資料と、今回の資料が**実際に違う**ことを確かめる（同じものを読ませて
# 「変わらなかった」と書く事故を防ぐ）。日付だけが変わっているのが正しい姿。
old = {r["id"]: r for r in _load("verified8_v13.json")}
same = [cid for cid in DEC if body_of(cid) == "\n\n".join(
    f"── {s} 枚目 ──\n{old[cid]['copy'].get(s,'')}" for s in DEC[cid]["sigma"])]
print(f"第13版と本文が同一のセル：{len(same)}件 {same}")
