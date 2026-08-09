# -*- coding: utf-8 -*-
"""記入した ν を1件だけ機械にかけて、落ちた理由を日本語で出す。

    python3 check_nu.py I01

記入者はこれを自分で回して、**落ちた理由が入力の不備か、モデルの言い分か**を判断する。
入力の不備なら直す。モデルの言い分なら直さず notes に書く。
"""
import json
import sys

import build_ind as B

HINT = {
    "A8_ALREADY_APPLIED":
        "τ の scope.applied_from に過去の日付を書いた。**既に適用されている制度は applied_from を null にする。**"
        "将来その区分へ適用が始まる日が確定しているときだけ書く欄である。",
    "A8_SCOPE_EMPTY": "τ に scope が無い。keys を buyer.context の同名キーと完全一致で書く。",
    "A8_SCOPE_MISMATCH": "τ の scope.keys の値が buyer.context の値と一字でも違う。写し違い。",
    "A8_SCOPE_UNVERIFIED": "τ の scope.keys に、buyer.context に無い属性名を使った。",
    "A8_BINDER_EMPTY": "src が「契約」または form が Ec の τ には binders が要る。",
    "A8_BINDER_NOT_ABOVE":
        "τ の binders が buyer.upstream に載っていない。**同じ文字列で upstream にも入れる。**",
    "A7_BINDER_UNSET": "D6a / D6c を使う手段には binders:[[\"D6c\",\"拘束者\"]] が要る。",
    "A7_BINDER_ABSENT":
        "手段の拘束者が buyer.upstream にも座席にも拒否権にも居ない。**同じ文字列で upstream に入れる。**",
    "A7_NOT_ABOVE": "手段の拘束者が upstream に無い（座席や拒否権では足りない）。",
    "A7_DIRECTION_REVERSED": "拘束者を downstream に置いた。買い手より上の当事者だけが拘束者になれる。",
    "A20_D5_BINDER_UNSET":
        "D5（資源配分）を使う手段には binders:[[\"D5\",\"座席名\"]] が要る。"
        "**その座席は executors に居る名前**でなければならない。",
    "A20_D5_NOT_IN_W": "D5 の拘束者が executors に居ない。費目を持つ座席を指すこと。",
    "A20_D5_IS_READER":
        "D5 の拘束者が最終裁定点そのもの。枠を決める権限が読み手自身にあるなら、それは拘束ではなく選択である（A20）。"
        "別の執行座席を指すか、その手段から D5 を外す。",
    "ALLOWED_VIOLATION": "mtype に許されていない次元を使った（仕様書 §4.2 の表）。",
    "DELTA_UNSET": "M0 以外の手段に dims が無い。",
    "R4_NO_PRECEDENT":
        "D4（手続）を使ったが、この売り手には前例が無い ―― 登録・認証も、構造キーの一致する事例も無い。"
        "**コンサルの売り手は登録を持たないので、事例の構造キーが一致しない業界では D4 を使えない。**",
    "R7_D6c_HALF":
        "D6c（上位者）を使ったが、売り手は承認の実測日数を持っていない。"
        "**コンサルの売り手は D6c を使えない。**",
    "R7_D6c_MISSING": "D6c を使ったが売り手に上位者承認の実績が無い。",
    "R7_D6a_HALF": "D6a を使ったが登録の有効期限が無い。",
    "R7_D6a_MISSING": "D6a を使ったが売り手に登録・認証が無い。コンサルの売り手は持たない。",
    "R7_D6b_MISSING": "D6b を使ったが売り手はチャネル母数も歩留まりも持たない。**どちらの売り手も使えない。**",
    "R6_NO_TAU": "τ が全部落ちた。上の reject の理由を読むこと。④が書けないので停止する。",
    "A12_NO_EXECUTOR": "executors が空。費目を持つ座席を1つ以上置く。",
    "A12_NO_ACCOUNT": "executors に accounts が無い。実在の費目名を入れる。",
    "R18_INSTITUTIONAL_MULTI_KAPPA": "origin=制度 の座席に κ を2つ以上置いた。制度の座席は1つだけ。",
    "R18_FORM_EMPTY": "origin=制度 で reads=true の座席に form が無い。様式にある語を入れる。",
    "R8_PRE_MISSING": "Σ から落ちた段が gamma_pre に無い。落ちた段は「資料の外で合意済み」と明示する。",
    "NO_ELIMINABLE_MI": "消せる手段が1つも残らなかった。",
    "A2_C_NOT_SINGLETON": "価格で見る座席がある（または比較検討中）のに、自社が残る根拠が売り手に1つも無い。",
    "A1_NOT_EXPRESSIBLE":
        "②の単位が最終裁定点の κ へ届かない。**これはモデルの言い分**である可能性が高い。"
        "座席列が実像どおりなら直さず notes に書く。",
    "A5_NOT_EXPRESSIBLE": "④の量の基準が最終裁定点の κ へ届かない。上と同じ。",
    "OUT_OF_SCOPE_LOW_INVOLVEMENT": "商材が低関与・反復購買と判定され、対象外になった。",
}

MODEL_SAYS = {"A1_NOT_EXPRESSIBLE", "A5_NOT_EXPRESSIBLE", "A20_D5_IS_READER",
              "R4_NO_PRECEDENT", "R7_D6c_HALF", "R7_D6c_MISSING", "R7_D6a_MISSING",
              "R7_D6b_MISSING", "A2_C_NOT_SINGLETON", "OUT_OF_SCOPE_LOW_INVOLVEMENT",
              "R18_INSTITUTIONAL_MULTI_KAPPA"}


def main():
    code = sys.argv[1] if len(sys.argv) > 1 else None
    cells = [c for c in B.make_cells() if code is None or c["_code"] == code]
    if not cells:
        print(f"nu/{code}.json が無い"); return
    for c in cells:
        try:
            r = B.rec_of(c)
        except Exception as e:
            print(f"\n═══ {c['id']}  ✗ 組み立てで例外: {type(e).__name__}: {e}")
            continue
        stops = [f for f in r["findings"] if f["level"] == "stop"]
        rejects = [f for f in r["findings"] if f["level"] == "reject"]
        print(f"\n═══ {c['id']} {c['業界']} × {c['商材']}"
              f"  {'較正' if r['calibrated'] else '未較正'}")
        print(f"    Σ={''.join(r['sigma'])} 座席={len(r['seats'])}(読む{len(r['chain'])}) "
              f"κ_n={','.join(r['kappa_n'])} τ生存={len(r['tau_ok'])}/{len(c['nu'].tau)} "
              f"手段={len(r['delta'])} → 生成 {'○' if r['generate'] else '×'}")
        for f in rejects:
            print(f"    棄却 {f['code']:28s} {f['ref']}")
            if f["code"] in HINT:
                print(f"         → {HINT[f['code']]}")
        for f in stops:
            tag = "【モデルの言い分】" if f["code"] in MODEL_SAYS else "【入力の不備】"
            print(f"    停止 {f['code']:28s} {f['ref']}")
            print(f"         {tag} {HINT.get(f['code'], '')}")
        if r["generate"]:
            print("    → 生成できる。")


if __name__ == "__main__":
    main()
