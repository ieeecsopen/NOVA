"""Reference evaluator for NOVA v0.2 (RFC 0001-0005).

The dynamic half of the executable specification. Effect rows and types
are *erased* at run time (RFC 0001 §9): they cost nothing here, exactly as
they should cost nothing in the compiler. Capabilities, structs, and enums
are all ordinary values — nothing about the runtime representation below
needs to know about generics or trait bounds, because both are erased by
the time a program typechecks (RFC 0003 §5).

This evaluator assumes the program has passed `check.py`. It is written
for obviousness, not speed — with one exception: `eval`/`_match_pattern`
dispatch by exact AST node type through a `dict[type, method]` table
built once per class, rather than a chain of `isinstance` checks tried in
declaration order. Every concrete `Expr`/`Pattern` subclass is a direct,
non-nested subclass (see ast.py), so exact-type dispatch is equivalent to
the old isinstance chain, just without re-testing every earlier case on
every call. On a workload dominated by function calls and arithmetic,
`Call`/`Binary`/`Var` used to be checked last or mid-chain on every single
node; profiling (`cProfile`, ~8M `eval` calls on a loop+recursion+list
stress program) showed `isinstance` itself costing ~19% of total time.

**Local bindings are cells, not values** (`env[name]` is a one-element
list `[value]`, not the value itself). This is what makes `let mut` +
`Assign` (RFC 0005) work correctly across nested blocks and loop
iterations without a second environment mechanism: a shallow `dict(env)`
copy (already used for lexical scoping) still shares the *same* cell
objects, so a write through any copy is visible through all of them.
This would be unsound for a general reference/aliasing feature — two
live handles to the same cell is exactly what Constitution Article XI
forbids — but `check.py`'s `_check_no_mut_capture` guarantees no closure
ever captures a `mut` local, so the only things that ever share a cell
are nested scopes *within a single call*, never two independently
escaping values. See RFC 0005 §4 for the full argument.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

from . import ast as a
from .check import CheckResult
from .diagnostics import Diagnostic, Label


class Unit:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self) -> str:
        return "()"


UNIT_VALUE = Unit()


@dataclass
class Closure:
    params: list[a.Param]
    body: a.Expr
    env: dict

    def __repr__(self) -> str:
        return f"<closure/{len(self.params)}>"


@dataclass
class CapValue:
    """A capability value. Unforgeable: only the host creates these."""
    cap_name: str
    ops: dict            # op name -> python callable(*args)

    def __repr__(self) -> str:
        return f"<capability {self.cap_name}>"


@dataclass
class StructValue:
    name: str
    fields: dict

    def __repr__(self) -> str:
        inner = ", ".join(f"{k}: {v!r}" for k, v in self.fields.items())
        return f"{self.name} {{ {inner} }}"


@dataclass
class EnumValue:
    enum_name: str
    variant: str
    args: tuple

    def __repr__(self) -> str:
        if not self.args:
            return f"{self.enum_name}::{self.variant}"
        inner = ", ".join(repr(a) for a in self.args)
        return f"{self.enum_name}::{self.variant}({inner})"


class NovaRuntimeError(Exception):
    pass


class AgentAuthorityError(NovaRuntimeError):
    """An autonomous invocation attempted authority it was not delegated."""


class AgentSandbox:
    """The authority boundary for an autonomous invocation.

    An agent starts with an empty authority set.  The embedding host may
    delegate *specific capability values* created by this interpreter; a
    capability is never looked up from the ambient Runtime or from the host
    process.  NOVA code run through :meth:`run` can therefore reach a host
    primitive only when that exact capability appears in its argument list.

    This deliberately is a capability boundary, not a Python security
    boundary: untrusted Python must run out of process.  The reference
    interpreter's supported guest language has no Python import, subprocess,
    filesystem, or network primitive of its own.
    """

    def __init__(self, interpreter: "Interpreter", delegated=()) -> None:
        self._interpreter = interpreter
        self._delegated = frozenset(id(cap) for cap in delegated)
        for cap in delegated:
            interpreter._require_delegable_capability(cap)

    def delegate(self, *capabilities: CapValue) -> "AgentSandbox":
        """Return a child sandbox with an explicitly attenuated grant."""
        for cap in capabilities:
            self._interpreter._require_delegable_capability(cap)
            if id(cap) not in self._delegated:
                raise AgentAuthorityError(
                    "cannot delegate a capability that is not in the "
                    "current agent's lexical authority")
        return AgentSandbox(self._interpreter, capabilities)

    def run(self, name: str, *args):
        """Run a named NOVA function with only explicitly passed authority."""
        for arg in args:
            if isinstance(arg, CapValue) and id(arg) not in self._delegated:
                raise AgentAuthorityError(
                    f"agent invocation of `{name}` was not delegated "
                    f"the `{arg.cap_name}` capability")
        return self._interpreter.call_fn(name, list(args))


def _runtime_head(v) -> str | None:
    """The nominal type name of a runtime value, for trait-method
    dispatch. `bool` is checked before `int` because `bool` is a Python
    subclass of `int`."""
    if isinstance(v, StructValue):
        return v.name
    if isinstance(v, EnumValue):
        return v.enum_name
    if isinstance(v, bool):
        return "Bool"
    if isinstance(v, int):
        return "Int"
    if isinstance(v, str):
        return "String"
    return None


_BINARY_OPS = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: int(x / y) if (x < 0) != (y < 0) else x // y,
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
}

# The interpreter recurses once per AST node and again per NOVA function
# call (eval -> apply -> call_fn -> eval -> ...), so NOVA call depth costs
# several Python stack frames each. The default CPython limit (1000)
# caps NOVA recursion at only a few hundred frames — raised here so a
# moderately recursive NOVA program (RFC 0001 has no tail-call guarantee)
# doesn't hit a Python RecursionError before it hits any NOVA-level limit.
# This is a mitigation, not a fix: deep enough recursion still exhausts
# the *C* stack (a segfault, not a catchable exception) well before this
# number is reached. A real fix needs an explicit evaluation stack
# (trampolining `eval`), which is a larger change tracked in
# docs/known-issues.md.
_MIN_RECURSION_LIMIT = 10_000
if sys.getrecursionlimit() < _MIN_RECURSION_LIMIT:
    sys.setrecursionlimit(_MIN_RECURSION_LIMIT)


class Interpreter:
    def __init__(self, result: CheckResult, out=None) -> None:
        self.r = result
        self.out = out if out is not None else []
        self._t0 = time.monotonic_ns()
        self.list_allocation_count = 0
        self.list_allocation_bytes = 0
        # Identity, rather than a capability name, makes grants
        # unforgeable at the host boundary as well as in the NOVA checker.
        self._issued_capabilities: set[int] = set()

    # ------------------------------------------------ host capabilities
    def _issue_capability(self, cap_name: str, ops: dict) -> CapValue:
        cap = CapValue(cap_name, ops)
        self._issued_capabilities.add(id(cap))
        return cap

    def _require_delegable_capability(self, cap) -> None:
        if not isinstance(cap, CapValue) or id(cap) not in self._issued_capabilities:
            raise AgentAuthorityError(
                "agent authority must be an explicit capability token "
                "issued by this interpreter")

    def agent_sandbox(self, *delegated: CapValue) -> AgentSandbox:
        """Create an autonomous invocation with zero authority by default.

        Passing no arguments is the secure default.  A host that wants an
        agent to use a tool must first obtain its capability lexically and
        pass that exact token here, then pass it to the agent function.
        """
        return AgentSandbox(self, delegated)

    def make_runtime(self) -> CapValue:
        clock = self._issue_capability("Clock", {
            "now": lambda: (time.monotonic_ns() - self._t0) // 1_000_000,
        })
        filesystem = self._issue_capability("Filesystem", {
            "read": self._fs_read,
            "write": self._fs_write,
            "exists": self._fs_exists,
        })
        network = self._issue_capability("Network", {
            "get": lambda url: self._net(url, None),
            "post": lambda url, body: self._net(url, body),
        })
        return self._issue_capability("Runtime", {
            "clock": lambda: clock,
            "filesystem": lambda: filesystem,
            "network": lambda: network,
            "print": self._print,
        })

    def _print(self, line):
        self.out.append(line)
        return UNIT_VALUE

    # The reference interpreter grounds `Filesystem` in the real disk,
    # relative to the working directory, so file-touching programs can
    # actually be run and their behaviour observed. This is the reference
    # semantics, not a production sandbox — a real deployment substitutes
    # a policy-enforcing host (see docs/runtime/RESOURCE-MODEL.md).
    def _fs_read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError as ex:
            raise NovaRuntimeError(f"Filesystem.read({path!r}): {ex}")

    def _fs_write(self, path, contents):
        try:
            data = contents.encode("utf-8")
            with open(path, "wb") as fh:
                fh.write(data)
            return len(data)
        except OSError as ex:
            raise NovaRuntimeError(f"Filesystem.write({path!r}): {ex}")

    def _fs_exists(self, path):
        return os.path.exists(path)

    # `Network` is inert by default: the reference interpreter does not
    # make outbound requests. Setting NOVA_ALLOW_NETWORK=1 opts in and
    # uses the standard library. Kept deliberately conservative so that
    # running an untrusted example can never reach the network silently.
    def _net(self, url, body):
        if os.environ.get("NOVA_ALLOW_NETWORK") != "1":
            raise NovaRuntimeError(
                f"Network access to {url!r} is disabled in the reference "
                "interpreter. Set NOVA_ALLOW_NETWORK=1 to enable it.")
        import urllib.request
        try:
            data = body.encode("utf-8") if body is not None else None
            with urllib.request.urlopen(url, data=data, timeout=10) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as ex:  # noqa: BLE001 - surface any transport error
            raise NovaRuntimeError(f"Network request to {url!r} failed: {ex}")

    # ------------------------------------------------------------ run
    def run_main(self):
        if "main" not in self.r.fns:
            raise NovaRuntimeError("no `main` function")
        fn = self.r.fns["main"].decl
        env = {fn.params[0].name: [self.make_runtime()]}
        # A `RecursionError` is caught only here, at the single outermost
        # frame, never inside `eval` itself: catching it at every nested
        # `eval` call would mean thousands of unwinding frames each running
        # exception-handling code, which itself needs stack space that
        # isn't there (see I6, docs/known-issues.md) — this is a NOVA
        # program hitting a real depth ceiling, not a Python bug, so it
        # gets a clean diagnostic instead of a raw interpreter traceback.
        try:
            res = self.eval(fn.body, env)
            if os.environ.get("NOVA_BENCH_LIST_ALLOC") == "1":
                print(
                    f"NOVA_LIST_ALLOC "
                    f"bytes={self.list_allocation_bytes} "
                    f"count={self.list_allocation_count}",
                    file=sys.stderr,
                )
            return res
        except RecursionError:
            raise NovaRuntimeError(
                "recursion depth exceeded — this program recurses too "
                "deeply for the reference interpreter to evaluate "
                "(see docs/known-issues.md I6; NOVA has no tail-call "
                "guarantee, and Python's own call stack backs this "
                "interpreter's recursion)") from None

    def call_fn(self, name: str, args: list):
        if name == "trim":
            return args[0].strip()
        if name == "starts_with":
            return args[0].startswith(args[1])
        if name == "ends_with":
            return args[0].endswith(args[1])
        if name == "split":
            s = args[0]
            delim = args[1]
            parts = s.split(delim) if delim != "" else list(s)
            res = EnumValue("List", "Nil", ())
            for p in reversed(parts):
                res = EnumValue("List", "Cons", (p, res))
            return res
        fn = self.r.fns[name].decl
        env = {p.name: [v] for p, v in zip(fn.params, args)}
        return self.eval(fn.body, env)

    def call_method(self, fn_decl: a.FnDecl, self_val, args: list):
        env = {"self": [self_val]}
        for p, v in zip(fn_decl.params[1:], args):
            env[p.name] = [v]
        return self.eval(fn_decl.body, env)

    # ----------------------------------------------------------- eval
    def eval(self, e, env: dict):
        handler = self._EVAL_DISPATCH.get(type(e))
        if handler is None:
            raise AssertionError(f"unhandled expression: {type(e).__name__}")
        return handler(self, e, env)

    def _eval_IntLit(self, e: a.IntLit, env: dict):
        return e.value

    def _eval_StrLit(self, e: a.StrLit, env: dict):
        return e.value

    def _eval_BoolLit(self, e: a.BoolLit, env: dict):
        return e.value

    def _eval_UnitLit(self, e: a.UnitLit, env: dict):
        return UNIT_VALUE

    def _eval_Var(self, e: a.Var, env: dict):
        if e.name in env:
            return env[e.name][0]
        if e.name in self.r.fns:
            return ("fn", e.name)
        raise NovaRuntimeError(f"unbound variable {e.name}")

    def _eval_Unary(self, e: a.Unary, env: dict):
        v = self.eval(e.operand, env)
        return -v if e.op == "-" else (not v)

    def _eval_Binary(self, e: a.Binary, env: dict):
        if e.op == "&&":
            return self.eval(e.left, env) and self.eval(e.right, env)
        if e.op == "||":
            return self.eval(e.left, env) or self.eval(e.right, env)
        lv = self.eval(e.left, env)
        rv = self.eval(e.right, env)
        if e.op == "/" and rv == 0:
            raise Diagnostic("E0300", "division by zero",
                             [Label(e.span, "evaluated here")])
        return _BINARY_OPS[e.op](lv, rv)

    def _eval_If(self, e: a.If, env: dict):
        return self.eval(e.then if self.eval(e.cond, env) else e.els, env)

    def _eval_While(self, e: a.While, env: dict):
        while self.eval(e.cond, env):
            self.eval(e.body, env)
        return UNIT_VALUE

    def _eval_For(self, e: a.For, env: dict):
        cur = self.eval(e.iter, env)
        while isinstance(cur, EnumValue) and cur.variant == "Cons":
            inner = dict(env)
            inner[e.var] = [cur.args[0]]
            self.eval(e.body, inner)
            cur = cur.args[1]
        return UNIT_VALUE

    def _eval_Assign(self, e: a.Assign, env: dict):
        env[e.name][0] = self.eval(e.value, env)
        return UNIT_VALUE

    def _eval_Block(self, e: a.Block, env: dict):
        inner = dict(env)
        for st in e.stmts:
            if isinstance(st, a.Let):
                inner[st.name] = [self.eval(st.value, inner)]
            else:
                self.eval(st, inner)
        return UNIT_VALUE if e.tail is None else self.eval(e.tail, inner)

    def _eval_Lambda(self, e: a.Lambda, env: dict):
        return Closure(e.params, e.body, dict(env))

    def _eval_TupleLit(self, e: a.TupleLit, env: dict):
        return tuple(self.eval(x, env) for x in e.elems)

    def _eval_StructLit(self, e: a.StructLit, env: dict):
        return StructValue(e.name, {n: self.eval(v, env)
                                    for n, v in e.fields})

    def _eval_EnumCtor(self, e: a.EnumCtor, env: dict):
        value = EnumValue(e.enum_name, e.variant,
                          tuple(self.eval(x, env) for x in e.args))
        if e.enum_name == "List":
            self.list_allocation_count += 1
            self.list_allocation_bytes += (
                sys.getsizeof(value) + sys.getsizeof(value.args)
            )
        return value

    def _eval_FieldAccess(self, e: a.FieldAccess, env: dict):
        recv = self.eval(e.recv, env)
        if isinstance(recv, StructValue):
            return recv.fields[e.field]
        if isinstance(recv, tuple):
            return recv[int(e.field)]
        raise NovaRuntimeError(f"no field `{e.field}` on {recv!r}")

    def _eval_Match(self, e: a.Match, env: dict):
        v = self.eval(e.scrutinee, env)
        for arm in e.arms:
            inner = dict(env)
            if self._match_pattern(arm.pattern, v, inner):
                return self.eval(arm.body, inner)
        raise NovaRuntimeError(f"no pattern matched {v!r}")

    def _eval_Call(self, e: a.Call, env: dict):
        f = self.eval(e.callee, env)
        args = [self.eval(x, env) for x in e.args]
        return self.apply(f, args, e)

    def _eval_MethodCall(self, e: a.MethodCall, env: dict):
        recv = self.eval(e.recv, env)
        args = [self.eval(x, env) for x in e.args]
        if isinstance(recv, CapValue):
            impl = recv.ops.get(e.op)
            if impl is None:
                raise Diagnostic(
                    "E0301",
                    f"`{recv.cap_name}.{e.op}` has no host implementation",
                    [Label(e.op_span, "cannot be executed")],
                    notes=["the reference interpreter implements only "
                           "the prelude capabilities; this program can "
                           "be checked but not run"])
            return impl(*args)
        head = _runtime_head(recv)
        found = [info for (_, h), info in self.r.impls.items()
                if h == head and e.op in info.methods]
        if not found:
            raise NovaRuntimeError(
                f"no method `{e.op}` for a value of head type {head!r} "
                f"— this should have been rejected by the checker")
        return self.call_method(found[0].methods[e.op], recv, args)

    # Built once per class from the `_eval_<TypeName>` methods above,
    # keyed by the exact AST node class (every concrete Expr subclass is
    # a direct, non-nested subclass of Expr — see ast.py — so there is no
    # subclassing ambiguity an exact-type dict could get wrong that the
    # old isinstance chain wouldn't). Unbound functions, not bound
    # methods: `self` is passed explicitly in `eval`, so this dict is
    # shared across all Interpreter instances rather than rebuilt per
    # instance.
    _EVAL_DISPATCH = {
        a.IntLit: _eval_IntLit,
        a.StrLit: _eval_StrLit,
        a.BoolLit: _eval_BoolLit,
        a.UnitLit: _eval_UnitLit,
        a.Var: _eval_Var,
        a.Unary: _eval_Unary,
        a.Binary: _eval_Binary,
        a.If: _eval_If,
        a.While: _eval_While,
        a.For: _eval_For,
        a.Assign: _eval_Assign,
        a.Block: _eval_Block,
        a.Lambda: _eval_Lambda,
        a.TupleLit: _eval_TupleLit,
        a.StructLit: _eval_StructLit,
        a.EnumCtor: _eval_EnumCtor,
        a.FieldAccess: _eval_FieldAccess,
        a.Match: _eval_Match,
        a.Call: _eval_Call,
        a.MethodCall: _eval_MethodCall,
    }

    def apply(self, f, args, site):
        if isinstance(f, tuple) and f[0] == "fn":
            return self.call_fn(f[1], args)
        if isinstance(f, Closure):
            inner = dict(f.env)
            for p, v in zip(f.params, args):
                inner[p.name] = [v]
            return self.eval(f.body, inner)
        raise NovaRuntimeError(f"not callable: {f!r}")

    # ----------------------------------------------------------- match
    def _match_pattern(self, p: a.Pattern, v, env: dict) -> bool:
        """Try to match `v` against `p`, extending `env` with bindings
        (as fresh cells) on success. `check.py`'s exhaustiveness check
        already guarantees some arm matches, so a `Match` with no
        matching arm at runtime indicates a checker bug, not a NOVA
        program error — hence `NovaRuntimeError`, not a `Diagnostic`,
        at the `Match` call site above."""
        handler = self._PATTERN_DISPATCH.get(type(p))
        if handler is None:
            raise AssertionError(f"unhandled pattern: {type(p).__name__}")
        return handler(self, p, v, env)

    def _match_PWildcard(self, p: a.PWildcard, v, env: dict) -> bool:
        return True

    def _match_PBind(self, p: a.PBind, v, env: dict) -> bool:
        env[p.name] = [v]
        return True

    def _match_PInt(self, p: a.PInt, v, env: dict) -> bool:
        return v == p.value

    def _match_PBool(self, p: a.PBool, v, env: dict) -> bool:
        return v == p.value

    def _match_PString(self, p: a.PString, v, env: dict) -> bool:
        return v == p.value

    def _match_PTuple(self, p: a.PTuple, v, env: dict) -> bool:
        return all(self._match_pattern(sub, x, env)
                  for sub, x in zip(p.elems, v))

    def _match_PVariant(self, p: a.PVariant, v, env: dict) -> bool:
        if not (isinstance(v, EnumValue) and v.variant == p.variant):
            return False
        return all(self._match_pattern(sub, x, env)
                  for sub, x in zip(p.args, v.args))

    _PATTERN_DISPATCH = {
        a.PWildcard: _match_PWildcard,
        a.PBind: _match_PBind,
        a.PInt: _match_PInt,
        a.PBool: _match_PBool,
        a.PString: _match_PString,
        a.PTuple: _match_PTuple,
        a.PVariant: _match_PVariant,
    }
