import json, html
D = json.load(open('v.json'))
S = D['syn']
DATA_JS = json.dumps(D, ensure_ascii=False)
def e(x): return html.escape(str(x))

gaps = ""
for g in S['confirmed_gaps']:
    sev = 'f' if g['severity'] == '致命' else 'm'
    gaps += f"""<article class="gap" data-sev="{e(g['severity'])}" style="display:none">
<div class="card" style="margin-bottom:14px">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
    <span class="sevtag {sev}">{e(g['severity'])}</span>
    <span class="mono">{e(g['axis'])}</span>
  </div>
  <h3 style="font-family:var(--fd);font-size:20px;line-height:1.55;margin-bottom:12px">{e(g['title'])}</h3>
  <p class="kv"><b>機序</b>{e(g['mechanism'])}</p>
  <p class="kv"><b>影響</b>{e(g['affected'])}</p>
  <p class="kv" style="margin-bottom:0"><b>修正案</b>{e(g['fix'])}</p>
</div></article>"""

prods = ""
for p in S['product_findings']:
    prods += f"""<article class="pf" style="display:none">
<div class="panel">
  <div class="ph">{e(p['product'])}</div>
  <div class="logic">{e(p['verdict'])}</div>
  <p class="kv"><b>構造</b>{e(p['finding'])}</p>
  <p class="kv"><b>支配的な消去次元</b>{e(p['dominant_d'])}</p>
  <p class="kv" style="margin-bottom:0"><b>支配的な「今」の形式</b>{e(p['dominant_t'])}</p>
</div></article>"""

clusters = ""
for c in S['industry_clusters']:
    clusters += f"""<div class="card" style="margin-bottom:14px">
  <h3 style="font-family:var(--fd);font-size:18px;margin-bottom:8px">{e(c['name'])}</h3>
  <div class="cellchips">{''.join('<span>%s</span>' % e(i) for i in c['industries'])}</div>
  <p class="kv" style="margin-top:12px"><b>性格</b>{e(c['character'])}</p>
  <p class="kv" style="margin-bottom:0"><b>効くもの</b>{e(c['what_works'])}</p>
</div>"""

changes = ""
for c in S['proposed_changes']:
    cls = {'小': 'c-s', '中': 'c-m', '大': 'c-l'}[c['cost']]
    changes += f"""<tr><th scope="row">{e(c['target'])}</th><td>{e(c['change'])}</td>
<td class="miss">{e(c['why'])}</td><td><span class="costtag {cls}">{e(c['cost'])}</span></td></tr>"""

opens = "".join("<li>%s</li>" % e(q) for q in S['open_questions'])
cv = S['coverage']

CSS = open('css25.css').read()

