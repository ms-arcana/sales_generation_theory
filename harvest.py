# -*- coding: utf-8 -*-
"""ワークフローの journal.jsonl から、各エージェントの返り値を取り出してファイルに落とす。

  python3 harvest.py <journal.jsonl のあるディレクトリ> <出力ディレクトリ> <鍵>

  鍵 … 返り値のどの欄をファイル名にするか（例 cell_id, seat）。複数なら "__" でつなぐ。

**突合はワークフロー側の依頼値を正とする**という申し合わせがあるので、
ここで名前に使うのは返り値の申告値である。取り違えは呼び出し側（validate*.py）で検出する。
"""
import json
import pathlib
import sys


def main():
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2]); dst.mkdir(exist_ok=True)
    keys = sys.argv[3].split(",")
    n = 0
    for line in (src / "journal.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "completed":
            continue
        val = rec.get("result")
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                pass
        if not isinstance(val, dict):
            print(f"  ★ dict でない返り値を飛ばした: {str(val)[:80]}")
            continue
        name = "__".join(str(val.get(k, "?")) for k in keys)
        (dst / f"out_{name}.json").write_text(
            json.dumps(val, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    print(f"取り出した {n} 件 → {dst}/")
    for p in sorted(dst.glob("out_*.json")):
        print("   ", p.name)


if __name__ == "__main__":
    main()
