"""Lexer for the regionlab prototype language. See regionlab/README.md."""
from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = {"fn", "let", "region", "close", "write", "read", "shared",
           "exclusive", "alloc", "copy"}

PUNCT = ["->", "(", ")", "{", "}", ",", ";", ":", "="]


@dataclass
class Token:
    kind: str
    text: str
    line: int


def lex(src: str) -> list[Token]:
    toks: list[Token] = []
    i, n = 0, len(src)
    line = 1
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c in " \t\r":
            i += 1
            continue
        if src.startswith("--", i) or c == "#":
            # `#` is also a comment marker (not just `--`) specifically
            # so the test harness's `# expect:` directive lines
            # (regionlab/tests/run.py) are ordinary comments to the
            # language itself, and a test file can be run directly
            # through the CLI unmodified, not only through the runner.
            while i < n and src[i] != "\n":
                i += 1
            continue
        start = i
        if c.isalpha() or c == "_":
            while i < n and (src[i].isalnum() or src[i] == "_"):
                i += 1
            text = src[start:i]
            toks.append(Token("kw" if text in KEYWORDS else "ident",
                              text, line))
            continue
        if c.isdigit():
            while i < n and src[i].isdigit():
                i += 1
            toks.append(Token("int", src[start:i], line))
            continue
        for p in PUNCT:
            if src.startswith(p, i):
                i += len(p)
                toks.append(Token(p, p, line))
                break
        else:
            raise SyntaxError(f"line {line}: unexpected character {c!r}")
    toks.append(Token("eof", "", line))
    return toks
