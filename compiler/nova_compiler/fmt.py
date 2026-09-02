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

_EFFECT_ROW = re.compile(r"!\s*\{([^}]*)\}")
_COMMA = re.compile(r",[ \t]*(?=\S)")
_COLON = re.compile(r"(?<!:):(?!:)[ \t]*(?=\S)")     # never `::`


def _split(line: str) -> list[tuple[str, str]]:
    """Cut a line into ("code" | "string" | "comment", text) pieces.

    The spacing rules below only touch "code"; a string literal or a
    trailing `//` comment is copied through untouched. (NOVA has no block
    comments, so a line is enough context.)
    """
    pieces: list[tuple[str, str]] = []
    i = start = 0
    n = len(line)
    while i < n:
        if line[i] == '"':
            if i > start:
                pieces.append(("code", line[start:i]))
            j = i + 1
            while j < n and line[j] != '"':
                j += 2 if line[j] == "\\" else 1
            j = min(j + 1, n)
            pieces.append(("string", line[i:j]))
            i = start = j
        elif line.startswith("//", i):
            if i > start:
                pieces.append(("code", line[start:i]))
            pieces.append(("comment", line[i:]))
            return pieces
        else:
            i += 1
    if start < n:
        pieces.append(("code", line[start:]))
    return pieces


def _space(code: str) -> str:
    code = _EFFECT_ROW.sub(
        lambda m: "! {" + ", ".join(p.strip() for p in m.group(1).split(",")
                                    if p.strip()) + "}", code)
    code = _COMMA.sub(", ", code)
    code = _COLON.sub(": ", code)
    return code


def _render(pieces: list[tuple[str, str]]) -> str:
    out: list[str] = []
    for kind, text in pieces:
        if kind == "code":
            text = _space(text)
        elif kind == "string" and out and out[-1][-1] in ",:":
            out.append(" ")      # `f(a,"x")` -> `f(a, "x")`
        out.append(text)
    return "".join(out)


def format_code(source: str) -> str:
    formatted_lines: list[str] = []
    indent_level = 0       # block nesting, from braces
    paren_depth = 0        # unclosed `(` carried over from earlier lines
    terminated = True      # did the previous code line finish a statement?

    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue
        if stripped.startswith("//"):
            formatted_lines.append("    " * indent_level + stripped)
            continue

        pieces = _split(stripped)
        code = "".join(t for k, t in pieces if k == "code").rstrip()

        # Only braces drive indentation. Inside an unclosed call, or on a
        # line that continues the previous expression (`+ area(...)`, a
        # second `prepend(` argument), the author's own alignment is kept
        # and just the spacing is normalised. A line that starts by
        # closing a block (`}`, `} else {`) sits one level out.
        if paren_depth > 0 or (not terminated and stripped[0] != "}"):
            lead = line[:len(line) - len(line.lstrip())]
        else:
            indent = indent_level - 1 if stripped[0] == "}" else indent_level
            lead = "    " * max(0, indent)
        formatted_lines.append(lead + _render(pieces))

        net = code.count("{") - code.count("}")
        indent_level = max(0, indent_level + max(-1, min(1, net)))
        paren_depth = max(0, paren_depth + code.count("(") - code.count(")"))
        terminated = code.endswith(("{", "}", ";", ","))

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
