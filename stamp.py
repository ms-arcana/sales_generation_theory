# -*- coding: utf-8 -*-
"""走行の出力に、そのとき動いていたコードの版を刻む。

二拠点・二スレッドで走らせると「その決定表はどの版で計算したのか」が必ず混ざる。
第10版で一度混ざりかけた（decisions8_v10.json が第11版で再計算されていた）。

  from stamp import stamp
  stamp("run8_v12.json")     # → {"_stamp": {...}} を先頭に足す
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


def stamp(path: str) -> dict:
    v = version()
    d = json.load(open(path, encoding="utf-8"))
    out = {"_stamp": v, "data": d} if isinstance(d, list) else {**d, "_stamp": v}
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return v


if __name__ == "__main__":
    print(json.dumps(version(), ensure_ascii=False, indent=1))
