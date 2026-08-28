# NOVA — Non-Goals

What NOVA will **not** attempt, and why. Constitution Article VII treats
subtraction as progress; this document is where it is recorded.

A non-goal is not a statement that the idea is bad. Most entries here are
good ideas that belong somewhere else, or good ideas whose time is after
NOVA's core exists. Each entry says which.

Removing something from this list requires an RFC that answers Article VI
in full — in particular question 9, *what does this foreclose?*

---

## 1. Things that are not NOVA's problem

### 1.1 Being a proof assistant

Lean, Coq/Rocq, Agda and Idris exist and are better at this than NOVA will
be. NOVA will not have full dependent types.

**Why:** dependent types tax every programmer, including the ones proving
nothing. Constitution Article III ranks ergonomics above verifiability
precisely so this trade is decided in advance. Milestone 6's target is
SPARK's level of ambition — opt-in refinements, pay nothing if unused —
not Lean's.

### 1.2 Being a probabilistic programming language

Stan, Gen, Pyro and Turing.jl exist. NOVA will not ship inference
algorithms, `sample`/`observe` syntax, or a probabilistic semantics.

**Why:** in a language with effect handlers, a PPL is a *library*
(R11). Building it into the language would add a large semantics for a
narrow audience and violate Article VIII.

### 1.3 Being an array/tensor DSL

Halide, TVM, Exo, Futhark and JAX exist. NOVA will not ship a scheduling
language or an autoscheduler.

**Why:** the algorithm/schedule separation is excellent and, after thirteen
years, still confined to array pipelines. Generalising it is
Open-research (P22). NOVA may eventually *host* such a DSL; it will not
be one.

### 1.4 Being a web framework

NOVA is a language and a compiler. It will not ship a router, an ORM, a
templating engine, or a component model for UI.

**Why:** README already says this. "Full-stack" in the Vision means the
type system can describe a boundary, not that NOVA has opinions about
HTTP verbs. Frameworks are where language projects go to lose focus.

### 1.5 A blockchain, smart-contract, or deterministic-consensus runtime

**Why:** the capability model attracts this suggestion. It is a different
product with different constraints (gas metering, adversarial execution,
consensus determinism) and it would distort every decision in the core.

---

## 2. Things that are premature, not wrong

These have a plausible NOVA design and are deferred with a named gate.

### 2.1 Effect handlers

