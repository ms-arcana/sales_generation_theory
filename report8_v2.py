# -*- coding: utf-8 -*-
import json, html

V = json.load(open("verified8_v2.json", encoding="utf-8"))
D = {r["id"]: r for r in json.load(open("decisions8_v2.json", encoding="utf-8"))}
CF = json.load(open("counterfactual_F2P1.json", encoding="utf-8"))
e = html.escape

VC = {"通過": "ok", "揺らぐ": "mid", "棄却": "ng"}

ANOM = [
 ("A5", "⑥に通貨の条件がない", "8/8",
  "第5版は A1 として <code>expressible(q, κ_n)</code> を <b>④にだけ</b>入れた。"
  "8セル全部が⑥で落ち、8人全員が同じことを言った——「金額に直して持ってこい」。"
  "§1.5 は『通貨は階段全体を貫く』と書いてあるのに、形式化が④止まりだった。"
  "<b>A1 の修正が不完全だった</b>ということであり、新しい発見ではなく、前回の直し残しである。",
  "推論規則 (6) に <code>expressible(P, κ_n)</code> を追加する。"
  "⑥は κ_n の基準で読める量（回収年数・粗利の変動・手元資金の増減）を必ず含む。",
  "形式系"),
 ("A6", "R10b と A1 が両立しない", "2/8（明示）",
  "K2-P1 の生成器は R10b（②で数え直した単位を⑥で比例換算して戻すな）を守り、"
  "「円／人日へは割り戻しません」と書いた。買い手（κ_n＝価格）はその一行で終わらせた——"
  "「割り戻せないものは、うちでは値段が付かん」。"
  "<b>規則を守ると中心命題を破る</b>。生成器は自己申告で「換算禁止の射程（併記も禁止か）が判断できなかった」と書いている。",
  "R10b の禁止対象を<b>単位の置換</b>に限定し、<b>併記</b>を明示的に許可する。"
  "さらに A5 の帰結として、κ_n が②の単位と異なるときの併記は<b>必須</b>になる。"
  "「②の単位を保持したまま、κ_n の量を並置する」——保持と両替は排他ではない。",
  "形式系"),
 ("A7", "消去次元が座席構造と無関係に立つ", "3/8",
  "F2（オーナー系中堅、親会社なし）の2セルで、買い手の第一声が「うちに親会社はないよ」だった。"
  "K1-P2 では「当社が元請だ。承認するのはこちら側であって、こちら<b>が</b>承認を待つ側ではない」。"
  "<code>ALLOWED</code> 表は 手段の類型 × 次元 しか見ておらず、"
  "<b>その拘束者が買い手の外側の上位に実在するか</b>を見ていない。D6c は向きを持つ関係なのに、"
  "δ は向きのない集合を返している。",
  "δ の型を <code>δ : M∖{M_0} → P(D)</code> から "
  "<code>δ : M∖{M_0} → P(D × Actor)</code> へ拡張し、"
  "D6a/b/c を立てる条件に <code>∃v ∈ J ∪ V ∪ Upstream. above(v, buyer)</code> を課す。"
  "買い手が拘束<b>する</b>側なら、その次元は使えない。",
  "軸（D軸）"),
 ("A8", "④の日付が「この買い手に効く日か」を検査していない", "3/8",
  "F2-P2「四月一日の線も、六年前に越えてる」。K1-P2「建設に適用されたのは2027年ではなく2024年4月1日だ」。"
  "K2-P1「どの元請の話だ。うちは元請が複数あって、審査の窓もばらばらだ」。"
  "外部性の3条件（制御不能・撤回不能・未計算の量）も出典階層も既知度も全部通したうえで、"
  "<b>その日付が当該買い手に適用されるか</b>だけが検査されていない。"
  "出典階層は「誰が決めた日か」を見るが「誰に効く日か」を見ていない。",
  "T軸の必須フィールドに <b>適用対象</b>（業種・規模・区分・当事者の同定）を追加し、"
  "<code>applies(d, buyer)</code> を <code>now(Q)</code> の連言に入れる。"
  "拘束者が複数いる場合（元請が複数）は、日付が一意に定まらないので、"
  "当事者を同定するまで④は立たない。",
  "軸（T軸）"),
 ("A9", "③で名づけた対象と⑥が消す対象の同一性が検査されていない", "3/8",
  "F1-P1 が最も鋭い——「この装置が消すのは盛付や持ち替えといった定常作業であって、"
  "②で数えた『立ち上がりが安定するまでの上乗せ』の中身は品質確認・手直し・ライン調整・洗浄立ち上げだ。"
  "<b>数えた人日と装置が置き換える人日が同じ集合だという説明がどこにもない</b>」。"
  "R10 は単位と周期を検査するが<b>外延</b>を検査しない。推論規則 (6) は "
  "<code>P ∈ C</code> と無矛盾性しか要求せず、<code>resolve</code> の Q が③の Q と"
  "同じ集合を指すことは<b>仮定されているだけ</b>である。",
  "推論規則 (6) に <code>ext(covered(P)) ⊆ ext(Q)</code> と、"
  "その被覆率を⑥で開示する条件を加える。⑥に「④で数えた量のうち、本提案が消すのはどの部分か」の"
  "対応表を必須ブロックとして点灯させる。",
  "形式系"),
 ("A10", "縮退で段を落としたとき、残った段の前提が未定義", "2/8＋生成器の自己申告2件",
  "①を落とした F1-P1 の②は「①でお示ししたのは」で始まった。存在しない枚を参照している。"
  "生成器は自己申告で「①の内容が与えられていないため、②の『同じ材料』を推定して置いた。"
  "①が別の材料を置いていた場合、②の数え直しは接続しない」と書いている。"
  "推論規則 (2) の側条件 <code>facts_2 ⊆ facts_1</code> は①の存在を前提にしており、"
  "<b>σ が①を落とすと側条件の定義域が空になる</b>。",
  "σ が段 s を落としたとき、s が供給していた Γ を「買い手が既に承認済みの前提」として"
  "外から与える規則を書く。落とした段は<b>消えるのではなく、資料の外で既に成立している</b>という扱いにする。"
  "Declared の定義域も同時に縮む（②を作らなければ s2_unit は未定義であって空文字ではない）。",
  "形式系"),
 ("A11", "名づけ（③）は移送で消える", "2/8",
  "F1-P1「調達本部の様式に〈切替こぼれ〉と書いた瞬間、『その科目は何か』で止まる。"
  "<b>社内の会話では使う、対外文書では使わない</b>」。"
  "F1-P2「持ち月って言葉は、うちの会議じゃ通らん。45時間超月数に直してくれ」。"
  "どちらも③の内容そのものは「正確だ」と認めたうえで、<b>語として運べない</b>と言っている。"
  "移送関数 <code>T_{k→k+1}</code> は Γ の命題を濾すが、"
  "<b>語彙が濾されること</b>を規定していない。§1.2 の減衰は、承認の減衰としてしか書かれていなかった。",
  "§1.2 に書き足す——<b>減衰するのは承認だけではない。語彙も減衰する。</b>"
  "新語は起案者の座席までしか運べず、そこから先は既存の科目名へ翻訳されるか、消える。"
  "③には<b>新語と、κ_n の座席の様式に既にある語との対応</b>を併記する条件を課す。",
  "中心命題（§1.2）"),
]

