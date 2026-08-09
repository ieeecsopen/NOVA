# NOVA — Language Philosophy

Phase 1 output. Precise definitions for twelve terms NOVA uses constantly
and none of which mainstream languages define consistently. This document
is the vocabulary; [PROGRAM-MODEL.md](PROGRAM-MODEL.md) uses it to
critique the program model, [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md)
uses it to state binding principles, and [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md)
uses it to classify features.

Constitution Article V applies to every entry: where a definition is
standard, it says so and cites the standard; where NOVA's stance is
unusual, it says exactly what the delta is and why.

Each entry has the same shape: **informal** (how you'd say it out loud),
**operational** (what it cashes out to in the reference implementation, or
would once the relevant milestone lands), **prior art**, and **status**
(implemented / designed-but-unbuilt / aspirational / explicitly rejected).

---

## 1. Value

**Informal.** A piece of data that evaluation produces — the answer, not
the question.

**Operational.** In `verifier/refspec/eval.py`, a value is exactly what
`Interpreter.eval` returns: a Python `int`, `str`, `bool`, `Unit`,
`Closure`, or `CapValue`. Nothing else is a value. There is no notion of
a "partial" or "pending" value in v0.1 — evaluation is strict and
terminates or doesn't.

**The one place NOVA's notion of value is non-standard.** Ordinary values
(`Int`, `String`, `Bool`, `Unit`, closures) are inert: they carry no
authority, and any well-typed expression that can construct one, can. A
**capability value** (`CapValue`) is a value in exactly the same runtime
sense — it can be passed, stored in principle, matched on in principle —
but no NOVA expression can *construct* one. It can only arrive as a
parameter, ultimately tracing back to `main`'s `rt: Runtime` (RFC 0001
§4.1, §4.7). The type system, not the runtime representation,
distinguishes the two: a capability value's type is a capability type,
and the checker treats those types specially (RFC 0001's `(CapUse)` rule).
This is Constitution Article IV's authority commitment restated at the
level of "what counts as a value" rather than "what counts as a function."

**Prior art.** "Value" as the result of evaluation is standard (Church,
Curry; Plotkin's SOS). Unforgeable capability-as-value is the object-
capability model (Dennis & Van Horn 1966; Miller's *Robust Composition*)
— NOVA's delta is only that the *type system*, not just the runtime,
enforces unforgeability; see [RESEARCH.md §R4](RESEARCH.md#r4--capability-security).

**Status.** Implemented for ordinary values and capabilities. Not yet
extended to compound data (structs, enums — Milestone 2), regions
(Milestone 1), or graded/uncertain values (§6, §11 below — not designed).

---

## 2. Computation

**Informal.** The process of getting from an expression to a value —
the verb, where a value is the noun.

**Operational.** `Interpreter.eval(e, env)` *is* a computation in
progress; its termination with a value, or its failure, or its
non-termination, are the three things a computation can do. A
computation's *type* is what the checker assigns to the expression before
running it: a value type, plus an **effect row** describing which
capabilities the computation may exercise on the way to that value
(RFC 0001 §4.2).

**The dual reading, made explicit.** A computation can be described from
two directions, and NOVA's effect row conflates them by design:

- **outward**: what the computation *does* through the capabilities it
  holds — this is the classical effect (Moggi's monads; Plotkin & Power's
  algebraic effects).
- **inward**: what the computation *requires from its context* to run at
  all — this is a **coeffect** (Petricek, Orchard & Mycroft, ICFP 2014;
  first cited at [RFC 0001 §3.1](RFC/0001-core-capability-effects.md#31-the-closest-prior-art)).

RFC 0001's derivation rule (§4.3) computes the outward description (the
row) *from* the inward one (the capabilities reachable in scope). NOVA's
position is that for authority specifically, effect and coeffect are the
same fact seen from two ends, and a single mechanism should carry both —
which is exactly the claim [Experiments 001–003](docs/experiments/)
tested.

**Prior art.** Computation-as-process is standard operational semantics.
The effect/coeffect duality is Petricek et al.'s, not NOVA's; NOVA's
delta is using it to justify *one* row rather than two parallel systems.

**Status.** Implemented for the effect direction (RFC 0001, checked).
The coeffect framing is descriptive of what already exists, not a new
mechanism — no further implementation is implied by this entry.

---

## 3. Program

**Informal.** A whole, runnable thing — as opposed to a computation, which
may be a sub-expression of one.

**Operational (v0.1, exact).** A program is a computation with a
distinguished entry point that receives the **root capability** and
produces an exit value:

```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

This is checked by `Checker.check_entry` (RFC 0001 §4.7, diagnostic
E0210) and is the only thing v0.1 can call a program. Everything else in
a `.nova` file is a *declaration available to* a program, not a program
itself.

**Aspirational (the long-term model, gated).** VISION.md and the original
Constitution Article II describe a far richer notion — `Program = Intent
+ State + Behavior + Constraints + Capabilities + Resources + Effects +
Uncertainty + Execution Strategy + Verification`. [PROGRAM-MODEL.md](PROGRAM-MODEL.md)
argues this list is not yet a model, in the sense that several of its
terms are not independent and one (`Execution Strategy`) has no
operational content at all. The exact, checkable definition above is
what "program" means *today*; the aspirational one is a research
direction, gated milestone-by-milestone exactly as Constitution
Article VIII requires.

**Why both definitions are given.** A word that means "the thing that
typechecks and runs" in one document and "intent plus nine other things"
in another is not defined. Keeping both, explicitly labeled, is more
honest than picking one and hiding the gap.

**Prior art.** Entry-point-as-capability-source is Eio's `Stdenv.t`
pattern (OCaml) and the object-capability tradition generally; see
[RESEARCH.md §R4](RESEARCH.md#r4--capability-security).

**Status.** Exact definition: implemented. Aspirational definition: see
[PROGRAM-MODEL.md](PROGRAM-MODEL.md) for the critique and the revision.

---

## 4. Service

**Informal.** A program that does not run once to an exit value, but
runs continuously or repeatedly, responding to input over time.

**Operational.** Not designed. There is no module system (Milestone 2)
and therefore no NOVA notion of a long-lived boundary yet. The shape a
service is expected to take, consistent with thesis T2
([DESIGN-OPPORTUNITIES.md §4](DESIGN-OPPORTUNITIES.md#4-theme-c--boundaries-and-the-adoption-problem)):
a **component** (WASI Component Model sense) whose capability *imports*
are its authority boundary, and whose entry points are ordinary
effectful functions rather than a single `main`. The difference between
a program and a service is then not a new mechanism — it is that a
service's capability imports are supplied at *link time* by a host,
repeatedly, rather than once by a bootstrapping runtime.

**Prior art.** The Component Model's shared-nothing linking with WIT
imports; see [RESEARCH.md §R16](RESEARCH.md#r16--webassembly-wasi-and-the-component-model).
Erlang's process model as an alternative shape for "runs continuously" —
not adopted, since NOVA's memory model is undecided (Theme B).

**Status.** Aspirational, Milestone 2–3. No syntax proposed here, per
this phase's scope.

---

## 5. Agent

**Informal.** As currently used in industry: a program that calls a
model, plans, and takes actions with some autonomy.

**NOVA's position: this is deliberately not a language concept.**
[NON-GOALS.md §2.3](NON-GOALS.md#23-ai--or-agent-specific-language-constructs)
already forbids an `agent` keyword or type. This entry exists to give the
word *some* precise meaning, so that "NOVA doesn't have agents" is not
mistaken for "NOVA can't express what people build with agents."

**Operational (deflationary, by construction).** Where "agent" is used
informally about NOVA code, it denotes an ordinary program or component
that:

1. holds a **model capability** — a capability like any other, gating a
   network-shaped effect (RFC 0001's mechanism, unmodified);
2. is bounded by an explicit **grade** on that capability — a cost or
   call-count limit (§6 below; Milestone 5, not yet implemented, and
   [Experiment 003](docs/experiments/003-graded-rows.md) already found
   the naive version of this does not survive row polymorphism);
3. has the model's output pass through an explicit boundary before
   reaching any privileged effect — an information-flow concern
   (P20/R14), which [DESIGN-OPPORTUNITIES.md §5](DESIGN-OPPORTUNITIES.md#5-theme-e--what-does-not-unify)
   found does **not** reduce to the capability model and is explicitly
   *not* solved by anything NOVA has.

Three ordinary mechanisms, one of them unbuilt and one of them entirely
unsolved. If all three existed and composed, "agent" would be a fully
adequate informal name for the pattern — and NOVA would have added no new
semantics to get there, which is the point.

**Prior art.** [RESEARCH.md §R13](RESEARCH.md#r13--ai-programming) and
[§R14](RESEARCH.md#r14--information-flow-and-agent-security).

**Status.** (1) implemented (it is just RFC 0001). (2) not implemented
(Milestone 5, open question). (3) unsolved by any known mechanism NOVA
has; recorded as a real gap, not a future promise.

---

## 6. Resource

**Informal.** Something finite that a computation consumes: time,
memory, network round-trips, tokens, money.

**Operational (proposed, not implemented).** A resource is *the thing a
grade measures*. [DESIGN-OPPORTUNITIES.md §2](DESIGN-OPPORTUNITIES.md#2-theme-a--obligations-are-one-mechanism)
proposes generalizing RFC 0001's row from a set of labels to a map from
labels to grades drawn from a semiring: `{Net: 3, Alloc: 4096}`. Under
that proposal, a *capability* is the authority to touch a resource; the
*resource* is what accumulates as the capability is used; the *grade* is
the checked bound on how much.

**The distinction that matters.** `Net` (the capability) answers "may
this code touch the network at all?" — already checked, today.
`{Net: 3}` (the resource, graded) would answer "how many times, at
most?" — proposed, not built. Conflating the two is a category error:
a function can be *permitted* to use a capability without any bound on
how much, and a bound without permission is meaningless. The two axes are
independent and both needed.

**The concrete finding against the naive version.**
[Experiment 003](docs/experiments/003-graded-rows.md) implemented
occurrence-counting as a syntactic pass *after* checking, and found it
gives sound, useful bounds for first-order code and collapses to "no
bound at all" the instant a row-polymorphic higher-order function
(`with_retry`, RFC 0001's own example) is involved. The conclusion
recorded there: grades must be carried on row *variables*, inside
unification, not bolted on afterward. Resource, as a NOVA concept, is
therefore precisely defined but **not yet soundly implementable** without
a type-system change that has not been designed.

**Prior art.** Graded modal types (Granule; Orchard, Liepelt & Eades
2019); RAML (Hoffmann, Aehlig & Hofmann); Quantitative Type Theory
(Atkey 2018) — see [RESEARCH.md §R5](RESEARCH.md#r5--resource-aware-programming).

**Status.** Defined. Not implemented. Milestone 5, gated on a type-system
RFC per the experiment 003 correction already applied to
[ROADMAP.md](ROADMAP.md).

---

## 7. Capability

**Informal.** A value that grants the power to do something to the
outside world — and the only such value in NOVA.

**Operational (implemented, exact).** RFC 0001 §4.1: a `capability`
declaration introduces a type and, simultaneously, an effect label of the
same name. No NOVA expression constructs a capability value from nothing;
every one traces back to `main`'s `rt: Runtime` parameter, by ordinary
argument-passing or (once designed) attenuation (RFC 0001 §4.6). A
capability is unforgeable **because the grammar contains no expression
form that produces one** — not because of a runtime check.

**Prior art.** Fully established; see
[RESEARCH.md §R4](RESEARCH.md#r4--capability-security), and RFC 0001 §3
for the specific delta from Effekt and Austral.

**Status.** Implemented and checked (25 conformance tests exercise this
directly). Attenuation is specified (§4.6) but not implemented — known
issue I5.

---

## 8. Effect

**Informal.** What a computation is observed or checked to do, as
opposed to what value it returns.

**Operational (implemented, exact).** A computation's effect is its
**row**: the set of capability-type names reachable from its body,
computed by the capability-reachability pass and checked for *equality*
(not subsumption) against the declared row (RFC 0001 §4.3, the
derivation rule). This is the single most load-bearing definition in the
language: it is what makes "effect" a *derived, checked fact* rather
than an *authored annotation* — see the effect/coeffect duality in
entry 2 above.

**What effect is not.** It is not a cost (that's a resource, entry 6, not
yet gradeable), not a guarantee about termination or timing, and not an
information-flow property (entry 7's dual concern, in entry 5's sense —
capability-safety and taint-safety are different axes;
[DESIGN-OPPORTUNITIES.md §5](DESIGN-OPPORTUNITIES.md#5-theme-e--what-does-not-unify)).

**Prior art.** Algebraic effects and row-typed effect systems generally;
see [RESEARCH.md §R3](RESEARCH.md#r3--effect-systems). RFC 0001 §3
already gives the full comparison and the withdrawn/narrowed novelty
claim.

**Status.** Implemented, checked, tested (conformance suite).

---

## 9. Constraint

**Informal.** Something that must hold about a program.

**This is the term the original program model treats as one peer among
ten, and Phase 1's central correction (developed fully in
[PROGRAM-MODEL.md](PROGRAM-MODEL.md)) is that "constraint" is not a peer
of "effect" or "resource" — it is the genus they belong to.**

**Operational, as a family, ordered by what discharges them:**

| Constraint | Carrier | Discharged by | Status |
|---|---|---|---|
| A value has this shape | a type | the checker, always | implemented |
| A computation touches only these capabilities | an effect row | the checker, equality (E0201/E0202) | implemented |
| A computation touches a capability at most *n* times | a grade | *type-system extension, undesigned* | not implemented |
| A value satisfies an arbitrary predicate | a refinement/contract | an SMT solver, opt-in | Milestone 6, not implemented |

Every row in that table is a **constraint**. The first two rows are
implemented today and share one mechanism, per Theme A. The third is
Theme A's proposed extension of that same mechanism (entry 6). The
fourth is Theme E's negative finding
([DESIGN-OPPORTUNITIES.md §5](DESIGN-OPPORTUNITIES.md#5-theme-e--what-does-not-unify)):
refinements constrain *values*, rows constrain *actions*, and they do not
reduce to one mechanism. A general-purpose refinement system needs its
own machinery (Milestone 6), separate from the row.

**Prior art.** "Constraint" as a supertype of types, effects, and
refinements is implicit throughout the type-theory literature (a type
*is* the cheapest constraint, in the sense of Reynolds/Pierce); NOVA's
contribution is only the classification table above, made concrete by
what actually shares a mechanism versus what doesn't.

**Status.** See per-row status above.

---

## 10. Guarantee

**Informal.** A constraint (entry 9) that has actually been discharged,
as opposed to merely stated.

**Operational.** A four-level ladder, used consistently across NOVA's
documents from here on:

1. **Assumption** — a constraint neither declared nor checked, silently
   relied upon. The dangerous, invisible case. SECURITY.md's disclaimers
   about FFI and the trusted computing base are assumptions in this
   precise sense.
2. **Declared constraint** — stated in a signature (a type, a row) but
   not yet related to what actually happens. A signature before checking.
3. **Guarantee** — a declared constraint the compiler has verified holds,
   by the mechanism appropriate to its kind: type checking for shapes,
   row-equality checking for effects (RFC 0001). This is what NOVA
   currently means whenever it says "checked."
4. **Verified guarantee** — a constraint discharged by an independent
   proof procedure (SMT, Milestone 6) rather than by the core checker
   alone. Strictly stronger than level 3 for the constraints it covers,
   and explicitly **not** attempted for whole-program correctness — see
   [NON-GOALS.md §1.1](NON-GOALS.md#11-being-a-proof-assistant).

**Why this matters as a named ladder, not just a remark.** Constitutional
principle "verification strength must be explicit"
([LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md)) is exactly the
requirement that every claim in NOVA documentation and NOVA code state
*which rung* it occupies. "NOVA prevents ambient authority" is a level-3
guarantee (checked, tested). "NOVA prevents information leaks" would be a
level-1 assumption if ever claimed, which is precisely why SECURITY.md
refuses to claim it.

**Prior art.** The assumption/specification/proof distinction is standard
in formal methods (e.g. the "verification gap" discussed for Dafny/SPARK
in [RESEARCH.md §R12](RESEARCH.md#r12--formal-verification)); the
four-level framing here is NOVA's organization of it, not a new idea.

**Status.** The ladder itself is a documentation discipline, adopted now.

---

## 11. Uncertainty

**Informal.** A value that is not known exactly — a measurement, an
estimate, a model's output — as opposed to a value computed exactly.

**NOVA's position: this is a property of a value, not a property of a
program.** The original program model lists `Uncertainty` as a top-level
ingredient alongside `State` and `Effects`. [RESEARCH.md §R10](RESEARCH.md#r10--uncertainty)
found the mature version of this idea already exists —
`Uncertain[T]` (Bornholt, Mytkowicz & McKinley, ASPLOS 2014) represents a
value as a distribution and makes comparison return evidence rather than
a boolean — and it is a **data type**, not a control-flow or authority
mechanism. [NON-GOALS.md §2.4](NON-GOALS.md#24-uncertainty-as-a-language-feature)
already declines to give it syntax.

**The connection to Guarantee (entry 10), stated precisely.** An
uncertain value is the *data-level* analogue of an *estimate* in the
Guarantee ladder: both are claims that have not been (and in the value
case, structurally cannot be) discharged to certainty. A resource
*estimate* (constitutional principle 6) and an uncertain *value* are the
same idea — "this is not exact" — applied to two different things a
program can say (a cost claim vs. a data value). NOVA should eventually
have one vocabulary for "not exact" that covers both, but that vocabulary
is `Uncertain[T]` as an ordinary generic type over data, applied
uniformly, not a new modality.

**Status.** Correctly demoted from the program model (see
[PROGRAM-MODEL.md](PROGRAM-MODEL.md)) to a library concern, gated on
generics (Milestone 2) existing at all.

---

## 12. Execution strategy

**Informal.** *How* a computation is carried out — its schedule,
placement (which core, which accelerator, which tier), and low-level
optimization — as distinct from *what* it computes.

**NOVA's position: this is the least-defined term in the original model,
and Constitution Article VIII already flags it as a category rather than
a design.** [RESEARCH.md §R20](RESEARCH.md#r20--adaptive-and-self-optimising-software)
and [PROBLEM-SPACE.md P22](PROBLEM-SPACE.md#p22--performance-tuning-is-entangled-with-algorithm)
found the one general, working precedent — Halide's separation of
algorithm from schedule — confined, after thirteen years, to array
pipelines, with no general-purpose analogue.

**The one constraint this entry commits to, in advance of any design.**
Whatever "execution strategy" eventually means, it must be a
**meaning-preserving transformation**: changing *how* a computation runs
must never change any **guarantee** (entry 10) already established about
*what* it computes. This is not a design — it is a precondition any
future design must satisfy, stated now so a scheduling feature cannot be
proposed later that quietly weakens an existing guarantee for
performance. It follows directly from Constitution Article III ranking
performance below soundness.

**Status.** No operational semantics. Explicitly speculative
([RESEARCH.md](RESEARCH.md#summary-where-the-literature-is-thin) tags
this Speculative outside the array/tensor domain). No syntax proposed.
