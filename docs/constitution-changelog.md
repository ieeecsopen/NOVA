# Constitution changelog

Constitution Article I requires every change to this project's governing
document to be recorded here, with the reason.

## 2026-08-28 — initial adoption

Articles I–XII adopted as the founding document. No prior version.

Two choices in the initial text are worth flagging as *decisions*, not
inherited defaults, because they are the ones most likely to be revisited:

- **Article III places ergonomics sixth**, below explicitness and
  security. This is the article that will be argued about, and it is the
  one that makes NOVA's error messages strict (`E0202` in particular).
- **Article IV names only three properties as core** — effects,
  authority, memory. Everything else is declared additive. If a fourth
  turns out to be non-retrofittable, that is a Constitution amendment,
  not a feature RFC.

## 2026-08-28 — Article II superseded (Phase 1)

Phase 1's brief was explicit: challenge the program model, improve it
where research shows a better abstraction. It did:

- **Capabilities, Effects, and Resources are not independent peers.**
  [DESIGN-OPPORTUNITIES.md Theme A](../DESIGN-OPPORTUNITIES.md#2-theme-a--obligations-are-one-mechanism),
  tested by [Experiments 001–003](experiments/), found they are one
  mechanism (a row) at increasing precision.
- **Verification is not a peer ingredient** — it is an axis (the
  Guarantee ladder, [LANGUAGE-PHILOSOPHY.md entry 10](../LANGUAGE-PHILOSOPHY.md#10-guarantee))
  that attaches to every `Constraint`, not a separate thing to build.
- **Uncertainty is a property of values**, not of programs — demoted to
  a note ([RESEARCH.md §R10](../RESEARCH.md#r10--uncertainty),
  [NON-GOALS.md §2.4](../NON-GOALS.md#24-uncertainty-as-a-language-feature)).
- **Execution Strategy has no operational content** and is kept only as
  an explicitly open slot, per Article VIII, with one binding constraint
  (meaning-preservation) stated in advance of any design.

Full argument: [PROGRAM-MODEL.md](../PROGRAM-MODEL.md). Article II now
carries the original model, marked superseded, and the revised one, so
the amendment is auditable rather than silently overwritten.

This is a **model refinement**, not a reversal: nothing the original list
could express is lost, and RFC 0001 required no change (verified — the
conformance suite passed unmodified before and after this amendment).

## 2026-08-28 — Article XI satisfied (Milestone 1)

Article XI has bound the core since the founding document: no
unrestricted aliasing, no GC, until a memory discipline exists. Phase 3
designed one — [MEMORY-MODEL.md](../MEMORY-MODEL.md) selects
region-based ownership over GC, reference counting, ARC, and Rust-style
per-value lifetimes, on the brief's own explicit instruction not to
assume Rust's model is optimal; [OWNERSHIP-MODEL.md](../OWNERSHIP-MODEL.md)
works the mechanism out precisely enough to implement, and does
implement it, in [`regionlab/`](../regionlab/), with negative tests for
every property the brief required (use-after-free, double-free, invalid
access, dangling references, data races).

The article's text is left unchanged (its restriction remains binding on
whatever the memory model does not yet cover) with a note added pointing
to the design that satisfies it — the same non-destructive pattern used
for Article II's amendment.
