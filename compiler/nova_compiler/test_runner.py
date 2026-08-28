"""NOVA Unified Test Runner (`nova test`).

Executes:
- Conformance test suites
- Memory & regionlab tests
- Capability manifest & security tests
- Example verification tests
"""
from __future__ import annotations

import os
import subprocess
import sys
import time


def run_tests(pattern: str = "") -> int:
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print("\033[1m=== Running NOVA Comprehensive Test Suites ===\033[0m\n")

    t0 = time.perf_counter()
    total_passed = 0
    total_failed = 0

    suites = [
        ("Documentation Links", [sys.executable, os.path.join(repo_root, "tools", "check-links.py")]),
        ("Core Conformance Suite", [sys.executable, os.path.join(repo_root, "tests", "run_conformance.py")]),
        ("RegionLab Memory Model Suite", [sys.executable, os.path.join(repo_root, "regionlab", "tests", "run.py")]),
        ("Capability Manifest Security Suite", [sys.executable, os.path.join(repo_root, "tests", "manifest", "run.py")]),
        ("Graded Effect Rows Suite", [sys.executable, os.path.join(repo_root, "tests", "grading", "run.py")]),
        ("Execution Tracing Suite", [sys.executable, os.path.join(repo_root, "tests", "tracing", "run.py")]),
    ]

    for name, cmd in suites:
        if pattern and pattern.lower() not in name.lower():
            continue

        print(f"Running \033[36m{name}\033[0m...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  \033[32m✓\033[0m {name} passed")
            total_passed += 1
        else:
            print(f"  \033[31m✗\033[0m {name} FAILED:\n{res.stderr}\n{res.stdout}")
            total_failed += 1

    elapsed = (time.perf_counter() - t0) * 1000.0
    print(f"\n\033[1mSummary:\033[0m {total_passed} suites passed, {total_failed} failed in {elapsed:.2f} ms")
    return 0 if total_failed == 0 else 1
