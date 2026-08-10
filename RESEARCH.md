# NOVA — Research Review

Phase 0 literature review across the twenty-one areas in scope. The
purpose is to establish what is **known**, so that NOVA does not
re-discover it and does not claim it.

---

## Maturity scale

Every finding below is tagged with one of:

| Tag | Meaning |
|---|---|
| **Established** | Shipped in production languages; textbook; the design questions are settled. |
| **Well researched** | Substantial literature and at least one real implementation; understood, but not mainstream. Adoption, not existence, is the open question. |
| **Experimental** | Implemented in research languages or one young production language; practical questions unresolved. |
| **Underexplored** | Obviously important; little literature or no serious implementation. |
| **Speculative** | No known operational semantics. May not be a coherent idea. |

Constitution Article V binds every claim in this document. Where NOVA has
a possible contribution, the sentence is phrased so it can be *falsified*
by a reviewer producing a citation.

---

## R1 — Memory safety

**Established.** Tracing GC; ARC; RAII; ownership + borrowing (Rust);
region-based allocation (Tofte & Talpin 1997; Cyclone, Grossman et al.
2002). Rust's model has a machine-checked soundness proof — RustBelt
(Jung, Jourdan, Krebbers & Dreyer, POPL 2018) — which is the strongest
formal result in the area and worth reading before proposing anything.

**Well researched.** Compile-time reference counting: *Perceus*
(Reinking, Xie, de Moura & Leijen, PLDI 2021), shipped in Koka and Lean 4,
with functional-but-in-place (FBIP) style. Aliasing models for
`unsafe` Rust: Stacked Borrows (Jung et al. 2020) and its successor Tree
Borrows. Linear and affine types back to Wadler (1990) and Girard (1987).

**Experimental.** *Generational references* (Vale) — a fat pointer with a
generation counter, giving use-after-free detection at low cost, claimed
to remove most borrow-checker annotation. Unproven at scale. *Regions as
the unit of ownership*: Verona (Microsoft Research) and Vale's region
borrowing. *Hardware capabilities*: CHERI and Arm Morello — real silicon,
real deployments, and a genuinely different point in the design space.

**Underexplored.** A memory model designed *around* an existing capability
and effect discipline, rather than beside one. Every system above chose
memory first. NOVA is, unusually, choosing effects first — which is either
an opportunity or a mistake, and Milestone 1 will decide which.

**What NOVA can rely on.** Nothing NOVA does here will beat Rust on
soundness. The realistic goal is Rust's guarantees at Swift's annotation
burden, and the most promising route is regions, because a region is a
value that can be *handed over* — the same shape as a capability.

---

## R2 — Type systems

**Established.** Hindley–Milner inference; System F and F-omega; algebraic
data types and exhaustive pattern matching; type classes (Wadler & Blott
1989) vs ML modules; parametricity (Reynolds 1983; Wadler's *Theorems for
Free!*); GADTs; variance and subtyping; bidirectional type checking
(Pierce & Turner 2000) — the practical basis for annotation-light checking
without full inference.

**Well researched.** Row polymorphism — Wand (1987), Rémy (1989), and
Leijen's *Extensible Records with Scoped Labels* (2005), which is the
algorithm NOVA's rows use. Refinement types: Freeman & Pfenning (1991);
Liquid types (Rondon, Kawaguchi & Jhala, PLDI 2008). Gradual typing (Siek
& Taha 2006) and its costs (Takikawa et al., *Is Sound Gradual Typing
Dead?*, POPL 2016 — the honest answer was largely "yes, at the boundaries").
Quantitative Type Theory (Atkey 2018), which underpins Idris 2 and unifies
linear, affine and unrestricted use in one system.

**Experimental.** Graded modal types (Granule; Orchard, Liepelt & Eades
2019) — types indexed by a semiring describing *how much* a value is used.
This is the most likely formal home for NOVA's resource budgets. Modular
implicits; higher-rank inference in practice.

