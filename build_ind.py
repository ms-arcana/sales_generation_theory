# -*- coding: utf-8 -*-
"""25業界 × 2商材（ITソリューション／コンサルティング）―― νの組み立てと決定表。

第12.8版のモデルで、8セル（学校法人・小売）の外へ出る最初の走行。

  nu/I01.json 〜 nu/I25.json   エージェントが記入した ν（買い手側は業界に1つ、τ・M は商材ごと）
      ↓  build_ind.py
  decisions_ind.json           決定表50件（版を刻む）
  prompts_ind.json / ind_run/in_*.json   指示文（1体1ファイル）

商材座標は売り手側の観測なので業界に依存しない（SPEC §12.2）。ここで固定する。

較正について。`CALIBRATED_ON` は6業界しか持っていない。第12.5版の規律
「**未較正の業界では縮退させない**」がここで初めて大規模に効く ――
20業界では Σ が縮まず、較正由来の停止は降格に落ちて `UNCALIBRATED` で申し送られる。
5業界（医療・物流・建設・小売・学校法人）だけを較正済みとして扱い、**業界内の対照**にする。
この対応づけは判断であって導出ではないので、ここに明記しておく。
"""
import copy
import json
import pathlib
from dataclasses import replace
from datetime import date

import cells8_v10 as C
import prompts8_v11 as P
from sales_logic import (Product, Seller, Seat, Veto, Executor, TauItem, Mi,
                         Scope, Nu, compile_deal, trial_of, migration_of)
from stamp import dump_stamped, assert_fresh

TODAY = C.TODAY
ARM = 1

# ───────────────────────────── 商材座標（業界に依存しない。売り手側の観測）
PROD = {
    # ITソリューション：需要予測・要員配置の最適化（SaaS＋初期設定）1,400万〜3,200万
    # 使ってみないと分からない経験財／段階導入は可／手続の切替は重い／効果は6か月後／
    # 成果は測れるが供給者は統制できない（現場が使わなければ出ない）／資産計上・固定費・予算外
    "IT": Product("使えば分かる", "段階分割", "高", 6, "高", "低",
                  "資産計上", "固定", "予算外"),
    # コンサルティング：業務改革（工数の可視化と生産性改善）3〜6か月・280万〜850万
    # 使っても効果の帰属が分からない信用財／フェーズ分割は可／切替コストは中／3か月／
    # 成果の測定可能性も供給者の統制可能性も低い／費用処理・変動費・予算外
    "CONSUL": Product("使っても分からない", "段階分割", "中", 3, "低", "低",
                      "費用処理", "変動", "予算外"),
}

# ───────────────────────────── 売り手（SELLER_DESC と対にする。片方だけ足さない）
S_IT = C.SELLERS["it"]

# prompts8_v10.SELLER_DESC["consult"] に対応する実体。
# 「上位者の承認取得の実績はあるが実測日数を記録していない」＝ upstream_lead_days が None。
# R7 は次元ごとに実数を2つ要求するので、D6c を使うと R7_D6c_HALF で止まる。**これは仕様どおり。**
S_CS = Seller(
    registrations=set(), registration_expiry=None,
    channel_total=0.0, funnel_present=False, funnel_yield=None,
    upstream_approvals=3, upstream_lead_days=None,
    named_cases=[
        {"実名": "□□食品株式会社", "拘束の所在": "上位者",
         "執行座席の同型": "本部が販促費と人時を分けて持つ", "暦の同型": "卸との定番改訂商談で締まる"},
        {"実名": "◇◇工業株式会社", "拘束の所在": "買い手の資源",
         "執行座席の同型": "経営者が人件費を単独で動かす", "暦の同型": "自分で決める"},
    ],
    liability_scope=False, price_disclosure=True,
)
SELLERS = {"IT": S_IT, "CONSUL": S_CS}
SELLER_KEY = {"IT": "it", "CONSUL": "consult"}
SHOHIN = {"IT": "ITソリューション", "CONSUL": "コンサルティング"}

# ───────────────────────────── 較正済みとして扱う業界（判断。導出ではない）
CALIB_MAP = {
    "I04": "小売", "I10": "物流", "I12": "建設", "I16": "医療", "I23": "学校法人",
}


def _scope(s):
    if not s:
        return None
    return Scope(keys=tuple((k, v) for k, v in (s.get("keys") or [])),
                 applied_from=date.fromisoformat(s["applied_from"]) if s.get("applied_from") else None,
                 source=s.get("source"))


