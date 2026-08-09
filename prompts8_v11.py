# -*- coding: utf-8 -*-
"""第12版の生成プロンプト。アーム3本。

第10版の走行で出た 25 件の stop を、指示文との照合で3つに分けた。

  (A) 指示文に書いていなかった  … 8件（R12b 1／R10a 5／R13 2）
        → 実験ではなく修正。全アーム共通に入れる。
  (B) リストにはあったが枚仕様に無い … 7件（A16）
        → Arm 1 で枚仕様に書き下ろす。
  (C) 枚仕様にあったのに守られなかった … 10件（R10b）
        → Arm 2 で字数を配分し直す。

対照が同一プロンプト内に既にある：
  リスト単独（A16_CHAIN）              → 0/7
  リスト＋枚仕様（R11 ＋③の一文）       → 6/6

アーム
  0：共通修正のみ。⑥の枚仕様・字数・申告欄は第10版のまま（ベースライン）
  1：0 ＋ ⑥の枚仕様に座席ごとの列挙（③と同型）＋ 申告欄 s6_kappa_by_seat
  2：1 ＋ ⑥の字数 700〜900字、末尾に表を許可

使い方：  python3 prompts8_v11.py        → prompts8_v11_arm{0,1,2}.json
"""
import json
import sys
from cells8_v10 import CELLS, SELLERS, TODAY
from prompts8_v10 import (STAGE_SPEC, BAN, DIM_PLAIN, FORM_KIND,
                          SELLER_DESC, PERSONA)

DEC = json.load(open("decisions8_v10.json", encoding="utf-8"))
MSG = json.load(open("messages.json", encoding="utf-8"))

ARMS = (0, 1, 2)


# ────────────────────────────────────────────── ⑥の枚仕様（アームで分岐）

def spec_s6(rec, stages, arm):
    """⑥の書き方。Arm 1 以降は③と同じ形――座席をその場に列挙して、個数を明示する。"""
    kn = "・".join(rec["kappa_n"])
    base = "②" if "②" in stages else "④"
    reading = rec.get("chain") or []
    s = STAGE_SPEC["⑥"]

    if arm == 0:
        # 第10版のまま（誤植「次の三つ」だけ直す）
        s += (f"\n      さらに⑥では次の四つを必ず満たすこと。"
              f"\n      (1) {base}で使った単位を**そのまま残したうえで**、{kn} の側で読める量"
              f"（金額・回収年数・利益の変動など）を**併記**する。単位を置き換えて消して"
              f"はならない。両方を並べる。"
              f"\n      (2) ④で数えた量のうち、本提案が実際に消すのはどの部分かを示す。"
              f"全部でないなら、どこまでかを数で書く。"
              f"\n      (3) 想定反論への回答は、最も保守的な一人が訊く順に置く。"
              f"\n      (4) **浮いた分を、誰が・いつ・どの費目で実際に減らすのか**を書く。"
              f"上の『費目を実際に減らせる座席』から選び、その人が減らせる費目だけを挙げる。"
              f"**減らす費目が複数あるなら、〈誰が・いつ・どの費目〉を費目の数だけ別々に書く。**")
        return s

    # ── Arm 1 / 2 ────────────────────────────────────────────
    names = "・".join(n for n, _k, _f, _o in reading) or rec["j_star"]
    s += (f"\n      さらに⑥では次の五つを必ず満たすこと。"
          f"\n      (1) **量は、資料を読む座席の数だけ並べる。**"
          f"この資料を読むのは {names} の{len(reading) or 1}座席。")
    for nm, kp, fm, og in reading:
        words = "／".join(fm) if fm else "・".join(kp)
        mark = "（制度が置いた座席。飛ばせない）" if og == "制度" else ""
        s += (f"\n          ・**{nm}** に向けて：{words} のいずれかの語で読める量を一つ{mark}")
    s += ("\n          座席名を明記して並べること。"
          "終端の座席の量だけを置くと、手前の座席で止まる。"
          "**一つの量で全部の座席を賄おうとしない。**")
    if "②" in stages:
        s += (f"\n      (2) {base}で使った単位は、**(1) の並びの中にそのまま残す**。"
              f"別の単位へ置き換えて消してはならない。"
              f"（{base}の単位で読む座席が上の一覧に居るなら、その行がそれに当たる）")
    else:
        s += (f"\n      (2) {base}で挙げた量は、(1) の並びの中にそのまま残す。置き換えて消さない。")
    s += ("\n      (3) ④で数えた量のうち、本提案が実際に消すのはどの部分かを示す。"
          "全部でないなら、どこまでかを数で書く。"
          "\n      (4) **浮いた分を、誰が・いつ・どの費目で実際に減らすのか**を書く。"
          "上の『費目を実際に減らせる座席』から選び、その人が減らせる費目だけを挙げる。"
          "**減らす費目が複数あるなら、〈誰が・いつ・どの費目〉を費目の数だけ別々に書く。**"
          "\n      (5) 想定反論への回答は、最も保守的な一人が訊く順に置く。")
    return s


