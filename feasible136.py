# -*- coding: utf-8 -*-
"""走らせる前に、**指示が充足可能か**を機械で確かめる（第13.5版 A37b の教訓）。

第13.5版では、④からの逆算日を「着手期限」と呼んだまま A37 を足したせいで、
8セル中6セルが**どう書いても違反する指示**になっていた。走行前に指示文を読んで気づいた。
今回は四つの制約が重なるので、**手で読むのではなく総当たりで確かめる**。

  today ≤ 決定 ≤ min(決定期限, 決定の窓)
  着手  ≥ 決定 ＋ LT
  着手  ≥ 決定の窓            ← A41b（第13.7版）
  実現  ≥ 着手 ＋ ω
  実現の月 ∉ 繁忙期

  python3 feasible136.py
"""
from datetime import date, timedelta

from sales_logic import add_months, iso_date
from stamp import load


def feasible(rec):
    t0 = iso_date(rec["today"])
    ub = [iso_date(rec.get("decide_deadline") or rec.get("start_deadline") or "")]
    ub += [iso_date(g[0]) for g in (rec.get("decision_gates") or [])]
    ub = [x for x in ub if x]
    hi = min(ub) if ub else date(t0.year + 5, t0.month, 1)
    lt, om = rec["lt_months"], rec["omega"]
    busy = set(rec.get("busy_months") or ())
    # A41b（第13.7版）：着手は〈決定＋LT〉と〈決定の窓〉の**両方より後**でなければならない。
    gate_lo = max([iso_date(g[0]) for g in (rec.get("decision_gates") or []) if iso_date(g[0])],
                  default=None)
    d = t0
    while d <= hi:                       # 決定日を総当たり（日単位）
        s = add_months(d, lt)
        if gate_lo and s < gate_lo:
            s = gate_lo
        r = add_months(s, om)
        for k in range(0, 24):           # 実現日は最短からひと月ずつ後ろへ
            rr = add_months(r, k)
            if rr.month not in busy:
                return {"決定": d, "着手": s, "実現": rr, "後ろ倒し月数": k}
        d += timedelta(days=1)
    return None


def main():
    rows = load("decisions8_v12.json")
    bad = []
    print("══ 指示は充足可能か（最も早い解）")
    print(f"  {'cell':7}{'LT':>3}{'ω':>3}  {'上限':11} {'決定':11} {'着手':11} {'実現':11} 繁忙で後ろ倒し")
    for r in rows:
        got = feasible(r)
        ub = [x for x in [r.get("decide_deadline")] + [g[0] for g in (r.get("decision_gates") or [])] if x]
        hi = min(ub) if ub else "―"
        if not got:
            bad.append(r["id"]); print(f"  {r['id']:7}★ 解なし"); continue
        print(f"  {r['id']:7}{r['lt_months']:>3}{r['omega']:>3}  {str(hi):11} "
              f"{got['決定']} {got['着手']} {got['実現']} {got['後ろ倒し月数']}か月")
    print()
    if bad:
        print(f"★★ 充足不能なセルがある：{bad}。**走らせてはいけない。**")
    else:
        print("   8セルとも解が在る。指示どうしは矛盾していない。")
    return not bad


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
