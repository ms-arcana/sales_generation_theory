import json, html

D = json.load(open('data.json'))
DATA_JS = json.dumps(D, ensure_ascii=False)

CSS = r"""
:root{--paper:#EFF0EC;--paper-2:#F7F8F5;--ink:#1A2420;--ink-soft:#5C6862;--ink-faint:#8B958F;--rule:#CDD1C9;
--accent:#473AA0;--accent-soft:#E5E2F6;--accent-line:#B4ACE4;--ochre:#8E6410;--ochre-soft:#F1E9D6;--ochre-line:#D8C48C;
--crim:#8F2B2B;--crim-soft:#F6E6E6;--crim-line:#DDABAB;
--font-display:"Shippori Mincho",serif;--font-body:"Zen Kaku Gothic New",sans-serif;--font-mono:"Roboto Mono",monospace;}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--paper);color:var(--ink);font-family:var(--font-body);font-weight:400;-webkit-font-smoothing:antialiased}
body{min-height:100vh;display:flex;flex-direction:column}
.stage{flex:1;display:flex;align-items:flex-start;justify-content:center;padding:36px 32px 20px}
.slide{display:none;width:100%;max-width:1080px}
.slide.is-active{display:block}
@media (prefers-reduced-motion:no-preference){.slide.is-active{animation:rise .3s ease-out both}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}}
.eyebrow{font-family:var(--font-mono);font-size:12px;letter-spacing:.14em;color:var(--ink-faint);margin:0 0 14px;display:flex;align-items:center;gap:12px}
.eyebrow::after{content:"";flex:1;height:1px;background:var(--rule)}
h1{font-family:var(--font-display);font-weight:700;font-size:clamp(28px,4.2vw,48px);line-height:1.34;letter-spacing:.01em;margin:0 0 26px}
h2{font-family:var(--font-display);font-weight:700;font-size:clamp(22px,3vw,34px);line-height:1.42;margin:0 0 20px}
h3{font-family:var(--font-body);font-weight:700;font-size:15px;letter-spacing:.04em;margin:0 0 10px}
p{line-height:1.85;margin:0 0 16px;font-size:16px}
.lead{font-size:17.5px;color:var(--ink-soft);max-width:66ch}
.note{font-size:13.5px;color:var(--ink-faint);line-height:1.78}
.pull{font-family:var(--font-display);font-size:clamp(18px,2.2vw,24px);line-height:1.7;border-left:3px solid var(--accent);padding:4px 0 4px 22px;margin:0 0 24px;max-width:52ch}
.cols{display:grid;gap:22px}.cols-2{grid-template-columns:1fr 1fr}.cols-3{grid-template-columns:repeat(3,1fr)}
.card{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;padding:18px 20px}
.card p:last-child{margin-bottom:0}
.title-meta{font-family:var(--font-mono);font-size:12.5px;letter-spacing:.1em;color:var(--ink-faint);display:flex;gap:22px;flex-wrap:wrap;border-top:1px solid var(--rule);padding-top:16px;margin-top:32px}
/* matrix */
.matrix{display:grid;grid-template-columns:120px repeat(3,1fr);gap:8px;margin-bottom:20px}
.mhead{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.1em;color:var(--ink-faint);display:flex;align-items:flex-end;padding-bottom:4px}
.mrow-label{font-size:13px;font-weight:500;color:var(--ink-soft);display:flex;align-items:center;line-height:1.5}
.mcell{border:1px solid var(--rule);background:var(--paper-2);border-radius:3px;padding:11px 12px;cursor:pointer;text-align:left;font-family:var(--font-body);min-height:78px}
.mcell:hover{background:#E8E9E4}
.mcell .cl{font-size:13px;font-weight:500;line-height:1.45;display:block;margin-bottom:6px;color:var(--ink)}
.mcell .cv{font-family:var(--font-mono);font-size:11px;letter-spacing:.06em;display:block}
.mcell.v-no .cv{color:var(--crim)}
.mcell.v-part .cv{color:var(--ochre)}
.mcell.v-ok .cv{color:var(--accent)}
.mcell[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-soft);box-shadow:inset 0 0 0 1px var(--accent-line)}
.ladder{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:0 0 16px}
.rung{border:1px solid var(--rule);border-radius:3px;padding:10px 11px;background:var(--paper-2);cursor:pointer;text-align:left;font-family:var(--font-body)}
.rung .rn{font-size:13px;font-weight:700;display:block;margin-bottom:5px}
.rung .rt{font-size:11px;font-family:var(--font-mono);letter-spacing:.04em;display:block;line-height:1.5}
.rung.pass{border-color:var(--accent-line);background:var(--accent-soft)}
.rung.pass .rn,.rung.pass .rt{color:#2F2570}
.rung.wob{border-color:var(--ochre-line);background:var(--ochre-soft)}
.rung.wob .rn,.rung.wob .rt{color:#6B4C0C}
.rung.fail{border-color:var(--crim-line);background:var(--crim-soft)}
.rung.fail .rn,.rung.fail .rt{color:var(--crim)}
.rung[aria-pressed="true"]{box-shadow:inset 0 0 0 2px var(--ink)}
.detail{border:1px solid var(--rule);border-radius:3px;background:var(--paper-2);padding:18px 20px}
.detail .dh{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.1em;color:var(--ink-faint);margin-bottom:8px}
.voice{font-family:var(--font-display);font-size:18px;line-height:1.72;border-left:3px solid var(--crim);padding:2px 0 2px 18px;margin:0 0 14px;color:#5E1F1F}
.voice.ok{border-left-color:var(--accent);color:#2F2570}
.voice.wob{border-left-color:var(--ochre);color:#6B4C0C}
.kv{font-size:14px;line-height:1.8;margin:0 0 12px}
.kv b{font-weight:700;font-size:12.5px;font-family:var(--font-mono);letter-spacing:.06em;color:var(--ink-faint);display:block;margin-bottom:2px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--rule);vertical-align:top;line-height:1.65}
thead th{font-family:var(--font-mono);font-size:12px;letter-spacing:.06em;font-weight:500;color:var(--ink-faint);border-bottom:1px solid var(--ink)}
tbody th{font-weight:500;color:var(--ink-soft);width:160px}
td.hit{color:var(--accent);font-weight:500}
td.miss{color:var(--ink-faint)}
td.bad{color:var(--crim);font-weight:500}
ul.plain{margin:0;padding:0;list-style:none}
ul.plain li{padding:11px 0 11px 20px;border-bottom:1px solid var(--rule);font-size:15px;line-height:1.75;position:relative}
ul.plain li::before{content:"";position:absolute;left:0;top:20px;width:8px;height:1px;background:var(--accent)}
ul.plain li:last-child{border-bottom:0}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.chips button{font-family:var(--font-body);font-size:12.5px;font-weight:500;background:transparent;color:var(--ink-soft);border:1px solid var(--rule);border-radius:999px;padding:6px 14px;cursor:pointer}
.chips button:hover{background:var(--paper-2)}
.chips button[aria-pressed="true"]{background:var(--ink);color:#fff;border-color:var(--ink)}
.chips button.sev-fatal[aria-pressed="true"]{background:var(--crim);border-color:var(--crim)}
.sevtag{font-family:var(--font-mono);font-size:11px;letter-spacing:.08em;padding:2px 7px;border-radius:2px;border:1px solid;display:inline-block}
.sevtag.f{color:var(--crim);border-color:var(--crim-line);background:var(--crim-soft)}
.sevtag.m{color:var(--ochre);border-color:var(--ochre-line);background:var(--ochre-soft)}
.cellchips{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.cellchips span{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.06em;color:var(--ink-faint);border:1px solid var(--rule);border-radius:2px;padding:2px 6px}
.slotbox{border:1px solid var(--rule);border-radius:3px;background:var(--paper-2);padding:14px 16px;margin-bottom:10px}
.slotbox .sh{font-family:var(--font-display);font-size:17px;font-weight:700;margin-bottom:8px}
.slotgrid{display:grid;grid-template-columns:92px 1fr;gap:4px 12px;font-size:13.5px;line-height:1.72}
.slotgrid .k{font-family:var(--font-mono);font-size:11px;letter-spacing:.06em;color:var(--ink-faint);padding-top:4px}
.slotgrid .rj{color:var(--crim)}
.nav{display:flex;align-items:center;gap:16px;padding:14px 32px 22px;border-top:1px solid var(--rule);background:var(--paper)}
.dots{display:flex;gap:7px;flex:1}
.dots button{width:24px;height:3px;padding:0;border:0;border-radius:2px;background:var(--rule);cursor:pointer}
.dots button[aria-current="true"]{background:var(--accent)}
.nav .counter{font-family:var(--font-mono);font-size:12px;color:var(--ink-faint)}
.nav .move{font-family:var(--font-mono);font-size:13px;background:transparent;border:1px solid var(--rule);border-radius:3px;color:var(--ink-soft);padding:6px 12px;cursor:pointer}
.nav .move:hover{background:var(--paper-2)}
button:focus-visible{outline:2px solid var(--ochre);outline-offset:2px}
@media (max-width:900px){.cols-2,.cols-3{grid-template-columns:1fr}.ladder{grid-template-columns:repeat(3,1fr)}
.matrix{grid-template-columns:1fr}.mhead,.mrow-label{display:none}.stage{padding:22px 16px 14px}.nav{padding:10px 16px 14px}tbody th{width:auto}}
"""

