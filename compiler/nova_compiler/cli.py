"""NOVA Command Line Interface (`nova`).

Commands:
  nova check <file>            Type and effect check a NOVA program
  nova build <file>            Compile a NOVA program to a native executable
  nova run <file>              Compile and immediately run a NOVA program
  nova test [pattern]          Run unified conformance and security test suites
  nova fmt [files...]          Format NOVA source files to canonical style
  nova lint [files...]         Lint NOVA source files for style and quality
  nova doc [path]              Generate structured API documentation
  nova add <pkg> [--caps ...]  Add a dependency to nova.toml with capability bounds
  nova remove <pkg>            Remove a dependency from nova.toml
  nova update                  Update and lock dependencies into nova.lock
  nova publish                 Package and compute integrity hashes for registry release
  nova deploy [--target ...]   Synthesize deployment bundles (container, edge, monolith)
  nova lsp                     Launch the Language Server Protocol (LSP) server
  nova bench <file>            Benchmark compile time, memory, binary size, and latency
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time

from .driver import NovaCompiler
from .fmt import format_file
from .lint import lint_file
from .test_runner import run_tests
from .docgen import generate_docs
from .pkg import (
    init_new_package,
    add_dependency,
    remove_dependency,
    update_dependencies,
    publish_package,
    deploy_application,
)
from .lsp_server import NovaLSPServer


def main(argv: list[str] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="nova",
        description="NOVA Developer Toolchain & Native Compiler",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # nova new
    new_p = subparsers.add_parser("new", help="Create a new production NOVA project scaffolding")
    new_p.add_argument("name", help="Name of project to create")

    # nova check
    check_p = subparsers.add_parser("check", help="Type-check and verify effect rows without code generation")
    check_p.add_argument("file", nargs="?", default="src/main.nova", help="Path to .nova source file (default: src/main.nova)")
    check_p.add_argument("--emit-hir", action="store_true", help="Print High-Level IR (HIR)")
    check_p.add_argument("--emit-mir", action="store_true", help="Print Mid-Level IR (MIR)")

    # nova build
    build_p = subparsers.add_parser("build", help="Compile NOVA source into an optimized machine binary or WASM")
    build_p.add_argument("file", nargs="?", default="src/main.nova", help="Path to .nova source file (default: src/main.nova)")
    build_p.add_argument("-o", "--output", help="Output executable binary path")
    build_p.add_argument("--target", default="native", choices=["native", "wasm", "wasi"], help="Compilation target. `wasm`/`wasi` are not implemented yet (Milestone 3) and fall back to the interpreter-backed runner.")
    build_p.add_argument("--clean", action="store_true", help="Force clean compilation (bypass cache)")
    build_p.add_argument("--emit-hir", action="store_true", help="Print High-Level IR (HIR)")
    build_p.add_argument("--emit-mir", action="store_true", help="Print Mid-Level IR (MIR)")

    # nova run
    run_p = subparsers.add_parser("run", help="Compile and execute a NOVA program")
    run_p.add_argument("file", nargs="?", default="src/main.nova", help="Path to .nova source file (default: src/main.nova)")
    run_p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the executable")

    # nova dev
    dev_p = subparsers.add_parser("dev", help="Start development mode with instant execution and hot check")
    dev_p.add_argument("file", nargs="?", default="src/main.nova", help="Path to .nova source file (default: src/main.nova)")
    dev_p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the executable")

    # nova test
    test_p = subparsers.add_parser("test", help="Run unified test suites")
    test_p.add_argument("pattern", nargs="?", default="", help="Optional test suite filter pattern")

    # nova fmt
    fmt_p = subparsers.add_parser("fmt", help="Format source files to canonical style")
    fmt_p.add_argument("files", nargs="*", default=["examples"], help="Files or directories to format")
    fmt_p.add_argument("--check", action="store_true", help="Check formatting without writing changes")

    # nova lint
    lint_p = subparsers.add_parser("lint", help="Lint source files for style and quality warnings")
    lint_p.add_argument("files", nargs="*", default=["examples"], help="Files or directories to lint")

    # nova doc
    doc_p = subparsers.add_parser("doc", help="Generate API documentation from source")
    doc_p.add_argument("path", nargs="?", default="examples", help="Source file or directory")
    doc_p.add_argument("-o", "--output", default="docs/api", help="Output directory for documentation")

    # nova add
    add_p = subparsers.add_parser("add", help="Add a dependency with explicit capability bounds")
    add_p.add_argument("pkg", help="Package name")
    add_p.add_argument("--version", default="1.0.0", help="Package version")
    add_p.add_argument("--caps", nargs="*", default=[], help="Allowed capabilities (e.g. Network Filesystem)")

    # nova remove
    remove_p = subparsers.add_parser("remove", help="Remove a dependency from nova.toml")
    remove_p.add_argument("pkg", help="Package name")

    # nova update
    subparsers.add_parser("update", help="Update and lock dependencies into nova.lock")

    # nova publish
    publish_p = subparsers.add_parser("publish", help="Package archive and calculate integrity hashes")
    publish_p.add_argument("-o", "--output", default="dist/", help="Output directory for archive")

    # nova deploy
    deploy_p = subparsers.add_parser("deploy", help="Synthesize deployment artifacts from application model")
    deploy_p.add_argument("--target", default="container", choices=["container", "edge", "monolith"], help="Deployment target")
    deploy_p.add_argument("-o", "--output", default="dist/deploy", help="Output directory for deployment files")

    # nova lsp
    subparsers.add_parser("lsp", help="Run Language Server Protocol server over stdio")

    # nova bench
    bench_p = subparsers.add_parser("bench", help="Measure compile time, memory, binary size, and runtime")
    bench_p.add_argument("file", help="Path to .nova source file")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    compiler = NovaCompiler()

    if args.command == "new":
        init_new_package(args.name)
        return 0

    elif args.command == "check":
        res, err = compiler.check_file(args.file)
        if err:
            print(err, file=sys.stderr)
            return 1
        if getattr(args, "emit_hir", False) and res:
            from .hir import lower_ast_to_hir
            hir_mod = lower_ast_to_hir(res.program.decls, module_name=os.path.splitext(os.path.basename(args.file))[0])
            print("=== HIGH-LEVEL IR (HIR) ===")
            for fn in hir_mod.functions:
                print(f"fn {fn.name}({', '.join(p.name + ': ' + str(p.ty) for p in fn.params)}) -> {fn.return_ty} ! {{{', '.join(fn.effects)}}}")
        if getattr(args, "emit_mir", False) and res:
            from .hir import lower_ast_to_hir
            from .mir import lower_hir_to_mir
            hir_mod = lower_ast_to_hir(res.program.decls, module_name=os.path.splitext(os.path.basename(args.file))[0])
            mir_mod = lower_hir_to_mir(hir_mod)
            print("=== MID-LEVEL IR (MIR) ===")
            for fn in mir_mod.functions:
                print(f"mir fn {fn.name}: {len(fn.blocks)} basic block(s), {len(fn.locals)} local(s)")
        print(f"\033[32m✓\033[0m {args.file}: checked ok (all type and capability invariants verified)")
        return 0

    elif args.command == "build":
        target = getattr(args, "target", "native")
        success, out, metrics = compiler.build_file(args.file, output_binary=args.output, force_clean=args.clean, target=target)
        if not success:
            print(out, file=sys.stderr)
            return 1
        if getattr(args, "emit_hir", False):
            res, _ = compiler.check_file(args.file)
            if res:
                from .hir import lower_ast_to_hir
                hir_mod = lower_ast_to_hir(res.program.decls, module_name=os.path.splitext(os.path.basename(args.file))[0])
                print("=== HIGH-LEVEL IR (HIR) ===")
                for fn in hir_mod.functions:
                    print(f"fn {fn.name}({', '.join(p.name + ': ' + str(p.ty) for p in fn.params)}) -> {fn.return_ty} ! {{{', '.join(fn.effects)}}}")
        if getattr(args, "emit_mir", False):
            res, _ = compiler.check_file(args.file)
            if res:
                from .hir import lower_ast_to_hir
                from .mir import lower_hir_to_mir
                hir_mod = lower_ast_to_hir(res.program.decls, module_name=os.path.splitext(os.path.basename(args.file))[0])
                mir_mod = lower_hir_to_mir(hir_mod)
                print("=== MID-LEVEL IR (MIR) ===")
                for fn in mir_mod.functions:
                    print(f"mir fn {fn.name}: {len(fn.blocks)} basic block(s), {len(fn.locals)} local(s)")
        cache_label = "(cached)" if metrics and metrics.is_cached else "(fresh build)"
        print(f"\033[32m✓\033[0m Compiled {args.file} -> \033[1m{out}\033[0m {cache_label}")
        if metrics:
            if metrics.backend == "native-c":
                print("  • Backend:     native binary (C backend)")
            else:
                reason = metrics.fallback_reason or "unsupported construct"
                print(f"  • Backend:     interpreter-backed runner ({reason})")
            print(f"  • Total time:  {metrics.total_time_ms:.2f} ms")
            print(f"  • Artifact:    {metrics.binary_size_bytes:,} bytes")
        return 0

    elif args.command == "run":
        return compiler.run_file(args.file, args=args.args)

    elif args.command == "dev":
        print(f"\033[1m[nova dev]\033[0m Starting instant execution for \033[36m{args.file}\033[0m...")
        return compiler.run_file(args.file, args=args.args)

    elif args.command == "test":
        return run_tests(args.pattern)

    elif args.command == "fmt":
        targets = []
        for f in args.files:
            if os.path.isfile(f):
                targets.append(f)
            elif os.path.isdir(f):
                for root, _, filenames in os.walk(f):
                    for fn in filenames:
                        if fn.endswith(".nova"):
                            targets.append(os.path.join(root, fn))
        all_ok = True
        for t in targets:
            ok, msg = format_file(t, check_only=args.check)
            print(f"  {msg}")
            if not ok:
                all_ok = False
        return 0 if all_ok else 1

    elif args.command == "lint":
        targets = []
        for f in args.files:
            if os.path.isfile(f):
                targets.append(f)
            elif os.path.isdir(f):
                for root, _, filenames in os.walk(f):
                    for fn in filenames:
                        if fn.endswith(".nova"):
                            targets.append(os.path.join(root, fn))
        total_warns = 0
        for t in targets:
            warns = lint_file(t)
            if warns:
                print(f"\n\033[1m{t}\033[0m:")
                for w in warns:
                    total_warns += 1
                    print(f"  \033[33mwarning[{w.rule}]\033[0m line {w.line}:{w.column}: {w.message}")
                    if w.suggestion:
                        print(f"    \033[36m= help:\033[0m {w.suggestion}")
        if total_warns == 0:
            print("\033[32m✓\033[0m No lint warnings found across scanned files")
            return 0
        else:
            print(f"\nFound {total_warns} lint warning(s)")
            return 0

    elif args.command == "doc":
        generate_docs(args.path, output_dir=args.output)
        return 0

    elif args.command == "add":
        add_dependency(args.pkg, version=args.version, capabilities=args.caps)
        return 0

    elif args.command == "remove":
        remove_dependency(args.pkg)
        return 0

    elif args.command == "update":
        update_dependencies()
        return 0

    elif args.command == "publish":
        publish_package(output_dir=args.output)
        return 0

    elif args.command == "deploy":
        deploy_application(target=args.target, output_dir=args.output)
        return 0

    elif args.command == "lsp":
        server = NovaLSPServer()
        server.run()
        return 0

    elif args.command == "bench":
        print(f"=== Benchmarking NOVA compiler: {args.file} ===")
        _, _, clean_m = compiler.build_file(args.file, force_clean=True)
        _, _, inc_m = compiler.build_file(args.file, force_clean=False)
        t0 = time.perf_counter()
        exit_code = compiler.run_file(args.file)
        t_run = (time.perf_counter() - t0) * 1000.0

        print(f"  [1] Clean build:       {clean_m.total_time_ms:.2f} ms" if clean_m else "  [1] Clean build: failed")
        print(f"  [2] Incremental build: {inc_m.total_time_ms:.2f} ms (cache hit)" if inc_m else "  [2] Incremental: failed")
        print(f"  [3] Artifact size:     {clean_m.binary_size_bytes:,} bytes ({clean_m.backend})" if clean_m else "  [3] Artifact size: -")
        print(f"  [4] Execution time:    {t_run:.2f} ms via reference interpreter (exit code: {exit_code})")
        print()
        print("  Note: these are wall-clock measurements on this machine. They are")
        print("  not a comparison against other languages; see benchmarks/README.md.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
