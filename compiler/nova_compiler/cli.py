"""NOVA Command Line Interface (`nova`).

Commands:
  nova check <file>      Type and effect check a NOVA program
  nova build <file>      Compile a NOVA program to a native executable
  nova run <file>        Compile and immediately run a NOVA program
  nova bench <file>      Benchmark clean vs incremental compilation and runtime metrics
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from .driver import NovaCompiler


def main(argv: list[str] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="nova",
        description="NOVA Programming Language Compiler and Toolchain",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # nova check
    check_p = subparsers.add_parser("check", help="Type-check and verify effect rows without code generation")
    check_p.add_argument("file", help="Path to .nova source file")

    # nova build
    build_p = subparsers.add_parser("build", help="Compile NOVA source into an optimized native machine binary")
    build_p.add_argument("file", help="Path to .nova source file")
    build_p.add_argument("-o", "--output", help="Output executable binary path")
    build_p.add_argument("--clean", action="store_true", help="Force clean compilation (bypass cache)")

    # nova run
    run_p = subparsers.add_parser("run", help="Compile and execute a NOVA program")
    run_p.add_argument("file", help="Path to .nova source file")
    run_p.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the executable")

    # nova bench
    bench_p = subparsers.add_parser("bench", help="Measure compile time, memory, binary size, and runtime")
    bench_p.add_argument("file", help="Path to .nova source file")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    compiler = NovaCompiler()

    if args.command == "check":
        res, err = compiler.check_file(args.file)
        if err:
            print(err, file=sys.stderr)
            return 1
        print(f"\033[32m✓\033[0m {args.file}: checked ok (all type and capability invariants verified)")
        return 0

    elif args.command == "build":
        success, out, metrics = compiler.build_file(args.file, output_binary=args.output, force_clean=args.clean)
        if not success:
            print(out, file=sys.stderr)
            return 1
        cache_label = "(cached)" if metrics and metrics.is_cached else "(fresh build)"
        print(f"\033[32m✓\033[0m Compiled {args.file} -> \033[1m{out}\033[0m {cache_label}")
        if metrics:
            print(f"  • Total time:  {metrics.total_time_ms:.2f} ms")
            print(f"  • Binary size: {metrics.binary_size_bytes:,} bytes")
        return 0

    elif args.command == "run":
        return compiler.run_file(args.file, args=args.args)

    elif args.command == "bench":
        print(f"=== Benchmarking NOVA Compiler: {args.file} ===")
        
        # 1. Clean build
        _, _, clean_m = compiler.build_file(args.file, force_clean=True)
        # 2. Incremental build
        _, _, inc_m = compiler.build_file(args.file, force_clean=False)
        # 3. Execution time
        t0 = time.perf_counter()
        exit_code = compiler.run_file(args.file)
        t_run = (time.perf_counter() - t0) * 1000.0

        print(f"  [1] Clean Compile Time:       {clean_m.total_time_ms:.2f} ms" if clean_m else "  [1] Clean Compile: failed")
        print(f"  [2] Incremental Compile Time: {inc_m.total_time_ms:.2f} ms" if inc_m else "  [2] Incremental: failed")
        print(f"  [3] Executable Binary Size:   {clean_m.binary_size_bytes:,} bytes" if clean_m else "  [3] Binary Size: -")
        print(f"  [4] Native Execution Time:    {t_run:.2f} ms (exit code: {exit_code})")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
