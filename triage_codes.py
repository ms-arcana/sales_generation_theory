# -*- coding: utf-8 -*-
"""**発火していない検査を仕分ける**（第14版 引き継ぎ書 §3・最大の未整理）。

`audit_model.py` (6) は「一度も出ていない」と数えるだけで、なぜ出ないかを言わない。
引き継ぎ書はこう分けろと言う。

    (a) 出るはずがない        入力側の定義域が違う／8セルでは条件が立たない
    (b) 出るはずなのに出ていない  ← いちばん高くつく。第12版の `R10a` と同型
    (c) 配線されていない       検査は書いたが、呼び出し側から呼ばれていない

**人の記憶ではなく、実行トレースで分ける。**入口は二つしかない。

    compile_deal(ν, seller, today)   … 8セルの決定表（決定的・LLM を呼ばない）
    validate_copy(copy, Declared…)   … 手元の生成物36件で再生する

    行が実行された            → ① 出た
    関数には入ったが行は未実行  → ② 条件が偽（(a) か (b)）
    関数に一度も入らなかった   → ③ (c) 配線されていない

② をさらに割るのに、**その検査が読む申告欄が届いているか**を見る。
届いていなければ「買い手が健全だから出ない」のではなく「測れていない」＝ **(b)**。

    python3 triage_codes.py
"""
import ast
import contextlib
import glob
import io
import json
import os
import sys

import stamp

SRCPATH = os.path.abspath("sales_logic.py")
SRC = open(SRCPATH, encoding="utf-8").read()
TREE = ast.parse(SRC)

# 回帰テストが叩く入口。8セルの走行では出ないのが正しい
AUDIT_FN = {"audit_requirements", "audit_symbols", "audit_axis_types", "audit_tau_forms"}


def emit_sites():
    """発火行 → コード／行 → 関数名／関数 → 読む申告欄"""
    from sales_logic import R7_DIMS
    site, fn_of_line, reads = {}, {}, {}
    for fn in [n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)]:
        for ln in range(fn.lineno, (fn.end_lineno or fn.lineno) + 1):
            fn_of_line.setdefault(ln, fn.name)
        # `dec.s5_disclaimers` の形で読んでいる申告欄
        reads[fn.name] = {n.attr for n in ast.walk(fn)
                          if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                          and n.value.id == "dec" and n.attr.startswith("s")}
    for n in ast.walk(TREE):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if nm not in ("Finding", "Judgment") or not n.args:
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            site.setdefault(n.lineno, set()).add(a.value)
        elif isinstance(a, ast.JoinedStr):
            t = ast.unparse(a).lstrip("f").strip("'\"")
            site.setdefault(n.lineno, set()).update(t.replace("{d}", d) for d in sorted(R7_DIMS))
    return site, fn_of_line, reads


def run_traced():
    """二つの入口を走らせ、実行された行と入った関数を集める"""
    executed, entered = set(), set()

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != SRCPATH:
            return None
        if event == "call":
            entered.add(frame.f_code.co_name)
            return tracer
        if event == "line":
            executed.add(frame.f_lineno)
        return tracer

    import cells8_v10 as C
    import validate8_v12 as V

    dec12 = {r["id"]: r for r in stamp.load("decisions8_v12.json")}
    dec13 = {r["id"]: r for r in stamp.load("decisions8_v13.json")}
    # 生成物 → 採点に使われた決定表（validate*.py が読んでいるもの）
    gens = [(p, dec12) for pat in ("run12/out_*.json", "run12b/out_*.json",
                                   "gen135/out_*.json", "gen136/out_*.json",
                                   "pair12/out_*.json", "pair12b/out_*.json")
            for p in sorted(glob.glob(pat))]
    gens += [(p, dec13) for p in sorted(glob.glob("gen137/out_*.json"))]

    n_gen = 0
    sys.settrace(tracer)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            C.run(os.path.join(os.environ.get("TMPDIR", "/tmp"), "_triage_dec.json"))
        for path, dec in gens:
            try:
                g = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            cid = g.get("cell_id") or os.path.basename(path)[4:-5]
            d = dec.get(cid) or dec.get(cid[:5])
            if not d:
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                V.score(d, g)
            n_gen += 1
    finally:
        sys.settrace(None)
    return executed, entered, n_gen


