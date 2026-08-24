#!/usr/bin/env python3
"""Diff the capability manifest of two versions of a NOVA file.

Experiment 001 (docs/experiments/001-capability-manifests.md), testing
P14: is a dependency's authority creep a detectable, checkable event
rather than something discovered at runtime.

    python3 tools/manifest-diff.py old.nova new.nova
    # exit 0: no breaking change.  exit 1: authority grew somewhere.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verifier"))

from refspec.diagnostics import Diagnostic   # noqa: E402
from refspec.driver import compile_source    # noqa: E402
from refspec.manifest import diff, has_breaking_change, manifest  # noqa: E402


def load(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        unit = compile_source(text, path)
    except Diagnostic as d:
        print(d.sources.render(d), file=sys.stderr)
        raise SystemExit(1)
    return manifest(unit.result)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: manifest-diff.py <old.nova> <new.nova>", file=sys.stderr)
        return 2
    old, new = load(argv[1]), load(argv[2])
    changes = diff(old, new)
    if not changes:
        print("no change in any published capability requirement")
        return 0
    for c in changes:
        print(c)
    breaking = has_breaking_change(changes)
    print()
    print("VERDICT: " + ("authority grew — this is a breaking change, "
                         "regardless of the version number attached to it"
                         if breaking else
                         "no authority growth; safe to treat as compatible"))
    return 1 if breaking else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
