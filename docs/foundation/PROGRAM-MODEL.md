# NOVA — The Program Model, Challenged

Phase 1 output. The founding documents state a model:

```text
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

The brief for this phase was explicit: *challenge this model. It may be
wrong. Improve it where research shows a better abstraction.* This
document does that, using [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md)'s
definitions and the Phase 0 findings in
[DESIGN-OPPORTUNITIES.md](../../DESIGN-OPPORTUNITIES.md). It ends with a revised
model and a concrete reconciliation with what actually exists today.

---

## 1. What a list with plus signs claims, and what that costs

Writing `A + B + C + …` asserts three things whether or not it means to:

1. **Independence** — each term varies freely of the others.
2. **Peerhood** — each term costs roughly the same to add and matters at
   roughly the same level.
3. **Completeness-by-enumeration** — the model is these ten things and
   nothing hidden between them.

Phase 0's research bears directly on all three claims, and finds each of
them false for at least one term in the list. That is the substance of
this document.

---

## 2. The four terms that collapse into one (Theme A)

**Capabilities, Effects, and Resources are listed as three independent
peers.** [DESIGN-OPPORTUNITIES.md §2](../../DESIGN-OPPORTUNITIES.md#2-theme-a--obligations-are-one-mechanism)
found, and [Experiments 001–003](../experiments) then tested, that
they are not independent:

- a **capability** (entry 7) is a value gating access to something;
- an **effect** (entry 8) is the *checked record* of which capabilities a
  computation touches — already built as a row;
- a **resource** (entry 6) is *what a capability's use accumulates*,
  measurable as a grade on the very same row.

These are not three mechanisms that happen to interact. They are one
row, viewed at three levels of refinement: unit-graded (a set — today's
RFC 0001), naturally-graded (a count — proposed, Milestone 5), and, if a
property lattice is added, policy-graded (idempotence, commutativity —
P10). **Constraints** (entry 9) is the genus that contains all three
levels, plus refinements, which do *not* reduce to the row
([Theme E](../../DESIGN-OPPORTUNITIES.md#5-theme-e--what-does-not-unify)).

So the "+" between Capabilities, Effects, Resources, and (partly)
Constraints is not addition of independent ingredients. It is one
mechanism examined at increasing precision, plus one genuinely separate
mechanism (refinements) that the list does not distinguish from it. The
original model cannot tell a reader which is which; the table in
[LANGUAGE-PHILOSOPHY.md entry 9](LANGUAGE-PHILOSOPHY.md#9-constraint)
now does.

---

## 3. Verification is not a peer — it is an axis on Constraints

The list treats `Verification` as a tenth ingredient, coequal with
`State` or `Behavior`. But ask: verification *of what*? Every answer
points back at a constraint already in the list — a type, a row, a
refinement. There is no such thing as verification in the abstract; there
is only "this particular constraint, discharged to this particular
strength."

[LANGUAGE-PHILOSOPHY.md entry 10](LANGUAGE-PHILOSOPHY.md#10-guarantee)
makes this an explicit four-level ladder (assumption → declared →
guarantee → verified-guarantee) and treats it as a **modifier that
attaches to every constraint**, not a peer ingredient with independent
content. This removes a whole top-level term from the model without
losing any information it was carrying — everything `Verification` meant
is now a property *of* `Constraints`, stated more precisely (which
strength, for which specific constraint) than the original list could
express.

---

## 4. Uncertainty is data wearing a program-model costume

`Uncertainty` sits at the same level as `State` and `Effects` in the
original list, suggesting it is a property of *programs*. Everything
Phase 0 found about it —
[RESEARCH.md §R10](../../RESEARCH.md#r10--uncertainty),
[PROBLEM-SPACE.md P18](../../PROBLEM-SPACE.md#p18--uncertainty-and-approximation-are-untyped) —
says it is a property of **values**: a sensor reading, a model output, a
float accumulation. `Uncertain[T]` (Bornholt et al. 2014) is a generic
type over ordinary data, not a control or authority mechanism, and
[NON-GOALS.md §2.4](NON-GOALS.md#24-uncertainty-as-a-language-feature)
already declines to give it syntax.

Keeping `Uncertainty` as a top-level peer of `State` implies it needs its
own language mechanism, the way `Effects` did. It doesn't.
[LANGUAGE-PHILOSOPHY.md entry 11](LANGUAGE-PHILOSOPHY.md#11-uncertainty)
demotes it to a note under `State`: a value's type may optionally say it
is uncertain, exactly as it may say it is a `List` or an `Option`, once
NOVA has generics to express either.

---

## 5. Execution Strategy has no operational content, and the list hides that

Constitution Article VIII already warns against shipping syntax for a
category with no semantics. `Execution Strategy` is that category today.
[RESEARCH.md §R20](../../RESEARCH.md#r20--adaptive-and-self-optimising-software)
found exactly one working precedent (Halide) confined to one domain
(array pipelines) after thirteen years of trying to generalize it. Listed
as a coequal "+" term, `Execution Strategy` visually claims the same
epistemic status as `State` — a well-understood ingredient waiting to be
built. It is not that; it is an open research problem, and the model
should say so structurally, not just in a footnote.

[LANGUAGE-PHILOSOPHY.md entry 12](LANGUAGE-PHILOSOPHY.md#12-execution-strategy)
keeps the term but attaches exactly one binding constraint to it — any
future design must be meaning-preserving with respect to whatever
`Constraints` already guarantee — and asserts nothing else. This is
weaker than the original list implies, and that is the correction:
the original implied more design maturity than exists.

---

## 6. Intent: the one term Phase 0 has nothing to say about, honestly

`Intent` never appears as a researched concept anywhere in
[PROBLEM-SPACE.md](../../PROBLEM-SPACE.md), [RESEARCH.md](../../RESEARCH.md), or
[COMPETITIVE-ANALYSIS.md](../../COMPETITIVE-ANALYSIS.md), because there is no
citable prior art for "intent" as a formal, checkable program property.
This is worth stating plainly rather than quietly dropping the term or
inventing content for it under pressure to fill out the model.

The honest reading: `Intent` names the informal, human purpose that
`Constraints` are a *lossy, partial formalization of*. This is not a
NOVA-specific insight — it is the standard, decades-old observation in
formal methods that a proof shows a program meets its *specification*,
never that the specification matches what anyone actually wanted (the
"specification gap"). NOVA's model should keep `Intent` for exactly this
reason — to remind readers that formalization is always partial — but it
must be visibly marked as the one ingredient that is **never checked**,
structurally different in kind from every other term in the list, not a
peer waiting for its own mechanism.

---

## 7. What survives, unmodified

Two terms in the original list hold up under this review with no
correction:

- **State + Behavior**, i.e. what
  [LANGUAGE-PHILOSOPHY.md entry 2](LANGUAGE-PHILOSOPHY.md#2-computation)
  calls **Computation**: what a program's values are and how they change.
  This is the substance every other term qualifies, and nothing in Phase 0
  suggests collapsing it into anything else.
- **Capabilities/Effects/Resources**, collapsed together per §2 above,
  as **one mechanism examined at three levels** — this is not a survival
  of the original list's shape, but the underlying concern (authority and
  its consequences) is real and central, more central than the original
  flat list suggested.

---

## 8. The revised model

```text
Program  =  Intent                     (informal; the one thing never checked
                                         — the reason Constraints exist at all)

         +  Computation                (State + Behavior: values and how
                                         they change — unchanged from the
                                         original list, merely renamed to
                                         match LANGUAGE-PHILOSOPHY entry 2)

         +  Row                        (Capabilities + Effects + Resources,
                                         ONE mechanism at increasing
                                         precision — Theme A; today: a set
                                         of labels, checked; proposed:
                                         graded, ungated by row polymorphism
                                         — Experiment 003)

         +  Constraints                (the general family: types ⊆ rows
                                         ⊆ refinements — Theme E; each one
                                         carries an explicit Verification
                                         STRENGTH, not a separate ingredient
                                         — the Guarantee ladder)

         +  [Uncertainty is a property of values inside Computation,
             not a peer — demoted, not deleted]

         +  [Execution Strategy remains an explicitly open, ungated slot;
             its one binding constraint is that it must preserve every
             Constraint already established]
