# NOVA — Design Principles: the Feature Hierarchy

Phase 1 output. Constitution Article VII treats subtraction as progress
and Article VI sets a bar for admission; neither tells a contributor
*where* a feature belongs once admitted. This document is that
classification, so that "NOVA is growing a feature" is always answerable
with "in which of six tiers, and why there rather than one tier up."

Every future RFC (per [RFC 0000](RFC/0000-rfc-process.md)) should state
which tier it targets and defend the classification using the test below.
Misclassifying a feature — putting an Optional feature in Core, or a
Runtime concern in the standard library — is exactly the kind of mistake
that causes uncontrolled growth, because each tier has a different cost
model and a feature costed as the wrong tier gets approved too easily.

---

## The six tiers

### Core

**Test:** cannot be added later without breaking every existing program
(Constitution Article IV), *or* is required for every program regardless
of what it does (there is no NOVA program without an entry point).

**Cost model:** paid by every program, every compile, unconditionally.
The bar for admission here is the highest in the hierarchy — Constitution
Article VI in full, plus Article IV's retrofitting test specifically.

**Currently in Core:** capability declarations, effect rows, the
derivation rule (RFC 0001); the entry-point convention
(`main(rt: Runtime)`). **Committed but unbuilt:** the memory discipline
(Milestone 1) — committed because Article XI already forbids the core
from assuming unrestricted aliasing, which constrains Core in advance of
Core actually containing a memory model.

### Optional language feature

**Test:** changes the type system, the checker, or the surface grammar,
but a program using none of it is unaffected in cost or required
ceremony (Constitutional Principle 10). Removable in principle without
changing the meaning of any program that didn't use it.

**Cost model:** paid only by programs that opt in; zero marginal cost
(parse time, check time, AST shape) for programs that don't. This is the
tier where "pay nothing if unused" is a testable regression-suite
obligation, not a slogan.

