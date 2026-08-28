# NOVA

A constraint-native programming language.

**Status: pre-alpha research.** There is a specification, an executable
reference semantics, a conformance suite, and a designed (prototyped,
not yet integrated) memory model. There is no compiler, no code
generator, and no second implementation of anything. Do not use this
for anything.

---

## The idea

Programs carry obligations their languages cannot express: *this must not
touch the network*, *this dependency must not read the filesystem*, *this
must not see unredacted PII*. Today those live in review comments, linter
configs, and service meshes — checked late, by tools that do not
understand the program.

NOVA's bet is that two of these are type-level information, and that they
cannot be retrofitted, so a language has to start with them:

- **Effects** — what a function *does* is part of its type.
- **Authority** — the power to act on the outside world is a *value* you
  must be handed, not an ambient power any import confers.

RFC 0001 unifies them: **an effect label is a capability type**, and a
function's effect row is *derived* from the capabilities its body can
reach, including through closure captures.

```nova
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("hello from NOVA");
    0
}
```

There is no `import std.io` and no free `print`. The authority to write to
the console arrived as `rt`, and `! {Runtime}` is the compiler stating
that it was used.

## The diagnostic that justifies the project

Capability-safe languages control who can *obtain* authority, but lose
track of it once it is captured in a closure. Effect-typed languages track
what happened, but let any code perform any effect. NOVA rejects this:

```nova
fn sneaky(c: Clock) -> (() -> Int) {
    || c.now()
}
```

```
error[E0203]: closure captures capability `Clock` but its expected type does not declare it
 --> sneaky.nova:2:5
  |
2 |     || c.now()
  |     ^^^^^^^^^^ this closure has type `() -> Int ! {Clock}`
  = note: captures `c: Clock`
  = note: expected `() -> Int`
  = note: passing it here would hide the effect `Clock` from callers
```

## Try it

Needs Python 3.11+ and nothing else.

```sh
python3 -m verifier.refspec run   examples/hello.nova
python3 -m verifier.refspec check examples/authority.nova
python3 -m verifier.refspec audit examples/retry.nova
python3 tests/run_conformance.py --verbose
```

`audit` prints every function's effect row and every deliberately widened
signature — the thing a reviewer actually wants to read.

## What exists

