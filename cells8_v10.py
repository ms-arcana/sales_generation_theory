# -*- coding: utf-8 -*-
"""第10版 ―― 商材座標と構造キーを入れた8セル。第8版と同じ業界・同じ買い手人格で走らせる対照実験。

第8版からの差は3点だけで、いずれも第9・10版で入れた欄である。
  商材座標   ν θ σp ω α β1 β2（較正表がここから導出される）
  構造キー   事例の同型性を {拘束の所在, 執行座席の同型, 暦の同型} で測る
  第9版の修正 座席の由来 / 決定が締まる日 / D5 の拘束者 / 無料の手段

検定したい予測は二つ。
  (1) ISO_CONTEXT_MISSING が 16/16 → 0 に落ちるか（構造キーの効果）
  (2) 座席3つのセルの上申が 0/4 から動くか（A16 の ∀k 修正の効果）
"""
import copy, json
from dataclasses import replace
from datetime import date
from sales_logic import Product, TauItem, Mi, Scope, compile_deal
import cells8_v9 as B

TODAY = B.TODAY

# ───────────────────────────── 商材座標（α は商材×適用先で決まるのでセル別）
PROD = {
 "E1-P1": Product("使っても分からない","段階分割","低",3,"低","低","費用処理","変動","予算計上済"),
 "E1-P2": Product("使えば分かる","段階分割","高",6,"高","低","資産計上","固定","予算外"),
 "E2-P1": Product("使っても分からない","段階分割","低",3,"低","低","費用処理","変動","予算計上済"),
 "E2-P2": Product("使えば分かる","段階分割","高",6,"高","低","資産計上","固定","予算外"),
 # 小売の販促は POS で効果が測れ、媒体は売り手が統制し、媒体費は変動費 → 実務性↔価格が開く
 "R1-P1": Product("使えば分かる","完全分割","低",1,"高","高","費用処理","変動","予算計上済"),
 "R1-P2": Product("使えば分かる","段階分割","高",6,"高","低","資産計上","固定","予算外"),
 "R2-P1": Product("使えば分かる","完全分割","低",1,"高","高","費用処理","変動","予算計上済"),
 "R2-P2": Product("使えば分かる","段階分割","高",6,"高","低","資産計上","固定","予算外"),
}

# ───────────────────────────── 構造キー（Π3 の λ で測る。所轄庁・系列は使わない）
CTX = {
 "E1": {"拘束の所在":"制度","執行座席の同型":"法人事務局が人件費と業務委託費を持つ","暦の同型":"外部機関の審査日で締まる"},
 "E2": {"拘束の所在":"買い手の資源","執行座席の同型":"経営者が人件費を単独で動かす","暦の同型":"認可の申請締切で締まる"},
 "R1": {"拘束の所在":"上位者","執行座席の同型":"本部が販促費と人時を分けて持つ","暦の同型":"卸との定番改訂商談で締まる"},
 "R2": {"拘束の所在":"買い手の資源","執行座席の同型":"経営者が人時と仕入を単独で動かす","暦の同型":"自分で決める"},
}
CASES = {
 "ad": [{"実名":"△△学院大学","拘束の所在":"制度","執行座席の同型":"法人事務局が人件費と業務委託費を持つ",
         "暦の同型":"外部機関の審査日で締まる"},
        {"実名":"○○ストア株式会社","拘束の所在":"上位者","執行座席の同型":"本部が販促費と人時を分けて持つ",
         "暦の同型":"卸との定番改訂商談で締まる"},
        {"実名":"□□学園（専修）","拘束の所在":"買い手の資源","執行座席の同型":"経営者が人件費を単独で動かす",
         "暦の同型":"認可の申請締切で締まる"}],
 "it": [{"実名":"□□女子大学","拘束の所在":"制度","執行座席の同型":"法人事務局が人件費と業務委託費を持つ",
         "暦の同型":"外部機関の審査日で締まる"},
        {"実名":"◇◇フーズ株式会社","拘束の所在":"上位者","執行座席の同型":"本部が販促費と人時を分けて持つ",
         "暦の同型":"卸との定番改訂商談で締まる"},
        {"実名":"◎◎商店（3店舗）","拘束の所在":"買い手の資源","執行座席の同型":"経営者が人時と仕入を単独で動かす",
         "暦の同型":"自分で決める"}],
}

# ───────────────────────────── 第9版で止まった箇所を、モデルの言うとおりに直した τ / M
TAU_NINKA = TauItem("A", date(2027,6,30), "公的暦", "未知",
    q="次年度の認可申請までに確定していない募集定員", q_kappa="財源",
    q_source="買い手データ", q_low=30, q_high=60, scope=B.B.SC_SENSHU,
    q_receipt="2026-07-20 事務局より受領。学科別の在籍・退学者一覧",
    decision=True, windows=1, binders=("都道府県私学担当課",))
TAU_SHODAN2 = TauItem("A", date(2027,9,30), "契約", "未知",
    q="秋の定番改訂商談までに確定していない売場の作業時間", q_kappa="実務性", q_recast=True,
    q_source="買い手データ", q_low=900, q_high=1400, scope=B.B.SC_SUPER,
    q_receipt="2026-07-28 店舗運営部より受領。全店の作業割当表",
    decision=True, windows=1, binders=("主要卸（一次問屋）",))

TAU_NINKA_NEXT = replace(TAU_NINKA, d=date(2028, 6, 30))   # LT が足りないので次の窓へ（R6b）

TAU = {"E1": lambda t: t,                       # 第9版のまま（認証評価が生きている）
       "E2": lambda t: [TAU_NINKA],
       "R1": lambda t: [TAU_SHODAN2, replace(B.B.TAU_KOUREI, decision=True, windows=1)],
       "R2": lambda t: [TAU_SHODAN2, replace(B.B.TAU_KOUREI, decision=True, windows=1)]}

