# -*- coding: utf-8 -*-
"""第13版 第2段 ―― 予測器8体 ＋ 盲検買い手16体 の入力を作る。

3役を分ける（引き継ぎ書 §5 ／ T&T）。
  生成器    済（第12.9版の8体）
  予測器    資料と座席構成だけを見て、買い手がどう反応するかを**予測する**
  盲検買い手 ペルソナ（自分の世界）と資料だけを見て、**反応する**

突合は配列のインデックスで行う。エージェントが返す文字列 id は信用しない。
"""
import pathlib
from stamp import load as _load, dump_stamped

V = {r["id"]: r for r in _load("verified8_v13.json")}
DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
PER = _load("persona12.json")
d = pathlib.Path("stage2"); d.mkdir(exist_ok=True)


def body_of(cid):
    r = V[cid]; sigma = DEC[cid]["sigma"]
    return "\n\n".join(f"── {s} 枚目 ──\n{r['copy'].get(s,'')}" for s in sigma)


def seats_of(cid):
    rec = DEC[cid]
    L = []
    for s in rec["seats"]:
        L.append(f"・{s['name']}（見るもの：{'・'.join(s['kappa'])} ／ 通し方：{s['chi']} ／ "
                 f"{s['gamma']} ／ {'資料を読む' if s['reads'] else '資料は読まない'}"
                 f" ／ 様式の語：{'／'.join(s['form']) or '（未登録）'}）")
    if rec["veto"]:
        L.append(f"・{rec['veto'][0]}（決裁権はないが、この人物が拒めば事業は止まる）")
    return "\n".join(L)


n_p = n_b = 0
for cid in DEC:
    dump_stamped({"id": cid, "sigma": DEC[cid]["sigma"], "seats": seats_of(cid),
                  "body": body_of(cid)}, str(d / f"in_pred_{cid}.json")); n_p += 1
for p in PER:
    cid, seat = p["id"], p["seat"]
    dump_stamped({"id": cid, "seat": seat, "sigma": DEC[cid]["sigma"],
                  "persona": p["persona"], "body": body_of(cid)},
                 str(d / f"in_buyer_{cid}__{seat}.json")); n_b += 1
print(f"予測器 {n_p} ／ 買い手 {n_b}")
for p in PER[:2]:
    print(f"  例 {p['id']} / {p['seat']}")
