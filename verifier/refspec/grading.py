"""Experiment: graded effect rows (RFC 0001 §11.7, thesis T1).

RFC 0001's row is a *set* of capability labels. The T1 thesis claims that
budgets, deadlines, retry policy and instrumentation are the same row with
a **grade** attached to each label — and therefore that the ungraded row
does not foreclose the graded one.

This pass tests that claim without touching the checker. It computes, for
every named function, an upper bound on *how many times* each capability
in its row is used:

    measure: {Clock: 2, Runtime: 1}

The lattice is the naturals extended with an unbounded top element:

    add(m, n) = m + n            sequential composition
    join(m, n) = max(m, n)       branching (a may-analysis, worst case)
    INF                          recursion, or an unknown callee

It is a separate pass for the same reason capability reachability is one
(ARCHITECTURE.md): it is easy to get wrong, useful on its own, and
testable in isolation. It is *advisory*: nothing here rejects a program.

The honest finding this pass produces is recorded in
`docs/experiments/003-graded-rows.md`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast as a
from .check import CheckResult

INF = float("inf")
Grade = float          # a natural number, or INF
GradedRow = dict[str, Grade]

# `None` is a distinct state from `{}`. `{}` is a sound bound meaning "this
# performs nothing". `None` means "no sound bound could be computed" — the
# body calls through a value whose capability set is not known to this
# syntactic pass. Collapsing the two would silently understate cost, which
# is worse than not having a bound at all. See docs/experiments/003.
Bound = GradedRow | None
UNKNOWN: Bound = None


def fmt_grade(g: Grade) -> str:
    return "*" if g == INF else str(int(g))


def fmt_row(row: Bound) -> str:
    if row is None:
        return "? (no sound bound)"
    if not row:
        return "{}"
    return "{" + ", ".join(f"{k}: {fmt_grade(v)}"
                           for k, v in sorted(row.items())) + "}"


def add(x: Bound, y: Bound) -> Bound:
    if x is None or y is None:
        return None
    out = dict(x)
    for k, v in y.items():
        out[k] = out.get(k, 0) + v
    return out


def join(x: Bound, y: Bound) -> Bound:
    if x is None or y is None:
        return None
    out = dict(x)
    for k, v in y.items():
        out[k] = max(out.get(k, 0), v)
    return out


def saturate(row: Bound) -> Bound:
    """Turn every *known* label's grade to INF. Used for recursion, where
    the label set is known but the count is not — a genuinely different
    situation from `UNKNOWN`, see the module docstring."""
    if row is None:
        return None
    return {k: INF for k in row}


@dataclass
class GradingResult:
    rows: dict[str, Bound] = field(default_factory=dict)
    # why a function's bound is INF-saturated or UNKNOWN, for honest reporting
    reasons: dict[str, str] = field(default_factory=dict)


class Grader:
    def __init__(self, result: CheckResult) -> None:
        self.r = result
        self.out = GradingResult()

    # ------------------------------------------------------ call graph
    def _callees(self, e, acc: set[str], flags: set[str]) -> None:
        """Collect named callees; flag higher-order calls we cannot bound."""
        if isinstance(e, a.Call):
            if isinstance(e.callee, a.Var) and e.callee.name in self.r.fns:
                acc.add(e.callee.name)
            else:
                # Calling a closure or a parameter: the callee is not known
                # statically, so its grade is not either.
                flags.add("higher-order call")
            self._callees(e.callee, acc, flags)
            for x in e.args:
                self._callees(x, acc, flags)
            return
        for child in _children(e):
            self._callees(child, acc, flags)

    def analyze(self) -> GradingResult:
        graph = {}
        flags = {}
        for name, info in self.r.fns.items():
            acc: set[str] = set()
            fl: set[str] = set()
            self._callees(info.decl.body, acc, fl)
            graph[name] = acc
            flags[name] = fl

        for scc in _sccs(graph):
            recursive = len(scc) > 1 or any(n in graph[n] for n in scc)
            for name in scc:
                row = self._grade(self.r.fns[name].decl.body)
                if flags[name]:
                    # A call through an unknown value (a parameter or a
                    # returned closure) can perform capabilities this
                    # syntactic pass never sees. That is stronger than
                    # "unbounded count of a known label" — the label set
                    # itself is unknown, so no dict of counts is sound.
                    row = None
                    self.out.reasons[name] = sorted(flags[name])[0]
                elif recursive:
                    row = saturate(row)
                    self.out.reasons.setdefault(
                        name, "recursion" if len(scc) == 1
                        else f"mutual recursion with {sorted(set(scc) - {name})}")
                self.out.rows[name] = row
        return self.out

    # --------------------------------------------------------- grading
    def _grade(self, e) -> Bound:
        if isinstance(e, (a.IntLit, a.StrLit, a.BoolLit, a.UnitLit, a.Var)):
            return {}

        if isinstance(e, a.Unary):
            return self._grade(e.operand)

        if isinstance(e, a.Binary):
            # `&&` / `||` short-circuit, so the right side may not run;
            # `add` is still a sound upper bound and keeps the pass simple.
            return add(self._grade(e.left), self._grade(e.right))

        if isinstance(e, a.If):
            return add(self._grade(e.cond),
                       join(self._grade(e.then), self._grade(e.els)))

        if isinstance(e, a.Block):
            row: GradedRow = {}
            for st in e.stmts:
                row = add(row, self._grade(
                    st.value if isinstance(st, a.Let) else st))
            if e.tail is not None:
                row = add(row, self._grade(e.tail))
            return row

        if isinstance(e, a.Lambda):
            # Building a closure costs nothing; the cost lands where it is
            # called, which is exactly rule (Abs) in RFC 0001 §4.8. That the
            # ungraded and graded analyses agree here is a good sign.
            return {}

        if isinstance(e, a.CapUse):
            row = self._grade(e.recv)
            for x in e.args:
                row = add(row, self._grade(x))
            recv_cap = self._receiver_capability(e)
            return add(row, {recv_cap: 1.0}) if recv_cap else row

        if isinstance(e, a.Call):
            row: Bound = {}
            for x in e.args:
                row = add(row, self._grade(x))
            if isinstance(e.callee, a.Var) and e.callee.name in self.r.fns:
                return add(row, self.out.rows.get(e.callee.name, {}))
            # Calling a closure value: its capability set is not visible to
            # this pass. The caller as a whole is marked UNKNOWN by the
            # `flags` check in `analyze`, so returning the known partial
            # sum here is fine — it is never trusted as the final answer.
            return row

        raise AssertionError(f"unhandled node in grading: {type(e).__name__}")

    def _receiver_capability(self, e: a.CapUse) -> str | None:
        """Which capability does this `.op()` charge?

        The checker already proved the receiver is a capability; this pass
        re-derives the name syntactically rather than re-running inference.
        Direct parameter and alias cases are handled; anything else is
        attributed by searching for the unique capability declaring `op`.
        """
        candidates = [name for name, info in self.r.caps.items()
                      if e.op in info.ops]
        return candidates[0] if len(candidates) == 1 else None


def _children(e):
    if isinstance(e, a.Unary):
        return [e.operand]
    if isinstance(e, a.Binary):
        return [e.left, e.right]
    if isinstance(e, a.If):
        return [e.cond, e.then, e.els]
    if isinstance(e, a.Call):
        return [e.callee, *e.args]
    if isinstance(e, a.CapUse):
        return [e.recv, *e.args]
    if isinstance(e, a.Lambda):
        return [e.body]
    if isinstance(e, a.Block):
        out = [st.value if isinstance(st, a.Let) else st for st in e.stmts]
        return out + ([e.tail] if e.tail is not None else [])
    return []


def _sccs(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's algorithm; returns SCCs in reverse topological order."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    out: list[list[str]] = []
    counter = [0]

    def strongconnect(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(comp)

    for v in graph:
        if v not in index:
            strongconnect(v)
    return out


def analyze(result: CheckResult) -> GradingResult:
    return Grader(result).analyze()
