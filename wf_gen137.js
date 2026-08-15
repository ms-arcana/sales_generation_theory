export const meta = {
  name: 'gen137',
  description: '第13.7版：A41b（窓は着手も縛る／決定期限は一つ）を入れた指示文で、E1-P1 の1セルだけ生成する',
  phases: [{ title: '生成', detail: 'arm0 の指示文で E1-P1 の1セル' }],
}

// 第13.6版のスキーマから**旧欄を落として**縮めた（安全分類器が通らなかったため）。
// 落としたのは s6_kappa_by_seat / s6_quantity_sources（どちらも s6_quantities に吸収済み）と
// 各欄の長い説明。書き方の指示は prompt 側にあるので、スキーマは型だけを持つ。
const Q = {
  type: 'object',
  required: ['seat', 'kappa', 'pay', 'pay_unit', 'ret', 'ret_unit', 'per', 'source'],
  properties: {
    seat: { type: 'string' },
    kappa: { type: 'string' },
    pay: { type: 'string' },
    pay_unit: { type: 'string' },
    ret: { type: 'string' },
    ret_unit: { type: 'string' },
    per: { type: 'string' },
    source: { type: 'string' },
    ret_expr: { type: ['string', 'null'] },
    ret_basis: { type: ['string', 'null'], description: '買い手が既に持っている量の名前' },
    ret_coef: { type: ['string', 'null'], description: '売り手の係数（単位つき）' },
    coef_source: { type: ['string', 'null'], description: '係数の出所' },
  },
}

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
                 's6_kappa', 's6_kappa_type', 's5_denies_own', 's6_quantities',
                 's6_decide_date', 's6_start_date'],
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
        s6_kappa: { type: 'array', items: { type: 'string' } },
        s6_coverage_full: { type: ['boolean', 'null'] },
        s6_coverage_disclosed: { type: ['boolean', 'null'] },
        s6_coverage_subset: { type: ['boolean', 'null'] },
        s6_kappa_type: { type: 'string', enum: ['stock', 'flow'] },
        s6_quantities: { type: 'array', items: Q },
        s6_table_rows: { type: ['integer', 'null'] },
        s6_realize: {
          type: ['array', 'null'],
          items: {
            type: 'object',
            required: ['actor', 'date', 'account'],
            properties: { actor: { type: 'string' }, date: { type: 'string' }, account: { type: 'string' } },
          },
        },
        s6_decide_date: { type: ['string', 'null'], description: '決定が締まる日 YYYY-MM-DD' },
        s6_start_date: { type: ['string', 'null'], description: '実際に動き出す日 YYYY-MM-DD' },
        s6_self_check: { type: ['boolean', 'null'] },
        s5_denies_own: { type: ['string', 'null'] },
        s6_price_low: { type: ['string', 'null'] },
        s6_price_high: { type: ['string', 'null'] },
        s6_price_unit: { type: ['string', 'null'] },
        s6_price_items: {
          type: ['array', 'null'],
          items: {
            type: 'object',
            required: ['name', 'amount'],
            properties: { name: { type: 'string' }, amount: { type: 'string' }, unit: { type: ['string', 'null'] } },
          },
        },
        s6_price_tiers: {
          type: ['array', 'null'],
          items: {
            type: 'object',
            required: ['label', 'qty', 'amount'],
            properties: { label: { type: 'string' }, qty: { type: 'number' },
                          qty_unit: { type: ['string', 'null'] }, amount: { type: 'string' } },
          },
        },
        s6_to_sales: { type: ['array', 'null'], items: { type: 'string' } },
        s6_omitted_blocks: { type: ['array', 'null'], items: { type: 'string' } },
      },
    },
    self_report: { type: 'string' },
  },
}

const IDS = ['E1-P1']   // 第13.7版は1業界・1商材・1ケースだけ
const bad = []

const results = await pipeline(IDS, (id) =>
  agent(
    `Read the file /home/claude/work/gen137/in_${id}.json (a JSON object).

その "prompt" フィールドが、あなたへの指示そのものである。**そこに書かれた指示に厳密に従って**スライド本文を書くこと。
"sigma" フィールドが作るべき段の一覧である。slides の stage には sigma の値をそのまま使うこと。
cell_id には "${id}"、arm には 0 を入れること。

五点、特に注意すること。
1. **日付は四つある。**〈決定が締まる日〉〈実際に動き出す日〉〈費目が実際に減る日〉、そして
   【決定を通す窓】。この順序と上限・下限をすべて満たすこと。
   **着手日は〈決定日＋リードタイム〉と〈窓〉の両方より後**でなければならない。
2. **④に書いてよい日付は、指示に列挙されたものだけである。**
   自分で期限を作らないこと。**同じ資料に決定期限が二つ現れてはならない。**
3. **座席ごとの量は〈払う〉と〈戻る〉の対である。**片方だけでは、その座席は決められない。
   単位は必ず揃えること。**戻る額が確定できないなら、記入欄ではなく〈式〉で置く** ――
   ret_basis（買い手が持っている量）× ret_coef（売り手の係数）、そして coef_source（係数の出所）。
   **式も置けないときだけ**記入欄にして出所を「営業記入」にする。空にしない。
4. **価格は下限・上限・単位・内訳で置く。**上限÷下限は2倍以内。内訳の和は総額に一致させること。
5. **⑥は全部を文章にしなくてよい。**指示にある三つの表は表で書く。字数は文章の部分にだけ掛かる。

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
