"""Type and effect checker for NOVA v0.2 (RFC 0001-0005).

Implements RFC 0001 §4.8 plus the derivation rule (§4.3): a function's
declared effect row is checked for *equality* with the row inferred from
its body, not subsumption. `= widen` opts into subsumption at a
syntactically greppable site.

RFC 0002 (structs/enums/pattern matching), RFC 0003 (generics/traits) and
RFC 0004 (modules) extend the same checker rather than adding a second
pass, for the reason RFC 0002 §3 gives in full: because a struct's field
types are ordinary, always-inspectable structural information (unlike a
closure's captured environment), the existing effect machinery generalizes
to structs with *no new rule* — `MethodCall`'s existing capability-op
branch fires exactly when a field projection's resolved type happens to
be a capability type. Nothing here special-cases that; it falls out of
ordinary structural type checking.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast as a
from .diagnostics import Diagnostic, Label, Span
from .reachability import Reach, analyze
from .types import (BOOL, GROUND, INT, STRING, UNIT, Row, RowMismatch,
                    Subst, TCap, TCon, TEnum, TFun, TStruct, TTuple, TVar,
                    Type, instantiate, occurs, substitute, unify_rows,
                    unify_types)


@dataclass
class CapInfo:
    name: str
    span: Span
    ops: dict[str, TFun] = field(default_factory=dict)


@dataclass
class FnInfo:
    name: str
    decl: a.FnDecl
    row_params: list[str]
    type_params: list[str]
    ty: TFun


@dataclass
class StructInfo:
    name: str
    decl: a.StructDecl
    type_params: list[str]
    fields: dict[str, Type] = field(default_factory=dict)


@dataclass
class EnumInfo:
    name: str
    decl: a.EnumDecl
    type_params: list[str]
    variants: dict[str, list[Type]] = field(default_factory=dict)


@dataclass
class TraitInfo:
    name: str
    decl: a.TraitDecl
    methods: dict[str, TFun] = field(default_factory=dict)   # no `self` slot


@dataclass
class ImplInfo:
    decl: a.ImplDecl
    trait_name: str
    type_params: list[str]
    target: Type
    methods: dict[str, a.FnDecl] = field(default_factory=dict)


@dataclass
class CheckResult:
    caps: dict[str, CapInfo]
    fns: dict[str, FnInfo]
    structs: dict[str, StructInfo]
    enums: dict[str, EnumInfo]
    traits: dict[str, TraitInfo]
    impls: dict[tuple[str, str], ImplInfo]     # (trait_name, type_head) -> impl
    reach: Reach
    widened: list[tuple[str, Span]]      # audit listing of `= widen` sites


def head_name(t: Type) -> str | None:
    """The nominal name at the head of a type, for trait-impl lookup and
    for enum/struct field-substitution — `Point`, `Option`, `Int`, or
    `None` for a type with no nominal head (a tuple, a function, a bare
    type variable)."""
    if isinstance(t, (TStruct, TEnum, TCon, TCap)):
        return t.name
    return None


class Checker:
    def __init__(self, prog: a.Program) -> None:
        self.prog = prog
        self.caps: dict[str, CapInfo] = {}
        self.fns: dict[str, FnInfo] = {}
        self.structs: dict[str, StructInfo] = {}
        self.enums: dict[str, EnumInfo] = {}
        self.traits: dict[str, TraitInfo] = {}
        self.impls: dict[tuple[str, str], ImplInfo] = {}
        self.widened: list[tuple[str, Span]] = []
        self.reach = analyze(prog)

        # Visibility (RFC 0004): which module a name was declared in, and
        # whether it is `pub`. Modules provide organization and visibility
        # control only, not namespacing — see RFC 0004 §2 for why a flat,
        # globally-unique name space was chosen over qualified paths.
        self.module_of: dict[str, str] = {}
        self.is_pub: dict[str, bool] = {}
        self.imports: dict[str, set[str]] = {}   # module -> imported modules
        for m in prog.modules:
            self.imports.setdefault(m.path, set())
            for d in m.decls:
                if isinstance(d, a.ImportDecl):
                    self.imports[m.path].add(".".join(d.path))

        # per-function state
        self.rigid_rows: set[str] = set()
        self.rigid_types: set[str] = set()
        self.bounds: dict[str, str] = {}      # type param name -> trait name
        self.subst = Subst()
        self.cur_fn: a.FnDecl | None = None
        self.cur_module: str = ""
        self.cur_self_type: Type | None = None      # inside an `impl`

    # ------------------------------------------------------ collection
    def collect(self) -> None:
        # Pass 1: register every name, so recursive/mutually-referencing
        # declarations (an enum whose variant contains itself, a struct
        # referring to another struct declared later in the file) can be
        # resolved before any field or signature type is filled in.
        for m in self.prog.modules:
            for d in m.decls:
                if isinstance(d, a.ImportDecl):
                    continue
                name = getattr(d, "name", None) or getattr(d, "trait_name", None)
                if isinstance(d, a.ImplDecl):
                    continue   # impls have no name of their own to register
                if name in self.module_of:
                    raise Diagnostic(
                        "E0100", f"`{name}` is declared twice",
                        [Label(d.name_span, "duplicate declaration")])
                self.module_of[name] = m.path
                self.is_pub[name] = getattr(d, "is_pub", False)
                if isinstance(d, a.CapabilityDecl):
                    self.caps[d.name] = CapInfo(d.name, d.name_span)
                elif isinstance(d, a.StructDecl):
                    self.structs[d.name] = StructInfo(
                        d.name, d, [tp.name for tp in d.type_params])
                elif isinstance(d, a.EnumDecl):
                    self.enums[d.name] = EnumInfo(
                        d.name, d, [tp.name for tp in d.type_params])
                elif isinstance(d, a.TraitDecl):
                    self.traits[d.name] = TraitInfo(d.name, d)

        # Pass 2: resolve field types, variant types, capability ops, and
        # function signatures, now that every nominal name exists.
        for m in self.prog.modules:
            self.cur_module = m.path
            for d in m.decls:
                if isinstance(d, a.CapabilityDecl):
                    info = self.caps[d.name]
                    for op in d.ops:
                        params = tuple(self.resolve_type(p.ty) for p in op.params)
                        info.ops[op.name] = TFun(params,
                                                 self.resolve_type(op.ret),
                                                 Row.of(d.name))
                elif isinstance(d, a.StructDecl):
                    info = self.structs[d.name]
                    rigid = set(info.type_params)
                    for f_ in d.fields:
                        info.fields[f_.name] = self.resolve_type(f_.ty, rigid_types=rigid)
                elif isinstance(d, a.EnumDecl):
                    info = self.enums[d.name]
                    rigid = set(info.type_params)
                    for v in d.variants:
                        info.variants[v.name] = [
                            self.resolve_type(t, rigid_types=rigid) for t in v.args]
                elif isinstance(d, a.TraitDecl):
                    info = self.traits[d.name]
                    for ms in d.methods:
                        params = tuple(self.resolve_type(p.ty) for p in ms.params)
                        info.methods[ms.name] = TFun(params,
                                                     self.resolve_type(ms.ret),
                                                     Row.pure())
                elif isinstance(d, a.FnDecl):
                    if d.name in self.fns:
                        raise Diagnostic(
                            "E0100", f"function `{d.name}` is declared twice",
                            [Label(d.name_span, "duplicate declaration")])
                    self.fns[d.name] = self._fn_info(d)
                elif isinstance(d, a.ImplDecl):
                    self._collect_impl(d)

    def _fn_info(self, d: a.FnDecl) -> FnInfo:
        row_rigid = set(d.row_params)
        type_rigid = {tp.name for tp in d.type_params}
        params = tuple(self.resolve_type(p.ty, row_rigid, type_rigid)
                       for p in d.params)
        ret = self.resolve_type(d.ret, row_rigid, type_rigid)
        eff = self.resolve_row(d.eff, row_rigid) if d.eff else Row.pure()
        return FnInfo(d.name, d, d.row_params,
                      [tp.name for tp in d.type_params],
                      TFun(params, ret, eff))

    def _collect_impl(self, d: a.ImplDecl) -> None:
        if d.trait_name not in self.traits:
            raise Diagnostic(
                "E0111", f"unknown trait `{d.trait_name}`",
                [Label(d.trait_name_span, "not declared")])
        rigid = {tp.name for tp in d.type_params}
        target = self.resolve_type(d.target, rigid_types=rigid)
        head = head_name(target)
        if head is None:
            raise Diagnostic(
                "E0112", "an `impl` target must be a nominal type",
                [Label(d.target.span, f"`{target}` has no name to "
                       "attach an implementation to")],
                notes=["tuples and function types cannot be `impl` targets "
                       "in v0.2"])
        key = (d.trait_name, head)
        if key in self.impls:
            raise Diagnostic(
                "E0113",
                f"`{d.trait_name}` is already implemented for `{head}`",
                [Label(d.trait_name_span, "duplicate implementation")])
        trait_methods = self.traits[d.trait_name].methods
        methods: dict[str, a.FnDecl] = {}
        for m in d.methods:
            if m.name not in trait_methods:
                raise Diagnostic(
                    "E0114",
                    f"`{m.name}` is not a method of trait `{d.trait_name}`",
                    [Label(m.name_span, "unknown trait method")],
                    notes=[f"`{d.trait_name}` declares: "
                           f"{', '.join(sorted(trait_methods)) or '(none)'}"])
            methods[m.name] = m
        missing = set(trait_methods) - set(methods)
        if missing:
            raise Diagnostic(
                "E0115",
                f"missing implementation for "
                f"{', '.join(sorted('`' + x + '`' for x in missing))}",
                [Label(d.trait_name_span, f"`impl {d.trait_name} for "
                       f"{d.target}` is incomplete")])
        self.impls[key] = ImplInfo(d, d.trait_name, [tp.name for tp in
                                                     d.type_params], target,
                                   methods)

    # -------------------------------------------------- type resolution
    def resolve_type(self, t: a.TypeExpr, rigid_rows: set[str] | None = None,
                     rigid_types: set[str] | None = None) -> Type:
        rigid_rows = rigid_rows or set()
        rigid_types = rigid_types or set()
        if isinstance(t, a.TName):
            if t.name == "Self":
                if self.cur_self_type is None:
                    raise Diagnostic(
                        "E0128", "`Self` used outside an `impl`",
                        [Label(t.span, "no target type in scope")])
                return self.cur_self_type
            if t.args:
                arg_tys = [self.resolve_type(x, rigid_rows, rigid_types)
                          for x in t.args]
                if t.name in self.structs:
                    return TStruct(t.name, tuple(arg_tys))
                if t.name in self.enums:
                    return TEnum(t.name, tuple(arg_tys))
                raise Diagnostic(
                    "E0102", f"`{t.name}` does not take type arguments",
                    [Label(t.span, "only structs and enums may be "
                           "parameterized")])
            if t.name in rigid_types:
                return TVar(t.name)
            if t.name in GROUND:
                return GROUND[t.name]
            if t.name in self.caps:
                return TCap(t.name)
            if t.name in self.structs:
                if self.structs[t.name].type_params:
                    raise Diagnostic(
                        "E0116", f"`{t.name}` requires type arguments",
                        [Label(t.span, f"expected `{t.name}[...]`")])
                return TStruct(t.name, ())
            if t.name in self.enums:
                if self.enums[t.name].type_params:
                    raise Diagnostic(
                        "E0116", f"`{t.name}` requires type arguments",
                        [Label(t.span, f"expected `{t.name}[...]`")])
                return TEnum(t.name, ())
            raise Diagnostic(
                "E0102", f"unknown type `{t.name}`",
                [Label(t.span, "not a built-in type, capability, struct, "
                       "enum, or type parameter in scope")],
                notes=[f"built-in types are: {', '.join(sorted(GROUND))}"])
        if isinstance(t, a.TTupleExpr):
            return TTuple(tuple(self.resolve_type(x, rigid_rows, rigid_types)
                                for x in t.elems))
        if isinstance(t, a.TFunExpr):
            return TFun(tuple(self.resolve_type(p, rigid_rows, rigid_types)
                              for p in t.params),
                        self.resolve_type(t.ret, rigid_rows, rigid_types),
                        self.resolve_row(t.eff, rigid_rows) if t.eff
                        else Row.pure())
        raise AssertionError(type(t).__name__)

    def resolve_row(self, r: a.RowExpr, rigid: set[str]) -> Row:
        labels = set()
        for name, span in r.labels:
            if name not in self.caps:
                raise Diagnostic(
                    "E0103", f"unknown effect `{name}`",
                    [Label(span, "no capability with this name is declared")],
                    notes=["an effect label is a capability type name "
                           "(RFC 0001 §4.1)"])
            labels.add(name)
        if r.tail is not None and r.tail not in rigid:
            raise Diagnostic(
                "E0104", f"unbound row variable `{r.tail}`",
                [Label(r.span, "not declared by the enclosing function")],
                helps=[f"declare it: `fn name[{r.tail}](...)`"])
        return Row(frozenset(labels), r.tail)

    # -------------------------------------------------------- checking
    def check(self) -> CheckResult:
        self.collect()
        for m in self.prog.modules:
            self.cur_module = m.path
            for d in m.decls:
                if isinstance(d, a.FnDecl):
                    self.check_fn(d)
                elif isinstance(d, a.ImplDecl):
                    rigid = {tp.name for tp in d.type_params}
                    target = self.resolve_type(d.target, rigid_types=rigid)
                    for md in d.methods:
                        self.check_fn(md, impl=self.impls[(d.trait_name,
                                                           head_name(target))])
        self.check_entry()
        return CheckResult(self.caps, self.fns, self.structs, self.enums,
                           self.traits, self.impls, self.reach, self.widened)

    def check_entry(self) -> None:
        main = self.fns.get("main")
        if main is None:
            return
        sig = main.ty
        ok = (len(sig.params) == 1 and isinstance(sig.params[0], TCap)
              and sig.params[0].name == "Runtime" and sig.ret == INT)
        if not ok:
            raise Diagnostic(
                "E0210", "`main` has the wrong signature",
                [Label(main.decl.name_span, f"found `{sig}`")],
                notes=["the entry point receives the root capability "
                       "(RFC 0001 §4.7)"],
                helps=["expected `fn main(rt: Runtime) -> Int ! {Runtime}`"])

    def check_fn(self, d: a.FnDecl, impl: ImplInfo | None = None) -> None:
        self.cur_self_type = impl.target if impl is not None else None
        info = self._fn_info(d) if impl is not None else self.fns[d.name]
        if impl is not None:
            self._check_impl_signature(d, info, impl)
        self.rigid_rows = set(d.row_params)
        self.rigid_types = {tp.name for tp in d.type_params}
        self.bounds = {tp.name: tp.bound for tp in d.type_params if tp.bound}
        if impl is not None:
            self.rigid_types |= set(impl.type_params)
        self.subst = Subst()
        self.cur_fn = d
        env: dict[str, tuple[Type, bool]] = {
            p.name: (impl.target if p.name == "self" and impl is not None
                    else t, False)
            for p, t in zip(d.params, info.ty.params)}

        body_ty, body_row = self.infer(d.body, env)
        self.expect_type(d.body, body_ty, info.ty.ret,
                         f"function `{d.name}` returns")

        inferred = self.subst.resolve_row(body_row)
        declared = self.subst.resolve_row(info.ty.eff)
        self.compare_rows(d, inferred, declared)

    def _check_impl_signature(self, d: a.FnDecl, info: FnInfo,
                              impl: ImplInfo) -> None:
        """An `impl`'s written signature must match the trait's declared
        one (with `Self` resolved to the impl's target), or a caller who
        checked against the trait's contract (`MethodCall`'s dispatch
        uses exactly that contract, never the impl's own text) could
        observe a value of a type the impl body never actually promised
        to produce — a soundness hole, not just a style issue."""
        trait_sig = self.traits[impl.trait_name].methods.get(d.name)
        if trait_sig is None:
            return    # already reported by `_collect_impl`
        # `self` occupies info.ty.params[0]; trait signatures exclude it.
        own = TFun(info.ty.params[1:], info.ty.ret, Row.pure())
        s = Subst()
        if not unify_types(own, trait_sig, s) or own != trait_sig:
            raise Diagnostic(
                "E0127",
                f"`{d.name}` does not match trait "
                f"`{impl.trait_name}`'s declared signature",
                [Label(d.name_span, f"found `{own}`")],
                notes=[f"trait declares `{trait_sig}`"])

    def compare_rows(self, d: a.FnDecl, inferred: Row, declared: Row) -> None:
        eff_span = d.eff_span or d.name_span
        missing = inferred.labels - declared.labels
        extra = declared.labels - inferred.labels
        tails_agree = inferred.tail == declared.tail

        if d.widen:
            self.widened.append((d.name, eff_span))
            if missing or (inferred.tail and not declared.tail):
                raise Diagnostic(
                    "E0201",
                    f"function declares effects {declared} but performs "
                    f"{inferred}",
                    [Label(eff_span, "declared row is too small")],
                    notes=["`= widen` permits over-approximation, "
                           "never under-approximation"])
            return

        if missing:
            labels = [Label(eff_span, f"declared row is {declared}")]
            spans = self.reach.binding_spans.get(d.node_id, {})
            for name, span in spans.items():
                labels.append(Label(span, "capability enters here",
                                    primary=False))
            raise Diagnostic(
                "E0201",
                f"function declares no effects but performs "
                f"{{{', '.join(sorted(missing))}}}" if declared.is_pure()
                else f"function performs undeclared effects "
                     f"{{{', '.join(sorted(missing))}}}",
                labels,
                notes=[f"inferred row is {inferred}, "
                       f"declared row is {declared}"],
                helps=[f"declare the effects: `! {inferred}`"])

        if extra:
            raise Diagnostic(
                "E0202",
                f"declared effect{'s' if len(extra) > 1 else ''} "
                f"{', '.join('`' + x + '`' for x in sorted(extra))} "
                f"{'are' if len(extra) > 1 else 'is'} never performed",
                [Label(eff_span, f"not in inferred row {inferred}")],
                notes=["NOVA checks effect rows for equality, not "
                       "subsumption (RFC 0001 §4.3)"],
                helps=["remove it, or mark the widening as deliberate with "
                       "`= widen`"])

        if not tails_agree:
            raise Diagnostic(
                "E0204", "effect row variables do not match",
                [Label(eff_span,
                       f"declared {declared}, inferred {inferred}")],
                notes=["a row-polymorphic function must pass its row "
                       "variable through unchanged"])

    # -------------------------------------------------------- visibility
    def check_visible(self, name: str, span: Span) -> None:
        owner = self.module_of.get(name)
        if owner is None or owner == self.cur_module:
            return
        if self.is_pub.get(name) and owner in self.imports.get(self.cur_module, ()):
            return
        if not self.is_pub.get(name):
            raise Diagnostic(
                "E0120", f"`{name}` is private to module `{owner}`",
                [Label(span, "not accessible from here")],
                helps=[f"mark it `pub` in `{owner}`"])
        raise Diagnostic(
            "E0121", f"`{name}` is not imported",
            [Label(span, f"defined in module `{owner}`, which this "
                   f"module does not import")],
            helps=[f"add `import {owner};`"])

    # ------------------------------------------------------- inference
    def infer(self, e, env: dict[str, Type]) -> tuple[Type, Row]:
        if isinstance(e, a.IntLit):
            return INT, Row.pure()
        if isinstance(e, a.StrLit):
            return STRING, Row.pure()
        if isinstance(e, a.BoolLit):
            return BOOL, Row.pure()
        if isinstance(e, a.UnitLit):
            return UNIT, Row.pure()

        if isinstance(e, a.Var):
            if e.name in env:
                return env[e.name][0], Row.pure()
            if e.name in self.fns:
                self.check_visible(e.name, e.span)
                fn = self.fns[e.name]
                rigid = set(fn.row_params) | set(fn.type_params)
                return instantiate(fn.ty, rigid, self.subst), Row.pure()
            raise Diagnostic("E0101", f"cannot find `{e.name}` in this scope",
                             [Label(e.span, "not found")])

        if isinstance(e, a.Unary):
            t, r = self.infer(e.operand, env)
            want = INT if e.op == "-" else BOOL
            self.expect_type(e.operand, t, want, f"operator `{e.op}`")
            return want, r

        if isinstance(e, a.Binary):
            lt, lr = self.infer(e.left, env)
            rt, rr = self.infer(e.right, env)
            row = self.join(lr, rr)
            if e.op in ("+", "-", "*", "/"):
                self.expect_type(e.left, lt, INT, f"operator `{e.op}`")
                self.expect_type(e.right, rt, INT, f"operator `{e.op}`")
                return INT, row
            if e.op in ("&&", "||"):
                self.expect_type(e.left, lt, BOOL, f"operator `{e.op}`")
                self.expect_type(e.right, rt, BOOL, f"operator `{e.op}`")
                return BOOL, row
            if e.op in ("<", "<=", ">", ">="):
                self.expect_type(e.left, lt, INT, f"operator `{e.op}`")
                self.expect_type(e.right, rt, INT, f"operator `{e.op}`")
                return BOOL, row
            self.expect_type(e.right, rt, lt, f"operator `{e.op}`")
            if isinstance(lt, (TFun, TCap)):
                raise Diagnostic(
                    "E0107", f"`{lt}` cannot be compared",
                    [Label(e.span, "equality is defined on Int, Bool, "
                                   "String and Unit only")])
            return BOOL, row

        if isinstance(e, a.If):
            ct, cr = self.infer(e.cond, env)
            self.expect_type(e.cond, ct, BOOL, "the condition of `if`")
            tt, tr = self.infer(e.then, env)
            et, er = self.infer(e.els, env)
            self.expect_type(e.els, et, tt, "both branches of `if`")
            return tt, self.join(cr, self.join(tr, er))

        if isinstance(e, a.While):
            ct, cr = self.infer(e.cond, env)
            self.expect_type(e.cond, ct, BOOL, "the condition of `while`")
            _, br = self.infer(e.body, env)
            return UNIT, self.join(cr, br)

        if isinstance(e, a.For):
            it, ir = self.infer(e.iter, env)
            it = self.subst.resolve_type(it)
            if not (isinstance(it, TEnum) and it.name == "List"):
                raise Diagnostic(
                    "E0122", f"`for` needs a `List[_]`, found `{it}`",
                    [Label(e.iter.span, f"has type `{it}`")])
            elem_ty = it.args[0]
            inner = dict(env)
            inner[e.var] = (elem_ty, False)
            _, br = self.infer(e.body, inner)
            return UNIT, self.join(ir, br)

        if isinstance(e, a.Assign):
            if e.name not in env:
                raise Diagnostic("E0101",
                                 f"cannot find `{e.name}` in this scope",
                                 [Label(e.name_span, "not found")])
            declared_ty, is_mut = env[e.name]
            if not is_mut:
                raise Diagnostic(
                    "E0126", f"cannot assign to `{e.name}`: not declared `mut`",
                    [Label(e.name_span, "immutable binding")],
                    helps=[f"declare it as `let mut {e.name} = ...;`"])
            vt, vr = self.infer(e.value, env)
            self.expect_type(e.value, vt, declared_ty,
                             f"assignment to `{e.name}`")
            return UNIT, vr

        if isinstance(e, a.Block):
            inner = dict(env)
            row = Row.pure()
            for st in e.stmts:
                if isinstance(st, a.Let):
                    vt, vr = self.infer(st.value, inner)
                    if st.ty is not None:
                        want = self.resolve_type(st.ty, self.rigid_rows,
                                                 self.rigid_types)
                        self.expect_type(st.value, vt, want,
                                         f"binding `{st.name}`")
                        vt = want
                    inner[st.name] = (vt, st.mut)
                    row = self.join(row, vr)
                else:
                    _, sr = self.infer(st, inner)
                    row = self.join(row, sr)
            if e.tail is None:
                return UNIT, row
            tt, tr = self.infer(e.tail, inner)
            return tt, self.join(row, tr)

        if isinstance(e, a.Lambda):
            self._check_no_mut_capture(e, env)
            inner = dict(env)
            ptys = []
            for p in e.params:
                t = self.resolve_type(p.ty, self.rigid_rows, self.rigid_types)
                inner[p.name] = (t, False)
                ptys.append(t)
            bt, br = self.infer(e.body, inner)
            return TFun(tuple(ptys), bt, self.subst.resolve_row(br)), \
                Row.pure()

        if isinstance(e, a.TupleLit):
            row = Row.pure()
            tys = []
            for x in e.elems:
                xt, xr = self.infer(x, env)
                tys.append(xt)
                row = self.join(row, xr)
            return TTuple(tuple(tys)), row

        if isinstance(e, a.StructLit):
            if e.name not in self.structs:
                raise Diagnostic("E0102", f"unknown struct `{e.name}`",
                                 [Label(e.name_span, "not declared")])
            self.check_visible(e.name, e.name_span)
            info = self.structs[e.name]
            given = {n for n, _ in e.fields}
            declared = set(info.fields)
            if given != declared:
                missing = declared - given
                extra = given - declared
                parts = []
                if missing:
                    parts.append(f"missing {', '.join(sorted(missing))}")
                if extra:
                    parts.append(f"unknown {', '.join(sorted(extra))}")
                raise Diagnostic(
                    "E0117", f"`{e.name}` field mismatch: {'; '.join(parts)}",
                    [Label(e.span, f"`{e.name}` declares "
                           f"{{{', '.join(sorted(declared))}}}")])
            mapping = {p: TVar(self.subst.fresh_type())
                      for p in info.type_params}
            row = Row.pure()
            for fname, fexpr in e.fields:
                want = substitute(info.fields[fname], mapping)
                ft, fr = self.infer(fexpr, env)
                self.expect_type(fexpr, ft, want, f"field `{fname}`")
                row = self.join(row, fr)
            args = tuple(self.subst.resolve_type(mapping[p])
                        for p in info.type_params)
            return TStruct(e.name, args), row

        if isinstance(e, a.EnumCtor):
            if e.enum_name not in self.enums:
                raise Diagnostic("E0102", f"unknown enum `{e.enum_name}`",
                                 [Label(e.span, "not declared")])
            self.check_visible(e.enum_name, e.span)
            info = self.enums[e.enum_name]
            if e.variant not in info.variants:
                raise Diagnostic(
                    "E0118",
                    f"`{e.enum_name}` has no variant `{e.variant}`",
                    [Label(e.variant_span, "unknown variant")],
                    notes=[f"`{e.enum_name}` declares: "
                           f"{', '.join(sorted(info.variants))}"])
            arg_tys = info.variants[e.variant]
            if len(arg_tys) != len(e.args):
                raise Diagnostic(
                    "E0106",
                    f"`{e.enum_name}::{e.variant}` expects {len(arg_tys)} "
                    f"argument{'s' if len(arg_tys) != 1 else ''}, "
                    f"found {len(e.args)}",
                    [Label(e.span, "here")])
            mapping = {p: TVar(self.subst.fresh_type())
                      for p in info.type_params}
            row = Row.pure()
            for arg, declared_t in zip(e.args, arg_tys):
                want = substitute(declared_t, mapping)
                at, ar = self.infer(arg, env)
                self.expect_type(arg, at, want, f"`{e.enum_name}::{e.variant}` argument")
                row = self.join(row, ar)
            args = tuple(self.subst.resolve_type(mapping[p])
                        for p in info.type_params)
            return TEnum(e.enum_name, args), row

        if isinstance(e, a.FieldAccess):
            rt_, rr = self.infer(e.recv, env)
            rt_ = self.subst.resolve_type(rt_)
            if isinstance(rt_, TTuple):
                if not e.field.isdigit() or int(e.field) >= len(rt_.elems):
                    raise Diagnostic(
                        "E0119", f"`{rt_}` has no field `.{e.field}`",
                        [Label(e.field_span, "out of range")])
                return rt_.elems[int(e.field)], rr
            if isinstance(rt_, TStruct):
                info = self.structs.get(rt_.name)
                if info is None or e.field not in info.fields:
                    raise Diagnostic(
                        "E0119", f"`{rt_}` has no field `{e.field}`",
                        [Label(e.field_span, "unknown field")],
                        notes=[f"`{rt_.name}` declares: "
                              f"{', '.join(sorted(info.fields)) if info else ''}"])
                mapping = dict(zip(info.type_params, rt_.args))
                return substitute(info.fields[e.field], mapping), rr
            raise Diagnostic(
                "E0119", f"`{rt_}` has no field `{e.field}`",
                [Label(e.recv.span, f"has type `{rt_}`")],
                notes=["field access `.name` applies to structs and tuples "
                       "only; use `.name(...)` for a method or capability "
                       "operation"])

        if isinstance(e, a.Match):
            st, sr = self.infer(e.scrutinee, env)
            st = self.subst.resolve_type(st)
            row = sr
            result_ty: Type | None = None
            covered: set[str] = set()
            has_catch_all = False
            for arm in e.arms:
                inner = dict(env)
                self.check_pattern(arm.pattern, st, inner, covered)
                if isinstance(arm.pattern, (a.PWildcard, a.PBind)):
                    has_catch_all = True
                bt, br = self.infer(arm.body, inner)
                if result_ty is None:
                    result_ty = bt
                else:
                    self.expect_type(arm.body, bt, result_ty,
                                     "every arm of `match`")
                row = self.join(row, br)
            self.check_exhaustive(e, st, covered, has_catch_all)
            return (result_ty if result_ty is not None else UNIT), row

        if isinstance(e, a.Call):
            ft, fr = self.infer(e.callee, env)
            ft = self.subst.resolve_type(ft)
            if not isinstance(ft, TFun):
                raise Diagnostic(
                    "E0105", f"`{ft}` is not callable",
                    [Label(e.callee.span, f"has type `{ft}`")])
            if len(ft.params) != len(e.args):
                raise Diagnostic(
                    "E0106",
                    f"expected {len(ft.params)} argument"
                    f"{'s' if len(ft.params) != 1 else ''}, "
                    f"found {len(e.args)}",
                    [Label(e.span, f"callee has type `{ft}`")])
            row = fr
            for arg, want in zip(e.args, ft.params):
                at, ar = self.infer(arg, env)
                self.expect_type(arg, at, want, "argument")
                row = self.join(row, ar)
            return ft.ret, self.join(row, ft.eff)

        if isinstance(e, a.MethodCall):
            rt_, rr = self.infer(e.recv, env)
            rt_ = self.subst.resolve_type(rt_)

            if isinstance(rt_, TCap):
                return self._infer_cap_use(e, rt_, rr, env)

            if isinstance(rt_, TVar) and self.subst.is_flexible(rt_.name):
                raise Diagnostic(
                    "E0123", "cannot call a method on a type that is "
                    "not yet known",
                    [Label(e.recv.span, "type must be resolved first")])

            trait_name = None
            if isinstance(rt_, TVar) and rt_.name in self.bounds:
                trait_name = self.bounds[rt_.name]
                sig = self.traits[trait_name].methods.get(e.op)
                if sig is None:
                    raise Diagnostic(
                        "E0114",
                        f"`{trait_name}` has no method `{e.op}`",
                        [Label(e.op_span, "unknown trait method")])
                target_map: dict[str, Type] = {}
            else:
                head = head_name(rt_)
                if head is None:
                    raise Diagnostic(
                        "E0108", f"`{rt_}` has no method `{e.op}`",
                        [Label(e.op_span, "not a capability, struct, or "
                               "enum with a matching trait implementation")])
                found = [key for key in self.impls
                        if key[1] == head and e.op in self.impls[key].methods]
                if not found:
                    raise Diagnostic(
                        "E0108",
                        f"`{rt_}` has no method `{e.op}`",
                        [Label(e.op_span, "no `impl` provides it")])
                impl = self.impls[found[0]]
                sig = self.traits[impl.trait_name].methods[e.op]
                target_map = dict(zip(impl.type_params,
                                      rt_.args if isinstance(rt_, (TStruct, TEnum))
                                      else ()))
            sig = substitute(sig, target_map) if target_map else sig
            if len(sig.params) != len(e.args):
                raise Diagnostic(
                    "E0106",
                    f"`.{e.op}(...)` expects {len(sig.params)} "
                    f"argument{'s' if len(sig.params) != 1 else ''}, "
                    f"found {len(e.args)}",
                    [Label(e.span, f"method type `{sig}`")])
            row = rr
            for arg, want in zip(e.args, sig.params):
                at, ar = self.infer(arg, env)
                self.expect_type(arg, at, want, "argument")
                row = self.join(row, ar)
            return sig.ret, row   # trait methods carry no effect of their own

        raise AssertionError(f"unhandled expression: {type(e).__name__}")

    def _infer_cap_use(self, e: a.MethodCall, rt_: TCap, rr: Row,
                       env: dict[str, Type]) -> tuple[Type, Row]:
        info = self.caps[rt_.name]
        if e.op not in info.ops:
            raise Diagnostic(
                "E0109",
                f"capability `{rt_.name}` has no operation `{e.op}`",
                [Label(e.op_span, "unknown operation")],
                notes=[f"`{rt_.name}` declares: "
                       f"{', '.join(sorted(info.ops)) or '(none)'}"])
        sig = info.ops[e.op]
        if len(sig.params) != len(e.args):
            raise Diagnostic(
                "E0106",
                f"`{rt_.name}.{e.op}` expects {len(sig.params)} "
                f"argument{'s' if len(sig.params) != 1 else ''}, "
                f"found {len(e.args)}",
                [Label(e.span, f"operation type `{sig}`")])
        row = rr
        for arg, want in zip(e.args, sig.params):
            at, ar = self.infer(arg, env)
            self.expect_type(arg, at, want, "argument")
            row = self.join(row, ar)
        # (CapUse): the receiver's own capability enters the row.
        return sig.ret, self.join(row, Row.of(rt_.name))

    # -------------------------------------------------------- patterns
    def check_pattern(self, p: a.Pattern, scrutinee: Type,
                      env: dict[str, tuple[Type, bool]],
                      covered: set[str]) -> None:
        scrutinee = self.subst.resolve_type(scrutinee)
        if isinstance(p, a.PWildcard):
            return
        if isinstance(p, a.PBind):
            env[p.name] = (scrutinee, False)
            return
        if isinstance(p, a.PInt):
            self.expect_type(p, INT, scrutinee, "pattern")
            return
        if isinstance(p, a.PBool):
            self.expect_type(p, BOOL, scrutinee, "pattern")
            return
        if isinstance(p, a.PString):
            self.expect_type(p, STRING, scrutinee, "pattern")
            return
        if isinstance(p, a.PTuple):
            if not isinstance(scrutinee, TTuple) or \
                    len(scrutinee.elems) != len(p.elems):
                raise Diagnostic(
                    "E0124", f"pattern does not match `{scrutinee}`",
                    [Label(p.span, "tuple pattern arity mismatch")])
            for sub, sty in zip(p.elems, scrutinee.elems):
                self.check_pattern(sub, sty, env, covered)
            return
        if isinstance(p, a.PVariant):
            if not isinstance(scrutinee, TEnum) or \
                    scrutinee.name != p.enum_name:
                raise Diagnostic(
                    "E0124", f"pattern does not match `{scrutinee}`",
                    [Label(p.span, f"expected a value of `{scrutinee}`")])
            info = self.enums[p.enum_name]
            if p.variant not in info.variants:
                raise Diagnostic(
                    "E0118", f"`{p.enum_name}` has no variant `{p.variant}`",
                    [Label(p.variant_span, "unknown variant")])
            covered.add(p.variant)
            mapping = dict(zip(info.type_params, scrutinee.args))
            arg_tys = [substitute(t, mapping) for t in info.variants[p.variant]]
            if len(arg_tys) != len(p.args):
                raise Diagnostic(
                    "E0106",
                    f"`{p.enum_name}::{p.variant}` pattern expects "
                    f"{len(arg_tys)} argument"
                    f"{'s' if len(arg_tys) != 1 else ''}, found {len(p.args)}",
                    [Label(p.span, "here")])
            for sub, sty in zip(p.args, arg_tys):
                self.check_pattern(sub, sty, env, covered)
            return
        raise AssertionError(f"unhandled pattern: {type(p).__name__}")

    def check_exhaustive(self, e: a.Match, scrutinee: Type,
                         covered: set[str], has_catch_all: bool) -> None:
        if has_catch_all:
            return
        if isinstance(scrutinee, TEnum):
            info = self.enums[scrutinee.name]
            missing = set(info.variants) - covered
            if missing:
                raise Diagnostic(
                    "E0220",
                    f"non-exhaustive match: missing "
                    f"{', '.join(sorted('`' + m + '`' for m in missing))}",
                    [Label(e.span, f"`{scrutinee}` has unmatched variants")],
                    helps=["add the missing arms, or a wildcard `_ => ...`"])
            return
        raise Diagnostic(
            "E0220",
            f"non-exhaustive match over `{scrutinee}`",
            [Label(e.span, "add a wildcard `_ => ...` arm")],
            notes=["only enum matches can be checked variant-by-variant; "
                   "every other scrutinee type needs a catch-all"])

    # -------------------------------------------------------- helpers
    def _check_no_mut_capture(self, e: a.Lambda,
                              env: dict[str, tuple[Type, bool]]) -> None:
        """RFC 0005 §4: a closure may not capture a `mut` local.

        If it could, the closure and its enclosing scope would hold two
        live references to the same mutable slot after the closure
        escapes — exactly the aliasing Constitution Article XI forbids.
        Forbidding this at the checker is what makes the reference
        evaluator's cell-sharing implementation of `mut` locals
        (eval.py) sound: mutation and capture never overlap, so nothing
        needs a borrow check to keep them apart.
        """
        from .reachability import _mentions
        param_names = {p.name for p in e.params}
        for name, (_, is_mut) in env.items():
            if is_mut and name not in param_names and _mentions(e.body, name):
                raise Diagnostic(
                    "E0130",
                    f"closure captures `mut` local `{name}`",
                    [Label(e.span, f"would alias `{name}` with its "
                           "enclosing scope")],
                    notes=["a captured `mut` variable would give the "
                           "closure and its enclosing scope two live "
                           "references to the same mutable slot"],
                    helps=[f"copy `{name}` into an immutable `let` "
                           "before forming the closure, if a snapshot "
                           "is what you want"])

    def join(self, x: Row, y: Row) -> Row:
        """Union two rows, reconciling open tails (see RFC 0001 §7)."""
        x, y = self.subst.resolve_row(x), self.subst.resolve_row(y)
        if x.tail is None or y.tail is None or x.tail == y.tail:
            return Row(x.labels | y.labels, x.tail or y.tail)
        fx, fy = Subst.is_flexible(x.tail), Subst.is_flexible(y.tail)
        if fx:
            self.subst.bind(x.tail, Row(frozenset(), y.tail))
            return self.subst.resolve_row(Row(x.labels | y.labels, y.tail))
        if fy:
            self.subst.bind(y.tail, Row(frozenset(), x.tail))
            return self.subst.resolve_row(Row(x.labels | y.labels, x.tail))
        raise Diagnostic(
            "E0205",
            f"cannot combine two distinct row variables `{x.tail}` "
            f"and `{y.tail}`",
            [Label(self.cur_fn.name_span if self.cur_fn else Span(0, 0),
                   "in this function")],
            notes=["NOVA supports one row variable per function; "
                   "see RFC 0001 §7"])

    @staticmethod
    def blame(expr):
        """Find the sub-expression actually responsible for a value."""
        while isinstance(expr, a.Block) and expr.tail is not None:
            expr = expr.tail
        return expr

    def expect_type(self, expr, actual: Type, expected: Type,
                    context: str) -> None:
        expr = self.blame(expr)
        try:
            ok = unify_types(actual, expected, self.subst)
        except RowMismatch as m:
            self.row_mismatch(expr, actual, expected, m, context)
            return
        if not ok:
            actual_r = self.subst.resolve_type(actual)
            expected_r = self.subst.resolve_type(expected)
            raise Diagnostic(
                "E0200", f"type mismatch in {context}",
                [Label(expr.span,
                       f"expected `{expected_r}`, found `{actual_r}`")])

    def row_mismatch(self, expr, actual: Type, expected: Type,
                     m: RowMismatch, context: str) -> None:
        actual_r = self.subst.resolve_type(actual)
        expected_r = self.subst.resolve_type(expected)
        hidden_set = _all_labels(actual_r) - _all_labels(expected_r)
        if isinstance(expr, a.Lambda) and hidden_set:
            hidden = sorted(hidden_set)
            captures = self.reach.captures.get(expr.node_id, {})
            labels = [Label(expr.span,
                            f"this closure has type `{actual_r}`")]
            notes = [f"expected `{expected_r}`",
                     f"passing it here would hide the "
                     f"{'effects' if len(hidden) > 1 else 'effect'} "
                     f"{', '.join('`' + h + '`' for h in hidden)} "
                     f"from callers"]
            if captures:
                notes.insert(0, "captures " + ", ".join(
                    f"`{n}: {c}`" for n, c in sorted(captures.items())))
            raise Diagnostic("E0203",
                             f"closure captures capability "
                             f"{', '.join('`' + h + '`' for h in hidden)} "
                             f"but its expected type does not declare it",
                             labels, notes=notes)
        raise Diagnostic(
            "E0206", f"effect mismatch in {context}",
            [Label(expr.span,
                   f"expected `{expected_r}`, found `{actual_r}`")],
            notes=[m.reason] if m.reason else [])


def _all_labels(t: Type) -> set[str]:
    """Every effect label anywhere in a type, at any arrow depth."""
    if isinstance(t, TFun):
        out = set(t.eff.labels)
        for p in t.params:
            out |= _all_labels(p)
        return out | _all_labels(t.ret)
    if isinstance(t, TTuple):
        out: set[str] = set()
        for x in t.elems:
            out |= _all_labels(x)
        return out
    if isinstance(t, (TStruct, TEnum)):
        out: set[str] = set()
        for x in t.args:
            out |= _all_labels(x)
        return out
    return set()


def check(prog: a.Program) -> CheckResult:
    return Checker(prog).check()