IMPL = [
 ("R10a の 0 の扱い", "6件を誤検出",
  "<code>s6_period_months = 0</code>（単発）が <code>0 ≤ 6</code> で「④の問題を⑥が反復させている」と判定されていた。"
  "0 を「反復しない」と「即座に反復する」の両方に使っていた型の誤り。"
  "<b>本走行で修正済み</b>（<code>R10a_NOT_PERIODIC</code> を新設）。誤検出6件がすべて消えた。"),
 ("R7 が件数しか検査していない", "3/8",
  "第4版 A3 の修正表は D6c に「承認取得実績<b>と</b>承認リードタイムの実測」の2つを要求しているのに、"
  "<code>Seller</code> 型にリードタイムのフィールドがなく、"
  "<code>check_R7</code> は <code>upstream_approvals &gt; 0</code> だけで OK を返していた。"
  "生成器3体が「実測日数の値が与えられていない」と自己申告し、うち2体は捏造を避けて欠落を開示した。"
  "<b>形式系は正しく、実装が半分だった。</b>"),
 ("τ 内の日付どうしの整合が未検査", "1/8（生成器の自己申告）",
  "K2-P2 に C（着手期限 2027-06-30）と A（終端日 2027-04-01）が同居し、"
  "生成器が「逆算の関係が成り立たない」と気づいた。"
  "<code>check_tau</code> は各項を個別に検査するだけで、項<b>間</b>の順序関係を見ていない。機械判定できる。"),
]

