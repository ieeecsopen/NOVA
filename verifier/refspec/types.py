"""Types and effect rows for NOVA v0.2 (RFC 0001 §4.2, RFC 0002, RFC 0003).

An effect row is a set of capability type names, optionally open with a
row variable tail:

    {}                 pure
    {Net, Clock}       closed
    {Net | r}          open

Row variables are either *rigid* (universally quantified by an enclosing
`fn f[r](..)`) or *flexible* (created by instantiation at a call site and
solvable by unification). Binding a rigid variable is an error; that is
what makes a declared row a promise rather than a hint.

RFC 0003 adds the same rigid/flexible distinction for ordinary *type*
variables (`TVar`), so that generic functions are checked the same way
row-polymorphic ones already were: a declared type parameter is rigid
inside the function that declares it, and is instantiated to a fresh
flexible variable at each call site, solved by the same substitution
object (renamed `Subst`, doing double duty for rows and types).
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------- rows

@dataclass(frozen=True)
class Row:
    labels: frozenset[str]
    tail: str | None = None      # row-variable name, or None if closed

    @staticmethod
    def pure() -> "Row":
        return Row(frozenset())

    @staticmethod
    def of(*labels: str) -> "Row":
        return Row(frozenset(labels))

    def is_pure(self) -> bool:
        return not self.labels and self.tail is None

    def union(self, other: "Row") -> "Row":
        if self.tail and other.tail and self.tail != other.tail:
            # Two distinct open tails cannot be joined without a fresh
            # variable; the checker always resolves tails before union,
            # so reaching here is an internal error.
            raise AssertionError("union of two distinct open rows")
        return Row(self.labels | other.labels, self.tail or other.tail)

    def __str__(self) -> str:
        inner = ", ".join(sorted(self.labels))
        if self.tail:
            return "{" + (inner + " | " if inner else "| ") + self.tail + "}"
        return "{" + inner + "}"


# --------------------------------------------------------------- types

class Type:
    pass


@dataclass(frozen=True)
class TCon(Type):
    """Built-in ground type: Int, Bool, String, Unit."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class TCap(Type):
    """A capability type. Its name is also its effect label (RFC 0001 §4.1)."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class TFun(Type):
    params: tuple[Type, ...]
    ret: Type
    eff: Row

    def __str__(self) -> str:
        ps = ", ".join(str(p) for p in self.params)
        suffix = "" if self.eff.is_pure() else f" ! {self.eff}"
        return f"({ps}) -> {_paren(self.ret)}{suffix}"


@dataclass(frozen=True)
class TVar(Type):
    """A type variable (RFC 0003). Rigid if bound by an enclosing `[T]`
    binder; flexible (its name starts with `?T`) if fresh, created at
    instantiation and solved by unification — the exact counterpart of a
    row variable, reusing the same rigid/flexible discipline."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class TTuple(Type):
    """The one *structural* type in NOVA (RFC 0002 §2): two tuples with
    the same element types are the same type, with no declaration
    needed. Structs and enums are nominal (RFC 0002 §1); tuples are the
    deliberate, sole exception, precisely because they need no identity
    beyond their shape — see TYPE-SYSTEM.md "Nominal vs structural"."""
    elems: tuple[Type, ...]

    def __str__(self) -> str:
        if len(self.elems) == 1:
            return f"({self.elems[0]},)"
        return "(" + ", ".join(str(e) for e in self.elems) + ")"


@dataclass(frozen=True)
class TStruct(Type):
    """A nominal struct type, with its type arguments already substituted
    in (RFC 0002 §1, RFC 0003 §2). Field types are looked up by name in
    `CheckResult.structs`, not stored here, so a generic struct's fields
    are computed once, at the declaration, and specialized on demand."""
    name: str
    args: tuple[Type, ...] = ()

    def __str__(self) -> str:
        if not self.args:
            return self.name
        return f"{self.name}[{', '.join(str(a) for a in self.args)}]"


@dataclass(frozen=True)
class TEnum(Type):
    """A nominal enum (tagged union) type; see `TStruct` for why type
    arguments are carried here but variant field types are not."""
    name: str
    args: tuple[Type, ...] = ()

    def __str__(self) -> str:
        if not self.args:
            return self.name
        return f"{self.name}[{', '.join(str(a) for a in self.args)}]"


def _paren(t: "Type") -> str:
    """Parenthesize an arrow in *return* position.

    `() -> (() -> Int) ! {Clock}` and `() -> (() -> Int ! {Clock})` are
    different types; without parentheses they print identically. Parameter
    positions are already delimited by commas, so they need no parentheses.
    """
    return f"({t})" if isinstance(t, TFun) else str(t)


INT = TCon("Int")
BOOL = TCon("Bool")
STRING = TCon("String")
UNIT = TCon("Unit")
GROUND = {"Int": INT, "Bool": BOOL, "String": STRING, "Unit": UNIT}


