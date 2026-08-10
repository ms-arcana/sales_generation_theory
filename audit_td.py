# -*- coding: utf-8 -*-
"""A42 の検分 ―― 25業界の記入者が T-D（漸増）に何を書いたか。

第13.5版で、R の 2027-04-01 を D 形で置いたところ、買い手 4/4 が
**年1回の硬い窓**として扱った（「4月1日の窓を一年分越えている」）。
D は γ＝斜（逓増・境界なし）のはずで、境界が無いなら「越える」ことはできない。

同じ型ずれが8セルだけの事故なのか、記入の仕方そのものに入っているのかを見る。
`ind25.json` の `t_forms` から T-D の記入を全部取り出し、
**確定した日付**と**反復の語**を両方持つものを数える。両方あるなら、それは
γ＝斜ではなく〈段・再来〉＝ B/C（機会喪失）である。

機械は真偽を見られない（A22）ので、ここでも判定は出さず**数える**だけにする。

  python3 audit_td.py
"""
import json
import re
from collections import Counter

DATE = re.compile(r"(20\d{2}年\s?\d{1,2}月\s?\d{1,2}日|20\d{2}-\d{2}-\d{2}"
                  r"|令和\d+年\s?\d{1,2}月\s?\d{1,2}日|毎年\s?\d{1,2}月\s?\d{1,2}日)")
RECUR = re.compile(r"(毎年|次段|次の段|年次|年度改定|毎年度|3年ごと|ごとに|順次|段階的|各年)")
MISS = re.compile(r"(逃す|次まで|翌年|1年待|一年待|来年度|次年度)")


def main():
    ind = json.load(open("ind25.json", encoding="utf-8"))["industries"]
    rows, c = [], Counter()
    for x in ind:
        for t in x.get("t_forms", []):
            if not t.get("form", "").startswith("T-D"):
                continue
            txt = " ".join(str(t.get(k, "")) for k in ("concrete_date", "source", "strength"))
            has_d, has_r = bool(DATE.search(txt)), bool(RECUR.search(txt))
            rows.append({"業界": x["industry_id"], "exists": t.get("exists"),
                         "日付": has_d, "反復": has_r,
                         "例": (DATE.search(txt).group(0) if has_d else ""),
                         "語": (RECUR.search(txt).group(0) if has_r else "")})
            c["記入あり"] += 1
            c["exists=True"] += bool(t.get("exists"))
            c["確定した日付を持つ"] += has_d
            c["反復の語を持つ"] += has_r
            c["両方持つ（＝段・再来の疑い）"] += (has_d and has_r)
            c["逃したら待つと書いてある"] += bool(MISS.search(txt))

    print("══ 25業界の T-D（漸増）に何が書かれているか")
    for k in ("記入あり", "exists=True", "確定した日付を持つ", "反復の語を持つ",
              "両方持つ（＝段・再来の疑い）", "逃したら待つと書いてある"):
        print(f"   {k:28s} {c[k]:>3d} / {c['記入あり']}")

    bad = [r for r in rows if r["日付"] and r["反復"]]
    print(f"\n══ 両方を持つ {len(bad)} 件（先頭12件）")
    for r in bad[:12]:
        print(f"   {r['業界'][:28]:30s} 日付「{r['例']}」 反復「{r['語']}」")

    print("\n══ 読み")
    print("   γ＝斜（逓増）は**境界が無い**ことを言う。境界が無いものに")
    print("   〈確定した日付〉と〈次の段〉は付かない。両方付いているなら、それは")
    print("   〈段・再来〉＝ B/C（機会喪失）である。")
    print("   `TD_ALONE` は「D 単独では〈なぜ今か〉を作れない」と正しく言っているが、")
    print("   **記入されている中身が D ではない**のなら、落としているのは D ではない。")
    print("   「T-D 漸増」という欄名そのものが、年次の段を書かせている疑いがある。")
    return rows


if __name__ == "__main__":
    main()