def esc(s): return html.escape(str(s))

S = D['synthesis']

# --- slide: breakages ---
brk_rows = ""
for i, b in enumerate(S['confirmed_breakages']):
    sev = 'f' if b['severity'] == '致命' else 'm'
    cells = "".join('<span>%s</span>' % esc(c) for c in b['affected_cells'])
    brk_rows += f"""<article class="brk" data-sev="{esc(b['severity'])}" data-kind="{esc(b['kind'])}" style="display:none">
  <div class="card" style="margin-bottom:14px">
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
      <span class="sevtag {sev}">{esc(b['severity'])}</span>
      <span class="note" style="font-family:var(--font-mono);font-size:11px;letter-spacing:.08em">{esc(b['stage'])}</span>
      <span class="note" style="font-family:var(--font-mono);font-size:11px;letter-spacing:.08em">{esc(b['kind'])}</span>
      <span class="note" style="font-family:var(--font-mono);font-size:11px;letter-spacing:.08em">修正コスト:{esc(b['fix_cost'])}</span>
    </div>
    <h3 style="font-family:var(--font-display);font-size:20px;line-height:1.55;margin-bottom:12px">{esc(b['title'])}</h3>
    <p class="voice">{esc(b['buyer_voice'])}</p>
    <p class="kv"><b>機序</b>{esc(b['mechanism'])}</p>
    <p class="kv" style="margin-bottom:0"><b>修正案</b>{esc(b['fix'])}</p>
    <div class="cellchips">{cells}</div>
  </div>
</article>"""

