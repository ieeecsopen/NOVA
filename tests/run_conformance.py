#!/usr/bin/env python3
"""NOVA conformance suite runner.

The conformance suite is the shared arbiter between implementations
(Constitution Article IX). Every implementation must run it and agree.

Each test is a `.nova` file with a header of `//!` directives:

    //! expect: ok                 the program must check
    //! expect: error E0201        the program must be rejected with this code
    //! sig: name = (Int) -> Int ! {Clock}
                                  assert a function's checked signature
    //! stdout: hello             expected output line (implies running)
    //! exit: 0                   expected value of `main` (implies running)

Usage:  python3 tests/run_conformance.py [--verbose] [filter]
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verifier"))

from refspec.diagnostics import Diagnostic          # noqa: E402
from refspec.driver import compile_source           # noqa: E402
from refspec.eval import Interpreter, NovaRuntimeError  # noqa: E402

CONFORMANCE_DIR = os.path.join(ROOT, "tests", "conformance")


@dataclass
class Expectation:
    expect: str = "ok"              # "ok" | "error"
    code: str | None = None
    sigs: dict[str, str] = field(default_factory=dict)
    stdout: list[str] = field(default_factory=list)
    exit: int | None = None
    should_run: bool = False


def parse_header(text: str) -> Expectation:
    exp = Expectation()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("//!"):
            if line and not line.startswith("//"):
                break
            continue
        body = line[3:].strip()
        key, _, value = body.partition(":")
        key, value = key.strip(), value.strip()
        if key == "expect":
            if value == "ok":
                exp.expect = "ok"
            elif value.startswith("error"):
                exp.expect = "error"
                parts = value.split()
                exp.code = parts[1] if len(parts) > 1 else None
            else:
                raise ValueError(f"bad expect directive: {value!r}")
        elif key == "sig":
            name, _, sig = value.partition("=")
            exp.sigs[name.strip()] = sig.strip()
        elif key == "stdout":
            exp.stdout.append(value)
            exp.should_run = True
        elif key == "exit":
            exp.exit = int(value)
            exp.should_run = True
        else:
            raise ValueError(f"unknown directive {key!r}")
    return exp


def run_one(path: str) -> tuple[bool, str]:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    exp = parse_header(text)
    name = os.path.basename(path)

    try:
        unit = compile_source(text, name)
    except Diagnostic as d:
        if exp.expect != "error":
            return False, f"expected ok, got error[{d.code}]: {d.title}\n" \
                          + _indent(d.sources.render(d))
        if exp.code and d.code != exp.code:
            return False, f"expected error[{exp.code}], " \
                          f"got error[{d.code}]: {d.title}\n" \
                          + _indent(d.sources.render(d))
        return True, ""

    if exp.expect == "error":
        return False, f"expected error[{exp.code}], but the program checked"

    for fn_name, want in exp.sigs.items():
        info = unit.result.fns.get(fn_name)
        if info is None:
            return False, f"no such function `{fn_name}`"
        got = str(info.ty)
        if got != want:
            return False, f"signature of `{fn_name}`:\n" \
                          f"    expected {want}\n    got      {got}"

    if not exp.should_run:
        return True, ""

    interp = Interpreter(unit.result)
    try:
        value = interp.run_main()
    except (Diagnostic, NovaRuntimeError) as e:
        return False, f"runtime failure: {e}"
    if interp.out != exp.stdout:
        return False, f"stdout:\n    expected {exp.stdout}\n" \
                      f"    got      {interp.out}"
    if exp.exit is not None and value != exp.exit:
        return False, f"exit: expected {exp.exit}, got {value!r}"
    return True, ""


def _indent(s: str) -> str:
    return "\n".join("    " + line for line in s.splitlines())


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    args = [x for x in argv[1:] if not x.startswith("-")]
    filt = args[0] if args else ""

    files = sorted(f for f in os.listdir(CONFORMANCE_DIR)
                   if f.endswith(".nova") and filt in f)
    if not files:
        print("no tests found", file=sys.stderr)
        return 2

    passed, failed = 0, []
    for f in files:
        ok, msg = run_one(os.path.join(CONFORMANCE_DIR, f))
        if ok:
            passed += 1
            if verbose:
                print(f"  ok   {f}")
        else:
            failed.append((f, msg))
            print(f"  FAIL {f}")
            print(_indent(msg))

    print()
    print(f"{passed} passed, {len(failed)} failed, {len(files)} total")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
