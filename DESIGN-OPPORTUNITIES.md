# NOVA — Design Opportunities

Phase 0 synthesis. Where the twenty-four problems in
[PROBLEM-SPACE.md](PROBLEM-SPACE.md) collapse into shared mechanisms,
where they do not, and what NOVA's thesis should therefore be.

The test applied throughout is Constitution Article VI, question 7:
*what is the simplest version that captures 80% of the value?* A theme
only earns a place here if several apparently separate problems turn out
to be **one mechanism applied at different points**.

---

## 1. Five themes

| Theme | Problems | Candidate shared mechanism | Verdict |
|---|---|---|---|
| **A. Obligations** | P3, P5, P8, P9, P10, P14, P19, P21 | graded capability rows | **Strong — this is the thesis** |
| **B. Ownership & lifetime** | P1, P2, P6, P7 | regions as handed-over things | **Strong, but blocked on M1** |
| **C. Boundaries** | P11, P12, P14, P23, P24 | the component boundary | **Strong strategically, weak technically** |
| **D. Identity of code** | P13, P15, P24 | content addressing | **Real, and largely borrowed from Unison** |
| **E. Assurance** | P16, P17, P20, P22 | *none found* | **Does not unify — say so** |

Themes A and B are the language. Theme C is the adoption strategy. Theme D
is an architecture decision. Theme E is where NOVA should be honest that
four hard problems remain four hard problems.

---

## 2. Theme A — Obligations are one mechanism

### The observation

Eight problems that are normally treated as unrelated all have the same
shape: *attach a property to a function, propagate it compositionally
through calls and captures, and check it at a boundary.*

| Problem | The property attached | Today it lives in |
|---|---|---|
| P3 invisible effects | which capabilities are used | nowhere |
| P5 function colouring | which colour(s) a function has | ad-hoc keywords |
| P8 deadlines | how much time remains | `context.Context`, by convention |
| P9 resource budgets | how many allocations / round-trips | load tests and alerts |
| P10 retry safety | whether the effect is idempotent | prose documentation |
| P14 dependency authority | what a package may do | nothing |
| P19 model calls | cost, nondeterminism, taint | libraries |
| P21 observability | what to instrument | a parallel hand-written program |

NOVA already computes the first one. RFC 0001's row is a set of capability
labels. Every remaining row in that table is the *same set, with something
attached to each label.*

### The mechanism: graded rows

Generalise the row from a **set** of labels to a **map** from labels to
grades drawn from a semiring:

```
ε ::= { C₁ : g₁ , … , Cₙ : gₙ | ρ }
```

- grade = **unit** → RFC 0001 exactly. Effects and colouring (P3, P5).
- grade = **natural number / cost** → occurrence counting. "At most three
  `Net` operations", "at most 4KB via `Alloc`" (P9), and deadlines as a
  consumable time grade (P8).
- grade = **property lattice** → `Payments : non-idempotent` lets a
  row-polymorphic `with_retry[r]` *refuse* to instantiate `r` with a
  non-idempotent label (P10).
- **the row itself, unmodified** → the package's published capability
  manifest (P14), the set of spans to emit (P21), and the tier-placement
  constraint (P12).

One mechanism, eight problems. Sequential composition adds grades;
branching takes the join; the row variable carries the rest. This is
exactly the algebra of **graded monads**, and it is not new — see below.

### Prior art, stated before the claim

| Idea | Prior art |
|---|---|
| Graded monads / effect grading | Katsumata (POPL 2014); Orchard, Petricek & Mycroft |
| Graded modal types | **Granule** (Orchard, Liepelt & Eades 2019) |
| Quantitative typing | Atkey's QTT (2018); Idris 2 |
| Resource bounds from types | RAML (Hoffmann, Aehlig & Hofmann) |
| Effects as capabilities | **Effekt** (Brachthäuser et al. 2020, 2022) |
| Row algebra | Leijen (2005) |

None of this is NOVA's invention. What this review did **not** find is any
system that uses *one* graded row as the common carrier for authority,
cost, retry policy, instrumentation and package manifests simultaneously.
That is an **integration claim**, not a theoretical one, and it should be
described as such forever.

### The sharpest single framing: coeffects

There is a better name for what RFC 0001's derivation rule is doing.

- An **effect** describes what a computation *does to* its context —
  graded monads.
