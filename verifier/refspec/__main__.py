"""CLI: `python3 -m verifier.refspec <command> <file.nova>`"""
from __future__ import annotations

import sys

from .check import CheckResult
from .diagnostics import Diagnostic
from .driver import compile_source
from .eval import Interpreter, NovaRuntimeError
from .grading import analyze as grade_analyze
from .grading import fmt_row as grade_fmt

USAGE = """\
usage: python3 -m verifier.refspec <command> <file.nova>

commands:
  check   type- and effect-check the program
  run     check, then evaluate `main`
  audit   list every function's effect row and every `= widen` site
  grade   experimental: bound how many times each capability is used
          (RFC 0001 \u00a711.7; see docs/experiments/003-graded-rows.md)
"""


def _audit(result: CheckResult) -> None:
    print("effect rows")
    print("-----------")
    for name, info in result.fns.items():
        widen = " (widened)" if info.decl.widen else ""
        print(f"  {name}{_row_params(info)}: {info.ty}{widen}")
    print()
    print("syntactically reachable capabilities")
    print("------------------------------------")
    for name, caps in result.reach.fn_caps.items():
        print(f"  {name}: {{{', '.join(sorted(caps))}}}")
    print()
    if result.widened:
        print("WIDENED SIGNATURES (over-approximated rows)")
        print("-------------------------------------------")
        for name, _ in result.widened:
            print(f"  {name}")
    else:
        print("no widened signatures")


def _row_params(info) -> str:
    return f"[{', '.join(info.row_params)}]" if info.row_params else ""


def _grade(result: CheckResult) -> None:
    print("EXPERIMENTAL — see docs/experiments/003-graded-rows.md")
    print("occurrence bounds (may-analysis; '?' = no sound bound)")
    print("-----------------------------------------------------")
    g = grade_analyze(result)
    for name, row in g.rows.items():
        why = g.reasons.get(name)
        suffix = f"   [{why}]" if why else ""
        print(f"  {name}: {grade_fmt(row)}{suffix}")


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("check", "run", "audit", "grade"):
        sys.stderr.write(USAGE)
        return 2
    command, path = argv[1], argv[2]
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    try:
        unit = compile_source(text, path)
    except Diagnostic as d:
        print(d.sources.render(d), file=sys.stderr)
        return 1

    if command == "check":
        print(f"{path}: ok")
        n = len(unit.result.widened)
        if n:
            print(f"note: {n} widened signature{'s' if n != 1 else ''} "
                  f"(see `audit`)")
        return 0

    if command == "audit":
        _audit(unit.result)
        return 0

    if command == "grade":
        _grade(unit.result)
        return 0

    interp = Interpreter(unit.result)
    try:
        value = interp.run_main()
    except Diagnostic as d:
        for line in interp.out:
            print(line)
        print(unit.sources.render(d), file=sys.stderr)
        return 1
    except NovaRuntimeError as e:
        print(f"runtime error: {e}", file=sys.stderr)
        return 1
    for line in interp.out:
        print(line)
    return int(value) if isinstance(value, int) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