H = f"""<!doctype html>
<html lang="ja">
<meta charset="utf-8">
<title>25業種 × 5商材 検証レポート</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>

<div class="stage">

<section class="slide is-active" aria-label="表紙">
  <p class="eyebrow">検証レポート / 2026-08-06 / リクナビ25業種 × 5商材</p>
  <h1>モデルは業種ではなく、<br>商材で割れた</h1>
  <p class="lead">{e(S['headline'])}</p>
  <div class="title-meta">
    <span>125通り検証</span><span>妥当 {cv['ok']}</span><span>条件付き {cv['conditional']}</span><span>不成立 {cv['fail']}</span>
    <span>総合：{e(S['overall_verdict'])}</span><span>全10枚</span>
  </div>
</section>

<section class="slide" aria-label="分布">
  <p class="eyebrow">01 — 何が起きたか</p>
  <h2>全滅した業種はゼロ。全滅した商材は1つ</h2>
  <div class="bars" id="bars"></div>
  <p class="kv" style="margin-top:22px"><b>分布の読み</b>{e(cv['summary'])}</p>
</section>

<section class="slide" aria-label="商材別">
  <p class="eyebrow">02 — 商材別 / タブで切替</p>
  <h2 style="margin-bottom:16px">同じ階段が、商材によって別物になる</h2>
  <div class="tabs" id="ptabs"></div>
  <div id="plist">{prods}</div>
</section>

<section class="slide" aria-label="クラスタ">
  <p class="eyebrow">03 — 業種は4群に分かれた</p>
  <h2>業種分類ではなく、モデルの効き方による分類</h2>
  {clusters}
</section>

<section class="slide" aria-label="確定した穴">
  <p class="eyebrow">04 — 確定した穴 {len(S['confirmed_gaps'])}件</p>
  <h2 style="margin-bottom:16px">業種横断で反復したものだけ</h2>
  <div class="chips" id="gchips"></div>
  <div id="glist">{gaps}</div>
</section>

<section class="slide" aria-label="アブダクティブ再読">
  <p class="eyebrow">05 — アブダクティブ分析による再読</p>
  <h2>予測が外れた方向に、意味がある</h2>
  <div class="cols cols-2" style="margin-bottom:22px">
    <div class="card">
      <h3>A1：形式が無いのに妥当だった — <span style="font-family:var(--fm);color:var(--accent)">0件</span></h3>
      <p class="note" style="margin:0">T軸の形式が実在しないと判定した業種で、それでも④が立った例はゼロ。<b style="color:var(--ink)">T軸の被覆は、少なくとも過小ではない。</b>5形式で足りている側の証拠。</p>
    </div>
    <div class="card" style="border-color:var(--crim-line);background:var(--crim-soft)">
      <h3 style="color:var(--crim)">A2：形式はあるのに不成立 — <span style="font-family:var(--fm)">20件</span></h3>
      <p class="note" style="margin:0;color:#5E1F1F">しかも20件すべてがオフィス用品。<b>T軸の存在は業種の性質だが、使えるかどうかは（業種 × 商材）の性質だった。</b>既定値を業種で保持する設計の破綻が、ここに数字として出た。</p>
    </div>
  </div>
  <p class="pull" style="max-width:60ch">④の暦（入所日と納期）は事務局長が売り手より正確に把握しており、指差した瞬間に承認ではなく『それは知っています』が返る。</p>
  <div class="card" style="border-color:var(--accent-line);background:var(--accent-soft)">
    <h3 style="color:#2F2570">アブダクティブ分析が、この破綻を先に説明していた</h3>
    <p style="margin:0;font-size:15.5px;line-height:1.88;color:#2F2570">Timmermans &amp; Tavory：<b>「既存の理論が経験的現象を完全に説明してしまうなら、研究者は単に既存理論を検証したにすぎない」</b>。私はこれを②の棄却条件として実装しました——買い手の既存の枠組みで完全に説明できる②は、①の言い換えである、と。<br><br>今回の20件が示したのは、<b>同じことが④にも起きる</b>ということです。買い手が既に手帳に書いている暦を指差す④は、承認を生まず「それは知っています」を生む。つまり<b>④にも verification と abduction の区別が要る</b>。「暦は外から」という私の定式は、外部性の基準を〈制度かどうか〉に置いた点で誤っていました。正しい基準は〈買い手の意思で撤回できないか〉＋〈買い手がまだ計算していない量を伴うか〉です。</p>
  </div>
</section>

<section class="slide" aria-label="中心命題の訂正">
  <p class="eyebrow">06 — 中心命題の訂正</p>
  <h2>「暦は外から」は、二方向に誤っていた</h2>
  <div class="asym">
    <div>
      <div class="t">狭すぎた</div>
      <div class="s">制度以外の硬い暦を排除していた</div>
      <p>買い手が動かせない暦の多くは制度ではない。自然暦（作物暦・漁期・農繁期・積雪）、需要曲線（宿泊の予約リードタイム、52週販促カレンダー、公演日と発売日）、契約暦（リース満了、年間契約更改、元請協定、指定管理の期間満了）。<b>在庫が固定であるぶん、日付の精度はむしろ制度暦より高い。</b></p>
    </div>
    <div>
      <div class="t">広すぎた</div>
      <div class="s">制度暦でも復唱になる場合がある</div>
      <p>買い手がその制度の<b>実施主体</b>である場合（金融・官公庁・教育・福祉・製薬の薬価）、暦が買い手自身の年度サイクルである場合、④は承認済み命題の復唱になり資本を生まない。加えて売り手都合の日付（媒体の入稿締切、値上げ通知日、自社工程表からの逆算）は形式要件を満たしてしまい、検出できない。</p>
    </div>
  </div>
  <div class="card" style="border-color:var(--ochre-line);background:var(--ochre-soft)">
    <div class="mono" style="color:var(--ochre);margin-bottom:8px">改訂後</div>
    <p style="margin:0 0 10px;font-family:var(--fd);font-size:21px;line-height:1.6;font-weight:700;color:#6B4C0C">暦は、買い手の意思の外から。かつ、買い手がまだ計算していない量とともに。</p>
    <p class="note" style="margin:0;color:#6B4C0C">外部性の判定を3条件へ：(i) 買い手の意思で動かせないか (ii) 発表主体が一者の意思で撤回できないか (iii) 買い手が未だ計算していない量を伴うか。<br><b>実際に機能した④は例外なく、日付そのものではなく買い手が計算していない量（並走検証12か月、次の窓まで12か月、着手期限日）を同時に持ち込んでいた。</b></p>
  </div>
</section>

<section class="slide" aria-label="モデル改訂">
  <p class="eyebrow">07 — 提案する改訂</p>
  <h2>軸を1本足し、既定値の持ち方を変える</h2>
  <table>
    <thead><tr><th style="width:170px">対象</th><th>変更</th><th>理由</th><th style="width:60px">コスト</th></tr></thead>
    <tbody>{changes}</tbody>
  </table>
</section>

<section class="slide" aria-label="D6">
  <p class="eyebrow">08 — 唯一の新設次元</p>
  <h2>D6 第三者拘束 ―― 二項世界の外に拘束がある</h2>
  <p style="max-width:64ch">D1〜D5は拘束の所在を〈手段の内部／手段と買い手の関係／買い手の内部〉に置いており、<b>売り手と買い手の二項で閉じた世界</b>を前提にしていました。ところが検証では、拘束が第三者に所在する型が3系統、多数業種で反復しました。</p>
  <div class="cols cols-3" style="margin-bottom:20px">
    <div class="card"><h3>(a) 制度が行為・主体を許さない</h3><p class="note" style="margin:0">保険業法275条の無登録募集、弁護士法72条と守秘義務、派遣法4条の警備、外為法のみなし輸出、専任宅建士・主任技術者・整備主任者の法定設置。<br><b style="color:var(--ink)">効く証拠</b>：登録・免許・認定の保有と条文照合<br><b style="color:var(--crim)">効かない</b>：責任分界表、他社実績</p></div>
    <div class="card"><h3>(b) 市場に供給が存在しない</h3><p class="note" style="margin:0">地方工場の技能工、大型・二種免許保有者、宿泊業の季節スタッフ、CRA・登録販売者の母数。<br><b style="color:var(--ink)">効く証拠</b>：需給統計と、売り手が持つ別チャネル（外国人材・他商圏・Uターン層）<br><b style="color:var(--crim)">効かない</b>：手段の性能比較</p></div>
    <div class="card"><h3>(c) 取引上位者が決定権を持つ</h3><p class="note" style="margin:0">川下OEMの4M変更承認、元請ゼネコンの指定システム、小売本部の帳合・口座、系列規範、指定管理の設置者。<br><b style="color:var(--ink)">効く証拠</b>：上位者の承認取得実績、受入仕様適合証明、承認リードタイム実績<br><b style="color:var(--crim)">効かない</b>：買い手向けROI</p></div>
  </div>
  <div class="card" style="border-color:var(--crim-line);background:var(--crim-soft)">
    <h3 style="color:var(--crim)">D6には自己適用検査を義務づける</h3>
    <p class="note" style="margin:0;color:#5E1F1F">航空宇宙と人材サービスで、<b>⑤の消去がそのまま⑥を自己消去する</b>事例が観測されました。「市場に人がいない」で既存手段を消すと、買い手は即座に「では御社も同じ市場から供給しているのでは」と返す。<b>D6を選んだら、⑥の手前に「提案主体自身が同じ拘束を通過するか」の検査を必須にする。</b></p>
  </div>
</section>

<section class="slide" aria-label="業種マトリクス">
  <p class="eyebrow">09 — 全125通り / 業種を選ぶと内訳が出る</p>
  <h2 style="margin-bottom:14px">生成された④⑤の実文を見る</h2>
  <div class="indgrid" id="indgrid"></div>
  <div class="detail" id="inddetail"></div>
</section>

<section class="slide" aria-label="判断">
  <p class="eyebrow">10 — 判断を仰ぎたいこと</p>
  <h2>次に決めたい{len(S['open_questions'])}点</h2>
  <ul class="plain">{opens}</ul>
</section>

</div>

<nav class="nav" aria-label="スライド操作">
  <button type="button" class="move" id="prev">← 前</button>
  <button type="button" class="move" id="next">次 →</button>
  <div class="dots" id="dots"></div>
  <span class="counter" id="counter"></span>
</nav>

<script>var DATA={DATA_JS};</script>
<script>{open('app25.js').read()}</script>
</html>"""
open('industry25-report.html', 'w').write(H)
print(len(H))
