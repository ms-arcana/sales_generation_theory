# -*- coding: utf-8 -*-
"""第13.3版 R1 の採点 ―― 買い手は資料の質を区別しているか。

現行（第13版の実測）を対照に、劣化版・改善版と比べる。
**①〜⑤は一字も変えていない**ので、そこの一致率が買い手の振れ幅（R2）の部分的な答えになる。

  python3 validate_r1.py
"""
import re
import sys
from collections import Counter, defaultdict

from stamp import load as _load, dump_stamped
from validate8_v12 import norm_stage

DEC = {r["id"]: r for r in _load("decisions8_v12.json")}
IDS = ("E1-P1", "R2-P2")
SEATS = {"E1-P1": ["入試広報課長", "学部長会"], "R2-P2": ["店長", "社長"]}

PREDICT = {"改善の⑥棄却": (0, 1, 2), "劣化の⑥棄却": (4,), "現行の⑥棄却": (4,)}
REASON = [("空欄・未記入", r"空欄|未記入|【　|埋め|記入欄"),
          ("金額の幅", r"幅|倍|レンジ|一本で"),
          ("座席ごとの量が無い", r"私(?:に|へ)(?:向け|宛)|自分(?:に|へ)(?:向け|宛)の(?:量|数字)|"
                            r"座席ごと|私の(?:様式|欄|物差し)で(?:読め|書け)|一行も(?:出て|書かれ)"),
          ("戻りが小さい", r"桁が違う|引き合わ|割に合わ|コンマ|届かない|%")]


def main():
    try:
        R = _load("r1/buyers.json")
    except FileNotFoundError:
        print("★ r1/buyers.json が要る（journal から書き出すこと）"); sys.exit(1)
    cur = {(r["id"], r["seat"]): r for r in _load("verified_stage2.json")["rows"]
           if r["id"] in IDS}
    got = {(x["id"], x["ver"], x["seat"]): x["gen"] for x in R if x.get("ok")}

    rows, agree, tot = [], 0, 0
    six = Counter()
    reasons = defaultdict(Counter)
    print("══ 判定（現行は第13版の実測）")
    for cid in IDS:
        sg = DEC[cid]["sigma"]
        print(f"  {cid}  Σ={''.join(sg)}")
        for seat in SEATS[cid]:
            base = cur[(cid, seat)]["verdicts"]
            line = f"     {seat:12s} 現行 " + " ".join(f"{s}:{base.get(s,'-')}" for s in sg)
            print(line)
            six["現行" if base.get("⑥") == "棄却" else "現行_通"] += 0
            if base.get("⑥") == "棄却":
                six["現行"] += 1
            for ver in ("劣化", "改善"):
                g = got.get((cid, ver, seat))
                if not g:
                    print(f"     {'':12s} {ver} ★欠落"); continue
                v = {}
                for i, x in enumerate(g.get("reactions", [])):
                    v[norm_stage(x.get("stage"), sg, i)] = x.get("verdict")
                print(f"     {'':12s} {ver} " + " ".join(f"{s}:{v.get(s,'-')}" for s in sg))
                print(f"     {'':12s}      「{(g.get('closing_line') or '')[:90]}」")
                if v.get("⑥") == "棄却":
                    six[ver] += 1
                    why = next((x.get("why", "") for i, x in enumerate(g["reactions"])
                                if norm_stage(x.get("stage"), sg, i) == "⑥"), "")
                    for n, p in REASON:
                        if re.search(p, why):
                            reasons[ver][n] += 1
                # ①〜⑤ は一字も変えていない → 一致するはず
                for s in sg[:-1]:
                    if s in base and s in v:
                        tot += 1; agree += (base[s] == v[s])
                rows.append({"id": cid, "ver": ver, "seat": seat, "verdicts": v,
                             "closing_line": g.get("closing_line"),
                             "own_retracted": g.get("own_retracted"),
                             "carries_forward": g.get("carries_forward"),
                             "reactions": g.get("reactions")})
    # 現行の⑥棄却理由（第13版の実測から数え直す）
    for cid in IDS:
        for seat in SEATS[cid]:
            r = next(x for x in _load("verified_stage2.json")["rows"]
                     if x["id"] == cid and x["seat"] == seat)
            if r["verdicts"].get("⑥") == "棄却":
                why = next((x.get("why", "") for x in r.get("reactions", [])
                            if "⑥" in (x.get("stage") or "")), "")
                for n, p in REASON:
                    if re.search(p, why):
                        reasons["現行"][n] += 1

    dump_stamped(rows, "verified_r1.json")

    print("\n══ ⑥の棄却（各版 4人中）")
    for ver in ("現行", "劣化", "改善"):
        print(f"  {ver}  {six[ver]} / 4")
    print("\n══ ⑥棄却の理由（重複あり）")
    hdr = [n for n, _ in REASON]
    print("        " + "".join(f"{h:>16s}" for h in hdr))
    for ver in ("現行", "劣化", "改善"):
        print(f"  {ver:4s}  " + "".join(f"{reasons[ver][h]:>16d}" for h in hdr))

    print("\n══ 予測との突合（走行前に置いたもの）")
    g = {"改善の⑥棄却": six["改善"], "劣化の⑥棄却": six["劣化"], "現行の⑥棄却": six["現行"]}
    miss = []
    for k, want in PREDICT.items():
        ok = g[k] in want
        print(f"  {'○' if ok else '×'} {k:14s} 予測={min(want)}〜{max(want)} 実測={g[k]}")
        if not ok:
            miss.append((k, g[k]))

    pct = 100 * agree // tot if tot else 0
    print(f"\n══ ①〜⑤（一字も変えていない）の一致 {agree}/{tot} = {pct}%   ／ 予測は 80〜100%")
    print("   ※ 60% を下回れば、買い手そのものが n=1 では読めない（R2 が最優先に繰り上がる）")

    print("\n══ 読み")
    if six["改善"] <= 2 and six["劣化"] >= 3:
        print("  → **買い手は形を区別している。**⑥ 0/16 はモデルについての情報であり、")
        print("     N₄′ の診断は正しい。実装へ進んでよい。")
    elif six["改善"] >= 3 and six["劣化"] >= 3:
        print("  → **N₄′ は誤診の疑い。**空欄でも幅でもない何かが⑥を落としている。")
        print("     棄却理由の中身を読み直すところからやり直す。")
    else:
        print("  → 予測の外。棄却理由の分布を読むこと。")
    if pct < 60:
        print("  → **①〜⑤ の一致が低い。買い手が振れている。**n=1 の結論すべてが読み直し。")
    print(f"\n{'予測はすべて的中' if not miss else '外れ: ' + str(miss)}")


if __name__ == "__main__":
    main()
