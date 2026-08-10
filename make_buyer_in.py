# -*- coding: utf-8 -*-
"""盲検買い手の入力を作る ―― buyer_run/in_*.json

**盲検である。**買い手役に渡すのは
  ・自分が誰か（役職・判断基準・自分の様式にある語・自社の文脈）
  ・資料の本文（①〜⑥）
だけ。決定表・仕様・申告欄・検査結果・モデルの語彙は**一切渡さない**。

引き継ぎ書 §5：生成器・独立予測器・盲検買い手の3役を分ける。
突合はインデックス（セルID）で行う。

**★留保（引き継ぎ書 §5）**：盲検買い手も LLM である。ここで測れるのは
「仕様を満たした資料が**モデルの想定する買い手像**を通るか」であって、
実在の買い手を通るかではない。これは帰納ではない。
"""
import glob
import json
import pathlib

from stamp import load as unwrap, dump_stamped

STAGE_NAME = {"①": "1枚目", "②": "2枚目", "③": "3枚目",
              "④": "4枚目", "⑤": "5枚目", "⑥": "6枚目"}


def persona_of(spec, code):
    b = spec["buyer"]
    seats = b["seats"]
    readers = [s for s in seats if s.get("reads", True)]
    me = readers[-1] if readers else seats[-1]          # 最終裁定点（読む座席の最後）
    others = [s for s in seats if s["name"] != me["name"]]
    ctx = b.get("context", {})
    lines = [
        f"あなたは{spec['industry']}の買い手企業の【{me['name']}】である。",
        f"・会社の姿：{ctx.get('業態','')}／{ctx.get('規模','')}／{ctx.get('商圏','')}",
        f"・あなたが見るのは〈{'・'.join(me.get('kappa') or [])}〉だけ。問いは「{me.get('chi','')}」。",
    ]
    if me.get("form"):
        lines.append(f"・あなたの部署の文書に載っている語は {('／'.join(me['form']))} である。"
                     f"**この語で書かれていないものは、あなたの会議の議題にならない。**")
    if me.get("gamma") == "合議":
        lines.append("・あなたの場は合議で、最も保守的な一人が止めれば止まる。")
    else:
        lines.append("・決裁はあなた一人で下りる。")
    if others:
        lines.append("・社内の他の関係者：")
        for s in others:
            r = "この資料を読む" if s.get("reads", True) else "この資料は読まない"
            lines.append(f"    {s['name']}（{'・'.join(s.get('kappa') or [])}／{r}）")
    if b.get("veto"):
        lines.append(f"・決裁権は無いが止められる相手：{'／'.join(b['veto'])}")
    if b.get("upstream"):
        lines.append(f"・自社の上に立つ当事者：{'／'.join(b['upstream'])}")
    if b.get("gamma_pre"):
        lines.append("・この資料より前に、営業とすでに確認済みのこと："
                     + "／".join(f"{v}" for v in b["gamma_pre"].values()))
    return "\n".join(lines)


def main():
    dec = {r["id"]: r for r in unwrap("decisions_ind.json") if not r.get("_error")}
    specs = {}
    for f in sorted(glob.glob("nu/*.json")):
        s = json.load(open(f, encoding="utf-8"))
        specs[s["code"]] = s

    d = pathlib.Path("buyer_run"); d.mkdir(exist_ok=True)
    n = 0
    for fp in sorted(glob.glob("ind_run/out_*.json")):
        g = unwrap(fp)
        cid = g.get("cell_id") or pathlib.Path(fp).stem[4:]
        code = cid.split("-")[0]
        if code not in specs or cid not in dec:
            print(f"   ✗ {cid} 飛ばす"); continue
        slides = [{"枚": STAGE_NAME.get(s.get("stage"), s.get("stage")), "本文": s.get("text", "")}
                  for s in g["slides"]]
        rec = {
            "id": cid,
            "業界": dec[cid]["業界"],
            "商材の呼び名": dec[cid]["商材"],
            "あなたは誰か": persona_of(specs[code], code),
            "資料": slides,
        }
        dump_stamped(rec, str(d / f"in_{cid}.json"))
        n += 1
    print(f"盲検買い手の入力 {n}件 → buyer_run/in_*.json")
    print("渡していないもの：決定表・仕様・申告欄・検査結果・モデルの語彙")


if __name__ == "__main__":
    main()
