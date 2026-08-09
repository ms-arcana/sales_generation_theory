# -*- coding: utf-8 -*-
import time
from datetime import date
from core import *
from core2 import *

TODAY = date(2026,8,6)
S = lambda nm,k,c,g,o,r=True: Seat(nm,k,c,g,o,r)

print("【項目13】j* の定義")
J=[S("看護部長","実務性","月次","単独","社内"),S("事務局","財源","予算年度","合議","社内"),
   S("市 情報政策課","説明可能性","庁内更改","合議","社外"),S("契約担当","説明可能性","契約規則","単独","社内",False),
   S("病院事業管理者","財源","事業年度","単独","社内",False)]
n=Nu(A="使っても分からない",I="1〜2年",S1="100〜1000万",S2="単発",S3=True,C_move="ふつう",
     J=J,procedural=True,downward=False,segment="公立病院",industry="医療",product="IT",
     E_reader="比較検討中",E_judge="手段を知らない",tau=[],M=[],LT_months=8)
print("  読む座席のうち最も遠い =", j_star(n).name, "／ 最終裁定者 =", n.J[-1].name)
print("  → 従来 J[-1] を使っていたのは実装の誤り。κ も違う（%s vs %s）\n" % (j_star(n).kappa, kappa_n(n)))

print("【項目2/20】未確定フィールド")
txs=[TauX(TauItem("C",date(2027,10,1),"公的暦","既知","約570万円","財源"),confirmed=False),
     TauX(TauItem("B",date(2026,10,15),"公的暦","既知","約30日","実務性"),confirmed=False)]
ok,msgs=tau_gate(txs)
for m in msgs: print("  ",m)
print()

print("【項目11】量の感度")
tx=TauX(TauItem("C",date(2027,4,1),"法令","未知","入院診療単価5.0万円×稼働率85%"),q_low=1785e4,q_high=2550e4)
print("  ",q_sensitivity(tx,2000e4))
print("  ",q_sensitivity(replace(tx,q_low=2100e4),2000e4))
print()

print("【項目16】データ取得LTの加算（自己言及の解消）")
txb=[TauX(TauItem("B",date(2026,10,1),"契約","未知"),q_source="買い手データ")]
print("  LT(P)=6か月 → 実効LT =",effective_LT(replace(n,LT_months=6),txb),"か月（要員名簿の取得1か月を加算）")
print()

print("【項目14】τ の優先順位")
tt=[TauX(TauItem("D",date(2027,4,1),"法令","未知")),TauX(TauItem("B",date(2026,9,30),"契約","既知")),
    TauX(TauItem("A",date(2027,12,31),"法令","未知"))]
print("  ",[f"{t.item.form}({M0_KILL[t.item.form]})" for t in tau_priority(tt)])
print()

print("【項目18】⑤の2つを選ぶ規則")
M=[Mi("拠点での運用改善","内製","D5"),Mi("現行ベンダー","既存外注","D2"),Mi("競合SaaS","競合","D1"),Mi("本部指定","取引上位者の指定","D6c")]
p,why=pick_two(M)
print("  ",[m.name for m in p]); print("  理由:",why); print()

print("【項目3】δ の候補提示 2問の自動生成")
for q in questions({"D2","D4","D5","D6b"}): print("  ",q)
print()

print("【項目12/21/23】R7 を売り手マスタで決定的に検査")
sf_ok=SellerFacts({"IT導入支援事業者 第xxxxx号"},{"在職ドライバー直接接触":1240,"外国人材(特定技能)":380},{"直近":"接触214→面接41→入社9"})
sf_ng=SellerFacts(set(),{},{})
for m in check_R7([Mi("競合","競合","D6a"),Mi("市場","競合","D6b")],sf_ok): print("  [充足]",m)
for m in check_R7([Mi("競合","競合","D6a"),Mi("市場","競合","D6b")],sf_ng): print("  [不足]",m)
print()

print("【項目22】6次元に該当しない拘束")
print("  ",out_of_scope("商圏相場を下回る賃金レンジで半年0件"))
print()
N=20000; t0=time.perf_counter()
for _ in range(N):
    j_star(n); tau_gate(txs); tau_priority(tt); pick_two(M); questions({"D2","D5"}); check_R7([Mi("x","競合","D6b")],sf_ok)
print("計時：(A)群の追加検査 %d回を %.3f秒 → 1商談あたり **%.1f マイクロ秒**"%(N,time.perf_counter()-t0,(time.perf_counter()-t0)/N*1e6))
