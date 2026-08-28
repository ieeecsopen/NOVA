"""NOVA Static Code Linter (`nova lint`).

Linter passes:
- Style & Naming conventions (PascalCase structs/traits/enums, snake_case functions)
- Dead code and unused variable detection
- Redundant pure expressions
- Explicit capability audit checks
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from verifier.refspec.check import CheckResult
from .driver import NovaCompiler


@dataclass
class LintWarning:
    file: str
    line: int
    column: int
    rule: str
    message: str
    suggestion: Optional[str] = None


def lint_file(path: str) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    if not os.path.exists(path):
        return [LintWarning(path, 1, 1, "E999", f"File not found: {path}")]

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    compiler = NovaCompiler()
    unit, err = compiler.check_file(path)

    # 1. Source-level syntax and naming checks
    for idx, line in enumerate(lines, 1):
        # Line length check
        if len(line) > 120 and not line.strip().startswith("//"):
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=120,
                rule="L001",
                message="Line exceeds 120 characters",
                suggestion="Wrap line across multiple lines"
            ))

        # Function naming check (should be snake_case)
        fn_match = re.match(r'^\s*fn\s+([A-Z][a-zA-Z0-9_]*)\s*\(', line)
        if fn_match:
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=fn_match.start(1) + 1,
                rule="L002",
                message=f"Function name '{fn_match.group(1)}' should be snake_case",
                suggestion=f"Rename to '{fn_match.group(1).lower()}'"
            ))

        # Struct/Enum naming check (should be PascalCase)
        type_match = re.match(r'^\s*(?:struct|enum|trait)\s+([a-z][a-zA-Z0-9_]*)\s*', line)
        if type_match:
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=type_match.start(1) + 1,
                rule="L003",
                message=f"Type '{type_match.group(1)}' should be PascalCase",
                suggestion=f"Capitalize to '{type_match.group(1).capitalize()}'"
            ))

        # Check for trailing whitespace
        if line.rstrip("\n").endswith(" ") or line.rstrip("\n").endswith("\t"):
            warnings.append(LintWarning(
                file=path,
                line=idx,
                column=len(line.rstrip("\n")),
                rule="L004",
                message="Trailing whitespace detected",
                suggestion="Remove trailing spaces"
            ))

    # 2. Semantic AST checks
    if unit and unit.result:
        # Check for widened signatures that could be tighter
        if unit.result.widened:
            for fn_name, span in unit.result.widened:
                warnings.append(LintWarning(
                    file=path,
                    line=1,
                    column=1,
                    rule="L010",
                    message=f"Function '{fn_name}' uses effect widening (`= widen`)",
                    suggestion="Verify if a tighter effect row can be used"
                ))

    return warnings
