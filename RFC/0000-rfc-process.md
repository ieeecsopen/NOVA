# RFC 0000 — The RFC Process

- **Status:** Accepted
- **Created:** 2026-08-28
- **Supersedes:** —

## Why

The Constitution (Article VI) sets a bar for admitting features. This RFC
defines the mechanism that enforces it.

## When an RFC is required

An RFC is required for anything that changes:

- the surface syntax
- the type system or its inference
- the effect or capability model
- the memory model
- the module or package model
- the IR or ABI
- the Constitution itself

An RFC is **not** required for: bug fixes, diagnostics wording,
performance work with no semantic change, documentation, or tests.

If you are unsure, open an issue first. A rejected idea costs a day; a
merged mistake in the core costs the language.

## States

```
Draft ──> Review ──> Accepted ──> Implemented
   │         │
   └─────────┴──> Rejected / Withdrawn / Postponed
```

- **Draft** — being written, not yet asking for a decision.
- **Review** — open for comment. Minimum 14 days.
- **Accepted** — the design is agreed. Implementation may begin.
- **Implemented** — landed, with tests, spec text, and docs.
- **Rejected** — kept in the tree with the reason recorded. Rejected RFCs
  are valuable; they stop the idea from being re-proposed annually.

## Required sections

Every RFC must contain, in this order:

1. **Summary** — one paragraph.
2. **Problem** — a concrete program that is impossible, unsafe, or
   unreasonably awkward today. Real code, not a hypothetical.
3. **Prior art** — how Rust, Koka, Pony, Swift, Haskell, TypeScript, and
   any directly relevant system solve this. Cite specifics. "X doesn't do
   this well" is not prior art; say what X does and where it breaks.
4. **Design** — syntax, static semantics, dynamic semantics. Precise
   enough that two people could implement it and agree.
5. **Examples** — including at least one that the design *rejects*, with
   the diagnostic the compiler should produce.
6. **Alternatives** — including "do nothing", argued honestly.
7. **Tradeoffs** — what gets worse. Every RFC makes something worse. An
   RFC claiming no downside has not been thought through.
8. **What this forecloses** — designs that become unavailable if this is
   accepted.
9. **Costs** — compile time, run time, binary size, reader effort.
10. **Staging** — the smallest shippable subset, and what is deferred.
11. **Open questions** — unresolved issues, explicitly listed.

## The reviewer's obligation

A reviewer must attempt to answer, in writing:

- Can this be simpler?
- Can this be a library instead of a language feature?
- What breaks if we are wrong?

An approval with no answer to those three is not an approval.

## Numbering

RFCs are numbered sequentially at the time they enter **Review**, not when
drafted. Drafts live at `RFC/draft-<slug>.md`.

## Amending an accepted RFC

Small corrections: edit in place, note it in a `## Revisions` section.
Semantic changes: a new RFC that supersedes the old one. The old RFC stays,
marked `Superseded by NNNN`.
