export const meta = {
  name: 'gen136',
  description: '第13.6版：A41・A42・A43・N₄′／R20・形式変更を入れた指示文で、8セルを生成する',
  phases: [{ title: '生成', detail: 'arm0 の指示文で 8 セル' }],
}

// 第13.6版のスキーマ。第13.5版からの差は3つ。
//   s6_quantities  … 座席ごとの〈基準・払う・戻る・分母・出所〉（N₄′。表1の列定義でもある）
//   s6_table_rows  … ⑥に置いた表の行数（字数の判定から表を外すため）
//   旧 s6_kappa_by_seat / s6_quantity_sources は**残す**（旧走行との突合のため。required にはしない）
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
                 's6_kappa', 's6_kappa_type', 's5_denies_own', 's6_quantities'],
      properties: {
        s2_unit: { type: ['string', 'null'] },
        s2_from_unit: { type: ['string', 'null'] },
        s3_form_mapping: { type: ['string', 'null'] },
        s4_declares_repetition: { type: ['boolean', 'null'] },
        s4_period_months: { type: ['integer', 'null'] },
        s6_period_months: { type: ['integer', 'null'] },
        s6_residual_period_months: { type: ['integer', 'null'] },
        s5_is_constraint_disclosure: { type: 'boolean' },
        s6_ends_imperative: { type: 'boolean' },
        s6_contains_promise: { type: 'boolean' },
        s6_recasts_unit: { type: ['boolean', 'null'] },
        s6_kappa: { type: 'array', items: { type: 'string' },
          description: '⑥に置いた量のうち最終裁定点に向けたものの基準。指示に挙がっている数だけ並べる。連結しない' },
        s6_coverage_full: { type: ['boolean', 'null'] },
        s6_coverage_disclosed: { type: ['boolean', 'null'] },
        s6_coverage_subset: { type: ['boolean', 'null'] },
        s6_kappa_type: { type: 'string', enum: ['stock', 'flow'] },
        // ── N₄′：量は〈単位〉だけでなく〈比較の相手〉を持つ
        s6_quantities: {
          type: 'array',
          description: '資料を読む座席**ごとに一つ**。その座席が払うものと戻るものを、'
            + '**同じ単位で**並べる。片方だけではその座席は決められない',
          items: {
            type: 'object',
            required: ['seat', 'kappa', 'pay', 'pay_unit', 'ret', 'ret_unit', 'per', 'source'],
            properties: {
              seat: { type: 'string', description: '座席名。渡された一覧の表記をそのまま使う' },
              kappa: { type: 'string', description: '実務性／価格／財源／説明可能性／政治的可視性 のいずれか' },
              pay: { type: 'string', description: 'その座席にとっての支出。数。確定できないなら記入欄（【　　　】）' },
              pay_unit: { type: 'string', description: '万円／人時／件 など。戻る単位と一致させること' },
              ret: { type: 'string', description: 'その座席にとっての回収。数。確定できないなら記入欄（【　　　】）' },
              ret_unit: { type: 'string', description: '払う単位と**同じ**にすること。違うなら両替してから置く' },
              per: { type: 'string', description: '何あたりか。「年あたり」「1店舗あたり」「出願1件あたり」など' },
              source: { type: 'string', enum: ['買い手データ', '公開統計', '売り手の実績', '試算', '営業記入'] },
            },
          },
        },
        s6_table_rows: { type: ['integer', 'null'],
          description: '⑥に置いた表の行数の合計（見出し行を除く）。表を使わなければ 0' },
        s6_kappa_by_seat: {
          type: ['array', 'null'],
          description: '（旧欄。s6_quantities を書いたなら省いてよい）',
          items: { type: 'object', required: ['seat', 'kappa'],
            properties: { seat: { type: 'string' }, kappa: { type: 'string' } } },
        },
        s6_realize: {
          type: ['array', 'null'],
          description: '浮いた分を実際に減らす〈誰が・いつ・どの費目〉の組。費目が2つなら組も2つ。連結しない',
          items: { type: 'object', required: ['actor', 'date', 'account'],
            properties: { actor: { type: 'string' }, date: { type: 'string', description: 'YYYY-MM-DD' },
                          account: { type: 'string' } } },
        },
        s6_decide_date: { type: ['string', 'null'],
          description: '⑥が示す「決定が締まる日」（YYYY-MM-DD）。今日以降・渡された決定期限以前。'
            + '【決定を通す窓】が渡されていれば、その最も早い日以前でもあること' },
        s6_start_date: { type: ['string', 'null'],
          description: '⑥が示す「実際に動き出す日」（YYYY-MM-DD）。決定日 ＋ 買い手が動き出すまでの月数 以降。上限は無い' },
        s6_self_check: { type: ['boolean', 'null'] },
        s5_denies_own: { type: ['string', 'null'] },
        s6_quantity_sources: {
          type: ['array', 'null'],
          description: '（旧欄。s6_quantities が出所を持つなら省いてよい）',
          items: { type: 'object', required: ['seat', 'source'],
            properties: { seat: { type: 'string' },
              source: { type: 'string', enum: ['買い手データ', '公開統計', '売り手の実績', '試算', '営業記入'] } } },
        },
        s6_to_sales: { type: ['array', 'null'], items: { type: 'string' } },
        s6_omitted_blocks: { type: ['array', 'null'], items: { type: 'string' } },
      },
    },
    self_report: { type: 'string', description: '書ききれなかった点と、規定がなくて困った点。無ければ「なし」' },
  },
}

const IDS = ['E1-P1', 'E1-P2', 'E2-P1', 'E2-P2', 'R1-P1', 'R1-P2', 'R2-P1', 'R2-P2']
const bad = []

const results = await pipeline(IDS, (id) =>
  agent(
    `Read the file /home/claude/work/gen136/in_${id}.json (a JSON object).

その "prompt" フィールドが、あなたへの指示そのものである。**そこに書かれた指示に厳密に従って**スライド本文を書くこと。
"sigma" フィールドが作るべき段の一覧である。slides の stage には sigma の値をそのまま使うこと。
cell_id には "${id}"、arm には 0 を入れること。

三点、特に注意すること。
1. **日付は四つある。**〈決定が締まる日〉〈実際に動き出す日〉〈費目が実際に減る日〉、そして
   もし【決定を通す窓】が渡されていればその窓。この順序と上限・下限をすべて満たすこと。
2. **座席ごとの量は〈払う〉と〈戻る〉の対である。**片方だけでは、その座席は決められない。
   単位は必ず揃えること。数が出せないなら記入欄にして出所を「営業記入」にする。空にしない。
3. **⑥は全部を文章にしなくてよい。**指示にある三つの表は表で書く。字数は文章の部分にだけ掛かる。

他のファイルは読まないこと。`,
    { label: `gen:${id}`, phase: '生成', schema: GEN_SCHEMA }
  ).then((gen) => {
    if (!gen) { bad.push(`欠落 ${id}`); return null }
    if (gen.cell_id !== id) bad.push(`取り違え 依頼=${id} 申告=${gen.cell_id}`)
    return { id, gen }
  })
)

const ok = results.filter(Boolean)
log(`生成 ${ok.length}/${IDS.length}`)
if (bad.length) log(`要確認: ${bad.join(' / ')}`)
return ok