| | |
|---|---|
| Specification | RFC 0000 (process), RFC 0001 (core, engineering RFC after Phase 0's correction), RFC 0002–0005 (structs/enums, generics/traits, modules, mutability) |
| Reference semantics | lexer, parser, capability reachability, type + effect checker, evaluator — Python, `verifier/refspec/` |
| Standard library | `std/option.nova`, `std/result.nova`, `std/list.nova` — ordinary NOVA, no compiler magic |
| Conformance suite | 45 tests, including adversarial attempts to defeat the effect rule and the mutability/trait soundness rules |
| Examples | 24 files under `examples/` — 22 complete, runnable programs |
| Memory model | designed and prototyped (region-based ownership) — `MEMORY-MODEL.md`, `OWNERSHIP-MODEL.md`, `regionlab/` — not yet integrated into `verifier/refspec/` |
| Compiler | **not started** — needs a Rust toolchain |
| Everything else | not started; see [ROADMAP.md](ROADMAP.md) |

Known gaps are enumerated in [docs/known-issues.md](docs/known-issues.md),
including the two open specification questions that gate Milestone 0.

## Phase 0 research

The design is preceded by a written research phase, so that NOVA does not
re-derive known results or claim them:

| Document | Contents |
|---|---|
| [PROBLEM-SPACE.md](research/PROBLEM-SPACE.md) | 24 problems in modern languages, with prior art, difficulty and impact |
| [COMPETITIVE-ANALYSIS.md](research/COMPETITIVE-ANALYSIS.md) | 20 languages and 5 systems compared across 7 dimensions |
| [RESEARCH.md](research/RESEARCH.md) | 21 research areas, every finding graded Established → Speculative |
| [DESIGN-OPPORTUNITIES.md](research/DESIGN-OPPORTUNITIES.md) | Which separate problems share one mechanism; 5 ranked theses |
| [NON-GOALS.md](docs/foundation/NON-GOALS.md) | What NOVA will not attempt, and why |

The review's first result was to **withdraw RFC 0001's novelty claim**:
Effekt (Brachthäuser et al., OOPSLA 2020) already frames effects as
capabilities. The RFC is now an engineering RFC arguing for a particular
set of trade-offs within a known design. That is Constitution Article V
doing its job.

Its second result was a thesis: **T1 (one graded row carries every
non-functional obligation) + T2 (capability-safe, adoptable-one-module-at-
a-time components)**, adopted in [VISION.md](VISION.md#the-thesis-adopted-2026-08-28-after-phase-0)
after ranking five candidates in
[DESIGN-OPPORTUNITIES.md §8](research/DESIGN-OPPORTUNITIES.md#8-five-candidate-theses-ranked).

Three falsification experiments have since run — cheap tests designed to
break the thesis before Milestones 2–5 are built on top of it:

| Experiment | Question | Result |
|---|---|---|
| [001 — capability manifests](docs/experiments/001-capability-manifests.md) | Can a dependency's authority creep be a detectable, checkable event? | **Works.** Zero new mechanism; a supply-chain-shaped demo (`tests/manifest/logging-lib/`) is caught, with no false positives on two controls. |
| [002 — rows → spans](docs/experiments/002-rows-to-spans.md) | Does deriving trace spans from types avoid the drift bug of hand-written instrumentation? | **Works, narrower than hoped.** Structurally drift-free for the *shape* of execution; semantic labeling (span names, redaction) is a separate, undesigned layer. |
| [003 — graded rows](docs/experiments/003-graded-rows.md) | Do budgets/cost fit the same row as effects? | **Partially confirmed, roadmap corrected.** Composes for first-order code; a syntactic pass cannot see through row-polymorphic calls like `with_retry`. Grading must live inside type unification, not beside it — RFC 0001 §11.7 and ROADMAP Milestone 5 updated accordingly. |

## Phase 1 — the constitution

Phase 1 turned Phase 0's research into binding philosophy, without
designing syntax:

| Document | Contents |
|---|---|
| [LANGUAGE-PHILOSOPHY.md](docs/foundation/LANGUAGE-PHILOSOPHY.md) | Precise definitions of value, computation, program, service, agent, resource, capability, effect, constraint, guarantee, uncertainty, execution strategy |
| [PROGRAM-MODEL.md](docs/foundation/PROGRAM-MODEL.md) | The original `Program = Intent + State + ... ` model, challenged and revised |
| [LANGUAGE-CONSTITUTION.md](docs/foundation/LANGUAGE-CONSTITUTION.md) | 12 binding semantic principles, each with a checkable status |
| [DESIGN-PRINCIPLES.md](docs/foundation/DESIGN-PRINCIPLES.md) | The six-tier feature hierarchy (Core / Optional / Stdlib / Tooling / Runtime / Research extension) |
| [ARCHITECTURAL-GOALS.md](docs/foundation/ARCHITECTURAL-GOALS.md) | Six invariants any implementation of NOVA must satisfy |

The headline result: the original program model listed ten terms as
independent peers. Phase 1 found four of them
(`Capabilities`/`Effects`/`Resources`, plus part of `Constraints`) are one
mechanism at increasing precision, `Verification` is an axis on
`Constraints` rather than a peer, and `Uncertainty` is a property of
values, not of programs. [CONSTITUTION.md Article II](CONSTITUTION.md#article-ii--the-program-model)
now carries both the original and revised model, with the amendment
recorded in [docs/constitution-changelog.md](docs/constitution-changelog.md) —
**RFC 0001 and the conformance suite required no changes.**

## Phase 2 — the core language

NOVA now has structs, tuples, enums, pattern matching (with checked
exhaustiveness), generics, traits, modules, local mutability, and loops
— the minimal general-purpose core Phase 2 set out to design. Every
piece is real: the reference implementation was extended end to end, and
every example below is checked *and run*, not just described.

```nova
import std.list;

struct Handler { rt: Runtime, c: Clock }         // bundles capabilities —
                                                  // constructing it is pure

fn handle(h: Handler, msg: String) -> Int ! {Clock, Runtime} {
    h.rt.print(msg);      // performs Runtime, through a field
    h.c.now()             // performs Clock, through a field
}
```

| Document | Contents |
|---|---|
| [SYNTAX.md](docs/language/SYNTAX.md) | Syntax principles, grammar, every named ambiguity and its resolution |
| [TYPE-SYSTEM.md](docs/language/TYPE-SYSTEM.md) | Nominal vs. structural, inference, variance, generics, coercion |
| [LANGUAGE-REFERENCE.md](docs/language/LANGUAGE-REFERENCE.md) | A complete walkthrough, every example real and runnable |
| [RFC 0002](RFC/0002-structs-tuples-enums-pattern-matching.md)–[0005](RFC/0005-local-mutability-and-loops.md) | Structs/enums, generics/traits, modules, mutability — each with the design argument in full |

Three real bugs were caught and fixed while building this, not after:
a type-unification ordering bug (RFC 0003 §3.1), a trait/impl signature
mismatch that would have been silently unsound (RFC 0003 §5.1, `E0127`),
and an aliasing hazard between mutable locals and closures, closed
before the runtime representation that would have made it exploitable
existed (RFC 0005 §3.1, `E0130`). RFC 0001's own open question — what
happens when a capability is stored in a struct field? — is answered:
nothing new is needed (RFC 0002 §3).

## Phase 3 — memory, resolved

The largest flagged risk in the project — would a memory model force
RFC 0001's capabilities to become second-class? — is closed. It would
not: capabilities stay uniformly first-class, and linearity is applied
to exactly one axis (exclusive region access), not to the capability
system as a whole. Regions were chosen over garbage collection,
reference counting, ARC, and Rust-style per-value lifetimes — compared
explicitly against Rust, with Rust's own real costs (self-referential
structs, `Rc<RefCell<T>>` retreats, `Send`/`Sync` as a bolted-on second
mechanism) stated before anything was proposed, per this phase's own
instruction not to assume Rust is optimal.

| Document | Contents |
|---|---|
| [MEMORY-MODEL.md](docs/language/MEMORY-MODEL.md) | The comparison (GC/RC/ARC/ownership/affine/linear/regions/hybrids), scored against NOVA's actual priorities, and the decision |
| [OWNERSHIP-MODEL.md](docs/language/OWNERSHIP-MODEL.md) | The mechanism: regions as capabilities, linear exclusive access, no named lifetime syntax anywhere |
| [SAFETY-GUARANTEES.md](research/SAFETY-GUARANTEES.md) | Every safety claim at an explicit, honest strength, mapped to a test that would falsify it |
| [`regionlab/`](regionlab/) | A small standalone prototype checker — 14 tests, one negative test per required property (use-after-free, double-free, invalid access, dangling references, data races) |

No named lifetime parameter exists anywhere in this design — the direct
answer to the brief's instruction not to add Rust's lifetime syntax
merely because Rust has it. `regionlab` is deliberately not merged into
`verifier/refspec/`: Phase 2's 45 conformance tests and 24 examples are
untouched by this phase.

## Read next

- [CONSTITUTION.md](CONSTITUTION.md) — the design rules. Article III
  (priority order) and Article VI (the feature bar) settle most arguments.
- [VISION.md](VISION.md) — the long-term thesis, and what NOVA is not.
- [RFC/0001-core-capability-effects.md](RFC/0001-core-capability-effects.md)
  — the language, its prior art, and its open questions.
- [ARCHITECTURE.md](docs/runtime/ARCHITECTURE.md) — the pipeline and why capability
  reachability is its own pass.
- [CONTRIBUTING.md](CONTRIBUTING.md) — the most useful thing right now is
  a counterexample to RFC 0001.

## On novelty

NOVA's row machinery is Koka's. Its capability discipline is E's and
Austral's. Its ownership story does not exist yet and Rust's is better.
Constitution Article V forbids claiming otherwise. The one narrow claim
NOVA makes is stated in RFC 0001 §3, phrased so that it can be falsified —
and if a reviewer finds prior art for it, the claim gets struck.
