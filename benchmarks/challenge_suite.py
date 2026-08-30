"""NOVA toolchain benchmark.

Measures wall-clock time for the operations the toolchain actually
performs today, on the real example programs:

  * `nova check`  — lex + parse + type/effect/capability checking
  * `nova build`  — the above, plus codegen (native C subset or the
                    interpreter-backed runner)
  * `nova run`    — the above, plus execution via the reference interpreter

This is a measurement of *this machine running this toolchain*. It is not
a comparison against other languages: the constructs such a comparison
would need (native tasks, channels, compiled loops) do not have a native
code path yet. See README.md for why there is no such table.

Usage:  python3 benchmarks/challenge_suite.py [--json]
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
NOVA = os.path.join(REPO_ROOT, "nova")
EXAMPLES = os.path.join(REPO_ROOT, "examples")
REPEATS = 5


def _time(cmd: list[str], repeats: int = REPEATS) -> dict:
    samples = []
    ok = True
    for _ in range(repeats):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        samples.append((time.perf_counter() - t0) * 1000.0)
        ok = ok and res.returncode == 0
    return {
        "median_ms": round(statistics.median(samples), 2),
        "min_ms": round(min(samples), 2),
        "ok": ok,
    }


def _sample_files() -> list[str]:
    files = []
    for name in sorted(os.listdir(EXAMPLES)):
        if name.endswith(".nova") and "rejected" not in name:
            files.append(os.path.join(EXAMPLES, name))
    return files


def bench_check(files: list[str]) -> dict:
    out = {}
    for f in files:
        out[os.path.basename(f)] = _time([NOVA, "check", f])
    return out


def bench_build_cache(sample: str) -> dict:
    """Clean vs. cached build for one file."""
    clean = _time([NOVA, "build", sample, "-o", "/tmp/nova_bench_out",
                   "--clean"], repeats=3)
    cached = _time([NOVA, "build", sample, "-o", "/tmp/nova_bench_out"],
                   repeats=REPEATS)
    return {"clean": clean, "cached": cached}


def bench_run(files: list[str]) -> dict:
    out = {}
    for f in files:
        out[os.path.basename(f)] = _time([NOVA, "run", f], repeats=3)
    return out


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    files = _sample_files()
    hello = os.path.join(EXAMPLES, "hello.nova")

    if not as_json:
        print("=== NOVA toolchain benchmark ===")
        print(f"repo: {REPO_ROOT}")
        print(f"samples: {len(files)} example programs, median of {REPEATS} runs\n")

    check = bench_check(files)
    build = bench_build_cache(hello)
    run = bench_run(files)

    check_med = statistics.median(v["median_ms"] for v in check.values())
    run_med = statistics.median(v["median_ms"] for v in run.values())

    summary = {
        "check_median_ms_across_examples": round(check_med, 2),
        "run_median_ms_across_examples": round(run_med, 2),
        "build_hello_clean_ms": build["clean"]["median_ms"],
        "build_hello_cached_ms": build["cached"]["median_ms"],
        "per_file": {"check": check, "run": run},
        "note": ("Wall-clock on this machine. Not a cross-language "
                 "comparison — see README.md."),
    }

    if as_json:
        json.dump(summary, sys.stdout, indent=2)
        print()
    else:
        print(f"  nova check   median across examples : {check_med:.2f} ms")
        print(f"  nova run     median across examples : {run_med:.2f} ms")
        print(f"  nova build hello.nova  (clean)      : {build['clean']['median_ms']:.2f} ms")
        print(f"  nova build hello.nova  (cached)     : {build['cached']['median_ms']:.2f} ms")
        print()
        print("  Wall-clock on this machine. Not a cross-language comparison.")

    with open(os.path.join(REPO_ROOT, "benchmarks", "results.json"),
              "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
