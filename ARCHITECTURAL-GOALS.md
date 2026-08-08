# NOVA — Architectural Goals

Phase 1 output. **This document is not [ARCHITECTURE.md](ARCHITECTURE.md).**
That document describes the compiler pipeline that exists *today* — lex,
parse, resolve, check, and the reference/Rust split. This document states
the invariants that must hold of **any** implementation of NOVA, present
or future, native or otherwise — the goals the pipeline in
ARCHITECTURE.md is one attempt to satisfy, not a description of what it
currently does.

Each goal is drawn from a specific finding in Phase 0/Phase 1, not
asserted from scratch, and each states what would falsify it.

---

## Goal 1 — Semantic portability

**Statement.** Two conforming NOVA implementations, or one implementation
targeting two backends, must agree on every **Guarantee**
([LANGUAGE-PHILOSOPHY.md entry 10](LANGUAGE-PHILOSOPHY.md#10-guarantee))
a program has — the same effect row must mean the same authority, the
same type must mean the same values, regardless of target. This is
Constitutional Principle 8 restated as an architectural obligation on the
compiler and runtime rather than a promise about the language.

**Why.** [RESEARCH.md §R16](RESEARCH.md#r16--webassembly-wasi-and-the-component-model)
found the WebAssembly Component Model already provides a formally
specified capability boundary (WIT, the canonical ABI); thesis T2 commits
NOVA to targeting it rather than a bespoke ABI. A bespoke ABI would make
this goal a matter of NOVA's own, unverified discipline; targeting an
external formal semantics makes it checkable against someone else's
specification too.

**Already satisfied, at the smallest possible scale.** Constitution
Article IX's two-implementation requirement is this goal in miniature:
the reference semantics (`verifier/refspec`) and the (unstarted) Rust
compiler are required to agree on every conformance test precisely
because "two implementations of NOVA" is the smallest instance of "two
targets of NOVA."

**Falsified by:** a program whose effect row checks differently, or whose
capability grants different authority, depending on whether it runs
through `verifier/refspec` or (eventually) the Rust compiler, with no
diagnostic explaining the divergence as a specification bug.

---

## Goal 2 — One front end, not two

**Statement.** The architecture must be demand-driven (query-based) from
its first implementation, so that an editor-integration tool (LSP,
formatter) can share the compiler's actual analysis rather than
reimplementing it.

**Why.** [RESEARCH.md §R17](RESEARCH.md#r17--incremental-compilation) and
[COMPETITIVE-ANALYSIS.md §6](COMPETITIVE-ANALYSIS.md#6-compilation-ir-and-tooling)
both single out the same cautionary tale: rustc shipped as a batch
pipeline, rust-analyzer had to be built as a second front end to get
incremental, error-tolerant analysis, and the two now drift and duplicate
bugs. Roslyn and Unison avoided this by deciding the architecture before
the first release. This goal exists so NOVA does not get to choose
between "batch compiler" and "IDE support" after the fact — the choice is
made now, before there is a second front end to build.

**Status.** Already recorded as binding in
[ARCHITECTURE.md](ARCHITECTURE.md#design-constraints-on-the-compiler-for-when-it-is-written);
this document elevates it from an implementation note to a goal any
future rewrite must also satisfy, because it is expensive specifically
to retrofit (same shape of argument as Constitution Article IV, applied
to tooling architecture rather than language semantics).

**Falsified by:** an LSP or formatter that reimplements parsing, name
resolution, or the capability-reachability pass independently of the
compiler's own query graph.

---

## Goal 3 — The escape hatch is always counted

**Statement.** Whatever mechanism exists for leaving the checked
fragment of the language (today: nothing; eventually: FFI, and per RFC
0001 §4.6, attenuation) must be enumerable by tooling across an entire
dependency graph, not merely visible at each individual site.

**Why.** [PROBLEM-SPACE.md P2](PROBLEM-SPACE.md#p2--escape-hatches-are-unbounded-and-unaudited)
found that Rust's `unsafe` is visible per-block but not summable across a
dependency graph — nobody computes the total trusted surface of a real
program, because no tool is positioned to. [SECURITY.md](SECURITY.md)
already admits attenuation is a trust boundary; this goal is what makes
that boundary auditable rather than merely documented. It generalizes the
mechanism [Experiment 001](docs/experiments/001-capability-manifests.md)
already demonstrated for ordinary capability growth to the strictly more
dangerous case of capability-dropping constructs.

**Status.** Aspirational — attenuation itself is not implemented
(known issue I5). Recorded now so that when it is, an audit listing (per
RFC 0001 §4.6's own text: "`nova check` reports every `attenuate` site")
is a launch requirement, not a follow-up.

**Falsified by:** any future escape hatch — an `unsafe` block, an FFI
boundary — that ships without a corresponding tooling-tier count.

---

## Goal 4 — Tooling never outruns the checker

**Statement.** No tool (formatter, manifest differ, tracer, linter) may
report a property of a program that the checker has not itself
established. A tool may *use* checked information more richly than the
checker's own diagnostics do; it may never *infer independently* and
present the result as checked.

**Why.** [Experiment 003](docs/experiments/003-graded-rows.md) is the
cautionary tale that motivates this goal, produced inside this project
rather than observed elsewhere: an early version of the grading pass
inferred a bound the checker had not established (`{}` for a function
whose real cost depended on an unresolved closure) and presented it as
sound. The fix — a distinct `UNKNOWN` state — is this goal enforced by
one bug report against the project's own tooling. This goal exists so the
next tool (a linter, a future budget-checker) is required to make the
same distinction from the start rather than rediscover it.

**Status.** Met by the grading experiment after correction; not yet
stated as a general obligation on tooling before this document.

**Falsified by:** any tool whose output could lead a user to trust an
unchecked claim as a checked one, without the tool itself marking the
distinction.

---

## Goal 5 — Adoption does not require a trusted hole

**Statement.** It must be possible to introduce NOVA into an existing
codebase one module at a time, without any boundary crossing that is
*less* checked than NOVA's own capability model — i.e., without the
equivalent of an untyped C FFI escape that silently grants full ambient
authority to foreign code.

**Why.** [PROBLEM-SPACE.md P24](PROBLEM-SPACE.md#p24--new-languages-cannot-incrementally-take-over-a-codebase)
identifies incremental adoptability as the axis most language projects
actually die on, independent of technical merit — TypeScript won this way
and Ur/Web/Links, technically excellent, did not.
[SECURITY.md](SECURITY.md) already admits NOVA's own FFI, whenever it
exists, will be exactly the kind of hole this goal warns against, unless
the Component Model's shared-nothing linking is used as the adoption
boundary instead of a raw C ABI (thesis T2).

**Status.** Aspirational — no module system, no FFI, no Component Model
target exists yet (Milestone 2–3). Recorded here so the eventual FFI
design is reviewed against this goal specifically, rather than accepted
as a necessary evil by default.

**Falsified by:** a NOVA release whose only interop story is an untyped C
FFI with no capability accounting at the boundary.

---

## Goal 6 — Self-hosting is a consequence, not a target

**Statement.** The compiler is written in Rust until NOVA itself is
stable enough that rewriting the compiler in NOVA is a good stress test
of the language, not before. Self-hosting is never scheduled as a
milestone in its own right.

**Why.** [NON-GOALS.md §2.5](NON-GOALS.md#25-self-hosting) already states
this as a non-goal; this entry exists so the *architecture* — not just
the roadmap — treats self-hosting as an emergent property to check for
later, rather than a constraint on early design decisions (e.g., never
choosing an IR or calling convention "because the self-hosted compiler
will need it" before Milestone 3 exists).

**Falsified by:** any Milestone 0–3 design decision whose stated
justification is self-hosting rather than the milestone's own goal.

---

## Relationship to the other Phase 1 documents

- [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md) defines the vocabulary
  these goals use (Guarantee, Row, Constraint).
- [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md) states what must be
  true of the *language*; this document states what must be true of any
  *implementation* of it. Principle 8 (semantic portability) and Goal 1
  are the same requirement viewed from each side.
- [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md)'s tiers classify
  *features*; these six goals constrain the *system* those features are
  built inside of, regardless of which tier a given feature sits in.
- [ARCHITECTURE.md](ARCHITECTURE.md) is the current, concrete attempt to
  satisfy these goals. When the two disagree, this document wins and
  ARCHITECTURE.md needs an update — not the reverse.
