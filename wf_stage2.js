export const meta = {
  name: 'stage2-blind-buyer',
  description: '第2段。予測器8体と盲検買い手16体を分けて走らせ、仕様を満たした資料が買い手を通るかを測る',
  phases: [
    { title: '予測', detail: '資料と座席構成だけを見て、買い手の反応を予測する 8体' },
    { title: '買い手', detail: 'ペルソナと資料だけを見て反応する 16体（各セル2座席）' },
  ],
}

const VERDICT = { type: 'string', enum: ['通過', '揺らぐ', '棄却'] }

const PRED_SCHEMA = {
  type: 'object',
  required: ['cell_id', 'predictions', 'longest_stage', 'weakest_point'],
  properties: {
    cell_id: { type: 'string' },
    predictions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['seat', 'stage', 'verdict', 'why'],
        properties: {
          seat: { type: 'string', description: '渡された座席一覧の表記をそのまま使う' },
          stage: { type: 'string', description: '「── ◯ 枚目 ──」の記号をそのまま' },
          verdict: VERDICT,
          why: { type: 'string' },
        },
      },
    },
    longest_stage: { type: 'string', description: '買い手が最も長く止まると思う段' },
    weakest_point: { type: 'string', description: '最初に破れると思う箇所' },
  },
}

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

const IDS = ['E1-P1', 'E1-P2', 'E2-P1', 'E2-P2', 'R1-P1', 'R1-P2', 'R2-P1', 'R2-P2']
const SEATS = {
  'E1-P1': ['入試広報課長', '学部長会'], 'E1-P2': ['入試広報課長', '学部長会'],
  'E2-P1': ['教務主任', '理事長'], 'E2-P2': ['教務主任', '理事長'],
  'R1-P1': ['店舗運営部', '商品本部バイヤー'], 'R1-P2': ['店舗運営部', '商品本部バイヤー'],
  'R2-P1': ['店長', '社長'], 'R2-P2': ['店長', '社長'],
}

const preds = await pipeline(IDS, (id) =>
  agent(
    `Read the file /home/claude/work/stage2/in_pred_${id}.json (a JSON object).

あなたは営業部門のレビュー担当。この資料を書いた本人ではなく、書き手の意図も知らない。
"seats" が相手先の座席構成、"body" が資料の全文である。

**資料と座席構成だけを見て、各座席が各枚にどう反応するかを予測する。**
資料を読む座席（"資料を読む" と書いてある座席）**すべて**について、
枚ごとに 通過／揺らぐ／棄却 のどれかを予測し、理由を書くこと。

  通過 ＝ その座席はその主張を認め、次の枚の前提として使う
  揺らぐ ＝ 「そうだね、気になるね」で止まる。認めも否定もしない
  棄却 ＝ 認めない

甘く見ないこと。買い手は数字を自分の物差しで検算し、日付が本当に自分を縛るかを疑い、
自分の様式に無い語で書かれたものは会議に載せられない。
cell_id には "${id}" を入れること。他のファイルは読まないこと。`,
    { label: `pred:${id}`, phase: '予測', schema: PRED_SCHEMA }
  ).then((g) => (g && g.cell_id === id ? { id, ok: true, gen: g } : { id, ok: false }))
)

const JOBS = IDS.flatMap((id) => SEATS[id].map((seat) => ({ id, seat })))

const buyers = await pipeline(JOBS, (j) =>
  agent(
    `Read the file /home/claude/work/stage2/in_buyer_${j.id}__${j.seat}.json (a JSON object).

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
    { label: `buyer:${j.id}/${j.seat}`, phase: '買い手', schema: BUYER_SCHEMA }
  ).then((g) => (g && g.cell_id === j.id && g.seat === j.seat
    ? { id: j.id, seat: j.seat, ok: true, gen: g } : { id: j.id, seat: j.seat, ok: false }))
)

return { preds, buyers }
