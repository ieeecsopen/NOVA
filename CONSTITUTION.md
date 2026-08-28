# The NOVA Constitution

This document governs the design of the NOVA language. It is deliberately
short. It constrains what may be added to NOVA and what must be justified
before it is added.

Changes to this document require an RFC and are recorded in
`docs/constitution-changelog.md`.

---

## Article I — What NOVA is

NOVA is a general-purpose, statically typed programming language whose
central research claim is:

> The obligations a program is under — what it may do, what it must not do,
> what it costs, and what it promises — belong in the language core, not in
> comments, linters, review checklists, or runtime configuration.

We call this **constraint-native**. It is a claim about *where* information
lives, not a claim to have invented static analysis.

## Article II — The program model

The model originally stated here was:

```
Program = Intent
        + State
        + Behavior
        + Constraints
        + Capabilities
        + Resources
        + Effects
        + Uncertainty
        + Execution Strategy
        + Verification
```

**Superseded 2026-08-28 by [PROGRAM-MODEL.md](docs/foundation/PROGRAM-MODEL.md)**, per
Phase 1's explicit mandate to challenge this model. That document found
four of the ten terms above (`Capabilities`, `Effects`, `Resources`, and
part of `Constraints`) are not independent — they are one mechanism (a
row) examined at increasing precision — and that `Verification` is not a
peer ingredient but an axis on `Constraints` (see the Guarantee ladder,
[LANGUAGE-PHILOSOPHY.md entry 10](docs/foundation/LANGUAGE-PHILOSOPHY.md#10-guarantee)).
`Uncertainty` is demoted to a property of values, not programs.
`Execution Strategy` is kept only as an explicitly open, ungated slot.
The revised model:

```
Program = Intent
        + Computation           (State + Behavior)
        + Row                   (Capabilities + Effects + Resources)
        + Constraints           (types ⊆ rows ⊆ refinements;
                                  each carries an explicit
                                  Verification strength)
        + [Uncertainty: a note under Computation, not a peer]
        + [Execution Strategy: an open, ungated slot]
```

See [PROGRAM-MODEL.md](docs/foundation/PROGRAM-MODEL.md) for the full argument and
[docs/constitution-changelog.md](docs/constitution-changelog.md) for the
record of this amendment. This remains a research agenda, not a v1
feature list: most terms are still not defined with enough precision to
implement, and a term may only enter the language when it has an RFC that
defines its semantics, its cost, and its interaction with every term
already in the language.

## Article III — Order of priority

When two goals conflict, the earlier one wins. This ordering is normative
and is the tiebreaker in design disputes.

1. **Soundness** — the type system must not lie. A design that is
   convenient but unsound is rejected, not patched.
2. **Explicit semantics** — a reader must be able to determine what a
   program does from the program text plus its declared interfaces.
3. **Safety** — memory safety, data-race freedom, and absence of undefined
   behavior in safe code.
4. **Security** — no ambient authority; least privilege by construction.
5. **Performance** — predictable cost, ahead-of-time compilable, no
   mandatory tracing GC in the core.
6. **Ergonomics** — the safe path should be the short path.
7. **Verifiability** — machine-checkable claims, opt-in and layered.
8. **Portability** — native and WebAssembly are co-equal targets.
9. **Interoperability** — C ABI and the WASM Component Model.
10. **Extensibility** — the ability to add the above later without a
    breaking redesign.

Ergonomics ranks below explicitness. NOVA will accept verbosity to avoid
hidden behavior. It will not accept verbosity that carries no information.

## Article IV — What must be in the core

A property must be in the language core if it **cannot be retrofitted
without breaking every existing program**. Empirically, these are:

- **Effects.** A language that starts effect-untracked never becomes
  effect-tracked. Every existing function signature is wrong.
- **Authority.** A language with ambient authority (`open`, `now`, `rand`
  as free functions) cannot later become capability-safe. Every call site
  is a hole.
- **Memory discipline.** Ownership cannot be added to a language whose
  libraries assume unrestricted aliasing.

Everything else — generics, traits, macros, async, distribution,
inference sugar — is *additive* and must be deferred until the core is
proven.

NOVA v0.1 therefore fixes effects and authority, and explicitly defers
memory discipline while committing to Article XI below.

## Article V — Nothing is novel until proven novel

No document in this repository may describe a feature as new, novel, or
unprecedented without citing the prior art it improves on and stating the
specific delta.

Known prior art that NOVA draws on directly, and must be cited rather than
reinvented:

| Idea | Prior art |
|---|---|
| Row-based effect types | Koka, Links, Frank, Eff |
| Algebraic effect handlers | Eff, Koka, Unison, Multicore OCaml |
| Capability-safe authority | KeyKOS, E, Joe-E, Caja, Pony, Austral, WASI |
| Ownership / affine types | Cyclone, Rust, Vale, ATS |
| Actor isolation | Erlang, Pony |
| Refinement / contract checking | Dafny, F\*, Liquid Haskell, Ada SPARK |
| Content-addressed code | Unison |
| Portable component boundaries | WebAssembly Component Model |
| Retargetable compiler IR | LLVM, MLIR, Cranelift |

## Article VI — The feature bar

A feature is admissible only if its RFC answers all of:

1. What concrete program is impossible or unsafe today?
2. How do Rust, Koka, Pony, Swift, TypeScript, and Haskell solve it?
3. Why is each of those insufficient *for NOVA's priority order*?
4. What is the semantics, stated precisely enough to implement twice?
5. What does it cost at compile time? At run time? In binary size?
6. What does it cost a reader who does not use the feature?
7. What is the simplest version that captures 80% of the value?
8. How is it tested in isolation?
9. What does it foreclose?

Question 9 is the one most often skipped and the most expensive to get
wrong.

## Article VII — Subtraction

Every release must be able to answer "what did we remove or simplify?"
A release that only adds is a warning sign. Feature count is not progress.

## Article VIII — No speculative futurism

"AI-native", "agent-native", "distributed-native", and "quantum-ready" are
not designs. They are categories. NOVA will not ship syntax for a concept
it cannot give an operational semantics for.

When these areas are addressed, they must reduce to mechanisms already in
the core (effects, capabilities, resources), or they must justify a new
core mechanism under Article VI.

## Article IX — Two implementations of every semantics

Every semantic rule in the core must be implemented in at least two places:
the checker and an executable reference semantics. Divergence between them
is a bug in the specification, not in either implementation.

## Article X — Errors are part of the language

Diagnostic quality is a first-class design constraint, not polish. A rule
that cannot be explained in a good error message is a rule that is too
subtle to keep.

## Article XI — Forward compatibility of the core

Until memory discipline is designed (RFC pending), no core construct may
assume unrestricted aliasing or garbage collection. In practice: no
implicit sharing in the surface language, no cyclic data in the v0 core,
and no library API whose contract would break under affine typing.

**Memory discipline is now designed** — [MEMORY-MODEL.md](docs/language/MEMORY-MODEL.md),
[OWNERSHIP-MODEL.md](docs/language/OWNERSHIP-MODEL.md), region-based ownership with
linear exclusive-access capabilities — and satisfies this Article's
constraint by construction: no garbage collection, and aliasing is
checked rather than assumed away
([SAFETY-GUARANTEES.md](research/SAFETY-GUARANTEES.md)). This Article's
restriction remains binding on anything the memory model itself does
not yet cover (§7 of OWNERSHIP-MODEL.md's open questions).

## Article XII — Versioning honesty

Version numbers describe stability commitments, not ambition. `0.x` means
the language will break. NOVA will not claim 1.0 before the core is frozen,
the specification is complete, and two independent implementations agree.
