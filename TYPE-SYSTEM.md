# NOVA — Type System

Phase 2 output: the type system for v0.2 (RFC 0001–0005), and the
research questions the brief asked to be investigated — nominal vs.
structural typing, inference, variance, generics, type aliases, coercion
— each answered as a decision, not a survey.

**§§11–14 are Phase 3 (Milestone 1) additions**: ownership types,
mutability, Send/Share, and aliasing, extending this document rather
than replacing it — the value type system Phase 2 built (§§1–10) is
unchanged by Milestone 1's memory model, exactly as
[OWNERSHIP-MODEL.md §6](OWNERSHIP-MODEL.md#6-interaction-with-phase-2s-type-system)
argues.

## 1. The type formers

```text
primitive types    Int, Bool, String, Unit
capability types    one per `capability` declaration (RFC 0001 §4.1)
struct types        nominal, RFC 0002 §4.1
tuple types          structural, RFC 0002 §4.2 — the one exception
enum types           nominal tagged unions, RFC 0002 §4.3
function types      (T, ...) -> T [! Row], RFC 0001 §4.2
generic types        struct/enum/function, parameterized, RFC 0003
```

There is no subtyping anywhere in this list, and no inheritance. This is
not an omission awaiting a follow-up RFC — it is a load-bearing
simplification, argued in §3.

## 2. Nominal vs. structural

**Decision: nominal for everything with a name (structs, enums,
capabilities); structural only for the one type former that has no
name to be nominal *about* (tuples).**

The argument, stated once so it need not be re-litigated per type
former: two types with identical shape are not necessarily the same
concept. `struct Meters { value: Int }` and `struct Count { value: Int }`
are shape-identical and semantically unrelated; a structural type system
would accept one wherever the other is expected, silently. NOVA's
priority order (Constitution Article III: explicitness above
ergonomics) rules this out for anything a programmer bothered to name.

[COMPETITIVE-ANALYSIS.md](COMPETITIVE-ANALYSIS.md) already documents the
cautionary case directly: TypeScript's structural typing is described
there as "unsound by design" — accepted deliberately, for a reason
(gradual adoption of untyped JavaScript) that does not apply to NOVA,
which has no legacy untyped corpus to be gradual about.

Tuples are the deliberate exception because an anonymous product
genuinely has no identity beyond its shape — `(Int, Bool)` *is*
"an Int and a Bool, in that order," with nothing else it could mean.
Rust, Swift, and OCaml all make the identical choice (nominal structs,
structural tuples), so this is confirmed practice, not a novel
position.

## 3. No subtyping — the simplification this buys

Java's covariant arrays are the standard cautionary tale: `Object[] xs =
new String[1]; xs[0] = 5;` typechecks and throws `ArrayStoreException`
at run time, because array covariance was unsound and the language
shipped it anyway. Kotlin's declaration-site variance
(`out`/`in` on type parameters) is the mature fix, and it is real
complexity — a whole sublanguage of variance annotations, with rules
for when they are and are not allowed to appear.

NOVA v0.2 has no subtyping of any kind — not between structs, not
between enums, not between generic instantiations (`List[Int]` and
`List[Object]`-if-it-existed are unrelated; there is no `Object`
supertype to relate them through in the first place), not for function
types beyond the exact effect-row equality RFC 0001 already requires.

**Consequence for variance:** the entire variance question — is
`List[Cat]` a `List[Animal]`? — does not arise, because there is no
notion of `Cat` being an `Animal` to begin with. This is not "variance
deferred"; it is variance made moot by a prior, more fundamental
decision. If NOVA ever adds interface-style subtyping (a real
possibility — traits are structurally close to interfaces already),
variance becomes a live question again, and Kotlin's declaration-site
model is the one to study first.

## 4. Inference

**No global (Hindley-Milner-style) inference.** Every binder — function
parameters, `let` (optionally), lambda parameters — is annotated. This
was already true in v0.1 and is unchanged: Constitution Article III
ranks explicitness above ergonomics, and RFC 0001 already made the more
consequential version of this call (no ambient inference of *effects*,
only of the row's internal unification).

**Local, bidirectional inference does exist**, at exactly the points RFC
0001 already established for row variables, now extended to type
variables (RFC 0003 §3):

- a generic function's type parameters are inferred from **argument
  types at the call site** (`identity(5)` infers `T = Int` by unifying
  the parameter type against the argument's inferred type) — no
  separate inference algorithm, the same `unify_types` RFC 0001 always
  had, now handling `TVar` as well as row tails.
- a generic struct/enum's type arguments are inferred the same way from
  constructor arguments (`Point { x: 1 }`, `Option::Some(5)`).
- a `let` binding's type is inferred from its initializer when no
  annotation is given (unchanged from v0.1).

What is **not** inferred: a function's own parameter or return types
(always written), and effect rows (RFC 0001 §4.3 — always checked for
equality against what the body actually does, never inferred and
accepted silently).

## 5. Generics

Full design and rationale: [RFC 0003](RFC/0003-generics-and-traits.md).
Summary of the type-system-relevant decisions:

- one `[...]` binder, classified by usage into type parameters and row
  parameters (SYNTAX.md §3.1);
- instantiation only by argument-type inference, never by explicit
  type-argument syntax (a v0.2 scope decision, not a design limit);
- a bound (`T: Trait`) restricts what a rigid type variable may do
  *inside* the generic function's own body (call a trait method on it);
  it says nothing about subtyping, because there is none (§3).

## 6. Traits

Full design: [RFC 0003 §5](RFC/0003-generics-and-traits.md#5-design-traits).
A trait is a set of required method signatures; an `impl` provides
bodies for one concrete type. Traits are the closest thing NOVA v0.2 has
to an interface, and deliberately do not carry any of the following
interface features yet: default methods, trait objects, supertraits,
associated types. Each is a plausible, separate future RFC.

## 7. Type aliases

```nova
type UserId = Int;
```

A **structural** alias: `UserId` and `Int` are the same type, and
NOVA's checker treats them identically (no new nominal identity is
created). This is the one place NOVA is unopinionated in a way that
looks, at first glance, inconsistent with §2's nominal stance — resolved
by noting that an alias declares no new *concept*, only a new *name for
an existing one*, which is exactly why it should not create a new
nominal boundary. A `struct UserId { value: Int }` remains the tool for
"this Int means something specific and should not be substitutable for
a bare Int" — the alias is for readability, not for distinctness.

**Status: designed here, not implemented in v0.2's reference semantics.**
No example in this phase's 20+ requires it; recorded as a small, safe,
deferred addition rather than built speculatively ahead of a real need.

## 8. Coercion

**NOVA has zero implicit coercions**, of any kind, including numeric
widening. `Int` is never silently treated as anything else. Every
conversion is an explicit function call.

This is not a gap — it is Rust's stance, adopted for the same reason
Rust adopted it: implicit numeric conversion is a well-documented source
of silent bugs in C-family languages (a `long` truncated into an `int`
at a call boundary, signed/unsigned comparison surprises), and
Constitution Article III ranks explicitness above the convenience
coercion buys. `Float` does not exist yet in v0.2 (no example in this
phase's 20+ needed it); when it is added, `Int -> Float` will be an
explicit function (`Int.to_float(x)`), not an implicit rule, by the same
argument, decided in advance rather than revisited under pressure later.

## 9. Effect rows, restated in type-system terms

An effect row is not a separate mini-language bolted onto the type
system — it is a **field of every function type**, unified by the same
`Subst` object as everything else (`types.py`), with its own algebra
(row union, scoped labels) exactly because Leijen's row-polymorphism
result (cited in RFC 0001 §3) is the established way to make an
open-ended label set unify efficiently. See RFC 0001 for the full
account and [LANGUAGE-PHILOSOPHY.md entry 8](LANGUAGE-PHILOSOPHY.md#8-effect)
for what "effect" means as a term.

## 10. What is out of scope for v0.2, on record

Refinement types, dependent types, effect handlers, associated types,
higher-kinded types (`F[_]`), const generics. None has an operational
semantics decided; per Constitution Article VIII, none gets syntax
before one does. See [NON-GOALS.md](NON-GOALS.md) for the full,
reasoned list.

---

## 11. Ownership types (Milestone 1)

Full research and decision: [MEMORY-MODEL.md](MEMORY-MODEL.md). Full
mechanism: [OWNERSHIP-MODEL.md](OWNERSHIP-MODEL.md). Summary of what
changes in the type system specifically:

- A region-allocated value's type carries its region's identity
  (`InRegion[T]` tagged with a region). This is **one more piece of
  information on a type**, not a new kind of type former alongside
  structs/enums/tuples/functions (§1) — the same way an effect row is
  one more piece of information on a function type, not a fifth type
  former.
- **No named lifetime parameter exists anywhere in the grammar.**
  [OWNERSHIP-MODEL.md §4.2](OWNERSHIP-MODEL.md#42-no-named-lifetimes-anywhere)
  is the direct answer to this phase's explicit instruction not to add
  lifetime syntax merely because Rust has one: a region's lifetime is
  its lexical scope, visible in the program text without a separate
  annotation language.
- **Two capabilities, one linear.** `Shared(Region)` is an ordinary,
  freely copyable RFC 0001 capability. `Exclusive(Region)` is linear
  (§3.6 of MEMORY-MODEL.md) — it is the **only** linear type in NOVA's
  design; nothing else in this document's type formers changes character.

## 12. Mutability

NOVA's v0.2 mutability story (RFC 0005: `let mut` locals, frame-scoped,
provably alias-free because there were no references at all) is
subsumed, not replaced, by Milestone 1: a `mut` local is the degenerate
case of region-based mutation where the "region" is a single stack
frame and the exclusive capability is implicit and un-nameable (there is
only ever one holder, because there is no way to construct a second
handle to a frame-local variable, per RFC 0005 §3). Heap-allocated,
region-based mutation (§11) is the general case: mutation requires the
region's linear exclusive capability, exactly as RFC 0005's rule
required a `mut` local to be the one thing writing to itself.

**No mutable struct fields, no mutable collection elements, no general
lvalues** (RFC 0005 §3.3) remains true of *values reached without going
through a region's exclusive capability*. Once a value is
region-allocated and an exclusive capability for its region is held,
writing through it (`write(x, v)` in [regionlab](regionlab/)'s
notation) is exactly the mutation RFC 0005's restriction was deferring —
this phase is where that deferral ends, for region-allocated data
specifically.

## 13. Send/Share

Not a separate trait mechanism (contrast Rust's `Send`/`Sync`, an
auto-derived unsafe-trait layer — [MEMORY-MODEL.md §2](MEMORY-MODEL.md#2-rust-evaluated-honestly-before-anything-is-proposed)
item 5 names this as a real cost of Rust's design, not a feature to
copy). NOVA derives both properties directly from §11's shared/exclusive
distinction:

| Rust | NOVA | Why it needs no separate trait |
|---|---|---|
| `Send` (safe to move across a thread) | A live `Exclusive(Region)` capability is movable | Moving it is an ordinary linear move (§11); the old holder loses access, so nothing is left to race with. |
| `Sync` / `Share` (safe to access concurrently, read-only) | A live `Shared(Region)` capability | Every holder has read-only access by construction (§2 of OWNERSHIP-MODEL.md); concurrent holders never conflict. |

Verified, not merely argued: [SAFETY-GUARANTEES.md §2](SAFETY-GUARANTEES.md#2-sendshare-verified-rather-than-merely-argued).

## 14. Aliasing rules

Stated once, precisely, as the type system's central invariant for
region-allocated data (restates
[OWNERSHIP-MODEL.md §2](OWNERSHIP-MODEL.md#2-the-core-claim-stated-as-a-typing-discipline)
in type-system vocabulary):

> A region's data may have any number of live `Shared` aliases, or
> exactly one live `Exclusive` alias, never both kinds at once.

This is checked at the granularity of a **whole region**, not per-value
(contrast Rust, which tracks aliasing per reference with a lifetime
parameter). The cost of this coarseness is named directly, not hidden:
[OWNERSHIP-MODEL.md §4.1](OWNERSHIP-MODEL.md#41-why-this-and-not-rusts-borrow-checker)
and §8 — two disjoint fields of one region cannot be exclusively aliased
independently; a program needing that splits the fields into two
regions.

For values that never touch a region at all (an `Int`, an ordinary
struct built and used entirely on the stack, as in every Phase 2
example), the aliasing story is unchanged from Phase 2: affine-by-default,
`.clone()` to reuse, no region tag, no exclusivity tracking — Milestone 1
adds a mechanism *for heap-allocated, region-owned data specifically* and
changes nothing about code that does not use it, per
[Constitutional Principle 10](LANGUAGE-CONSTITUTION.md#principle-10--advanced-features-must-not-contaminate-simple-programs-unnecessarily).
