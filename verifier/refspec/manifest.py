"""Experiment: capability manifests (RFC/DESIGN-OPPORTUNITIES §4, thesis T2).

P14 asks whether a dependency's authority requirements can be published as
part of its interface and checked *before* install, rather than
discovered at first run. This module tests the cheap half of that claim:
can the requirement be **computed and diffed** at all, using only what
RFC 0001 already checks?

NOVA v0.1 has no module or package system (Milestone 2), so there is no
real notion of "this package's public interface" yet. The experiment
therefore treats **one file's checked functions** as a stand-in for a
package's manifest. That is a real limitation, noted in
`docs/experiments/001-capability-manifests.md`, not hidden.
"""
from __future__ import annotations

from dataclasses import dataclass

from .check import CheckResult
from .types import Row


def manifest(result: CheckResult) -> dict[str, str]:
    """name -> printed effect row, for every declared function."""
    return {name: str(info.ty.eff) for name, info in result.fns.items()}


@dataclass
class Change:
    name: str
    kind: str          # "added" | "removed" | "grew" | "shrank" | "changed"
    old: str | None
    new: str | None
    breaking: bool

    def __str__(self) -> str:
        tag = "BREAKING" if self.breaking else "compatible"
        if self.kind == "added":
            return f"  [{tag}] {self.name}: new function, row {self.new}"
        if self.kind == "removed":
            return f"  [{tag}] {self.name}: removed (was {self.old})"
        return f"  [{tag}] {self.name}: {self.old} -> {self.new}"


def _labels(row_str: str) -> set[str]:
    inner = row_str.strip("{}").split("|")[0]
    return {s.strip() for s in inner.split(",") if s.strip()}


def diff(old: dict[str, str], new: dict[str, str]) -> list[Change]:
    """Compare two manifests.

    A function whose row *gained* a capability is flagged breaking: the
    published claim about what it may do just widened, and anything that
    depended on it having a smaller row (an audit, a sandbox, a `widen`-free
    caller) may now be wrong. A row that *shrank* is compatible: any caller
    that tolerated the old, larger row still does.

    This is deliberately narrower than full semver compatibility (P13):
    it says nothing about parameter or return types. It answers exactly
    one question — did this dependency's authority grow? — because that is
    the question P14 is about and the one nothing today checks.
    """
    changes: list[Change] = []
    for name in sorted(set(old) - set(new)):
        changes.append(Change(name, "removed", old[name], None, True))
    for name in sorted(set(new) - set(old)):
        changes.append(Change(name, "added", None, new[name], False))
    for name in sorted(set(old) & set(new)):
        if old[name] == new[name]:
            continue
        old_labels, new_labels = _labels(old[name]), _labels(new[name])
        grew = bool(new_labels - old_labels)
        changes.append(Change(name, "grew" if grew else "shrank",
                              old[name], new[name], grew))
    return changes


def has_breaking_change(changes: list[Change]) -> bool:
    return any(c.breaking for c in changes)
