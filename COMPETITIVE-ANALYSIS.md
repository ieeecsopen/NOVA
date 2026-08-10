# NOVA — Competitive Analysis

Phase 0 research. What each language and system actually solved, what NOVA
should take, and what NOVA must not repeat.

Assessments describe the state of each system as of **mid-2026**. Where a
feature is in progress or unshipped, the table says so rather than
crediting it.

---

## 1. Master matrix

Legend: ● full / ◐ partial / ○ none / — not applicable.

| Language | Memory management | Safe by default | Effect tracking | No ambient authority | Data-race freedom | Verification | Primary target |
|---|---|---|---|---|---|---|---|
| **Rust** | ownership + borrows | ● (outside `unsafe`) | ○ ad-hoc colours | ○ | ● (`Send`/`Sync`) | ◐ external (Verus, Creusot, Kani) | native, wasm |
| **Go** | tracing GC | ◐ (races are UB-adjacent) | ○ | ○ | ○ | ○ | native |
| **Zig** | manual, explicit allocator | ○ (checked in safe modes) | ○ | ◐ *allocators only* | ○ | ○ | native, wasm |
| **C++** | manual + RAII | ○ | ○ | ○ | ○ | ◐ external | native |
| **Swift** | ARC (+ `~Copyable`) | ● | ◐ `async`/`throws`/typed throws | ○ | ● (Swift 6 strict) | ○ | native, wasm |
| **Kotlin** | JVM GC | ● | ◐ `suspend` | ○ | ○ | ○ | JVM, native, JS |
| **TypeScript** | JS GC | ○ (unsound by design) | ○ | ○ | — (single-threaded) | ○ | JS |
| **Python** | RC + cycle GC | ● (dynamic) | ○ | ○ | ○ | ○ | interpreter |
| **Haskell** | tracing GC | ● | ◐ `IO` = one bit; libraries add rows | ○ | ◐ STM | ◐ Liquid Haskell | native |
| **OCaml** | tracing GC | ● | ◐ handlers, **untracked in types** | ◐ *Eio convention* | ◐ domains | ◐ external | native, wasm |
| **Koka** | Perceus compile-time RC | ● | ● row-typed + handlers | ○ | — | ○ | C, wasm, JS |
| **Unison** | GC | ● | ● abilities + handlers | ○ | ◐ | ○ | own runtime |
| **Mojo** | ownership + ARC | ◐ (maturing) | ○ | ○ | ◐ | ○ | MLIR → CPU/GPU |
| **Vale** | generational refs + regions | ● (claimed) | ○ | ○ | ◐ | ○ | native (research) |
| **Pony** | per-actor ORCA GC | ● | ○ | ● `AmbientAuth` | ● (ref caps) | ○ | native |
| **Erlang / Elixir** | per-process GC | ● (dynamic) | ○ | ○ | ● (isolation) | ○ | BEAM |
| **Lean 4** | RC (Perceus-like) | ● | ◐ monadic | ○ | ○ | ● dependent types | C |
| **Dafny** | host GC | ● | ○ | ○ | ○ | ● SMT (Boogie/Z3) | C#, Java, Go, JS, Rust |
| **F\*** | host GC / Low\* manual | ● | ● **user-definable effects** | ○ | ○ | ● dependent + SMT | OCaml, C (KaRaMeL) |
| **NOVA (target)** | *undesigned* (M1) | ● | ● rows derived from capabilities | ● | *undesigned* (M4) | ◐ layered (M6) | native, wasm (M3) |

Two rows in that table deserve emphasis because they are the ones people
misremember:

- **OCaml 5 shipped effect handlers with no type-level tracking.** The
  designers had the option and declined it, citing inference and
  backward-compatibility cost. That is the strongest available evidence
  for Constitution Article IV: OCaml could not add effect *types* later
  because every existing signature would be wrong.
- **F\* has a user-definable effect system** (Dijkstra monads) and is
  therefore more expressive here than Koka. It pays for it with dependent
  types and SMT, which is the trade NOVA is declining.

---

## 2. Effect systems in detail

