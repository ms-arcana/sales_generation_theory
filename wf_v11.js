export const meta = {
  name: 'arm3-compliance-v11',
  description: '提示仕様のアーム3本を、同じ8セルで生成し、仕様の遵守だけを測る（買い手は使わない）',
  phases: [
    { title: 'Arm0', detail: '共通修正のみ（ベースライン）8セル' },
    { title: 'Arm1', detail: 'Arm0 ＋ ⑥の枚仕様に座席ごとの列挙 ＋ 申告欄 8セル' },
    { title: 'Arm2', detail: 'Arm1 ＋ ⑥の字数 700〜900字と表の許可 8セル' },
  ],
}

// 第12版のスキーマ。第10版からの差分は2つだけ。
//   s6_realize        … 〈誰が・いつ・どの費目〉の組の配列（A24：行為は集合である）
//   s6_kappa_by_seat  … 〈座席名・基準〉の組の配列（A23：⑥の量は座席ごとの組である）
// どちらも required に入れない。**入れたかどうか自体が測定対象**だから。
const GEN_SCHEMA = {
  type: 'object',
  required: ['cell_id', 'arm', 'slides', 'declared', 'self_report'],
  properties: {
    cell_id: { type: 'string' },
    arm: { type: 'integer' },
    slides: {
      type: 'array',
      items: {
        type: 'object',
        required: ['stage', 'text'],
        properties: { stage: { type: 'string' }, text: { type: 'string' } },
      },
    },
    declared: {
      type: 'object',
      required: ['s5_is_constraint_disclosure', 's6_ends_imperative', 's6_contains_promise',
                 's6_kappa', 's6_kappa_type', 's5_denies_own'],
      properties: {
        s2_unit: { type: ['string', 'null'], description: '②で導入した単位語。②を書いていなければ null' },
        s2_from_unit: { type: ['string', 'null'], description: '②で数え直す前の単位語' },
        s3_form_mapping: { type: ['string', 'null'], description: '③の新語と、資料を読む各座席の様式語との対応。書いていなければ null' },
        s4_declares_repetition: { type: ['boolean', 'null'], description: '④が「毎年」「都度」など反復性を問題化しているか' },
        s4_period_months: { type: ['integer', 'null'], description: '④で問題化した反復の周期（月）。反復しないなら 0' },
        s6_period_months: { type: ['integer', 'null'], description: '⑥の課金・工数が発生する周期（月）。単発なら 0' },
        s6_residual_period_months: { type: ['integer', 'null'], description: '④で問題化した事象が、本提案の実施後も再発する周期（月）。仕組み・様式・型が買い手側に残って再発しないなら 0。課金周期とは別物' },
        s5_is_constraint_disclosure: { type: 'boolean', description: '⑤が能力の否定ではなく、条件下での不成立の形になっているか' },
        s6_ends_imperative: { type: 'boolean' },
        s6_contains_promise: { type: 'boolean' },
        s6_recasts_unit: { type: ['boolean', 'null'], description: '⑥で②の単位を別単位へ換算したか（併記でも true）' },
        // 第12.5b版：欄を割った。最終裁定点の κ_n は2つありうるのに欄が単数で、
        // 指示文が「価格・財源」と連結表示していた（型1・A24/A25/A25c と同じ形の4例目）。
        s6_kappa: {
          type: 'array',
          description: '⑥に置いた量のうち、最終裁定点に向けたものの基準。'
            + '指示に挙がっている基準をその数だけ並べる。一つの文字列に連結しないこと',
          items: { type: 'string', description: '実務性／価格／財源／説明可能性／政治的可視性 のいずれか' },
        },
        s6_coverage_full: { type: ['boolean', 'null'], description: '提案が④で数えた量を全部消すか' },
        s6_coverage_disclosed: { type: ['boolean', 'null'], description: '全部でない場合、どこまで消すかを数で書いたか' },
        s6_coverage_subset: { type: ['boolean', 'null'], description: '提案が消す集合は、④で数えた集合に含まれるか' },
        s6_kappa_type: { type: 'string', enum: ['stock', 'flow'], description: '⑥に置いた量が総額系(stock)か流量系(flow)か' },
        s6_kappa_by_seat: {
          type: ['array', 'null'],
          description: '⑥に置いた量を、資料を読む座席ごとに一つずつ。指示にその要求が無ければ null',
          items: {
            type: 'object',
            required: ['seat', 'kappa'],
            properties: {
              seat: { type: 'string', description: '座席名。渡された一覧の表記をそのまま使う' },
              kappa: { type: 'string', description: '実務性／価格／財源／説明可能性／政治的可視性 のいずれか' },
            },
          },
        },
        s6_realize: {
          type: ['array', 'null'],
          description: '浮いた分を実際に減らす〈誰が・いつ・どの費目〉の組。費目が2つなら組も2つ。連結しない',
          items: {
            type: 'object',
            required: ['actor', 'date', 'account'],
            properties: {
              actor: { type: 'string', description: '渡された「費目を実際に減らせる座席」から選ぶ' },
              date: { type: 'string', description: 'YYYY-MM-DD' },
              account: { type: 'string', description: 'その座席が減らせる費目。一覧の語をそのまま一つだけ' },
            },
          },
        },
        // A37（第13.5版）：一つの欄が〈決定〉と〈着手〉の二つを指していた。欄を割る。
        s6_decide_date: { type: ['string', 'null'], description: '⑥が示す「決定が締まる日」（YYYY-MM-DD）。今日以降かつ、渡された決定期限以前' },
        s6_start_date: { type: ['string', 'null'], description: '⑥が示す「実際に動き出す日」（YYYY-MM-DD）。決定日 ＋ 買い手が動き出すまでの月数 以降。上限は無い' },
        s6_self_check: { type: ['boolean', 'null'], description: '⑤で他手段を落とした条件を、自社の提案にも当てて確かめたか' },
        s5_denies_own: { type: ['string', 'null'], description: '⑤が否定してしまっている「買い手が自分で決めてきたこと」。無ければ空文字' },
        s6_quantity_sources: {
          type: ['array', 'null'],
          description: '⑥に置いた量それぞれの出所を、座席ごとに申告する',
          items: {
            type: 'object',
            required: ['seat', 'source'],
            properties: {
              seat: { type: 'string', description: '座席名。渡された一覧の表記をそのまま使う' },
              source: { type: 'string', enum: ['買い手データ', '公開統計', '売り手の実績', '試算', '営業記入'],
                        description: '裏づけが無い見込みなら「試算」。数字を確定できず営業に埋めてもらうなら「営業記入」' },
            },
          },
        },
        s6_to_sales: {
          type: ['array', 'null'],
          description: '営業に算出・判断を仰ぐ項目。自分では確定できなかった数字や判断を、そのまま言葉で書く。無ければ空の配列 []',
          items: { type: 'string' },
        },
        s6_omitted_blocks: {
          type: ['array', 'null'],
          description: '【必ず入れる要素】のうち書けなかったものの名前。全部書けたなら空の配列 []。字数に収めるために落とした場合もここに出す（落とすこと自体が仕様違反なので隠さない）',
          items: { type: 'string', description: '渡された【必ず入れる要素】の表記をそのまま使う' },
        },
      },
    },
    self_report: { type: 'string', description: '書ききれなかった点と、規定がなくて困った点。無ければ「なし」' },
  },
}

