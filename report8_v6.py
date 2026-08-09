# -*- coding: utf-8 -*-
import json, html

V = json.load(open("verified8_v6b.json", encoding="utf-8"))
D = {r["id"]: r for r in json.load(open("decisions8_v6b.json", encoding="utf-8"))}
OLD = json.load(open("decisions8_v6.json", encoding="utf-8"))
e = html.escape
VC = {"通過": "ok", "揺らぐ": "mid", "棄却": "ng"}

ANOM = [
 ("A12", "両替できることと、両替されることは別", "8/8", "中心命題（§1.2）",
  "第6版は A5 として <code>expressible(P, κ_n)</code> を⑥に入れた。8枚とも金額と回収年数が載った。"
  "それでも8人全員が同じ問いを残した——<b>「浮いた分を、誰が、いつ、どの費目の支払い減として確定させるのか」</b>。"
  "<blockquote>人日が110人日減っても、要員表から落とすか、残業・応援手当・外注加工費の支払いを実際に止めない限り、"
  "加工単価は1円も動かない。<b>人が浮くだけで支払いは減らない、というのが現場で起きる普通の結末だ</b>（食品・生産技術部）</blockquote>"
  "<blockquote>うちは人を減らさん。減らさん以上、<b>給料は一円も減らんのだ</b>（食品・オーナー社長）</blockquote>"
  "<blockquote>480時間が浮いても、<b>金は一銭も浮かんのや</b>。——で、その浮いた手待ち、誰が返しに来るんや。"
  "工事課長は返さんぞ（建設・下請社長）</blockquote>"
  "<code>expressible</code> は**写像の存在**を言うだけで、写像が**適用される**ことを言っていない。"
  "両替所は表があるだけでは機能しない。<b>窓口に立って両替する行為者</b>が要る。",
  "$\\mathrm{expressible}(q,\\kappa_n) \\Rightarrow \\mathrm{realizable}(q,\\kappa_n)$ は成り立たない。"
  "⑥に <code>realizable</code> の3項組——<b>誰が（座席）／いつ（日付）／何を止めるか（費目）</b>——を必須化する。"
  "さらに重い帰結がある：<b>その行為者が $J$ に入っていないことがある。</b>"
  "「工場長は人を減らさない、調達本部は人の話を聞かない。<b>この間を埋める人間がこの資料のどこにも出てこない</b>」。"
  "$J$ は〈裁定する座席〉の列だが、両替を実行する座席は別にいる。$J$ の定義を拡張する必要がある。"),
 ("A13", "④の周期と⑥の量の型が合っていない", "3/8", "形式系（R10a の対称形）",
  "<blockquote>60〜90人日に派遣単価2万円をかけて120〜180万円。だが④では切替は2027-03-01の一回きりだ。"
  "<b>単発の削減なら回収年数の分母が立たない</b>（食品・生産技術部）</blockquote>"
  "R10a は「④が反復を問題化しているのに⑥が同じ周期で課金する」を止める。"
  "その**対称形**——④が単発なのに⑥が年額系の量（回収年数・年間削減額）を出す——を止めていない。"
  "$\\kappa_n$ の量にはストック（総額・手元資金）とフロー（年額・回収年数）の型があり、"
  "④の周期と型が一致しなければ計算が成立しない。",
  "宣言に <code>s6_kappa_type ∈ {stock, flow}</code> を足し、"
  "$s_4$ が単発（<code>period = 0</code>）なら <code>flow</code> を棄却する。機械判定できる。"),
 ("A14", "日付の辻褄が、資料の中で閉じていない", "2/8", "形式系（R12 の拡張）",
  "<blockquote>40日しかないという話で始まって、<b>着手が11月末になってるでしょう</b>。"
  "ここ、私が常務会で真っ先に指摘される（建設・工務部）</blockquote>"
  "予測エージェントも同じ箇所を最初の破れ目に挙げた——「起案理由に据えた着手期限より後に解が届く。"
  "破れた瞬間に⑤の『内製も応援も期限に間に合わない』<b>がそのまま提案自身に跳ね返る</b>」。"
  "R12 は $\\tau$ の元どうしの順序を見るが、<b>⑥が提示する実施期日</b>を見ていない。",
  "R12 を $\\tau$ 内から**資料全体**へ広げる。$⑥$ の着手日 $\\leq$ $④$ の着手期限日。"
  "⑤で他手段を期限超過で落としたなら、自社の期日が同じ検査を通ることを必須にする"
  "（$M_i$ に課した条件は $P$ にも課される——$\\Gamma_5 \\cup \\{P\\} \\nvdash \\bot$ の具体形）。"),
 ("A15", "「御社データ」の実在が検査されていない", "4/8", "軸（T軸）",
  "<blockquote>11〜18工程、180〜260人日が『御社データからの概算』とあるが、"
  "<b>うちの部からデータを出した記憶がない。誰が、いつ、どのデータを渡したのか</b>（食品・生産技術部）</blockquote>"
  "<blockquote>その「御社データ」は誰から受け取ったのか、次に来るときに教えてくれ（建設・工務部）</blockquote>"
  "<code>q_source</code> は $\\mathrm{acquire}$ の月数を足すためだけに使われており、"
  "<b>そのデータを実際に受け取ったか</b>を検査していない。"
  "しかも②で「その粒度のデータは存在しない」と書いた資料が、④で同じ粒度の数を出した例もあった"
  "（出所の循環）。買い手は検算ではなく**読解だけ**でこれを破る。",
  "$q$ の出所に**受領記録**（誰から・いつ・どの抽出条件で）を必須フィールドにする。"
  "空欄なら「買い手データ」を名乗れず、公開統計か売り手データとして扱う。"),
]