| System | Representation | Handlers | Inferred or annotated | Polymorphism | Ships in production |
|---|---|---|---|---|---|
| Haskell `IO` | one type constructor | ○ | inferred | via type classes | ● widely |
| mtl / effectful / polysemy | monad transformer stack | ● | annotated constraints | ● | ◐ some |
| **Koka** | row of labels | ● | inferred + optional annotation | ● row variables | research/production-adjacent |
| **Frank** | ability set, bidirectional | ● | inferred | ● | research |
| **Eff** | effect instances | ● | inferred | ● | research |
| **Links** | rows | ● | inferred | ● | research |
| **Effekt** | **capabilities, second-class** | ● | *contextual*, largely implicit | ● lightweight | research |
| **Unison** | abilities | ● | inferred | ● | ● (Unison Cloud) |
| **OCaml 5** | none (runtime only) | ● | — | — | ● |
| **F\*** | user-defined effect lattice | ● | annotated | ● | ● (HACL\*) |
| Swift | `async`, `throws`, typed throws | ○ | annotated | ◐ `rethrows`/`reasync` | ● |
| Kotlin | `suspend` | ◐ | annotated | ◐ inline functions | ● |
| Rust | `async`, `const`, `unsafe` | ○ | annotated | ○ (effect generics unshipped) | ● |
| **NOVA** | row of **capability type names** | ○ (deferred) | **derived**, checked for equality | ● row variables | ○ |

### The finding that matters for RFC 0001

**Effekt** (Brachthäuser, Schuster & Ostermann, *Effects as Capabilities*,
OOPSLA 2020) already frames effects as capabilities. Its design:
capabilities are **second-class** — they cannot be captured or returned —
which yields effect polymorphism without row variables.

