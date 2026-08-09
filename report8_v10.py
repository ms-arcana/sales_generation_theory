# -*- coding: utf-8 -*-
import json, html
from stamp import load as _load, assert_fresh as _assert_fresh   # 第12.5版：刻みの入口

V = json.load(open("verified8_v10.json", encoding="utf-8"))
D = {r["id"]: r for r in _load("decisions8_v10.json")}
OLD = _load("decisions8_v10.json")
e = html.escape
VC = {"通過": "ok", "揺らぐ": "mid", "棄却": "ng"}

ANOM = [
 ("検定1", "ISO_KEYS の構造キー ―― 予測どおり", "16/16 → 0/8", "確認",
  "第6〜8版の全16セルで <code>ISO_CONTEXT_MISSING</code> が発火し、事例の同型性検査は一度も走っていなかった。"
  "$\Pi_3$ から導いた構造キー〈拘束の所在・執行座席の同型・暦の同型〉に置き換えたところ、"
  "<b>8セルすべてで検査が走り、7セルで $D_7$ の根拠が立った。</b>"
  "所轄庁・系列は $\lambda$ の粗い代理変数だったという診断が、そのまま確かめられた。",
  "変更なし。ただし『構造類似が説得に効く』の実証にはならない——"
  "検査が<b>走るようになった</b>ことと、それが<b>説得に効く</b>ことは別である。後者は現場のA/Bでしか取れない。"),
 ("検定2", "A16 の ∀k 修正 ―― 上申は動かなかった", "3座席 0/4 → 0/4", "反証されず・未達",
  "第8版の予測は「中間座席で止まる」で、位置は当たっていた。$\Pi_2$ を $\forall k$ へ広げ、"
  "読む座席すべての様式語と基準を生成器に渡した。<b>それでも座席3つのセルは 0/4 のままだった。</b>"
  "ただし落ち方が変わっている——<b>生成後検査の <code>A16_NOT_CONV_AT_SEAT</code> が 7/8 で発火した。</b>"
  "規則は正しく立っており、<b>生成器がそれを満たせていない</b>。前回は規則がなかった。今回は規則があって守られていない。",
  "機序は <code>R10b_UNIT_ABSENT</code>（5/8）と同じである。"
  "実務性の座席に届かせる唯一の道は<b>②の単位を⑥に残すこと</b>だが、生成器はそれを落としている。"
  "A16 と R10b は同じ失敗の二面だった。<b>提示仕様で二つを一つの指示に束ねる</b>のが次の手当てになる。"),
 ("A21", "$W$ は存在しても、実行を拒むことがある", "2/8", "中心命題（§1.7 の穴）",
  "> パートの時間が浮いても、<b>シフトを実際に削らんかぎり、うちの金は一円も残らんの。"
  "それを削るのは店長で、店長は棚替えの時期に人は減らせんと言う</b>（地場スーパー・社長）"
  "<br>A12 は $W$ の<b>存在</b>を要求し、R13 は〈誰が・いつ・どの費目〉の三つ組を要求した。"
  "どちらも満たしたうえで、<b>その $w$ が実行を拒む</b>という経路が残っている。"
  "$V$（決裁権はないが止められる）とまったく同じ構造が、$W$ にもあった。",
  "$\mathrm{auth}(w,a)$ に加えて $\mathrm{willing}(w,a)$ が要る。"
  "$W$ を座席型（$N_5$）で書けば $\kappa_W$ が立ち、"
  "『店長は棚替えの時期に人は減らせない』は $\kappa_W = $ 実務性 の拒否として書ける。"
  "§3 の帳簿表でいえば、$\mathrm{Acct}$ の $-$ セルに $V$ と同じ拒否の欄が要る。"),
 ("A22", "適用対象は値が正しいかを検査できない", "2/8", "T軸の限界",
  "> <b>認証評価は学校教育法に基づいて国公私立すべての大学に課される。</b>設置形態で区分される制度ではない<br>"
  "> <b>認証評価に点数はない。</b>適合／不適合の判定と、指摘事項の区分があるだけだ（学部長会）"
  "<br>A8 の $\mathrm{scope}$ は「業態＝私立大学」で買い手属性と一致したので通った。"
  "だが<b>制度の実際の適用範囲が違っていた</b>。機械は照合しかできない——値そのものの真偽は見られない。",
  "これは修正できる欠陥ではなく<b>境界の明示</b>である。$\mathrm{scope}$ の値は"
  "「誰がいつどの条文から取ったか」の受領記録（A15 と同型）を要求し、"
  "空欄なら主位置に使えない扱いへ。$\Pi_2$ の〈世界→紙〉の境界がもう一つあった。"),
]