- A **coeffect** describes what a computation *requires from* its
  context — graded comonads. Petricek, Orchard & Mycroft, *Coeffects: A
  Calculus of Context-Dependent Computation* (ICFP 2014).

RFC 0001's capabilities-in-scope are a **coeffect**: a requirement on the
calling context. The derived row is the induced **effect**. NOVA's
"derivation rule" is, in this language, *an effect computed from a
coeffect* — and that is a well-studied relationship, not a new one.

This framing is worth adopting because it immediately predicts where the
design will strain: coeffects are about *what flows in*, which is also
where information-flow labels live (P20). It tells us the IFC question
(§5) is a coeffect question, not an effect question.

### What to build first

The cheapest falsification tests, in order:

1. **Instrumentation from rows (P21).** Generate trace spans from
   capability operations; compare with hand-written instrumentation on a
   real program. Costs days. Tests whether the row carries real
   information. *Do this before anything in Milestone 5.*
2. **Capability manifests (P14).** Emit a package's row as a manifest and
   diff it across versions. Costs days once modules exist. Directly tests
   the Theme C payoff.
3. **Occurrence counting (P9, minimal).** Grade rows with natural numbers
   and count round-trips only. Tests whether grading composes before
   committing to a full semiring.

If (1) produces instrumentation nobody wants, the row is thinner than
claimed and the thesis weakens. That is the point of doing it first.

---

## 3. Theme B — Ownership, scope and lifetime are one mechanism

### The observation

Four problems all reduce to: *this thing is handed to you, you may use it
here, and you may not let it outlive this scope.*

- P1 memory: a region of objects you own.
- P2 escape hatches: an `Unsafe` authority you were granted.
- P6 data races: exclusive access to a region while you hold it.
- P7 structured concurrency: a `Nursery` whose tasks cannot outlive it.

In each case the mechanism is a **scoped, non-escaping, handed-over
resource** — which is what a capability already is in RFC 0001, except
that RFC 0001's capabilities are first-class and *may* escape.

### The unification, and its cost

If NOVA adopts **regions as the unit of ownership** (Verona, Vale), then:

