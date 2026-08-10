# -*- coding: utf-8 -*-
"""第13.6版の採点 ―― A41・A43・N₄′／R20・形式を入れた資料が、同じ買い手16体を通るか。

第13.5版（`verified_stage135.json`）が対照である。生成器も買い手のペルソナも同じ。
**走行の中にも対照が入っている** ―― A41 は E1 の2セルで処置し、A42 は R の4セルで放置した
（predict_v13_6.md §1）。日付の文字列そのもので数える B6・B7 が最も信用できる指標である。

**突合は配列のインデックスで行う。**エージェントが返す文字列は段の正規化にだけ使い、
セル・座席の対応は依頼側の (id, seat) を正とする。

  python3 validate_stage136.py
"""
import re
import sys
from collections import Counter, defaultdict

from stamp import load as _load, dump_stamped
from validate8_v12 import norm_stage
import score_reasons as SR

DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
OUT = "verified_stage136.json"

# predict_v13_5.md §2。基準線は第13版の実測
PRED = {
    "B1 ⑥の通過": (tuple(range(0, 4)), 0),
    "B2 ⑥の棄却": (tuple(range(9, 16)), 15),
    "B3 decisive な〈空欄〉": (tuple(range(5, 13)), 15),
    "B4 decisive な〈量の裏づけ〉": (tuple(range(4, 11)), 7),
    "B5 decisive な〈日程〉": (tuple(range(4, 11)), 10),
    "B6 E1の4体が 2027-05-31 に触れる": (tuple(range(0, 2)), 4),
    "B7 Rの8体が 2027-04-01 に触れる": (tuple(range(3, 9)), 4),
    "B8 decisive な〈形式〉": (tuple(range(0, 3)), 0),
    "B9 第13版型の日程の苦情": ((0,), 0),
}
GATE_RE = {"B6 E1の4体が 2027-05-31 に触れる": (r"(2027-05-31|5月31日)", ("E1-P1", "E1-P2")),
           "B7 Rの8体が 2027-04-01 に触れる": (r"(2027-04-01|4月1日|4/1)",
                                             ("R1-P1", "R1-P2", "R2-P1", "R2-P2"))}

RETRACT_NEG = (r"取り消す必要(?:は)?(?:生じ|無|な)|強いられる取り消しは(?:無|な)い"
               r"|^(?:null|なし|無い|ない)|取り消していない")


def main():
    try:
        B = {(x["id"], x["seat"]): x["gen"] for x in _load("stage136/buyers.json") if x.get("ok")}
    except FileNotFoundError:
        print("★ stage136/buyers.json が要る（journal から書き出すこと）"); sys.exit(1)
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

    print("\n══ 枚ごとの判定の分布（第13.5版 → 第13.6版）")
    old = defaultdict(Counter)
    for r in _load("verified_stage135.json"):
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
    g_now = SR.summary(rrows, "第13.6版")
    old_rows = SR.score(_load("stage135/buyers.json"))
    print()
    g_old = SR.summary(old_rows, "第13.5版（対照）")

    print("\n══ 申告された理由（種類別・decisive のみ）")
    dc = Counter(x["kind"] for r in buyers_for_reasons
                 for x in (r["gen"].get("reasons") or []) if x.get("decisive"))
    for k, n in dc.most_common():
        print(f"   {k:8s} {n}")

    import re as _re
    def _touch(pat, ids):
        n = 0
        for r in buyers_for_reasons:
            if r["id"] not in ids:
                continue
            t = " ".join(x.get("why", "") for x in r["gen"].get("reactions", [])) + " " + \
                " ".join(x["text"] for x in (r["gen"].get("reasons") or []))
            n += bool(_re.search(pat, t))
        return n

    got = {
        "B1 ⑥の通過": verd["⑥"]["通過"],
        "B2 ⑥の棄却": verd["⑥"]["棄却"],
        "B3 decisive な〈空欄〉": dc.get("空欄", 0),
        "B4 decisive な〈量の裏づけ〉": dc.get("量の裏づけ", 0),
        "B5 decisive な〈日程〉": dc.get("日程", 0),
        "B6 E1の4体が 2027-05-31 に触れる": _touch(*GATE_RE["B6 E1の4体が 2027-05-31 に触れる"]),
        "B7 Rの8体が 2027-04-01 に触れる": _touch(*GATE_RE["B7 Rの8体が 2027-04-01 に触れる"]),
        "B8 decisive な〈形式〉": dc.get("形式", 0),
        "B9 第13版型の日程の苦情": g_now["第13版型"],
    }
    print("\n══ 走行前の予測との突合（predict_v13_6.md §2）")
    n_hit = 0
    for k, (want, base) in PRED.items():
        ok = got[k] in want
        n_hit += ok
        print(f"  {'当' if ok else '外'}  {k:34s} 第13.5版={base:<3d} "
              f"予測 {min(want)}〜{max(want):<3d} 実測 {got[k]}")
    print(f"  ―― {n_hit}/{len(PRED)}")
    print("\n  ★ 走行内の対照（predict_v13_6.md §1）")
    print(f"     A41 処置した E1（2セル・4体）：2027-05-31 に触れた {got['B6 E1の4体が 2027-05-31 に触れる']}/4"
          f"　←第13.5版は 4/4")
    print(f"     A42 放置した R （4セル・8体）：2027-04-01 に触れた "
          f"{got['B7 Rの8体が 2027-04-01 に触れる']}/8　←第13.5版は 4/8")
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