KEEP = [
 ("A5 は効いた。ただし一段足りなかった", "8/8 が⑥に金額を載せた",
  "第5版では8人全員が「金額に直して持ってこい」で終わった。第6版では8枚すべてに金額・回収年数・手元資金の増減が載り、"
  "<b>誰もその一言を言わなかった</b>。代わりに全員が一段深い問いを出した（A12）。"
  "枠が正しく、一段ずつしか進めない、ということである。"),
 ("A7 / A8 / R7 は生成前に止めた", "8/8 → 2/8",
  "第5版の走行で使った入力をそのまま第6版コアに当てると、生成可は 8/8 から <b>2/8</b> に落ちた。"
  "買い手が一行で落とした箇所が、文言を書く前に止まる。"
  "「うちに親会社はないよ」→ 拘束者が実在しない。「当社が元請だ」→ 拘束の向きが逆。"
  "「六年前に越えてる」→ 適用開始が過去。「どの元請の話だ」→ 拘束者が一意でない。"),
 ("A11 は半分効いた", "③の名づけは1件も語として拒否されなかった",
  "第5版では「その言葉はうちの会議じゃ通らん」「様式に書いた瞬間に止まる」と2セルで語が落ちた。"
  "第6版では③に既存科目名との対応を併記させ、<b>語として運べないという指摘は消えた</b>。"
  "ただし対応の**中身**が3セルで棄却された（「切替占有＝単価の等号は雑だ」）。"
  "語は運べるようになったが、翻訳が正しいかは別の検査が要る——これが A12 に繋がる。"),
 ("提示語彙の分離（R9）", "36枚／漏洩 0（3回連続）",
  "業界・商材・仕様をすべて替えても、分析語彙は一度も本文に出ていない。"),
 ("予測を第三者に出させた", "段一致 16/36 → 20/36、上申可否 7/8 的中",
  "第5版で生成器に自己予測させたときは系統的に楽観へ寄った。"
  "生成物だけを見るレビュー座席に出させたところ、<b>破れ目の指摘が買い手の指摘とほぼ一致した</b>。"
  "K1-P1 の日付の辻褄、F2-P2 の「給与は固定費だから支払は動かない」、K2-P1 の回収10〜23年——"
  "いずれも予測が先に当て、買い手が同じ理由で落とした。"),
]


def slides_html(r):
    out = []
    for s in r["sigma"]:
        t, v, w, p = r["copy"].get(s, ""), r["obs"].get(s, ""), r["obs_why"].get(s, ""), r["pred"].get(s, "")
        out.append(f"""<div class="slide"><div class="sh"><span class="stg">{s}</span>
<span class="vb {VC.get(v,'')}">{e(v or '—')}</span><span class="pred">予測 {e(p or '—')}</span></div>
<div class="body">{e(t).replace(chr(10),'<br>')}</div>
<div class="react"><b>買い手：</b>{e(w)}</div></div>""")
    return "\n".join(out)


