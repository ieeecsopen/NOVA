#!/usr/bin/env python3
"""Tests for the developer tools in compiler/nova_compiler/ (`nova fmt`,
`nova lint`, `nova add`) and for diagnostic rendering.

None of this is language conformance -- tests/run_conformance.py stays
the arbiter for that. A failure here is a bug in a tool, not in the
language. Each `test_*` function is one case and raises to fail.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from compiler.nova_compiler.fmt import format_code                   # noqa: E402
from compiler.nova_compiler.lint import lint_file                    # noqa: E402
from compiler.nova_compiler.pkg import add_dependency, is_semver     # noqa: E402
from verifier.refspec.diagnostics import Diagnostic, Label, Source, Span  # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")


# ---------------------------------------------------------- diagnostics

def _render(text: str, start: int, end: int) -> tuple[str, str]:
    """The (source, caret) line pair of a one-label diagnostic on `text`."""
    src = Source(text, "t.nova")
    d = Diagnostic("E0000", "t", [Label(Span(start, end), "here")])
    lines = src.render(d).splitlines()
    return lines[3], lines[4]


def test_diag_plain_ascii():
    shown, caret = _render("let x = 1;", 4, 5)
    assert shown == "1 | let x = 1;", shown
    assert caret == "  |     ^ here", caret


def test_diag_caret_after_tab():
    shown, caret = _render("\tlet x = 1;", 5, 6)
    assert shown == "1 |     let x = 1;", shown
    assert caret == "  |         ^ here", caret


def test_diag_caret_after_wide_glyph():
    text = "let 名前 = 1;\nlet y = 名前 + z;"
    z = text.index("z")
    shown, caret = _render(text, z, z + 1)
    assert shown == "2 | let y = 名前 + z;", shown
    assert caret == "  | " + " " * 15 + "^ here", caret


def test_diag_underline_counts_cells():
    _, caret = _render("let 名前 = 1;", 4, 6)
    assert caret == "  |     ^^^^ here", caret


# ------------------------------------------------------------------ fmt

def test_fmt_trailing_comma_has_no_trailing_space():
    src = "struct S {\n    a: Int,\n    b: Int,\n}\n"
    assert format_code(src) == src
    out = format_code('let s = S {\nid: 1,\nname: "x",\n};\n')
    assert out == 'let s = S {\n    id: 1,\n    name: "x",\n};\n', out


def test_fmt_leaves_paths_and_strings_alone():
    src = 'let o = Option::Some(1);\nrt.print("a,b: c // d");\n'
    assert format_code(src) == src


def test_fmt_else_branch_indent():
    src = "fn f() -> Int {\nif c {\n1\n} else {\n2\n}\n}\n"
    want = "fn f() -> Int {\n    if c {\n        1\n    } else {\n        2\n    }\n}\n"
    assert format_code(src) == want, format_code(src)


def test_fmt_spacing_rules():
    src = 'fn f(a:Int,b:Int) -> Int !{Clock,Runtime} { g(a,"x") }\n'
    want = 'fn f(a: Int, b: Int) -> Int ! {Clock, Runtime} { g(a, "x") }\n'
    assert format_code(src) == want, format_code(src)


def test_fmt_keeps_continuation_alignment():
    src = ("fn f() -> Int {\n"
           "    let v = area(a)\n"
           "        + area(b);\n"
           "    let l = prepend(1,\n"
           "                    prepend(2, empty()));\n"
           "    v\n"
           "}\n")
    assert format_code(src) == src, format_code(src)


def test_fmt_examples_are_canonical():
    for root, _, files in os.walk(EXAMPLES):
        for name in files:
            if not name.endswith(".nova"):
                continue
            path = os.path.join(root, name)
            src = open(path, encoding="utf-8").read()
            out = format_code(src)
            assert out == src, f"{path} would be reformatted"
            assert format_code(out) == out, f"{path}: formatting is not idempotent"


# ----------------------------------------------------------------- lint

LINT_PROBE = """fn shadow() -> Int {
    let x = 1;
    let x = x + 1;
    let dead = 5;
    let _ignored = 6;
    x
}
fn captured() -> Int {
    let base = 10;
    let add = |n: Int| n + base;
    add(1)
}
fn assigned_only() -> Int {
    let mut count = 0;
    count = 1;
    let mut seen = 0;
    seen = seen + 1;
    seen
}
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("lint");
    let unused = shadow();
    captured() + assigned_only()
}
"""


def test_lint_unused_let():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "probe.nova")
        with open(path, "w", encoding="utf-8") as f:
            f.write(LINT_PROBE)
        got = [(w.line, w.message) for w in lint_file(path) if w.rule == "W0201"]
    assert got == [
        (4, "Local `dead` is never used"),
        (14, "Local `count` is assigned to but never read"),
        (22, "Local `unused` is never used"),
    ], got


# ------------------------------------------------------------------ pkg

def test_semver_accepts_spec_forms():
    for v in ("1.0.0", "0.2.0", "10.20.30", "1.0.0-alpha.1", "1.0.0+build.5",
              "1.0.0-rc.1+exp.sha.5114f85"):
        assert is_semver(v), v


def test_semver_rejects_loose_forms():
    for v in ("v1", "v1.0.0", "alpha", "1.0", "01.0.0", "1.0.0-", "", "1.0.0 "):
        assert not is_semver(v), v


def test_add_rejects_bad_version_without_touching_manifest():
    out, err = io.StringIO(), io.StringIO()
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                ok = add_dependency("analytics", version="v1.2.0", capabilities=["Network"])
                assert ok is False
                assert not os.path.exists("nova.toml")
                assert add_dependency("analytics", version="1.2.0-beta.1",
                                      capabilities=["Network"])
            text = open("nova.toml", encoding="utf-8").read()
        finally:
            os.chdir(cwd)
    assert "not a valid version" in err.getvalue(), err.getvalue()
    assert "drop the leading `v`" in err.getvalue(), err.getvalue()
    want = 'analytics = { version = "1.2.0-beta.1", capabilities = ["Network"] }'
    assert want in text, text


def main() -> int:
    os.chdir(ROOT)      # lint_file goes through NovaCompiler, which keeps .nova_cache/ in cwd
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
        except Exception:
            failed += 1
            print(f"  FAIL {name}")
            for line in traceback.format_exc().splitlines()[-3:]:
                print("       " + line)
        else:
            passed += 1
            print(f"  ok   {name}")
    print(f"\n{passed} passed, {failed} failed")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
