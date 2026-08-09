export const meta = {
  name: 'ladder-8cell-v6',
  description: '第6版で食品・建設8セルを再生成し、予測を独立させて盲検の買い手で検証する',
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
      required: ['s5_is_constraint_disclosure', 's6_ends_imperative', 's6_contains_promise', 's6_kappa'],
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
  F1: `あなたは大手食品グループの生産子会社の【親会社 生産技術部】の担当部長。
・自分の判断基準は〈現場で回るか〉と〈グループ標準に説明がつくか〉の二つ。
・あなたの上に【親会社 調達本部】がいる。ここは価格だけを見る。相見積3社が規程で決まっており、
  あなたが上げた資料はそのまま調達の様式に転記される。転記できる語は 単価・回収年数・見積総額 だけ。
・工場側（工場長）は現場の再現性しか見ていない。`,
  F2: `あなたはオーナー系中堅食品メーカー（惣菜・日配、従業員180名）の【社長】。創業家の二代目。
・自分の判断基準は〈手元資金がいくら減るか〉と〈その金がどこから出るか〉の二つ。
・決裁はあなた一人で下りる。稟議も取締役会もない。親会社はない。
・製造部長は現場の再現性しか見ていない。あなたは彼の言うことを聞くが、金の話は自分でする。`,
  K1: `あなたは中堅ゼネコン（完成工事高450億円）の【本社 工務部】の部長。
・自分の判断基準は〈施工計画・安全衛生・積算と整合するか〉と〈常務会に説明がつくか〉。
・最終決裁は【常務会】。完成工事総利益で見る。合議で、最も保守的な一人が止めれば止まる。
・この現場では当社が元請である。協力会社に対して承認するのはこちら側。
・作業所長からは「現場が回るなら何でもいい」としか上がってこない。
・あなたはすでに他社の同種装置の提案を2社から受けている。`,
  K2: `あなたは専門工事業（下請、従業員120名、鉄骨・設備）の【社長】。
・自分の判断基準は〈常用単価に見合うか〉と〈手元資金〉の二つだけ。
・決裁はあなた一人。ただし【元請A社の安全衛生管理責任者】が「うちの現場では使わせない」と言えば、
  買っても現場に入らない。この人物に決裁権はないが、事業は止まる。
・工事課長は常用の手間しか見ていない。`,
}

const SEATS = {
  F1: '工場長（現場の再現性）→ 親会社 生産技術部（実務性・説明可能性、合議）→ 親会社 調達本部（価格のみ、資料は読まない、相見積3社が規程）',
  F2: '製造部長（現場の再現性）→ 社長（財源・価格、単独決裁、親会社なし）',
  K1: '作業所長（実務性）→ 本社 工務部（実務性・説明可能性、合議）→ 常務会（財源・説明可能性、合議、資料は読まない、完成工事総利益で見る）。買い手自身が元請',
  K2: '工事課長（実務性）→ 社長（価格のみ、単独決裁）。加えて元請A社の安全衛生管理責任者が拒めば事業は止まる',
}

const CELLS = [
  { id: 'F1-P1', seg: 'F1' }, { id: 'F1-P2', seg: 'F1' },
  { id: 'F2-P1', seg: 'F2' }, { id: 'F2-P2', seg: 'F2' },
  { id: 'K1-P1', seg: 'K1' }, { id: 'K1-P2', seg: 'K1' },
  { id: 'K2-P1', seg: 'K2' }, { id: 'K2-P2', seg: 'K2' },
]

const results = await pipeline(
  CELLS,
  (c) =>
    agent(
      `Read the file /home/claude/work/prompts8_v6.json (a JSON array). Find the element whose "id" is exactly "${c.id}".

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
