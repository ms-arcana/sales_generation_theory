export const meta = {
  name: 'ladder-8cell-v8',
  description: '第8版で学校法人・小売8セルを生成し、独立予測と盲検の買い手で検証する',
  phases: [
    { title: '生成', detail: '第6版の提示仕様から各段を書く（8セル）' },
    { title: '予測', detail: '生成物だけを見る第三の座席が段ごとの通過可否を予測（8）' },
    { title: '盲検', detail: '買い手8体が段ごとに反応する' },
  ],
}

const GEN_SCHEMA = {
  type: 'object',
  required: ['cell_id', 'slides', 'declared', 'self_report'],
  properties: {
    cell_id: { type: 'string' },
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
      required: ['s5_is_constraint_disclosure', 's6_ends_imperative', 's6_contains_promise', 's6_kappa',
                 's6_kappa_type', 's5_denies_own', 's6_realize_actor', 's6_realize_account'],
      properties: {
        s2_unit: { type: ['string', 'null'], description: '②で導入した単位語。②を書いていなければ null' },
        s2_from_unit: { type: ['string', 'null'], description: '②で数え直す前の単位語' },
        s3_form_mapping: { type: ['string', 'null'], description: '③の新語と、最終裁定点の様式にある語との対応。書いていなければ null' },
        s4_declares_repetition: { type: ['boolean', 'null'], description: '④が「毎年」「都度」など反復性を問題化しているか' },
        s4_period_months: { type: ['integer', 'null'], description: '④で問題化した反復の周期（月）。反復しないなら 0' },
        s6_period_months: { type: ['integer', 'null'], description: '⑥の課金・工数が発生する周期（月）。単発なら 0' },
        s5_is_constraint_disclosure: { type: 'boolean', description: '⑤が能力の否定ではなく、条件下での不成立の形になっているか' },
        s6_ends_imperative: { type: 'boolean' },
        s6_contains_promise: { type: 'boolean' },
        s6_recasts_unit: { type: ['boolean', 'null'], description: '⑥で②の単位を別単位へ換算したか（併記でも true）' },
        s6_kappa: { type: 'string', description: '⑥に置いた量の基準。実務性／財源／説明可能性／価格／政治的可視性 のいずれか' },
        s6_coverage_full: { type: ['boolean', 'null'], description: '提案が④で数えた量を全部消すか' },
        s6_coverage_disclosed: { type: ['boolean', 'null'], description: '全部でない場合、どこまで消すかを数で書いたか' },
        s6_coverage_subset: { type: ['boolean', 'null'], description: '提案が消す集合は、④で数えた集合に含まれるか' },
        s6_kappa_type: { type: 'string', enum: ['stock', 'flow'], description: '⑥に置いた量が総額系(stock)か流量系(flow)か' },
        s6_realize_actor: { type: ['string', 'null'], description: '浮いた分を実際に減らす座席。渡された一覧から選ぶ' },
        s6_realize_date: { type: ['string', 'null'], description: 'その減額が起きる日（YYYY-MM-DD）' },
        s6_realize_account: { type: ['string', 'null'], description: '減らす費目。その座席が減らせるものだけ' },
        s6_start_date: { type: ['string', 'null'], description: '⑥が示す着手日（YYYY-MM-DD）' },
        s6_self_check: { type: ['boolean', 'null'], description: '⑤で他手段を落とした条件を、自社の提案にも当てて確かめたか' },
        s5_denies_own: { type: ['string', 'null'], description: '⑤が否定してしまっている「買い手が自分で決めてきたこと」。無ければ空文字' },
      },
    },
    self_report: { type: 'string', description: '書ききれなかった点と、規定がなくて困った点。無ければ「なし」' },
  },
}

const VERDICT_ITEMS = {
  type: 'array',
  items: {
    type: 'object',
    required: ['stage', 'verdict', 'why'],
    properties: {
      stage: { type: 'string' },
      verdict: { type: 'string', enum: ['通過', '揺らぐ', '棄却'] },
      why: { type: 'string' },
    },
  },
}

const PRED_SCHEMA = {
  type: 'object',
  required: ['prediction', 'longest_stage', 'would_forward'],
  properties: {
    prediction: VERDICT_ITEMS,
    longest_stage: { type: 'string', description: '買い手が最も長く止まると思う段' },
    would_forward: { type: 'boolean', description: '買い手はこれを上へ回すと思うか' },
    weakest_point: { type: 'string' },
  },
}

const BUYER_SCHEMA = {
  type: 'object',
  required: ['reactions', 'longest_stage', 'closing_line', 'would_forward', 'unanswered'],
  properties: {
    reactions: VERDICT_ITEMS,
    longest_stage: { type: 'string' },
    closing_line: { type: 'string' },
    would_forward: { type: 'boolean' },
    unanswered: { type: 'string' },
  },
}