# --------------------------------------------------------- substitution

class Subst:
    """Solution set for flexible row variables *and* flexible type
    variables (RFC 0003). One object, two independent maps: a row
    variable and a type variable never collide (their fresh names use
    disjoint prefixes, `?` vs `?T`), and nothing about solving one kind
    depends on the other, but a single generic, row-polymorphic function
    needs both solved together against one set of call-site arguments,
    so one object is simpler than threading two."""

    def __init__(self) -> None:
        self._rows: dict[str, Row] = {}
        self._types: dict[str, "Type"] = {}
        self._counter = 0

    def fresh(self) -> str:
        self._counter += 1
        return f"?{self._counter}"

    def fresh_type(self) -> str:
        self._counter += 1
        return f"?T{self._counter}"

    @staticmethod
    def is_flexible(var: str) -> bool:
        return var.startswith("?")

    def resolve_row(self, r: Row) -> Row:
        """Follow tail bindings until the tail is unbound or rigid."""
        labels, tail = r.labels, r.tail
        seen: set[str] = set()
        while tail is not None and tail in self._rows:
            if tail in seen:
                raise AssertionError("cyclic row substitution")
            seen.add(tail)
            nxt = self._rows[tail]
            labels = labels | nxt.labels
            tail = nxt.tail
        return Row(labels, tail)

    def resolve_type(self, t: Type) -> Type:
        if isinstance(t, TVar):
            seen: set[str] = set()
            while isinstance(t, TVar) and t.name in self._types:
                if t.name in seen:
                    raise AssertionError("cyclic type substitution")
                seen.add(t.name)
                t = self._types[t.name]
            if isinstance(t, TVar):
                return t
            return self.resolve_type(t)
        if isinstance(t, TFun):
            return TFun(tuple(self.resolve_type(p) for p in t.params),
                        self.resolve_type(t.ret),
                        self.resolve_row(t.eff))
        if isinstance(t, TTuple):
            return TTuple(tuple(self.resolve_type(e) for e in t.elems))
        if isinstance(t, TStruct):
            return TStruct(t.name, tuple(self.resolve_type(a) for a in t.args))
        if isinstance(t, TEnum):
            return TEnum(t.name, tuple(self.resolve_type(a) for a in t.args))
        return t

    def bind(self, var: str, row: Row) -> None:
        assert self.is_flexible(var), "cannot bind a rigid row variable"
        self._rows[var] = row

    def bind_type(self, var: str, ty: "Type") -> None:
        assert self.is_flexible(var), "cannot bind a rigid type variable"
        self._types[var] = ty


# Kept as an alias: every existing caller (check.py, the experiments)
# was written against the row-only name before RFC 0003 generalized it.
RowSubst = Subst


class RowMismatch(Exception):
    def __init__(self, left: Row, right: Row, reason: str = "") -> None:
        self.left, self.right, self.reason = left, right, reason


class TypeMismatch(Exception):
    def __init__(self, left: "Type", right: "Type", reason: str = "") -> None:
        self.left, self.right, self.reason = left, right, reason


def occurs(var: str, t: "Type", s: "Subst") -> bool:
    t = s.resolve_type(t)
    if isinstance(t, TVar):
        return t.name == var
    if isinstance(t, TFun):
        return (any(occurs(var, p, s) for p in t.params)
                or occurs(var, t.ret, s))
    if isinstance(t, TTuple):
        return any(occurs(var, e, s) for e in t.elems)
    if isinstance(t, (TStruct, TEnum)):
        return any(occurs(var, a, s) for a in t.args)
    return False


def unify_rows(a: Row, b: Row, s: RowSubst) -> None:
    """Unify two effect rows under `s`, or raise RowMismatch.

    Rigid tails behave like ordinary labels: they must match exactly.
    """
    a, b = s.resolve_row(a), s.resolve_row(b)

    if a.tail is None and b.tail is None:
        if a.labels != b.labels:
            raise RowMismatch(a, b)
        return

    # One side closed, one open.
    if a.tail is None or b.tail is None:
        closed, open_ = (a, b) if a.tail is None else (b, a)
        if not s.is_flexible(open_.tail):
            raise RowMismatch(a, b, f"row variable `{open_.tail}` is rigid")
        if not open_.labels <= closed.labels:
            raise RowMismatch(a, b)
        s.bind(open_.tail, Row(closed.labels - open_.labels))
        return

    # Both open.
    if a.tail == b.tail:
        if a.labels != b.labels:
            raise RowMismatch(a, b)
        return
    if not s.is_flexible(a.tail) and not s.is_flexible(b.tail):
        raise RowMismatch(a, b, "two distinct rigid row variables")
    rest = s.fresh()
    if s.is_flexible(a.tail):
        s.bind(a.tail, Row(b.labels - a.labels, rest))
    if s.is_flexible(b.tail):
        s.bind(b.tail, Row(a.labels - b.labels, rest))
    return