IMPL_NOTE = True

KEEP = [
 ("予測の精度が上がった", "段一致 19→25／36、最長滞在 2→5／8",
  "第8版と<b>同じ買い手・同じ人格</b>で回した対照実験である。最長滞在の一致が初めて過半を超えた。"
  "モデルが「どこで止まるか」を当てられるようになったこと自体は、規則が現実の順序に近づいた証拠である。"
  "ただし上申可否の的中は 8/8 → 6/8 に落ちた。"),
 ("両端から中央へ寄った", "通過7→4／揺らぐ13→18／棄却16→14",
  "棄却が減り、揺らぐが増えた。買い手が「認められない」から「判断を保留する」へ移っている。"
  "上申の数（2/8）は変わらないが、<b>閉じる一言の中身が変わった</b>——"
  "第8版は「これは学部長会に出す紙ではありません」、第10版は「6月30日が本当にうちの期日なのか、事務局に確認させてください」。"
  "門前払いから、確認事項の列挙へ。"),
 ("R9 の語彙分離", "36枚／漏洩 0（5回連続）",
  "医療・物流、食品・建設、その再走行、学校法人・小売、そして第10版。一度も本文に出ていない。"),
 ("⑤は今回も最も強い枚", "4セルで名指しの評価",
  "「ここまで自分から不利を書いた業者を、私はここ数年見ていない」（学部長会）"
  "「五枚目の『内訳が出せるかどうか』、あれだけは頂戴するね」（地場スーパー社長）。"
  "R16（自己適用）と R17（侮辱検査）を入れた⑤は、業界を替えても評価される。"),
 ("生成後検査が7件を捕まえた", "A16 7件・R10b 10件・R13 2件・R12b 1件",
  "第10版で新設した <code>A16_NOT_CONV_AT_SEAT</code> が最多で発火した。"
  "<b>機械は正しく検出しているが、生成器が守れていない。</b>これは規則の欠落ではなく、提示仕様の問題である。"),
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
<title>第10版 検証 ―― 第8版との対照実験</title>
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
<h1>第10版 検証<br>学校法人／小売 ―― 第8版と同じ買い手による対照実験</h1>
<div class="sub">3原理・5記法（SPEC8.md）→ <code>sales_logic.py</code> の決定 → 36枚の生成 →
<b>予測（生成物だけを見る第三の座席）</b>と<b>盲検の買い手8体</b>を並行。2026-08-06 基準日。</div>

<div class="kpi">
<div><b>0／8</b><span>ISO_CONTEXT_MISSING（第8版は 8／8）</span></div>
<div><b>{cnt['通過']}／{cnt['揺らぐ']}／{cnt['棄却']}</b><span>通過／揺らぐ／棄却（全{tot}枚）</span></div>
<div><b>{fwd_hit}／8</b><span>上申可否の予測的中</span></div>
<div><b>{agree}／{tot}</b><span>段ごとの予測一致（前回 16／36）</span></div>
<div><b>0／36</b><span>分析語彙の漏洩（4回連続）</span></div>
</div>

<div class="note"><b>この走行は第8版との対照実験である。</b>
業界・セグメント・商材・買い手人格をすべて第8版と同じにし、<b>モデルだけを替えた</b>。
検定したのは二つ——(1) 構造キーで <code>ISO_CONTEXT_MISSING</code> が消えるか、(2) $\Pi_2$ の $\forall k$ 修正で座席3つのセルの上申が動くか。<br><br>
<b>(1) は予測どおり 8/8 → 0/8。(2) は動かなかった（0/4 のまま）。</b>
ただし落ち方が変わっている——生成後検査の <code>A16_NOT_CONV_AT_SEAT</code> が 7/8 で発火した。
<b>規則は立っていて、生成器が守れていない。</b>前回は規則がなかった。今回はある。<br><br>
そして予測の精度が上がった（段一致 19→25/36、最長滞在 2→5/8）。<span style="display:none">
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

open("report8_v10.html", "w", encoding="utf-8").write(HTML)
print("written", len(HTML))
