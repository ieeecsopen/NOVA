"""Lexer for NOVA Core v0.1 (RFC 0001)."""
from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import Diagnostic, Label, Span

KEYWORDS = {
    "capability", "fn", "let", "mut", "if", "else", "true", "false", "widen",
    "struct", "enum", "trait", "impl", "for", "in", "while", "match",
    "pub", "import", "self",
}

# Longest-first so that `->` beats `-`, `::` beats `:`, `||` beats `|`.
PUNCT = [
    "->", "::", "==", "!=", "<=", ">=", "&&", "||", "=>",
    "(", ")", "{", "}", "[", "]",
    ",", ";", ":", ".", "!", "|", "=", "<", ">", "+", "-", "*", "/",
]


@dataclass
class Token:
    kind: str      # 'ident' | 'int' | 'string' | 'kw' | punctuation | 'eof'
    text: str
    span: Span

    def __repr__(self) -> str:
        return f"{self.kind}({self.text!r})"


def lex(src: str, base: int = 0) -> list[Token]:
    """`base` offsets every span, so several files share one span space."""
    toks: list[Token] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1
            continue
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
            continue
        start = i
        if c.isalpha() or c == "_":
            while i < n and (src[i].isalnum() or src[i] == "_"):
                i += 1
            text = src[start:i]
            toks.append(Token("kw" if text in KEYWORDS else "ident",
                              text, Span(base + start, base + i)))
            continue
        if c.isdigit():
            while i < n and (src[i].isdigit() or src[i] == "_"):
                i += 1
            toks.append(Token("int", src[start:i].replace("_", ""),
                              Span(base + start, base + i)))
            continue
        if c == '"':
            i += 1
            buf = []
            while i < n and src[i] != '"':
                if src[i] == "\\" and i + 1 < n:
                    esc = src[i + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"',
                                "\\": "\\"}.get(esc, esc))
                    i += 2
                else:
                    buf.append(src[i])
                    i += 1
            if i >= n:
                raise Diagnostic("E0004", "unterminated string literal",
                                 [Label(Span(base + start, base + n), "starts here")])
            i += 1
            toks.append(Token("string", "".join(buf), Span(base + start, base + i)))
            continue
        for p in PUNCT:
            if src.startswith(p, i):
                i += len(p)
                toks.append(Token(p, p, Span(base + start, base + i)))
                break
        else:
            raise Diagnostic("E0003", f"unexpected character {c!r}",
                             [Label(Span(base + start, base + start + 1), "not valid here")])
    toks.append(Token("eof", "", Span(base + n, base + n)))
    return toks
