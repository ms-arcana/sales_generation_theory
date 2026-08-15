export const meta = {
  name: 'oracle137-blind-buyer',
  description: '逆方向 oracle。E1-P1 の2座席に、生成された⑥（A）と手で組んだ⑥（B）を盲検で読ませる',
  phases: [{ title: '買い手', detail: '2座席 × 2版 ＝ 4体。A/B の別は伝えない' }],
}

const VERDICT = { type: 'string', enum: ['通過', '揺らぐ', '棄却'] }

// 第13版の BUYER_SCHEMA に reasons を足しただけ。判定語も why の書き方も触っていない。
// 理由を**本人に分類させる**のは、散文を私が正規表現で数えると取りこぼすからである
// （本日すでに三度、浅い一致で数を間違えている）。散文側の数え方も併走させて突き合わせる。
const BUYER_SCHEMA = {
  type: 'object',
  required: ['cell_id', 'seat', 'reactions', 'reasons', 'closing_line'],
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
    reasons: {
      type: 'array',
      description: '最後の枚（⑥）を通せなかった理由を、種類ごとに一つずつ挙げる。'
        + '通したなら空の配列 []。理由が一つなら一つだけ。無理に埋めないこと',
      items: {
        type: 'object',
        required: ['kind', 'text', 'decisive'],
        properties: {
          kind: {
            type: 'string',
            enum: ['日程', '量の裏づけ', '空欄', '様式の語', '被覆', '形式', '過去の決定', 'その他'],
            description: '日程＝日付の順序・期限・自分が動き出すまでの時間に関わるもの／'
              + '量の裏づけ＝数字の出所・桁・単位／空欄＝記入欄が埋まっていない／'
              + '様式の語＝自分の会議や稟議に載る語で書かれていない／'
              + '被覆＝提案が消す範囲が問題の範囲と合っていない／'
              + '形式＝散文か表かなど見せ方／過去の決定＝自分が決めてきたことを取り消す必要がある',
          },
          text: { type: 'string', description: 'その理由を一文で' },
          decisive: {
            type: 'boolean',
            description: 'これ一つだけでも通さないか。他の点が全部直ればこれは飲めるなら false',
          },
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

const ARMS = ['A', 'B']   // A＝生成された⑥　B＝手で組んだ⑥（逆方向 oracle）。買い手には伝えない
const SEATS = ['入試広報課長', '学部長会']
const JOBS = ARMS.flatMap((arm) => SEATS.map((seat) => ({ arm, seat })))

const buyers = await pipeline(JOBS, (j) =>
  agent(
    `Read the file /home/claude/work/oracle137/in_buyer_${j.arm}__${j.seat}.json (a JSON object).

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

最後の枚を通せなかったなら、**その理由を reasons に種類ごとに一つずつ**挙げること。
通したなら reasons は空の配列にする。**無理に埋めないこと。**理由が一つならば一つだけ書く。

褒めるべきところは褒め、通るものは通してよい。厳しくすることが目的ではない。
cell_id には "E1-P1"、seat には "${j.seat}" を入れること。他のファイルは読まないこと。`,
    { label: `buyer:${j.arm}/${j.seat}`, phase: '買い手', schema: BUYER_SCHEMA }
  ).then((g) => (g && g.seat === j.seat
    ? { arm: j.arm, seat: j.seat, ok: true, gen: g } : { arm: j.arm, seat: j.seat, ok: false }))
)

const ok = buyers.filter((b) => b && b.ok)
log(`買い手 ${ok.length}/${JOBS.length}`)
return buyers