UNTOUCHED = [
 ("⑤に挙げる手段の完全性を誰が決めるか",
  "F1-P1「うちには他工場・他ラインからの<b>グループ内応援</b>という三つ目の選択肢があり、"
  "外部支出ゼロのその案が調達本部の第一候補になる。それを潰していない以上、"
  "『内製も派遣も成立しない』という詰め方は私の中では完結しない」。"
  "⑤は <code>∀M_i ∈ M∖{M_0}</code> を要求するが、M の同定主体が規定されていない。"
  "人間記入スロットは⑥にしかなく、⑤にはない。"),
 ("最も保守的な一人 と 資料を読まない最終裁定者 の関係",
  "生成器が明示的に「規定から決められなかった」と書いた唯一の点。"
  "B3（可搬層は最も保守的な一人の基準で）と、κ_n（＝資料を読まない座席）と、"
  "j*（＝読む中で最も遠い座席）の三者関係が未規定。生成器は j* を採る解釈で走った。"),
 ("段と枚の対応が 1:1 と暗黙に仮定されている",
  "4セルで⑥の字数が破綻した（超過または必須要素の圧縮）。"
  "<code>blocks_on</code> は段にブロックを割り当てるが、"
  "1段が何枚になるかを規定していない。⑥が1枚である必然性はどこにもない。"),
 ("検収・返金・不承認時の扱いが必須要素にない",
  "F2-P1「判断して駄目だったら金は戻るのか」。K2-P1「元請の安管が『柵なしは認めない』と言った時、"
  "この1,200万〜2,800万は誰が持つのか。返金なのか、引き取りなのか」。"
  "3人が同じことを訊いた。⑥のブロック一覧に該当する項目がない。"),
]

KEEP = [
 ("提示語彙の分離（R9）", "36枚／漏洩 0",
  "前回に続き、分析語彙の本文への漏洩はゼロ。形式系を生成器に渡さず、"
  "段ごとに提示形態だけを指定する設計は、業界を替えても効いた。"),
 ("責任分界表（D2）", "3セルで名指しの評価",
  "F1-P1「この五枚で一番良いのは責任分界の表だ。相見積様式の責任範囲欄にそのまま写せる形で来た資料は、"
  "正直ここ数年ほとんどない」。K1-P1「責任分界表、この5行を御社の名前で埋めて、もう一度持ってきてください。"
  "話はそこからです」。⑤の次元のうち D2 が最も強い。"),
 ("V（決裁権なき拒否権）を売り手から先に開示する", "K2-P1",
  "「特に、<b>元請の安管が首を振ったら終わりだと、そっちから先に言った</b>ところは信用した」。"
  "第4版で V を導入した判断の直接の裏付け。ただし K2-P2 は「あの人が何て言えば通るのかを"
  "先に調べてから来い。順番が逆なんだよ」と、V を<b>開示するだけでは足りない</b>ことも示した。"),
 ("無矛盾性（§1.1・爆発律）", "K2-P2",
  "「40〜70日ってのがどこから出たのか説明できないなら、"
  "<b>その一行があるだけで残り全部が疑わしくなる</b>」。"
  "説明できない量ひとつが Γ 全体を落とす、という第5版の追加が、そのままの形で観察された。"),
 ("③の現象記述", "4セルで「正確だ」",
  "名づけの<b>中身</b>は一貫して認められた。落ちたのは語の運搬（A11）であって、casing の失敗ではない。"),
]


