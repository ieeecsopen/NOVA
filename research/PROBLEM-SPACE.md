# NOVA — Problem Space

Phase 0 research. Twenty-four problems in modern programming languages,
assessed for whether NOVA should attempt them.

Every entry ends with a **novelty assessment** on the scale defined in
[RESEARCH.md](RESEARCH.md#maturity-scale):

> **Established** · **Well researched** · **Experimental** ·
> **Underexplored** · **Speculative**

Constitution Article V applies throughout: nothing here is claimed as a
NOVA invention. Where NOVA's angle is genuinely narrow, the entry says so
in one sentence, phrased to be falsifiable.

Difficulty is rated Low / Medium / High / Very High / **Open research**
(meaning: nobody knows how to do this, and a solution would be a paper).
Impact is rated Low / Medium / High / **Transformative**.

---

## P1 — Memory safety still costs too much programmer effort

**Problem.** Rust proved memory safety without GC is possible, but the
cost is a borrow checker that programmers fight for months and data
structures (graphs, doubly-linked lists, back-references) that require
`unsafe`, `Rc<RefCell<_>>`, or arena indices.

**Why it matters.** Roughly 70% of severe CVEs at Microsoft and Google
were memory-safety bugs. The industry has the fix and is adopting it
slowly because the ergonomic cost is real.

**Current solutions.** Tracing GC (Go, Java, C#); ARC (Swift); ownership
+ borrowing (Rust); compile-time reference counting (Koka's Perceus,
Lobster); generational references (Vale); reference capabilities (Pony);
hardware capabilities (CHERI).

**Current limitations.** GC costs latency predictability and blocks
systems use. ARC costs retain/release traffic and cycles leak. Borrowing
costs learning time and expressiveness. Perceus is elegant but assumes a
functional, mostly-immutable core. Vale is unproven at scale.

**Existing research.** Cyclone (regions); RustBelt (Jung et al., semantic
soundness of Rust); Stacked/Tree Borrows; Perceus (Reinking, Xie, de
Moura, Leijen 2021); Verona regions (MSR); Vale's generational references;
Austral's linear types; Quantitative Type Theory (Atkey 2018).

**Potential NOVA solution.** Not yet designed. Deliberately deferred to
Milestone 1 with Constitution Article XI as the guard rail. The leading
candidate is *regions as the unit of ownership* (Verona/Vale-like) rather
than per-value borrowing, because region membership composes with the
capability model NOVA already has: a region is a thing you can be handed.

**Difficulty.** Very High. **Impact.** Transformative.

**Novelty.** **Well researched.** NOVA has no new idea here yet and Rust's
solution is better than anything NOVA could produce today. Any claim
otherwise is prohibited by Article V.

---

## P2 — Escape hatches are unbounded and unaudited

**Problem.** `unsafe`, FFI, reflection, and `any` are all-or-nothing
holes. Rust's `unsafe` disables a specific set of checks but the block
boundary tells you nothing about *which* invariant is being assumed.

**Why it matters.** The trusted computing base of a "safe" program is the
union of every escape hatch in every transitive dependency, and nobody
computes that union. The 2024 xz backdoor lived in build scripts, not even
in the language.

**Current solutions.** Rust's `unsafe` + `# Safety` doc convention;
`#![forbid(unsafe_code)]`; cargo-geiger; Zig's explicit allocator and
`@ptrCast`; Ada/SPARK's partitioning of verified and unverified code;
Java's (withdrawn) SecurityManager.

**Current limitations.** `unsafe` is a single undifferentiated capability.
Auditing is manual and does not compose across a dependency graph. FFI
escapes everything, including the effect system, in every language that
has one.

**Existing research.** RustBelt's "semantic well-typedness" gives a
principled account of what an `unsafe` block owes its callers; Miri;
Fil-C; CHERI's hardware compartments; Joe-E's taming of the Java library.

**Potential NOVA solution.** Make the escape hatch a *capability*, so it
is (a) a value that must be granted, (b) visible in an effect row, and
(c) countable by tooling across the whole dependency graph. `unsafe` stops
being a keyword and becomes `Unsafe`, obtainable only from `main`.

**Difficulty.** Medium (mechanism) / High (making it usable).
**Impact.** High.

**Novelty.** **Experimental.** Austral and Pony gate authority this way;
applying it to memory-unsafety specifically, with a whole-graph audit
number, is a small delta and mostly an engineering claim.

---

## P3 — Effects are invisible in mainstream type systems

**Problem.** `fn f(x: Int) -> Int` may read a file, mutate a global, block
for a second, or call a payment API. The type says none of it.

**Why it matters.** It defeats local reasoning, makes retry/caching/
sandboxing unsound to apply generically, and lets a dependency update
change what your program does without changing any signature.

**Current solutions.** Haskell's `IO` (one bit); monad transformers and
effect libraries (mtl, polysemy, fused-effects, effectful, cleff);
Koka/Frank/Eff/Links row-typed effects; Unison abilities; OCaml 5 effect
handlers (**untracked** — not in types); Kotlin `suspend`; Swift `async`/
`throws`/typed throws; Rust's `const`/`async`/`unsafe` as ad-hoc effects.

**Current limitations.** Haskell's `IO` is too coarse; transformer stacks
have poor inference and real performance cost. Row-typed effects work but
have not crossed into industry — the standing objections are annotation
burden, error-message quality, and separate compilation. OCaml 5 shipped
handlers *without* type tracking, which is a deliberate and instructive
retreat.

**Existing research.** Leijen, *Koka: Programming with Row-Polymorphic
Effect Types* (2014) and *Extensible Records with Scoped Labels* (2005);
Bauer & Pretnar, *Eff*; Lindley/McBride/McLaughlin, *Frank*; Brachthäuser
et al., *Effekt*; Convent et al., *Doo Bee Doo Bee Doo*.

**Potential NOVA solution.** RFC 0001: effect rows where the label set is
derived from capabilities in scope, so annotation is a checked consequence
rather than a maintained artifact.

**Difficulty.** High. **Impact.** Transformative.

**Novelty.** **Well researched.** Effect rows are twenty years old. The
open question is adoption, not existence.

---

## P4 — Ambient authority

**Problem.** In nearly every mainstream language, any code that can
`import` can open sockets, read `~/.ssh`, and spawn processes. Authority
follows the *process*, not the *code*.

**Why it matters.** This is the structural cause of supply-chain
compromise. A logging library has no business reading the filesystem, and
no mainstream language can express that.

**Current solutions.** Object-capability languages (E, Joe-E, Caja,
Monte, Pony's `AmbientAuth`, Austral); OS/runtime sandboxes (seccomp,
Deno permissions, WASI); CHERI in hardware; OCaml 5's Eio, which passes
an `Eio.Stdenv.t` into `main` instead of exposing global IO.

**Current limitations.** Runtime sandboxes are process-granular and
cannot express "this *function* may not touch the network". Language-level
ocap systems exist but authority becomes invisible once captured in a
closure or a struct field. Deno's model is coarse and asked at the wrong
boundary.

**Existing research.** Dennis & Van Horn (1966); KeyKOS; Miller's
*Robust Composition* (2006); Maffeis, Mitchell & Taly, *Object
Capabilities and Isolation of Untrusted Web Applications* (2010); Mettler
& Wagner's Joe-E; the WASI/Component Model capability discipline.

**Potential NOVA solution.** RFC 0001 §4.1 and §4.7: no ambient
authority, all capabilities descend from `main(rt: Runtime)`. Combined
with P3 so that *capture* of authority is also visible.

**Difficulty.** Medium mechanically; **Very High** ecologically — it
requires the entire standard library and package ecosystem to be written
capability-passing from day one.

**Impact.** Transformative.

**Novelty.** **Established** (the ocap model itself). NOVA's only delta is
its interaction with effect rows; see P5 and the Effekt caveat in
[RESEARCH.md](RESEARCH.md#r3--effect-systems).

---

## P5 — Function coloring and the absence of effect polymorphism

**Problem.** `async`, `throws`, `const`, `unsafe`, `suspend`, `pure` each
partition the world in two, and every combination needs a duplicate of
every higher-order function. `map` needs a sync version, an async version,
a throwing version, a const version.

**Why it matters.** It is the single largest source of API duplication in
Rust, Swift, Kotlin and C++. Rust's ecosystem maintains parallel sync and
async universes of nearly every library.

**Current solutions.** Duplication (Rust: `std` vs `tokio`); macros
(`maybe_async`); Kotlin's `suspend` with inline higher-order functions;
Swift's `rethrows` and `reasync`; C++ `constexpr`-if; Rust's keyword
generics / effect-generics initiative (unshipped).

**Current limitations.** Every mainstream solution is a special case for
one specific colour. None generalises, because none of these languages has
a general notion of "effect" to be polymorphic *over*.

**Existing research.** Row polymorphism (Rémy, Wand, Leijen); Koka's
effect-polymorphic `map`; Frank's ability polymorphism; Effekt's
contextual effect polymorphism; Kiselyov's extensible effects.

**Potential NOVA solution.** One mechanism — the row variable — makes
`with_retry[r](f: () -> T ! r) -> T ! r` cover every colour at once,
including colours added later. This is the strongest *practical*
argument for an effect system, and the one that speaks to working
engineers rather than to type theorists.

**Difficulty.** Medium, given P3. **Impact.** Transformative.

**Novelty.** **Well researched** as theory; **Underexplored** as an
industrial argument. No mainstream language has shipped general effect
polymorphism, and Rust's decade-long struggle is evidence that bolting it
on later is very hard — which supports Constitution Article IV.

---

## P6 — Data races and the cost of concurrency correctness

**Problem.** Shared mutable state across threads is undefined behaviour in
C/C++, a silent bug in Go and Java, and prevented in Rust only via
`Send`/`Sync` plus ownership.

**Why it matters.** Concurrency bugs are the least reproducible and most
expensive class of defect in production systems.

**Current solutions.** Rust's `Send`/`Sync` + borrowing; Pony's reference
capabilities; Swift 6's strict concurrency with `Sendable` and
region-based isolation (SE-0414); actors (Erlang, Akka, Orleans); STM
(Haskell, Clojure); Go's race detector (dynamic, incomplete).

**Current limitations.** Rust's guarantee is strong but is entangled with
lifetimes. Swift's arrived late and forced a painful migration. Erlang's
isolation costs copying. Dynamic detectors find only executed races.

**Existing research.** Boyapati/Rinard ownership types; Deterministic
Parallel Java; Pony's `iso`/`val`/`ref`/`box`/`tag` lattice (Clebsch et
al.); Verona's concurrent ownership; LVars (Kuper & Newton).

**Potential NOVA solution.** Must fall out of Milestone 1's memory
discipline rather than sit beside it. If NOVA chooses regions, data-race
freedom is a property of region ownership, as in Verona.

**Difficulty.** Very High. **Impact.** Transformative.

**Novelty.** **Established/Well researched.** Rust and Pony have solved
this; the open question is doing it with less ceremony.

---

## P7 — Structured concurrency is a convention, not a guarantee

**Problem.** `go f()` and `Thread.start()` create lifetimes that outlive
their lexical scope. Nothing forces a spawned task to be awaited,
cancelled, or supervised.

**Why it matters.** Unstructured spawning produces leaked tasks, lost
errors, and shutdown that never completes — the "goroutine leak" genre of
production incident.

**Current solutions.** Trio's nurseries; Kotlin's `CoroutineScope`;
Swift's `async let` / `TaskGroup`; Java's `StructuredTaskScope`
(JEP 453/480/499); Erlang's supervision trees; `errgroup` in Go.

**Current limitations.** In Kotlin, Swift and Java it is a library
convention that the language does not enforce — you can still escape
scope. Erlang enforces supervision but at process granularity with copying
costs. Go's language design actively fights it.

**Existing research.** Sústrik, *Structured Concurrency* (2016); Smith,
*Notes on structured concurrency, or: Go statement considered harmful*
(2018); Erlang/OTP design principles.

**Potential NOVA solution.** Make task lifetime a *scope-bound
capability*: spawning requires a `Nursery` value, and that value cannot
outlive its scope. This is the same second-class-value discipline Effekt
uses for effect capabilities, applied to concurrency. It needs P1's
memory model to say what "cannot outlive" means.

**Difficulty.** High (blocked on Milestone 1). **Impact.** High.

**Novelty.** **Well researched** as a pattern; **Experimental** as an
enforced language rule. No mainstream language enforces it in the type
system.

---

## P8 — Cancellation and deadlines do not compose

**Problem.** Cancellation is threaded manually (Go's `context.Context`),
implicit and cooperative (Swift/Kotlin), or absent. Timeouts do not
compose: a 100ms budget spread over five sequential calls has no
representation.

**Why it matters.** It is the mechanism by which one slow dependency turns
into a cascading outage, and it is the single most common cause of
retry-storm amplification.

**Current solutions.** `context.Context`; `CancellationToken`;
`Task.isCancelled`; structured concurrency's implicit propagation; service
meshes and RPC deadlines (gRPC deadline propagation).

**Current limitations.** `context.Context` is a manual first parameter
that the compiler does not check you pass on — the same failure mode as
manual capability passing without a type system. Deadlines are wall-clock
values, not budgets: nothing subtracts elapsed time as they propagate.

**Existing research.** Thin. Dean & Barroso's *The Tail at Scale* (2013)
frames the problem; Google's Dapper/Census propagate deadlines
operationally. There is very little *language-level* literature.

**Potential NOVA solution.** A deadline is a resource budget (P9) carried
as a capability, and passing it is checked exactly as authority is.
`Deadline` is a capability whose remaining time is consumed.

**Difficulty.** High. **Impact.** High.

**Novelty.** **Underexplored.** This is a genuinely thin area of the
literature and one of the more promising places for NOVA to contribute.

---

## P9 — Resource consumption is not expressible

**Problem.** No mainstream language lets you write "this function
allocates at most 4KB", "this handler performs at most 3 database
round-trips", or "this loop terminates".

**Why it matters.** It is the difference between a service that degrades
and one that falls over. Today these constraints live in load tests and
alerting thresholds, discovered after deployment.

**Current solutions.** Runtime limiters (cgroups, `ulimit`, semaphores,
circuit breakers); WCET analysis in avionics (Ada/SPARK); manual
budgeting.

**Current limitations.** All of it is runtime and process-granular. A
limit that trips in production is a detection mechanism, not a
correctness property.

**Existing research.** This area is stronger than most people realise:
RAML / Automatic Amortised Resource Analysis (Hofmann & Jost; Hoffmann,
Aehlig, Hofmann); Granule's graded modal types (Orchard, Liepelt & Eades);
Quantitative Type Theory (Atkey); linear and graded type systems;
cost-annotated semantics (CerCo).

**Potential NOVA solution.** Milestone 5. Budgets as *graded* effects: the
row already says *what* a function does; a grading says *how much*. If
this does not reduce to the existing effect machinery, the
"constraint-native" thesis is weaker than claimed and NOVA must say so.

**Difficulty.** Open research for anything precise; Medium for
coarse counting (round-trips, allocations at type granularity).
**Impact.** Transformative if solved even approximately.

**Novelty.** **Well researched** in academia, **Underexplored** in
practice. RAML exists and works; nothing industrial has adopted it.

---

## P10 — Failure semantics are untyped

**Problem.** Whether an operation is safe to retry — idempotent,
at-most-once, at-least-once, compensatable — is documented in prose if at
all. `with_retry(charge_card)` typechecks everywhere.

**Why it matters.** Duplicate side effects at scale mean double charges
and duplicate emails. Retry policy is currently a property of
infrastructure config, applied uniformly to operations with wildly
different semantics.

**Current solutions.** Naming conventions; idempotency keys; sagas and
compensating transactions; exactly-once frameworks (Kafka transactions);
Temporal/Cadence workflow durability.

**Current limitations.** All library-level and unchecked. Temporal gets
the closest by making the durable/nondurable split explicit, but enforces
it with runtime determinism checks rather than types.

**Existing research.** Sagas (Garcia-Molina & Salem 1987); CALM and
Bloom/Dedalus (Hellerstein, Alvaro); Helland's *Life beyond Distributed
Transactions*; session types for protocol conformance.

**Potential NOVA solution.** Retry-safety is a *property of an effect
label*, not of a function. If `Payments` is declared non-idempotent, a
row-polymorphic `with_retry[r]` can refuse to instantiate `r` with it.
This makes RFC 0001's row a place to hang policy, which is the strongest
argument that the row was worth having.

**Difficulty.** Medium given P3. **Impact.** High.

**Novelty.** **Underexplored.** Attaching algebraic properties to effect
labels and constraining polymorphism on them is not, as far as this
review found, done anywhere. Worth an RFC after Milestone 0.

---

## P11 — The network is invisible

**Problem.** A local call and a remote call look identical at the call
site, differing only in latency, partial failure, serialisation cost, and
security domain. The type system distinguishes none of it.

**Why it matters.** The eight fallacies of distributed computing are
fallacies precisely because languages let you pretend a remote call is a
function call. Two decades of RPC frameworks (CORBA, DCOM, gRPC) have
reinforced the pretence rather than fixed it.

**Current solutions.** Erlang/OTP (explicit message passing, no shared
state); Unison's distributed abilities; Orleans virtual actors; Ray;
gRPC/protobuf codegen; tRPC's type-sharing.

**Current limitations.** Codegen approaches preserve types but not
effects, latency, or failure modes. Erlang preserves the model but
requires the whole system to be Erlang.

**Existing research.** Waldo et al., *A Note on Distributed Computing*
(1994) — still the definitive statement; Argus (Liskov); Cloud Haskell;
Unison's distributed runtime; **choreographic programming** (Montesi;
Choral; HasChor; Pirouette) — write one global protocol, compile to
per-endpoint code.

**Potential NOVA solution.** A remote boundary is a capability with a
latency and failure grading. Choreographic projection is the more
ambitious option and maps unusually well onto P12.

**Difficulty.** Very High. **Impact.** Transformative.

**Novelty.** **Experimental.** Choreographies are a live research area
with real implementations and almost no industrial presence.

---

## P12 — Full-stack applications are written twice

**Problem.** The client/server boundary forces duplicate type
definitions, duplicate validation, hand-written serialisation, and a
manual decision about which code runs where.

**Why it matters.** It is the dominant source of accidental complexity in
web development, and the reason a "simple CRUD app" needs a framework.

**Current solutions.** Ur/Web; Links; Eliom/Ocsigen; Meteor; Elm + a
separate backend; tRPC; React Server Components; Phoenix LiveView; Blazor.

**Current limitations.** Ur/Web and Links are the deepest solutions and
remain research languages — a fact worth taking seriously rather than
repeating. RSC and LiveView solve the split for one framework, with
placement decided by convention (`"use server"`) and no static account of
what crosses the wire.

**Existing research.** Chlipala, *Ur/Web: A Simple Model for Programming
the Web* (POPL 2015); Cooper, Lindley, Wadler & Yallop, *Links: Web
Programming Without Tiers* (2006); Eliom's client/server sections;
choreographic programming (again — P11 and P12 are the same problem).

**Potential NOVA solution.** Nothing before Milestone 3. If NOVA gets
there, the honest framing is: *tier placement is an execution-strategy
decision, and the constraint that survives the split is the capability
row.* A client cannot be handed a `Database`.

**Difficulty.** Very High. **Impact.** High.

**Novelty.** **Well researched** and repeatedly under-adopted. Any NOVA
work here must first explain why Ur/Web did not win, or it will lose the
same way.

---

## P13 — Semantic versioning is a promise, not a property

**Problem.** Semver is asserted by a human. Nothing checks that a patch
release is compatible, and nothing detects that a minor release broke you.

**Why it matters.** It is the root of dependency resolution complexity,
lockfile churn, and "works on my machine" upgrades.

**Current solutions.** Cargo's semver + `cargo-semver-checks`; Go's
Minimal Version Selection (Cox) and import-path major versions; Elm's
`elm-publish`, which *computes* the version bump from an API diff and
refuses a wrong one; Unison's content-addressed definitions, which make
the question disappear.

**Current limitations.** Elm's check is syntactic (types only, not
behaviour) but is still the strongest thing shipped. Unison's answer is
the most principled and requires abandoning the file/name model entirely.

**Existing research.** Cox's MVS essays; Unison's content-addressed code;
*Build Systems à la Carte* (Mokhov, Mitchell, Peyton Jones 2018).

**Potential NOVA solution.** At minimum: compute the compatibility class
from the checked interface, Elm-style, and refuse mislabelled releases.
NOVA's addition is that the *effect row and capability requirements are
part of the interface* — a dependency that starts touching the network in
a patch release is a detectable breaking change.

**Difficulty.** Medium. **Impact.** High.

**Novelty.** **Experimental.** Elm proved the mechanism; including effects
and capabilities in the compatibility relation is a small, testable delta.

---

## P14 — A dependency inherits all of your authority

**Problem.** `npm install` grants every transitive package the full
authority of your process at install time and at run time.

**Why it matters.** event-stream, colors/faker, node-ipc, xz. This is now
the primary attack surface of most software.

**Current solutions.** Lockfiles and audit tooling; sigstore/SLSA
provenance; Deno's runtime permissions; WASI/Component Model's
shared-nothing linking; vendoring and review.

**Current limitations.** Provenance proves *who built it*, not *what it
does*. Runtime permission prompts are process-granular and untyped.

**Existing research.** Joe-E and Caja's taming of hostile code; the
Component Model's per-component import lists; capability-safe module
systems.

**Potential NOVA solution.** A package's capability requirements are part
of its published interface (P13), computable, diffable, and enforceable at
*install* time rather than first run. This is the concrete pay-off of P4
and the question SECURITY.md flags as unanswered.

**Difficulty.** Medium given P4. **Impact.** Transformative.

**Novelty.** **Underexplored.** WASI does this at component granularity;
doing it at package granularity inside one language, checked statically,
is not established practice.

---

## P15 — Incremental compilation and language tooling are rebuilt twice

**Problem.** Compilers are batch pipelines; IDEs need demand-driven,
error-tolerant, incremental analysis. Most projects build two front ends
(rustc + rust-analyzer, Swift + SourceKit) that drift.

**Why it matters.** Duplicate front ends means duplicate bugs and
divergent diagnostics, and it is very expensive.

**Current solutions.** Salsa and rustc's query system; Roslyn's
compiler-as-a-service; Adapton; self-adjusting computation; Skip
(abandoned); Unison's content-addressed cache; Bazel/Buck2 at the build
level.

**Current limitations.** Retrofitting a query architecture is a rewrite,
which is exactly why rust-analyzer exists separately.

**Existing research.** Acar's self-adjusting computation; *Build Systems à
la Carte*; Salsa's design notes; Roslyn.

**Potential NOVA solution.** No new idea needed — just the discipline to
be demand-driven and span-preserving from the first commit. Already
recorded as a binding constraint in ARCHITECTURE.md.

**Difficulty.** Medium if done early; Very High if done late.
**Impact.** High.

**Novelty.** **Established.** Purely an engineering-discipline decision.

---

## P16 — Verification lives in a different language from programming

**Problem.** You either write Rust and get no proofs, or write Dafny/F\*/
Lean and rewrite your program in a proof language. Real systems do the
latter only for cryptographic cores.

**Why it matters.** The cost of verification is dominated by the
translation, not the proving. Where the gap is small (SPARK, Dafny at
AWS), verification is used routinely.

**Current solutions.** Dafny (Boogie/Z3); F\* + KaRaMeL extraction to C
(HACL\*, EverCrypt); Ada/SPARK; Liquid Haskell; Verus and Creusot for
Rust; Kani (bounded model checking); Lean 4 as a general-purpose language.

**Current limitations.** SMT automation is brittle at the edges and error
messages are famously bad. Full dependent types (Lean, Idris) impose a
cost on every programmer, including those proving nothing.

**Existing research.** Project Everest; Dafny's industrial use at AWS; the
Verus/Creusot line; Liquid types (Rondon, Kawaguchi, Jhala 2008).

**Potential NOVA solution.** Milestone 6, and only as a *layer*: opt-in
refinements where a program using none pays nothing, including in compile
time. The realistic target is SPARK's level of ambition, not Lean's.

**Difficulty.** High. **Impact.** High.

**Novelty.** **Established/Well researched.** NOVA has no new idea here
and should say so.

---

## P17 — Time, ordering and staleness are unexpressible

**Problem.** "This cache entry may be up to 5s stale", "this must complete
before that", "this read must see that write" are properties every
distributed system depends on, and no mainstream type system holds any of
them.

**Why it matters.** Consistency bugs are silent, data-dependent, and
surface as customer-visible anomalies rather than crashes.

**Current solutions.** TLA+ and Alloy (external specification); P
(Microsoft; used to model S3 and DynamoDB); Jepsen (external testing);
session types for protocol ordering; typestate for object protocols.

**Current limitations.** TLA+ and P verify a *model*, not the code that
ships; drift between model and implementation is unmanaged. Session types
are well developed for two-party protocols and awkward beyond.

**Existing research.** Lamport's TLA+; Honda's session types and
multiparty session types (Honda, Yoshida, Carbone 2008); typestate (Strom
& Yemini 1986; Plaid); CRDTs (Shapiro et al.); the CALM theorem (Hellerstein
& Alvaro).

**Potential NOVA solution.** Nothing designed. The nearest tractable
sub-problem is *staleness as a grading on a value* — a refinement of P9's
graded types rather than a new mechanism.

**Difficulty.** Open research. **Impact.** High.

**Novelty.** **Well researched** in parts (session types, TLA+),
**Speculative** as a unified language feature.

---

## P18 — Uncertainty and approximation are untyped

**Problem.** A GPS reading, a sensor value, a floating-point accumulation,
an ML classifier's output and an exact integer all have the same type.
Comparing two uncertain values with `<` is almost always a bug.

**Why it matters.** It is the source of a whole class of silent errors in
sensing, analytics and ML pipelines — and, increasingly, in anything that
calls a model.

**Current solutions.** Probabilistic programming languages (Stan, Gen,
Pyro, Church, Anglican, Turing.jl); interval arithmetic; units-of-measure
types (F#); manual error bars.

**Current limitations.** PPLs are DSLs for *inference*, not general
languages that happen to track uncertainty. Nothing propagates uncertainty
through ordinary application code.

**Existing research.** Bornholt, Mytkowicz & McKinley, *Uncertain\<T\>: A
First-Order Type for Uncertain Data* (ASPLOS 2014) — directly on point;
EnerJ's approximate types (Sampson et al. 2011); Gen (Cusumano-Towner et
al. 2019); probabilistic effects in Koka.

**Potential NOVA solution.** Not before Milestone 7, and only if it
reduces to an existing mechanism. `Uncertain[T]` as a graded type with
conditional-comparison semantics is the tractable version. The Vision's
"Uncertainty" term is currently a category, not a design — Article VIII.

**Difficulty.** High. **Impact.** Medium, rising.

**Novelty.** **Well researched** (Uncertain\<T\> is a decade old and
under-adopted); **Underexplored** industrially.

---

## P19 — Calls to AI models are untyped, unbounded, nondeterministic effects

**Problem.** An LLM call is a network effect with unbounded latency,
unbounded cost, nondeterministic output, prompt-injection exposure, and no
schema guarantee — and in every language it is `client.chat(...)`,
indistinguishable from a hashmap lookup.

**Why it matters.** This is now a routine part of production systems, and
the *language* offers nothing: no cost budget, no taint tracking from
model output to privileged action, no structural guarantee on the result.

**Current solutions.** Libraries: DSPy, LMQL, Guidance, Outlines, BAML,
TypeChat, Instructor; constrained decoding for schema conformance;
tool-calling protocols; agent frameworks; evaluation harnesses.

**Current limitations.** All of it is library-level. Nothing prevents an
LLM's output from flowing into a shell command — the central agent
security problem — because that requires *information-flow control*
(P20), which no mainstream language has.

**Existing research.** Constrained decoding / grammar-based generation;
DSPy's compiled prompt programs; the extensive prompt-injection
literature; classic IFC (Denning; Myers' JIF; Jeeves; LIO) applied to a
new source.

**Potential NOVA solution.** Deliberately *not* AI-specific syntax. An
LLM call is (a) a capability, (b) an effect label, (c) a cost budget
(P9), and (d) a *taint source* (P20). If NOVA's existing mechanisms cover
it, that is strong evidence the mechanisms are right — and Article VIII
forbids inventing new ones for it.

**Difficulty.** Low as composition of P4/P9/P20; the difficulty is
entirely in P20. **Impact.** High and rising.

**Novelty.** **Underexplored**, and the most over-claimed area in the
industry. The honest statement is that the *components* are well
researched and nobody has assembled them.

---

## P20 — Information flow is not tracked

**Problem.** Authority control answers "may this code act?". It does not
answer "may this *data* reach here?". A capability-safe program can still
log a password.

**Why it matters.** It is the mechanism behind PII leaks, secret exposure
in logs and traces, and — newly — prompt-injection escalation, where
untrusted model output reaches a privileged sink.

**Current solutions.** Taint tracking in static analysers (CodeQL,
Semgrep); JIF/Jif and FlowCaml as research languages; LIO in Haskell;
Jeeves; runtime taint in Perl/Ruby.

**Current limitations.** Static analysers are heuristic, path-insensitive
and outside the language. Full IFC languages impose annotation burden
everywhere and have never been adopted. Declassification — the point where
tainted data legitimately becomes clean — is the hard part and the least
solved.

**Existing research.** Denning & Denning (1977); Myers & Liskov's
decentralised label model; Sabelfeld & Myers' survey (2003); Sabelfeld &
Sands on declassification dimensions (2005); LIO (Stefan et al.).

**Potential NOVA solution.** None designed, and SECURITY.md already states
plainly that NOVA does *not* do this. The observation worth recording is
that IFC and capability-effects are *dual* — one constrains data flow, one
constrains authority flow — and a language with both would be the first.
Whether they share a mechanism is a real research question (see
[DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md)).

**Difficulty.** Open research (adoption, not theory). **Impact.**
Transformative.

**Novelty.** **Well researched** and consistently unadopted — a warning
sign that NOVA should study carefully before attempting.

---

## P21 — Observability is bolted on and drifts

**Problem.** Instrumentation is written by hand, duplicated across
logging/metrics/tracing, and drifts from the code it describes. Adding a
span is a manual edit; forgetting one is invisible.

**Why it matters.** The gap between what a program does and what it
reports is where production debugging time goes.

**Current solutions.** OpenTelemetry; structured logging; eBPF and
auto-instrumentation agents; Erlang's built-in tracing; continuous
profilers; Coz causal profiling.

**Current limitations.** Auto-instrumentation is framework-shaped and
misses domain semantics. Manual instrumentation is a parallel program with
no type relationship to the real one.

**Existing research.** Dapper (Sigelman et al. 2010); Coz (Curtsinger &
Berger 2015); Erlang's tracing BIFs; aspect-oriented programming, whose
failure modes are instructive.

**Potential NOVA solution.** The effect row already *is* a description of
what a function does. Deriving span boundaries from capability uses —
rather than from hand-placed instrumentation — is a small, concrete idea
and a good early test of whether the row carries real information.

**Difficulty.** Low–Medium. **Impact.** Medium–High.

**Novelty.** **Underexplored.** Effects-as-instrumentation is occasionally
mentioned in effect-system papers and has no serious implementation.

---

## P22 — Performance tuning is entangled with algorithm

**Problem.** Changing tiling, vectorisation, layout or parallelisation
means rewriting the algorithm. The *what* and the *how* are the same text.

**Why it matters.** It makes performance work unportable and
unmaintainable; the tuned version and the readable version diverge
permanently.

**Current solutions.** Halide's algorithm/schedule separation; Exo's
exocompilation; TVM; Triton; Sequoia; OpenMP pragmas; profile-guided
optimisation; BOLT; MLGO.

**Current limitations.** Halide's separation is superb and confined to
image/array pipelines. Nothing equivalent exists for general programs, and
it is not obvious that it can.

**Existing research.** Ragan-Kelley et al., *Halide* (PLDI 2013); Ikarashi
et al., *Exocompilation* (Exo, PLDI 2022); Chen et al., *TVM* (OSDI 2018);
autotuning (OpenTuner, ATLAS).

**Potential NOVA solution.** This is what "Execution Strategy" in the
Vision's program model should mean, and it is currently the least-defined
term in it. The honest position: NOVA has no design, and the burden is to
show it generalises past array pipelines — which is exactly what nobody
has done.

**Difficulty.** Open research in general; High in restricted domains.
**Impact.** High.

**Novelty.** **Well researched** in the array/tensor domain;
**Speculative** as a general-purpose language feature.

---

## P23 — Heterogeneous hardware needs a second language

**Problem.** CPU code is one language; GPU/TPU/NPU code is CUDA, SYCL,
Triton, or a framework's graph IR. Crossing the boundary loses types,
effects and safety.

**Why it matters.** Increasing fraction of compute is on accelerators, and
the two-language split is the main source of both bugs and cost.

**Current solutions.** CUDA/HIP/SYCL; Mojo (MLIR-based, one language,
CPU+GPU); Futhark; JAX/XLA; Triton; OpenMP target offload; WebGPU/WGSL.

**Current limitations.** Mojo is the most serious attempt and is young,
partly proprietary, and Python-shaped. Framework graph IRs (XLA) win on
performance and lose on generality.

**Existing research.** MLIR's progressive lowering through dialects
(Lattner et al. 2021) is the enabling infrastructure; Halide/TVM/Exo for
scheduling; Futhark's data-parallel core.

**Potential NOVA solution.** None before Milestone 3, and the decision is
an *IR* decision: MLIR would make this plausible and LLVM alone would not.
Recorded as an open architectural question.

**Difficulty.** Very High. **Impact.** High.

**Novelty.** **Experimental.** Mojo is doing this now; NOVA has nothing to
add today.

---

## P24 — New languages cannot incrementally take over a codebase

**Problem.** Adopting a new language is all-or-nothing per component,
because FFI loses every guarantee the new language provides. This is the
main reason good languages fail.

**Why it matters.** It determines whether any of the above ever reaches
production. It is a *distribution* problem, and language designers
systematically under-weight it.

**Current solutions.** C ABI FFI everywhere; TypeScript's gradual typing
(the most successful language adoption of the last fifteen years, and it
succeeded *because* it was gradual); Kotlin's Java interop; Swift's
Objective-C interop; WebAssembly Component Model's shared-nothing linking
with WIT interfaces.

**Current limitations.** C FFI is a hole in every safety story — including
NOVA's, per SECURITY.md. Gradual typing's soundness/performance costs are
well documented (Takikawa et al., *Is Sound Gradual Typing Dead?*).

**Existing research.** Siek & Taha's gradual typing; Takikawa et al.
(POPL 2016); the Component Model; Vale's "Fearless FFI" (isolate foreign
data rather than trust it).

**Potential NOVA solution.** The Component Model is the most credible
answer available and it aligns exactly with NOVA's capability model —
shared-nothing linking with explicit imports *is* capability passing at
module granularity. Targeting it seriously would make NOVA adoptable
alongside existing code without a trusted-FFI hole.

**Difficulty.** Medium–High. **Impact.** Transformative *for adoption*,
which is the axis on which languages actually die.

**Novelty.** **Established** (the Component Model exists). Choosing to
build on it is a strategy decision, not a research contribution — and it
may be the single highest-leverage decision on this list.

---

## Summary table

| # | Problem | Difficulty | Impact | Maturity | NOVA milestone |
|---|---|---|---|---|---|
| P1 | Memory safety ergonomics | Very High | Transformative | Well researched | M1 |
| P2 | Unbounded escape hatches | Medium | High | Experimental | M1–M2 |
| P3 | Invisible effects | High | Transformative | Well researched | **M0** |
| P4 | Ambient authority | Medium/Very High | Transformative | Established | **M0** |
| P5 | Function coloring | Medium | Transformative | Well researched | **M0** |
| P6 | Data races | Very High | Transformative | Established | M4 |
| P7 | Unstructured concurrency | High | High | Experimental | M4 |
| P8 | Cancellation/deadlines | High | High | **Underexplored** | M5 |
| P9 | Resource budgets | Open research | Transformative | Well researched | M5 |
| P10 | Untyped failure semantics | Medium | High | **Underexplored** | M5 |
| P11 | Invisible network | Very High | Transformative | Experimental | M7 |
| P12 | Full-stack duplication | Very High | High | Well researched | M7 |
| P13 | Unchecked semver | Medium | High | Experimental | M2 |
| P14 | Dependency authority | Medium | Transformative | **Underexplored** | M2 |
| P15 | Tooling duplication | Medium | High | Established | **M0** |
| P16 | Verification gap | High | High | Established | M6 |
| P17 | Temporal properties | Open research | High | Speculative | — |
| P18 | Untyped uncertainty | High | Medium | Well researched | M7 |
| P19 | AI calls as effects | Low* | High | **Underexplored** | M5+ |
| P20 | No information flow control | Open research | Transformative | Well researched | — |
| P21 | Bolted-on observability | Low–Medium | Medium–High | **Underexplored** | M2 |
| P22 | Algorithm/schedule entanglement | Open research | High | Speculative | — |
| P23 | Heterogeneous hardware | Very High | High | Experimental | M3+ |
| P24 | Incremental adoption | Medium–High | Transformative | Established | M3 |

\* P19 is Low *given* P4, P9 and P20; its real difficulty is P20's.

The five entries marked **Underexplored** — P8, P10, P14, P19, P21 — are
where this review found the thinnest literature relative to obvious
importance. Four of the five are downstream of the effect row NOVA is
already committed to, which is the central finding of Phase 0 and is
developed in [DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md).
