# -*- coding: utf-8 -*-
"""生成後検査（層3.5）＋ 予測と観察の突合。

突合は **配列の順序** で行う。エージェントが返した文字列 id を鍵にしない
（前回それで欠損した）。段の対応も、Σ の順序に対して位置で合わせる。
"""
import json, re, sys
from sales_logic import Declared, validate_copy

STAGES = ("①", "②", "③", "④", "⑤", "⑥")
NORM = {"1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤", "6": "⑥",
        "S1": "①", "S2": "②", "S3": "③", "S4": "④", "S5": "⑤", "S6": "⑥"}


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


DECFILE = "decisions8_v10.json"
OUT = "verified8_v10.json"


def main(runfile):
    run = json.load(open(runfile, encoding="utf-8"))
    dec = {r["id"]: r for r in json.load(open(DECFILE, encoding="utf-8"))}
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for cell in run:
        d = dec[cell["id"]]
        sigma = d["sigma"]
        g, o = cell["gen"], cell["obs"]
        copy = {}
        for i, s in enumerate(g["slides"]):
            copy[norm_stage(s.get("stage"), sigma, i)] = s.get("text", "")
        dd = g.get("declared", {})
        D = Declared(
            s2_unit=(dd.get("s2_unit") or None),
            s2_from_unit=(dd.get("s2_from_unit") or None),
            s4_declares_repetition=dd.get("s4_declares_repetition"),
            s4_period_months=dd.get("s4_period_months"),
            s6_period_months=dd.get("s6_period_months"),
            s5_is_constraint_disclosure=dd.get("s5_is_constraint_disclosure"),
            s6_ends_imperative=dd.get("s6_ends_imperative"),
            s6_contains_promise=dd.get("s6_contains_promise"),
            s6_recasts_unit=dd.get("s6_recasts_unit"),
            s3_form_mapping=dd.get("s3_form_mapping"),
            s6_kappa=dd.get("s6_kappa"),
            s6_coverage_full=dd.get("s6_coverage_full"),
            s6_coverage_disclosed=dd.get("s6_coverage_disclosed"),
            s6_coverage_subset=dd.get("s6_coverage_subset"),
            s6_kappa_type=dd.get("s6_kappa_type"),
            s6_realize_actor=dd.get("s6_realize_actor"),
            s6_realize_date=dd.get("s6_realize_date"),
            s6_realize_account=dd.get("s6_realize_account"),
            s6_start_date=dd.get("s6_start_date"),
            s6_self_check=dd.get("s6_self_check"),
            s5_denies_own=dd.get("s5_denies_own"),
        )
        v = validate_copy(copy, D, kappa_final=d['kappa_n'],
                          stages=sigma, n_seats=len(d['seats']),
                          executors=[(a, cs) for a, cs in (d.get('executors') or [])],
                          deadline=d.get('start_deadline'),
                          gamma_own=d.get('gamma_own') or {},
                          chain=[tuple(x) for x in (d.get('chain') or [])])
        pred = {norm_stage(p.get("stage"), sigma, i): p.get("verdict")
                for i, p in enumerate((cell.get("pred") or {}).get("prediction", []))}
        obs = {norm_stage(r.get("stage"), sigma, i): r.get("verdict")
               for i, r in enumerate(o.get("reactions", []))}
        obs_why = {norm_stage(r.get("stage"), sigma, i): r.get("why", "")
                   for i, r in enumerate(o.get("reactions", []))}
        diff = [{"stage": s, "pred": pred.get(s), "obs": obs.get(s), "why": obs_why.get(s, "")}
                for s in sigma if pred.get(s) != obs.get(s)]
        out.append({
            "id": cell["id"], "業界": d["業界"], "セグメント": d["セグメント"], "商材": d["商材"],
            "sigma": sigma, "kappa_n": d["kappa_n"], "j_star": d["j_star"],
            "rank_path": d.get("rank_path"), "monotone": d.get("monotone"),
            "copy": copy, "declared": dd,
            "pred": pred, "obs": obs, "obs_why": obs_why, "diff": diff,
            "pred_longest": norm_stage((cell.get("pred") or {}).get("longest_stage"), sigma, 0),
            "pred_forward": (cell.get("pred") or {}).get("would_forward"),
            "weakest_point": (cell.get("pred") or {}).get("weakest_point", ""),
            "obs_longest": norm_stage(o.get("longest_stage"), sigma, 0),
            "closing_line": o.get("closing_line", ""),
            "would_forward": o.get("would_forward"),
            "unanswered": o.get("unanswered", ""),
            "self_report": g.get("self_report", ""),
            "post_findings": [{"code": f.code, "level": f.level, "ref": f.ref,
                               "msg": msgs["findings"].get(f.code, f.code)} for f in v["findings"]],
            "post_judgments": [{"code": j.code, "ref": j.ref,
                                "msg": msgs["judgments"].get(j.code, j.code)} for j in v["needs_judgment"]],
            "post_pass": v["pass"],
        })
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("cell    Σ        予測最長 観察最長 上申  R9/R10")
    for r in out:
        stops = [f["code"] for f in r["post_findings"] if f["level"] == "stop"]
        print(f"{r['id']:7s} {''.join(r['sigma']):9s} {r['pred_longest']:5s} {r['obs_longest']:5s} "
              f"{'○' if r['would_forward'] else '×'}   {stops if stops else 'clean'}")
    print()
    hit = sum(1 for r in out if r["pred_longest"] == r["obs_longest"])
    print(f"最長滞在の予測一致 {hit}/{len(out)}")
    tot = sum(len(r["sigma"]) for r in out)
    dif = sum(len(r["diff"]) for r in out)
    print(f"段ごとの予測一致 {tot-dif}/{tot}")
    print(f"⑥まで通過（上申する）{sum(1 for r in out if r['would_forward'])}/{len(out)}")
    print()
    for r in out:
        if r["diff"]:
            print(f"― {r['id']}")
            for d_ in r["diff"]:
                print(f"   {d_['stage']} 予測={d_['pred']} 観察={d_['obs']}  {d_['why'][:90]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "run8_v2.json")
