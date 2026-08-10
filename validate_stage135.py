# -*- coding: utf-8 -*-
"""第13.5版の採点 ―― A37 を直した資料が、同じ買い手16体を通るか。

第13版（`verified_stage2.json`）が対照である。生成器も買い手のペルソナも同じで、
違うのは⑥の日付の扱いだけ（predict_v13_5.md §0）。

**突合は配列のインデックスで行う。**エージェントが返す文字列は段の正規化にだけ使い、
セル・座席の対応は依頼側の (id, seat) を正とする。

  python3 validate_stage135.py
"""
import re
import sys
from collections import Counter, defaultdict

from stamp import load as _load, dump_stamped
from validate8_v12 import norm_stage
import score_reasons as SR

DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
OUT = "verified_stage135.json"

# predict_v13_5.md §2。基準線は第13版の実測
PRED = {
    "P1 日程を理由に挙げた買い手（散文）": ((0, 1, 2, 3), 12),
    "P2 ⑥の通過": ((0, 1, 2), 0),
    "P3 ⑥の棄却": ((11, 12, 13, 14, 15), 15),
    "P9 own_retracted 実質あり": (tuple(range(9, 17)), 12),
}
RETRACT_NEG = (r"取り消す必要(?:は)?(?:生じ|無|な)|強いられる取り消しは(?:無|な)い"
               r"|^(?:null|なし|無い|ない)|取り消していない")


def main():
    try:
        B = {(x["id"], x["seat"]): x["gen"] for x in _load("stage135/buyers.json") if x.get("ok")}
    except FileNotFoundError:
        print("★ stage135/buyers.json が要る（journal から書き出すこと）"); sys.exit(1)
    if len(B) != 16:
        print(f"★ 買い手が {len(B)}/16 しか無い")

    rows, out, buyers_for_reasons = [], [], []
    verd = defaultdict(Counter)
    retracted, front6, jstar6 = [], [], []

    for cid in IDS:
        sg = DEC[cid]["sigma"]
        jstar = DEC[cid]["j_star"]
        for seat in [c[0] for c in DEC[cid]["chain"]]:
            g = B.get((cid, seat))
            if not g:
                print(f"★ 欠落 {cid}/{seat}"); continue
            rs = g.get("reactions", [])
            row = {"id": cid, "seat": seat, "j_star": seat == jstar, "verdicts": {}}
            for i, x in enumerate(rs):
                st = norm_stage(x.get("stage"), sg, i)
                v = x.get("verdict")
                row["verdicts"][st] = v
                verd[st][v] += 1
                if st == "⑥" and v == "棄却":
                    (jstar6 if seat == jstar else front6).append(f"{cid}/{seat}")
            _o = (g.get("own_retracted") or "").strip()
            if _o and not re.search(RETRACT_NEG, _o):
                retracted.append(f"{cid}/{seat}: {_o[:60]}")
            row["closing_line"] = g.get("closing_line")
            row["reasons"] = g.get("reasons") or []
            rows.append(row)
            out.append({**row, "reactions": rs, "own_retracted": _o,
                        "carries_forward": g.get("carries_forward")})
            buyers_for_reasons.append({"id": cid, "seat": seat, "gen": g})

    dump_stamped(out, OUT)

    print("══ 買い手16人 × 枚の判定")
    for cid in IDS:
        sg = DEC[cid]["sigma"]
        print(f"  {cid}  Σ={''.join(sg)}")
        for r in [x for x in rows if x["id"] == cid]:
            print(f"     {'j*' if r['j_star'] else '  '} {r['seat']:14s} "
                  + " ".join(f"{s}:{r['verdicts'].get(s,'-')}" for s in sg))
            print(f"        「{r['closing_line']}」")

    print("\n══ 枚ごとの判定の分布（第13版 → 第13.5版）")
    old = defaultdict(Counter)
    for r in _load("verified_stage2.json")["rows"]:
        for s, v in r["verdicts"].items():
            old[s][v] += 1
    for s in ("①", "②", "③", "④", "⑤", "⑥"):
        c, o = verd[s], old[s]
        if c or o:
            print(f"  {s}  通過 {o['通過']:>2d}→{c['通過']:<3d} 揺らぐ {o['揺らぐ']:>2d}→{c['揺らぐ']:<3d} "
                  f"棄却 {o['棄却']:>2d}→{c['棄却']:<3d}")

    # ── 理由：申告と散文の二重の数え（predict_v13_5.md §3）
    print()
    rrows = SR.score(buyers_for_reasons)
    g_now = SR.summary(rrows, "第13.5版")
    old_rows = SR.score(_load("stage2/buyers.json"))
    print()
    g_old = SR.summary(old_rows, "第13版（対照）")

    print("\n══ 申告された理由（種類別・decisive のみ）")
    dc = Counter(x["kind"] for r in buyers_for_reasons
                 for x in (r["gen"].get("reasons") or []) if x.get("decisive"))
    for k, n in dc.most_common():
        print(f"   {k:8s} {n}")

    got = {
        "P1 日程を理由に挙げた買い手（散文）": g_now["散文"],
        "P2 ⑥の通過": verd["⑥"]["通過"],
        "P3 ⑥の棄却": verd["⑥"]["棄却"],
        "P9 own_retracted 実質あり": len(retracted),
    }
    print("\n══ 走行前の予測との突合（predict_v13_5.md §2）")
    # 走行前に置いた裁定規則（§3）：申告と散文が食い違ったら P1 は**保留**にする。
    # 今回は 申告16 / 散文3 で 13 件食い違った。どちらの数も P1 の判定には使えない。
    hold = g_now["食い違い"] >= 4
    n_hit = 0
    for k, (want, base) in PRED.items():
        if k.startswith("P1") and hold:
            print(f"  保留 {k:34s} 第13版={base:<3d} 予測 {min(want)}〜{max(want):<3d} 実測 {got[k]}"
                  f"　←申告{g_now['申告']}と散文{g_now['散文']}が食い違った（§3の取り決め）")
            continue
        ok = got[k] in want
        n_hit += ok
        print(f"  {'当' if ok else '外'}  {k:34s} 第13版={base:<3d} 予測 {min(want)}〜{max(want):<3d} 実測 {got[k]}")
    print(f"  ―― {n_hit}/{len(PRED) - (1 if hold else 0)}（P1 は保留）")
    print(f"\n  ★ 的そのもの：**第13版型（着手日が LT を無視）の苦情 "
          f"{g_old['第13版型']}/16 → {g_now['第13版型']}/16**")
    print("     これは語彙を第13版に合わせた物差しなので、"
          "「狙った苦情が消えたか」だけを測る。日程の苦情一般は測れない。")
    print(f"\n  申告側の日程 {g_now['申告']}/16（決定的 {g_now['申告_決定的']}）"
          f"　散文側 {g_now['散文']}/16　食い違い {g_now['食い違い']}")
    if front6:
        print(f"  手前の座席が⑥を棄却 {len(front6)}: {front6}")
    if retracted:
        print("\n  own_retracted:")
        for x in retracted:
            print("   ", x)
    print(f"\n  書き出し：{OUT}")
    return rrows


if __name__ == "__main__":
    main()