cells = []
for r in V:
    d = D[r["id"]]
    stops = [f for f in r["post_findings"] if f["level"] == "stop"]
    cells.append(f"""<section class="cell">
<h3>{e(r['id'])}　{e(r['業界'])}／{e(r['セグメント'])}／{e(r['商材'])}</h3>
<table class="meta">
<tr><th>Σ</th><td>{'・'.join(r['sigma'])}</td></tr>
<tr><th>κ_n と、その座席の様式にある語</th><td>{'・'.join(r['kappa_n'])}　／　{e('・'.join(d['form_n']))}</td></tr>
<tr><th>座席</th><td>{e(' → '.join(s['name']+('（読まない）' if not s['reads'] else '') for s in d['seats']))}
{('　拒否権：'+e(d['veto'][0])) if d['veto'] else ''}</td></tr>
<tr><th>使った日付</th><td>{e('／'.join(f"{t[1]}（{t[0]}・{t[2]}）" for t in d['tau_ok']))}</td></tr>
<tr><th>⑤で落とす手段</th><td>{e('／'.join(d['five_mentions']))}</td></tr>
<tr><th>生成後の検査</th><td>{e('／'.join(f['code'] for f in stops) or 'clean')}</td></tr>
<tr><th>予測（別エージェント）</th><td>最長 {e(r['pred_longest'])}／上申 {'する' if r['pred_forward'] else 'しない'}
　<span class="dim">{e((r.get('weakest_point') or '')[:160])}</span></td></tr>
</table>
{slides_html(r)}
<div class="close"><b>閉じる一言</b><p>{e(r['closing_line'])}</p>
<b>資料が答えていない問い</b><p>{e(r['unanswered'])}</p>
<b>上申するか</b><p>{'<span class="ok2">する</span>' if r['would_forward'] else '<span class="ng2">しない</span>'}</p></div>
</section>""")

anom = "\n".join(f"""<div class="an"><h3><span class="tag">{a[0]}</span>{e(a[1])}
<span class="rep">{e(a[2])}</span><span class="scope">{e(a[3])}</span></h3>
<p class="mech">{a[4]}</p><p class="fix"><b>修正</b>　{a[5]}</p></div>""" for a in ANOM)
keep = "\n".join(f"""<div class="an kp"><h3>{e(x[0])}<span class="rep">{e(x[1])}</span></h3>
<p class="mech">{x[2]}</p></div>""" for x in KEEP)

tot = sum(len(r["sigma"]) for r in V)
agree = tot - sum(len(r["diff"]) for r in V)
long_hit = sum(1 for r in V if r["pred_longest"] == r["obs_longest"])
fwd_hit = sum(1 for r in V if r["pred_forward"] == r["would_forward"])
cnt = {"通過": 0, "揺らぐ": 0, "棄却": 0}
for r in V:
    for x in r["obs"].values():
        cnt[x] = cnt.get(x, 0) + 1
old_gen = sum(1 for r in OLD if r["generate"])

rows = "\n".join(
    f"<tr><td>{e(r['id'])}</td><td>{e(r['業界'])}</td><td>{e(r['セグメント'])}</td><td>{e(r['商材'])}</td>"
    f"<td>{'・'.join(r['sigma'])}</td><td>{'・'.join(r['kappa_n'])}</td>"
    f"<td>{e(r['pred_longest'])}</td><td>{e(r['obs_longest'])}</td>"
    f"<td class='{'ok2' if r['would_forward'] else 'ng2'}'>{'する' if r['would_forward'] else 'しない'}</td></tr>"
    for r in V)