# 卸の販促支援は「取引上位者の指定」として D6c 主位置で扱う（無料の手段は D6 系でしか消えない）
M_OROSHI = Mi("主要卸の販促支援を使う", "取引上位者の指定", frozenset({"D6c"}), ("D6c",),
              binders=(("D6c","主要卸（一次問屋）"),), cost_to_buyer=0.0)

CELLS = []
for c0 in B.CELLS:
    c = dict(c0); nu = copy.deepcopy(c0["nu"]); seg = c["id"][:2]
    nu.prod = PROD[c["id"]]
    # 構造キー（事例の同型性用）と、適用対象の照合に要る属性を併せて持つ。
    # 所轄庁・系列は入れない —— それが λ の粗い代理変数だった。
    nu.buyer_context = {**c0["nu"].buyer_context, **CTX[seg]}
    nu.buyer_context.pop("所轄庁", None); nu.buyer_context.pop("系列", None)
    nu.tau = TAU[seg](nu.tau)
    if c["id"] == "E2-P2":
        nu.tau = [TAU_NINKA_NEXT]
    # 読み手自身が枠を持つセルでは D5 が立たない → 内製を⑤から外す（A20 の言うとおり）
    if seg in ("E2", "R2"):
        nu.M = [m for m in nu.M if "D5" not in m.dims]
    nu.M = [M_OROSHI if "卸" in m.name else m for m in nu.M]
    # A43（第13.5b版）：買い手の繁忙期。**これは較正値であり、導出ではない。**
    # 出所は第13.5版の買い手16体の言葉そのもの（`stage135/buyers.json`）。
    #   「一般選抜の出願が立ち上がるところ」「2027年12月27日までの繁忙期」   → 学校 12・1・2月
    #   「募集説明会の準備が始まる時期そのもの」                             → 学校 10・11月
    #   「お盆の直前」「一年で一番人手の要る時期」「秋の改訂」               → 小売 7・8・9月・12月
    # したがって「買い手が繁忙期を理由に棄却しなくなるか」は**循環に近い**。
    # ここで測れるのは〈渡した季節を生成器が守るか〉だけである。
    # 導出の側（効果発現ラグ ω）は循環しない。予測ではこの二つを分けて置く。
    nu.busy_months = (10, 11, 12, 1, 2) if seg.startswith("E") else (7, 8, 9, 12)
    c["nu"] = nu; CELLS.append(c)

SELLERS = {k: replace(v, named_cases=CASES["ad" if k=="ad" else "it"])
           if False else v for k, v in B.SELLERS.items()}
for k in SELLERS:
    SELLERS[k].named_cases = CASES[k]


def run(dump="decisions8_v10.json"):
    msgs = json.load(open("messages.json", encoding="utf-8"))
    out = []
    for c in CELLS:
        d = compile_deal(c["nu"], SELLERS[c["seller"]], TODAY)
        rec = {k: c[k] for k in ("id","業界","セグメント","商材")}
        rec.update({k: d.get(k) for k in
            ("generate","sigma","j_star","kappa_n","form_n","tau_ok","delta","five_mentions",
             "d7_basis","blocks","rules","executors","start_deadline","chain","talk_guide",
             "lt_months","today","decide_deadline",
             "decision_gates","omega","busy_months")})   # A41・A43
    # A37：⑥の日付は〈決定〉〈着手〉〈実現〉の三段。表に載せないと指示へ渡らない
    # A37b：start_deadline の担体は決定期限。鍵名は旧走行との突合のために残し、正しい名を足す
        rec["findings"]=[{"code":f.code,"level":f.level,"ref":f.ref,
                          "msg":msgs["findings"].get(f.code,f.code)} for f in d["findings"]]
        rec["needs_judgment"]=[{"code":j.code,"ref":j.ref,
                                "msg":msgs["judgments"].get(j.code,j.code)} for j in d["needs_judgment"]]
        rec["seats"]=[{"name":s.name,"kappa":sorted(s.kappa),"chi":s.chi,"gamma":s.gamma,
                       "reads":s.reads,"form":sorted(s.form),"origin":s.origin} for s in c["nu"].J]
        rec["veto"]=[v.name for v in c["nu"].V]
        rec["gamma_own"]=c["nu"].gamma_pre
        rec["prod"]=vars(c["nu"].prod)
        out.append(rec)
    # 第12.5版：刻むのを呼び出し側に任せていたので、run() を直接叩くと刻まれなかった。
    # 第12版で踏んだ配管の罠（古い決定表が指示文へ入る）がそのまま踏み直せる状態だった。
    # **書き出す側で刻む。** 読む側は stamp.load() で両方の形を受ける。
    from stamp import dump_stamped
    dump_stamped(out, dump)
    iso=sum(1 for r in out if any(j["code"]=="ISO_CONTEXT_MISSING" for j in r["needs_judgment"]))
    for r in out:
        st=[f"{f['code']}({f['ref']})" for f in r["findings"] if f["level"]=="stop"]
        rj=[f["code"] for f in r["findings"] if f["level"] in ("reject","demote")]
        print(f"{r['id']:6s} {'生成可' if r['generate'] else '★不成立'} Σ={''.join(r['sigma'] or [])}"
              f" 座席{len(r['seats'])} D7={r['d7_basis']}")
        if st: print("        停止",st)
        if rj: print("        棄却/降格",rj)
    print(f"\n生成可 {sum(1 for r in out if r['generate'])}/{len(out)}"
          f"   ISO_CONTEXT_MISSING {iso}/{len(out)}（第8版は 8/8）")
    return out


if __name__ == "__main__":
    run()