def undelivered_fields():
    """届いていない申告欄 ―― スキーマに欄が無い／全生成物で一度も非⊥にならない"""
    import audit_model as AM
    from sales_logic import is_bottom
    no_slot = set(AM.reqs_not_in_gen_schema("wf_gen137.js"))
    seen = {}
    files = [p for pat in ("run12/out_*.json", "run12b/out_*.json", "gen135/out_*.json",
                           "gen136/out_*.json", "gen137/out_*.json", "pair12/out_*.json",
                           "pair12b/out_*.json") for p in sorted(glob.glob(pat))]
    for path in files:
        try:
            dd = (json.load(open(path, encoding="utf-8")).get("declared") or {})
        except Exception:
            continue
        for k, v in dd.items():
            if v is not None and not is_bottom(v) and v not in ([], {}):
                seen[k] = seen.get(k, 0) + 1
    return no_slot, seen, len(files)


def main():
    site, fn_of_line, reads = emit_sites()
    executed, entered, n_gen = run_traced()
    no_slot, seen, n_files = undelivered_fields()

    fired, guard_false, never_entered, audit = set(), {}, {}, set()
    for ln, cs in site.items():
        fn = fn_of_line.get(ln, "?")
        for c in cs:
            if ln in executed:
                fired.add(c)
            elif fn in AUDIT_FN:
                audit.add(c)
            elif fn in entered:
                guard_false.setdefault(fn, set()).add(c)
            else:
                never_entered.setdefault(fn, set()).add(c)
    for d in (guard_false, never_entered):
        for k in list(d):
            d[k] -= fired
            if not d[k]:
                del d[k]
    audit -= fired

    total = sum(len(v) for v in site.values())
    total = len({c for cs in site.values() for c in cs})
    print(f"══ 発火していない検査の仕分け   理由コード {total} ／ "
          f"8セル決定表＋生成物 {n_gen} 件を実行トレース\n")
    print(f"  ① 出た                       {len(fired)}")
    print(f"  ② 関数に入ったが条件が偽      {sum(len(v) for v in guard_false.values())}"
          f"  （{len(guard_false)}関数）")
    print(f"  ③ 関数に一度も入らなかった    {sum(len(v) for v in never_entered.values())}"
          f"  （{len(never_entered)}関数）  ＝ (c) 配線されていない")
    print(f"  ④ 監査入口（回帰テストが叩く） {len(audit)}\n")

    if never_entered:
        print("=== (c) 配線されていない ===")
        for f, cs in sorted(never_entered.items()):
            print(f"  {f}  {sorted(cs)}")
    else:
        print("=== (c) 配線されていない: なし ―― 全ての検査関数が実行時に呼ばれている ===")

    # ② を割る：読む申告欄が届いていないものは (b)
    # **一度も届いていない欄**（seen==0）だけを (b) 確定とする。
    # 途中でスキーマから外した欄（seen>0）は、吸収済みかどうかを人が確かめる必要がある。
    hard = {f: sorted((reads.get(f) or set()) & no_slot)
            for f in guard_false}
    hard = {f: bs for f, bs in hard.items() if bs}
    b_sure = {f: [b for b in bs if seen.get(b, 0) == 0] for f, bs in hard.items()}
    b_sure = {f: bs for f, bs in b_sure.items() if bs}
    b_check = {f: [b for b in bs if seen.get(b, 0) > 0] for f, bs in hard.items()}
    b_check = {f: bs for f, bs in b_check.items() if bs}

    print("\n=== (b) 出るはずなのに出ていない ―― 申告欄が一度も届いていない ===")
    if not b_sure:
        print("  なし")
    for f, bs in sorted(b_sure.items()):
        print(f"  {f}")
        for b in bs:
            print(f"      申告欄 {b}：生成スキーマに欄が無く、{n_files}件の生成物で {seen.get(b, 0)}件")
        print(f"      出られないコード: {sorted(guard_false[f])}")

    if b_check:
        print("\n=== (b) 要確認 ―― 途中でスキーマから外した欄（吸収済みかを人が見る）===")
        for f, bs in sorted(b_check.items()):
            for b in bs:
                print(f"  {f}  申告欄 {b}：{n_files}件中 {seen.get(b, 0)}件で届いていた（いまは欄が無い）")

    print("\n=== (a) 出るはずがない（8セルの入力では条件が立たない）===")
    for f, cs in sorted(guard_false.items(), key=lambda x: -len(x[1])):
        if f in b_sure:
            continue
        print(f"  {f:26} {len(cs):3}  {sorted(cs)[:3]}{' …' if len(cs) > 3 else ''}")

    print("\n  ※ (a) は「この8セルでは立たない」であって「立ちえない」ではない。"
          "\n     8セル・粗検16体で測り直すまで、(a) と (b) の境目は動く。")


if __name__ == "__main__":
    main()
