"""AST for NOVA v0.2 (RFC 0001, RFC 0002, RFC 0003, RFC 0004, RFC 0005).

Every node carries a span (Architecture: "spans everywhere").
`node_id` gives closures a stable identity so the capability reachability
pass and the checker can talk about the same node.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from .diagnostics import Span

_ids = count()


@dataclass
class Node:
    span: Span
    node_id: int = field(default_factory=lambda: next(_ids), init=False,
                         repr=False, compare=False)


# ------------------------------------------------------- type syntax

@dataclass
class TypeExpr(Node):
    pass


@dataclass
class TName(TypeExpr):
    name: str
    args: list[TypeExpr] = field(default_factory=list)   # `List[Int]`


@dataclass
class TTupleExpr(TypeExpr):
    elems: list[TypeExpr]


@dataclass
class TFunExpr(TypeExpr):
    params: list[TypeExpr]
    ret: TypeExpr
    eff: "RowExpr | None"


@dataclass
class RowExpr(Node):
    labels: list[tuple[str, Span]]
    tail: str | None


# -------------------------------------------------------- expressions

@dataclass
class Expr(Node):
    pass


@dataclass
class IntLit(Expr):
    value: int


@dataclass
class StrLit(Expr):
    value: str


@dataclass
class BoolLit(Expr):
    value: bool


@dataclass
class UnitLit(Expr):
    pass


@dataclass
class Var(Expr):
    name: str


@dataclass
class Unary(Expr):
    op: str
    operand: Expr


@dataclass
class Binary(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class If(Expr):
    cond: Expr
    then: Expr
    els: Expr


@dataclass
class Call(Expr):
    callee: Expr
    args: list[Expr]


@dataclass
class MethodCall(Expr):
    """`recv.name(args)` — RFC 0002/0003: ONE syntax for both capability
    operations (RFC 0001's original `CapUse`, which introduces an effect)
    and trait method calls (which do not). The receiver's *type*, not the
    syntax, decides which rule applies (TYPE-SYSTEM.md "Method calls").
    """
    recv: Expr
    op: str
    op_span: Span
    args: list[Expr]


CapUse = MethodCall   # RFC 0001's name, kept as an alias for old callers.


@dataclass
class FieldAccess(Expr):
    """`recv.name` with no parentheses — a struct field or tuple
    position (`.0`, `.1`). Distinguished from `MethodCall` purely by the
    absence of `(...)`, exactly as in Rust; see SYNTAX.md."""
    recv: Expr
    field: str
    field_span: Span


@dataclass
class TupleLit(Expr):
    elems: list[Expr]


@dataclass
class StructLit(Expr):
    """`Name { field: expr, ... }`."""
    name: str
    name_span: Span
    fields: list[tuple[str, Expr]]


@dataclass
class EnumCtor(Expr):
    """`Name::Variant(args)` or a bare `Name::Variant` with no payload."""
    enum_name: str
    variant: str
    variant_span: Span
    args: list[Expr]


# ------------------------------------------------------------ patterns

@dataclass
class Pattern(Node):
    pass


@dataclass
class PWildcard(Pattern):
    pass


@dataclass
class PBind(Pattern):
    name: str


@dataclass
class PInt(Pattern):
    value: int


@dataclass
class PBool(Pattern):
    value: bool


@dataclass
class PString(Pattern):
    value: str


@dataclass
class PTuple(Pattern):
    elems: list[Pattern]


@dataclass
class PVariant(Pattern):
    """`Name::Variant(sub, sub, ...)` or `Name::Variant` with no payload."""
    enum_name: str
    variant: str
    variant_span: Span
    args: list[Pattern]


@dataclass
class MatchArm(Node):
    pattern: Pattern
    body: "Expr"


@dataclass
class Match(Expr):
    scrutinee: Expr
    arms: list[MatchArm]


@dataclass
class Lambda(Expr):
    params: list["Param"]
    body: Expr


@dataclass
class Let(Node):
    name: str
    name_span: Span
    ty: TypeExpr | None
    value: Expr
    mut: bool = False


@dataclass
class Assign(Expr):
    """`name = expr;` — rebinds a `let mut` local. RFC 0005: this is
    frame-local rebinding, never a reference; NOVA v0.2 has no reference
    or pointer type, so nothing can alias a local slot and this cannot
    violate Constitution Article XI. See RFC 0005 §2."""
    name: str
    name_span: Span
    value: Expr


@dataclass
class While(Expr):
    cond: Expr
    body: "Block"


@dataclass
class For(Expr):
    """`for x in iter { body }` over a `List[T]` (RFC 0005 §3). Desugars
    to a `while` in the reference evaluator; see eval.py."""
    var: str
    var_span: Span
    iter: Expr
    body: "Block"


@dataclass
class Block(Expr):
    stmts: list["Let | Expr"]
    tail: Expr | None


# ------------------------------------------------------- declarations

@dataclass
class Param(Node):
    name: str
    ty: TypeExpr


@dataclass
class OpSig(Node):
    name: str
    params: list[Param]
    ret: TypeExpr


@dataclass
class CapabilityDecl(Node):
    name: str
    name_span: Span
    ops: list[OpSig]


@dataclass
class TypeParam(Node):
    """`T` or `T: Trait` in a `[...]` binder list (RFC 0003 §1)."""
    name: str
    bound: str | None      # a trait name, or None if unbounded


@dataclass
class FnDecl(Node):
    name: str
    name_span: Span
    type_params: list[TypeParam]
    row_params: list[str]
    params: list[Param]
    ret: TypeExpr
    eff: RowExpr | None
    eff_span: Span | None
    widen: bool
    body: Block
    is_pub: bool = False
    is_method: bool = False      # first param is an implicit `self`


@dataclass
class StructField(Node):
    name: str
    ty: TypeExpr


@dataclass
class StructDecl(Node):
    """RFC 0002 §1: a nominal product type. Two structs with identical
    fields remain distinct types — see TYPE-SYSTEM.md, "Nominal vs
    structural"."""
    name: str
    name_span: Span
    type_params: list[TypeParam]
    fields: list[StructField]
    is_pub: bool = False


@dataclass
class VariantDecl(Node):
    """RFC 0002 §2: a tagged variant. `args` are positional field types;
    an empty list means a payload-free variant (`None`, `Nil`)."""
    name: str
    name_span: Span
    args: list[TypeExpr]


@dataclass
class EnumDecl(Node):
    name: str
    name_span: Span
    type_params: list[TypeParam]
    variants: list[VariantDecl]
    is_pub: bool = False


@dataclass
class TraitMethodSig(Node):
    """A required method inside a `trait` block. Signature only — RFC
    0003 §4 does not support default method bodies in v0.2."""
    name: str
    name_span: Span
    params: list[Param]     # excludes the implicit `self`
    ret: TypeExpr


@dataclass
class TraitDecl(Node):
    name: str
    name_span: Span
    methods: list[TraitMethodSig]
    is_pub: bool = False


@dataclass
class ImplDecl(Node):
    """`impl Trait for Type { fn method(self, ...) { ... } }`.
    `type_params` are the impl's own fresh generics (RFC 0003 §4), e.g.
    `impl[T] Show for Option[T]`."""
    trait_name: str
    trait_name_span: Span
    type_params: list[TypeParam]
    target: TypeExpr
    methods: list[FnDecl]


@dataclass
class ImportDecl(Node):
    """`import a.b.c;` — RFC 0004. Brings every `pub` item of module
    `a.b.c` into scope, qualified by its last path segment (`c.name`)."""
    path: list[str]
    path_span: Span


Decl = (CapabilityDecl | FnDecl | StructDecl | EnumDecl | TraitDecl
        | ImplDecl | ImportDecl)


@dataclass
class Module(Node):
    """One `.nova` file. `path` is its dotted module name, derived from
    its filesystem path relative to the program's root (RFC 0004 §1)."""
    path: str
    decls: list[Decl]


@dataclass
class Program(Node):
    """RFC 0004: a program is now a set of modules, not a flat decl list.
    `decls` is kept as a computed, flattened convenience view so every
    existing single-file pass (RFC 0001's checker) keeps working
    unmodified; only `driver.py`'s loader and diagnostics that need a
    module *name* look at `modules` directly."""
    modules: list[Module]

    @property
    def decls(self) -> list[Decl]:
        return [d for m in self.modules for d in m.decls]
