# -*- coding: utf-8 -*-
"""25業界走行の21件を、いまのコードで採点し直す（引き継ぎ書 第14版 §5 #4）。**走らせない。**

as-run は第12.8版（`sales_logic.py` sha256[:12] `28181539e212`）。
生成物と決定表は別枝にあり、`industry-run.bundle` で受け取っている。

    git fetch industry-run.bundle \
      refs/heads/industry23-it-consulting:refs/remotes/bundle/industry23
    python3 rescore21.py

問いは一つ ―― **`R12b_START_AFTER_DEADLINE` は誤停止だったか。**
25業界の突合（`25業界走行との突合.md` §1）はこう言った。

    停止9件のうち5件で買い手は進めた。うち3件が同じ検査 R12b。
    逆算日は「着手期限」ではなく**決定期限**だった（A37b）。
    旧い読みのままなら、着手日が逆算日を越えただけで止まる ―― **誤停止の疑いが濃い。**

反実仮想も一緒に測る。`check_dates_v7` の

    dcd = dec.s6_decide_date or dec.s6_start_date      # 旧走行は欄が一つしかない

という**代入をやめたら**停止が何件になるか。⊥ を⊥のまま扱う（`N₂`）とどうなるか。
"""
import contextlib
import io
import json
import os
import subprocess
import sys

REF = "bundle/industry23"
LEDGER = "ind25_data.json"


def from_bundle(path):
    r = subprocess.run(["git", "show", f"{REF}:{path}"], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"★ {REF}:{path} が読めない。先に取り込んでください:\n"
                 f"   git fetch industry-run.bundle "
                 f"refs/heads/industry23-it-consulting:refs/remotes/{REF}")
    return json.loads(r.stdout)


def unwrap(o):
    return o["data"] if isinstance(o, dict) and "_stamp" in o else o


def main():
    import validate8_v12 as V

    dec = {r["id"]: r for r in unwrap(from_bundle("decisions_ind.json"))
           if not r.get("_error")}
    ids = sorted(r["id"] for r in unwrap(from_bundle("verified_ind.json")))
    asrun = {r["id"]: r for r in unwrap(from_bundle("verified_ind.json"))}
    led = {r["id"]: r for r in json.load(open(LEDGER, encoding="utf-8"))}
    gens = {c: unwrap(from_bundle(f"ind_run/out_{c}.json")) for c in ids}

    def measure():
        out = {}
        for c in ids:
            with contextlib.redirect_stdout(io.StringIO()):
                _, D, v = V.score(dec[c], gens[c])
            out[c] = ({f.code for f in v["findings"] if f.level == "stop"},
                      {j.code for j in v["needs_judgment"]}, D)
        return out

    now = measure()

    print(f"══ 25業界21件を、いまのコードで採点し直す（as-run は第12.8版）\n")
    print(f"{'id':9}{'買い手の判定':14}{'④逆算日':12}{'⑥決定日':10}{'⑥着手日':12} R12b")
    for c in ids:
        stop, _, D = now[c]
        was = set(asrun[c].get("stops") or {})
        r_was = any("R12b" in x for x in was)
        r_now = "R12b_START_AFTER_DEADLINE" in stop
        mark = {(1, 1): "出た→出た", (1, 0): "出た→消えた",
                (0, 1): "無→出た", (0, 0): "―"}[(int(r_was), int(r_now))]
        dl = dec[c].get("decide_deadline") or dec[c].get("start_deadline")
        print(f"{c:9}{led.get(c, {}).get('判定', '?'):14}{str(dl or '—'):12}"
              f"{str(D.s6_decide_date or '⊥'):10}{str(D.s6_start_date or '⊥'):12} {mark}")

    stops = [c for c in ids if "R12b_START_AFTER_DEADLINE" in now[c][0]]
    adv = [c for c in stops if led.get(c, {}).get("判定") != "差し戻す"]
    print(f"\nR12b 停止 {len(stops)}件 {stops}")
    print(f"  うち**買い手は進めた** {len(adv)}件 {adv}   ← 誤停止の疑い")
    print(f"  ⑥決定日を申告している件数: "
          f"{sum(1 for c in ids if now[c][2].s6_decide_date)} / {len(ids)}")

    # ── 反実仮想：代入をやめる
    import inspect
    import sales_logic as SL
    orig = SL.check_dates_v7
    src = inspect.getsource(orig).replace(
        "dcd = dec.s6_decide_date or dec.s6_start_date", "dcd = dec.s6_decide_date")
    ns = dict(SL.__dict__)
    exec(compile(src, "<patched>", "exec"), ns)
    SL.check_dates_v7 = ns["check_dates_v7"]
    try:
        alt = measure()
    finally:
        SL.check_dates_v7 = orig

    a_stops = [c for c in ids if "R12b_START_AFTER_DEADLINE" in alt[c][0]]
    a_jud = [c for c in ids if "R12b_START_UNDECLARED" in alt[c][1]]
    print(f"\n══ 反実仮想 ―― ⑥決定日が ⊥ なら ⊥ のまま（着手日で代用しない）")
    print(f"  R12b 停止 {len(a_stops)}件 {a_stops}")
    print(f"  R12b 申し送り（未申告）{len(a_jud)}件")
    print(f"  買い手が進めたのに停止: "
          f"{len([c for c in a_stops if led.get(c, {}).get('判定') != '差し戻す'])}件")
    print("\n  ※ 代入をやめると、停止は申し送りへ移る。**⊥ は「遅い」とは比べられない**（N₂）。")
    print("     `check_dates_v7` の定義域の変更なので、**提案までにとどめる**。")


if __name__ == "__main__":
    main()
