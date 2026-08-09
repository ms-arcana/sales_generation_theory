# -*- coding: utf-8 -*-
import json, html

V = json.load(open("verified8_v8.json", encoding="utf-8"))
D = {r["id"]: r for r in json.load(open("decisions8_v8.json", encoding="utf-8"))}
OLD = json.load(open("decisions8_v8.json", encoding="utf-8"))
e = html.escape
VC = {"通過": "ok", "揺らぐ": "mid", "棄却": "ng"}

ANOM = [
 ("A16", "中間座席の通関が検査されていない ―― 予測した場所で起きた", "座席3つのセル 4/4", "形式系（R11・A5 を ∀k へ）",
  "第8版 §5 は次のアノマリーの位置を予測していた——<b>「$j_n$ には通ったが中間座席で止まった」型が出る</b>。"
  "そのために E1（私立大学）の座席を 実務性(0) → 説明可能性(3) → 財源(2) と非単調に組み、R1 を単調な対照に置いた。"
  "<blockquote>置かれた名前は私の三語のどれでもなく、理事会の様式へ直接つないだと本文に書いてある。"
  "<b>私の座席を通過させるのではなく迂回する設計だと自分で明かしている。</b>結論として学部長会では扱えない（学部長会）</blockquote>"
  "<blockquote>うちの三語がそちらの「想定反論」の欄に並んでいる時点で、"
  "<b>これは学部長会に出す紙ではありません</b>（同）</blockquote>"
  "<blockquote>三語のそれぞれで「効果は主張しない」と書いてある。<b>私の基準で測れる変化がどこにもない。</b>"
  "これは学部長会の議題ではなく、法人の議題だ（同）</blockquote>"
  "機序ははっきりしている。<b>R11 は新語に $\mathrm{Form}(j_n)$ の語との対応を求め、A5 は⑥に $\kappa_n$ の量を求める。"
  "どちらも終端の座席しか見ていない。</b>生成器は仕様どおりに書き、その結果として中間座席を飛ばした。"
  "第7版の N7（減衰の合成が終端一点に潰れている）が、そのまま事故になった。",
  "$\Pi_2$ は「運搬は<b>各リンクで</b>濾す」と正しく書いている。実装が終端一点だっただけである——"
  "<b>A5 と完全に同型の、4度目の再発。</b>R11・A5 を $\forall k$ へ広げ、"
  "$\mathrm{conv}(x, \kappa_k)$ をすべてのリンクで要求する。③の新語には $j_n$ だけでなく"
  "<b>読む座席すべての様式語</b>との対応を併記させる。"),
 ("A16b", "ただし、予測の「選択条件」は外れた", "非単調 2/8・単調でも発生", "予測の修正",
  "予測は「$\mathrm{rk}(\kappa_k)$ が<b>非単調</b>な $J$ で選択的に起きる」だった。"
  "実際には単調な R1（実務性0→価格1→財源2）でも同じ形で起きている——"
  "<blockquote>最後の一枚、半年で五百万出して半期百万戻る話を、俺は社長の前で読み上げられない。"
  "<b>原価率も粗利率も取引条件も一ミリも動いてない</b>しな（商品本部バイヤー）</blockquote>"
  "<b>位置の予測は当たり、条件の予測は外れた。</b>露出は予測より広い。",
  "選択条件は非単調性ではなく<b>$n \geq 3$</b>（読む中間座席が存在すること）である。"
  "実際、上申は<b>座席3つのセルで 0/4、座席2つのセルで 2/4</b>。"
  "中間座席があるセルは、非単調でも単調でも一つも通らなかった。"),
 ("A17", "④の反復性と⑥の課金周期が同じ", "6/8（機械が検出）", "実装は正しく働いた",
  "$s_4$ の周期＝12か月、$s_6$ の周期＝12か月。R10a が 6セルで停止を出した。"
  "④で「この締切は毎年回ってきます」と書いた資料が、⑥で年次契約を提案している。"
  "第5版で立てた規則が、業界を替えて<b>初めて大量に発火した</b>。"
  "これはアノマリーではなく、<b>規則が想定どおり効いた事例</b>である。",
  "修正不要。ただし生成器は6セルでこれを踏んだので、"
  "<b>提示仕様の側に「④が毎年なら⑥は一度で終わる形にする」を明示する</b>のが実務的。"),
]

IMPL_NOTE = True

