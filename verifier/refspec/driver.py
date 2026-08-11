"""Front-end driver: source map, prelude loading, module resolution
(RFC 0004), and the public API."""
from __future__ import annotations

import os
from dataclasses import dataclass

from . import ast as a
from .check import CheckResult, check
from .diagnostics import Diagnostic, Label, Source, Span
from .eval import Interpreter, Unit  # noqa: F401  (re-exported)
from .parser import parse_module

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
PRELUDE_PATH = os.path.join(_REPO_ROOT, "std", "prelude.nova")
STD_DIR = os.path.join(_REPO_ROOT, "std")


class SourceMap:
    """Several files sharing one span space, so a diagnostic can point at any.

    Each file is given a disjoint range of offsets by the lexer's `base`
    argument, so no span rewriting is ever needed.
    """

    def __init__(self) -> None:
        self._files: list[tuple[int, Source]] = []
        self._next = 0

    def add(self, text: str, name: str) -> int:
        base = self._next
        self._files.append((base, Source(text, name)))
        self._next += len(text) + 1
        return base

    def lookup(self, offset: int) -> tuple[Source, int]:
        best = self._files[0]
        for entry in self._files:
            if entry[0] <= offset:
                best = entry
        return best[1], best[0]

    def render(self, d: Diagnostic) -> str:
        """Render a diagnostic whose labels may span several files.

        Each label is resolved against its *own* file; rebasing them all
        against the first label's file produces nonsense offsets when a
        diagnostic points at both the prelude and user code.
        """
        out = [f"error[{d.code}]: {d.title}"]
        for lab in d.labels:
            src, base = self.lookup(lab.span.start)
            out += src.label_lines(
                Label(Span(lab.span.start - base, lab.span.end - base),
                      lab.message, lab.primary))
        out += [f"  = note: {n}" for n in d.notes]
        out += [f"  = help: {h}" for h in d.helps]
        return "\n".join(out)


@dataclass
class CompilationUnit:
    program: a.Program
    result: CheckResult
    sources: SourceMap


def _find_module_file(path: list[str], roots: list[str]) -> str | None:
    rel = os.path.join(*path) + ".nova"
    for root in roots:
        candidate = os.path.join(root, rel)
        if os.path.isfile(candidate):
            return candidate
    return None


def compile_source(text: str, name: str = "<input>",
                   with_prelude: bool = True,
                   import_roots: list[str] | None = None) -> CompilationUnit:
    """Lex, parse and check `text`, resolving any `import` declarations
    (RFC 0004) transitively against `import_roots`.

    `import_roots` defaults to `[std/]`, plus the directory containing
    `name` when `name` is a real file on disk — so examples can import
    sibling files by their on-disk layout, and every program can
    `import std.<name>`.

    Raises `Diagnostic` on failure, with a `.sources` attribute attached so
    the caller can render it against the right file.
    """
    # The repository root is a search root, not std/ itself, so that
    # `import std.list;` reads naturally as "the `list` module inside
    # the `std` namespace" rather than colliding with STD_DIR's own name.
    roots = list(import_roots) if import_roots else [_REPO_ROOT]
    if os.path.isfile(name):
        d = os.path.dirname(os.path.abspath(name))
        if d not in roots:
            roots = [d] + roots

    sm = SourceMap()
    modules: list[a.Module] = []
    try:
        if with_prelude:
            with open(PRELUDE_PATH, "r", encoding="utf-8") as fh:
                prelude_text = fh.read()
            modules.append(parse_module(
                prelude_text, sm.add(prelude_text, "std/prelude.nova"),
                "std.prelude"))

        main_mod = parse_module(text, sm.add(text, name), "main")
        modules.append(main_mod)

        seen = {"main", "std.prelude"}
        queue: list[tuple[list[str], Span]] = [
            (d.path, d.path_span) for d in main_mod.decls
            if isinstance(d, a.ImportDecl)]
        while queue:
            path, span = queue.pop(0)
            dotted = ".".join(path)
            if dotted in seen:
                continue
            seen.add(dotted)
            file_path = _find_module_file(path, roots)
            if file_path is None:
                raise Diagnostic(
                    "E0125", f"cannot find module `{dotted}`",
                    [Label(span, "no matching file")],
                    notes=[f"looked under: {', '.join(roots)}"])
            with open(file_path, "r", encoding="utf-8") as fh:
                mod_text = fh.read()
            mod = parse_module(mod_text, sm.add(mod_text, file_path), dotted)
            modules.append(mod)
            queue += [(d.path, d.path_span) for d in mod.decls
                     if isinstance(d, a.ImportDecl)]

        prog = a.Program(main_mod.span, modules)
        return CompilationUnit(prog, check(prog), sm)
    except Diagnostic as d:
        d.sources = sm
        raise


def check_source(text: str, name: str = "<input>") -> CompilationUnit:
    return compile_source(text, name)


def run_source(text: str, name: str = "<input>"):
    """Check then evaluate `main`. Returns (value, stdout_lines)."""
    unit = compile_source(text, name)
    interp = Interpreter(unit.result)
    return interp.run_main(), interp.out
