#!/usr/bin/env python3
"""Demonstrates and checks the drift property claimed in
docs/experiments/002-rows-to-spans.md: a derived trace picks up a new
capability call site with zero changes to the tracer itself.

Not a generic conformance harness (there is only one case worth encoding
this way) -- it directly asserts the property the experiment is about.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "verifier"))

from refspec.driver import compile_source          # noqa: E402
from refspec.tracing import TracingInterpreter, render  # noqa: E402

DIR = os.path.join(ROOT, "tests", "tracing", "drift-demo")


def trace(path: str) -> list[str]:
    unit = compile_source(open(path, encoding="utf-8").read(), path)
    t = TracingInterpreter(unit.result)
    t.run_main()
    return [f"{s.capability}.{s.op}" for s in t.spans]


def main() -> int:
    v1 = trace(os.path.join(DIR, "v1.nova"))
    v2 = trace(os.path.join(DIR, "v2.nova"))

    print("v1 trace:", v1)
    print("v2 trace:", v2)

    ok = True
    if v1 != ["Runtime.print"]:
        print("FAIL: v1 trace is not what was expected")
        ok = False
    if "Clock.now" not in v2:
        print("FAIL: v2's new capability use did not appear in the trace "
             "-- the derived-tracer approach did NOT survive the change, "
             "which would falsify the claim in experiment 002")
        ok = False
    elif v2.count("Clock.now") != 2:
        print(f"FAIL: expected 2 Clock.now spans in v2, got "
             f"{v2.count('Clock.now')}")
        ok = False
    else:
        print("ok: v2's new capability use (Clock.now, x2) appears in the "
             "trace with ZERO changes to tracing.py")

    print()
    print("1 passed" if ok else "0 passed", "0 failed" if ok else "1 failed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
