#!/usr/bin/env python3
"""Conformance runner for regionlab, mirroring tests/run_conformance.py's
own `//! expect:` convention (here `# expect:`) so the two test suites
read the same way even though the languages are unrelated."""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from regionlab.checker import CheckError, check   # noqa: E402
from regionlab.parser import ParseError, parse     # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
DIRECTIVE = re.compile(r"^#\s*expect:\s*(.+)$")


def run_one(path: str) -> tuple[bool, str]:
    raw = open(path, encoding="utf-8").read()
    want = "ok"
    for line in raw.splitlines():
        m = DIRECTIVE.match(line.strip())
        if m:
            want = m.group(1).strip()
            break

    # `#`-prefixed lines are the test harness's own directive/comment
    # convention (matching tests/run_conformance.py's `//!`), not part
    # of the regionlab language itself, which only has `--` comments
    # (regionlab/README.md). Strip them before parsing.
    text = "\n".join(l for l in raw.splitlines()
                      if not l.strip().startswith("#"))

    try:
        prog = parse(text)
        check(prog)
        got = "ok"
        got_detail = ""
    except ParseError as e:
        got, got_detail = "parse-error", str(e)
    except CheckError as e:
        got, got_detail = e.code, e.msg

    if want == "ok":
        return got == "ok", f"expected ok, got {got}: {got_detail}"
    return got == want, f"expected {want}, got {got}: {got_detail}"


def main() -> int:
    files = sorted(f for f in os.listdir(DIR) if f.endswith(".rlab"))
    passed, failed = 0, 0
    for f in files:
        ok, msg = run_one(os.path.join(DIR, f))
        print(f"  {'ok  ' if ok else 'FAIL'} {f}" + ("" if ok else f" — {msg}"))
        passed += ok
        failed += not ok
    print(f"\n{passed} passed, {failed} failed, {len(files)} total")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