**Underexplored.** Type systems designed for *diagnostic quality* as a
first-class constraint. Constitution Article X asserts this matters and
the literature is surprisingly thin — the exception being work on error
localisation for HM inference and Elm's engineering practice, which was
never written up as research.

**What NOVA can rely on.** Bidirectional checking plus Leijen's row
unification is a complete, well-understood foundation for v0.1. NOVA needs
no new type theory before Milestone 2.

---

## R3 — Effect systems

**Established.** Monads (Moggi 1991; Wadler 1992) and `IO` as a coarse
effect. Ad-hoc colouring: `async`, `throws`, `const`, `suspend`.

**Well researched.** Algebraic effects and handlers: Plotkin & Power
(2003); Plotkin & Pretnar's *Handlers of Algebraic Effects* (2009); **Eff**
(Bauer & Pretnar). Row-typed effects: **Koka** (Leijen, *Koka: Programming
with Row-Polymorphic Effect Types*, 2014); **Links** (Cooper, Lindley,
Wadler & Yallop); **Frank** (Lindley, McBride & McLaughlin, POPL 2017).
Extensible effects in Haskell (Kiselyov, Sabry & Swords 2013) and the
modern library generation (`effectful`, `cleff`, `fused-effects`).
**Unison**'s abilities. **F\***'s user-definable effect lattice via
Dijkstra monads. **OCaml 5** shipped handlers with *no* type-level
tracking — an instructive, deliberate retreat.

**The finding that changes RFC 0001.**

> **Effekt** — Brachthäuser, Schuster & Ostermann, *Effects as
> Capabilities: Effect Handlers and Lightweight Effect Polymorphism*
> (OOPSLA 2020), plus *Effects, Capabilities, and Boxes* (OOPSLA 2022).

Effekt already unifies effects and capabilities. Its key move: effect
capabilities are **second-class** — they cannot be captured in closures,
stored, or returned — which gives *contextual* effect polymorphism with no
row variables and very light annotation. The 2022 follow-up adds "boxes"
to let capabilities become first-class *when explicitly boxed*, and the
box's type records the captured capability set.

This is close enough to RFC 0001 that the RFC's novelty claim must be
narrowed. Honest comparison:

| | Effekt | NOVA RFC 0001 |
|---|---|---|
| Effect = capability | ● yes | ● yes |
| Capabilities first-class | ○ (second-class; boxed with annotation) | ● always |
| Capture of authority | forbidden by default | permitted, and reflected in the row |
| Effect polymorphism | contextual, implicit | explicit row variables |
| Row discipline | none needed | Leijen scoped labels |
| Declared row vs inferred | inferred | **checked for equality** |
| Handlers | ● core | deferred |

**Revised claim.** "Effects as capabilities" is **not** NOVA's idea and
RFC 0001 §3 must cite Effekt as the nearest prior art. What remains
unclaimed by any system this review found is narrower:

> Effect rows checked for **equality** rather than subsumption, over
> **first-class** capabilities, with a single syntactically greppable
> widening construct.

Whether that is *desirable* is untested — it may simply be too strict, and
RFC 0001 §7 already names the `widen` rate as the falsification test.
Effekt's 2022 "boxes" paper is the strongest argument that the
first-class/second-class question is the real design axis.