# ────────────────────────────────────────────── 出力欄（アームで分岐）

def spec_out(rec, arm):
    reading = rec.get("chain") or []
    if arm <= 1:
        head = "【出力】各枚 200〜450字の日本語本文。"
    else:
        head = ("【出力】①〜⑤ は各 200〜450字。**⑥ は 700〜900字。**"
                "⑥ は他の枚より要求が多いので、枠を広く取ってある。"
                "\n  ⑥の末尾に限り、〈座席ごとの量〉〈消す部分の対応〉〈誰がいつどの費目を減らすか〉の"
                "三点を**表の形で置いてよい**（この表は下の『見出し語だけの箇条書きにしない』の対象外）。"
                "本文だけで書ききれるならそれでもよい。\n  ")
    tail = ("見出し語だけの箇条書きにしない。そのままスライドに貼れる文章にすること。"
            "加えて declared の各項目を正直に申告すること（書いていない段の項目は null にする）。"
            "\n  ・**s6_realize** は〈誰が・いつ・どの費目〉の**組の配列**で申告する。"
            "費目が2つなら組も2つ。一つの文字列に連結してはならない。")
    if arm >= 1:
        seats = "／".join(n for n, _k, _f, _o in reading) or rec["j_star"]
        tail += (f"\n  ・**s6_kappa_by_seat** は〈座席名・基準〉の**組の配列**で申告する。"
                 f"座席は {seats} の**すべて**を挙げる。基準はその座席に向けて⑥に置いた量の側"
                 f"（実務性／価格／財源／説明可能性／政治的可視性 のいずれか）。")
    tail += ("\n  **買い手がどう反応するかの予測は書かない。**"
             "self_report には、仕様のうち書ききれなかった点と、規定がなくて困った点だけを書く。")
    return head + tail


# ────────────────────────────────────────────── 本体