# --- slide: axes ---
axis_rows = ""
for a in S['axis_proposals']:
    vals = " ／ ".join(a['values'])
    axis_rows += f"""<tr><th scope="row">{esc(a['name'])}</th><td>{esc(vals)}</td><td class="miss">{esc(a['why'])}</td><td class="hit">{esc(a['affected_blocks'])}</td></tr>"""

# --- slide: slots ---
slot_boxes = ""
for s in S['slot_constraints']:
    slot_boxes += f"""<div class="slotbox">
  <div class="sh">{esc(s['stage'])}</div>
  <div class="slotgrid">
    <div class="k">前提化</div><div>{esc(s['presupposes'])}</div>
    <div class="k">様相を上げる先</div><div>{esc(s['raises_to'])}</div>
    <div class="k">発話行為 / 主語</div><div>{esc(s['speech_act'])} ／ {esc(s['subject'])}</div>
    <div class="k">棄却条件</div><div class="rj">{esc(s['reject_if'])}</div>
  </div>
</div>"""

open_lis = "".join("<li>%s</li>" % esc(q) for q in S['open_questions'])

HTML = f"""<!doctype html>
<html lang="ja">
<meta charset="utf-8">
<title>買い手マルチエージェント反証レポート ― 様相フローは商材横断で通用するか</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>

<div class="stage">

<section class="slide is-active" aria-label="表紙">
  <p class="eyebrow">反証レポート / 2026-08-06</p>
  <h1>階段の①〜③は全セルで登れた。<br>落ちるのは④⑤⑥——<br>そのうち2つは軸の穴、1つは思想の欠陥</h1>
  <p class="lead">{esc(S['headline'])}</p>
  <div class="title-meta">
    <span>買い手9体 × 検証3レンズ</span>
    <span>破綻主張 {D['stats']['survived'] + D['stats']['killed']}件 → 生存 {D['stats']['survived']}件</span>
    <span>総合判定：{esc(S['overall_verdict'])}</span>
    <span>全9枚</span>
  </div>
</section>

<section class="slide" aria-label="検証のやり方">
  <p class="eyebrow">01 — どう検証したか</p>
  <h2>3商材 × 3業界の買い手を演じさせ、<br>各段で「そうだね」と言えるかだけを見た</h2>
  <div class="cols cols-3" style="margin-bottom:22px">
    <div class="card"><h3>買い手 9体</h3><p class="note" style="margin:0">ITソリューション／コンサルティング／ロボットハンドを、決裁文化の異なる業界へ当てる。各エージェントは軸の値から必須ブロックを機械的に導き、生成されるはずのスライドを自分で書いてから、買い手として判定した。</p></div>
    <div class="card"><h3>検証 3レンズ</h3><p class="note" style="margin:0">買い手が挙げた破綻を、①モデルの欠陥か入力ミスか ②日本のB2B購買実務で本当に起きるか ③修正すべきか範囲外宣言すべきか、の3視点で多数決。2/3以上で生存。</p></div>
    <div class="card"><h3>結果</h3><p class="note" style="margin:0">破綻主張 {D['stats']['survived'] + D['stats']['killed']}件のうち {D['stats']['killed']}件を却下、{D['stats']['survived']}件が生存。重複を統合して{len(S['confirmed_breakages'])}件に整理した。</p></div>
  </div>
  <p class="pull">判定を甘くしないよう、各エージェントには「全部破綻と書くのは無価値。通る段は素直に通ると書け」と指示した。実際、①と③は9セル全部で通過している。</p>
  <p class="note">なお本レポートは買い手をシミュレートした思考実験であり、実顧客の反応の実測ではない。破綻の指摘は仮説として扱い、実際の商談での検証が要る。</p>
</section>

<section class="slide" aria-label="マトリクス実演">
  <p class="eyebrow">02 — 実演 / セルを選ぶと階段の登り方が出る</p>
  <h2 style="margin-bottom:16px">同じフローを9通りの買い手に通した</h2>
  <div class="matrix" id="matrix"></div>
  <div class="ladder" id="ladder"></div>
  <div class="detail" id="detail"></div>
</section>

<section class="slide" aria-label="段別の破綻">
  <p class="eyebrow">03 — 何が分かったか</p>
  <h2>破綻は段ごとに偏っている</h2>
  <table>
    <thead><tr><th scope="col">段</th><th scope="col">通過</th><th scope="col">揺らぐ</th><th scope="col">破綻</th><th scope="col">読み</th></tr></thead>
    <tbody id="stagetable"></tbody>
  </table>
  <div class="cols cols-2" style="margin-top:22px">
    <div class="card"><h3>①〜③は設計思想の勝ち</h3><p class="note" style="margin:0">生活世界の措定・内在的否定・名づけの3段は、業界も商材も問わず機能した。②が全セルで「揺らぐ」に留まるのは仕様どおり（否定の萌芽は承認と不安の中間でよい）。ここは触らなくてよい。</p></div>
    <div class="card" style="border-color:var(--crim-line);background:var(--crim-soft)"><h3 style="color:var(--crim)">④⑤⑥に集中する</h3><p class="note" style="margin:0;color:#5E1F1F">④は「今」を担うブロックが規則上どの軸の組合せでも点かない。⑤は消去の次元が能力一次元しかない。⑥は読み手を裁定者だと思い込んでいる。3つとも別々の原因で、別々の直し方が要る。</p></div>
  </div>
</section>

<section class="slide" aria-label="確定した破綻">
  <p class="eyebrow">04 — 生き残った破綻 {len(S['confirmed_breakages'])}件</p>
  <h2 style="margin-bottom:16px">2/3以上の検証者が反証として認めたもの</h2>
  <div class="chips" id="brkchips"></div>
  <div id="brklist">{brk_rows}</div>
</section>

<section class="slide" aria-label="適用範囲">
  <p class="eyebrow">05 — 効く範囲と効かない範囲</p>
  <h2>モデルは万能ではない。境界を先に引く</h2>
  <p class="pull" style="max-width:60ch">{esc(S['scope_statement'].split('。')[0])}。</p>
  <div class="card"><p style="margin:0;font-size:15px;line-height:1.9">{esc(S['scope_statement'])}</p></div>
</section>

<section class="slide" aria-label="軸の追加提案">
  <p class="eyebrow">06 — 直し方 / 軸</p>
  <h2>既存5軸で表現できないと確定したものだけ足す</h2>
  <table>
    <thead><tr><th scope="col">追加・変更する軸</th><th scope="col">値</th><th scope="col">なぜ要るか</th><th scope="col">どのブロックを動かすか</th></tr></thead>
    <tbody>{axis_rows}</tbody>
  </table>
  <p class="note" style="margin-top:18px"><b style="color:var(--ink)">営業の商談ごと入力は3〜5問増える。</b>　既定値（読み手＝伝達者、②の帰責先＝環境・制度の変化）を実務上いちばん安全な側に置くことで、現場が既定のまま流しても事故らない設計にしてある。</p>
</section>

<section class="slide" aria-label="スロット制約">
  <p class="eyebrow">07 — 直し方 / 骨格制約</p>
  <h2 style="margin-bottom:16px">各段が持つスロット（CLAUDE.md に据える形）</h2>
  <p class="note" style="margin-bottom:16px">「前段のどの承認を前提化し、どの様相を一段上げるか」をスロットとして持たせ、棄却条件を層2.5の機械判定に落とす。棄却条件は文字列マッチと入力値の参照だけで判定できる粒度にしてある。</p>
  {slot_boxes}
</section>

<section class="slide" aria-label="判断を仰ぎたいこと">
  <p class="eyebrow">08 — 判断を仰ぎたいこと</p>
  <h2>次に決めたい{len(S['open_questions'])}点</h2>
  <ul class="plain">{open_lis}</ul>
</section>

</div>

<nav class="nav" aria-label="スライド操作">
  <button type="button" class="move" id="prev">← 前</button>
  <button type="button" class="move" id="next">次 →</button>
  <div class="dots" id="dots"></div>
  <span class="counter" id="counter"></span>
</nav>

<script>
var DATA = {DATA_JS};
(function(){{
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var dots=document.getElementById('dots'),counter=document.getElementById('counter'),idx=0;
  slides.forEach(function(s,i){{var b=document.createElement('button');b.type='button';
    b.setAttribute('aria-label',(i+1)+'枚目へ');b.addEventListener('click',function(){{go(i);}});dots.appendChild(b);}});
  function go(n){{idx=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(s,i){{s.classList.toggle('is-active',i===idx);}});
    [].forEach.call(dots.children,function(d,i){{d.setAttribute('aria-current',i===idx?'true':'false');}});
    counter.textContent=String(idx+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
    window.scrollTo(0,0);}}
  document.getElementById('prev').addEventListener('click',function(){{go(idx-1);}});
  document.getElementById('next').addEventListener('click',function(){{go(idx+1);}});
  document.addEventListener('keydown',function(e){{
    if(e.target.tagName==='BUTTON'&&(e.key===' '||e.key==='Enter'))return;
    if(e.key==='ArrowRight'||e.key==='PageDown'){{e.preventDefault();go(idx+1);}}
    if(e.key==='ArrowLeft'||e.key==='PageUp'){{e.preventDefault();go(idx-1);}}}});
  go(0);

  /* ---- matrix ---- */
  var ORDER=['IT-AUTO','IT-BANK','IT-SME','CON-TRADE','CON-HOSP','CON-GOV','ROB-TIER1','ROB-3PL','ROB-FOOD'];
  var ROWS=[['ITソリューション',['IT-AUTO','IT-BANK','IT-SME']],
            ['コンサルティング',['CON-TRADE','CON-HOSP','CON-GOV']],
            ['ロボットハンド',['ROB-TIER1','ROB-3PL','ROB-FOOD']]];
  var COLS=['大企業・多段稟議','規制・合議','小規模・単独決裁'];
  var byId={{}};DATA.buyers.forEach(function(b){{byId[b.id]=b;}});
  var cur='IT-AUTO',curStage=0;
  var mx=document.getElementById('matrix'),ld=document.getElementById('ladder'),dt=document.getElementById('detail');

  function vclass(v){{return v==='不成立'?'v-no':(v==='部分的に成立'?'v-part':'v-ok');}}
  function tclass(t){{return t.indexOf('破綻')>=0?'fail':(t.indexOf('揺らぐ')>=0?'wob':'pass');}}

  mx.appendChild(el('div','mhead',''));
  COLS.forEach(function(c){{mx.appendChild(el('div','mhead',c));}});
  ROWS.forEach(function(r){{
    mx.appendChild(el('div','mrow-label',r[0]));
    r[1].forEach(function(id){{
      var b=byId[id];
      var btn=document.createElement('button');btn.type='button';
      btn.className='mcell '+vclass(b.verdict);btn.dataset.id=id;
      btn.innerHTML='<span class="cl">'+b.label.split(' × ')[1]+'</span><span class="cv">'+b.verdict+'</span>';
      btn.addEventListener('click',function(){{cur=id;curStage=firstFail(byId[id]);render();}});
      mx.appendChild(btn);
    }});
  }});
  function el(tag,cls,txt){{var d=document.createElement(tag);d.className=cls;d.textContent=txt;return d;}}
  function firstFail(b){{for(var i=0;i<b.stages.length;i++){{if(b.stages[i].t.indexOf('破綻')>=0)return i;}}return 0;}}

  function render(){{
    [].forEach.call(mx.querySelectorAll('.mcell'),function(c){{
      c.setAttribute('aria-pressed',c.dataset.id===cur?'true':'false');}});
    var b=byId[cur];
    ld.innerHTML='';
    b.stages.forEach(function(s,i){{
      var btn=document.createElement('button');btn.type='button';
      btn.className='rung '+tclass(s.t);
      btn.setAttribute('aria-pressed',i===curStage?'true':'false');
      btn.innerHTML='<span class="rn">'+s.s+'</span><span class="rt">'+s.t+'</span>';
      btn.addEventListener('click',function(){{curStage=i;render();}});
      ld.appendChild(btn);
    }});
    var s=b.stages[curStage];
    var vc=tclass(s.t);
    dt.innerHTML=
      '<div class="dh">'+b.label+' 　/　 '+b.axes+'</div>'+
      '<p class="voice '+(vc==='fail'?'':vc==='wob'?'wob':'ok')+'">'+s.v+'</p>'+
      '<p class="kv"><b>この段で生成されるスライド</b>'+s.c+'</p>'+
      '<p class="kv"><b>なぜその判定か</b>'+s.a+'</p>'+
      '<p class="kv" style="margin-bottom:0"><b>このセルの総合判定 — '+b.verdict+'</b>'+b.reason+'</p>';
  }}
  render();

  /* ---- stage table ---- */
  var STAGES=['①現状S','②否定の内在','③問題化Q','④必然化','⑤消去','⑥提案P'];
  var READ={{'①現状S':'措定は業界を問わず成立する。ただし縮退が効かず「調べた証明」に落ちる例あり',
    '②否定の内在':'仕様どおり中間状態。ただし欠如を誰に帰すかで承認にも防衛にも転ぶ',
    '③問題化Q':'名づけは機能する。買い手が既に名づけている場合は復唱になる',
    '④必然化':'「今」のwarrantを担うブロックが規則上どの軸でも点かない',
    '⑤消去':'消去次元が能力一次元。内製・帰責・権限に触れると論証が自壊する',
    '⑥提案P':'読み手＝裁定者の前提が崩れる。エンテュメーメが上申の妨げになる'}};
  var tb=document.getElementById('stagetable');
  STAGES.forEach(function(st){{
    var p=0,w=0,f=0;
    DATA.buyers.forEach(function(b){{
      var s=b.stages.filter(function(x){{return x.s===st;}})[0];
      if(!s)return;
      if(s.t.indexOf('破綻')>=0)f++;else if(s.t.indexOf('揺らぐ')>=0)w++;else p++;
    }});
    var tr=document.createElement('tr');
    tr.innerHTML='<th scope="row">'+st+'</th>'+
      '<td class="'+(p>=5?'hit':'miss')+'">'+p+' / 9</td>'+
      '<td class="miss">'+w+' / 9</td>'+
      '<td class="'+(f>=3?'bad':'miss')+'">'+f+' / 9</td>'+
      '<td class="miss">'+READ[st]+'</td>';
    tb.appendChild(tr);
  }});

  /* ---- breakage filter ---- */
  var arts=[].slice.call(document.querySelectorAll('.brk'));
  var chips=document.getElementById('brkchips');
  var FILTERS=[['すべて',null],['致命のみ','致命'],['重大のみ','重大']];
  var curF=null;
  FILTERS.forEach(function(f){{
    var b=document.createElement('button');b.type='button';b.textContent=f[0];
    if(f[1]==='致命')b.className='sev-fatal';
    b.addEventListener('click',function(){{curF=f[1];paint();}});
    b.dataset.v=f[1]===null?'':f[1];
    chips.appendChild(b);
  }});
  function paint(){{
    [].forEach.call(chips.children,function(c){{
      c.setAttribute('aria-pressed',(c.dataset.v||null)===curF?'true':'false');}});
    arts.forEach(function(a){{
      a.style.display=(!curF||a.dataset.sev===curF)?'block':'none';}});
  }}
  paint();
}})();
</script>
</html>"""

open('buyer-falsification-report.html', 'w').write(HTML)
print(len(HTML))