def _tau(t):
    return TauItem(
        form=t["form"], d=date.fromisoformat(t["d"]), src=t["src"], known=t["known"],
        q=t.get("q"), q_kappa=t.get("q_kappa"), q_recast=bool(t.get("q_recast")),
        q_source=t.get("q_source", "公開統計"),
        q_low=t.get("q_low"), q_high=t.get("q_high"),
        confirmed=t.get("confirmed", True), wait_months=t.get("wait_months"),
        scope=_scope(t.get("scope")), binders=tuple(t.get("binders") or []),
        q_receipt=t.get("q_receipt"), decision=t.get("decision"),
        windows=int(t.get("windows", 1)))


def _mi(m):
    return Mi(name=m["name"], mtype=m["mtype"],
              dims=frozenset(m.get("dims") or []), order=tuple(m.get("order") or []),
              binder=m.get("binder"),
              binders=tuple((d, w) for d, w in (m.get("binders") or [])),
              cost_to_buyer=m.get("cost_to_buyer"))


def _seat(s):
    return Seat(name=s["name"], kappa=frozenset(s.get("kappa") or []), chi=s.get("chi", ""),
                gamma=s.get("gamma", "単独"), omega=s.get("omega", "社内"),
                reads=bool(s.get("reads", True)), form=frozenset(s.get("form") or []),
                origin=s.get("origin", "個人"))


def _c_move(p: Product) -> str:
    """C_move は ν と同じ二重の真実（第12.5版）。座標から見て食い違わない値を置く。

    trial_of / migration_of は座標から出るので、旧軸がそれと一致するように選ぶ。
    一致しなければ `C_MOVE_AXIS_CONFLICT` が立つ ―― それは入力の不備であって発見ではない。
    """
    tmp = Nu(A=p.nu, I="役務", S1="100万〜1000万", S2="年次以下", S3=False,
             C_move="", J=[Seat("x", frozenset({"実務性"}), "")], prod=p)
    want_t, want_m = trial_of(tmp), migration_of(tmp)
    for cand in ("大仕事", "すぐ試せる", "どちらでもない"):
        old_t = (p.nu == "使えば分かる" or cand == "すぐ試せる")
        old_m = (cand == "大仕事")
        if old_t == want_t and old_m == want_m:
            return cand
    return "どちらでもない"


def build_nu(spec: dict, pkey: str) -> Nu:
    b = spec["buyer"]
    p = PROD[pkey]
    pr = spec["products"][pkey]
    return Nu(
        A=p.nu,                       # G4：商材座標を正とする。旧軸は揃えて置く
        I="役務", S1="100万〜1000万", S2="年次以下", S3=False,
        C_move=_c_move(p),
        J=[_seat(s) for s in b["seats"]],
        prod=p,
        V=[Veto(v) for v in (b.get("veto") or [])],
        W=[Executor(name=w["name"], accounts=frozenset(w.get("accounts") or []),
                    willing=w.get("willing"), kappa=frozenset(w.get("kappa") or []))
           for w in (b.get("executors") or [])],
        procedural=bool(b.get("procedural")), downward=bool(b.get("downward")),
        E_reader=b.get("E_reader", "手段を知らない"),
        E_judge=b.get("E_judge", "手段を知らない"),
        tau=[_tau(t) for t in (pr.get("tau") or [])],
        M=[_mi(m) for m in (pr.get("M") or [])],
        LT_months=int(b.get("LT_months", 6)),
        buyer_context=dict(b.get("context") or {}),
        upstream=frozenset(b.get("upstream") or []),
        downstream=frozenset(b.get("downstream") or []),
        gamma_pre=dict(b.get("gamma_pre") or {}),
    )


def make_cells():
    cells = []
    for f in sorted(pathlib.Path("nu").glob("I*.json")):
        spec = json.load(open(f, encoding="utf-8"))
        code = spec["code"]
        for pkey in ("IT", "CONSUL"):
            cells.append({
                "id": f"{code}-{'IT' if pkey == 'IT' else 'CS'}",
                "業界": spec["industry"], "セグメント": spec["segment"],
                "商材": SHOHIN[pkey], "seller": SELLER_KEY[pkey],
                "_pkey": pkey, "_code": code,
                "industry_key": CALIB_MAP.get(code, spec["industry"]),
                "nu": build_nu(spec, pkey),
                "_notes": spec.get("notes", ""),
            })
    return cells