def slides_html(r):
    out = []
    for s in r["sigma"]:
        t = r["copy"].get(s, "")
        v = r["obs"].get(s, "")
        w = r["obs_why"].get(s, "")
        p = r["pred"].get(s, "")
        out.append(f"""<div class="slide">
<div class="sh"><span class="stg">{s}</span>
<span class="vb {VC.get(v,'')}">{e(v or '—')}</span>
<span class="pred">予測 {e(p or '—')}</span></div>
<div class="body">{e(t).replace(chr(10),'<br>')}</div>
<div class="react"><b>買い手：</b>{e(w)}</div></div>""")
    return "\n".join(out)


cells = []
for r in V:
    d = D[r["id"]]
    stops = [f for f in r["post_findings"] if f["level"] == "stop"]
    cells.append(f"""<section class="cell">
<h3>{e(r['id'])}　{e(r['業界'])}／{e(r['セグメント'])}／{e(r['商材'])}</h3>
<table class="meta"><tr><th>Σ（縮退後の段）</th><td>{'・'.join(r['sigma'])}　<span class="dim">σ_read（買い手の状態から）</span></td></tr>
<tr><th>κ_n（最終裁定点の基準）</th><td>{'・'.join(r['kappa_n'])}</td></tr>
<tr><th>座席</th><td>{e(' → '.join(s['name']+('（読まない）' if not s['reads'] else '') for s in d['seats']))}
{('　拒否権：'+e(d['veto'][0])) if d['veto'] else ''}</td></tr>
<tr><th>使った日付</th><td>{e('／'.join(f"{t[1]}（{t[0]}・{t[2]}・{t[3]}）" for t in d['tau_ok']))}</td></tr>
<tr><th>⑤で落とす手段</th><td>{e('／'.join(d['five_mentions']))}</td></tr>
<tr><th>生成前の検査</th><td>{e('／'.join(f"{f['code']}" for f in d['findings'] if f['level']!='info') or '棄却なし')}</td></tr>
<tr><th>生成後の検査</th><td>{e('／'.join(f['code'] for f in stops) or 'clean')}</td></tr>
</table>
{slides_html(r)}
<div class="close"><b>閉じる一言</b><p>{e(r['closing_line'])}</p>
<b>資料が答えていない問い</b><p>{e(r['unanswered'])}</p>
<b>上申するか</b><p>{'する' if r['would_forward'] else '<span class="ng2">しない</span>'}</p></div>
</section>""")

anom = "\n".join(f"""<div class="an"><h3><span class="tag">{a[0]}</span>{e(a[1])}
<span class="rep">{e(a[2])}</span><span class="scope">{e(a[5])}</span></h3>
<p class="mech">{a[3]}</p><p class="fix"><b>修正</b>　{a[4]}</p></div>""" for a in ANOM)

impl = "\n".join(f"""<div class="an im"><h3>{e(x[0])}<span class="rep">{e(x[1])}</span></h3>
<p class="mech">{x[2]}</p></div>""" for x in IMPL)

unt = "\n".join(f"""<div class="an ut"><h3>{e(x[0])}</h3><p class="mech">{x[1]}</p></div>""" for x in UNTOUCHED)

keep = "\n".join(f"""<div class="an kp"><h3>{e(x[0])}<span class="rep">{e(x[1])}</span></h3>
<p class="mech">{x[2]}</p></div>""" for x in KEEP)

n = len(V)
tot = sum(len(r["sigma"]) for r in V)
agree = tot - sum(len(r["diff"]) for r in V)
long_hit = sum(1 for r in V if r["pred_longest"] == r["obs_longest"])
cnt = {"通過": 0, "揺らぐ": 0, "棄却": 0}
for r in V:
    for v_ in r["obs"].values():
        cnt[v_] = cnt.get(v_, 0) + 1

summary_rows = "\n".join(
    f"<tr><td>{e(r['id'])}</td><td>{e(r['業界'])}</td><td>{e(r['セグメント'])}</td>"
    f"<td>{e(r['商材'])}</td><td>{'・'.join(r['sigma'])}</td>"
    f"<td>{'・'.join(r['kappa_n'])}</td><td>{e(r['pred_longest'])}</td>"
    f"<td>{e(r['obs_longest'])}</td>"
    f"<td class='{'ng2' if not r['would_forward'] else ''}'>{'する' if r['would_forward'] else 'しない'}</td></tr>"
    for r in V)