KEEP = [
 ("上申可否の予測", "8/8 的中",
  "生成物だけを見るレビュー座席の予測が、買い手の上申可否と<b>完全に一致した</b>（第7版は 7/8）。"
  "第6版で「予測は生成器に出させない」とした判断は、業界を替えても保たれている。"
  "段ごとの一致は 19/36、最長滞在の一致は 2/8 で、こちらは改善していない。"),
 ("提示語彙の分離（R9）", "36枚／漏洩 0（4回連続）",
  "医療・物流、食品・建設、その再走行、そして学校法人・小売。"
  "業界・商材・仕様をすべて替えても、分析語彙は一度も本文に出ていない。"),
 ("R17 侮辱検査", "8/8 で申告ゼロ",
  "第8版で新設した「⑤は買い手が自分で決めてきたことを否定しない」を提示仕様に入れた結果、"
  "8セルすべてで生成器の自己申告が空、買い手からも過去の判断を否定されたという反応は出なかった。"
  "E1-P1 の⑤には<b>「現在の体制も現在の取引先も、当時の条件のもとでの妥当な判断です」</b>と明記された。"
  "ただし n=1 の観察であり、効果と言い切るには対照が要る。"),
 ("R13 の対検査", "1件を検出",
  "E1-P2 で、実行者が持っていない費目を⑥に書いた。第7版の内部検査で直した"
  "〈人と費目の対〉の検査が、実運用で初めて発火した。"),
 ("④の量の検算", "8/8 で買い手が自分で計算した",
  "「420〜660万の外注に対し媒体費を年300〜500万落とすなら、費用の純増は▲80万から＋360万。"
  "<b>収支差額への影響であれば符号が逆</b>で▲360万〜＋80万になる。最良に見える欄に最悪の数字が載っている」——"
  "買い手は例外なく数字を自分の物差しで割り戻した。"),
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
    f"<td>{len(D[r['id']]['seats'])}</td>"
    f"<td>{'→'.join(str(x) for x in (r.get('rank_path') or []))}"
    f"{'' if r.get('monotone') else ' <b>非単調</b>'}</td>"
    f"<td class='{'ok2' if r['would_forward'] else 'ng2'}'>{'する' if r['would_forward'] else 'しない'}</td></tr>"
    for r in V)

HTML = f"""<!doctype html><html lang="ja"><meta charset="utf-8">
<title>第8版 検証 ―― 学校法人／小売（食品スーパー）8セル</title>
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
<h1>第8版 検証<br>学校法人／小売（食品スーパー） ―― 予測を試験する走行</h1>
<div class="sub">3原理・5記法（SPEC8.md）→ <code>sales_logic.py</code> の決定 → 36枚の生成 →
<b>予測（生成物だけを見る第三の座席）</b>と<b>盲検の買い手8体</b>を並行。2026-08-06 基準日。</div>

<div class="kpi">
<div><b>0／4</b><span>座席3つのセルの上申（座席2つは 2／4）</span></div>
<div><b>{cnt['通過']}／{cnt['揺らぐ']}／{cnt['棄却']}</b><span>通過／揺らぐ／棄却（全{tot}枚）</span></div>
<div><b>{fwd_hit}／8</b><span>上申可否の予測的中</span></div>
<div><b>{agree}／{tot}</b><span>段ごとの予測一致（前回 16／36）</span></div>
<div><b>0／36</b><span>分析語彙の漏洩（4回連続）</span></div>
</div>

<div class="note"><b>この走行は仮説検定である。</b>
第8版 §5 は、次のアノマリーが<b>どこに出るか</b>を予測した——「$j_n$ には通ったが中間座席で止まった」型。
そこで E1（私立大学）の座席を 実務性(0) → 説明可能性(3) → 財源(2) と<b>非単調</b>に組み、
R1（小売チェーン本部）を単調な対照に置いた。予測が外れれば §5 は反証される。<br><br>
<b>位置の予測は当たった。条件の予測は外れた。</b>
中間座席で止まる現象は起きたが、非単調なセルだけでなく<b>読む中間座席のあるセルすべて</b>で起きた。
上申は座席3つのセルで <b>0/4</b>、座席2つのセルで 2/4。露出は予測より広い。</div>

<h2>1. 8セルの結果</h2>
<table><tr><th>ID</th><th>業界</th><th>セグメント</th><th>商材</th><th>Σ</th><th>κ_n</th>
<th>座席</th><th>階数</th><th>上申</th></tr>{rows}</table>
<p class="dim">階数は座席の基準を数直線に置いたもの。0＝実務性 1＝価格 2＝財源 3＝説明可能性。
E1 だけが非単調（0→3→2）。上申したのは座席が2つのセルだけだった。</p>

<h2>2. 予測の検定と、新しいアノマリー</h2>
{anom}

<h2>3. 効いた部分</h2>
{keep}

<h2>4. 8セルの本文と反応</h2>
{''.join(cells)}
</div></html>"""

open("report8_v8.html", "w", encoding="utf-8").write(HTML)
print("written", len(HTML))
