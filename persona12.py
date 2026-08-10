# -*- coding: utf-8 -*-
"""第13版 ―― 買い手ペルソナの再構築。

第12.9版まで、盲検買い手に渡していたのは **業態・規模・自分の κ・様式の語・上位座席の κ・γ・拒否権者**
だけだった。モデルが持っている買い手側の事実の大半を渡していなかった。

そして、**過去にアノマリーを生んだ買い手の一言は、ほぼ全部「渡していない属性」から出ている。**

    A7  「うちに親会社はないよ」        ← τ の binders
    A19 「卸の販促支援はうちにとってタダだ」← M の cost_to_buyer
    A21 執行座席が実行を拒む            ← W の willing
    A22 その日付は自分の区分に効かない   ← Scope

つまり買い手エージェントは、**渡されていない属性を自分で補って**発言していた。
補った中身は LLM の事前分布から来ている（→ 引き継ぎ書 §5 の★留保）。

とくに R17（侮辱検査）は、買い手が資料の外で自分で積んだ承認 Γ^own を⑤が取り消せと
要求していないかを見る規則なのに、**その承認をペルソナに書いていなかった**。
検査だけが片側で走っていた。

## 何を渡し、何を渡さないか

    渡す    買い手が「持っているもの」   Γ^own ／ τ の適用範囲・拘束者・窓 ／ M と cost ／ W と willing
                                        ／ 自分の κ・χ・γ・様式の語 ／ 上下の座席とその κ ／ 拒否権者
    渡さない 資料が「言うべきこと」      Σ ／ 必須要素 ／ 規則 ／ 診断コード ／ 形式系の語彙（BAN）
                                        ／ 生成器の自己申告 ／ 予測器の予測

**渡すのは買い手の世界であって、食い違いそのものではない。**
「その日付はあなたを縛らない」とは書かない。「あなたを縛っているのは誰か」だけを書く。
食い違いを見つけるのは買い手の仕事である。

  python3 persona12.py     → persona12.json（8セル×読む座席ぶん）
"""
import json
import pathlib

import cells8_v10 as C
from stamp import dump_stamped, load as _load

ORG = {"E1": "私立大学（学生5,200名・関西）", "E2": "専修学校（学生620名）",
       "R1": "食品スーパーチェーン（32店舗）", "R2": "地場の食品スーパー（3店舗・従業員パート込み90名）"}
KNOWN_JA = {"既知": "あなたは以前からこの日を知っている", "未知": "あなたはこの日をまだ意識していなかった"}


def persona(rec, cell, seat_name):
    n = cell["nu"]
    seat = next(s for s in n.J if s.name == seat_name)
    seg = rec["id"][:2]
    L = []
    L.append(f"あなたは{ORG[seg]}の【{seat.name}】。")
    L.append(f"・自分の判断基準は〈{seat.chi}〉。{'・'.join(sorted(seat.kappa))}でしか物を見ない。")
    if seat.form:
        L.append(f"・あなたの文書様式に載っている語は次のものだけ：{'／'.join(sorted(seat.form))}。"
                 f"**この語で書かれていないものは、あなたの会議・稟議には載らない。**")
    L.append("・あなたの決め方は" + ("合議。最も保守的な一人が止めれば止まる。" if seat.gamma == "合議"
                                else "単独。あなたが決めればそれで決まる。"))

    readers = [s for s in n.J if s.reads]
    idx = [s.name for s in readers].index(seat.name)
    if idx + 1 < len(readers):
        nxt = readers[idx + 1]
        L.append(f"・あなたの次に読むのは【{nxt.name}】（{'・'.join(sorted(nxt.kappa))}で見る）。"
                 f"**あなたが通さなければ、そこには何も行かない。**")
    last = n.J[-1]
    if last.name != seat.name:
        L.append(f"・最後に決めるのは【{last.name}】（{'・'.join(sorted(last.kappa))}で見る）"
                 + ("。この人は資料そのものは読まない。あなたが要点を運ぶ。" if not last.reads else "。"))
    else:
        L.append("・最後に決めるのはあなた自身。")
    for s in readers:
        if s.name != seat.name and s.name != last.name:
            L.append(f"・{s.name}は{'・'.join(sorted(s.kappa))}しか見ていない。")
    if n.V:
        L.append(f"・【{n.V[0].name}】は決裁権を持たないが、この人物が拒めば決めても現場に入らない。")

    # ── 買い手が自分で積んできたもの（R17 侮辱検査の対応物）
    L.append("\n【あなたが自分で決めてきたこと】")
    L.append("・いまの体制も、いまの取引先も、あなた（またはあなたの組織）がそのときの条件で選んだ結果である。")
    L.append(f"・この件の判断基準を〈{seat.chi}〉に置いているのも、あなた自身の決めである。")
    for st, v in (n.gamma_pre or {}).items():
        L.append(f"・{v}")
    L.append("**これらを『誤りだった』と読める書き方をされたら、あなたは自分の過去の判断を"
             "取り消さないと提案を受け入れられなくなる。そこは正直に反応してよい。**")

    # ── 買い手が知っている外の事情
    L.append("\n【あなたの側の事情（資料には書かれていないかもしれない）】")
    for t in n.tau:
        sc = "／".join(f"{k}が{v}" for k, v in (t.scope.keys if t.scope else ())) or "特に区分の限定はない"
        b = "・".join(t.binders) if t.binders else "（誰が握っているかは分からない）"
        L.append(f"・{t.d.isoformat()} という日がある。この日を握っているのは {b}。"
                 f"効くのは {sc} という範囲。{KNOWN_JA.get(t.known, '')}。"
                 + (f"この窓は年に{t.windows}回しかない。" if t.windows and t.windows == 1 else ""))
    L.append(f"・あなたの組織が何かを決めてから実際に動き出すまで、だいたい {n.LT_months} か月かかる。")

    L.append("\n【この件で、あなたが代わりに取りうる手】")
    for m in n.M:
        cost = ("**あなたにとって費用はかからない**" if m.cost_to_buyer == 0
                else "費用はかかる" if m.cost_to_buyer else "費用は分からない")
        who = ("・".join(x[1] for x in m.binders) if m.binders else "")
        L.append(f"・{m.name}（{cost}"
                 + (f"／これを動かす承認は {who} が持っている" if who else "") + "）")

    L.append("\n【実際に費目を動かせる人】")
    for w in n.W:
        st = ("実行に同意している" if w.willing is True
              else "**実行には同意していない**" if w.willing is False
              else "同意しているかは、まだ誰も聞いていない")
        L.append(f"・{w.name}（動かせる費目：{'・'.join(sorted(w.accounts))}／{st}）")

    L.append("\nあなたはこの資料の作り手が何を狙って書いたかを知らない。予測も見ていない。"
             "自分の座席の判断基準だけで、上から順に読むこと。")
    return "\n".join(L)


def main():
    dec = {r["id"]: r for r in _load("decisions8_v12.json")}
    out = []
    for cell in C.CELLS:
        rec = dec[cell["id"]]
        for name, _k, _f, _o in rec["chain"]:
            out.append({"id": cell["id"], "seat": name, "j_star": rec["j_star"],
                        "persona": persona(rec, cell, name)})
    dump_stamped(out, "persona12.json")
    print(f"{len(out)} 人分（8セル × 読む座席）")
    print("\n" + "═" * 70)
    x = next(o for o in out if o["id"] == "E1-P1" and o["seat"] == "学部長会")
    print(f"見本 {x['id']} / {x['seat']}\n")
    print(x["persona"])


if __name__ == "__main__":
    main()