def build(rec, cell, arm):
    stages = rec["sigma"]
    lines = []
    lines.append(f"あなたは営業資料の作成者。以下の条件で、スライド {len(stages)} 枚の本文を書く。\n")
    lines.append(f"【買い手】{rec['業界']} ／ {rec['セグメント']}")
    lines.append("【読み手と裁定者】")
    for s in rec["seats"]:
        lines.append(f"  ・{s['name']}（見るもの：{'・'.join(s['kappa'])} ／ 通し方：{s['chi']} ／ "
                     f"{s['gamma']} ／ {'資料を読む' if s['reads'] else '資料は読まない'}）")
    if rec["veto"]:
        lines.append(f"  ・{rec['veto'][0]}（決裁権はないが、この人物が拒めば事業は止まる）")
    last = rec["seats"][-1]
    lines.append(f"  ※ 最後に決めるのは【{last['name']}】。この人物は {'・'.join(rec['kappa_n'])} でしか物を見ない。")
    lines.append(f"  ※ この座席の文書様式に載っている語は次のものだけ：{'／'.join(rec['form_n']) or '（未登録）'}")
    lines.append("  ※ **資料は途中の座席を全部通る。**終端だけに合わせて書くと、手前で止まる。")
    for nm, kp, fm, og in rec.get("chain", []):
        mark = "（制度が置いた座席。飛ばせない）" if og == "制度" else ""
        lines.append(f"     ・{nm} は {'・'.join(kp)} でしか読まない／様式の語：{'／'.join(fm) or '（未登録）'}{mark}")
    lines.append(f"  ※ 資料を最後まで読む人のうち、最も遠い座席は【{rec['j_star']}】。\n")

    if rec["gamma_own"]:
        lines.append("【この資料より前に、すでに買い手と合意できていること】")
        for s, v in rec["gamma_own"].items():
            if s not in stages:
                lines.append(f"  ・{s}に当たる内容：{v}")
        lines.append("  ※ 上は資料の外で成立している。**資料の中で言及してはならない**"
                     "（読み手には見えない枚を指すことになる）。前提として使うだけ。\n")

    if rec.get("executors"):
        lines.append("【費目を実際に減らせる座席（この人たちが動かなければ、金額は紙の上だけの話になる）】")
        for name, accts in rec["executors"]:
            lines.append(f"  ・{name}（減らせる費目：{'・'.join(accts)}）")
        lines.append("  ※ 費目は上の一覧の語をそのまま使う。**二つ以上を一つの語に繋げない**"
                     "（「媒体費・広報外注費」のような書き方は、そういう費目が無いという意味になる）。")
        lines.append("")
    lines.append("【買い手が自分で決めてきたこと（これを否定してはならない）】")
    lines.append("  ・現在の体制も、いまの取引先も、買い手自身が選んだ結果である。")
    lines.append("    『その選択は誤りだった』と読める書き方をすると、買い手は自分の判断を")
    lines.append("    取り消さなければ提案を受け入れられなくなる。⑤では手段の**条件**を書き、")
    lines.append("    買い手の**過去の決定**には触れないこと。")
    lines.append("")
    lines.append(SELLER_DESC[cell["seller"]])
    lines.append("")
    lines.append(f"【今日の日付】{TODAY.isoformat()}")
    lines.append("【使える日付（これ以外の日付を『今やる理由』にしてはならない）】")
    for form, d, src, known in rec["tau_ok"]:
        t = next(t for t in cell["nu"].tau if t.form == form and t.d.isoformat() == d)
        extra = f"／逃した場合は次まで {t.wait_months} か月待つ" if t.wait_months else ""
        lines.append(f"  ・{d}（{FORM_KIND[form]}／出所：{src}／買い手にとって{known}{extra}）")
        sc = []
        if t.scope and t.scope.keys:
            sc.append("／".join(f"{k}が{v}" for k, v in t.scope.keys))
        if t.binders:
            sc.append(f"この日を握っているのは {t.binders[0]}")
        lines.append(f"      この日付が効く相手：{'、'.join(sc) if sc else '当該業界の全事業者'}"
                     f"（**この範囲を④に必ず書く**）")
        if t.q:
            rng = f"{t.q_low}〜{t.q_high}" if t.q_low is not None else "（幅は自分で推定して明示）"
            lines.append(f"      添える量：{t.q}  概算 {rng}  出所：{t.q_source}")
            if t.q_recast:
                lines.append(f"      ※ この量は {'・'.join(rec['kappa_n'])} では直接読めない。"
                             f"同じ枚の中で、誰の何が {'・'.join(rec['kappa_n'])} の側で動くのかを書き添えること。")
    # 伝達漏れの修正（全アーム共通）：着手期限は決定表にあり、生成後にも検査しているのに、
    # 第10版までは指示文に一度も出していなかった（R12b が 1 件、教えていない期限で落ちた）。
    if rec.get("start_deadline"):
        lines.append(f"  ※ **上の日付から逆算した着手期限：{rec['start_deadline']}。**"
                     f"⑥に書く着手日は、この日以前にすること。"
                     f"（リードタイムを引いた日。これを過ぎると、上の日付には間に合わない）")
    lines.append("")
    lines.append("【⑤で扱う打ち手（これ以外は⑤に出さない）】")
    for name, mtype, dims, binder in rec["delta"]:
        if name not in rec["five_mentions"]:
            continue
        bmap = binder if isinstance(binder, dict) else {}
        txt = " ／ ".join(DIM_PLAIN[d].replace("{binder}", bmap.get(d, ""))
                         for d in dims if d in DIM_PLAIN)
        lines.append(f"  ・「{name}」 → {txt}")
    if rec["d7_basis"]:
        lines.append("【⑥で、同種の他社ではなく自社が残る根拠として使えるもの】")
        lines.append("  ・" + " ／ ".join(DIM_PLAIN.get(d, d) for d in rec["d7_basis"]))
    lines.append("")
    lines.append("【必ず入れる要素】")
    for b in rec["blocks"]:
        lines.append(f"  ・{MSG['blocks'][b]}")
    lines.append("【書き方の制約】")
    for r in rec["rules"]:
        k = r.split(":")[0]
        if k in MSG["rules"]:
            lines.append(f"  ・{MSG['rules'][k]}")
    lines.append("")
    lines.append(f"【作る枚】{'・'.join(stages)}（この段だけ。他の段は作らない）")
    for s in stages:
        spec = STAGE_SPEC[s]
        if s == "⑥":
            spec = spec_s6(rec, stages, arm)
        if s == "③":
            spec += ("\n      併記する既存語は、**資料を読むすべての座席の様式語から一つずつ**選ぶ。"
                     "終端の語だけでは途中の座席で止まる。")
        lines.append(f"  {s}：{spec}")
    lines.append("")
    lines.append("【本文に出してはならない語】" + "、".join(BAN))
    lines.append("  これらは資料を設計するための言葉であって、買い手に見せる言葉ではない。"
                 "現場の言葉に置き換えて書くこと。")
    lines.append("")
    lines.append(spec_out(rec, arm))
    return "\n".join(lines)


def main():
    for arm in ARMS:
        out = []
        for rec, cell in zip(DEC, CELLS):
            assert rec["id"] == cell["id"]
            out.append({"id": rec["id"], "sigma": rec["sigma"], "arm": arm,
                        "persona": PERSONA[rec["id"][:2]],
                        "prompt": build(rec, cell, arm)})
        fn = f"prompts8_v11_arm{arm}.json"
        json.dump(out, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n6 = [len(o["prompt"]) for o in out]
        print(f"arm{arm}: {len(out)} prompts / avg {sum(n6)//len(n6)} chars / "
              f"min {min(n6)} max {max(n6)}  → {fn}")


if __name__ == "__main__":
    main()
