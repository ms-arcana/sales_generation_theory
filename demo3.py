# -*- coding: utf-8 -*-
import time
from anomaly_fix import *

print("=== A1：④の量が最終裁定点で両替できるか ===")
print(" 公立病院 j_n=事業管理者(κ=財源) に 時間の量 を出した場合")
print("  ", a1_check("実務性", "財源", None))
print("  ", a1_check("実務性", "財源", "看護師長7名の管理職手当は固定。減るのは時間外ではなく、"
                                      "夜勤専従の会計年度任用職員2名分の任用（年1,280万円）の要否判断"))
print(" 医療法人 j_n=理事長(κ=財源) に 金額の量 を出した場合")
print("  ", a1_check("財源", "財源", None))
print()

print("=== A2：B1 が立つときの⑥カテゴリ内差別化 ===")
print("  ", a2_check(True, SellerDiff()))
print("  ", a2_check(True, SellerDiff({"同型の実名事例": "△△運輸（12拠点・3年更改）",
                                       "認定・登録の非対称": "業務前自動点呼の使用機器認定 第xx号"})))
print("  ", a2_check(False, SellerDiff()))
print()

print("=== A4-a：⑥が④の問題を反復させていないか ===")
s4 = "会計年度任用職員は1年で任期が切れ、翌年また同じ公募と選考を回します。この時間と円は毎年発生します。"
print("  ", r10a(s4, Declared(s4_period_months=12, s6_period_months=12)))
print("  ", r10a(s4, Declared(s4_period_months=12, s6_period_months=36)))
print("  ", r10a(s4, Declared()))
print()

print("=== A4-b：②の単位が⑥で保持されているか ===")
d = Declared(s2_unit="枠", s2_from_unit="床")
print("  ", r10b("東3病棟を12床で部分再開すると、夜勤帯は124枠のまま必要です。", d))
print("  ", r10b("90枠は124枠の73%ですので、12床の部分再開が可能です。", d))
print("  ", r10b("東3病棟を12床で部分再開できます。", d))
print()

N=50000; t0=time.perf_counter()
for _ in range(N):
    a1_check("実務性","財源",None); a2_check(True,SellerDiff({"同型の実名事例":"x"})); r10(s4,"…枠…",d)
print("計時：A1+A2+A4 を %d回 %.3f秒 → 1商談あたり **%.1f マイクロ秒**"%(N,time.perf_counter()-t0,(time.perf_counter()-t0)/N*1e6))