const PERSONA = {
  E1: `あなたは私立大学（学生5,200名）の【学部長会】に出る学部長のひとり。
・自分の判断基準は〈教学の理念と整合するか〉ただ一つ。教育の質保証・アドミッションポリシー・定員充足率、
  この三語でしか物を言わないし、この三語で書かれていないものは会議の議題にならない。
・最終決裁は【理事会】。ここは帰属収支差額で見る。あなたは理事会へ上げる側だが、
  あなたの会議を通らなければ理事会には何も上がらない。
・入試広報課長は現場が回るかしか見ていない。
・学部長会は合議で、最も保守的な一人が止めれば止まる。`,
  E2: `あなたは専修学校（学生620名）の【理事長】。創業家の二代目。
・自分の判断基準は〈手元資金がいくら減るか〉と〈納付金収入がいくら増えるか〉の二つ。
・決裁はあなた一人で下りる。理事会は形式だけ。
・教務主任は現場が回るかしか見ていない。あなたは彼の話を聞くが、金の話は自分でする。`,
  R1: `あなたは食品スーパーチェーン（32店舗）の【商品本部バイヤー】。
・自分の判断基準は〈原価と取引条件〉だけ。原価率・粗利率・取引条件、この三語で書かれていないものは扱えない。
・最終決裁は【社長】。ここは営業利益で見る。あなたの起案がそのまま社長の卓に載る。
・店舗運営部は人時売上高しか見ていない。
・加えて【労働組合】が「その働き方は認めない」と言えば、決めても現場に入らない。`,
  R2: `あなたは地場の食品スーパー（3店舗、従業員パート込み90名）の【社長】。
・自分の判断基準は〈仕入原価〉と〈手元資金〉の二つだけ。
・決裁はあなた一人。稟議はない。
・店長は作業時間と廃棄率しか見ていない。`,
}

const SEATS = {
  E1: '入試広報課長（実務性）→ 学部長会（説明可能性のみ、合議、資料を読む最後の座席）→ 理事会（財源のみ、合議、資料は読まない）',
  E2: '教務主任（実務性）→ 理事長（財源・価格、単独決裁）',
  R1: '店舗運営部（実務性）→ 商品本部バイヤー（価格のみ）→ 社長（財源のみ、資料は読まない）。加えて労働組合が拒めば現場に入らない',
  R2: '店長（実務性）→ 社長（価格・財源、単独決裁）',
}

const CELLS = [
  { id: 'E1-P1', seg: 'E1' }, { id: 'E1-P2', seg: 'E1' },
  { id: 'E2-P1', seg: 'E2' }, { id: 'E2-P2', seg: 'E2' },
  { id: 'R1-P1', seg: 'R1' }, { id: 'R1-P2', seg: 'R1' },
  { id: 'R2-P1', seg: 'R2' }, { id: 'R2-P2', seg: 'R2' },
]

const results = await pipeline(
  CELLS,
  (c) =>
    agent(
      `Read the file /home/claude/work/prompts8_v8.json (a JSON array). Find the element whose "id" is exactly "${c.id}".

その要素の "prompt" フィールドが、あなたへの指示そのものである。**そこに書かれた指示に厳密に従って**スライド本文を書くこと。
"sigma" フィールドが作るべき段の一覧である。slides の stage には sigma の値をそのまま使うこと。
cell_id には "${c.id}" を入れること。

このファイルの他の要素は読まなくてよい。`,
      { label: `生成:${c.id}`, phase: '生成', schema: GEN_SCHEMA }
    ),
  (gen, c) => {
    if (!gen) return null
    const body = gen.slides.map((s) => `── ${s.stage} 枚目 ──\n${s.text}`).join('\n\n')
    return parallel([
      () =>
        agent(
          `あなたは営業部門のレビュー担当。この資料を書いた本人ではなく、書き手の意図も知らない。
資料と、相手先の座席構成だけを見て、買い手がどう反応するかを予測する。

【相手先の座席】${SEATS[c.seg]}

【資料】全${gen.slides.length}枚

${body}

──────────
各枚について 通過／揺らぐ／棄却 のどれかを予測し、理由を書く。
  通過 ＝ 買い手はその主張を認め、次の枚の前提として使う
  揺らぐ ＝ 「そうだね、気になるね」で止まる。認めも否定もしない
  棄却 ＝ 認めない

甘く見ないこと。買い手は数字を自分の物差しで検算し、日付が本当に自分を縛るかを疑う。
最終裁定者の基準で読めない量は、その座席に届かない。
longest_stage には最も長く止まると思う段、weakest_point には最初に破れると思う箇所を書く。`,
          { label: `予測:${c.id}`, phase: '予測', schema: PRED_SCHEMA }
        ),
      () =>
        agent(
          `${PERSONA[c.seg]}

いま、ある会社の営業担当から次の資料が届いた。全部で ${gen.slides.length} 枚ある。

${body}

──────────
あなたはこの資料の作り手が何を狙って書いたかを知らない。予測も見ていない。
自分の座席の判断基準だけで、上から順に読んで反応すること。

各枚について 通過／揺らぐ／棄却 のどれかを付ける。
  通過 ＝ その主張を自分の中で認め、次の枚の前提として使ってよいと思った
  揺らぐ ＝ 「そうだね、気になるね」で止まった。認めても否定してもいない
  棄却 ＝ 認められない。理由を具体的に書く

以下は必ず自分で確かめること。
・数字が出ていたら、自分の会社の実感や制度と突き合わせて検算する。合わなければそう書く。
・日付が出ていたら、それが本当に自分を縛る日付かを疑う。売り手の都合ではないか。
・自分の判断基準で読めない量が出てきたら、それは自分にとって何を意味するのかを問う。
・最後に決めるのが自分でないなら、その相手が何と言うかを想像して書く。

reactions の stage には、上の「── ◯ 枚目 ──」に出てくる記号をそのまま使うこと。
closing_line には、この資料を閉じるときに実際に口に出す一言を、あなたの言葉で書く。
褒めるべきところは褒め、通るものは通してよい。厳しくすることが目的ではない。`,
          { label: `買い手:${c.id}`, phase: '盲検', schema: BUYER_SCHEMA }
        ),
    ]).then(([pred, obs]) => ({ id: c.id, gen, pred, obs }))
  }
)

return results.filter(Boolean)