def unify_types(a: Type, b: Type, s: Subst) -> bool:
    """Unify two types under `s`.

    Flexible type variables (RFC 0003) are bound, exactly as flexible row
    variables already were; rigid ones must match a structurally equal
    type, or another occurrence of the *same* rigid variable — never a
    different type, which is what makes a declared type parameter a
    promise rather than a hint, the same discipline RFC 0001 already
    applies to declared effect rows. Raises `RowMismatch` if an effect
    row inside a function type disagrees; returns False (never raises)
    for an ordinary type mismatch, so callers can produce their own
    diagnostic with full context.
    """
    a, b = s.resolve_type(a), s.resolve_type(b)

    if isinstance(a, TVar) and isinstance(b, TVar) and a.name == b.name:
        return True
    # A flexible variable binds to *whatever* the other side is — rigid,
    # concrete, or another flexible variable — regardless of which
    # position it appears in. This must be checked before either side is
    # assumed to be rigid, or a rigid type parameter meeting a fresh
    # flexible one (e.g. a generic `List::Cons(x, xs)` inside a generic
    # `prepend[T]`, where both happen to be named `T`) is wrongly
    # rejected as a mismatch instead of being solved.
    if isinstance(a, TVar) and s.is_flexible(a.name):
        if occurs(a.name, b, s):
            return False
        s.bind_type(a.name, b)
        return True
    if isinstance(b, TVar) and s.is_flexible(b.name):
        if occurs(b.name, a, s):
            return False
        s.bind_type(b.name, a)
        return True
    if isinstance(a, TVar) or isinstance(b, TVar):
        return False   # both rigid (or rigid vs. a concrete type) and unequal

    if isinstance(a, TFun) and isinstance(b, TFun):
        if len(a.params) != len(b.params):
            return False
        for pa, pb in zip(a.params, b.params):
            if not unify_types(pa, pb, s):
                return False
        if not unify_types(a.ret, b.ret, s):
            return False
        unify_rows(a.eff, b.eff, s)   # may raise RowMismatch
        return True

    if isinstance(a, TTuple) and isinstance(b, TTuple):
        if len(a.elems) != len(b.elems):
            return False
        return all(unify_types(x, y, s) for x, y in zip(a.elems, b.elems))

    if isinstance(a, (TStruct, TEnum)) and isinstance(b, (TStruct, TEnum)):
        if type(a) is not type(b) or a.name != b.name:
            return False
        if len(a.args) != len(b.args):
            return False
        return all(unify_types(x, y, s) for x, y in zip(a.args, b.args))

    return a == b


def instantiate(t: Type, rigid: set[str], s: Subst,
                mapping: dict[str, str] | None = None) -> Type:
    """Replace the given rigid row *and* type variables with fresh
    flexible ones — RFC 0003's generic instantiation, unifying with RFC
    0001's row instantiation under one traversal so a function that is
    both generic and row-polymorphic (e.g. `with_retry[T, r]`) is
    instantiated in one pass."""
    if mapping is None:
        mapping = {}

    def go_row(r: Row) -> Row:
        if r.tail in rigid:
            mapping.setdefault(r.tail, s.fresh())
            return Row(r.labels, mapping[r.tail])
        return r

    def go(x: Type) -> Type:
        if isinstance(x, TVar):
            if x.name in rigid:
                mapping.setdefault(x.name, s.fresh_type())
                return TVar(mapping[x.name])
            return x
        if isinstance(x, TFun):
            return TFun(tuple(go(p) for p in x.params), go(x.ret),
                        go_row(x.eff))
        if isinstance(x, TTuple):
            return TTuple(tuple(go(e) for e in x.elems))
        if isinstance(x, TStruct):
            return TStruct(x.name, tuple(go(a) for a in x.args))
        if isinstance(x, TEnum):
            return TEnum(x.name, tuple(go(a) for a in x.args))
        return x

    return go(t)


def substitute(t: Type, mapping: dict[str, Type]) -> Type:
    """Replace type variables by name per `mapping`, with no freshening —
    used to specialize a generic struct/enum/trait-impl's declared field
    or method types once concrete type arguments are known (RFC 0003 §2),
    as opposed to `instantiate`, which freshens for unification."""
    def go(x: Type) -> Type:
        if isinstance(x, TVar):
            return mapping.get(x.name, x)
        if isinstance(x, TFun):
            return TFun(tuple(go(p) for p in x.params), go(x.ret), x.eff)
        if isinstance(x, TTuple):
            return TTuple(tuple(go(e) for e in x.elems))
        if isinstance(x, TStruct):
            return TStruct(x.name, tuple(go(a) for a in x.args))
        if isinstance(x, TEnum):
            return TEnum(x.name, tuple(go(a) for a in x.args))
        return x
    return go(t)
