"""CLI: `python3 -m regionlab check <file.rlab>`"""
from __future__ import annotations

import sys

from .checker import CheckError, check
from .parser import ParseError, parse


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "check":
        sys.stderr.write("usage: python3 -m regionlab check <file.rlab>\n")
        return 2
    with open(argv[2], "r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        prog = parse(text)
        check(prog)
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 1
    except CheckError as e:
        print(f"error[{e.code}] (line {e.line}): {e.msg}", file=sys.stderr)
        return 1
    print(f"{argv[2]}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
