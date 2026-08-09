# -*- coding: utf-8 -*-
"""第12.2版 ―― Arm 1 再走行の採点（層3.5）。

第12版の走行では R10a の指示文が一度も渡っていなかった（決定表がコードより古かった）。
今回はその一行を入れた `prompts8_v12_arm1.json` で同じ8セルを回し、**同じ物差しで**測る。

  ・生成物は run12/out_<ID>.json（各エージェントが自分で書いたもの）
  ・決定表は decisions8_v12.json（指示文を組んだのと同じ表）
  ・比較対象は verified8_v11.json の arm==1（第12.1版の物差しで採点済み）
  ・予測は predict_v12_2.md（走る前に置いたもの）

  python3 validate8_v12.py
"""
import glob
import json
import os
import re
import sys
from collections import Counter

from sales_logic import Declared, Product, validate_copy

STAGES = ("①", "②", "③", "④", "⑤", "⑥")
NORM = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤", "6": "⑥",
        "S1": "①", "S2": "②", "S3": "③", "S4": "④", "S5": "⑤", "S6": "⑥"}

DECFILE = "decisions8_v12.json"
PREVFILE = "verified8_v11.json"
OUT = "verified8_v12_arm1.json"

# 走る前に置いた予測（predict_v12_2.md）。外れたものが次のアノマリー
PREDICT = {"stop": 3, "R10a": 3, "A16": 0, "R10b": 0, "SEATWORD": 0,
           "pass": 4, "s4_false": 2, "by_seat_declared": 8}


