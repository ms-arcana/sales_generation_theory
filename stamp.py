# -*- coding: utf-8 -*-
"""走行の出力に、そのとき動いていたコードの版を刻む。

二拠点・二スレッドで走らせると「その決定表はどの版で計算したのか」が必ず混ざる。
第10版で一度混ざりかけた（decisions8_v10.json が第11版で再計算されていた）。

  from stamp import stamp, load, dump_stamped
  stamp("run8_v12.json")        # → {"_stamp": {...}} を先頭に足す（何度掛けても二重にならない）
  dec = load("decisions8_v12.json")   # 刻んであっても無くても、中身だけ返す

第12.5版 ―― 罠が半分しか塞がっていなかった。
`stamp()` は**呼んだときだけ**刻むので、`cells8_v10.run()` を直接叩けば刻まれない。
刻むのを呼び出し側の作法に任せていると、作法を知らない経路が必ず一つ残る。
だから**書き出す側で刻む**（`run()` の中）。読む側は `load()` で両方の形を受ける。
"""
import hashlib
import json
import subprocess


def version() -> dict:
    def sh(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, cwd=".").stdout.strip()
        except Exception:
            return ""
    h = hashlib.sha256(open("sales_logic.py", "rb").read()).hexdigest()[:12]
    return {
        "git": sh("git", "rev-parse", "--short", "HEAD"),
        "tag": sh("git", "describe", "--tags", "--always"),
        "dirty": bool(sh("git", "status", "--porcelain")),
        "sales_logic_sha256_12": h,
    }


def unwrap(d):
    """刻まれていれば中身を、刻まれていなければそのまま返す"""
    return d["data"] if isinstance(d, dict) and set(d) == {"_stamp", "data"} else d


def load(path: str):
    """決定表・走行結果を読む唯一の入口。刻みの有無を呼び出し側に意識させない"""
    return unwrap(json.load(open(path, encoding="utf-8")))


def stamp_of(path: str) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    return d.get("_stamp", {}) if isinstance(d, dict) else {}


def dump_stamped(obj, path: str) -> dict:
    """書き出す側で刻む。**これが唯一の書き出し口**（→ モジュール docstring）"""
    v = version()
    obj = unwrap(obj)
    out = {"_stamp": v, "data": obj} if isinstance(obj, list) else {**obj, "_stamp": v}
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return v


def stamp(path: str) -> dict:
    """既にあるファイルに刻む。二度掛けても入れ子にならない（`unwrap` を通す）"""
    return dump_stamped(json.load(open(path, encoding="utf-8")), path)


def assert_fresh(path: str, strict: bool = True) -> bool:
    """**配管の罠の本体はここ。** 刻むだけでは、古い表が指示文へ入るのを止められない。

    第12版：`fire_rules` に足した規則が `decisions8_v10.json` に入っておらず、
    指示文に一度も載らなかった。刻みがあっても、**照合しなければ気づけない**。
    指示文を組む前に、決定表がいまの `sales_logic.py` で計算されたものかを突き合わせる。
    """
    s = stamp_of(path)
    now = version()["sales_logic_sha256_12"]
    got = s.get("sales_logic_sha256_12")
    ok = got == now
    if not ok:
        msg = (f"決定表 {path} は古い版で計算されている："
               f"表={got or '刻み無し'} / いまのコード={now}。"
               f"  cells8_v10.run('{path}') で作り直すこと")
        if strict:
            raise SystemExit("★配管の罠：" + msg)
        print("※ " + msg)
    return ok


if __name__ == "__main__":
    print(json.dumps(version(), ensure_ascii=False, indent=1))
