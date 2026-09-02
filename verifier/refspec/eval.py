"""Reference evaluator for NOVA v0.2 (RFC 0001-0005).

The dynamic half of the executable specification. Effect rows and types
are *erased* at run time (RFC 0001 §9): they cost nothing here, exactly as
they should cost nothing in the compiler. Capabilities, structs, and enums
are all ordinary values — nothing about the runtime representation below
needs to know about generics or trait bounds, because both are erased by
the time a program typechecks (RFC 0003 §5).

This evaluator assumes the program has passed `check.py`. It is written
for obviousness, not speed.

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


class Interpreter:
    def __init__(self, result: CheckResult, out=None) -> None:
        self.r = result
        self.out = out if out is not None else []
        self._t0 = time.monotonic_ns()

    # ------------------------------------------------ host capabilities
    def make_runtime(self) -> CapValue:
        clock = CapValue("Clock", {
            "now": lambda: (time.monotonic_ns() - self._t0) // 1_000_000,
        })
        filesystem = CapValue("Filesystem", {
            "read": self._fs_read,
            "write": self._fs_write,
            "exists": self._fs_exists,
        })
        network = CapValue("Network", {
            "get": lambda url: self._net(url, None),
            "post": lambda url, body: self._net(url, body),
        })
        return CapValue("Runtime", {
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
        return self.eval(fn.body, env)

    def call_fn(self, name: str, args: list):
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
        if isinstance(e, a.IntLit):
            return e.value
        if isinstance(e, a.StrLit):
            return e.value
        if isinstance(e, a.BoolLit):
            return e.value
        if isinstance(e, a.UnitLit):
            return UNIT_VALUE

        if isinstance(e, a.Var):
            if e.name in env:
                return env[e.name][0]
            if e.name in self.r.fns:
                return ("fn", e.name)
            raise NovaRuntimeError(f"unbound variable {e.name}")

        if isinstance(e, a.Unary):
            v = self.eval(e.operand, env)
            return -v if e.op == "-" else (not v)

        if isinstance(e, a.Binary):
            if e.op == "&&":
                return self.eval(e.left, env) and self.eval(e.right, env)
            if e.op == "||":
                return self.eval(e.left, env) or self.eval(e.right, env)
            lv = self.eval(e.left, env)
            rv = self.eval(e.right, env)
            if e.op == "/" and rv == 0:
                raise Diagnostic("E0300", "division by zero",
                                 [Label(e.span, "evaluated here")])
            ops = {
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
            return ops[e.op](lv, rv)

        if isinstance(e, a.If):
            return self.eval(e.then if self.eval(e.cond, env) else e.els, env)

        if isinstance(e, a.While):
            while self.eval(e.cond, env):
                self.eval(e.body, env)
            return UNIT_VALUE

        if isinstance(e, a.For):
            cur = self.eval(e.iter, env)
            while isinstance(cur, EnumValue) and cur.variant == "Cons":
                inner = dict(env)
                inner[e.var] = [cur.args[0]]
                self.eval(e.body, inner)
                cur = cur.args[1]
            return UNIT_VALUE

        if isinstance(e, a.Assign):
            env[e.name][0] = self.eval(e.value, env)
            return UNIT_VALUE

        if isinstance(e, a.Block):
            inner = dict(env)
            for st in e.stmts:
                if isinstance(st, a.Let):
                    inner[st.name] = [self.eval(st.value, inner)]
                else:
                    self.eval(st, inner)
            return UNIT_VALUE if e.tail is None else self.eval(e.tail, inner)

        if isinstance(e, a.Lambda):
            return Closure(e.params, e.body, dict(env))

        if isinstance(e, a.TupleLit):
            return tuple(self.eval(x, env) for x in e.elems)

        if isinstance(e, a.StructLit):
            return StructValue(e.name, {n: self.eval(v, env)
                                        for n, v in e.fields})

        if isinstance(e, a.EnumCtor):
            return EnumValue(e.enum_name, e.variant,
                             tuple(self.eval(x, env) for x in e.args))

        if isinstance(e, a.FieldAccess):
            recv = self.eval(e.recv, env)
            if isinstance(recv, StructValue):
                return recv.fields[e.field]
            if isinstance(recv, tuple):
                return recv[int(e.field)]
            raise NovaRuntimeError(f"no field `{e.field}` on {recv!r}")

        if isinstance(e, a.Match):
            v = self.eval(e.scrutinee, env)
            for arm in e.arms:
                inner = dict(env)
                if self._match_pattern(arm.pattern, v, inner):
                    return self.eval(arm.body, inner)
            raise NovaRuntimeError(f"no pattern matched {v!r}")

        if isinstance(e, a.Call):
            f = self.eval(e.callee, env)
            args = [self.eval(x, env) for x in e.args]
            return self.apply(f, args, e)

        if isinstance(e, a.MethodCall):
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

        raise AssertionError(f"unhandled expression: {type(e).__name__}")

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
        if isinstance(p, a.PWildcard):
            return True
        if isinstance(p, a.PBind):
            env[p.name] = [v]
            return True
        if isinstance(p, a.PInt):
            return v == p.value
        if isinstance(p, a.PBool):
            return v == p.value
        if isinstance(p, a.PString):
            return v == p.value
        if isinstance(p, a.PTuple):
            return all(self._match_pattern(sub, x, env)
                      for sub, x in zip(p.elems, v))
        if isinstance(p, a.PVariant):
            if not (isinstance(v, EnumValue) and v.variant == p.variant):
                return False
            return all(self._match_pattern(sub, x, env)
                      for sub, x in zip(p.args, v.args))
        raise AssertionError(f"unhandled pattern: {type(p).__name__}")