def unwrap(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["data"] if isinstance(d, dict) and "data" in d else d


def norm_stage(s, sigma, idx):
    s = (s or "").strip()
    if s in STAGES:
        return s
    if s in NORM:
        return NORM[s]
    m = re.search(r"[①-⑥]", s)
    if m:
        return m.group(0)
    m = re.search(r"[1-6]", s)
    if m:
        return NORM[m.group(0)]
    return sigma[idx] if idx < len(sigma) else "?"


MSG_BLOCKS = json.load(open("messages.json", encoding="utf-8"))["blocks"]


def to_declared(dd):
    by_seat = None
    if dd.get("s6_kappa_by_seat"):
        by_seat = {x["seat"]: x["kappa"] for x in dd["s6_kappa_by_seat"]
                   if isinstance(x, dict) and x.get("seat")}
    realize = None
    if dd.get("s6_realize"):
        realize = tuple((x.get("actor"), x.get("date"), x.get("account"))
                        for x in dd["s6_realize"] if isinstance(x, dict))
    omitted = None
    if dd.get("s6_omitted_blocks") is not None:
        # 生成器は日本語の要素名で答える（コードは渡していない）。ここでコードへ戻す。
        # sales_logic は記号しか扱わない設計なので、翻訳はこの層でやる。
        rev = {v: k for k, v in MSG_BLOCKS.items()}
        omitted = tuple(rev.get(str(x).strip(), str(x).strip())
                        for x in dd["s6_omitted_blocks"] if str(x).strip())
    qsrc = None
    if dd.get("s6_quantity_sources"):
        qsrc = {x["seat"]: x["source"] for x in dd["s6_quantity_sources"]
                if isinstance(x, dict) and x.get("seat")}
    to_sales = None
    if dd.get("s6_to_sales") is not None:
        to_sales = tuple(str(x).strip() for x in dd["s6_to_sales"] if str(x).strip())
    return Declared(
        s2_unit=(dd.get("s2_unit") or None),
        s2_from_unit=(dd.get("s2_from_unit") or None),
        s3_form_mapping=dd.get("s3_form_mapping"),
        s4_declares_repetition=dd.get("s4_declares_repetition"),
        s4_period_months=dd.get("s4_period_months"),
        s6_period_months=dd.get("s6_period_months"),
        s6_residual_period_months=dd.get("s6_residual_period_months"),
        s5_is_constraint_disclosure=dd.get("s5_is_constraint_disclosure"),
        s6_ends_imperative=dd.get("s6_ends_imperative"),
        s6_contains_promise=dd.get("s6_contains_promise"),
        s6_recasts_unit=dd.get("s6_recasts_unit"),
        s6_kappa=dd.get("s6_kappa"),
        s6_coverage_full=dd.get("s6_coverage_full"),
        s6_coverage_disclosed=dd.get("s6_coverage_disclosed"),
        s6_coverage_subset=dd.get("s6_coverage_subset"),
        s6_kappa_type=dd.get("s6_kappa_type"),
        s6_start_date=dd.get("s6_start_date"),
        s6_self_check=dd.get("s6_self_check"),
        s5_denies_own=dd.get("s5_denies_own"),
        s6_kappa_by_seat=by_seat,
        s6_realize=realize,
        s6_omitted_blocks=omitted,
        s6_quantity_sources=qsrc,
        s6_to_sales=to_sales,
    )


def score(d, g):
    sigma = d["sigma"]
    copy = {}
    for i, s in enumerate(g["slides"]):
        copy[norm_stage(s.get("stage"), sigma, i)] = s.get("text", "")
    D = to_declared(g.get("declared", {}))
    v = validate_copy(copy, D, kappa_final=d["kappa_n"], stages=sigma,
                      n_seats=len(d["seats"]),
                      executors=[(a, cs) for a, cs in (d.get("executors") or [])],
                      deadline=d.get("start_deadline"),
                      gamma_own=d.get("gamma_own") or {},
                      chain=[tuple(x) for x in (d.get("chain") or [])],
                      unwilling=d.get("unwilling") or [],
                      prod=Product(**d["prod"]) if d.get("prod") else None,
                      industry=d.get("industry"),
                          blocks=d.get("blocks") or [])
    return copy, D, v


def main():
    dec = {r["id"]: r for r in unwrap(DECFILE)}
    msgs = json.load(open("messages.json", encoding="utf-8"))

    # ── 前提の確認：採点に使う欄が、as-run の表と新しい表で同じであること
    old = {r["id"]: r for r in unwrap("decisions8_v10.json")}
    keys = ("sigma", "kappa_n", "seats", "executors", "start_deadline",
            "gamma_own", "chain", "unwilling", "prod")
    drift = [(i, k) for i in dec for k in keys if dec[i].get(k) != old[i].get(k)]
    print(f"══ 採点入力の同一性：as-run の決定表と新しい表で、採点に使う欄の差 {len(drift)}件"
          f" {drift if drift else '（＝前回 Arm 1 と同じ物差しで比べられる）'}")

    files = sorted(glob.glob("run12/out_*.json"))
    if not files:
        sys.exit("run12/out_*.json が無い。走行が終わっていない")
    out = []
    for fp in files:
        g = json.load(open(fp, encoding="utf-8"))
        cid = g.get("cell_id") or os.path.basename(fp)[4:-5]
        if cid not in dec:
            print(f"  ★ 未知のセル {cid}（{fp}）"); continue
        d = dec[cid]
        copy, D, v = score(d, g)
        out.append({
            "arm": 1, "id": cid, "業界": d["業界"], "セグメント": d["セグメント"], "商材": d["商材"],
            "sigma": d["sigma"], "copy": copy, "declared": g.get("declared", {}),
            "chars": {k: len(t) for k, t in copy.items()},
            "self_report": g.get("self_report", ""),
            "post_findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                               "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
            "post_judgments": [{"code": j.code, "ref": j.ref,
                                "msg": msgs["judgments"].get(j.code, j.code)} for j in v["needs_judgment"]],
            "post_pass": v["pass"],
        })
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    prev = {r["id"]: r for r in json.load(open(PREVFILE, encoding="utf-8")) if r["arm"] == 1}

    print(f"\n══ セル別（前回 Arm 1 → 今回）")
    print(f"{'cell':8s} {'⑥字数':>10s}  {'s4宣言':>16s} {'s4周期':>10s} {'s6周期':>10s}  停止")
    for r in sorted(out, key=lambda x: x["id"]):
        p = prev.get(r["id"], {})
        pd, nd = p.get("declared", {}), r["declared"]
        st = [f["code"] for f in r["post_findings"] if f["level"] == "stop"]
        pst = [f["code"] for f in p.get("post_findings", []) if f["level"] == "stop"]

        def arrow(a, b):
            return f"{str(a)}→{str(b)}" if a != b else str(b)
        print(f"{r['id']:8s} {arrow(p.get('chars',{}).get('⑥',0), r['chars'].get('⑥',0)):>10s}  "
              f"{arrow(pd.get('s4_declares_repetition'), nd.get('s4_declares_repetition')):>16s} "
              f"{arrow(pd.get('s4_period_months'), nd.get('s4_period_months')):>10s} "
              f"{arrow(pd.get('s6_period_months'), nd.get('s6_period_months')):>10s}  "
              f"{pst if pst else 'clean'} → {st if st else 'clean'}")

    codes = Counter(f["code"] for r in out for f in r["post_findings"] if f["level"] == "stop")
    infos = Counter(f["code"] for r in out for f in r["post_findings"] if f["level"] == "info")
    juds = Counter(j["code"] for r in out for j in r["post_judgments"])
    got = {
        "stop": sum(codes.values()),
        "R10a": codes.get("R10a_REPRODUCES_PROBLEM", 0),
        "A16": codes.get("A16_NOT_CONV_AT_SEAT", 0),
        "R10b": codes.get("R10b_UNIT_ABSENT", 0),
        "SEATWORD": codes.get("A23_SEAT_WORD_ABSENT", 0),
        "pass": sum(1 for r in out if r["post_pass"]),
        "s4_false": sum(1 for r in out if r["declared"].get("s4_declares_repetition") is False),
        "by_seat_declared": sum(1 for r in out if r["declared"].get("s6_kappa_by_seat")),
    }

    print(f"\n══ 合計（前回 Arm 1 → 今回）")
    prev_codes = Counter(f["code"] for r in prev.values()
                         for f in r["post_findings"] if f["level"] == "stop")
    print(f"  stop {sum(prev_codes.values())} → {got['stop']}")
    for k in sorted(set(codes) | set(prev_codes)):
        print(f"      {prev_codes.get(k,0):>2d} → {codes.get(k,0):>2d}  {k}")
    print(f"  pass {sum(1 for r in prev.values() if r['post_pass'])}/8 → {got['pass']}/8")
    c6 = [r["chars"].get("⑥", 0) for r in out]
    p6 = sorted(r["chars"].get("⑥", 0) for r in prev.values())
    print(f"  ⑥字数 平均 {sum(p6)//len(p6)} → {sum(c6)//len(c6)}")
    print(f"    前回 {p6}")
    print(f"    今回 {sorted(c6)}")
    if infos:
        print("  註記(info):", dict(infos))
    if juds:
        print("  要判断:", dict(juds))

    print(f"\n══ 予測との差（外したものが次のアノマリー）")
    for k, want in PREDICT.items():
        mark = "的中" if got[k] == want else f"外れ（差 {got[k]-want:+d}）"
        print(f"  {k:18s} 予測 {want:>3d} / 観察 {got[k]:>3d}   {mark}")

    print(f"\n══ R10a の中身（今回）")
    for r in sorted(out, key=lambda x: x["id"]):
        nd = r["declared"]
        if "④" not in r["sigma"]:
            print(f"  {r['id']:8s} ④が Σ に無い（検査対象外）"); continue
        s4r, s4p, s6p = (nd.get("s4_declares_repetition"), nd.get("s4_period_months"),
                         nd.get("s6_period_months"))
        if s4r is not True:
            kind = "回避A：④の反復宣言を下ろした"
        elif s6p == 0 or s4p == 0:
            kind = "回避B：単発と申告"
        elif s6p <= s4p:
            kind = "★発火（変化なし）"
        else:
            kind = "実質的充足：⑥の周期 > ④の周期"
        print(f"  {r['id']:8s} s4宣言={str(s4r):5s} s4={str(s4p):>4s} s6={str(s6p):>4s}  {kind}")

    print(f"\n══ 自己申告（書ききれなかった点・規定が無くて困った点）")
    for r in sorted(out, key=lambda x: x["id"]):
        sr = (r["self_report"] or "").replace("\n", " ")
        if sr and sr != "なし":
            print(f"  ── {r['id']}\n     {sr[:420]}")


if __name__ == "__main__":
    main()
