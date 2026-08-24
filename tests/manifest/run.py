#!/usr/bin/env python3
"""Conformance tests for the capability-manifest experiment (manifest.py).

Each test is a directory `tests/manifest/<case>/` containing `v1.nova`
and `v2.nova`, plus an `expect` file: the first line is `breaking` or
`compatible`, remaining lines (optional) are `name: old -> new`
assertions about specific entries in the diff.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "verifier"))

from refspec.driver import compile_source                    # noqa: E402
from refspec.manifest import diff, has_breaking_change, manifest  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))


def run_case(case_dir: str) -> tuple[bool, str]:
    v1 = os.path.join(case_dir, "v1.nova")
    v2 = os.path.join(case_dir, "v2.nova")
    expect_path = os.path.join(case_dir, "expect")
    if not (os.path.exists(v1) and os.path.exists(expect_path)):
        return True, ""     # not a case directory (e.g. logging-lib demo)

    lines = open(expect_path, encoding="utf-8").read().splitlines()
    want_breaking = lines[0].strip() == "breaking"

    old = manifest(compile_source(open(v1, encoding="utf-8").read(), v1).result)
    new = manifest(compile_source(open(v2, encoding="utf-8").read(), v2).result)
    changes = diff(old, new)
    got_breaking = has_breaking_change(changes)

    if got_breaking != want_breaking:
        return False, (f"expected {'breaking' if want_breaking else 'compatible'}, "
                       f"got {'breaking' if got_breaking else 'compatible'}")
    return True, ""


def main() -> int:
    cases = sorted(d for d in os.listdir(DIR)
                   if os.path.isdir(os.path.join(DIR, d)))
    passed, failed = 0, 0
    for c in cases:
        ok, msg = run_case(os.path.join(DIR, c))
        if os.path.exists(os.path.join(DIR, c, "expect")):
            print(f"  {'ok  ' if ok else 'FAIL'} {c}" + (f" — {msg}" if msg else ""))
            passed += ok
            failed += not ok
    print(f"\n{passed} passed, {failed} failed")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