NOVA's RFC 0001 makes capabilities **first-class** and reflects capture in
the type instead of forbidding it. That is a real difference, but the
framing "an effect is a capability" is **not novel**, and RFC 0001 §3
must be corrected to say so. See
[RESEARCH.md §R3](RESEARCH.md#r3--effect-systems) for the full comparison
and the revised claim.

This is the intended function of Phase 0, and of Constitution Article V.

---

## 3. Memory management in detail

| Approach | Systems | Pause-free | No annotations | Cycles handled | Ergonomic cost |
|---|---|---|---|---|---|
| Tracing GC | Go, Java, Kotlin, Haskell, OCaml | ○ | ● | ● | none |
| Per-entity GC | Erlang, Pony (ORCA) | ● | ● | ● | actor model required |
| ARC | Swift, Python | ◐ | ● | ○ (leaks) | low, plus cycle discipline |
| Compile-time RC (Perceus) | Koka, Lean 4 | ● | ● | ○ | low; assumes functional core |
| Ownership + borrowing | Rust | ● | ○ lifetimes | ● | **high** |
| Ownership, no borrow checker | Mojo, C++ moves | ● | ◐ | ◐ | medium |
| Generational references | Vale | ● | ● | ● | low (claimed); unproven |
| Regions / concurrent ownership | Verona, Vale regions | ● | ◐ | ● | medium; research |
| Reference capabilities | Pony | ● | ○ (6 annotations) | ● | high |
| Manual + explicit allocator | Zig | ● | ● | — | high, but *legible* |
| Linear capabilities | Austral | ● | ○ | — | high |

**Reading for NOVA.** The interesting frontier is not "GC vs borrow
checker". It is *regions*: Verona and Vale both make the unit of ownership
a region rather than a value, which reduces annotation burden and composes
with concurrency. Regions also compose with NOVA's existing model in an
obvious way — **a region is a thing you can be handed**, exactly like a
capability. That is the leading Milestone 1 candidate, recorded in
[PROBLEM-SPACE.md P1](PROBLEM-SPACE.md#p1--memory-safety-still-costs-too-much-programmer-effort).

**Zig deserves specific credit.** Passing an allocator explicitly to every
function that allocates is capability discipline for memory, arrived at
from an ergonomics argument rather than a security one. It is
under-cited in the capability literature and is direct evidence that
explicit resource passing is tolerable to working programmers.

---

## 4. Concurrency in detail

| System | Model | Structured | Cancellation | Race freedom | Distribution |
|---|---|---|---|---|---|
| Go | goroutines + channels | ○ | manual `context.Context` | ○ | ○ |
| Rust | async tasks, `Send`/`Sync` | ◐ library (`JoinSet`) | ◐ drop-based | ● | ○ |
| Swift | actors + tasks | ● language-level | ● cooperative | ● (Swift 6) | ○ |
| Kotlin | coroutines + scopes | ● library-enforced | ● cooperative | ○ | ○ |
| Java | virtual threads + `StructuredTaskScope` | ◐ (API, unenforced) | ◐ interrupt | ○ | ○ |
| Python | asyncio; Trio | ○ / ● (Trio nurseries) | ◐ | ○ (GIL; PEP 703 changes this) | ○ |
| Erlang / Elixir | processes + supervision | ● supervision trees | ● links/monitors | ● isolation | ● **built in** |
| Pony | actors + ref caps | ◐ | ○ | ● **statically** | ○ |
| Haskell | green threads + STM | ◐ (`async` library) | ● async exceptions | ◐ STM | ○ |
| Unison | abilities + distributed runtime | ◐ | ◐ | ◐ | ● |
| **NOVA** | *undesigned* (M4) | — | — | must follow from M1 | — |

**Reading for NOVA.** Erlang remains the only system that solved
distribution and failure together, and it did so by giving up shared
memory and static types. Swift 6 is the best evidence of the retrofit
cost: adding data-race safety to a mature language took years and forced
an ecosystem-wide migration. Both support Article IV.

---

## 5. Capability security in detail

| System | Granularity | Static or runtime | Effects visible | Ambient authority |
|---|---|---|---|---|
| E, Joe-E, Caja | object | static (by construction) | ○ | eliminated |
| Pony | object, via `AmbientAuth` | static | ○ | eliminated |
| Austral | linear capability values | static | ◐ via linearity | eliminated |
| Effekt | second-class capabilities | static | ● (that *is* the effect) | eliminated |
| OCaml Eio | `Stdenv.t` passed to main | convention only | ○ | **not** eliminated (`Stdlib` remains) |
| Zig | allocators only | convention | ○ | not eliminated |
| Deno | process permissions | runtime prompts | ○ | reduced, coarse |
| WASI / Component Model | module imports | static link-time | ○ | eliminated at the boundary |
| CHERI | hardware pointers | runtime, hardware | ○ | reduced |
| Java `SecurityManager` | stack inspection | runtime | ○ | attempted, **withdrawn** (JEP 411) |
| **NOVA** | capability values + rows | static | ● | eliminated |

Two lessons:

1. **`SecurityManager` failed** because it tried to add authority control
   to a language with ambient authority, at runtime, via stack inspection.
   Oracle removed it. This is the clearest available proof of Article IV's
   claim about authority.
2. **The Component Model is the only capability system with industrial
   momentum**, and its shared-nothing linking with explicit WIT imports is
   the same idea as NOVA's capability passing, one level up. This is a
   strategic alignment worth taking seriously — see
   [P24](PROBLEM-SPACE.md#p24--new-languages-cannot-incrementally-take-over-a-codebase).

---

## 6. Compilation, IR and tooling

| System | IR | Incremental | Single front end for IDE | Compile speed | Targets |
|---|---|---|---|---|---|
| LLVM | SSA, low-level | ○ | — | slow | very many |
| **MLIR** | multi-dialect, regions | ○ | — | varies | very many, incl. accelerators |
| Cranelift | SSA, fast | ○ | — | **fast** | native, wasm |
| rustc | HIR/MIR + LLVM | ● queries | ○ (rust-analyzer is separate) | slow | native, wasm |
| Roslyn | — | ● | ● **compiler as a service** | fast | .NET |
| Go | own SSA | ◐ package-level | ○ (gopls separate) | **very fast** | native |
| Zig | own IR + LLVM/self-hosted | ◐ | ○ | fast | native, wasm |
| Swift | SIL + LLVM | ◐ | ◐ SourceKit shares some | slow | native |
| Unison | content-addressed AST | ● **by construction** | ● | fast | own runtime |

**Reading for NOVA.** Roslyn and Unison are the two systems that avoided
building the front end twice, and both did it by choosing the architecture
before the first release. rustc/rust-analyzer is the cautionary case.
ARCHITECTURE.md already records "queries, not phases" as binding.

**On the IR choice** (still open): MLIR is the only option that keeps
[P23](PROBLEM-SPACE.md#p23--heterogeneous-hardware-needs-a-second-language)
reachable, at the cost of a much larger dependency and a C++ toolchain.
Cranelift is the best fit for fast debug builds and wasm. LLVM is the
safe default and forecloses accelerators in practice. This decision
should be made deliberately in Milestone 3, not by drift.

---

## 7. Package management and distribution

| System | Version selection | Compatibility checked | Capability manifest | Reproducible |
|---|---|---|---|---|
| npm | SAT solving, nested | ○ | ○ | ◐ lockfile |
| Cargo | SAT solving | ◐ `cargo-semver-checks` (opt-in) | ○ | ◐ lockfile |
| Go modules | **MVS** | ○ | ○ | ● (+ checksum DB) |
| **Elm** | semver | ● **computed from API diff, enforced** | ○ | ● |
| Nix | content-addressed derivations | — | ○ | ● **fully** |
| **Unison** | content-addressed definitions | ● **problem dissolved** | ○ | ● |
| WASI Component Model | link-time | ◐ WIT interface types | ● **explicit imports** | ● |
| **NOVA (target)** | undecided | should be computed (Elm) | should include the row (P14) | required |

The combination nobody has shipped: **Elm's computed compatibility +
the Component Model's explicit imports**, i.e. a published interface that
includes the capability requirements, so that a dependency which starts
touching the network is a *detectable* breaking change. That is
[P13](PROBLEM-SPACE.md#p13--semantic-versioning-is-a-promise-not-a-property)
+ [P14](PROBLEM-SPACE.md#p14--a-dependency-inherits-all-of-your-authority),
and it is one of the cheapest high-value ideas in this review.

---

## 8. What NOVA takes from each

| System | Take | Do not repeat |
|---|---|---|
| **Rust** | ownership rigour; MIR; diagnostics quality as a cultural norm | lifetime syntax burden; sync/async ecosystem split; retrofitted effect generics |
| **Go** | compile speed as a feature; small language surface | unstructured `go`; no effect or error typing; `context.Context` by convention |
| **Zig** | explicit allocator passing; no hidden control flow; `comptime` over macros | no safety guarantee; no ecosystem-level authority story |
| **C++** | RAII; zero-overhead principle | everything else |
| **Swift** | value semantics; structured concurrency in the language; progressive disclosure | late retrofit of data-race safety; ABI-stability constraints on evolution |
| **Kotlin** | `suspend` proving colouring is tolerable when polymorphism exists | colour without general effect polymorphism |
| **TypeScript** | gradual adoption is *the* distribution strategy | deliberate unsoundness |
| **Python** | readability; batteries; the packaging lesson (do it early) | dynamic typing; ambient IO |
| **Haskell** | purity as a default; STM | monad transformer ergonomics; `IO` as one bit |
| **OCaml** | module system; Eio's `Stdenv` passing; fast compiles | **shipping handlers without effect types** — the exact mistake Article IV forbids |
| **Koka** | row-typed effects; Perceus; scoped labels | small ecosystem; syntax churn |
| **Unison** | content-addressed code; abilities; dissolving dependency hell | abandoning files and text tooling wholesale |
| **Mojo** | MLIR as the route to accelerators; Python-adjacency for adoption | proprietary phases; superset-of-a-dynamic-language constraints |
| **Vale** | generational references; region borrowing; "Fearless FFI" | unproven at scale — treat as hypothesis |
| **Pony** | `AmbientAuth`; reference capabilities; race freedom by types | six-way ref-cap annotation burden; niche ecosystem |
| **Erlang / Elixir** | supervision; isolation; distribution and failure designed together | no static types; copying costs |
| **Lean 4** | proofs and programs in one language; Perceus-style RC | dependent types as the default cost |
| **Dafny** | verification with usable automation; industrial adoption at AWS | separate language from the shipping one |
| **F\*** | user-definable effect lattice; extraction to C | dependent types + SMT for everyone |
| **LLVM** | mature backends | slow compiles; poor accelerator story |
| **MLIR** | progressive lowering; dialects; the accelerator path | C++ dependency weight |
| **WebAssembly** | portable, sandboxed target; deterministic core | limited GC/host interop maturity |
| **WASI + Component Model** | capability-based imports; shared-nothing linking; **the adoption path** | churn across preview versions |

---

## 9. Where NOVA would actually be differentiated

Being honest about the size of the gap:

| Claim | Status |
|---|---|
| Effect rows | **Not differentiated.** Koka, Frank, Links, Unison. |
| Capabilities as authority | **Not differentiated.** E, Pony, Austral, WASI. |
| Effects *as* capabilities | **Not differentiated.** Effekt got there in 2020. |
| First-class capabilities with capture reflected in the row | **Narrow, plausible delta.** Effekt forbids capture; NOVA types it. Falsifiable. |
| Row **equality** rather than subsumption | **Narrow, untested.** No system does this; it may simply be too strict. `widen`-rate is the experiment. |
| Effect row as the carrier for budgets, retry policy, tracing and package manifests | **The actual thesis.** Unexplored as a unified claim. |
| Memory model | **Behind.** Rust is better; NOVA has nothing. |
| Everything in Milestones 5–7 | **Not started.** |

The fourth and sixth rows are where Phase 0 says NOVA's contribution
might be. The sixth is developed in
[DESIGN-OPPORTUNITIES.md](DESIGN-OPPORTUNITIES.md).