```

Ten peer terms become four real ingredients (`Intent`, `Computation`,
`Row`, `Constraints`) plus two deliberately demoted notes kept visible so
they are not silently reinvented as peers later. Nothing that the
original list could express is lost — `Verification` is now a precise
property *of* `Constraints` rather than a vague fifth wheel, and
`Uncertainty` is now a concrete generic type rather than an unscoped
promise.

---

## 9. Reconciling the model with what actually exists

The revised model must agree with the one thing NOVA has actually built.
It does:

```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

is, exactly:

- **Intent**: "handle whatever `main` is for" — unformalized, as it must
  be, and not present anywhere in the signature above. Correct: `Intent`
  is never checked.
- **Computation**: the function body — ordinary `State + Behavior`.
- **Row**: `{Runtime}` — today's unit-graded case of the collapsed
  mechanism, checked by RFC 0001, tested by 25 conformance cases.
- **Constraints**: the type `Int` (weakest constraint, always checked)
  and the row `{Runtime}` (checked for equality, RFC 0001 §4.3) — both
  discharged at **Guarantee** strength (level 3 of the ladder), stated
  explicitly rather than assumed.
- **Uncertainty, Execution Strategy**: absent from this program, which is
  the correct state for both under the revised model — neither is core,
  neither is required, and nothing about `main`'s signature changes when
  they eventually exist.

This is the test the revised model had to pass: the smallest real NOVA
program should already be a complete, correctly-classified instance of
it, with the unbuilt parts visibly and honestly absent rather than
silently assumed.

---

## 10. Disposition

This document does not, by itself, change Constitution Article II's
text — that requires the amendment process
([RFC 0000](../../RFC/0000-rfc-process.md), [GOVERNANCE.md](../../GOVERNANCE.md)).
It is the argument an amendment would cite. Article II has been updated
to point here; see
[docs/constitution-changelog.md](../constitution-changelog.md) for the
recorded change.
