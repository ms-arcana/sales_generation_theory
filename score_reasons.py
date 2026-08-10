# -*- coding: utf-8 -*-
"""買い手が⑥を通せなかった理由を数える ―― **二重に数える**（predict_v13_5.md §3）。

  申告  buyers.reasons[].kind      買い手本人に分類させたもの（第13.5版で追加）
  散文  ⑥の why を私が読んで数える  第13版と比べるための、同じやり方

第13版の16体に散文側を当てて**手で検分した**結果、素朴な一致は 11/16 を返したが、
手で読むと 13/16 が日程を理由に挙げていた（取りこぼし2件：
「うちは決めてから動くまで3か月なので…」「今日決めてようやく11月上旬——すでに余裕がない」）。
担体語が〈動くまで〉で否定語が〈余裕がない〉だと落ちる。**約 12% の取りこぼしがある道具である。**
下の CARRIER / NEG はその2件を拾えるまで広げたもので、第13版では **12/16** を返す。
手で読むと **13/16**。残る1件（E2-P1 教務主任「うちは決めてから動くまで3か月なので、
2027-03-14 に見て決めても実際に動くのは 2027-06 月中旬」）は**否定語を一つも使わずに**
日付を並べているだけなので、語の一致では取れない。**基準線は 散文12／手読み13 と書く。**
それでも申告側と食い違ったら、**食い違いそのものを結果として書く**
（第13版の「12/15」も同じだけ疑わしいことになる）。
"""
import re

CARRIER = re.compile(r"(着手|動き出|動くまで|決めてから|決定してから|逆算|リードタイム|決めても|決めて)")
NEG = re.compile(r"(成立しない|不可能|届かない|間に合わない|合っていない|合わない|ずれ|過ぎ|"
                 r"数えられていない|両立しない|物理的に|できない|無理|矛盾|余裕がない|"
                 r"待てない|遅い|遠い|後|前)")


# ── 第13版型の苦情だけを取る（A37 が狙った的そのもの）
# 「着手日が私のリードタイムを無視している／今決めても着手日には届かない」。
# 上の CARRIER/NEG は**日程の苦情一般**を取るので、的が当たったかの判定には使えない。
# 語彙が第13版のものに合わせてあることを承知の上で、**狙った苦情の消滅**だけを測る。
OLD_TYPE = re.compile(
    r"(着手|動き出|動く)[^。]{0,40}(不可能|物理的に|届かない|成立しない|間に合わない)"
    r"|決めても[^。]{0,30}(着手|動き出)[^。]{0,20}(不可能|届かない|できない)"
    r"|(こちら|うち|当方|本会|当社|当校)が動き出すまでの[^。]{0,10}が(数えられていない|入っていない)")


def prose_date_sentences(why: str):
    """⑥の why のうち、日付の順序を理由にしている文を返す"""
    return [s.strip() for s in re.split(r"(?<=。)", why or "")
            if CARRIER.search(s) and NEG.search(s)]


def old_type_hit(rec) -> str:
    """第13版型の苦情（着手日が LT を無視）が出ているならその箇所を返す"""
    s6 = s6_of(rec) if rec.get("reactions") else None
    t = (s6["why"] if s6 else "") + " " + " ".join(
        x.get("text", "") for x in (rec.get("reasons") or []))
    m = OLD_TYPE.search(t)
    return m.group(0) if m else ""


def s6_of(rec):
    for x in rec["reactions"]:
        if "⑥" in x["stage"]:
            return x
    return None


def score(buyers):
    """buyers … [{"id","seat","gen":{...}}]。申告と散文の両方で数える"""
    rows = []
    for r in buyers:
        g = r.get("gen") or {}
        s6 = s6_of(g) if g.get("reactions") else None
        declared = g.get("reasons") or []
        kinds = [x["kind"] for x in declared]
        dec_kinds = [x["kind"] for x in declared if x.get("decisive")]
        prose = prose_date_sentences(s6["why"] if s6 else "")
        rows.append({
            "id": r.get("id"), "seat": r.get("seat"),
            "⑥": s6["verdict"] if s6 else None,
            "申告_日程": "日程" in kinds,
            "申告_日程が決定的": "日程" in dec_kinds,
            "申告_種類": kinds,
            "散文_日程": bool(prose),
            "散文_文": prose[:2],
            "第13版型": old_type_hit(g),
            "why": (s6["why"] if s6 else "")[:400],
        })
    return rows


def summary(rows, label=""):
    n = len(rows)
    a = sum(1 for r in rows if r["申告_日程"])
    ad = sum(1 for r in rows if r["申告_日程が決定的"])
    p = sum(1 for r in rows if r["散文_日程"])
    o = sum(1 for r in rows if r["第13版型"])
    disagree = [(r["id"], r["seat"], r["申告_日程"], r["散文_日程"])
                for r in rows if r["申告_日程"] != r["散文_日程"]]
    print(f"══ 日程を理由に挙げた買い手 {label}（n={n}）")
    print(f"   申告  {a}/{n}（うち決定的 {ad}）")
    print(f"   散文  {p}/{n}")
    print(f"   **第13版型（着手日が LT を無視）だけ  {o}/{n}**  ← A37 が狙った的")
    print(f"   食い違い {len(disagree)} 件 {disagree if disagree else ''}")
    from collections import Counter
    c = Counter(k for r in rows for k in r["申告_種類"])
    if c:
        print("   申告された理由の種類：" + " ／ ".join(f"{k}{v}" for k, v in c.most_common()))
    return {"申告": a, "申告_決定的": ad, "散文": p, "第13版型": o, "食い違い": len(disagree)}
