#!/usr/bin/env python3
"""Verify every internal Markdown link and anchor in the repository.

The design record is heavily cross-referenced and a dead link in the
Constitution or an RFC is a real defect, so this runs in CI alongside the
conformance suite.

Anchor slugs follow GitHub's rule: lowercase, drop characters that are
neither word characters, whitespace, nor hyphens, then replace each
remaining whitespace character with a hyphen (consecutive spaces produce
consecutive hyphens - do not collapse them).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*$', re.M)
CODE_SPAN = re.compile(r'`[^`\n]*`')
FENCED_BLOCK = re.compile(r'```.*?```', re.S)


def _strip_code_spans(text: str) -> str:
    """Blank out inline code spans before scanning for links.

    A code example like `` `fn f[r](...)` `` accidentally matches the
    link pattern (`[r]` immediately followed by `(...)`), even though it
    is prose about NOVA's own `[...]` binder syntax, not a Markdown
    link. Replacing each span with equal-length spaces keeps every
    other offset in the file unchanged, which matters for nothing here
    (this script only reports file/anchor names, not offsets) but is
    the cheap, obviously-correct way to do the blanking regardless.
    """
    text = FENCED_BLOCK.sub(lambda m: " " * len(m.group(0)), text)
    return CODE_SPAN.sub(lambda m: " " * len(m.group(0)), text)


def slug(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'\s', '-', text)


def main() -> int:
    docs = [p for p in ROOT.rglob('*.md') if '.git' not in p.parts]
    anchors = {p: {slug(m.group(2)) for m in HEADING.finditer(p.read_text())}
               for p in docs}

    broken: list[str] = []
    checked = 0
    for doc in docs:
        for m in LINK.finditer(_strip_code_spans(doc.read_text())):
            link = m.group(1)
            if link.startswith(('http://', 'https://', 'mailto:', '#!')):
                continue
            path, _, anchor = link.partition('#')
            target = (doc.parent / path).resolve() if path else doc
            here = doc.relative_to(ROOT)
            checked += 1
            if not target.exists():
                broken.append(f"{here}: missing file -> {link}")
                continue
            if anchor and target in anchors and anchor not in anchors[target]:
                broken.append(f"{here}: missing anchor -> {link}")

    for b in broken:
        print(b, file=sys.stderr)
    print(f"{checked - len(broken)}/{checked} internal links resolve")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
