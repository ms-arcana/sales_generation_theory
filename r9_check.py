# -*- coding: utf-8 -*-
"""R9 提示変換 検査器 — 層2.5 に組み込む最小実装"""
import re, json

BANNED = [
 r'消去対象', r'(?<!法)消去(?!法)', r'残余', r'カテゴリ\s*C',
 r'M[_₀-₉][0-9i]|M_[0-9i]|Mᵢ',
 r'様相', r'必然化', r'問題化', r'内在的否定', r'措定', r'実然', r'可能態',
 r'warrant|ウォラント',
 r'前提化', r'承認を積', r'資本として', r'共著者',
 r'蝶番', r'縮退', r'様相の階段',
 r'\bD[1-6]\b', r'拘束の所在',
 r'T-[A-E]', r'閉扉', r'開扉', r'漸増形式',
 r'エンテュメーメ', r'省略三段論法',
 r'を立証', r'を担保', r'着弾', r'という論点',
]
NEG_ENUM = r'[はも](?:届かない|解決しない|できません|不可能)'

def check5(text, max_mi=2):
    hits = [p for p in BANNED if re.search(p, text)]
    # 選択肢の列挙検出：読点で区切られた3項以上＋否定
    enum = len(re.findall(r'[、，]', text)) >= 3 and re.search(NEG_ENUM, text)
    return {'banned': hits, 'enum_negation': bool(enum), 'pass': not hits and not enum}

BEFORE = "消去対象はM_0（今のまま／来期送り）、M_1（情報システム部と生産技術部による内製移行）、M_2（既存ベンダーの延長保守で2030年末まで引き延ばす）。M_1について能力の話は申し上げません、御社の情シス6名は2027年度に第二工場の生産管理立ち上げのマイルストーンを持っており、現行アドオンの棚卸だけで8人月と見込まれる移行工数をそこへ割く判断は、新工場の立ち上げを後ろへずらす判断と同じものだ、という配分の問題です。"
AFTER = "移行に必要な工数は、現行アドオンの棚卸だけで8人月と見込まれます。この8人月を出せる要員は、2027年度に第二工場の生産管理立ち上げを担当する6名と同一です。延長保守で2030年末まで引き延ばした場合も、この重なりは解消せず、立ち上げ時期が後ろへずれる年が変わるだけになります。"

print('BEFORE:', check5(BEFORE))
print('AFTER :', check5(AFTER))
print()
# 全125本の⑤に適用
d = json.load(open('ind25.json'))
tot = ng = 0
for r in d['industries']:
    for p in r['products']:
        tot += 1
        if not check5(p['line_5'])['pass']: ng += 1
print('現行の⑤ %d本中 %d本が R9 で棄却される (%.0f%%)' % (tot, ng, ng/tot*100))
tot4 = ng4 = 0
for r in d['industries']:
    for p in r['products']:
        tot4 += 1
        if not check5(p['line_4'])['pass']: ng4 += 1
print('現行の④ %d本中 %d本が R9 で棄却される (%.0f%%)' % (tot4, ng4, ng4/tot4*100))
