"""Checker for the regionlab prototype.

Validates OWNERSHIP-MODEL.md §3-§6 on a minimal calculus: regions,
allocation, shared/exclusive region capabilities, and the linearity rule
on exclusive access. See regionlab/README.md for the language and
SAFETY-GUARANTEES.md for what each diagnostic here is claimed to prove.

Region acquisition is RAII-scoped: a `let x = shared(r)` / `exclusive(r)`
inside block B holds that access for exactly B's lexical extent, and it
is released automatically when B finishes checking -- mirroring exactly
how RFC 0005's `mut` locals and NOVA's regions themselves are already
scope-bound in the shipped v0.2 language, rather than introducing a
second, different scoping idea just for this prototype.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast as a


class CheckError(Exception):
    def __init__(self, code: str, line: int, msg: str) -> None:
        self.code, self.line, self.msg = code, line, msg
        super().__init__(f"{code} (line {line}): {msg}")


# ------------------------------------------------------------------ types

class Ty:
    pass


@dataclass(frozen=True)
class TInt(Ty):
    def __str__(self): return "Int"


@dataclass(frozen=True)
class TInRegion(Ty):
    region: str
    def __str__(self): return f"InRegion({self.region}, Int)"


@dataclass(frozen=True)
class TShared(Ty):
    region: str
    def __str__(self): return f"Shared({self.region})"


@dataclass(frozen=True)
class TExcl(Ty):
    region: str
    def __str__(self): return f"Excl({self.region})"


def is_linear(t: Ty) -> bool:
    """Only the exclusive region capability is linear (OWNERSHIP-MODEL.md
    §4) -- every other type, including the shared capability, is
    ordinary and freely copyable."""
    return isinstance(t, TExcl)


def region_of(t: Ty) -> str | None:
    if isinstance(t, (TInRegion, TShared, TExcl)):
        return t.region
    return None


# --------------------------------------------------------- region state

@dataclass
class RegionState:
    open: bool = True
    shared_live: int = 0
    excl_live: bool = False


@dataclass
class Undo:
    """What to unwind when the block that acquired an access finishes."""
    region: str
    kind: str      # "shared" | "excl"


class Checker:
    def __init__(self, prog: a.Program) -> None:
        self.prog = prog
        self.regions: dict[str, RegionState] = {}

    def check(self) -> None:
        for fn in self.prog.fns.values():
            self.check_fn(fn)
        self.check_block(self.prog.main, {})

    def check_fn(self, fn: a.FnDecl) -> None:
        if any(p.ty != "Int" for p in fn.params) or fn.ret != "Int":
            raise CheckError("R1000", fn.line,
                             "regionlab functions support only `Int` "
                             "parameters and return type in this "
                             "prototype (region-typed function "
                             "boundaries are an open question -- "
                             "OWNERSHIP-MODEL.md §7.3)")
        env = {p.name: TInt() for p in fn.params}
        self.check_block(fn.body, env)

    # ------------------------------------------------------------- block
    def check_block(self, block: a.Block, outer_env: dict) -> Ty:
        env = dict(outer_env)
        undo: list[Undo] = []
        for st in block.stmts:
            self.check_stmt(st, env, undo)
        result: Ty = TInt()
        if block.tail is not None:
            result = self.check_expr(block.tail, env)
        self._unwind(undo)
        return result

    def _unwind(self, undo: list[Undo]) -> None:
        for u in reversed(undo):
            st = self.regions[u.region]
            if u.kind == "shared":
                st.shared_live -= 1
            else:
                st.excl_live = False

    # --------------------------------------------------------- statements
    def check_stmt(self, st, env: dict, undo: list[Undo]) -> None:
        if isinstance(st, a.Let):
            ty = self.check_expr(st.value, env)
            env[st.name] = ty
            self._record_acquisition(st.value, undo)
            return
        if isinstance(st, a.Close):
            r = self._region(st.region, st.line)
            if not r.open:
                raise CheckError("R1003", st.line,
                                 f"region `{st.region}` is already closed "
                                 f"-- closing it twice is a double-free")
            r.open = False
            return
        if isinstance(st, a.Write):
            ty = env.get(st.name)
            if ty is None:
                raise CheckError("R1008", st.line, f"unknown name `{st.name}`")
            if not isinstance(ty, TInRegion):
                raise CheckError("R1006", st.line,
                                 f"`{st.name}` is not region-allocated data "
                                 f"(has type {ty})")
            self._check_live(ty.region, st.line)
            r = self.regions[ty.region]
            if not r.excl_live:
                raise CheckError("R1006", st.line,
                                 f"write to `{st.name}` needs a live "
                                 f"exclusive capability for region "
                                 f"`{ty.region}` -- none is held here")
            self.check_expr(st.value, env)
            return
        if isinstance(st, a.ExprStmt):
            self.check_expr(st.value, env)
            return
        raise AssertionError(type(st))

    def _record_acquisition(self, expr, undo: list[Undo]) -> None:
        if isinstance(expr, a.Shared):
            undo.append(Undo(expr.region, "shared"))
        elif isinstance(expr, a.Exclusive):
            undo.append(Undo(expr.region, "excl"))
        elif isinstance(expr, a.Copy):
            # a copy of a Shared value is itself another live share
            undo.append(Undo(self._copy_target_region, "shared"))

    # -------------------------------------------------------- expressions
    def check_expr(self, e, env: dict) -> Ty:
        if isinstance(e, a.IntLit):
            return TInt()

        if isinstance(e, a.Var):
            ty = env.get(e.name)
            if ty is None:
                raise CheckError("R1008", e.line, f"unknown name `{e.name}`")
            r = region_of(ty)
            if r is not None:
                self._check_live(r, e.line)
            return ty

        if isinstance(e, a.RegionBlock):
            self.regions[e.name] = RegionState()
            result = self.check_block(e.body, env)
            r = region_of(result)
            if r == e.name:
                raise CheckError(
                    "R1001", e.line,
                    f"a value tied to region `{e.name}` escapes the block "
                    f"that owns it -- this would be a dangling reference "
                    f"the instant the region closes")
            self.regions[e.name].open = False
            return result

        if isinstance(e, a.Alloc):
            r = self._region(e.region, e.line)
            if not r.open:
                raise CheckError("R1002", e.line,
                                 f"cannot allocate into closed region "
                                 f"`{e.region}`")
            self.check_expr(e.value, env)
            return TInRegion(e.region)

        if isinstance(e, a.Read):
            ty = env.get(e.name)
            if ty is None:
                raise CheckError("R1008", e.line, f"unknown name `{e.name}`")
            if isinstance(ty, TInRegion):
                self._check_live(ty.region, e.line)
                r = self.regions[ty.region]
                if r.shared_live == 0 and not r.excl_live:
                    raise CheckError(
                        "R1006", e.line,
                        f"reading `{e.name}` needs a live shared or "
                        f"exclusive capability for region `{ty.region}` "
                        f"-- none is held here")
                return TInt()
            r = region_of(ty)
            if r is not None:
                self._check_live(r, e.line)
            return TInt()

        if isinstance(e, a.Shared):
            r = self._region(e.region, e.line)
            if not r.open:
                raise CheckError("R1002", e.line,
                                 f"cannot borrow closed region `{e.region}`")
            r.shared_live += 1
            return TShared(e.region)

        if isinstance(e, a.Exclusive):
            r = self._region(e.region, e.line)
            if not r.open:
                raise CheckError("R1002", e.line,
                                 f"cannot borrow closed region `{e.region}`")
            if r.excl_live or r.shared_live > 0:
                raise CheckError(
                    "R1005", e.line,
                    f"region `{e.region}`'s exclusive capability is "
                    f"already held (or a shared reader is live) -- two "
                    f"simultaneous holders would be exactly the aliasing "
                    f"that causes a data race once concurrency exists "
                    f"(OWNERSHIP-MODEL.md §6)")
            r.excl_live = True
            return TExcl(e.region)

        if isinstance(e, a.Copy):
            ty = env.get(e.name)
            if ty is None:
                raise CheckError("R1008", e.line, f"unknown name `{e.name}`")
            if is_linear(ty):
                raise CheckError(
                    "R1007", e.line,
                    f"`{e.name}` has type {ty}, which is linear and "
                    f"cannot be copied -- exactly one holder may exist "
                    f"at a time (OWNERSHIP-MODEL.md §4)")
            if isinstance(ty, TShared):
                self._check_live(ty.region, e.line)
                self.regions[ty.region].shared_live += 1
                self._copy_target_region = ty.region
            return ty

        if isinstance(e, a.Call):
            fn = self.prog.fns.get(e.fn)
            if fn is None:
                raise CheckError("R1008", e.line, f"unknown function `{e.fn}`")
            if len(fn.params) != len(e.args):
                raise CheckError(
                    "R1009", e.line,
                    f"`{e.fn}` expects {len(fn.params)} argument(s), "
                    f"found {len(e.args)}")
            for arg, p in zip(e.args, fn.params):
                at = self.check_expr(arg, env)
                if not isinstance(at, TInt):
                    raise CheckError(
                        "R1000", e.line,
                        f"argument to `{e.fn}` must be Int in this "
                        f"prototype, found {at}")
            return TInt()

        raise AssertionError(type(e))

    def _region(self, name: str, line: int) -> RegionState:
        if name not in self.regions:
            raise CheckError("R1008", line, f"unknown region `{name}`")
        return self.regions[name]

    def _check_live(self, region: str, line: int) -> None:
        if not self.regions[region].open:
            raise CheckError(
                "R1002", line,
                f"use of a value from region `{region}` after it closed "
                f"-- this is exactly a use-after-free")


def check(prog: a.Program) -> None:
    Checker(prog).check()