Was deferred until after the memory model (Milestone 1); the memory
model now exists ([MEMORY-MODEL.md](../../MEMORY-MODEL.md),
[OWNERSHIP-MODEL.md](../../OWNERSHIP-MODEL.md)), which lifts the *precondition*
for this gate — it does not lift the gate itself. Handlers are still not
designed, still not implemented, and still need their own RFC, which
must now address a concrete, newly-answerable question: how does a
captured continuation interact with a live linear exclusive-region
capability on the stack being captured? Region-based ownership makes
this question askable precisely (a continuation capturing a frame that
holds `Excl(Region)` is exactly the case
[OWNERSHIP-MODEL.md §7](../../OWNERSHIP-MODEL.md#7-open-questions) has not
yet considered) — it does not answer it. Remains a non-goal until that
RFC exists.

**Why the original deferral was right:** handlers involve non-local
control flow and capturing continuations, which interacts hard with
ownership. Koka needed Perceus to make it work; OCaml 5 needed a new
runtime. Adding handlers before knowing how NOVA manages memory would
have been deciding the memory model by accident. RFC 0001 §6
alternative E.

### 2.2 Distribution, choreography, and tier splitting

Deferred to Milestone 7, gated on Milestone 3 (a working compiler).

**Why:** Article VIII. NOVA has no operational semantics for a remote
call. Ur/Web and Links solved a version of this over a decade ago and did
not win (R21); until NOVA can say *why*, it would repeat their result.

### 2.3 AI- or agent-specific language constructs

No `prompt` keyword, no `agent` type, no built-in model calls — ever, in
the form of dedicated syntax.

**Why:** a model call decomposes exactly into capability + effect +
budget + taint (R13). If NOVA's existing mechanisms cover it, no new
syntax is warranted; if they do not, something upstream is wrong and
should be fixed there. This is the clearest possible application of
Article VIII, and it is the area where the industry is most eager for
NOVA to be undisciplined.

### 2.4 Uncertainty as a language feature

`Uncertain[T]` (Bornholt et al. 2014) is a good idea and is
library-shaped in a language with graded types (R10). It does not get
syntax.

### 2.5 Self-hosting

Not before Milestone 3, and not a goal in itself.

**Why:** self-hosting is a milestone that feels like progress and mostly
costs time. It matters when the language is stable enough that the
compiler is a good stress test — not before.

### 2.6 A package registry

Milestone 2 at the earliest, and the interesting question is the manifest
(P14), not the hosting.

---

## 3. Things NOVA is deliberately not competing on

### 3.1 Beating Rust on memory safety

NOVA has no memory model. Rust's is machine-checked (RustBelt). Any
NOVA claim to improve on it before Milestone 1 is prohibited by Article V.
The realistic goal is Rust's guarantees with less annotation, and even
that is a hypothesis.

### 3.2 Beating Go on compile speed, or C on codegen quality

Both are worth wanting and neither is a differentiator. NOVA will lose
both for years.

### 3.3 Feature count

Article VII. NOVA will have fewer features than every language it is
compared to, for a long time, on purpose.

### 3.4 Syntax novelty

The surface syntax is provisional and unremarkable by design. CONTRIBUTING
already declines syntax-preference feedback. A language remembered for its
syntax has failed to be remembered for its semantics.

---

## 4. Things that are tempting and structurally dangerous

### 4.1 Information-flow control, for now

NOVA will **not** claim taint tracking, PII protection, or
prompt-injection safety until an RFC exists. SECURITY.md already says so.

**Why this is in this section rather than §2:** IFC is the most tempting
addition, because "no ambient authority" *sounds* like it should already
imply it. It does not (DESIGN-OPPORTUNITIES §5). Thirty years of research
shows the hard part is declassification, and capabilities contribute
nothing to it. Claiming otherwise would be a security lie, which is worse
than a missing feature.

### 4.2 Silent effect subsumption

RFC 0001 checks rows for **equality**. The pressure to relax this to
subsumption will be constant, because equality is annoying.

**Why it is dangerous:** subsumption is how effect rows rot. Once a
signature may over-claim silently, rows drift from reality and the whole
mechanism becomes decoration. If equality proves untenable, the answer is
an RFC that changes it deliberately with measurements — the `widen` rate —
not a quiet relaxation.

### 4.3 An ambient standard library

`std` will never grow a free `print`, `now`, or `open`. This is the single
largest ergonomic cost NOVA is accepting (RFC 0001 §8) and the concession
most likely to be requested "just for logging".

**Why it is dangerous:** one ambient function defeats the entire authority
model, because any code can call it. Java's `SecurityManager` is the
worked example of trying to recover from this and failing.

### 4.4 A `#[no_effects]` / trust-me attribute

Any per-call escape from the effect system that is not `widen` or an
audited attenuation boundary.

**Why it is dangerous:** escape hatches accumulate. The whole value of the
row is that it is *complete*; one uncounted hole makes every audit number
meaningless (P2).

### 4.5 Adding a term from the Vision's program model because it is in the Vision

"Intent", "Uncertainty", "Execution Strategy", "Adaptive" and
"Distributed" appear in the Vision's program model. Several are categories
rather than designs. Article VIII: they do not get syntax until they have
an operational semantics, and a term's presence in the Vision is not an
argument for implementing it.

---

## 5. Where this leaves NOVA

After removing all of the above, NOVA v1 is a much smaller language than
the Vision suggests:

> A statically typed, capability-safe, effect-tracked systems language
> with a memory model, compiling to native code and WebAssembly
> components.

Everything else is either a library, a later milestone, or someone else's
project. That is the intended outcome of Phase 0.
