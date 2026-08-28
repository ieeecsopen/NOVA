"""NOVA Source Code Formatter (`nova fmt`).

Applies consistent canonical style:
- 4-space indentation
- Uniform spacing around binary operators, commas, and colons
- Canonical formatting for effect rows: `! {Clock, Network}`
- Preservation of comments and docstrings
"""
from __future__ import annotations

import os
import re
import sys


def format_code(source: str) -> str:
    lines = source.splitlines()
    formatted_lines: list[str] = []
    indent_level = 0
    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()

        # Handle empty lines
        if not stripped:
            formatted_lines.append("")
            continue

        # Comments
        if stripped.startswith("//"):
            formatted_lines.append("    " * indent_level + stripped)
            continue

        if stripped.startswith("/*"):
            in_multiline_comment = True
            formatted_lines.append("    " * indent_level + stripped)
            if "*/" in stripped:
                in_multiline_comment = False
            continue

        if in_multiline_comment:
            formatted_lines.append("    " * indent_level + stripped)
            if "*/" in stripped:
                in_multiline_comment = False
            continue

        # Adjust dedent for closing braces
        closing_braces = stripped.count("}") - stripped.count("{")
        if stripped.startswith("}") or stripped.startswith("),") or stripped.startswith(");"):
            indent_level = max(0, indent_level - 1)

        # Standardize spacing around binary operators
        s = stripped
        # Format effect rows
        s = re.sub(r'!\s*\{([^}]*)\}', lambda m: '! {' + ', '.join(p.strip() for p in m.group(1).split(',') if p.strip()) + '}', s)
        # Format commas
        s = re.sub(r',\s*', ', ', s)
        # Format colons
        s = re.sub(r':\s*', ': ', s)

        formatted_lines.append("    " * indent_level + s)

        # Adjust indent for opening braces
        opening_braces = s.count("{") - s.count("}")
        if opening_braces > 0:
            indent_level += opening_braces
        elif opening_braces < 0 and not (stripped.startswith("}") or stripped.startswith("),")):
            indent_level = max(0, indent_level + opening_braces)

    # Ensure single trailing newline
    return "\n".join(formatted_lines).rstrip() + "\n"


def format_file(path: str, check_only: bool = False) -> tuple[bool, str]:
    if not os.path.exists(path):
        return False, f"error: file not found: {path}"

    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    formatted = format_code(original)

    if check_only:
        if original != formatted:
            return False, f"{path}: needs formatting"
        return True, f"{path}: ok"

    if original != formatted:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted)
        return True, f"formatted {path}"

    return True, f"{path} already formatted"