**Candidates, not yet built:** generics (Milestone 2), algebraic data
types and pattern matching (Milestone 2), effect handlers (deferred past
Milestone 1 per [NON-GOALS.md §2.1](NON-GOALS.md#21-effect-handlers)),
graded rows (Milestone 5, and per
[Experiment 003](docs/experiments/003-graded-rows.md), this one requires
a unification change — still Optional, because a program that declares
no grades is unaffected), refinement types (Milestone 6).

### Standard library

**Test:** implementable *in* NOVA itself using only Core and Optional
features already accepted, with no compiler special-casing. If it needs
the compiler to know about it by name, it is not standard library.

**Cost model:** paid only by programs that import it; ships with the
toolchain but is otherwise an ordinary dependency, versioned and
manifest-checked like any other (per
[Experiment 001](docs/experiments/001-capability-manifests.md)).

**Candidates, not yet built (blocked on generics existing at all —
[ROADMAP.md](ROADMAP.md) Milestone 2):** collections, string formatting,
`Uncertain[T]`
([LANGUAGE-PHILOSOPHY.md entry 11](LANGUAGE-PHILOSOPHY.md#11-uncertainty)),
a `Metrics` capability whose operations carry sampling/redaction metadata
— the exact refinement
[Experiment 002](docs/experiments/002-rows-to-spans.md) found missing
(derived traces give shape; semantic labeling needs to live somewhere,
and a capability with declared metadata is the somewhere, not a new
compiler feature).

### Tooling

**Test:** operates on NOVA programs or their published interfaces but is
outside the compiled program's own semantics entirely. Could be deleted
without any NOVA program's meaning changing.

**Cost model:** paid only by whoever runs the tool. No interaction with
Core's cost obligations at all.

**Already built, and worth naming as a worked example that this tier is
not hypothetical:** `tools/manifest-diff.py`
([Experiment 001](docs/experiments/001-capability-manifests.md)) —
diffs two versions of a program's published effect rows and flags
authority growth. It required zero changes to the checker, the grammar,
or the runtime. That is what makes it Tooling rather than an Optional
feature: delete it, and every NOVA program still means exactly what it
meant before. **Also here:** the `audit` and `grade` (experimental)
subcommands of `verifier/refspec/__main__.py`, a future formatter, a
future LSP (Milestone 0/ongoing), a future package manager (Milestone 2).

### Runtime

**Test:** the non-compiled, host-provided implementation of root
capabilities and execution services. Swapping one implementation for
another must never change a program's *checked* meaning (Principle 8,
semantic portability) — only its performance or environment.

**Cost model:** paid at execution, not at compile time; invisible to the
type system by design (a program cannot observe which `Runtime`
implementation it was handed, only what its declared capabilities let it
do).

**Already built:** `Interpreter.make_runtime()` in
`verifier/refspec/eval.py` — the reference implementation of the
`Runtime` and `Clock` capabilities. **Not yet built:** a native runtime,
a `wasm` host runtime, a region/allocation manager (once Milestone 1
lands), a scheduler (once Milestone 4 lands).

### Research extension

**Test:** no operational semantics exists yet (Constitution Article VIII).
Lives only as an idea an RFC could eventually formalize; explicitly not
scheduled against any milestone.

**Cost model:** none — nothing here is built, and nothing here may gate
or delay work in the other five tiers.

**Currently here, cross-referencing
[NON-GOALS.md §2](NON-GOALS.md#2-things-that-are-premature-not-wrong):**
choreographic distribution (P11/P12), general execution-strategy
scheduling (P22,
[LANGUAGE-PHILOSOPHY.md entry 12](LANGUAGE-PHILOSOPHY.md#12-execution-strategy)),
information-flow control (P20, Constitutional Principle 11), temporal/
staleness properties (P17), heterogeneous-hardware codegen (P23) beyond
whatever Milestone 3's IR choice happens to enable for free.

---

## Worked classification: twelve items from Phase 0

Concrete enough to be checked, not just described. Drawn from
[PROBLEM-SPACE.md](PROBLEM-SPACE.md) and the experiments.

| Item | Tier | Why not one tier up |
|---|---|---|
| Effect row derivation (RFC 0001) | **Core** | Retrofitting later breaks every signature — Article IV's test, met exactly. |
| Memory discipline (Milestone 1) | **Core** | Same test: every aliasing assumption in every library would need to change. |
| Generics | **Optional** | A non-generic program is unaffected; removable without changing any monomorphic program's meaning. |
| Graded rows (P9) | **Optional**, pending a type-system RFC | Experiment 003: cannot be a Tooling-level afterthought pass — must sit inside unification — but a program declaring no grades still pays nothing, so it is not Core. |
| Refinement types (Milestone 6) | **Optional** | Layered, opt-in, pay-nothing-if-unused is the explicit design constraint (RFC 0001 comparison table, R12). |
| `Uncertain[T]` (P18) | **Standard library** | A generic type over data, nothing compiler-special about it, per Language Philosophy entry 11. |
| Retry-safety labels on capabilities (P10) | **Standard library** *or* Optional, undecided | Genuinely open: if "idempotent" is just a marker capabilities can declare, it's stdlib; if it must constrain row-polymorphic instantiation at the type level, it's Optional. Not yet designed either way — recorded as open rather than forced into a tier prematurely. |
| Capability manifest diffing (P14) | **Tooling** | Experiment 001, built, and it required zero compiler changes — the clearest possible example of this tier. |
| Rows-to-spans tracing (P21) | **Tooling** | Experiment 002: a wrapper around the reference evaluator, no grammar or checker change. |
| Native code generation | **Runtime** *and* compiler backend (outside this hierarchy — see note) | Backend/codegen is compiler-internal machinery, not a "feature" this hierarchy classifies; the *root capability implementations* it enables are Runtime. |
| Package manager | **Tooling** | Operates on published manifests (Tooling), same as `manifest-diff.py`, at larger scope. |
| Choreographic tier-splitting (P12) | **Research extension** | No operational semantics; Ur/Web and Links solved a version of this and did not win — Article VIII bars syntax before the "why didn't they win" question is answered. |
| AI/agent-specific syntax (P19) | **Explicitly refused**, no tier | Not classified because it is not admitted at all — see [NON-GOALS.md §2.3](NON-GOALS.md#23-ai--or-agent-specific-language-constructs) and [LANGUAGE-PHILOSOPHY.md entry 5](LANGUAGE-PHILOSOPHY.md#5-agent). What "agent" denotes decomposes entirely into Core (capabilities) + Optional (grading) + Research extension (information flow) — no sixth thing is needed, so nothing new is classified. |

The last two rows are deliberate: this hierarchy is also how NOVA says
**no**. A feature that cannot be placed in Core through Research Extension
without inventing a seventh category is a feature that has not been
reduced to what NOVA already has, and Constitution Article VI's question
7 ("can this be simpler?") has not yet been answered for it.

---

## How to use this for a future RFC

RFC 0000 §"Required sections" already asks for staging (§10) and what a
feature forecloses (§8). This hierarchy sharpens both:

1. **State the tier explicitly**, in the RFC's opening summary.
2. **Defend it against the tier one level stricter.** A proposed Optional
   feature must explain why it can't be Standard library instead (usually:
   because it needs compiler-level checking, not just an API). A proposed
   Core feature must explain why it can't be Optional (usually: Article
   IV's retrofitting argument, made concretely, the way RFC 0001 §4 does
   for effects and RFC 0001 §6 alternative D declines to do prematurely
   for linear capabilities).
3. **If it doesn't fit any of the six tiers**, that is evidence the
   feature has not been reduced far enough — revisit
   [DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md) before writing the
   RFC, not after.
