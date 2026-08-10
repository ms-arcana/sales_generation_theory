# -*- coding: utf-8 -*-
"""25業界走行（16業界分）の HTML レポート。

    python3 report_ind.py   → 25業界レポート.html

既存の report8_v*.py と同じ作り（単一ファイル・素の JS・絞り込み UI）。
"""
import collections
import html
import json

from stamp import load

V = {r["id"]: r for r in load("verified_ind.json")}
B = {r["id"]: r for r in load("buyer_ind.json")}
D = {r["id"]: r for r in load("decisions_ind.json") if not r.get("_error")}

PAT = {
    "量の出所が確かめられない": ["根拠", "出所", "どこから", "試算", "算出", "裏付", "裏づけ", "確かめ", "検証でき"],
    "価格・費用の内訳が無い": ["価格", "見積", "単価", "費用", "コスト", "金額", "予算"],
    "④の日付が自社に効かない": ["日付", "期限", "締切", "スケジュール", "逆算", "時期", "いつまで"],
    "自分の語で書かれていない": ["うちの言葉", "様式", "稟議", "規程", "起案", "フォーマット", "用語", "所掌"],
    "⑤が自社の過去の決定の否定": ["既に", "すでに", "うちは", "自前", "内製", "選んだ", "決めた", "検討済"],
    "営業へ回した空欄が資料を殺す": ["空欄", "【", "埋め", "空いて"],
    "幅のある金額が稟議に載らない": ["幅", "倍", "開き", "レンジ"],
    "断り書きが逆に侮辱に読まれる": ["述べていません", "評価ではありません", "当否", "二度"],
    "②の問い返しが決めつけに読まれる": ["数えて", "把握して", "ないのでは", "残っていない", "ではないだろうか"],
}


def tags_of(b):
    t = (b["逐語"] + " " + b["侮辱"] + " " + " ".join(b["当てはまらぬ"])
         + " " + " ".join(b["確認不能"]) + " " + b["聞き返し"])
    return [k for k, ws in PAT.items() if any(w in t for w in ws)]


def e(x):
    return html.escape(str(x))


ROWS = []
for cid in sorted(V):
    v, b, d = V[cid], B.get(cid), D.get(cid, {})
    if not b:
        continue
    ROWS.append({
        "id": cid, "業界": v["業界"], "商材": v["商材"],
        "較正": v["較正"], "座席": v["読む座席"], "ブロック": v["ブロック"],
        "検査": "通過" if v["pass"] else "停止",
        "停止コード": list(v["stops"]),
        "判定": b["判定"], "つまずき": b["つまずき"],
        "逐語": b["逐語"], "侮辱": b["侮辱"],
        "確認不能": b["確認不能"], "当てはまらぬ": b["当てはまらぬ"],
        "聞き返し": b["聞き返し"], "次の行動": b["次の行動"],
        "タグ": tags_of(b),
        "⑥字数": v["⑥字数"], "営業へ": v["to_sales"],
        "seats": [s["name"] for s in (d.get("seats") or [])],
        "j_star": d.get("j_star", ""),
    })

tag_count = collections.Counter(t for r in ROWS for t in r["タグ"])
cross = collections.Counter((r["検査"], r["判定"]) for r in ROWS)
stump = collections.Counter(x for r in ROWS for x in r["つまずき"])
n = len(ROWS)
n_pass = sum(1 for r in ROWS if r["検査"] == "通過")
n_send = sum(1 for r in ROWS if r["判定"] == "差し戻す")

