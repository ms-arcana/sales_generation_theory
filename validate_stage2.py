# -*- coding: utf-8 -*-
"""第13版 第2段の採点 ―― 仕様を満たした資料が、買い手を通るか。

**突合は配列のインデックスで行う。**エージェントが返す文字列は段の正規化にだけ使い、
セル・座席の対応は依頼側の (id, seat) を正とする。

  python3 validate_stage2.py
"""
import json
import re
import sys
from collections import Counter, defaultdict

from stamp import load as _load, dump_stamped
from validate8_v12 import norm_stage

DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
IDS = ("E1-P1", "E1-P2", "E2-P1", "E2-P2", "R1-P1", "R1-P2", "R2-P1", "R2-P2")
OUT = "verified_stage2.json"

PREDICT = {   # predict_v13.md（走行前）
    "素通りのセル": (0, 1, 2),
    "誰かが棄却したセル": (5, 6, 7, 8),
    "手前の座席が⑥を棄却したセル": (1, 2, 3),
    "j*が⑥を棄却したセル": (2, 3, 4),
    "運べないと書いた手前の座席": (2, 3, 4),
    "own_retracted 実質ありの買い手": (2, 3, 4, 5),
    "タダだと言った買い手": (0,),
}
DATE_RE = r"日付|期日|締切|縛[らるり]|効く|区分|握[っる]"
# A34 と同型：照合が浅いと「ただ、」（接続詞）に当たる。境界を取る
FREE_RE = r"タダ|無料|一円も(?:かか|要ら)|費用は(?:かから|発生し)ない|コストは(?:ゼロ|かから)|持ち出しゼロ"


def stages_of(cid):
    return DEC[cid]["sigma"]


def main():
    try:
        P = {x["id"]: x["gen"] for x in _load("stage2/preds.json") if x.get("ok")}
        B = {(x["id"], x["seat"]): x["gen"] for x in _load("stage2/buyers.json") if x.get("ok")}
    except FileNotFoundError:
        print("★ stage2/preds.json と stage2/buyers.json が要る（journal から書き出すこと）")
        sys.exit(1)

    rows, out = [], []
    cell_reject, cell_all_pass = set(), set()
    front_reject6, jstar_reject6, cannot_carry, retracted, freebie, date_doubt = [], [], [], [], [], []
    verd_by_stage = defaultdict(Counter)
    agree = miss = 0

    for cid in IDS:
        sg = stages_of(cid)
        chain = [c[0] for c in DEC[cid]["chain"]]
        jstar = DEC[cid]["j_star"]
        pred = P.get(cid)
        pmap = {}
        for i, x in enumerate(pred.get("predictions", []) if pred else []):
            pmap[(x.get("seat", "").strip(), norm_stage(x.get("stage"), sg, 0))] = x.get("verdict")
        allpass = True
        for seat in chain:
            g = B.get((cid, seat))
            if not g:
                print(f"★ 欠落 {cid}/{seat}"); continue
            rs = g.get("reactions", [])
            row = {"id": cid, "seat": seat, "j_star": seat == jstar, "verdicts": {}}
            for i, x in enumerate(rs):
                st = norm_stage(x.get("stage"), sg, i)
                v = x.get("verdict")
                row["verdicts"][st] = v
                verd_by_stage[st][v] += 1
                if v != "通過":
                    allpass = False
                    cell_reject.add(cid) if v == "棄却" else None
                pv = pmap.get((seat, st))
                if pv is not None:
                    agree += (pv == v); miss += (pv != v)
                if st == "⑥" and v == "棄却":
                    (jstar_reject6 if seat == jstar else front_reject6).append(f"{cid}/{seat}")
            cf = (g.get("carries_forward") or "")
            if seat != jstar and re.search(r"運べ(ない|ません)|運搬できない|上げられない", cf):
                cannot_carry.append(f"{cid}/{seat}")
            # 文章での否定（「取り消す必要は生じなかった」）を非 null と数えないこと
            _o = (g.get("own_retracted") or "").strip()
            if _o and not re.search(r"取り消す必要(?:は)?(?:生じ|無|な)|強いられる取り消しは(?:無|な)い|^(?:null|なし|無い|ない)|取り消していない", _o):
                retracted.append(f"{cid}/{seat}: {_o[:60]}")
            txt = " ".join(x.get("why", "") for x in rs) + " " + (g.get("closing_line") or "")
            if re.search(FREE_RE, txt):
                freebie.append(f"{cid}/{seat}")
            if re.search(DATE_RE, txt):
                date_doubt.append(f"{cid}/{seat}")
            row["closing_line"] = g.get("closing_line")
            row["own_retracted"] = g.get("own_retracted")
            row["carries_forward"] = cf
            rows.append(row)
            out.append({**row, "reactions": rs})
        if allpass:
            cell_all_pass.add(cid)

    dump_stamped({"rows": out, "preds": P}, OUT)

    print("══ 買い手16人 × 枚の判定")
    for cid in IDS:
        sg = stages_of(cid)
        print(f"  {cid}  Σ={''.join(sg)}")
        for r in [x for x in rows if x["id"] == cid]:
            v = " ".join(f"{s}:{r['verdicts'].get(s,'-')}" for s in sg)
            print(f"     {'j*' if r['j_star'] else '  '} {r['seat']:14s} {v}")
            print(f"        「{r['closing_line']}」")
    print("\n══ 枚ごとの判定の分布")
    for s in ("①", "②", "③", "④", "⑤", "⑥"):
        c = verd_by_stage[s]
        if c:
            print(f"  {s}  通過{c['通過']:>3d} 揺らぐ{c['揺らぐ']:>3d} 棄却{c['棄却']:>3d}")

    got = {
        "素通りのセル": len(cell_all_pass),
        "誰かが棄却したセル": len(cell_reject),
        "手前の座席が⑥を棄却したセル": len(set(x.split("/")[0] for x in front_reject6)),
        "j*が⑥を棄却したセル": len(set(x.split("/")[0] for x in jstar_reject6)),
        "運べないと書いた手前の座席": len(cannot_carry),
        "own_retracted 実質ありの買い手": len(retracted),
        "タダだと言った買い手": len(freebie),
    }
    print("\n══ 予測との突合（走行前に置いたもの）")
    misses = []
    for k, want in PREDICT.items():
        ok = got[k] in want
        print(f"  {'○' if ok else '×'} {k:26s} 予測={min(want)}〜{max(want):<3d} 実測={got[k]}")
        if not ok:
            misses.append((k, f"{min(want)}〜{max(want)}", got[k]))
    tot = agree + miss
    print(f"\n  予測器と買い手の一致 {agree}/{tot} = {100*agree//tot if tot else 0}%   ／ 予測は 60〜80%")
    print(f"  日付を疑った買い手 {len(set(date_doubt))}/16   ／ 予測は 2〜6")
    if retracted:
        print("\n  own_retracted:")
        for x in retracted: print("   ", x)
    if front_reject6: print("\n  手前の座席が⑥を棄却:", front_reject6)
    if cannot_carry:   print("  運べないと書いた:", cannot_carry)
    if freebie:        print("  タダだと言った:", freebie)
    print(f"\n{'予測はすべて的中' if not misses else '外れ ' + str(len(misses)) + '件: ' + str(misses)}")


if __name__ == "__main__":
    main()
