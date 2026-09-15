"""Bounded parser fuzz smoke test for CI and local regression checks."""
from __future__ import annotations

import argparse
import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.refspec.diagnostics import Diagnostic
from verifier.refspec.parser import parse


ALPHABET = string.printable


def fuzz(iterations: int, seed: int) -> int:
    generator = random.Random(seed)
    diagnostics = 0
    for _ in range(iterations):
        source = "".join(generator.choice(ALPHABET) for _ in range(generator.randrange(0, 256)))
        try:
            parse(source)
        except Diagnostic:
            diagnostics += 1
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    diagnostics = fuzz(args.iterations, args.seed)
    print(f"parser fuzz smoke: {args.iterations} inputs, {diagnostics} diagnostics")


if __name__ == "__main__":
    main()
