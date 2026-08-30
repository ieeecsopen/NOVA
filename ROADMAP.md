# NOVA — Roadmap

Dates are deliberately absent. Each milestone gates the next; a milestone
is done when its exit criteria are met, not when a date arrives.

## Phase 0 — Research *(complete)*

**Question:** what are the real unsolved problems, and which of them share
a mechanism?

- [x] [PROBLEM-SPACE.md](research/PROBLEM-SPACE.md) — 24 problems, assessed
- [x] [COMPETITIVE-ANALYSIS.md](research/COMPETITIVE-ANALYSIS.md) — 20 languages, 5 systems
- [x] [RESEARCH.md](research/RESEARCH.md) — 21 areas, findings graded by maturity
- [x] [DESIGN-OPPORTUNITIES.md](research/DESIGN-OPPORTUNITIES.md) — themes and 5 ranked theses
- [x] [NON-GOALS.md](docs/foundation/NON-GOALS.md) — what NOVA will not attempt

**Outputs that changed existing work:**

1. RFC 0001's novelty claim was **withdrawn** — Effekt (OOPSLA 2020/2022)
   is prior art for "effects as capabilities". The RFC is now an
   engineering RFC. This is Article V working as intended.
2. Two new open questions on RFC 0001: whether the memory model forces
   second-class capabilities (§11.6), and whether rows should be graded
   (§11.7).

**Decisions still open, for the maintainer:**

- **Thesis.** DESIGN-OPPORTUNITIES §8 recommends T1 (the obligation row)
  as the technical thesis with T2 (capability-safe components) as its
  expression and adoption path. Not yet adopted.
- **Two experiments recommended for early promotion**, because they
  falsify the thesis in days rather than milestones: rows → trace spans
  (P21) and capability manifests (P14). Both currently sit in
  Milestones 2–5.
- **WebAssembly Component Model** as an explicit Milestone 3 commitment
  rather than one option, since it is the only credible incremental
  adoption path (P24) and it constrains the IR choice.

## Phase 1 — Constitution *(complete)*

**Question:** what does NOVA fundamentally believe, independent of
syntax?

- [x] [LANGUAGE-PHILOSOPHY.md](docs/foundation/LANGUAGE-PHILOSOPHY.md) — 12 term definitions
- [x] [PROGRAM-MODEL.md](docs/foundation/PROGRAM-MODEL.md) — the program model, challenged and revised
- [x] [LANGUAGE-CONSTITUTION.md](docs/foundation/LANGUAGE-CONSTITUTION.md) — 12 semantic principles, each with a checkable status
- [x] [DESIGN-PRINCIPLES.md](docs/foundation/DESIGN-PRINCIPLES.md) — the six-tier feature hierarchy
- [x] [ARCHITECTURAL-GOALS.md](docs/foundation/ARCHITECTURAL-GOALS.md) — six implementation invariants
- [x] [CONSTITUTION.md](CONSTITUTION.md) Article II amended to the revised model (non-breaking: RFC 0001 and the conformance suite unaffected)

**What Phase 1 leaves open, for the maintainer or a future RFC:**

- Whether retry-safety labels (P10) belong in the standard library or
  require a type-system change — [DESIGN-PRINCIPLES.md](docs/foundation/DESIGN-PRINCIPLES.md#worked-classification-twelve-items-from-phase-0)
  records this as genuinely undecided rather than forcing a tier.
- No syntax has been designed for anything in this phase, per its scope.
  Phase 2 (not yet started) is where surface syntax begins, gated by
  [DESIGN-PRINCIPLES.md](docs/foundation/DESIGN-PRINCIPLES.md)'s hierarchy and
  [LANGUAGE-CONSTITUTION.md](docs/foundation/LANGUAGE-CONSTITUTION.md)'s principles.

## Phase 2 — Core Language *(complete)*

**Question:** can NOVA express ordinary, ordinary-feeling programs —
structs, enums, generics, traits, modules, mutation, a real collection —
without contradicting anything Phases 0–1 established?

- [x] [RFC 0002](RFC/0002-structs-tuples-enums-pattern-matching.md) —
      structs, tuples, enums, pattern matching; resolves RFC 0001 §11.3
- [x] [RFC 0003](RFC/0003-generics-and-traits.md) — generics and traits
- [x] [RFC 0004](RFC/0004-modules-and-imports.md) — modules and imports
- [x] [RFC 0005](RFC/0005-local-mutability-and-loops.md) — local
      mutability and loops, safe without a memory model
- [x] [SYNTAX.md](docs/language/SYNTAX.md), [TYPE-SYSTEM.md](docs/language/TYPE-SYSTEM.md),
      [LANGUAGE-REFERENCE.md](docs/language/LANGUAGE-REFERENCE.md)
- [x] The reference implementation extended end to end (lexer through
      evaluator) — every example below actually runs, not just parses
- [x] `std/option.nova`, `std/result.nova`, `std/list.nova` — written in
      ordinary NOVA, no compiler special-casing
- [x] 24 example files (22 complete programs + a library module + a
      deliberately-rejected file), all checked and run in CI
- [x] 20 new conformance tests (026–045), on top of the existing 25

**What Phase 2 found, corrected in the process rather than after:**

- A real soundness gap in the type-checker's own unification (rigid vs.
  flexible type-variable ordering) — found by a real generic program,
  fixed, and now load-bearing (RFC 0003 §3.1).