- a region is a capability for memory,
- exclusive region access gives data-race freedom (Verona's result),
- a nursery is a region with a task set,
- `Unsafe` is a capability like any other.

One concept — *a resource you are handed, scoped* — covers memory,
concurrency, task lifetime and escape hatches.

**The cost is real and must be stated.** This pushes NOVA toward
second-class or region-bound capabilities for *some* uses, which is
exactly Effekt's design and is in tension with RFC 0001's decision to make
capabilities first-class. RFC 0001 §6 alternative D deferred linearity
"so as not to pre-decide the memory model by accident" — Theme B says the
memory model will decide it instead, and Milestone 1 must therefore
revisit RFC 0001, not just extend it.

**This is the single largest structural risk in the project** and it is
now on the record.

> **Resolved, Milestone 1 —** [MEMORY-MODEL.md](MEMORY-MODEL.md),
> [OWNERSHIP-MODEL.md](OWNERSHIP-MODEL.md). The forced choice above was
> not, in fact, forced: there is a third option between "capabilities
> stay first-class" and "capabilities become second-class," which is to
> keep every capability first-class and apply *linearity* to exactly
> the one capability kind that needs it (exclusive region access).
> RFC 0001 required no revision. The risk named here is closed, and
> [SAFETY-GUARANTEES.md](SAFETY-GUARANTEES.md) states precisely, with
> tests, what is and is not proven about the result.

---

## 4. Theme C — Boundaries, and the adoption problem

Five problems are about what happens at a boundary:

- P11 the network boundary
- P12 the client/server boundary
- P14 the package boundary
- P23 the host/accelerator boundary
- P24 the interop boundary with existing code

The **WebAssembly Component Model** is one answer to four of the five. Its
shared-nothing linking with explicit WIT imports *is* capability passing
at module granularity — the same idea NOVA has at function granularity,
one level up.

This yields an unusually clean alignment:

```
NOVA function      capability parameters   →  effect row
NOVA module        capability imports      →  package manifest   (P14)
Wasm component     WIT imports             →  linkable boundary  (P24)
```

The strategic consequence is larger than the technical one. **P24 is the
axis on which languages actually die**, and the Component Model is the
only credible incremental-adoption story that does not require a trusted
C FFI hole — the hole SECURITY.md currently admits to.

Recommendation: make targeting the Component Model an explicit Milestone 3
commitment rather than one option among several, and let that decision
inform the IR choice (which then favours something that reaches Wasm
cleanly and cheaply — Cranelift or MLIR over plain LLVM).

Theme C does **not** solve P11/P12 technically. Choreographic projection
is the interesting research route there and it stays in Milestone 7.

---

## 5. Theme E — What does *not* unify

Honest negative results, which are the most useful part of a review.

**P20 (information flow) does not reduce to capabilities.** Authority
control asks "may this code act?"; IFC asks "may this data be here?". A
capability-safe program can still log a password. The coeffect framing
(§2) suggests they are *neighbours* — both are context disciplines — but
thirty years of IFC research shows the hard part is **declassification**,
and capabilities offer nothing for it. NOVA should keep SECURITY.md's
explicit disclaimer and not pretend otherwise.

**P16 (verification) does not reduce to effects.** Refinements constrain
*values*; rows constrain *actions*. They compose but they are not the same
mechanism, and Milestone 6 remains genuinely separate work.

**P17 (temporal properties) and P22 (algorithm/schedule separation) do not
reduce to anything NOVA has.** Both are Open-research in
[PROBLEM-SPACE.md](PROBLEM-SPACE.md). Neither should get syntax; see
[NON-GOALS.md](NON-GOALS.md).

**P1 does not reduce to capabilities either** — Theme B unifies the
*shape* (scoped handed-over resources), not the *checking*. Region
inference is its own hard problem and Rust's solution remains better than
anything NOVA has.

---

## 6. Consequences for the current design

Phase 0 produces four concrete changes to work already done:

1. **RFC 0001 §3 must cite Effekt** and narrow its novelty claim. The
   framing "effects as capabilities" is Brachthäuser et al. (2020). What
   remains unclaimed is equality-checked rows over *first-class*
   capabilities. *(Applied — see the RFC's Revisions section.)*
2. **RFC 0001's prior-art table must add** OCaml 5 / Eio, Pony's
   `AmbientAuth`, Effekt, and the coeffect framing. *(Applied.)*
3. **RFC 0001 §11 gains an open question:** does the derivation rule
   survive the memory model choosing region-bound capabilities (Theme B)?
   This is more likely to force a redesign than the existing §11.1.
4. **The roadmap should pull two cheap experiments forward** — rows→spans
   (P21) and capability manifests (P14) — because they falsify the thesis
   for days of work, and both currently sit in Milestones 2–5.

---

## 7. The final research question

> **What should a program be able to express in 2035 that today's
> mainstream languages do not express naturally?**

Setting aside the areas where the answer is "nothing new, just adopt what
exists" (memory safety, verification, structured concurrency), five things
stand out. Each is stated as a sentence a programmer should be able to
write and have *checked*:

**1. What a piece of code is allowed to do — and what it therefore does.**
Not as a runtime sandbox, a linter rule, or a service-mesh policy, but as
a type. Today a function's authority is invisible, its effects are
invisible, and the union of both across a dependency graph is
uncomputable. In 2035 that union should be a number the build prints.

**2. What a piece of code is allowed to consume.**
Time, memory, syscalls, round-trips, tokens, money. Today every one of
these is a runtime limiter that trips after the fact. A budget that
propagates and is *consumed* across call boundaries — the thing
`context.Context` gestures at and does not check — is the most obviously
missing composable abstraction in production software, and the literature
on it is nearly empty relative to how much code depends on it.

**3. Which properties of an operation survive being retried, cached,
parallelised, or moved.**
Idempotence, commutativity, purity, and cost are the properties that
decide whether an optimisation or a recovery strategy is *sound*. Today
they are prose. Every distributed-systems bug of the "we double-charged
the customer" genre is this gap.

**4. Where code runs, as a decision separate from what it computes.**
Client or server, CPU or accelerator, this machine or that one. Halide
showed the algorithm/schedule separation works in one domain; nothing has
generalised it, and the client/server split is still written twice by
hand.

**5. Where untrusted data may and may not flow.**
The oldest of the five (IFC, 1977) and the least adopted — and the one
newly made urgent, because every agent system routes untrusted model
output toward privileged actions and no language can express the
constraint.

**The common shape.** All five are *non-functional obligations attached to
code and propagated compositionally.* Today each has its own out-of-band
mechanism — sandboxes, limiters, documentation, frameworks, scanners —
and none composes with the others or survives a refactor. The claim worth
testing is that they are one mechanism, and that a language which carries
them in the type system makes all five ordinary.

That claim is falsifiable, which is what makes it worth building.

---

## 8. Five candidate theses, ranked

Scored 1–5 on: **Defensible** (survives Article V — is there a real
gap?), **Falsifiable** (can we be proven wrong cheaply?),
**Differentiated** (is NOVA the obvious place to do it?),
**Scoped** (can a small team reach a useful v1?),
**Adoptable** (is there a path into real codebases?).

| # | Thesis | Def | Fals | Diff | Scope | Adopt | Total |
|---|---|---|---|---|---|---|---|
| **T1** | **The obligation row** | 4 | 5 | 4 | 4 | 3 | **20** |
| **T2** | **The capability-safe component language** | 4 | 4 | 4 | 4 | 5 | **21** |
| T3 | The verified-enough systems language | 3 | 3 | 2 | 2 | 3 | 13 |
| T4 | The tierless / choreographic language | 4 | 3 | 3 | 1 | 2 | 13 |
| T5 | The adaptive / schedule-separated language | 2 | 2 | 2 | 1 | 2 | 9 |

### T1 — The obligation row *(the intellectual thesis)*

> Every non-functional obligation a program is under — authority, effects,
> cost, retry policy, instrumentation, and eventually taint — is carried
> by **one** graded row on function types, derived from context rather
> than authored, and checked compositionally.

**Why it ranks high.** It is the only thesis here that *unifies* rather
than adds, it is directly falsifiable (§2's three experiments), and four
of the five Underexplored problems in Phase 0 fall inside it.

**What would falsify it.** Grades that do not compose across branches;
a `widen` rate above 10% (RFC 0001 §7); instrumentation derived from rows
that nobody wants; budgets that need a mechanism unrelated to rows.

**Its weakness.** Adoptability. "Better types for obligations" does not
move a working engineer on its own.

### T2 — The capability-safe component language *(the strategic thesis)*

> NOVA is the language for building systems out of **mutually distrusting
> components**: no ambient authority, capability requirements as part of
> every published interface, compiled to WebAssembly components so it can
> be adopted one module at a time.

**Why it ranks highest overall.** It scores where T1 is weak. It answers
a problem people are actively bleeding from (P14: supply-chain), it has
an incremental adoption path that does not require a trusted FFI hole
(P24), and it aligns with the one capability system that has industrial
momentum. It is also *demonstrable* — a supply-chain demo where a
malicious dependency simply cannot open a socket is a thing you can show
in ninety seconds.

**What would falsify it.** Capability-passing proving intolerable in
practice (measure: parameter counts and manifest churn in a real
program); Component Model tooling not maturing; the guarantee turning out
to be defeatable in ordinary code.

### T3 — The verified-enough systems language

Rust-class memory safety plus layered SMT verification. Defensible and
useful, but the field is crowded — Verus, Creusot, Kani, Vale, Austral —
and NOVA has no memory model yet. This is a *milestone*, not a thesis.

### T4 — The tierless / choreographic language

One program, many locations, tier split by projection. Intellectually the
most attractive and the highest risk: Ur/Web and Links solved a version of
this and did not win, and NOVA has no answer yet to *why*. Scope is far
beyond a small team pre-Milestone 3.

### T5 — The adaptive / schedule-separated language

Speculative outside array pipelines (P22, R20). No operational semantics.
Article VIII applies. Not a thesis; a research direction for someone else
right now.

### Recommendation

**Adopt T1 as the thesis and T2 as its expression.**

They are not competitors — T2 is what T1 looks like to a user, and T1 is
why T2 is sound. The row is the mechanism; capability-safe components are
the product. That pairing gives NOVA:

- a falsifiable technical claim (T1),
- a demonstrable user-visible benefit (T2),
- an adoption path that does not require rewriting the world (P24),
- and a reason to build the memory model *second*, which is where it
  honestly belongs given that Rust already did it better.

The one thing this recommendation demands in return is discipline about
Theme B: **the memory model will constrain the capability model**, and
RFC 0001 must be treated as provisional until Milestone 1 closes, not as
settled.
