"""NOVA Static Code Linter (`nova lint`).

Linter passes:
- Style & Naming conventions (PascalCase structs/traits/enums, snake_case functions)
- Dead code and unused variable detection
- Redundant pure expressions
- Explicit capability audit checks
"""
from __future__ import annotations

import dataclasses
import os
import re
from dataclasses import dataclass
from typing import Optional

from verifier.refspec import ast as a
from verifier.refspec.check import CheckResult
from verifier.refspec.driver import CompilationUnit
from .driver import NovaCompiler


@dataclass
class LintWarning:
    file: str
    line: int
    column: int
    rule: str
    message: str
    suggestion: Optional[str] = None


def _children(node: a.Node):
    for f in dataclasses.fields(node):
        v = getattr(node, f.name)
        if isinstance(v, a.Node):
            yield v
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, a.Node):
                    yield item
                elif isinstance(item, tuple):
                    for part in item:
                        if isinstance(part, a.Node):
                            yield part


def _pattern_names(p: a.Pattern) -> list[str]:
    if isinstance(p, a.PBind):
        return [p.name]
    if isinstance(p, (a.PTuple, a.PVariant)):
        return [n for sub in (p.elems if isinstance(p, a.PTuple) else p.args)
                for n in _pattern_names(sub)]
    return []


def unused_lets(program: a.Program) -> list[tuple[a.Let, bool]]:
    """Every `let` whose name is never read afterwards, paired with whether
    it was at least assigned to. Names starting with `_` are skipped.

    Scoping follows the checker (check.py, `Block`): a block opens a scope,
    a later `let` of the same name shadows the earlier one, and closure /
    match / `for` binders shadow too but are not `let`s so are never
    reported. A read in a closure body counts for the enclosing binding.
    """
    found: list[tuple[a.Let, bool]] = []

    # scope: name -> [Let, read, assigned], or None for a non-let binder
    def bind(scopes, name, let):
        prev = scopes[-1].get(name)
        if prev is not None:
            close({name: prev})
        scopes[-1][name] = [let, False, False]

    def use(scopes, name, read):
        for scope in reversed(scopes):
            if name in scope:
                entry = scope[name]
                if entry is not None:
                    entry[1 if read else 2] = True
                return

    def close(scope):
        for name, entry in scope.items():
            if entry is not None and not entry[1] and not name.startswith("_"):
                found.append((entry[0], entry[2]))

    def visit(e, scopes):
        if isinstance(e, a.Block):
            scopes.append({})
            for st in e.stmts:
                if isinstance(st, a.Let):
                    visit(st.value, scopes)
                    bind(scopes, st.name, st)
                else:
                    visit(st, scopes)
            if e.tail is not None:
                visit(e.tail, scopes)
            close(scopes.pop())
        elif isinstance(e, a.Var):
            use(scopes, e.name, read=True)
        elif isinstance(e, a.Assign):
            visit(e.value, scopes)
            use(scopes, e.name, read=False)
        elif isinstance(e, a.Lambda):
            scopes.append({p.name: None for p in e.params})
            visit(e.body, scopes)
            scopes.pop()
        elif isinstance(e, a.For):
            visit(e.iter, scopes)
            scopes.append({e.var: None})
            visit(e.body, scopes)
            scopes.pop()
        elif isinstance(e, a.Match):
            visit(e.scrutinee, scopes)
            for arm in e.arms:
                scopes.append({n: None for n in _pattern_names(arm.pattern)})
                visit(arm.body, scopes)
                scopes.pop()
        else:
            for child in _children(e):
                visit(child, scopes)

    fns = []
    for d in program.decls:
        if isinstance(d, a.FnDecl):
            fns.append(d)
        elif isinstance(d, a.ImplDecl):
            fns.extend(d.methods)
    for fn in fns:
        visit(fn.body, [{p.name: None for p in fn.params}])
    return found


def _unused_let_warnings(unit: CompilationUnit, path: str) -> list[LintWarning]:
    warnings = []
    for let, assigned in unused_lets(unit.program):
        src, base = unit.sources.lookup(let.name_span.start)
        if src.name != path:
            continue        # the prelude is not ours to lint
        line, col = src.line_col(let.name_span.start - base)
        what = "assigned to but never read" if assigned else "never used"
        warnings.append(LintWarning(
            file=path, line=line, column=col, rule="W0201",
            message=f"Local `{let.name}` is {what}",
            suggestion=f"Remove the binding, or name it `_{let.name}` if this is deliberate"))
    return warnings


def lint_file(path: str) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    if not os.path.exists(path):
        return [LintWarning(path, 1, 1, "E999", f"File not found: {path}")]

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    compiler = NovaCompiler()
    unit, err = compiler.check_file(path)

    # 1. Source-level syntax and naming checks
    for idx, line in enumerate(lines, 1):
        # Line length check
        if len(line) > 120 and not line.strip().startswith("//"):
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=120,
                rule="L001",
                message="Line exceeds 120 characters",
                suggestion="Wrap line across multiple lines"
            ))

        # Function naming check (should be snake_case)
        fn_match = re.match(r'^\s*fn\s+([A-Z][a-zA-Z0-9_]*)\s*\(', line)
        if fn_match:
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=fn_match.start(1) + 1,
                rule="L002",
                message=f"Function name '{fn_match.group(1)}' should be snake_case",
                suggestion=f"Rename to '{fn_match.group(1).lower()}'"
            ))

        # Struct/Enum naming check (should be PascalCase)
        type_match = re.match(r'^\s*(?:struct|enum|trait)\s+([a-z][a-zA-Z0-9_]*)\s*', line)
        if type_match:
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=type_match.start(1) + 1,
                rule="L003",
                message=f"Type '{type_match.group(1)}' should be PascalCase",
                suggestion=f"Capitalize to '{type_match.group(1).capitalize()}'"
            ))

        # Check for trailing whitespace
        if line.rstrip("\n").endswith(" ") or line.rstrip("\n").endswith("\t"):
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=len(line.rstrip("\n")),
                rule="L004",
                message="Trailing whitespace detected",
                suggestion="Remove trailing spaces"
            ))

    # 2. Semantic AST checks
    if unit and unit.result:
        # Check for widened signatures that could be tighter
        if unit.result.widened:
            for fn_name, span in unit.result.widened:
                warnings.append(LintWarning(
                    file=path,
                    line=1,
                    column=1,
                    rule="L010",
                    message=f"Function '{fn_name}' uses effect widening (`= widen`)",
                    suggestion="Verify if a tighter effect row can be used"
                ))
        warnings.extend(_unused_let_warnings(unit, path))

    return warnings
