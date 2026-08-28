# NOVA — Memory Model

Milestone 1. This document resolves the largest open risk on record:
[DESIGN-OPPORTUNITIES.md Theme B](../../research/DESIGN-OPPORTUNITIES.md#3-theme-b--ownership-scope-and-lifetime-are-one-mechanism)
predicted that choosing a memory discipline would force RFC 0001's
first-class capabilities into tension with second-class, non-escaping
ones, and flagged this as "the single largest structural risk in the
project." [RFC 0001 §11 open question 6](../../RFC/0001-core-capability-effects.md#11-open-questions)
made RFC 0001 provisional on this document existing. It now does; §7
resolves the tension, and RFC 0001's Revisions section records the
outcome.

Per the brief: **Rust's model is not assumed optimal.** §2 states
specific, concrete weaknesses in it before this document proposes
anything, and §7's design deliberately does not clone Rust's mechanism
where the research suggests a cheaper one exists.

---

## 1. What must be prevented, made precise

The brief lists five properties. Each needs an operational definition
before it can be checked against — "prevents use-after-free" is not
falsifiable until "use-after-free" is defined for NOVA specifically:

| Property | Operational definition for NOVA |
|---|---|
| Use-after-free | Reading or writing a value after the region that owns it has ended, or after the value has been moved. |
| Double-free | Deallocating a region's storage more than once — impossible if regions are deallocated exactly at scope exit, by construction, never by explicit call. |
| Invalid memory access | Reading a value through a reference whose region is not the one currently live for that memory — i.e., a stale or mistyped reference. |
| Dangling references | A reference that outlives the region (or, for a stack value, the frame) it points into. |
| Data races where the model promises race freedom | Two concurrent tasks holding write access, or one holding write while another holds read, to the same region at the same time. |

Every claim in [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md) is checked
against this table, row by row, with a test that would fail if the
claim were false.

---

## 2. Rust, evaluated honestly before anything is proposed

Rust is the strongest existing answer and the one every alternative in
this document is measured against. It is also not without real,
specific costs — stated here because the brief explicitly warns against
assuming it is automatically optimal, and because Constitution Article V
requires citing what exists rather than re-deriving it.

**What Rust gets right, unambiguously.** Ownership + borrowing gives
compile-time memory safety and data-race freedom with no runtime cost,
and the result has a machine-checked soundness proof — RustBelt (Jung,
Jourdan, Krebbers & Dreyer, POPL 2018). No other systems language has
both the guarantee and the proof.

**Specific, concrete costs, not "it's hard":**

1. **Self-referential structures are second-class.** A struct that
   holds a pointer into its own field cannot be moved safely; Rust's
   answer is `Pin`, a wrapper type with its own subtle rules that most
   Rust programmers avoid rather than learn. This is not a corner case —
   generators, some parser combinators, and intrusive linked structures
   all hit it.
2. **Graphs and back-references need to leave the ownership model.**
   `Rc<RefCell<T>>` (shared ownership + interior mutability, checked at
   run time) or arena-plus-integer-index patterns (ownership abandoned
   in favor of a flat array and hand-rolled "pointers") are both
   standard, both taught in every intermediate Rust resource, and both
   are ways of *opting out* of the feature that is supposed to be the
   point.
3. **The formal foundations shipped after the language.** Rust 1.0
   (2015) predates Stacked Borrows (Jung et al., 2020) — the first
   attempt at a precise aliasing model for `unsafe` code — by five
   years, and Stacked Borrows was superseded by Tree Borrows only
   recently. For half of Rust's public life, "what `unsafe` code is
   allowed to assume" did not have a settled answer. This is a genuine
   caution about shipping an ownership model before its edge cases are
   understood, not a criticism of Rust's engineering.
4. **Lifetime elision is large, useful, and partially opaque.** Most
   function signatures need no explicit `'a` because of elision rules —
   good for ergonomics, but it means a beginner's mental model is "the
   compiler does something with lifetimes I don't fully see," which
   directly contradicts NOVA's diagnostic-quality principle
   ([LANGUAGE-CONSTITUTION.md Principle 9](../foundation/LANGUAGE-CONSTITUTION.md#principle-9--ordinary-code-should-remain-simple)):
   a rule powerful enough to need elision to be tolerable is a rule
   whose full form is not simple.
5. **Mutability polymorphism doesn't exist, so APIs triple.**
   `iter()` / `iter_mut()` / `into_iter()` is not one generic method
   parameterized over "how much access" — it is three, hand-written,
   because Rust's type system has no way to abstract over
   shared-vs-exclusive-vs-owned access the way RFC 0001 already
   abstracts over effects with row variables. This is the same
   function-coloring problem
   ([PROBLEM-SPACE.md P5](../../research/PROBLEM-SPACE.md#p5--function-coloring-and-the-absence-of-effect-polymorphism))
   NOVA already solved once, in a different dimension, and it is worth
   noticing that Rust's ownership system has not solved its own version
   of it.

None of this makes Rust wrong. It makes "clone Rust" an unexamined
default rather than a decision, which is exactly what the brief warns
against.

---

## 3. The full comparison

Measured on the brief's own seven criteria. Scale: **●** strong / **◐**
partial or costly / **○** weak or absent, plus a short note on *why*.

### 3.1 Tracing garbage collection

| Criterion | Rating | Note |
|---|---|---|
| Safety | ● | No use-after-free or dangling references by construction; the collector never frees live memory. |
| Performance | ◐ | Throughput is competitive; latency is not — pause times are a real cost for anything with a tail-latency budget. |
| Compile time | ● | Nothing to check; this is the cheapest option at compile time by a wide margin. |
| Mental overhead | ● | Lowest of any option — "the runtime handles it" is the entire model. |
| Ergonomics | ● | No annotations anywhere. |
| FFI complexity | ◐ | Foreign code holding a pointer into GC'd memory across a collection cycle is the classic hazard; needs pinning or copying. |
| Concurrency | ○ | Buys nothing for data races; a GC prevents dangling pointers, not concurrent mutation. |

### 3.2 Reference counting (naive — Python-style)

| Criterion | Rating | Note |
|---|---|---|
| Safety | ◐ | No use-after-free for acyclic data; **cycles leak silently**, forever, with no diagnostic. |
| Performance | ○ | A retain/release on every copy and scope exit; worse cache behavior than tracing GC in practice. |
| Compile time | ● | Nothing to check. |
| Mental overhead | ◐ | "Everything is counted" is simple until cycles are involved, and then it is a silent correctness bug, not a checked one. |
| Ergonomics | ● | No annotations. |
| FFI complexity | ◐ | A foreign holder must increment the count; easy to get wrong silently. |
| Concurrency | ○ | Naive counting is not thread-safe without atomics, which cost performance exactly where RC was chosen to avoid GC pauses. |

### 3.3 ARC (Swift, Objective-C)

Refines 3.2: atomic counts, deterministic destruction, compiler-inserted
retain/release.

| Criterion | Rating | Note |
|---|---|---|
| Safety | ◐ | Same cycle problem as naive RC — Swift's answer is `weak`/`unowned`, opt-in and easy to omit. |
| Performance | ◐ | Deterministic (good for resource cleanup) but atomic traffic on every copy is real, measured overhead. |
| Compile time | ● | Nothing to check. |
| Mental overhead | ◐ | Cycle-breaking (`weak` vs `unowned`, and *which* one) is a real, non-mechanical judgment call every Swift programmer has to make correctly, by hand, with no compiler help. |
| Ergonomics | ● | Retain/release is invisible in source. |
| FFI complexity | ◐ | Bridging to/from unmanaged pointers (`Unmanaged<T>`) is a real, documented sharp edge. |
| Concurrency | ○ | Swift 6's data-race safety is a *separate*, later addition (region-based isolation, SE-0414) — ARC itself gives nothing here. |

### 3.4 Ownership + borrowing (Rust)

| Criterion | Rating | Note |
|---|---|---|
| Safety | ● | Machine-proven (RustBelt); the strongest guarantee on this list. |
| Performance | ● | Zero runtime cost; the annotation is the entire price. |
| Compile time | ◐ | Borrow-check adds real time; not the dominant cost of `rustc` builds but not free either. |
| Mental overhead | ○ | Named lifetimes, variance, elision rules — real, teachable, and still the most commonly cited reason engineers describe Rust as hard to learn. |
| Ergonomics | ○ | §2.2's `Rc<RefCell<T>>` retreat is the concrete cost. |
| FFI complexity | ◐ | `unsafe` at the boundary is well-understood *as a concept* but the aliasing rules inside it were unsettled for years (§2.3). |
| Concurrency | ● | `Send`/`Sync` give race freedom by construction — the other half of RustBelt's proof. |

### 3.5 Affine types (the theoretical category Rust's ownership instantiates)

Affine: a value may be used **at most once**; dropping without using is
allowed. This is the general term; Rust's ownership is one concrete
affine type system (Wadler 1990 names the category).

Evaluated as a category rather than repeated: affine typing is what
*makes* single ownership checkable at all — the same ratings as 3.4
apply to the underlying theory. The engineering choices that make Rust
specifically feel costly (named lifetimes, no mutability polymorphism)
are not forced by affinity itself — a different affine system could
choose differently, which is exactly what §7 does.

### 3.6 Linear types (Austral, Clean, linear Haskell)

Linear: a value must be used **exactly once** — stricter than affine
(no silent drop).

| Criterion | Rating | Note |
|---|---|---|
| Safety | ● | Strongest of any option: forgetting to release a resource is a compile error, not just a leak. |
| Performance | ● | Zero runtime cost, same as affine. |
| Compile time | ◐ | Similar to borrow-checking. |
| Mental overhead | ○ | Every linear value needs an explicit consuming use on every path, including error paths — more ceremony than affine's "drop is implicit and fine." |
| Ergonomics | ○ | Austral's own documentation describes this tradeoff directly; it is a real cost, accepted deliberately there for capability-safety reasons close to NOVA's own. |
| FFI complexity | ◐ | A linear capability crossing an FFI boundary must be explicitly consumed or explicitly leaked (documented, checked) — arguably *clearer* than Rust's `unsafe`, at the cost of more required ceremony. |
| Concurrency | ● | A linear value has exactly one owner at every point in the program, which is a stronger property than affine's "at most one" and composes at least as well with exclusivity-based race freedom. |

### 3.7 Region-based memory (Cyclone, ML-Kit/Tofte-Talpin, Vale, Verona)

| Criterion | Rating | Note |
|---|---|---|
| Safety | ● | No use-after-free (a reference cannot outlive its region, checked), no dangling references. |
| Performance | ● | Region deallocation is a bulk operation (often a single pointer bump backward), typically *faster* than per-object free. |
| Compile time | ◐ | Region-inference cost is real but the region graph is typically much smaller than a full per-value lifetime graph. |
| Mental overhead | ● | "Which region is this in, and is that region still open" is a coarser, shallower question than "does this specific reference's lifetime outlive that specific other one." |
| Ergonomics | ● | No per-value lifetime parameters; a function takes a region capability, not N lifetime-annotated references. |
| FFI complexity | ● | A foreign region (Vale's "Fearless FFI": isolate foreign data in its own region, never trust its internal aliasing, only ever hand it whole regions across the boundary) is a clean, checked story. |
| Concurrency | ● | Exclusive region access composes directly with race freedom (Verona's result) — a region is the natural unit of both memory ownership and concurrent isolation. |

### 3.8 Hybrids

**Compile-time reference counting (Perceus — Koka, Lean 4).** Static
analysis proves many retain/release pairs are redundant and elides them,
plus "functional but in place" (FBIP) reuse of dead allocations. Safety
●, performance ● (competitive with C in Perceus's own benchmarks for
functional-style code), mental overhead ● (looks like GC to the
programmer), ergonomics ●, but **assumes a mostly-immutable, functional
core** — NOVA's v0.2 language (Phase 2) is close to this shape already
(structs/enums are immutable except for the narrow, provably-safe `mut`
local case in RFC 0005), which is a real point in its favor worth
weighing against regions in §6.

**Generational references (Vale).** A fat pointer (address + generation
counter); freeing bumps the generation, so a stale reference's read is
caught at the point of use rather than prevented statically. Safety ●
*if* the check is never skipped (an unproven claim at Vale's current
scale — RESEARCH.md already flagged this), performance ◐ (a runtime
check per dereference, unlike regions' fully static story), mental
overhead ● (claimed to need no annotations at all), ergonomics ● in
theory. The claim is attractive and specifically unproven — recorded
honestly rather than adopted on faith.

**Reference capabilities (Pony).** A six-point lattice
(`iso`/`val`/`ref`/`box`/`tag`/...) tracked per reference, giving
compile-time data-race freedom for an actor model. Safety ●, performance
●, but mental overhead ○ — six annotations is a real, high floor, and
Pony's own adoption curve is evidence of the cost.

---

## 4. What NOVA's existing commitments already constrain

This is not a green-field choice. Four decisions already made in
Phases 0–2 rule out several rows above outright, and should narrow the
field before §5's scoring:

- **RFC 0001: capabilities are first-class values, with no ambient
  authority.** A memory model that requires *capabilities themselves* to
  become second-class (Effekt's route, and Theme B's original worry)
  would mean walking that decision back, not extending it — see §7 for
  how this document avoids that outcome.
- **Constitution Article III: explicitness ranks above ergonomics, but
  ergonomics still ranks above nothing.** This rules out naive RC's
  silent cycle leaks (an unchecked failure mode) but does not by itself
  mandate the *most* explicit option (linear types' exactly-once
  ceremony) if a cheaper option gives the same checked guarantee.
- **RFC 0005: `let mut` locals are already frame-scoped, non-escaping,
  and provably alias-free — with zero named-lifetime syntax.** This is
  a working existence proof, already shipped, that scope-based
  reasoning without per-value lifetime names is viable in NOVA
  specifically, not just in the abstract.
- **Thesis T2 (component boundaries, WASM Component Model target,
  [DESIGN-OPPORTUNITIES.md §4](../../research/DESIGN-OPPORTUNITIES.md#4-theme-c--boundaries-and-the-adoption-problem)).**
  A memory model whose FFI story is "isolate untrusted memory in its own
  region, hand off whole regions at a checked boundary" (Vale's framing)
  aligns with shared-nothing component linking; a model whose FFI story
  is "raw pointers, trust the C side" does not.

## 5. Scoring against NOVA's actual priorities

Constitution Article III's order — soundness, explicitness, safety,
security, performance, ergonomics, verifiability, portability,
interoperability, extensibility — applied as a filter, not a fresh
popularity contest:

| Model | Soundness | Explicitness | Safety | Perf | Ergonomics | Verdict |
|---|---|---|---|---|---|---|
| Tracing GC | ● | — | ● | ◐ (latency) | ● | Rejected: Constitution Article III(5), "no mandatory tracing GC in the core" |
| Naive RC / ARC | ◐ | ◐ | ◐ (cycles) | ◐ | ● | Rejected: cycle leaks are an *unchecked* failure, contradicting Article III(2) |
| Rust-style ownership + named lifetimes | ● | ● | ● | ● | ○ | Rejected as the *default*, not as unsound — §2's costs, and §4's `mut`-local precedent, both point at a cheaper option existing |
| Pure linear types (Austral-style, everywhere) | ● | ● | ● | ● | ○○ | Rejected as the *default for all data* — ceremony cost exceeds what most NOVA code needs; **retained for the narrow case in §7** |
| Perceus-style compile-time RC | ● | ◐ | ● | ● | ● | **Strong candidate** — see §6 |
| Regions (Vale/Verona-style) | ● | ● | ● | ● | ● | **Selected** — see §7 |
| Generational references (Vale) | ◐ (unproven) | ● | ◐ | ◐ | ● | Rejected for now: the central safety claim is not yet independently verified at scale |
| Reference capabilities (Pony) | ● | ● | ● | ● | ○ | Rejected: six-point lattice exceeds NOVA's ergonomics floor for a default |

## 6. Regions vs. Perceus — the real remaining choice

Both survive §5's filter. The deciding argument:

**Perceus assumes a mostly-immutable, mostly-functional core.** It is
extremely well matched to Koka and Lean 4, both of which are
functional-first. NOVA v0.2 (Phase 2) is *close* to this shape but not
committed to it — RFC 0005 already introduced frame-local mutation
specifically because "ordinary programming" needed it
([PROBLEM-SPACE.md P1](../../research/PROBLEM-SPACE.md#p1--memory-safety-still-costs-too-much-programmer-effort)'s
whole complaint is that memory safety without mutation-shaped ergonomics
is a hard sell). Perceus does not, by itself, give a story for
*heap-allocated, mutable, shared-nothing* data — exactly what a real
server or systems program needs (structs holding capabilities, per
§4's `Handler` example from RFC 0002).

**Regions give a direct answer to concurrency for free (§3.7), which
Perceus does not address at all.** Milestone 4 (concurrency) is
downstream of whatever Milestone 1 decides (Constitutional Principle 4);
regions are the only option in §5 that hands Milestone 4 a
data-race-freedom argument it does not have to invent separately.

**Regions are the option [RESEARCH.md](../../research/RESEARCH.md#r1--memory-safety)
and [COMPETITIVE-ANALYSIS.md](../../research/COMPETITIVE-ANALYSIS.md#3-memory-management-in-detail)
already flagged as the leading candidate**, on the same grounds: a
region is a thing that can be *handed over*, which is the same shape as
a capability, and NOVA already has a capability system to hand it
through.

**Decision: regions.** Perceus-style compile-time reference counting is
recorded as the strongest *alternative*, not a straw man — a future RFC
revisiting this decision should have to argue past §6, not past a
weaker case.

---

## 7. The design, and how it resolves Theme B

[DESIGN-OPPORTUNITIES.md Theme B](../../research/DESIGN-OPPORTUNITIES.md#3-theme-b--ownership-scope-and-lifetime-are-one-mechanism)
framed the risk as a forced choice: either capabilities stay first-class
(RFC 0001) and the memory model has no aliasing discipline to build on,
or memory needs second-class capabilities (Effekt's route) and RFC 0001
must be walked back.

**There is a third option, and it is what NOVA adopts: capabilities stay
uniformly first-class (no walk-back), and aliasing safety comes from
making *specific* capabilities — the ones that grant exclusive,
mutating access to a region — linear (§3.6), while every other
capability (including shared, read-only region access, and every
capability RFC 0001 already defined) stays exactly as first-class and
non-linear as it always was.**

This is not a new theoretical idea — Austral already combines
capabilities with linear types, cited in RFC 0001 §3 and
[RESEARCH.md §R4](../../research/RESEARCH.md#r4--capability-security). NOVA's specific
contribution is narrower and stated precisely: **linearity is applied
to one axis of the existing capability system (exclusive region access)
instead of to capabilities as a whole**, which is why RFC 0001's
authority-and-effects design needs no revision — see
[OWNERSHIP-MODEL.md](OWNERSHIP-MODEL.md) for the complete mechanism and
[TYPE-SYSTEM.md](TYPE-SYSTEM.md) for how it sits inside the type system
Phase 2 already built.

## 8. What this decides, and what it leaves open

**Decided:** regions as the unit of ownership; linear exclusive-access
capabilities; affine-by-default ordinary values (Rust's `Copy`/`Clone`
split, kept because it is uncontroversial, not reinvented); no named
lifetime syntax anywhere in NOVA source.

**Left open, explicitly, for later RFCs:** the exact region-inference
algorithm (whether regions are always lexically scoped or can be
inferred more flexibly, à la ML-Kit); whether a region can itself be
resized/grown; the interaction between regions and generics (a
`List[T]` where `T`'s region is itself generic) — flagged in
[OWNERSHIP-MODEL.md §7](OWNERSHIP-MODEL.md#7-open-questions) rather than
answered here.
