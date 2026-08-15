# このリポジトリでの作法（Claude Code 向け）

営業資料生成モデル。中核は「文章を書く機械」ではなく
**「この買い手・この状況で、何が通り何が落ちるかを機械的に決める機械」**です。

## あなたの持ち場

**検証**です。実装の細部と回帰、物差しの検分、仕様書の債務返済。
走行（マルチエージェント）と版付けは Cowork 側が持ちます。

- 詳細 → **`引き継ぎ書-VSCode-第14版.md`（最初にこれを読む）**
- 前版 → `引き継ぎ書-VSCode-コード検証.md`（第13.6版。置き換え済み）
- 面の分担 → `役割分担-3面.md`
- モデルの現在地と次の一手 → `モデル-流れの図解.html`（flow.html・第14版）／`第14版-畳んだ.md`
- 仕様 → `SPEC8.md`（第11版まで。A24〜A54・N₄′・N₆追補・R20 が未記載＝債務。**型の側から書けば短くなる**）

## 動かす

```bash
python3 test_sales_logic.py
python3 test_v14_2.py
python3 test_v14_3.py
python3 -c "from sales_logic import audit_requirements as a, audit_symbols as b; print(len(a()), len(b()))"
python3 audit_model.py
python3 triage_codes.py
python3 audit_matchers.py
python3 render_slides.py --check
python3 feasible136.py
python3 regen_v13.py
```

期待値は `314項目すべて ok` ／ `8 0` ／ `8セルとも解が在る` ／ `整合性チェックの (3)(4)(5) が「なし」`。
外部ネットワーク・乱数・時刻に依存しません。標準ライブラリのみ。

25業界21件の採点し直しだけは、別枝の走行物が要ります（無ければ飛ばして構いません）。

```bash
git fetch industry-run.bundle refs/heads/industry23-it-consulting:refs/remotes/bundle/industry23
python3 rescore21.py
```

`regen_v13.py` は `decisions8_v13.json` と `prompts8_v13_arm*.json` を**書き直します**。
中身は同じでも `_stamp` が今の版で上書きされ、**その表を作ったコードの来歴が消えます**。
確かめるために走らせたなら `git checkout --` で戻してください。

## 守ること

1. **モデルの意味論を変えない。**検査の閾値・定義域・語の変更は**提案まで**。
   走行の途中で意味が動くと、アノマリーの効果測定が切り分け不能になります。
2. **回帰テストを先に書いて落としてから直す。**テスト名に「何が起きていたか」を書く。
3. **`predict_*.md` は書き換えない。**走行前に置いた予測です。外れも記録。
4. **as-run（`decisions8_v10.json`・`prompts8_v11_arm*.json`）を上書きしない。**
5. **`_stamp` を持つ JSON は `stamp.load()` で読む。**`json.load` だと包みが返ります。
6. **版はタグで指す。**短縮ハッシュで指さない。
7. **記号を足す前に `GLOSSARY` を見る。**同じ記号が既に在るなら、書き分け（`distinct`）を
   書かないと `audit_symbols()` が落とします（N₆ 追補「担体は一つ」・第14版）。
8. **⊥ かどうかは `is_bottom` でだけ決める。**`UNIT_UNKNOWN` を生で引かないこと
   （記入欄【　　　】が漏れます）。**⊥ を別の欄で代用しない** ―― `a or b` で埋めない。
   担体の一意性は、記号の名前だけでなく**述語**にも要ります（**A55**・第14.3版）。

## この設計で最も多い欠陥

**モデルの誤りではなく、検査の誤りです。**「浅い一致」は **A54** として畳みました（8件）。
**監査の道具にも出ます** ―― `audit_model.py` の正規表現が `R6b` を拾えず、理由コードを 199 と数えていた（正しくは 254）。

```
own_retracted の数え方   散文の否定を非 null と数えた            12→6
「タダ」の照合            接続詞の「ただ、」に当たった             16→2
SLOT_RE                 括弧の中に空白しか無い前提。9個置いて0個判定
散文で苦情を数える物差し    前の版の語彙で較正されていた（申告16／散文3）
R20 の is_bottom        記入欄【　　　】を「値が在る」と読んだ。停止0→21件
audit_model の正規表現①  R6b の小文字を拾えず、理由コードを 199 と数えた（正しくは 254）
audit_model の正規表現②  記号名・ブロック名・規則発火名まで拾った        257→208
audit_model の正規表現③  `_` を必須にし、UNCALIBRATED を見落とした
audit_model の正規表現④  f-string の `R7_{d}_OK` 系9件を取りこぼした
発火の数え方             走行 JSON を生テキストで舐め、`blocks`/`rules` を発火と数えた 90→44
                        自己申告の集計鍵 `"KAPPA_MERGED": 0` ―― **値が 0** ―― も「出た」と数えた
```

**理由コードとは「`Finding`／`Judgment` の第1引数に渡る文字列」です。**構文木で取ってください。
**発火とは「判定欄（`findings`／`needs_judgment`／`post_*`）に載ったこと」です。**

**⊥ を値として扱っている箇所**と**境界を取らない部分一致**を、まず疑ってください。
`N₂` は「⊥ はいかなる値とも比較できない」と言います。
空文字・`None`・記入欄・「なし」「未定」・散文での否定 ―― 全部 ⊥ です。