CSS = """
:root{--bg:#0f1115;--pn:#171a21;--ln:#252a34;--fg:#e6e8ec;--mu:#9aa3b2;
--ok:#4ea87a;--warn:#c9a227;--bad:#c0554d;--acc:#5b8dd6;
--fd:'Hiragino Mincho ProN','Yu Mincho',serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.75 -apple-system,'Hiragino Sans','Yu Gothic',sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:48px 24px 96px}
h1{font-family:var(--fd);font-size:30px;line-height:1.5;margin:0 0 6px;font-weight:600}
h2{font-family:var(--fd);font-size:22px;margin:56px 0 16px;padding-bottom:8px;
border-bottom:1px solid var(--ln);font-weight:600}
h3{font-size:16px;margin:28px 0 10px}
.sub{color:var(--mu);font-size:13px;margin-bottom:34px}
.card{background:var(--pn);border:1px solid var(--ln);border-radius:9px;padding:18px 20px;margin-bottom:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:22px 0 8px}
.kpi{background:var(--pn);border:1px solid var(--ln);border-radius:9px;padding:16px 18px}
.kpi b{display:block;font-size:30px;font-family:var(--fd);line-height:1.2}
.kpi span{color:var(--mu);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--ln);vertical-align:top}
th{color:var(--mu);font-weight:500;font-size:12px;white-space:nowrap}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.tag{display:inline-block;padding:2px 8px;border-radius:11px;font-size:11.5px;
border:1px solid var(--ln);margin:2px 4px 2px 0;white-space:nowrap}
.t-ok{color:var(--ok);border-color:#2c5b45}.t-bad{color:var(--bad);border-color:#6b322d}
.t-warn{color:var(--warn);border-color:#6b5a1b}
.bar{height:7px;border-radius:4px;background:#20242c;overflow:hidden;margin-top:6px}
.bar i{display:block;height:100%;background:var(--acc)}
.q{border-left:3px solid var(--ln);padding:2px 0 2px 14px;margin:10px 0;color:#cdd3dc;font-size:14px}
.q b{color:var(--fg)}
button{background:var(--pn);color:var(--fg);border:1px solid var(--ln);border-radius:7px;
padding:6px 13px;font-size:13px;cursor:pointer;margin:0 6px 6px 0}
button.on{border-color:var(--acc);color:var(--acc)}
.note{color:var(--mu);font-size:13px}
details{margin:8px 0}summary{cursor:pointer;color:var(--acc);font-size:13.5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
"""

JS = """
const D=DATA;
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
let F={verdict:null,check:null,prod:null,tag:null};
function draw(){
 const rows=D.filter(r=>(!F.verdict||r.判定===F.verdict)&&(!F.check||r.検査===F.check)
   &&(!F.prod||r.商材===F.prod)&&(!F.tag||r.タグ.includes(F.tag)));
 document.getElementById('cnt').textContent=rows.length+' / '+D.length+' 件';
 document.getElementById('cells').innerHTML=rows.map(r=>`
 <div class="card">
  <div style="display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:9px">
   <span class="mono">${esc(r.id)}</span>
   <b style="font-family:var(--fd);font-size:17px">${esc(r.業界)}</b>
   <span class="tag">${esc(r.商材)}</span>
   <span class="tag ${r.検査==='通過'?'t-ok':'t-bad'}">⑦検査 ${esc(r.検査)}</span>
   <span class="tag ${r.判定==='差し戻す'?'t-bad':'t-warn'}">買い手 ${esc(r.判定)}</span>
   <span class="tag">読む座席 ${r.座席}</span>
   <span class="tag">要素 ${r.ブロック}</span>
   <span class="tag">⑥ ${r["⑥字数"]}字</span>
   <span class="tag">営業へ ${r.営業へ}件</span>
  </div>
  ${r.停止コード.length?`<div class="mono" style="color:var(--bad);margin-bottom:8px">停止 ${r.停止コード.map(esc).join(' / ')}</div>`:''}
  <div style="margin-bottom:8px">${r.タグ.map(t=>`<span class="tag t-warn">${esc(t)}</span>`).join('')}</div>
  <div class="note" style="margin-bottom:4px">つまずいた枚：${r.つまずき.map(esc).join('・')||'なし'}</div>
  <div class="q">${esc(r.逐語)}</div>
  <details><summary>失礼だと感じた箇所／確かめようのない数字／当てはまらない記述／次の行動</summary>
   <p class="note"><b>失礼だと感じた箇所</b><br>${esc(r.侮辱)}</p>
   <p class="note"><b>確かめようのない数字（${r.確認不能.length}）</b><br>${r.確認不能.map(esc).join('<br>')}</p>
   <p class="note"><b>自社に当てはまらない記述（${r.当てはまらぬ.length}）</b><br>${r.当てはまらぬ.map(esc).join('<br>')}</p>
   <p class="note"><b>営業に最初に聞き返すこと</b><br>${esc(r.聞き返し)}</p>
   <p class="note"><b>実際に取る行動</b><br>${esc(r.次の行動)}</p>
  </details>
 </div>`).join('');
}
function mk(id,key,vals){
 document.getElementById(id).innerHTML=vals.map(v=>`<button data-k="${key}" data-v="${esc(v)}">${esc(v)}</button>`).join('');
}
document.addEventListener('click',ev=>{
 const b=ev.target.closest('button[data-k]'); if(!b)return;
 const k=b.dataset.k,v=b.dataset.v;
 F[k]=(F[k]===v)?null:v;
 document.querySelectorAll('button[data-k]').forEach(x=>
   x.classList.toggle('on',F[x.dataset.k]===x.dataset.v));
 draw();
});
mk('f1','verdict',['差し戻す','条件付きで通す']);
mk('f2','check',['通過','停止']);
mk('f3','prod',[...new Set(D.map(r=>r.商材))]);
mk('f4','tag',TAGS);
draw();
"""