const IDS = ['E1-P1', 'E1-P2', 'E2-P1', 'E2-P2', 'R1-P1', 'R1-P2', 'R2-P1', 'R2-P2']
const ARMS = [0, 1, 2]

// **セル優先で交互に並べる**（arm 優先にしない）。
// このマシンは 2 コアで並列上限が実質 1 なので、24 体は直列に回る。
// arm 優先だと途中で落ちたとき arm2 だけが欠け、アーム間の比較ができなくなる。
// セル優先なら、どこで止まっても3本が同じところまで進んでいる。
const JOBS = IDS.flatMap((id) => ARMS.map((arm) => ({ arm, id })))

const bad = []

const results = await pipeline(JOBS, (j) =>
  agent(
    `Read the file /home/claude/work/prompts8_v11_arm${j.arm}.json (a JSON array). Find the element whose "id" is exactly "${j.id}".

その要素の "prompt" フィールドが、あなたへの指示そのものである。**そこに書かれた指示に厳密に従って**スライド本文を書くこと。
"sigma" フィールドが作るべき段の一覧である。slides の stage には sigma の値をそのまま使うこと。
cell_id には "${j.id}"、arm には ${j.arm} を入れること。

このファイルの他の要素は読まなくてよい。他のアームのファイルも読まないこと。`,
    { label: `arm${j.arm}:${j.id}`, phase: `Arm${j.arm}`, schema: GEN_SCHEMA }
  ).then((gen) => {
    // 取り違えの検出。アームを間違えて読んだ生成物を採点に混ぜると、
    // 差が出ても何の差か分からなくなる。突合は依頼側の (arm, id) を正とする。
    if (!gen) {
      bad.push(`欠落 arm${j.arm}:${j.id}`)
      return null
    }
    if (gen.arm !== j.arm || gen.cell_id !== j.id) {
      bad.push(`取り違え 依頼=arm${j.arm}:${j.id} 申告=arm${gen.arm}:${gen.cell_id}`)
    }
    return { arm: j.arm, id: j.id, gen }
  })
)

const ok = results.filter(Boolean)
const per = ARMS.map((a) => `arm${a}=${ok.filter((r) => r.arm === a).length}/8`).join(' ')
log(`生成 ${ok.length}/${JOBS.length}　${per}`)
if (bad.length) log(`要確認: ${bad.join(' / ')}`)

return ok
