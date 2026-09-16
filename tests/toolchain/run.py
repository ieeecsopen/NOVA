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
import subprocess
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from compiler.nova_compiler.fmt import format_code                   # noqa: E402
from compiler.nova_compiler.lint import lint_file                    # noqa: E402
from compiler.nova_compiler.pkg import add_dependency, is_semver     # noqa: E402
from compiler.nova_compiler.driver import NovaCompiler               # noqa: E402
from compiler.nova_compiler.hir import HIRMethodCall, lower_ast_to_hir  # noqa: E402
from verifier.refspec.diagnostics import Diagnostic, Label, Source, Span  # noqa: E402
from verifier.refspec.driver import compile_source                    # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")


# ---------------------------------------------------------- diagnostics

def test_hir_preserves_generic_and_trait_dispatch_metadata():
    source = """struct Point { value: Int }
trait Show { fn show(self) -> String; }
impl Show for Point { fn show(self) -> String { \"point\" } }
fn identity[T](x: T) -> T { x }
fn main(rt: Runtime) -> Int ! {Runtime} {
    let p = Point { value: 1 };
    rt.print(p.show());
    identity(0)
}
"""
    unit = compile_source(source, "<hir-test>")
    hir = lower_ast_to_hir(unit.program.modules[-1].decls,
                           check_result=unit.result)

    identity = next(fn for fn in hir.functions if fn.name == "identity")
    assert identity.type_params == ["T"]
    assert [(trait.name, trait.methods) for trait in hir.traits] == [
        ("Show", ["show"])]
    assert [(impl.trait_name, impl.methods) for impl in hir.impls] == [
        ("Show", ["show"])]

    main = next(fn for fn in hir.functions if fn.name == "main")
    calls = []

    def visit(expr):
        if isinstance(expr, HIRMethodCall):
            calls.append(expr)
        for value in vars(expr).values():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "__dataclass_fields__"):
                        visit(item)
            elif hasattr(value, "__dataclass_fields__"):
                visit(value)

    visit(main.body)
    assert any(call.dispatch_target == "Show::show" for call in calls)

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


def test_enterprise_demo_builds_successfully():
    """The enterprise platform example builds cleanly."""
    with tempfile.TemporaryDirectory() as d:
        compiler = NovaCompiler(cache_dir=os.path.join(d, ".nova_cache"))
        output = os.path.join(d, "enterprise-platform")
        success, message, metrics = compiler.build_file(
            os.path.join(EXAMPLES, "enterprise-platform.nova"),
            output_binary=output)
    assert success, message
    assert metrics is not None
    assert metrics.backend in ("native-c", "interpreter")


def test_cli_demo_is_explicitly_interpreter_backed():
    """Constructs outside the native C subset fall back to interpreter-backed runner."""
    with tempfile.TemporaryDirectory() as d:
        compiler = NovaCompiler(cache_dir=os.path.join(d, ".nova_cache"))
        output = os.path.join(d, "cli-program")
        success, message, metrics = compiler.build_file(
            os.path.join(EXAMPLES, "cli-program.nova"),
            output_binary=output)
    assert success, message
    assert metrics is not None
    assert metrics.backend == "interpreter"
    assert "enum types" in metrics.fallback_reason


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


# ---------------------------------------------------------------- WASI security

def test_wasi_build_fails_closed_instead_of_emitting_host_runner():
    """A requested WASI guest must never be replaced by a host-authority script."""
    source = """fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("sandbox probe");
    0
}
"""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "guest.nova")
        output = os.path.join(d, "guest.wasm")
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        success, message, metrics = NovaCompiler(
            cache_dir=os.path.join(d, ".nova_cache")).build_file(
                path, output_binary=output, target="wasi")

        assert success is False
        assert metrics is None
        assert "refusing to emit an interpreter-backed artifact" in message
        assert not os.path.exists(output), "WASI build emitted a host runner"


def test_cli_help_includes_example_usage():
    result = subprocess.run(
        [sys.executable, "-m", "compiler.nova_compiler.cli", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    help_text = result.stdout + result.stderr
    assert "nova dev examples/hello.nova" in help_text, help_text
    assert "nova build examples/hello.nova --target wasm -o app.wasm" in help_text, help_text
    assert "nova check examples/hello.nova --emit-hir" in help_text, help_text


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
