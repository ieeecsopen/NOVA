"""Experiment: instrumentation derived from effect rows (P21, thesis T1).

A function's effect row already says which capabilities it uses. This
module tests whether that is enough information to generate trace spans
automatically, with no hand-placed instrumentation, by intercepting every
`CapUse` the reference evaluator executes.

The question P21 asks is not "can we log capability calls" — that part is
trivial, and this module is a few dozen lines. The question is whether
doing so **avoids the drift bug**: hand-written instrumentation is a
second program that must be kept in sync with the first, and it silently
falls out of sync when someone adds a call site and forgets the matching
log line. A derived trace cannot fall out of sync with the capability
uses, because it is not a second program — it is a read of the first.

See `docs/experiments/002-rows-to-spans.md` for the result, including the
granularity limit this experiment found.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast as a
from .check import CheckResult
from .eval import UNIT_VALUE, CapValue, Closure, Interpreter, NovaRuntimeError
from .diagnostics import Diagnostic


@dataclass
class Span:
    depth: int
    capability: str
    op: str
    args: str

    def __str__(self) -> str:
        return "  " * self.depth + f"{self.capability}.{self.op}({self.args})"


class TracingInterpreter(Interpreter):
    """Same evaluator, plus a derived trace of every capability operation.

    No function in this class decides *what* to log — that would be
    hand-instrumentation again. It only decides *how* to render a call
    that `CapUse` already identifies, which is exactly the information
    RFC 0001's row makes visible in the type.
    """

    def __init__(self, result: CheckResult, out=None) -> None:
        super().__init__(result, out)
        self.spans: list[Span] = []
        self._depth = 0

    def eval(self, e, env: dict):
        # `Interpreter.eval(self, ...)` rather than zero-arg `super()`:
        # the latter does not resolve correctly from inside a list
        # comprehension's implicit scope.
        if isinstance(e, a.CapUse):
            recv = Interpreter.eval(self, e.recv, env)
            args = [Interpreter.eval(self, x, env) for x in e.args]
            if not isinstance(recv, CapValue):
                raise NovaRuntimeError(f"not a capability: {recv!r}")
            impl = recv.ops.get(e.op)
            if impl is None:
                raise Diagnostic(
                    "E0301",
                    f"`{recv.cap_name}.{e.op}` has no host implementation",
                    [])
            self.spans.append(Span(self._depth, recv.cap_name, e.op,
                                   ", ".join(_show(a_) for a_ in args)))
            self._depth += 1
            try:
                return impl(*args)
            finally:
                self._depth -= 1
        return Interpreter.eval(self, e, env)


def _show(v) -> str:
    if isinstance(v, str):
        return f'"{v}"'
    if v is UNIT_VALUE:
        return "()"
    return repr(v)


def render(spans: list[Span]) -> str:
    return "\n".join(str(s) for s in spans)