HTML = f"""<!doctype html><html lang="ja"><meta charset="utf-8">
<title>第5版 形式系の実運用 ―― 食品メーカー／建設・設備工事 8セル検証</title>
<style>
:root{{--ink:#1a1a1a;--dim:#6b6b6b;--line:#e0ddd6;--bg:#faf9f6;--ok:#2f6f4e;--mid:#8a6d1f;--ng:#993326;--acc:#2a4d69}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font-family:"Hiragino Mincho ProN","Yu Mincho",serif;line-height:1.85;font-size:15.5px}}
.wrap{{max-width:960px;margin:0 auto;padding:48px 24px 96px}}
h1{{font-size:26px;line-height:1.5;margin:0 0 6px;letter-spacing:.02em}}
.sub{{color:var(--dim);font-size:13.5px;margin-bottom:36px}}
h2{{font-size:19px;margin:56px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--ink)}}
h3{{font-size:16px;margin:26px 0 8px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0}}
th,td{{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#f2efe8;font-weight:600;white-space:nowrap}}
.meta th{{width:170px}}
.dim{{color:var(--dim);font-size:12px}}
.kpi{{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0 8px}}
.kpi div{{flex:1;min-width:150px;border:1px solid var(--line);background:#fff;padding:14px 16px}}
.kpi b{{display:block;font-size:27px;line-height:1.2;font-family:Georgia,serif}}
.kpi span{{font-size:12.5px;color:var(--dim)}}
.cell{{border:1px solid var(--line);background:#fff;padding:22px 24px;margin:26px 0}}
.slide{{border-left:3px solid var(--line);padding:8px 0 8px 16px;margin:16px 0}}
.sh{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.stg{{font-size:19px;font-weight:700}}
.vb{{font-size:12px;padding:2px 9px;border-radius:2px;color:#fff;background:var(--dim)}}
.vb.ok{{background:var(--ok)}}.vb.mid{{background:var(--mid)}}.vb.ng{{background:var(--ng)}}
.pred{{font-size:12px;color:var(--dim)}}
.body{{font-size:14.5px}}
.react{{margin-top:8px;font-size:13.5px;background:#f7f5f0;padding:10px 12px;color:#333}}
.close{{margin-top:20px;border-top:1px dashed var(--line);padding-top:14px;font-size:13.5px}}
.close p{{margin:4px 0 12px}}
.ng2{{color:var(--ng);font-weight:700}}
.an{{border:1px solid var(--line);border-left:4px solid var(--ng);background:#fff;padding:16px 20px;margin:16px 0}}
.an.im{{border-left-color:var(--acc)}}.an.ut{{border-left-color:var(--dim)}}.an.kp{{border-left-color:var(--ok)}}
.tag{{display:inline-block;background:var(--ng);color:#fff;font-size:12px;padding:1px 8px;margin-right:8px;
font-family:Georgia,serif}}
.rep{{float:right;font-size:12px;color:var(--dim);font-weight:400}}
.scope{{float:right;font-size:11.5px;color:#fff;background:var(--acc);padding:1px 8px;margin-right:10px}}
.mech{{font-size:14px;margin:8px 0}}
.fix{{font-size:14px;background:#f4f6f8;padding:10px 12px;margin:10px 0 0}}
code{{font-family:"SF Mono",Menlo,monospace;font-size:12.5px;background:#f0ede6;padding:1px 4px}}
.note{{font-size:13.5px;color:#444;background:#fff;border:1px solid var(--line);padding:14px 18px;margin:14px 0}}
</style>
<div class="wrap">
<h1>第5版 形式系の実運用<br>食品メーカー／建設・設備工事 ―― 2業界 × 2買い手セグメント × 2商材</h1>
<div class="sub">2026-08-06 基準日。中心命題・軸・形式系（SPEC.md）から <code>sales_logic.py</code> が決定を算出し、
その決定<b>だけ</b>を提示仕様に翻訳して36枚を生成。予測を見ていない買い手8体が盲検で読んだ。</div>

<div class="kpi">
<div><b>{cnt['通過']}／{cnt['揺らぐ']}／{cnt['棄却']}</b><span>通過／揺らぐ／棄却（全{tot}枚）</span></div>
<div><b>0／8</b><span>最終裁定点へ上申された</span></div>
<div><b>0／36</b><span>分析語彙の漏洩（R9）</span></div>
<div><b>{long_hit}／{n}</b><span>最長滞在段の予測的中</span></div>
<div><b>{agree}／{tot}</b><span>段ごとの予測一致</span></div>
</div>

<div class="note"><b>この走行の位置づけ。</b>
前回（医療・物流）で見つかった A1〜A4 を第5版に取り込んだうえで、<b>業界も商材も全部入れ替えて</b>回した。
狙いは「直した箇所が別の業界でも効くか」と「直し方が正しかったか」の二つ。
結論から言うと、<b>R9 は効いた（漏洩ゼロを再現）が、A1 の直し方は段を間違えていた</b>。
8セル全部が⑥で落ち、8人が同じ一言を言った。</div>

<h2>1. 8セルの設定と結果</h2>
<table><tr><th>ID</th><th>業界</th><th>セグメント</th><th>商材</th><th>Σ</th><th>κ_n</th>
<th>予測最長</th><th>観察最長</th><th>上申</th></tr>
{summary_rows}</table>
<p class="dim">Σ はすべて σ_read で決まった（S1 が高額帯のため σ_prod は full を返す）。
同一業界・同一商材でもセグメントが変われば Σ・κ_n・δ がすべて動いている。</p>

<div class="note"><b>生成前に1件を止めた。</b>
F2-P1 で「棚替えに伴う増員工数（人日）」を κ_n＝{{価格, 財源}} の社長へそのまま出す設定にすると、
<code>A1_NOT_EXPRESSIBLE</code> で<b>生成に入る前に停止する</b>（{e(str(CF['generate']))}）。
両替経路を同じ枚に書く指定に変えて初めて通った。この検査は<b>正しく働いた</b>——
ただし後述の A5 のとおり、同じ検査が⑥にはない。</div>

<h2>2. アノマリー ―― 理論・軸・形式系の修正を導くもの</h2>
<p>判定の基準：形式系が「通る」と判定したのに買い手が落とし、かつ原因が
<b>述語の欠落・型の誤り・定義域の不足</b>にあるもの。生成器が仕様を読み違えただけのものは含めない。</p>
{anom}

<h2>3. 実装の穴 ―― 形式系は正しく、Python が追いついていないもの</h2>
{impl}

<h2>4. 未踏 ―― 記録するが、今回は修正しない</h2>
{unt}

<h2>5. 変更しない部分 ―― 裏付けられたもの</h2>
{keep}

<h2>6. 予測が外れたことについて</h2>
<div class="note">
最長滞在段の予測的中は {long_hit}/{n}、段ごとの一致は {agree}/{tot}。前回（8/8 的中）から大きく落ちた。
原因は買い手側にある——<b>今回の買い手は数字を実際に検算した</b>。
「上限の260人日、年二回、応援の人日単価2万円で見ても年間1,040万円。標準構成1,200〜2,800万円なら回収は四年から十年」
（F1-P1）のように、売り手が出した量を自分の物差しで割り戻し、投資回収基準と突き合わせている。
生成器の予測にはこの検算が織り込まれていない。<br><br>
これはモデルの穴ではなく<b>測定手順の欠陥</b>である。生成器に自分の書いたものの通過可否を予測させると、
系統的に楽観へ寄る。次回からは<b>予測を第三のエージェントに出させる</b>。
なお、予測を先に置いたこと自体は今回も効いている——予測がなければ、
「⑥で全部落ちた」を「買い手が厳しかった」で片付けていた。
</div>

<h2>7. 8セルの本文と反応</h2>
{''.join(cells)}

</div></html>"""

open("report8_v2.html", "w", encoding="utf-8").write(HTML)
print("written", len(HTML), "bytes")
