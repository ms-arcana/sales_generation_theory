# -*- coding: utf-8 -*-
"""アーム3本の生成物を、同じ論理式で採点する（層3.5）。

買い手は使わない。ここで測るのは **仕様の遵守** だけ。
突合は配列の順序で行う（エージェントが返した文字列 id を鍵にしない）。

  python3 validate8_v11.py run8_v11.json
"""
import json
import re
import sys
from collections import Counter

from sales_logic import Declared, Product, validate_copy

STAGES = ("①", "②", "③", "④", "⑤", "⑥")
NORM = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤", "6": "⑥",
        "S1": "①", "S2": "②", "S3": "③", "S4": "④", "S5": "⑤", "S6": "⑥"}

DECFILE = "decisions8_v10.json"
OUT = "verified8_v11.json"

# 走る前に置いた予測（外したらそれがアノマリー）
#   arm0 … 共通修正で R12b 1・R10a 5・R13/A24 2 が消える。A16 と R10b はそのまま残る
#   arm1 … ⑥の枚仕様に座席ごとの列挙を入れたので A16 は落ちる。字数は変えていないので R10b は残る
#   arm2 … 字数を配分し直したので R10b も落ちる
PREDICT = {0: {"stop": 17, "A16": 7, "R10b": 10, "SEATWORD": 0},
           1: {"stop": 10, "A16": 1, "R10b": 8, "SEATWORD": 1},
           2: {"stop": 2, "A16": 0, "R10b": 1, "SEATWORD": 0}}


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


def to_declared(dd):
    """LLM の申告（配列形式）を Declared へ。A23／A24 の組はタプルに畳む。"""
    by_seat = None
    if dd.get("s6_kappa_by_seat"):
        by_seat = {x["seat"]: x["kappa"] for x in dd["s6_kappa_by_seat"]
                   if isinstance(x, dict) and x.get("seat")}
    realize = None
    if dd.get("s6_realize"):
        realize = tuple((x.get("actor"), x.get("date"), x.get("account"))
                        for x in dd["s6_realize"] if isinstance(x, dict))
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
    )


def main(runfile):
    run = json.load(open(runfile, encoding="utf-8"))
    dec = {r["id"]: r for r in json.load(open(DECFILE, encoding="utf-8"))}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for cell in run:
        d = dec[cell["id"]]
        sigma = d["sigma"]
        g = cell["gen"]
        copy = {}
        for i, s in enumerate(g["slides"]):
            copy[norm_stage(s.get("stage"), sigma, i)] = s.get("text", "")
        D = to_declared(g.get("declared", {}))
        v = validate_copy(copy, D, kappa_final=d["kappa_n"],
                          stages=sigma, n_seats=len(d["seats"]),
                          executors=[(a, cs) for a, cs in (d.get("executors") or [])],
                          deadline=d.get("start_deadline"),
                          gamma_own=d.get("gamma_own") or {},
                          chain=[tuple(x) for x in (d.get("chain") or [])],
                          unwilling=d.get("unwilling") or [],
                          # 第12.1版：生成後検査にも商材座標を渡す（第10版の生成子が
                          # 生成前にしか届いていなかった）。業界は決定表が持っていれば渡す。
                          prod=Product(**d["prod"]) if d.get("prod") else None,
                          industry=d.get("industry"))
        out.append({
            "arm": cell["arm"], "id": cell["id"],
            "業界": d["業界"], "セグメント": d["セグメント"], "商材": d["商材"],
            "sigma": sigma, "copy": copy, "declared": g.get("declared", {}),
            "chars": {k: len(t) for k, t in copy.items()},
            "self_report": g.get("self_report", ""),
            "post_findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                               "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
            "post_judgments": [{"code": j.code, "ref": j.ref,
                                "msg": msgs["judgments"].get(j.code, j.code)} for j in v["needs_judgment"]],
            "post_pass": v["pass"],
        })
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"{'arm':4s} {'cell':8s} {'⑥字数':>6s}  停止コード")
    for r in sorted(out, key=lambda x: (x["arm"], x["id"])):
        st = [f["code"] for f in r["post_findings"] if f["level"] == "stop"]
        print(f"{r['arm']:<4d} {r['id']:8s} {r['chars'].get('⑥', 0):>6d}  {st if st else 'clean'}")

    print("\n=== アーム別 ===")
    print(f"{'arm':4s} {'stop':>5s} {'予測':>5s} {'A16':>5s} {'R10b':>5s} {'紙側':>5s} {'pass':>6s} "
          f"{'座席申告':>8s} {'⑥平均字':>8s}")
    for a in sorted({r["arm"] for r in out}):
        rs = [r for r in out if r["arm"] == a]
        codes = Counter(f["code"] for r in rs for f in r["post_findings"] if f["level"] == "stop")
        n_stop = sum(codes.values())
        a16 = codes.get("A16_NOT_CONV_AT_SEAT", 0)
        r10b = codes.get("R10b_UNIT_ABSENT", 0) + codes.get("R10b_UNIT_REPLACED", 0)
        sw = codes.get("A23_SEAT_WORD_ABSENT", 0)
        npass = sum(1 for r in rs if r["post_pass"])
        nseat = sum(1 for r in rs if r["declared"].get("s6_kappa_by_seat"))
        c6 = [r["chars"].get("⑥", 0) for r in rs]
        p = PREDICT.get(a, {})
        print(f"{a:<4d} {n_stop:>5d} {p.get('stop', '-'):>5} {a16:>5d} {r10b:>5d} {sw:>5d} "
              f"{npass:>4d}/{len(rs):<2d} {nseat:>6d}/{len(rs):<2d} {sum(c6)//len(c6):>8d}")
        for k, n in codes.most_common():
            print(f"       {n:>2d} {k}")

    print("\n=== 予測との差（外したものが次のアノマリー） ===")
    for a in sorted({r["arm"] for r in out}):
        rs = [r for r in out if r["arm"] == a]
        codes = Counter(f["code"] for r in rs for f in r["post_findings"] if f["level"] == "stop")
        got = {"stop": sum(codes.values()),
               "A16": codes.get("A16_NOT_CONV_AT_SEAT", 0),
               "R10b": codes.get("R10b_UNIT_ABSENT", 0) + codes.get("R10b_UNIT_REPLACED", 0),
               "SEATWORD": codes.get("A23_SEAT_WORD_ABSENT", 0)}
        for k, want in PREDICT.get(a, {}).items():
            mark = "的中" if got[k] == want else f"外れ（差 {got[k] - want:+d}）"
            print(f"  arm{a} {k:5s} 予測 {want:>3d} / 観察 {got[k]:>3d}  {mark}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "run8_v11.json")
