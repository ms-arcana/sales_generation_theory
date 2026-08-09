# -*- coding: utf-8 -*-
import time, statistics
from datetime import date
from core import *

TODAY = date(2026, 8, 6)

def seat(nm,k,c,g,o,r=True): return Seat(nm,k,c,g,o,r)

CELLS = {}
CELLS["MED-PUB-IT"] = Nu(
  A="使っても分からない", I="1〜2年", S1="100〜1000万", S2="単発", S3=True, C_move="ふつう",
  J=[seat("看護部長","実務性","月次","単独","社内"), seat("事務局","財源","予算年度","合議","社内"),
     seat("市 情報政策課","説明可能性","庁内更改","合議","社外"), seat("契約担当","説明可能性","契約規則","単独","社内"),
     seat("病院事業管理者","財源","事業年度","単独","社内")],
  procedural=True, downward=False, segment="公立病院", industry="医療・病院", product="IT",
  E_reader="比較検討中", E_judge="手段を知らない",
  tau=[TauItem("C", date(2027,10,1), "公的暦", "既知", "45営業日→9月定例会控除で約30日", "実務性"),
       TauItem("B", date(2026,10,15), "公的暦", "既知", "12か月＝84回＝1,512時間＝約570万円", "実務性"),
       TauItem("Ec", date(2027,3,31), "法令", "未知")],
  M=[Mi("現状維持","M0"), Mi("情シスによる内製","内製","D5"),
     Mi("既存ベンダーの追加開発","既存外注","D2"), Mi("市の全庁標準指定","取引上位者の指定","D6c")],
  LT_months=8)

CELLS["MED-PRV-IT"] = Nu(
  A="使っても分からない", I="1〜2年", S1="100〜1000万", S2="単発", S3=False, C_move="ふつう",
  J=[seat("事務長","実務性","月次","単独","社内"), seat("理事長","財源","事業年度","単独","社内")],
  procedural=False, downward=False, segment="医療法人", industry="医療・病院", product="IT",
  E_reader="手段を知らない", E_judge="手段を知らない",
  tau=[TauItem("C", date(2027,4,1), "法令", "未知", "120床の65日＝約7,000万円", "財源")],
  M=[Mi("現状維持","M0"), Mi("事務長が続ける","内製","D5"), Mi("電子カルテベンダー","既存外注","D2")],
  LT_months=4)

CELLS["LOG-3PL-IT"] = Nu(
  A="使えば分かる", I="5〜10年", S1="1000万〜", S2="単発", S3=True, C_move="大仕事",
  J=[seat("センター長","実務性","月次","単独","社内"), seat("本部長","実務性","四半期","単独","社内"),
     seat("購買部門","価格","購買規程","単独","社内"), seat("投資委員会","財源","四半期","合議","社内")],
  procedural=False, downward=True, segment="3PL大手", industry="運輸・交通・物流", product="IT",
  E_reader="比較検討中", E_judge="比較検討中",
  tau=[TauItem("C", date(2027,4,1), "法令", "未知", "年 約66,000回の点呼", "実務性"),
       TauItem("B", date(2026,9,30), "契約", "既知", "四半期委員会を逃すと待ちは年度1本", "財源")],
  M=[Mi("現状維持","M0"), Mi("拠点での運用改善","内製","D5"),
     Mi("現行TMSベンダー","既存外注","D2"), Mi("競合SaaS","競合","D1")],
  LT_months=6)

# 過去日・売り手都合・δ違反を混ぜた不良入力
CELLS["BAD-EXAMPLE"] = Nu(
  A="使えば分かる", I="1〜2年", S1="100〜1000万", S2="単発", S3=False, C_move="ふつう",
  J=[seat("担当","実務性","月次","単独","社内")],
  procedural=False, downward=False, segment="—", industry="—", product="—",
  E_reader="困っていない", E_judge="困っていない",
  tau=[TauItem("A", date(2024,1,1), "法令", "未知"),                       # 過去日
       TauItem("B", date(2026,9,1), "売り手都合", "未知"),                  # 売り手都合
       TauItem("D", date(2026,10,1), "公的暦", "既知")],                    # T-D単独＋既知で量なし
  M=[Mi("現状維持","M0"), Mi("内製","内製","D1")],                           # D1×内製＝禁止
  LT_months=6)

# 低関与・反復購買（縮退テスト）
CELLS["OFFICE-LIKE"] = Nu(
  A="買う前に分かる", I="いつでも止められる", S1="〜10万", S2="週次以上", S3=False, C_move="すぐ試せる",
  J=[seat("総務課長","価格","月次","単独","社内")],
  procedural=False, downward=False, segment="—", industry="—", product="消耗品",
  E_reader="うちも知っている", E_judge="うちも知っている",
  tau=[TauItem("A", date(2027,3,31), "契約", "既知", None)],
  M=[Mi("現状維持","M0"), Mi("既存代理店","既存外注","D2")],
  LT_months=1)

for k, v in CELLS.items():
    r = compile_deal(v, TODAY)
    print("="*72)
    print(k, " → 生成可" if r["generate"] else " → ★停止")
    print("  Σ =", "".join(r["Sigma"]), " (", r["Sigma_by"], ")")
    print("  τ 通過:", r["tau_ok"])
    for m in r["tau_msg"]: print("   ", m)
    print("  δ:", r["delta"])
    for m in r["delta_msg"]: print("   ", m)
    print("  発火:", " / ".join(r["rules"]))
    print("  点灯ブロック:", ", ".join(r["blocks"]))
    print("  必要なLLM呼び出し:", r["llm_calls_needed"], "回")

# 計時
N = 10000
t0 = time.perf_counter()
for _ in range(N):
    for v in CELLS.values():
        compile_deal(v, TODAY)
t1 = time.perf_counter()
per = (t1 - t0) / (N * len(CELLS)) * 1e6
print("\n" + "="*72)
print("計時：%d商談の導出を %.3f 秒 → 1商談あたり **%.1f マイクロ秒**" % (N*len(CELLS), t1-t0, per))
print("θ_auto：δ=%.4f ／ 移送入力=%.4f ／ τ=%.4f" % (theta_auto("delta"), theta_auto("transport"), theta_auto("tau")))
print("segment_action(δ, c=0.85, 候補2) →", segment_action("delta", 0.85, 2))
print("segment_action(移送, c=0.85, 候補2) →", segment_action("transport", 0.85, 2))
