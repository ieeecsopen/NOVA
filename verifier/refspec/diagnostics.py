"""Diagnostics. Constitution Article X: errors are part of the language.

A rule that cannot be explained in a good error message is a rule that is
too subtle to keep, so this module is deliberately not an afterthought.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    """A byte range in a source file."""
    start: int
    end: int

    def to(self, other: "Span") -> "Span":
        return Span(min(self.start, other.start), max(self.end, other.end))


EMPTY_SPAN = Span(0, 0)


@dataclass
class Label:
    span: Span
    message: str
    primary: bool = True


@dataclass
class Diagnostic(Exception):
    code: str          # e.g. "E0201"
    title: str
    labels: list[Label] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    helps: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover - overridden by render()
        return f"error[{self.code}]: {self.title}"


class Source:
    """A source file, with the line arithmetic needed to render diagnostics."""

    def __init__(self, text: str, name: str = "<input>") -> None:
        self.text = text
        self.name = name
        self._line_starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                self._line_starts.append(i + 1)

    def line_col(self, offset: int) -> tuple[int, int]:
        lo, hi = 0, len(self._line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1, offset - self._line_starts[lo] + 1

    def line_text(self, line_no: int) -> str:
        start = self._line_starts[line_no - 1]
        end = (self._line_starts[line_no]
               if line_no < len(self._line_starts) else len(self.text))
        return self.text[start:end].rstrip("\n")

    def label_lines(self, lab: Label) -> list[str]:
        """Render one label. `lab.span` must already be local to this file."""
        line, col = self.line_col(lab.span.start)
        text = self.line_text(line)
        pad = " " * len(str(line))
        width = max(1, min(lab.span.end - lab.span.start,
                           len(text) - (col - 1)))
        caret = ("^" if lab.primary else "-") * width
        return [f"{pad}--> {self.name}:{line}:{col}",
                f"{pad} |",
                f"{line} | {text}",
                f"{pad} | {' ' * (col - 1)}{caret} {lab.message}"]

    def render(self, d: Diagnostic) -> str:
        out = [f"error[{d.code}]: {d.title}"]
        for lab in d.labels:
            out += self.label_lines(lab)
        out += [f"  = note: {n}" for n in d.notes]
        out += [f"  = help: {h}" for h in d.helps]
        return "\n".join(out)
