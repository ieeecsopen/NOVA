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

import gc
import json
import os
import statistics
import subprocess
import sys
import time
import tracemalloc
from typing import Callable
import shutil

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
NOVA = os.path.join(REPO_ROOT, "nova")
EXAMPLES = os.path.join(REPO_ROOT, "examples")
REPEATS = 5
LIST_ALLOCATION_SIZE = 100_000
LIST_ALLOCATION_REPEATS = 3

def _repo_path(*parts: str) -> str:
    return os.path.join(*parts).replace(os.sep, "/")

def _bash_executable() -> str | None:
    bash = shutil.which("bash")
    if bash:
        return bash
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    if os.path.exists(git_bash):
        return git_bash
    return None


def _nova_cmd(*args: str) -> list[str]:
    if os.name == "nt":
        bash = _bash_executable()
        if bash is None:
            raise RuntimeError(
                "Running the NOVA benchmark on Windows requires Git Bash or WSL "
                "because the nova launcher is a shell script."
            )
        return [bash, "./nova", *args]
    return [NOVA, *args]


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    if os.name == "nt":
        env.setdefault("PYTHON", sys.executable.replace(os.sep, "/"))
    return env

def _time(cmd: list[str], repeats: int = REPEATS) -> dict:
    samples = []
    ok = True
    for _ in range(repeats):
        t0 = time.perf_counter()
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=_subprocess_env())
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
            files.append(_repo_path("examples", name))
    return files


def bench_check(files: list[str]) -> dict:
    out = {}
    for f in files:
        out[os.path.basename(f)] = _time(_nova_cmd("check", f))
    return out


def bench_build_cache(sample: str) -> dict:
    """Clean vs. cached build for one file."""
    output_path = _repo_path("benchmarks", "nova_bench_out")
    clean = _time(_nova_cmd("build", sample, "-o", output_path, "--clean"), repeats=3)
    cached = _time(_nova_cmd("build", sample, "-o", output_path), repeats=REPEATS)
    return {"clean": clean, "cached": cached}


def bench_run(files: list[str]) -> dict:
    out = {}
    for f in files:
        out[os.path.basename(f)] = _time(_nova_cmd("run", f), repeats=3)

    return out

def _allocation_totals(
    before: tracemalloc.Snapshot,
    after: tracemalloc.Snapshot,
) -> tuple[int, int]:
    """Return positive heap growth bytes and allocation block count."""
    stats = after.compare_to(before, "lineno")

    allocated_bytes = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
    allocation_count = sum(stat.count_diff for stat in stats if stat.count_diff > 0)

    return int(allocated_bytes), int(allocation_count)

def _measure_list_allocation(
    name: str,
    transform: Callable[[list[int]], list[int]],
    size: int = LIST_ALLOCATION_SIZE,
) -> dict:
    """Measure heap allocations for one large list transformation."""
    source = list(range(size))

    gc.collect()
    tracemalloc.start()

    before = tracemalloc.take_snapshot()

    t0 = time.perf_counter()
    transformed = transform(source)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    after = tracemalloc.take_snapshot()
    _, peak_bytes = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    allocated_bytes, allocation_count = _allocation_totals(before, after)

    return {
        "operation": name,
        "input_size": size,
        "output_size": len(transformed),
        "elapsed_ms": round(elapsed_ms, 2),
        "total_heap_allocation_bytes": allocated_bytes,
        "allocation_count": allocation_count,
        "peak_traced_heap_bytes": int(peak_bytes),
        "checksum": sum(transformed[:10]),
    }


def bench_list_allocations(
    size: int = LIST_ALLOCATION_SIZE,
    repeats: int = LIST_ALLOCATION_REPEATS,
) -> dict:
    """Benchmark heap allocation behaviour for large list transformations."""
    operations: dict[str, Callable[[list[int]], list[int]]] = {
        "copy": lambda values: [value for value in values],
        "map": lambda values: [(value * 3) + 1 for value in values],
        "filter_map": lambda values: [
            (value * 3) + 1
            for value in values
            if value % 2 == 0
        ],
    }

    results = {}

    for name, transform in operations.items():
        samples = [
            _measure_list_allocation(name, transform, size)
            for _ in range(repeats)
        ]

        results[name] = {
            "median_total_heap_allocation_bytes": int(
                statistics.median(
                    sample["total_heap_allocation_bytes"]
                    for sample in samples
                )
            ),
            "median_allocation_count": int(
                statistics.median(
                    sample["allocation_count"]
                    for sample in samples
                )
            ),
            "median_elapsed_ms": round(
                statistics.median(sample["elapsed_ms"] for sample in samples),
                2,
            ),
            "max_peak_traced_heap_bytes": max(
                sample["peak_traced_heap_bytes"]
                for sample in samples
            ),
            "samples": samples,
        }

    return {
        "input_size": size,
        "repeats": repeats,
        "operations": results,
        "note": "Heap allocation metrics are measured with Python tracemalloc.",
    }


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    files = _sample_files()
    hello = _repo_path("examples", "hello.nova")

    if not as_json:
        print("=== NOVA toolchain benchmark ===")
        print(f"repo: {REPO_ROOT}")
        print(f"samples: {len(files)} example programs, median of {REPEATS} runs\n")

    check = bench_check(files)
    build = bench_build_cache(hello)
    run = bench_run(files)
    list_allocations = bench_list_allocations()

    check_med = statistics.median(v["median_ms"] for v in check.values())
    run_med = statistics.median(v["median_ms"] for v in run.values())

    summary = {
        "check_median_ms_across_examples": round(check_med, 2),
        "run_median_ms_across_examples": round(run_med, 2),
        "build_hello_clean_ms": build["clean"]["median_ms"],
        "build_hello_cached_ms": build["cached"]["median_ms"],
        "per_file": {"check": check, "run": run},
        "list_allocations": list_allocations,
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
        print("List allocation benchmark:")
        print(f"input size                         : {list_allocations['input_size']}")
        print(f"repeats                            : {list_allocations['repeats']}")
        print()
        print("  Wall-clock on this machine. Not a cross-language comparison.")

    with open(os.path.join(REPO_ROOT, "benchmarks", "results.json"),
              "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))