- A real soundness gap between a trait's declared contract and an
  `impl`'s own text (`E0127`) — closed before it could ship silently
  (RFC 0003 §5.1).
- A real aliasing hazard in `mut` locals plus closures — closed by
  `E0130` before implementing the runtime representation that would
  have made it exploitable (RFC 0005 §3.1).
- RFC 0001 §11.3 ("what is the row of a stored capability?") is
  answered: nothing new. See RFC 0002 §3.

**What Phase 2 leaves open, by design:**

- No explicit generic instantiation syntax, no conditional trait impls,
  no trait objects, no mutable fields, no qualified import paths — six
  named limitations (`docs/known-issues.md` P1–P6), each argued rather
  than hidden.
- Whether retry-safety labels (P10, from Phase 1) belong in the standard
  library or need a type-system change is still undecided.

## Phase 3 — Type System and Memory Model *(designed and prototyped)*

**Question:** how does NOVA manage memory, and does the answer force a
redesign of RFC 0001's capability system, as
[DESIGN-OPPORTUNITIES.md Theme B](research/DESIGN-OPPORTUNITIES.md#3-theme-b--ownership-scope-and-lifetime-are-one-mechanism)
warned it might?

- [x] [MEMORY-MODEL.md](docs/language/MEMORY-MODEL.md) — GC, RC, ARC, ownership +
      borrowing, affine types, linear types, regions, and hybrids,
      compared against Rust specifically and scored against NOVA's own
      priorities, not assumed in advance
- [x] [OWNERSHIP-MODEL.md](docs/language/OWNERSHIP-MODEL.md) — regions as capabilities,
      linear exclusive-access, no named lifetime syntax
- [x] [TYPE-SYSTEM.md](docs/language/TYPE-SYSTEM.md) §§11–14 — ownership types,
      mutability, Send/Share, aliasing, extending Phase 2's document
- [x] [SAFETY-GUARANTEES.md](research/SAFETY-GUARANTEES.md) — every claim at an
      explicit Guarantee-ladder strength, mapped to a named test
- [x] [`regionlab/`](regionlab/) — a small standalone prototype checker,
      14 tests, including a negative test for every required property
      (use-after-free, double-free, invalid access, dangling references,
      data races) plus the Send/Share derivation

**The headline result:** Theme B's forced choice — first-class
capabilities *or* a working memory model, not both — was not actually
forced. NOVA keeps every capability first-class (RFC 0001 unmodified)
and applies linearity to one specific capability kind (exclusive region
access) rather than to capabilities as a whole. This is Austral's
combination of capabilities and linear types (already cited in RFC 0001
§3), applied narrowly rather than adopted wholesale — not a novel
theoretical idea, but a specific, argued choice about *where* to apply
an existing one.

**What Phase 3 leaves open, named rather than hidden:**

- `regionlab` is a prototype, not an integration — Phase 2's shipped
  v0.2 checker and its 45 conformance tests are untouched by this phase.
- Five open questions in
  [OWNERSHIP-MODEL.md §7](docs/language/OWNERSHIP-MODEL.md#7-open-questions): field-level
  exclusivity splitting, region resizing, generics over region-ness,
  interaction with graded rows, non-lexical region inference.
- No second independent implementation yet (Constitution Article IX) —
  `regionlab` is the first.
- Constitution Article XI is satisfied by this design but the article's
  text is deliberately left in place, not deleted, per this project's
  standing practice for amendments (see Article II's own precedent).

## Milestone 0 — Foundation *(current)*

**Question:** is the core idea coherent enough to specify?

- [x] Constitution, Vision, Architecture
- [x] RFC process (RFC 0000)
- [x] RFC 0001 — capability-derived effects, in Review
      *(novelty claim withdrawn after Phase 0; see its §3.2)*
- [x] Executable reference semantics: lexer, parser, capability
      reachability, type + effect checker, evaluator
- [x] Conformance suite (47 tests)
- [x] Prelude capabilities: `Runtime`, `Clock`, `Filesystem`, `Network`
- [x] First-order native C backend + interpreter-backed fallback for the
      rest (`nova build`)
- [x] Toolchain benchmark harness (`benchmarks/challenge_suite.py`) —
      wall-clock only; the language-level cost measurements RFC 0001 §9
      wants still need a native code path
- [ ] Rust compiler front end (second implementation) — blocked on toolchain
- [ ] RFC 0001 open questions §11.1 / §11.2 (does effect derivation
      survive abstraction?) — the gate that keeps Milestone 0 open

**Exit:** RFC 0001 Accepted, a second implementation agreeing on the
conformance suite, and §11.1 answered.

> **Note on the "1.0 Genesis" commits.** An earlier series of commits
> tagged a `v1.0.0` release and rewrote the README and several docs in
> the voice of a finished platform. That was inaccurate — see
> [CONSTITUTION.md](CONSTITUTION.md) Article XII. The 0.2 honesty pass
> re-scoped the version, the README, the benchmarks, and added a status
> banner to the affected design documents. The tag is retained for
> history but does not denote a real 1.0.

## Milestone 1 — Memory discipline *(designed and prototyped)*

**Question:** how does NOVA manage memory without a tracing GC, and does
that choice break the effect model?

**Answered:** region-based ownership, with linearity applied to
exclusive-region-access capabilities only —
[MEMORY-MODEL.md](docs/language/MEMORY-MODEL.md) (research and decision),
[OWNERSHIP-MODEL.md](docs/language/OWNERSHIP-MODEL.md) (mechanism),
[SAFETY-GUARANTEES.md](research/SAFETY-GUARANTEES.md) (precise, tested claims),
validated in [`regionlab/`](regionlab/) — a small standalone prototype
checker, not merged into `verifier/refspec/`, with negative tests for
every required property.

**Does not break the effect model:** RFC 0001's derivation rule needed
no revision — see the RFC's own Revisions section and
[DESIGN-OPPORTUNITIES.md Theme B](research/DESIGN-OPPORTUNITIES.md#3-theme-b--ownership-scope-and-lifetime-are-one-mechanism)'s
resolution note. Constitution Article XI is now satisfied by
construction, not merely respected by omission.

**What remains before this milestone is fully closed:**

- Integration into `verifier/refspec/`'s shipped v0.2 checker
  (`regionlab` is deliberately separate; Phase 2's 45 conformance tests
  and 24 examples are unmodified by this phase).
- The five open questions in
  [OWNERSHIP-MODEL.md §7](docs/language/OWNERSHIP-MODEL.md#7-open-questions):
  field-level exclusivity splitting, region resizing, generics over
  region-ness, interaction with graded rows, non-lexical region
  inference.
- A second, independent implementation (Constitution Article IX) —
  `regionlab` is the first, not yet the confirming second.

**Exit (revised):** the mechanism above is designed and prototype-tested;
full exit requires the integration and second-implementation work listed
above.

## Milestone 2 — Abstraction

Generics, interfaces/protocols, modules, and the answer to RFC 0001 §11.1
and §11.3 (rows of stored capabilities). Blocks `std`.

**Exit:** a non-trivial `std` prelude written in NOVA itself.

## Milestone 3 — Compilation

The IR (undecided), then native codegen, then WebAssembly. Bootstrapping
does not begin before this milestone completes.

**Exit:** `nova build` produces a native binary and a `.wasm` module from
the same source, and the conformance suite passes on both.

## Milestone 4 — Concurrency

Structured concurrency, effect-typed. Data-race freedom must fall out of
Milestone 1's memory discipline, not be bolted on beside it.

## Milestone 5 — Resources

Resource budgets (allocation, time, syscalls) as checked constraints.
This is the first milestone that tests whether the "constraint-native"
thesis extends past effects — if budgets do not reduce to the existing
effect machinery, the thesis is weaker than claimed and the docs say so.

**Corrected by [experiment 003](docs/experiments/003-graded-rows.md):**
grading cannot be a syntactic pass added after the type checker runs. It
must be part of row unification itself, with grades carried on row
*variables* and resolved at instantiation — otherwise it does not survive
row polymorphism, which `with_retry` (RFC 0001 §2, the language's own
motivating example) immediately exercises. Milestone 5 now starts with a
type-system RFC, not a pass.

## Milestone 6 — Contracts and verification

Opt-in refinement types and contracts, discharged by an SMT backend.
Prior art: Dafny, F\*, Liquid Haskell, SPARK. Layered — a program that
uses none of it pays nothing, including in compile time.

## Milestone 7 and beyond — the deferred agenda

Distribution, adaptive execution strategy, uncertainty, AI/agent
integration.

These appear in the Vision and are **not scheduled**. Constitution
Article VIII: they do not get syntax until they have an operational
semantics, and each must either reduce to effects/capabilities/resources
or justify a new core mechanism.

## Self-hosting

NOVA v0 compiler in Rust → NOVA v1+ compiler in NOVA. Not before
Milestone 3, and not a goal in itself.

## What is explicitly not on this roadmap

- A web framework
- A package registry
- Marketing before 1.0
- Any feature whose justification is that another language has it