def bar(v, mx):
    return f'<div class="bar"><i style="width:{100*v/max(mx,1):.0f}%"></i></div>'


tag_rows = "".join(
    f'<tr><td>{e(k)}</td><td class="mono">{v} / {n}</td><td style="width:44%">{bar(v, n)}</td></tr>'
    for k, v in tag_count.most_common())

cross_rows = "".join(
    f'<tr><th scope="row">⑦{e(a)}</th><td>{cross.get((a,"差し戻す"),0)}</td>'
    f'<td>{cross.get((a,"条件付きで通す"),0)}</td><td>{cross.get((a,"通す"),0)}</td></tr>'
    for a in ("通過", "停止"))

stump_rows = "".join(
    f'<tr><td>{e(k)}</td><td class="mono">{v} / {n}</td><td style="width:50%">{bar(v, n)}</td></tr>'
    for k, v in sorted(stump.items()))

HTML = f"""<!doctype html><html lang="ja"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>25業界走行レポート ―― ITソリューションとコンサルティング</title>
<style>{CSS}</style>
<div class="wrap">
<h1>16業界 × 2商材 ―― 生成と盲検買い手</h1>
<div class="sub">営業資料生成モデル 第12.8版（<span class="mono">sales_logic.py</span> sha256[:12]
<span class="mono">28181539e212</span>）／Arm 1／1体1資料<br>
本レポートは思考実験であり、実顧客の反応の実測ではない。盲検買い手も LLM である
（引き継ぎ書 §5 の★留保）。<b>これは帰納ではない。</b></div>

<div class="kpis">
<div class="kpi"><b>0</b><span>買い手が無条件で通した件数（{n}件中）</span></div>
<div class="kpi"><b>{n_send}</b><span>差し戻し</span></div>
<div class="kpi"><b>{n_pass}</b><span>⑦の検査を通過</span></div>
<div class="kpi"><b>{cross.get(("通過","差し戻す"),0)}</b><span>⑦を通ったのに差し戻された</span></div>
<div class="kpi"><b>{cross.get(("停止","条件付きで通す"),0)}</b><span>⑦で止まったのに買い手は進めた</span></div>
</div>

<h2>1. ⑦の検査は、買い手の判定を予測していない</h2>
<div class="card">
<table><thead><tr><th></th><th>差し戻す</th><th>条件付きで通す</th><th>通す</th></tr></thead>
<tbody>{cross_rows}</tbody></table>
<p class="note" style="margin:14px 0 0">
⑦を通った{n_pass}件のうち{cross.get(("通過","差し戻す"),0)}件が差し戻され、⑦で止まった
{n-n_pass}件のうち{cross.get(("停止","条件付きで通す"),0)}件は買い手が先へ進めた。
<b>仕様を満たすことと、買い手を通ることは別のことである。</b>
引き継ぎ書 §3 が「最重要の未測定項目」と呼んできたものに、初めて数字が付いた。</p>
</div>

<h2>2. つまずいた枚</h2>
<div class="card"><table><tbody>{stump_rows}</tbody></table>
<p class="note" style="margin:14px 0 0">
④と⑥は<b>全件</b>でつまずいている。①〜③はほとんど問題にならない。
モデルが「日本語を書くのは最後の1工程だけ」と設計してきた前半は、買い手の側では争点になっていない。</p></div>

<h2>3. 買い手が実際に言ったこと</h2>
<div class="card"><table><tbody>{tag_rows}</tbody></table>
<p class="note" style="margin:14px 0 0">
<b>買い手には理由の型を一切示していない。</b>実務者が自然に答える形（確かめようのない数字／
自社に当てはまらない記述／失礼だと感じた箇所／次に取る行動）で聞き、型付けは採点側で行った。<br>
走行前の予測（<span class="mono">predict_ind.md</span> §6）は
「差し戻しの理由は〈④の日付〉と〈⑤の否定〉に集中する」だった。<b>外れた。</b>
その2つも多いが、それ以上に多いのは〈量の出所〉と〈価格の内訳〉である。</p></div>

<h2>4. 新しいアノマリー</h2>
<div class="grid2">
<div class="card"><h3>A37　営業へ回した空欄が、資料を殺す</h3>
<p class="note">A28（第12.4版）は「確定できない量は作り話をせず、営業が埋める記入欄にして申し送る」という
出口を作った。<b>21/21 で使われた。</b>そして 21/21 の買い手が、その空欄を理由に止めている。</p>
<div class="q">財源が空欄の紙は、県にも公庫にも産地部会にも出せん。<b>― 農業・林業・水産業／代表取締役</b></div>
<p class="note"><b>モデルが正しく動いた結果として、資料が通らなくなっている。</b>
捏造を防ぐことと、資料が使えることが、ここで正面から衝突している。</p></div>

<div class="card"><h3>A38　幅のある金額は、稟議に載らない</h3>
<p class="note">売り手の価格帯そのもの（1,400万〜3,200万＝2.3倍）が拒まれる。20/21。</p>
<div class="q">1,400万から3,200万は2.3倍の開きで、これは見積ではなく相場表だ。<b>― 製造・メーカー／購買部長</b></div>
<div class="q">この幅のまま銀行の融資担当のところへ持って行ったら、まず「で、いくらなんですか」で終わる。
<b>― 観光・旅行・宿泊／社長</b></div></div>

<div class="card"><h3>A36　侮辱を避けるための断り書きが、逆に侮辱として読まれる</h3>
<p class="note">R17 は「⑤が買い手の既承認を否定してはならない」と要求する。生成器はそれに従い、
⑤末尾と⑥末尾で「過去の決定の当否については述べていません」と断った。8/21 がこれを咎めた。</p>
<div class="q">二度言われると、逆に否定されている気がする。<b>― 製造・メーカー／購買部長</b></div></div>

<div class="card"><h3>A39　②の問い返しが、決めつけとして着弾する</h3>
<p class="note">②は①の事実を別の単位で数え直して驚きを作る段である
（T&amp;T の defamiliarization）。その問いの形が、買い手には「あなたは数えていない」という
決めつけとして届く。8/21。</p>
<div class="q">三十年そうやって回してきた宿に向かって、どなたの手元にあるでしょうか、はない。
<b>― 観光・旅行・宿泊／社長</b></div>
<p class="note"><b>②の設計の核心そのものが、買い手の側では危険物である。</b></p></div>
</div>

<h2>5. 21件すべて</h2>
<div class="card" style="padding-bottom:10px">
<p class="note" style="margin:0 0 8px">絞り込み（もう一度押すと解除）</p>
<div id="f1"></div><div id="f2"></div><div id="f3"></div><div id="f4"></div>
<p class="note" style="margin:10px 0 0"><span id="cnt"></span></p>
</div>
<div id="cells"></div>

<h2>6. 読み方の留保</h2>
<div class="card"><p class="note" style="margin:0">
各条件 n=1 である。読んでよいのは<b>構造的な傾向</b>だけで、個別セルの差は振れ幅と区別できない。<br>
⑥の字数は採点の根拠にしていない（第12.3版で採点根拠から外した。同じ指示で振れるため）。<br>
盲検買い手は LLM であり、ここで測れたのは「仕様を満たした資料が<b>モデルの想定する買い手像</b>を
通るか」であって、実在の買い手を通るかではない。<b>帰納の場は、営業ウェブアプリの
ページ単位の閲覧ログにある。モデルとアプリはまだ接続されていない。</b></p></div>
</div>
<script>const DATA={json.dumps(ROWS, ensure_ascii=False)};
const TAGS={json.dumps(list(tag_count), ensure_ascii=False)};
{JS}</script></html>"""

open("25業界レポート.html", "w", encoding="utf-8").write(HTML)
print(f"25業界レポート.html を書いた（{n}件・{len(HTML):,}バイト）")
