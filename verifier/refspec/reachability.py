"""Capability reachability (RFC 0001 §4.3, Architecture §"Why ... its own pass").

Computes, for every function and every closure, the set of capability-typed
values reachable from its body through parameters and closure captures.

This pass is *conservative and advisory*. The typing rules in `check.py`
are authoritative for effect rows; this pass exists because:

  - its output is what an audit tool needs ("which code can touch the
    network?"), independent of whether the program typechecks;
  - it produces the capture information that makes diagnostic E0203
    readable;
  - it runs before unification, so it still works on programs the checker
    rejects.

It tracks capability-typed bindings syntactically: annotated parameters,
annotated `let`s, and direct aliases (`let d = c;`). A capability obtained
from a call (`let c = rt.clock();`) is *not* tracked here — the checker
sees it through types. Under-approximation here is safe because this pass
never grants permission; it only explains.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import ast as a


@dataclass
class Reach:
    """Result of the pass."""
    # node_id of a Lambda -> {var name: capability type name} it captures
    captures: dict[int, dict[str, str]] = field(default_factory=dict)
    # function name -> capability type names syntactically reachable
    fn_caps: dict[str, set[str]] = field(default_factory=dict)
    # spans of capability-typed bindings, for diagnostics
    binding_spans: dict[int, dict[str, object]] = field(default_factory=dict)


def _cap_name(t: a.TypeExpr | None, caps: set[str]) -> str | None:
    if isinstance(t, a.TName) and t.name in caps:
        return t.name
    return None


def analyze(prog: a.Program) -> Reach:
    caps = {d.name for d in prog.decls if isinstance(d, a.CapabilityDecl)}
    r = Reach()

    def do_fn(d: a.FnDecl, key: str) -> None:
        env: dict[str, str] = {}
        spans: dict[str, object] = {}
        for p in d.params:
            c = _cap_name(p.ty, caps)
            if c:
                env[p.name] = c
                spans[p.name] = p.span
        r.binding_spans[d.node_id] = spans
        r.fn_caps[key] = _walk(d.body, env, caps, r)

    for d in prog.decls:
        if isinstance(d, a.FnDecl):
            do_fn(d, d.name)
        elif isinstance(d, a.ImplDecl):
            for m in d.methods:
                do_fn(m, f"{d.trait_name}::{m.name}")
    return r


def _walk(e, env: dict[str, str], caps: set[str], r: Reach) -> set[str]:
    """Return the capability names used by `e` under `env`."""
    used: set[str] = set()

    if isinstance(e, a.Var):
        if e.name in env:
            used.add(env[e.name])
        return used

    if isinstance(e, (a.IntLit, a.StrLit, a.BoolLit, a.UnitLit)):
        return used

    if isinstance(e, a.Unary):
        return _walk(e.operand, env, caps, r)

    if isinstance(e, a.Binary):
        return _walk(e.left, env, caps, r) | _walk(e.right, env, caps, r)

    if isinstance(e, a.If):
        return (_walk(e.cond, env, caps, r) | _walk(e.then, env, caps, r)
                | _walk(e.els, env, caps, r))

    if isinstance(e, a.Call):
        used |= _walk(e.callee, env, caps, r)
        for arg in e.args:
            used |= _walk(arg, env, caps, r)
        return used

    if isinstance(e, a.MethodCall):
        used |= _walk(e.recv, env, caps, r)
        for arg in e.args:
            used |= _walk(arg, env, caps, r)
        return used

    if isinstance(e, a.FieldAccess):
        # RFC 0002 §3: a struct field can itself be a capability. This
        # syntactic pass does not track *which* field of a struct holds
        # what (it only tracks whole-variable bindings) — so a field
        # projection is treated as "unknown," contributing nothing here.
        # This is a sound under-approximation (the pass's stated
        # contract): the checker still sees the field's true type via
        # ordinary structural lookup and enforces the row correctly even
        # where this advisory pass says less than it could.
        return _walk(e.recv, env, caps, r)

    if isinstance(e, a.TupleLit):
        for x in e.elems:
            used |= _walk(x, env, caps, r)
        return used

    if isinstance(e, a.StructLit):
        for _, fv in e.fields:
            used |= _walk(fv, env, caps, r)
        return used

    if isinstance(e, a.EnumCtor):
        for x in e.args:
            used |= _walk(x, env, caps, r)
        return used

    if isinstance(e, a.Match):
        used |= _walk(e.scrutinee, env, caps, r)
        for arm in e.arms:
            inner = dict(env)
            _bind_pattern(arm.pattern, inner)
            used |= _walk(arm.body, inner, caps, r)
        return used

    if isinstance(e, a.Assign):
        return _walk(e.value, env, caps, r)

    if isinstance(e, a.While):
        return _walk(e.cond, env, caps, r) | _walk(e.body, env, caps, r)

    if isinstance(e, a.For):
        inner = dict(env)
        inner.pop(e.var, None)
        return _walk(e.iter, env, caps, r) | _walk(e.body, inner, caps, r)

    if isinstance(e, a.Lambda):
        inner = dict(env)
        for p in e.params:
            c = _cap_name(p.ty, caps)
            inner.pop(p.name, None)      # shadowing removes the outer binding
            if c:
                inner[p.name] = c
        body_used = _walk(e.body, inner, caps, r)
        # A capture is a capability the lambda uses that came from *outside*.
        param_names = {p.name for p in e.params}
        r.captures[e.node_id] = {
            name: cap for name, cap in env.items()
            if name not in param_names and cap in body_used
            and _mentions(e.body, name)
        }
        return body_used

    if isinstance(e, a.Block):
        inner = dict(env)
        for st in e.stmts:
            if isinstance(st, a.Let):
                used |= _walk(st.value, inner, caps, r)
                c = _cap_name(st.ty, caps)
                if c is None and isinstance(st.value, a.Var):
                    c = inner.get(st.value.name)      # direct alias
                inner.pop(st.name, None)
                if c:
                    inner[st.name] = c
            else:
                used |= _walk(st, inner, caps, r)
        if e.tail is not None:
            used |= _walk(e.tail, inner, caps, r)
        return used

    raise AssertionError(f"unhandled node in reachability: {type(e).__name__}")


def _mentions(e, name: str) -> bool:
    """Does `name` occur free in `e`? Used to keep captures precise."""
    if isinstance(e, a.Var):
        return e.name == name
    if isinstance(e, (a.IntLit, a.StrLit, a.BoolLit, a.UnitLit)):
        return False
    if isinstance(e, a.Unary):
        return _mentions(e.operand, name)
    if isinstance(e, a.Binary):
        return _mentions(e.left, name) or _mentions(e.right, name)
    if isinstance(e, a.If):
        return any(_mentions(x, name) for x in (e.cond, e.then, e.els))
    if isinstance(e, a.Call):
        return _mentions(e.callee, name) or any(
            _mentions(x, name) for x in e.args)
    if isinstance(e, a.MethodCall):
        return _mentions(e.recv, name) or any(
            _mentions(x, name) for x in e.args)
    if isinstance(e, a.FieldAccess):
        return _mentions(e.recv, name)
    if isinstance(e, a.TupleLit):
        return any(_mentions(x, name) for x in e.elems)
    if isinstance(e, a.StructLit):
        return any(_mentions(fv, name) for _, fv in e.fields)
    if isinstance(e, a.EnumCtor):
        return any(_mentions(x, name) for x in e.args)
    if isinstance(e, a.Match):
        if _mentions(e.scrutinee, name):
            return True
        return any(_mentions(arm.body, name) for arm in e.arms
                   if not _pattern_binds(arm.pattern, name))
    if isinstance(e, a.Assign):
        return e.name == name or _mentions(e.value, name)
    if isinstance(e, a.While):
        return _mentions(e.cond, name) or _mentions(e.body, name)
    if isinstance(e, a.For):
        if e.var == name:
            return _mentions(e.iter, name)
        return _mentions(e.iter, name) or _mentions(e.body, name)
    if isinstance(e, a.Lambda):
        if any(p.name == name for p in e.params):
            return False
        return _mentions(e.body, name)
    if isinstance(e, a.Block):
        for st in e.stmts:
            if isinstance(st, a.Let):
                if _mentions(st.value, name):
                    return True
                if st.name == name:
                    return False
            elif _mentions(st, name):
                return True
        return e.tail is not None and _mentions(e.tail, name)
    raise AssertionError(f"unhandled node in _mentions: {type(e).__name__}")


def _bind_pattern(p: a.Pattern, env: dict[str, str]) -> None:
    """Remove pattern-bound names from `env` (they shadow), mirroring how
    lambda parameters already shadow in `_walk`. Patterns cannot bind a
    capability-typed name to a *different* capability, so nothing needs
    to be added, only removed."""
    if isinstance(p, a.PBind):
        env.pop(p.name, None)
    elif isinstance(p, a.PTuple):
        for sub in p.elems:
            _bind_pattern(sub, env)
    elif isinstance(p, a.PVariant):
        for sub in p.args:
            _bind_pattern(sub, env)


def _pattern_binds(p: a.Pattern, name: str) -> bool:
    if isinstance(p, a.PBind):
        return p.name == name
    if isinstance(p, a.PTuple):
        return any(_pattern_binds(sub, name) for sub in p.elems)
    if isinstance(p, a.PVariant):
        return any(_pattern_binds(sub, name) for sub in p.args)
    return False