**Underexplored.** Effect labels carrying *algebraic properties*
(idempotent, commutative, compensatable) that constrain polymorphic
instantiation — see [P10](PROBLEM-SPACE.md#p10--failure-semantics-are-untyped).
Effects as the source of observability instrumentation —
[P21](PROBLEM-SPACE.md#p21--observability-is-bolted-on-and-drifts).
Both are downstream of machinery that already exists.

**What NOVA can rely on.** The theory is finished. NOVA's contribution, if
any, is in what the row is *used for* and whether the discipline is
tolerable to working programmers. Those are engineering and empirical
questions, and they should be described as such.

---

## R4 — Capability security

**Established.** The object-capability model: Dennis & Van Horn (1966);
KeyKOS; EROS; Mark Miller's *Robust Composition* (2006), which is the
definitive statement. No ambient authority, no designation without
authority, unforgeable references. Language realisations: **E**, **Joe-E**
(Mettler & Wagner), **Caja**, **Monte**, **Pony**'s `AmbientAuth`,
**Austral**'s linear capabilities.

**Established (negative result).** Java's `SecurityManager` attempted
authority control at runtime via stack inspection on a language with
ambient authority. It was deprecated and removed (JEP 411, JEP 486). This
is the cleanest evidence available for Constitution Article IV.

**Well researched.** Taming — mechanically restricting an existing library
to a capability-safe subset (Joe-E's treatment of the JDK). Attenuation
and facets, and the trust obligation they carry. Confused-deputy analysis
(Hardy 1988).

**Experimental / industrial.** **WASI Preview 2** and the **WebAssembly
Component Model**: capability-based imports, shared-nothing linking, WIT
interface types, and virtualisable interfaces. This is object-capability
discipline with real industrial momentum, at module granularity.
**CHERI**: capabilities in hardware, with production silicon.

**Underexplored.** Capability requirements as part of a *published package
interface*, checkable at install time —
[P14](PROBLEM-SPACE.md#p14--a-dependency-inherits-all-of-your-authority).
The Component Model does this per component; nothing does it per package
inside a language.

**What NOVA can rely on.** The model is fully worked out; NOVA is applying
it, not extending it. The unsolved part is ecological: capability
discipline only works if the *entire* standard library is written that
way from the first day, which is precisely why Article IV puts it in the
core.

---

## R5 — Resource-aware programming

**Well researched.** Automatic Amortised Resource Analysis: Hofmann & Jost
(POPL 2003); **RAML** (Hoffmann, Aehlig & Hofmann) — infers polynomial
bounds on heap, time and stack for a real functional language. This works
and is far less known than it should be. Cost-annotated compilation
(CerCo). Implicit computational complexity as a field. WCET analysis in
Ada/SPARK for avionics.

**Experimental.** Graded modal types (Granule) as a general framework for
"how much" a value is used. Quantitative Type Theory. Linear types for
resource protocols.

**Underexplored.** *Budgets that propagate across call boundaries and are
consumed*, rather than bounds inferred for a closed program. Deadlines are
the special case that matters most in practice —
[P8](PROBLEM-SPACE.md#p8--cancellation-and-deadlines-do-not-compose) —
and the language-level literature on them is close to empty, despite
`context.Context` being one of the most-used APIs in the industry.

**What NOVA can rely on.** RAML shows precise bounds are achievable for
restricted languages. NOVA should aim far lower first: *counting* effect
occurrences (round-trips, allocations, model calls) as a grading on the
row it already computes. That is a small step from RFC 0001 and would be
the first real test of the constraint-native thesis beyond effects.

---

## R6 — Concurrency

**Established.** Threads and locks; CSP (Hoare 1978) → Go; the actor model
(Hewitt 1973) → Erlang, Akka, Orleans; STM (Shavit & Touitou 1995; Harris
et al. 2005) → Haskell, Clojure; work-stealing schedulers (Blumofe &
Leiserson); memory models (Java JMM; C++11).

**Well researched.** Static data-race freedom: ownership types (Boyapati &
Rinard); Deterministic Parallel Java; **Rust**'s `Send`/`Sync` +
borrowing; **Pony**'s reference capabilities (Clebsch, Drossopoulou,
Blessing & McNeil, *Deny Capabilities for Safe, Fast Actors*, 2015).
Deterministic parallelism: LVars (Kuper & Newton).

**Experimental.** **Verona**'s concurrent ownership — regions as the unit
of both memory ownership and concurrency isolation, which is the most
interesting current attempt to unify R1 and R6. **Swift 6**'s
region-based isolation (SE-0414) is the first industrial shipment of a
region-flavoured race-freedom analysis.

**What NOVA can rely on.** Data-race freedom must be a *consequence* of
the memory model, not a parallel mechanism. Rust, Pony, Verona and Swift 6
all demonstrate this; the ones that bolted concurrency on later (Java,
Go) did not get the guarantee.

---

## R7 — Structured concurrency

**Established as a pattern.** Sústrik (2016); Nathaniel Smith, *Notes on
structured concurrency, or: Go statement considered harmful* (2018) — the
essay that named it; Trio's nurseries; Erlang/OTP supervision trees, which
got there decades earlier by a different route.

**Established as an API.** Kotlin `CoroutineScope`; Swift `TaskGroup` and
`async let`; Java's `StructuredTaskScope` (JEP 453 → 480 → 499).

**Underexplored.** *Enforcement.* In every mainstream implementation
except Erlang's process model, structure is a convention the type system
does not check — a task handle can be smuggled out of its scope. Effekt's
second-class values and Rust's lifetimes are the two mechanisms that could
enforce it, and neither language has applied them to task scopes.

**What NOVA can rely on.** The pattern is settled; the enforcement
mechanism is not. A scope-bound, non-escaping `Nursery` capability is the
obvious NOVA design and is blocked on Milestone 1 defining what
"non-escaping" means.

---

## R8 — Distributed programming

**Established.** The eight fallacies; Waldo, Wyant, Wollrath & Kendall,
*A Note on Distributed Computing* (1994) — still correct, still ignored.
Erlang/OTP: location-transparent messaging, supervision, and the only
industrially-proven integration of distribution with a language.
Consensus (Paxos, Raft); CRDTs (Shapiro, Preguiça, Baquero & Zawirski
2011); the CALM theorem (Hellerstein & Alvaro).

**Well researched.** Argus (Liskov); Cloud Haskell; Orleans virtual
actors; session types for protocol conformance (Honda; Honda, Yoshida &
Carbone's multiparty session types, POPL 2008).

**Experimental.** **Choreographic programming** — write one global
protocol, compile it to per-participant code, with deadlock freedom by
construction. Montesi's thesis; **Choral**; **HasChor**; **Pirouette**.
This is the most interesting under-adopted idea in the area, and it is the
*same* idea that solves full-stack tier splitting (R21).
**Unison**'s distributed abilities. **Hydro / Hydroflow** (Berkeley) —
compiling single-node programs to distributed dataflow.
Differential dataflow (McSherry).

**Underexplored.** Latency and partial failure as *type-level gradings* on
a remote capability, rather than as documentation.

**What NOVA can rely on.** Nothing before Milestone 3, and Article VIII
forbids syntax before semantics here. The one durable insight to carry
forward: Erlang succeeded by making the network *visible*, not
transparent, and every system that made it transparent failed.

---

## R9 — Temporal reasoning

**Established.** Temporal logic (Pnueli 1977); **TLA+** (Lamport) and
model checking with TLC; Alloy (Jackson). Industrial use is real: AWS's
use of TLA+ on S3 and DynamoDB, and Microsoft's **P** language for
event-driven systems.

**Well researched.** Session types and typestate (Strom & Yemini 1986;
Plaid) for protocol ordering within a program. Real-time systems: WCET,
rate-monotonic scheduling, Ada/SPARK's Ravenscar profile.

**Underexplored / Speculative.** Bringing model-level temporal properties
into the implementation language, so the model cannot drift from the code.
TLA+ and P verify a *model*; nothing checks the model against the shipped
implementation. Staleness bounds as value gradings are the one tractable
sub-problem.

**What NOVA can rely on.** Very little. This is the area where the Vision
is furthest from a design, and NON-GOALS.md places most of it outside
NOVA's scope.

---

## R10 — Uncertainty

**Well researched, under-adopted.** Bornholt, Mytkowicz & McKinley,
*Uncertain\<T\>: A First-Order Type for Uncertain Data* (ASPLOS 2014) —
represents a value as a distribution, makes comparison return evidence
rather than a boolean, and propagates through ordinary code. It is a
decade old, addresses a real and growing problem, and essentially nobody
uses it. That combination deserves study before NOVA proposes anything.
Approximate computing: EnerJ (Sampson et al. 2011). Interval arithmetic;
units of measure (F#).

**Underexplored.** Uncertainty from *model outputs* specifically — an LLM
classification is an uncertain value and is universally treated as exact.

**What NOVA can rely on.** `Uncertain[T]` is a library-shaped idea in a
language with graded types. It should not get syntax.

---

## R11 — Probabilistic programming

**Established.** The field is mature: Church (Goodman et al. 2008);
Anglican; Stan; **Gen** (Cusumano-Towner et al., PLDI 2019); Pyro;
Turing.jl; Infer.NET. Inference algorithms (MCMC, HMC, variational,
programmable inference) are the substance of the field.

**Well researched.** Probability as an algebraic effect — `sample` and
`observe` as operations with handlers is a textbook example in the effect
literature, and it is how Koka and several Haskell libraries present it.

**What NOVA can rely on.** This is a **library**, not a language feature,
in any language that has effect handlers. That is the correct conclusion
and it is recorded in NON-GOALS.md. Building a PPL into NOVA would be
Article VIII futurism.

---

## R12 — Formal verification

**Established.** Hoare logic; separation logic (Reynolds, O'Hearn);
SMT-based verification — **Dafny** (Leino) on Boogie/Z3, with sustained
industrial use at AWS; **Ada/SPARK** in avionics and rail. Dependent
types: Coq/Rocq, Agda, Idris, **Lean 4**. **F\*** with extraction to C
(KaRaMeL), and the Project Everest artefacts (HACL\*, EverCrypt,
miTLS) — verified crypto in production browsers.

**Well researched.** Refinement types with SMT: Liquid Haskell.
Verification for Rust: **Verus**, **Creusot**, **Prusti**, **Kani**
(bounded model checking) — a genuinely active area, and the closest
analogue to what NOVA would want.

**Established (negative).** Full functional verification does not scale to
whole applications at acceptable cost. Every industrial success is
*targeted*: crypto cores, protocol state machines, schedulers.

**What NOVA can rely on.** Layering is the only viable posture: opt-in,
pay-nothing-if-unused, SPARK-level ambition. Verus is the model to study
because it is verification layered onto an ownership language, which is
the shape NOVA will be in after Milestone 1.

---

## R13 — AI programming

**Experimental.** Structured generation and constrained decoding
(Outlines, Guidance, JSON-schema-constrained sampling) — the one place
where a *type* meaningfully constrains a model's behaviour today.
**DSPy** (Khattab et al.) — programs over language models with compiled
prompts, the closest thing to a principled programming model. LMQL; BAML;
TypeChat; Instructor.

**Underexplored.** Treating a model call as what it actually is: a
capability, an effect with unbounded latency and cost, a nondeterministic
function, and a **taint source**. Every component exists in the
literature; nobody has assembled them.

**Speculative.** Anything described as an "AI-native language". No
published operational semantics exists for such a thing, and Article VIII
applies directly.

**What NOVA can rely on.** The correct NOVA position is that a model call
needs *no new mechanism* — capability (R4) + effect (R3) + budget (R5) +
taint (R14). If those four cover it, that is evidence the mechanisms are
right. If NOVA needs AI-specific syntax, something upstream is wrong.

---

## R14 — Information flow and agent security

**Well researched, consistently unadopted.** Denning & Denning (1977);
Myers & Liskov's decentralised label model; **Jif**/JFlow; FlowCaml;
Sabelfeld & Myers' survey (2003); Sabelfeld & Sands on the dimensions of
declassification (2005); **LIO** (Stefan et al.) for dynamic IFC in
Haskell; Jeeves.

The consistent finding across thirty years: IFC is theoretically solid,
and annotation burden plus the declassification problem have prevented
adoption every time. This is a *warning*, not an invitation.

**Underexplored.** IFC as the solution to prompt injection — untrusted
model output reaching a privileged sink is precisely an information-flow
violation, and the agent-security literature has largely not connected to
the IFC literature.

**Structural observation.** Capability-effects and information flow are
**dual**: one constrains *authority* flowing outward, one constrains
*data* flowing inward. No language has both. Whether they can share a
mechanism is a genuine open question and is examined in
[DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md).

---

## R15 — Heterogeneous computing

**Established.** CUDA; OpenCL; SYCL; OpenMP offload; the two-language
split as the status quo.

**Well researched.** Separation of algorithm and schedule: **Halide**
(Ragan-Kelley et al., PLDI 2013) — the single most important idea in this
area. **TVM**; **Exo** (Ikarashi et al., PLDI 2022); Futhark; polyhedral
compilation.

**Experimental.** **MLIR** (Lattner et al., CGO 2021) as shared
infrastructure for progressive lowering across dialects. **Mojo** as the
first serious attempt at one language spanning CPU and accelerator with
ownership and MLIR underneath.

**What NOVA can rely on.** This is an **IR decision**, made in
Milestone 3. Choosing LLVM alone quietly forecloses it. That should be a
deliberate decision recorded in an RFC, not a default.

---

## R16 — WebAssembly, WASI and the Component Model

**Established.** The core Wasm spec has a full formal semantics — rare and
valuable. Sandboxing by construction; deterministic execution modulo
declared nondeterminism; broad toolchain support. Shipped extensions:
SIMD, threads, reference types, tail calls, exception handling, WasmGC,
memory64.

**Experimental / industrial.** **WASI Preview 2** and the **Component
Model**: WIT interface definitions, the canonical ABI, shared-nothing
linking, per-component capability imports, and interface virtualisation.
Preview 3 adds async composition. The **stack-switching** proposal is
directly relevant to implementing effect handlers efficiently.

**What NOVA can rely on.** A great deal, and this may be the most
important strategic finding in Phase 0. The Component Model is
capability-based module linking with industrial backing, and it aligns
almost exactly with NOVA's authority model one level up. Targeting it
gives NOVA:

- a portable target with a formal semantics,
- an *incremental adoption* story ([P24](PROBLEM-SPACE.md#p24--new-languages-cannot-incrementally-take-over-a-codebase)) that does not require a trusted C FFI hole,
- a natural boundary at which NOVA's capability rows become WIT imports.

---

## R17 — Incremental compilation

**Established.** Self-adjusting computation (Acar); Salsa; rustc's query
system; **Roslyn** as compiler-as-a-service; *Build Systems à la Carte*
(Mokhov, Mitchell & Peyton Jones, ICFP 2018) — the clean framework for
thinking about build systems and caches.

**Well researched.** Content-addressed code as an incrementality strategy:
**Unison** dissolves rebuild, rename and dependency-conflict problems by
identifying definitions with hashes rather than names.

**Established (negative).** Retrofitting demand-driven architecture is a
rewrite. rustc/rust-analyzer is the canonical example of paying twice.

**What NOVA can rely on.** No research needed — only discipline, applied
from the first commit. Already binding in ARCHITECTURE.md.

---

## R18 — Package management

**Established.** SAT-based resolution (npm, Cargo); **Minimal Version
Selection** (Go; Cox 2018) — simpler, reproducible, and underrated; Nix's
content-addressed derivations; lockfiles; checksum transparency logs.

**Well researched.** **Elm**'s enforced semver: the publisher does not
choose the version bump; the tool computes it from an API diff and
refuses a wrong one. This is the only shipped system that makes semver a
*checked property*. **Unison** removes the problem by content-addressing
definitions.

**Underexplored.** Publishing *capability requirements* as part of the
interface, so authority creep in a dependency is a detectable breaking
change — [P14](PROBLEM-SPACE.md#p14--a-dependency-inherits-all-of-your-authority).
Supply-chain provenance (SLSA, sigstore) proves *who built* an artefact,
never *what it does*.

**What NOVA can rely on.** MVS + Elm-style computed compatibility +
capability manifests is an assemblable design from three proven parts.
This is one of the cheapest high-value items in the whole review.

---

## R19 — Observability

**Established.** Dapper (Sigelman et al. 2010) and distributed tracing;
OpenTelemetry as the interoperability layer; structured logging; eBPF and
auto-instrumentation; continuous profiling; Erlang's built-in tracing
BIFs, which remain the best language-integrated observability in
production.

**Well researched.** Causal profiling — **Coz** (Curtsinger & Berger,
SOSP 2015). Provenance and dynamic taint tracking as debugging tools.

**Underexplored.** Deriving instrumentation from a program's *type*.
A function's effect row is already a description of what it does; span
boundaries could be generated from capability uses rather than
hand-placed. This is mentioned in passing in effect-system papers and has
no serious implementation.

**What NOVA can rely on.** A small, concrete, early experiment: generate
trace spans from capability operations and compare against hand-written
instrumentation. It is cheap and it tests whether the row carries real
information.

---

## R20 — Adaptive and self-optimising software

**Established.** JIT compilation and tiered optimisation (HotSpot, V8,
PyPy's meta-tracing, GraalVM/Truffle partial evaluation); profile-guided
optimisation; AutoFDO; BOLT; adaptive inlining.

**Well researched.** Autotuning (ATLAS, OpenTuner, Halide's
autoscheduler); superoptimisation; ML-guided compiler heuristics (MLGO in
LLVM, CompilerGym).

**Speculative.** "Software that rewrites itself for its workload" as a
*language* feature. There is no operational semantics for it, and the
Vision's "Execution Strategy" and "Adaptive" terms are currently
categories rather than designs — Article VIII.

**What NOVA can rely on.** The tractable, non-speculative core is
Halide's: **separate the algorithm from the schedule**, so that changing
the *how* does not touch the *what*. Whether that generalises beyond array
pipelines is unknown and is the open question in
[P22](PROBLEM-SPACE.md#p22--performance-tuning-is-entangled-with-algorithm).

---

## R21 — Full-stack application development

**Well researched, under-adopted.** **Ur/Web** (Chlipala, POPL 2015) —
one statically typed language for client, server and database, with
metaprogramming and strong guarantees (no XSS, no dead intra-app links, no
SQL injection *by typing*). **Links** (Cooper, Lindley, Wadler & Yallop
2006) — "web programming without tiers", with an effect system doing the
tier-splitting work. **Eliom/Ocsigen** — client/server sections in OCaml.

**Established industrially.** tRPC; React Server Components; Phoenix
LiveView; Blazor. All solve type-sharing within one framework; none gives
a static account of what crosses the wire or what authority each tier
holds.

**Experimental.** Choreographic programming (R8) is the same problem
viewed from distributed systems, and is the more principled framing:
a tier split is an endpoint projection of a global program.

**The lesson NOVA must absorb.** Ur/Web and Links solved this well over a
decade ago and did not win. Any NOVA work here must first answer *why*,
or it will lose the same way. The most likely answers are ecosystem
gravity and the cost of being unable to use existing libraries — which is
an argument for [P24](PROBLEM-SPACE.md#p24--new-languages-cannot-incrementally-take-over-a-codebase)
being more important than the feature itself.

---

## Summary: where the literature is thin

Of twenty-one areas, five have a genuine gap between obvious importance
and available work:

| Area | Gap |
|---|---|
| R5 / P8 | Deadlines and budgets that **propagate and are consumed** across calls |
| R3 / P10 | Effect labels carrying **algebraic properties** that constrain polymorphism |
| R18 / P14 | **Capability manifests** as part of a published package interface |
| R19 / P21 | Instrumentation **derived from types** rather than hand-placed |
| R13 / R14 | Model calls as capability + effect + budget + **taint**, assembled |

Four of the five are downstream of an effect row. That is the central
result of Phase 0 and is developed in
[DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md).
