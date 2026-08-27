#!/usr/bin/env python3
"""Conformance tests for the graded-rows experiment (grading.py).

Separate from tests/run_conformance.py because grading is explicitly
experimental (docs/experiments/003-graded-rows.md) and is not part of
the checked language RFC 0001 specifies. A failure here is a bug in the
experiment, not a language conformance failure.

Each test is a `.nova` file with:

    //! grade: name = {Label: N, ...}     exact expected bound
    //! grade: name = ?                   expected: no sound bound
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "verifier"))

from refspec.driver import compile_source          # noqa: E402
from refspec.grading import analyze, fmt_row        # noqa: E402

DIR = os.path.join(ROOT, "tests", "grading")
DIRECTIVE = re.compile(r"^//!\s*grade:\s*(\w+)\s*=\s*(.+)$")


def run_one(path: str) -> tuple[bool, str]:
    text = open(path, encoding="utf-8").read()
    expected = {}
    for line in text.splitlines():
        m = DIRECTIVE.match(line.strip())
        if m:
            expected[m.group(1)] = m.group(2).strip()

    unit = compile_source(text, os.path.basename(path))
    g = analyze(unit.result)

    for name, want in expected.items():
        got = fmt_row(g.rows.get(name))
        got_norm = "?" if got.startswith("?") else got
        if got_norm != want:
            return False, f"`{name}`: expected {want}, got {got}"
    return True, ""


def main() -> int:
    files = sorted(f for f in os.listdir(DIR) if f.endswith(".nova"))
    passed, failed = 0, 0
    for f in files:
        ok, msg = run_one(os.path.join(DIR, f))
        print(f"  {'ok  ' if ok else 'FAIL'} {f}" + (f" — {msg}" if msg else ""))
        passed += ok
        failed += not ok
    print(f"\n{passed} passed, {failed} failed, {len(files)} total")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
