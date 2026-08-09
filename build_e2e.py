import json, html
D = json.load(open('e2e_view.json'))
DATA_JS = json.dumps(D, ensure_ascii=False)
CSS = open('css25.css').read() + """
.cellbar{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:16px}
.cellbtn{border:1px solid var(--rule);background:var(--paper-2);border-radius:3px;padding:9px 10px;cursor:pointer;text-align:left;font-family:var(--fb);font-size:12px;line-height:1.45}
.cellbtn:hover{background:#E8E9E4}
.cellbtn[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent)}
.cellbtn .sg{display:block;font-family:var(--fm);font-size:10px;color:var(--ink-faint);margin-top:3px}
.cellbtn .vv{display:flex;gap:2px;margin-top:5px}
.cellbtn .vv i{width:10px;height:10px;border-radius:1px;display:block}
.mok{background:var(--accent)}.mng{background:var(--crim)}
.slidebox{border:1px solid var(--rule);border-left:3px solid var(--accent);background:#fff;border-radius:2px;padding:12px 15px;margin-bottom:10px;font-size:14px;line-height:1.85;white-space:pre-wrap}
.slidebox .sh{font-family:var(--fm);font-size:10.5px;letter-spacing:.08em;color:var(--ink-faint);display:flex;gap:10px;align-items:center;margin-bottom:7px}
.slidebox.brk{border-left-color:var(--crim)}
.slidebox.wob{border-left-color:var(--ochre)}
.pv{font-family:var(--fm);font-size:10.5px;padding:1px 6px;border-radius:2px;border:1px solid}
.pv.ok{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.pv.wob{color:var(--ochre);border-color:var(--ochre-line);background:var(--ochre-soft)}
.pv.brk{color:var(--crim);border-color:var(--crim-line);background:var(--crim-soft)}
.pv.ng{color:var(--ink-faint);border-color:var(--rule);background:#fff}
.why{font-size:13px;line-height:1.8;color:var(--ink-soft);background:var(--paper-2);border:1px solid var(--rule);border-radius:2px;padding:9px 12px;margin:-4px 0 12px}
.derivbox{font-size:12.5px;line-height:1.75;color:var(--ink-soft);background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;padding:12px 14px;margin-bottom:12px;white-space:pre-wrap;max-height:230px;overflow:auto}
.stat{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.statc{border:1px solid var(--rule);background:var(--paper-2);border-radius:3px;padding:16px 18px;text-align:center}
.statc .n{font-family:var(--fd);font-size:34px;font-weight:700;line-height:1.2;display:block}
.statc .l{font-size:12.5px;color:var(--ink-faint);line-height:1.6;display:block;margin-top:6px}
@media(max-width:900px){.cellbar,.stat{grid-template-columns:repeat(2,1fr)}}
"""
def e(x): return html.escape(str(x))