def rec_of(cell):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    d = compile_deal(cell["nu"], SELLERS[cell["_pkey"]], TODAY, cell["industry_key"])
    rec = {k: cell[k] for k in ("id", "業界", "セグメント", "商材")}
    rec["industry"] = cell["industry_key"]
    rec.update({k: d.get(k) for k in
                ("generate", "sigma", "j_star", "kappa_n", "form_n", "tau_ok", "delta",
                 "five_mentions", "d7_basis", "blocks", "rules", "executors",
                 "start_deadline", "chain", "talk_guide", "calibrated", "unwilling",
                 "out_of_scope")})
    rec["findings"] = [{"code": f.code, "level": f.level, "ref": f.ref,
                        "msg": msgs["findings"].get(f.code, f.code)} for f in d["findings"]]
    rec["needs_judgment"] = [{"code": x.code, "ref": x.ref,
                              "msg": msgs["judgments"].get(x.code, x.code)}
                             for x in d["needs_judgment"]]
    rec["seats"] = [{"name": s.name, "kappa": sorted(s.kappa), "chi": s.chi, "gamma": s.gamma,
                     "reads": s.reads, "form": sorted(s.form), "origin": s.origin}
                    for s in cell["nu"].J]
    rec["veto"] = [v.name for v in cell["nu"].V]
    rec["gamma_own"] = cell["nu"].gamma_pre
    rec["prod"] = vars(cell["nu"].prod)
    return rec


def main():
    cells = make_cells()
    recs = []
    for c in cells:
        try:
            recs.append(rec_of(c))
        except Exception as e:               # 入力の不備は隠さず出す
            recs.append({"id": c["id"], "業界": c["業界"], "商材": c["商材"],
                         "_error": f"{type(e).__name__}: {e}"})
    dump_stamped(recs, "decisions_ind.json")
    assert_fresh("decisions_ind.json")

    print(f"══ 決定表 {len(recs)}件")
    err = [r for r in recs if r.get("_error")]
    for r in err:
        print(f"   ✗ {r['id']:8s} {r['_error']}")
    good = [r for r in recs if not r.get("_error")]
    print(f"   組めた {len(good)} / 失敗 {len(err)}")

    print("\n══ 生成可否と停止")
    for r in good:
        st = [f["code"] for f in r["findings"] if f["level"] == "stop"]
        dm = [f["code"] for f in r["findings"] if f["level"] == "demote"]
        print(f"   {r['id']:8s} {'較正' if r['calibrated'] else '未較正'} "
              f"Σ={''.join(r['sigma'])} 座席={len(r['seats'])}(読む{len(r['chain'])}) "
              f"κ_n={','.join(r['kappa_n'])} 生成={'○' if r['generate'] else '×'} "
              f"停止={','.join(st) or '無'}{' 降格=' + ','.join(dm) if dm else ''}")

    gen = [r for r in good if r["generate"]]
    print(f"\n   生成可 {len(gen)} / {len(good)}")

    built = []
    for r, c in zip(recs, cells):
        if r.get("_error") or not r.get("generate"):
            continue
        assert r["id"] == c["id"]
        P.PERSONA.setdefault(r["id"][:2], "")     # PERSONA は買い手役用。生成器には渡らない
        built.append({"id": r["id"], "sigma": r["sigma"], "arm": ARM,
                      "persona": "", "prompt": P.build(r, c, ARM)})
    dump_stamped(built, "prompts_ind.json")
    d = pathlib.Path("ind_run"); d.mkdir(exist_ok=True)
    for x in built:
        dump_stamped(x, str(d / f"in_{x['id']}.json"))
    print(f"   指示文 {len(built)}件 → ind_run/in_*.json")

    print("\n══ 指示文への到達（走行前に確認する ―― 第12版で踏んだ配管の罠）")
    bad = [x["id"] for x in built if not (
        "その事象が再発するか" in x["prompt"] and "要素を落としてはならない" in x["prompt"]
        and "どこから来たのかを本文に添える" in x["prompt"])]
    print(f"   A26/A27/A28 が全件に届いている: {not bad}" + (f"  未達={bad}" if bad else ""))
    ln = [len(x["prompt"]) for x in built]
    if ln:
        print(f"   指示文の長さ {min(ln)}〜{max(ln)}字（平均 {sum(ln)//len(ln)}）")


if __name__ == "__main__":
    main()
