#!/usr/bin/env python3
"""
excerpt.py: друкує рядки збереженого джерела дослівно, без номерів.

    python3 excerpt.py page.txt 120 145
    python3 excerpt.py page.txt 120 145 --count

У claims.json фрагмент задається так само:
"source_file": "page.txt", "lines": [[120, 145]].
"""

import re
import sys
from pathlib import Path


def read_lines(path, ranges):
    rows = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(\d+)\| ?(.*)$", raw)
        if match:
            rows[int(match.group(1))] = match.group(2)
    out = []
    for start, end in ranges:
        out.extend(rows[i] for i in range(int(start), int(end) + 1) if i in rows)
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    text = read_lines(sys.argv[1], [(sys.argv[2], sys.argv[3])])
    print(len(text.split()) if "--count" in sys.argv else text)