H = f"""<!doctype html>
<html lang="ja"><meta charset="utf-8">
<title>8セル生成・検証レポート</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<div class="stage">

<section class="slide is-active" aria-label="表紙">
  <p class="eyebrow">生成・検証レポート / 2026-08-06 / 2業界 × 2セグメント × 2商材</p>
  <h1>④は完全に当たり、<br>⑥は7セルで落ちた</h1>
  <p class="lead">形式系に従って48枚を生成し、予測を見ていない買い手8体に読ませました。R9の語彙漏洩は 98% から実質ゼロへ。最長滞在の予測は8/8で的中。一方⑥は7/8で破綻し、その機序は4つに収束しました。</p>
  <div class="stat" style="margin-top:30px">
    <div class="statc"><span class="n" style="color:var(--accent)">8/8</span><span class="l">④が最長滞在<br>（予測・観察とも）</span></div>
    <div class="statc"><span class="n" style="color:var(--accent)">4%</span><span class="l">R9棄却率<br>（前回⑤は98%漏洩）</span></div>
    <div class="statc"><span class="n" style="color:var(--crim)">7/8</span><span class="l">⑥が破綻</span></div>
    <div class="statc"><span class="n">15/48</span><span class="l">段判定の予測一致<br>（内訳は02枚目）</span></div>
  </div>
</section>

<section class="slide" aria-label="一致率の内訳">
  <p class="eyebrow">01 — 予測と観察の突合</p>
  <h2>一致31%。ただし食い違いの大半は「誤用」だった</h2>
  <p style="max-width:66ch">アブダクティブ分析の手順どおり、食い違いを<b>アノマリー／未踏／誤用</b>に分けます。安易にアノマリーへ数えると、直す必要のない箇所を直すことになります。</p>
  <table>
    <thead><tr><th style="width:60px">段</th><th>食い違いの型</th><th style="width:60px">件数</th><th>分類</th></tr></thead>
    <tbody>
      <tr><th scope="row">②</th><td>予測=通過 → 観察=揺らぐ</td><td>8</td><td class="miss"><b>誤用。</b>仕様は「②だけは〈そうだね…気になるね〉に留まってよい」と明記している。<b>買い手は仕様どおりに振る舞い、生成側が仕様を読み違えた</b></td></tr>
      <tr><th scope="row">③</th><td>予測=揺らぐ → 観察=通過</td><td>7</td><td class="miss"><b>誤用。</b>生成側が③（名づけ）を過度に悲観していた。実際は③が最も安定して通る段だった</td></tr>
      <tr><th scope="row">⑥</th><td>予測=通過 → 観察=破綻</td><td>7</td><td class="bad"><b>アノマリー。</b>機序は4つに収束（03〜04枚目）</td></tr>
      <tr><th scope="row">⑤</th><td>混在（破綻2／通過3／揺らぐ1）</td><td>6</td><td class="miss">⑤は予測が最も外れにくかった。破綻2件はいずれも⑥の破綻に連動</td></tr>
      <tr><th scope="row">①④</th><td>—</td><td>2</td><td class="hit">①は8/8通過。④の破綻3件はすべて「量が最終裁定点で通貨に両替できない」型（アノマリーA2）</td></tr>
    </tbody>
  </table>
  <p class="pull" style="margin-top:24px;max-width:58ch">②の8件は、予測を先に置いたからこそ「モデルが外した」ではなく「生成側が読み違えた」と切り分けられました。予測なしなら、全部モデルの穴に見えていたはずです。</p>
</section>

<section class="slide" aria-label="④の検証">
  <p class="eyebrow">02 — 当たった部分</p>
  <h2>④の「まだ計算していない量」は、8セル全部で最長滞在だった</h2>
  <p style="max-width:66ch">第4版で中心命題に追記した <b>「暦は買い手の意思の外から。かつ、買い手がまだ計算していない量とともに」</b> の直接の裏付けです。予測8/8、観察8/8。しかも買い手は全員、その量を<b>自分で検算しています</b>。</p>
  <div class="cols cols-2" style="margin-bottom:20px">
    <div class="card"><h3>買い手が検算した記録</h3><p class="note" style="margin:0">「45営業日と『9月定例会を引いて約30日』の算定を、<b>手元の予算編成方針と議会日程を出して突き合わせた</b>」（公立病院）／「④の『2026年11月28日』とその逆算。ここでいったん資料を置いて、<b>壁のカレンダーで自分でも日数を数えた</b>」（中小運送）</p></div>
    <div class="card" style="border-color:var(--accent-line);background:var(--accent-soft)"><h3 style="color:#2F2570">閉じるときの一言にも出ている</h3><p class="note" style="margin:0;color:#5F55A8">「……9月30日か。<b>この日付は使わせてもらう</b>」（3PL）／「11月28日ってのは、まあ、そうだ。<b>そこは合ってる</b>」（中小運送）／「<b>時間の話は当たってる。</b>月曜、運行管理者に4月からの分を人別で出させる」（中小運送）</p></div>
  </div>
  <div class="card" style="border-color:var(--teal-line);background:var(--teal-soft)">
    <h3 style="color:var(--teal)">R9 提示変換も効いた</h3>
    <p class="note" style="margin:0;color:#2C514E">生成48枚のうち<b>禁止語彙の漏洩はゼロ</b>。棄却2件はいずれも「列挙＋否定形」ヒューリスティックの誤検出でした（この検出器が弱いことは実装時に申告済み）。前回の⑤が123/125本＝98%漏洩だったことと比べると、<b>提示形態を段ごとに指定するだけで漏洩は止まる</b>ことが確認できました。</p>
  </div>
</section>

<section class="slide" aria-label="アノマリー">
  <p class="eyebrow">03 — アノマリー / ⑥が落ちた4つの機序</p>
  <h2>⑤までは登れる。⑥で落ちる</h2>

  <div class="card" style="margin-bottom:14px;border-color:var(--crim-line);background:var(--crim-soft)">
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:8px"><span class="sevtag f">致命</span><span class="mono">⑥／中心命題§1.2／形式系</span></div>
    <h3 style="font-family:var(--fd);font-size:19px;line-height:1.6;margin-bottom:10px;color:var(--crim)">A1. ④で積んだ量が、最終裁定点の通貨に両替できない</h3>
    <p class="kv" style="color:#5E1F1F"><b style="color:var(--crim)">買い手の声</b>「1,512時間が減っても<b>決算資料の人件費は1円も動かない</b>。議会で必ず出るのは『で、いくら減るんですか』の一言で、そこに『減りません、時間が空きます』と答えることになる」（公立病院・事業管理者）</p>
    <p class="kv" style="color:#5E1F1F;margin-bottom:0"><b style="color:var(--crim)">機序</b>形式系には移送関数 $T$ があるのに、<b>④の量の選択が κ_n（最終裁定点の基準）を参照していない</b>。看護師長の勤務表作成時間は管理職手当なので時間外申請が出ず、時間の量は円へ両替できない。now(Q) の uncomputed(q) に expressible(q, κ_n) の条件が抜けている。<b>述語の弱さ</b></p>
  </div>

  <div class="card" style="margin-bottom:14px;border-color:var(--crim-line);background:var(--crim-soft)">
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:8px"><span class="sevtag f">致命</span><span class="mono">⑥／適用範囲宣言</span></div>
    <h3 style="font-family:var(--fd);font-size:19px;line-height:1.6;margin-bottom:10px;color:var(--crim)">A2. ⑤はカテゴリまでしか絞れないのに、⑥でカテゴリ内差別化を要求される</h3>
    <p class="kv" style="color:#5E1F1F"><b style="color:var(--crim)">買い手の声</b>「3条件を満たすのは『配車と点呼のデジタル化SaaS』という<b>カテゴリであって、貴社ではない</b>。3社相見積が規程で決まっている当社に、<b>なぜ貴社かが一行もない</b>」（3PL・本部長）／閉じる一言は「これ、<b>御社じゃなくても成り立つ話だよね</b>」</p>
    <p class="kv" style="color:#5E1F1F;margin-bottom:0"><b style="color:var(--crim)">機序</b>第3版の適用範囲宣言は「相見積でのカテゴリ内比較は本モデルの範囲外」としていた。だが<b>B1（購買部門の独立審査）が立つセルでは、範囲外にすると⑥が必ず破綻する</b>。宣言で逃げられない。⑥の要件に「カテゴリ内で自社が残る根拠」を追加する必要がある</p>
  </div>

  <div class="card" style="margin-bottom:14px;border-color:var(--ochre-line);background:var(--ochre-soft)">
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:8px"><span class="sevtag m">重大</span><span class="mono">R7／D6b</span></div>
    <h3 style="font-family:var(--fd);font-size:19px;line-height:1.6;margin-bottom:10px;color:#6B4C0C">A3. R7は「拘束に掛かっていないこと」しか要求せず、その実数を要求していない</h3>
    <p class="kv" style="color:#6B4C0C"><b style="color:var(--ochre)">買い手の声</b>「<b>母数で他社の手段を否定した以上、自分の母数を出さないなら</b>、11月28日は約束ではなくただの願望だ。うちの商圏内に、大型を握って現在走っていて、御社が接触できる人間が何人いるのか」（中小運送・社長）</p>
    <p class="kv" style="color:#6B4C0C;margin-bottom:0"><b style="color:var(--ochre)">機序</b>R7 は ¬blocked(δ(M_i), seller, Q) を要求するが、これは<b>真偽の主張であって量の提示ではない</b>。D6b（市場に供給が存在しない）で消去した場合、⑥に<b>自社の供給量の実数</b>（接触可能母数・直近の接触→面接→入社の実績）が必須になる。R7を量の要件へ強化する</p>
  </div>

  <div class="card" style="border-color:var(--ochre-line);background:var(--ochre-soft)">
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:8px"><span class="sevtag m">重大</span><span class="mono">⑥／②との整合</span></div>
    <h3 style="font-family:var(--fd);font-size:19px;line-height:1.6;margin-bottom:10px;color:#6B4C0C">A4. ⑥が④で立てた問題を再生産し、②で導入した単位を元に戻す</h3>
    <p class="kv" style="color:#6B4C0C"><b style="color:var(--ochre)">買い手の声</b>「④であなた自身が『<b>1年で任期が切れ、翌年また同じ手続を回す。この時間と円は毎年発生します</b>』と書いておきながら、⑥の提案は会計年度任用職員1名に64〜100万円を載せる。<b>あなたが指さした「毎年」を、あなたの商品が最も高い単価で反復させる構造</b>になっている」（公立病院・事務局長）</p>
    <p class="kv" style="color:#6B4C0C;margin-bottom:0"><b style="color:var(--ochre)">機序</b>もう一例——「<b>枠の数で数え直しましょうと2枚目で宣言した資料が、最後に枠を床数に比例配分して戻している</b>」（医療法人・理事長）。②の revisiting で導入した単位が⑥で破棄されている。<b>⑥→④ と ⑥→② の整合検査が形式系に存在しない</b>。定義域の不足</p>
  </div>
</section>

<section class="slide" aria-label="セグメント">
  <p class="eyebrow">04 — セグメントは効いたか</p>
  <h2>同一業種・同一商材で、Σ・J・δ がすべて反転した</h2>
  <table>
    <thead><tr><th style="width:130px">医療 × IT</th><th>公立病院</th><th>医療法人</th></tr></thead>
    <tbody>
      <tr><th scope="row">Σ（縮退）</th><td>S3=あり（随契規程・入札）→ σ_prod=full → σ_read が決定。6段</td><td class="miss">S3=なし → 単価・反復性で判定</td></tr>
      <tr><th scope="row">J（裁定列）</th><td class="bad">n=5（看護部長→事務局→<b>市の情報政策課</b>→契約担当→事業管理者）。κ が2回替わる<b>両替所が2つ</b></td><td class="hit">n=2（事務長→理事長）。<b>理事長が実質単独決裁</b></td></tr>
      <tr><th scope="row">δ（消去次元）</th><td>D5（内製）＋D2（既存外注）＋<b>D6c</b>（市の全庁標準指定）</td><td class="miss">D5＋D2。<b>D6c が消える</b>（取引上位者が存在しない）</td></tr>
      <tr><th scope="row">D4（前例）</th><td class="bad">R4の同型性×実名で<b>落とした</b>（同一都道府県内・300床・全部適用の実名前例なし）</td><td class="miss">—</td></tr>
      <tr><th scope="row">⑥の形</th><td>n=5 ⟹ 結論文・金額・期日・想定質問を<b>座席ごと5問</b>書き切る</td><td class="miss">n=2 ⟹ 簡略</td></tr>
    </tbody>
  </table>
  <div class="cols cols-2" style="margin-top:22px">
    <div class="card" style="border-color:var(--accent-line);background:var(--accent-soft)">
      <h3 style="color:#2F2570">セグメント軸は必要だった</h3>
      <p class="note" style="margin:0;color:#5F55A8">業種既定（医療＝主D3・従D2）は<b>どちらのセグメントでも使われませんでした</b>。D3 は allowed 表上、競合類型にしか立たず、⑤で実際に相手にする内製・既存外注の行に存在しないためです。<b>業種単位で既定を持つ設計が、ここでも破綻している</b>ことが再確認できました。</p>
    </div>
    <div class="card">
      <h3>信頼度機構は設計どおり動いた</h3>
      <p class="note" style="margin:0">8セル全部で δ の判定が<b>「候補提示（営業が2問で確定）」</b>になりました。θ_auto ≒ 1 なので自動採用に落ちない、という §8 の予測どおりです。初期状態では全セルが候補提示から始まる、という設計の確認になります。</p>
    </div>
  </div>
</section>

<section class="slide" aria-label="実物">
  <p class="eyebrow">05 — 生成された48枚 / セルを選ぶ</p>
  <h2 style="margin-bottom:14px">論理式から出た実文</h2>
  <div class="cellbar" id="cellbar"></div>
  <div id="celldetail"></div>
</section>

<section class="slide" aria-label="未踏">
  <p class="eyebrow">06 — 未踏領域</p>
  <h2>モデルが何も言っていない事項</h2>
  <p class="note" style="margin-bottom:16px">生成エージェントに自己申告させたもの。<b>アノマリーではないので修正の対象にしません。</b>被覆範囲の地図として積みます。</p>
  <ul class="plain" id="silent"></ul>
</section>

<section class="slide" aria-label="次">
  <p class="eyebrow">07 — 第5版への差分</p>
  <h2>アノマリー4件から導かれる修正だけ</h2>
  <table>
    <thead><tr><th style="width:150px">対象</th><th>変更</th><th style="width:70px">コスト</th></tr></thead>
    <tbody>
      <tr><th scope="row">now(Q)（形式系）</th><td><b>uncomputed(q) に expressible(q, κ_n) を連言で追加。</b>④で提示する量は、最終裁定点の基準で表現できるものに限る。時間の量しか出せない場合は、円への両替経路（誰の何が減るのか）を同じ枚に書く</td><td><span class="costtag c-s">小</span></td></tr>
      <tr><th scope="row">⑥の要件</th><td><b>B1 が立つとき「カテゴリ内で自社が残る根拠」を必須点灯。</b>適用範囲宣言で「相見積は範囲外」とする逃げを撤回する。⑤がカテゴリまでしか絞れないことは変わらないが、⑥がその先を引き受ける</td><td><span class="costtag c-m">中</span></td></tr>
      <tr><th scope="row">R7</th><td><b>真偽から量へ強化。</b>D6 で消去したら、⑥に自社側の同一指標の実数を必須にする（D6b なら接触可能母数と直近の歩留まり、D6a なら登録番号、D6c なら承認取得実績）</td><td><span class="costtag c-s">小</span></td></tr>
      <tr><th scope="row">整合検査（新設 R10）</th><td><b>⑥→④ と ⑥→② の整合。</b>⑥の提案が④で立てた問題を反復させていないか。②で導入した単位が⑥で保持されているか。いずれも機械判定できる（単位語の一致、反復性の語の検出）</td><td><span class="costtag c-m">中</span></td></tr>
    </tbody>
  </table>
  <p class="note" style="margin-top:20px"><b style="color:var(--ink)">②③の食い違い15件からは何も導きません。</b>あれは生成側が仕様を読み違えたもので、モデルの穴ではありません。予測を先に置かなければ、この15件も「モデルが外した」として数え、直す必要のない箇所を直していたはずです。</p>
</section>

</div>
<nav class="nav" aria-label="スライド操作">
  <button type="button" class="move" id="prev">← 前</button>
  <button type="button" class="move" id="next">次 →</button>
  <div class="dots" id="dots"></div><span class="counter" id="counter"></span>
</nav>
<script>var DATA={DATA_JS};</script>
<script>
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
document.addEventListener('keydown',function(ev){{
  if(ev.target.tagName==='BUTTON'&&(ev.key===' '||ev.key==='Enter'))return;
  if(ev.key==='ArrowRight'){{ev.preventDefault();go(idx+1);}}
  if(ev.key==='ArrowLeft'){{ev.preventDefault();go(idx-1);}}}});
go(0);
function cls(v){{return v==='通過'?'ok':(v==='破綻'?'brk':(v==='揺らぐ'?'wob':'ng'));}}
var cb=document.getElementById('cellbar'),cd=document.getElementById('celldetail'),cc=0;
DATA.cells.forEach(function(c,i){{
  var b=document.createElement('button');b.type='button';b.className='cellbtn';
  var vv=c.stages.map(function(s){{return '<i class="'+(s.o===s.p?'mok':'mng')+'"></i>';}}).join('');
  b.innerHTML=c.ind.split('・')[0]+' '+c.seg+'<span class="sg">'+c.prod.split('：')[0]+'</span><span class="vv">'+vv+'</span>';
  b.addEventListener('click',function(){{cc=i;cr();}});cb.appendChild(b);
}});
var KEYS=['s1','s2','s3','s4','s5','s6'];
function cr(){{
  [].forEach.call(cb.children,function(x,i){{x.setAttribute('aria-pressed',i===cc?'true':'false');}});
  var c=DATA.cells[cc];
  var body=c.stages.map(function(s,i){{
    return '<div class="slidebox '+cls(s.o)+'"><div class="sh"><span>'+s.s+'</span>'+
      '<span class="pv '+cls(s.p)+'">予測 '+s.p+'</span><span class="pv '+cls(s.o)+'">観察 '+s.o+'</span></div>'+
      c.copy[KEYS[i]]+'</div><div class="why"><b>買い手：</b>'+s.w+'</div>';
  }}).join('');
  cd.innerHTML='<div class="mono" style="margin-bottom:10px">'+c.ind+' ／ '+c.seg+' ／ '+c.prod+'</div>'+
    '<p class="note" style="margin-bottom:12px">'+c.segdef+'</p>'+
    '<div class="derivbox"><b>Σ</b>　'+c.sigma+'\\n\\n<b>J</b>　'+c.J+'\\n\\n<b>τ</b>　'+c.tau+'\\n\\n<b>δ</b>　'+c.delta+'\\n\\n<b>発火規則</b>　'+c.rules.join(' ／ ')+'\\n\\n<b>セグメント判定</b>　'+c.segconf+' ／ '+c.segd+'</div>'+
    body+
    '<div class="card" style="margin-top:14px"><h3>最長滞在</h3><p class="note" style="margin:0"><b>予測：</b>'+c.lp+'<br><b>観察：</b>'+c.lo+'</p></div>'+
    '<div class="card" style="margin-top:10px;border-color:var(--crim-line);background:var(--crim-soft)"><h3 style="color:var(--crim)">閉じるときの一言 — 総合：'+c.verdict+'</h3><p style="margin:0;font-family:var(--fd);font-size:17px;line-height:1.75;color:#5E1F1F">「'+c.voice+'」</p></div>';
}}
cr();
var sl=document.getElementById('silent');
DATA.cells.forEach(function(c){{
  (c.silent||[]).slice(0,3).forEach(function(t){{
    var li=document.createElement('li');
    li.innerHTML='<span class="mono">'+c.id+'</span>　'+t;sl.appendChild(li);
  }});
}});
}})();
</script></html>"""
open('e2e-report.html','w').write(H)
print(len(H))