HTML = f"""<!doctype html><html lang="ja"><meta charset="utf-8">
<title>第6版 検証 ―― 食品メーカー／建設・設備工事 8セル 再走行</title>
<style>
:root{{--ink:#1a1a1a;--dim:#6b6b6b;--line:#e0ddd6;--bg:#faf9f6;--ok:#2f6f4e;--mid:#8a6d1f;--ng:#993326;--acc:#2a4d69}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:"Hiragino Mincho ProN","Yu Mincho",serif;line-height:1.85;font-size:15.5px}}
.wrap{{max-width:960px;margin:0 auto;padding:48px 24px 96px}}
h1{{font-size:26px;line-height:1.5;margin:0 0 6px}}
.sub{{color:var(--dim);font-size:13.5px;margin-bottom:36px}}
h2{{font-size:19px;margin:56px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--ink)}}
h3{{font-size:16px;margin:26px 0 8px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0}}
th,td{{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#f2efe8;font-weight:600;white-space:nowrap}}
.meta th{{width:200px}}
.dim{{color:var(--dim);font-size:12px}}
.kpi{{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0 8px}}
.kpi div{{flex:1;min-width:150px;border:1px solid var(--line);background:#fff;padding:14px 16px}}
.kpi b{{display:block;font-size:26px;line-height:1.2;font-family:Georgia,serif}}
.kpi span{{font-size:12.5px;color:var(--dim)}}
.cell{{border:1px solid var(--line);background:#fff;padding:22px 24px;margin:26px 0}}
.slide{{border-left:3px solid var(--line);padding:8px 0 8px 16px;margin:16px 0}}
.sh{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.stg{{font-size:19px;font-weight:700}}
.vb{{font-size:12px;padding:2px 9px;border-radius:2px;color:#fff;background:var(--dim)}}
.vb.ok{{background:var(--ok)}}.vb.mid{{background:var(--mid)}}.vb.ng{{background:var(--ng)}}
.pred{{font-size:12px;color:var(--dim)}}
.body{{font-size:14.5px}}
.react{{margin-top:8px;font-size:13.5px;background:#f7f5f0;padding:10px 12px}}
.close{{margin-top:20px;border-top:1px dashed var(--line);padding-top:14px;font-size:13.5px}}
.close p{{margin:4px 0 12px;white-space:pre-wrap}}
.ng2{{color:var(--ng);font-weight:700}}.ok2{{color:var(--ok);font-weight:700}}
.an{{border:1px solid var(--line);border-left:4px solid var(--ng);background:#fff;padding:16px 20px;margin:16px 0}}
.an.kp{{border-left-color:var(--ok)}}
.tag{{display:inline-block;background:var(--ng);color:#fff;font-size:12px;padding:1px 8px;margin-right:8px;font-family:Georgia,serif}}
.rep{{float:right;font-size:12px;color:var(--dim);font-weight:400}}
.scope{{float:right;font-size:11.5px;color:#fff;background:var(--acc);padding:1px 8px;margin-right:10px}}
.mech{{font-size:14px;margin:8px 0}}
.fix{{font-size:14px;background:#f4f6f8;padding:10px 12px;margin:10px 0 0}}
blockquote{{margin:10px 0;padding:8px 14px;border-left:3px solid var(--line);background:#f7f5f0;font-size:13.5px}}
code{{font-family:"SF Mono",Menlo,monospace;font-size:12.5px;background:#f0ede6;padding:1px 4px}}
.note{{font-size:13.5px;background:#fff;border:1px solid var(--line);padding:14px 18px;margin:14px 0}}
</style>
<div class="wrap">
<h1>第6版 検証<br>食品メーカー／建設・設備工事 ―― 同じ8セルの再走行</h1>
<div class="sub">中心命題・軸・形式系（SPEC.md 第6版）→ <code>sales_logic.py</code> の決定 → 36枚の生成 →
<b>予測（生成物だけを見る第三の座席）</b>と<b>盲検の買い手8体</b>を並行。2026-08-06 基準日。</div>

<div class="kpi">
<div><b>3／8</b><span>最終裁定点へ上申された（前回 0／8）</span></div>
<div><b>{cnt['通過']}／{cnt['揺らぐ']}／{cnt['棄却']}</b><span>通過／揺らぐ／棄却（全{tot}枚）</span></div>
<div><b>{old_gen}／8</b><span>旧入力を第6版コアに当てたときの生成可</span></div>
<div><b>{agree}／{tot}</b><span>段ごとの予測一致（前回 16／36）</span></div>
<div><b>{fwd_hit}／8</b><span>上申可否の予測的中</span></div>
<div><b>0／36</b><span>分析語彙の漏洩</span></div>
</div>

<div class="note"><b>要点。</b>第6版の修正は効いた。ただし<b>一段だけ</b>である。<br>
前回、8人全員が「金額に直して持ってこい」で終わった。A5 を入れた今回、8枚すべてに金額と回収年数が載り、
その一言は<b>一度も出なかった</b>。3人が上へ回すと言った。<br>
代わりに8人全員が、一段深いところで同じ問いを残した——
<b>「浮いた分を、誰が、いつ、どの費目の支払い減として確定させるのか」。</b>
両替できることと、両替されることは別だった。</div>

<h2>1. 8セルの結果</h2>
<table><tr><th>ID</th><th>業界</th><th>セグメント</th><th>商材</th><th>Σ</th><th>κ_n</th>
<th>予測最長</th><th>観察最長</th><th>上申</th></tr>{rows}</table>

<h2>2. 新しいアノマリー</h2>
{anom}

<h2>3. 第6版で直した部分の効き</h2>
{keep}

<h2>4. 8セルの本文と反応</h2>
{''.join(cells)}
</div></html>"""

open("report8_v6.html", "w", encoding="utf-8").write(HTML)
print("written", len(HTML))
