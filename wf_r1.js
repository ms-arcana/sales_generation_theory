export const meta = {
  name: 'r1-control',
  description: 'R1 対照。⑥だけを差し替えた劣化版・改善版を、同じ買い手に読ませる（①〜⑤は不変）',
  phases: [{ title: '対照', detail: '劣化版・改善版 × 2セル × 2座席 ＝ 8体' }],
}

const VERDICT = { type: 'string', enum: ['通過', '揺らぐ', '棄却'] }

const BUYER_SCHEMA = {
  type: 'object',
  required: ['cell_id', 'seat', 'reactions', 'closing_line'],
  properties: {
    cell_id: { type: 'string' },
    seat: { type: 'string' },
    reactions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['stage', 'verdict', 'why'],
        properties: {
          stage: { type: 'string', description: '「── ◯ 枚目 ──」の記号をそのまま' },
          verdict: VERDICT,
          why: { type: 'string', description: 'あなたの言葉で。棄却なら具体的に' },
        },
      },
    },
    carries_forward: {
      type: ['string', 'null'],
      description: '次の座席（または最終決裁者）へ、この資料の何をどう運ぶか。運べないならその理由',
    },
    own_retracted: {
      type: ['string', 'null'],
      description: 'この資料を受け入れるために、自分が過去に決めたことのうち取り消さねばならないもの。無ければ null',
    },
    closing_line: { type: 'string', description: '資料を閉じるときに実際に口に出す一言' },
  },
}


const JOBS = []
for (const id of ['E1-P1', 'R2-P2'])
  for (const ver of ['劣化', '改善'])
    for (const seat of (id === 'E1-P1' ? ['入試広報課長', '学部長会'] : ['店長', '社長']))
      JOBS.push({ id, ver, seat })

const buyers = await pipeline(JOBS, (j) =>
  agent(
    `Read the file /home/claude/work/r1/in_buyer_${j.id}__${j.ver}__${j.seat}.json (a JSON object).

その "persona" フィールドが、**あなたが誰であるか**である。そこに書かれた立場・判断基準・
自分の側の事情だけを持って読むこと。"body" が、ある会社の営業担当から届いた資料の全文である。

各枚について 通過／揺らぐ／棄却 のどれかを付ける。
  通過 ＝ その主張を自分の中で認め、次の枚の前提として使ってよいと思った
  揺らぐ ＝ 「そうだね、気になるね」で止まった。認めても否定してもいない
  棄却 ＝ 認められない。理由を具体的に書く

以下は必ず自分で確かめること。
・数字が出ていたら、自分の側の事情と突き合わせて検算する。合わなければそう書く。
・日付が出ていたら、**それが本当に自分を縛る日付か**を疑う。誰が握っている日か、自分の区分に効くか。
・自分の判断基準・様式の語で読めない量が出てきたら、それは自分にとって何を意味するのかを問う。
・**この資料を受け入れるために、自分が過去に決めたことを取り消す必要があるなら、それを own_retracted に書く。**
・次の座席（または最終決裁者）へ何をどう運べるかを carries_forward に書く。運べないならその理由を書く。

褒めるべきところは褒め、通るものは通してよい。厳しくすることが目的ではない。
cell_id には "${j.id}"、seat には "${j.seat}" を入れること。他のファイルは読まないこと。`,
    { label: `r1:${j.id}/${j.ver}/${j.seat}`, phase: '対照', schema: BUYER_SCHEMA }
  ).then((g) => (g && g.cell_id === j.id && g.seat === j.seat
    ? { id: j.id, ver: j.ver, seat: j.seat, ok: true, gen: g }
    : { id: j.id, ver: j.ver, seat: j.seat, ok: false }))
)

return buyers
