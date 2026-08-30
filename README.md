# NOVA

<div align="center">

[![CI](https://github.com/ieeecsopen/NOVA/actions/workflows/ci.yml/badge.svg)](https://github.com/ieeecsopen/NOVA/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-0.2_research_preview-f59e0b.svg)](ROADMAP.md)
[![Conformance](https://img.shields.io/badge/Conformance-47%2F47-0e8a16.svg)](tests/conformance/)
[![RegionLab](https://img.shields.io/badge/RegionLab-14%2F14-0e8a16.svg)](regionlab/)

**A constraint-native programming language — research preview**

*Purity by default. Authority as an unforgeable token. Effects in the type.*

[**Quickstart**](#quickstart) • [**The idea**](#the-idea) • [**What actually works**](#what-actually-works-today) • [**Roadmap**](#roadmap) • [**Contributing**](#contributing)

</div>

---

## Status

NOVA is an **early research preview (0.2)**. What exists and is tested is a
**frontend and a reference interpreter**: a lexer, parser, Hindley–Milner
type inference, row-typed effect checking, capability-reachability
analysis, and a tree-walking evaluator that runs checked programs. There
is also a native C backend for a first-order subset of the language, and
`regionlab`, a separate prototype for the region-based memory model.

Everything else the design documents describe — the distributed runtime,
the reactive WASM frontend, autonomous-agent governance, a package
registry, self-hosting — is **design, not implementation**. See
[ROADMAP.md](ROADMAP.md) for what is gated on what, and
[docs/known-issues.md](docs/known-issues.md) for every gap we know about,
recorded honestly per [Constitution](CONSTITUTION.md) Article XII.

The version is `0.2` deliberately: Article XII forbids claiming 1.0
before the core is frozen, the specification is complete, and two
independent implementations agree. Currently there is one implementation.

---

## The idea

Programs carry real-world obligations that mainstream languages cannot
express in a signature:

* *This dependency must not touch the network.*
* *This closure must not smuggle out filesystem authority it captured.*
* *This function's side effects must be visible to its caller.*

Today those obligations live in code-review comments, linter configs and
runtime sandboxes — checked late, by tools that do not understand
whole-program semantics. NOVA puts them in the type system:

1. **Pure by default.** What a function *does* is part of its signature:
   `fn f(rt: Runtime) -> Int ! {Runtime}`.
2. **Object capabilities.** Authority over the outside world is an
   unforgeable lexical token you must be *handed*. No `import` confers it.
3. **No authority laundering.** A closure that captures a capability
   carries it in its type; it cannot be passed somewhere that expects a
   pure function.

```nova
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("hello from NOVA");
    0
}
```

### The diagnostic that motivates it

Capability-safe languages control who can *obtain* authority but lose
track of it once it is captured in a closure. Effect-typed languages
track what happened but allow ambient effects. NOVA rejects authority
laundering statically:

```nova
fn sneaky(c: Clock) -> (() -> Int) {
    || c.now()
}
```

```text
error[E0203]: closure captures capability `Clock` but its expected type
              does not declare it
 --> sneaky.nova:2:5
  |
2 |     || c.now()
  |     ^^^^^^^^^^ this closure has type `() -> Int ! {Clock}`
  = note: captures `c: Clock`
  = note: expected `() -> Int`
  = note: passing it here would hide the effect `Clock` from callers
```

This is real; it is `tests/conformance/004-closure-cannot-launder-authority.nova`.

---

## Quickstart

Requires **Python 3.10+** and, for `nova build`, **clang**.

```bash
git clone https://github.com/ieeecsopen/NOVA.git
cd NOVA

# Run the full verification suite (what CI runs)
./tools/check-all.sh

# Type- and effect-check a program
./nova check examples/hello.nova

# Run it (reference interpreter — the authoritative engine)
./nova run examples/hello.nova

# Build an executable artifact
./nova build examples/hello.nova && ./hello
```

`nova build` produces a **native binary** when the program stays inside
the subset the C backend supports (top-level functions, `Int` / `Bool` /
`String` / `struct`, `Runtime` / `Clock`), and otherwise an
**interpreter-backed runner** — a real runnable artifact that executes
through the reference interpreter. It tells you which, and it never emits
a binary it cannot compile.

```bash
# Scaffold a project
./nova new my_service && cd my_service && ../nova check

# Inspect intermediate representations (informational)
./nova check examples/hello.nova --emit-hir --emit-mir
```

---

## What actually works today

| Area | State |
| :--- | :--- |
| Lexer, parser, spans, diagnostics | **Working**, `verifier/refspec/` |
| Hindley–Milner type inference | **Working** |
| Row-typed effect checking (equality, not subsumption) | **Working** |
| Capability model + laundering prevention (closures **and** struct fields) | **Working** |
| Structs, enums, tuples, pattern matching, exhaustiveness | **Working** |
| Generics, traits, `impl` | **Working** (limits: [known-issues](docs/known-issues.md) P1–P2) |
| Modules, visibility | **Working** (flat namespace: [known-issues](docs/known-issues.md) P3) |
| Local mutability, `while`, `for` over `List` | **Working** |
| Prelude capabilities: `Runtime`, `Clock`, `Filesystem`, `Network` | **Working** in the interpreter |
| Reference interpreter | **Working**, authoritative |
| Native C backend | **First-order subset only** ([known-issues](docs/known-issues.md) C1) |
| `regionlab` region/ownership checker | **Prototype**, separate, [regionlab/](regionlab/) |
| HIR / MIR | **Informational scaffolding** ([known-issues](docs/known-issues.md) C2) |
| Package registry, `attenuate`, string ops, WASM Component Model | **Not implemented** |
| Distributed runtime, WASM UI, AI-agent governance, concurrency runtime | **Design only** — see [ROADMAP.md](ROADMAP.md) |

The 47-test conformance suite (`tests/conformance/`) is the shared
arbiter for the semantics; it includes explicit attack cases (return a
capability, stash it in a let-bound closure, hide an effect in one
`match` arm).

---

## Compiler pipeline

```text
NOVA source (.nova)
  │  verifier/refspec/   — the authoritative frontend
  ▼
Lexer → Parser → AST (spans + node ids)
  → name & module resolution (RFC 0004)
  → Hindley–Milner type inference (RFC 0001)
  → row-typed effect checking (RFC 0001 §4.3 — equality, `= widen` to opt into subsumption)
  → capability reachability (RFC 0001 §4.5 — zero ambient authority)
  │
  ├─► nova check   — stop, report diagnostics
  ├─► nova run     — reference interpreter (verifier/refspec/eval.py)
  └─► nova build   — native C for the supported subset, else an
                      interpreter-backed runner
```

`regionlab/` implements the Region XOR memory model (Shared Read XOR
Exclusive Write) as a standalone prototype with its own 14-test suite. It
is **not yet integrated** into the main pipeline — that integration is
Milestone 1.

---

## Benchmarks

`benchmarks/` contains a wall-clock harness for the toolchain
(`challenge_suite.py`: `nova build` / `nova run` timings on this
machine) and a Python micro-benchmark of the host's own threading
primitives (`concurrency_bench.py`).

**These are not a cross-language comparison, and there is no honest one to
make yet** — the constructs you would compare (tasks, channels, native
loops) do not have a native code path. Any earlier table pitting NOVA
against Rust / Go / C++ was removed. See
[benchmarks/README.md](benchmarks/README.md).

---

## Roadmap

NOVA is at **Milestone 0 → 1** on a milestone ladder with no dates
([ROADMAP.md](ROADMAP.md)). In brief:

- **M0 Foundation** *(current)* — freeze the frontend semantics; resolve
  the open effect-derivation questions (known-issues S1, S2).
- **M1 Memory discipline** — integrate `regionlab` into the checker.
- **M2 Abstraction** — package manager, `attenuate`, qualified imports.
- **M3 Compilation** — a real IR and a full native backend; WASM.
- **M4+ Concurrency, resources, contracts** — built *on* the memory
  model, not bolted beside it.

The "platform" documents under `docs/full-stack/`, `docs/distributed/`
and `docs/ai/` are the deferred agenda (M7+). They are kept because the
thinking is load-bearing, not because the code exists.

---

## Documentation

| Category | Documents |
| :--- | :--- |
| **Foundation** | [Constitution](docs/foundation/LANGUAGE-CONSTITUTION.md) • [Philosophy](docs/foundation/LANGUAGE-PHILOSOPHY.md) • [Program Model](docs/foundation/PROGRAM-MODEL.md) • [Non-Goals](docs/foundation/NON-GOALS.md) • [Decision Log](docs/foundation/DECISION-LOG.md) • [Authority Map](docs/foundation/AUTHORITY-MAP.md) |
| **Language** | [Syntax & Grammar](docs/language/SYNTAX.md) • [Type System](docs/language/TYPE-SYSTEM.md) • [Effect System](docs/language/EFFECT-SYSTEM.md) • [Capabilities](docs/language/CAPABILITY-MODEL.md) • [Memory Model](docs/language/MEMORY-MODEL.md) |
| **RFCs** | [0001 core](RFC/0001-core-capability-effects.md) • [0002 data types](RFC/0002-structs-tuples-enums-pattern-matching.md) • [0003 generics/traits](RFC/0003-generics-and-traits.md) • [0004 modules](RFC/0004-modules-and-imports.md) • [0005 mutability](RFC/0005-local-mutability-and-loops.md) |
| **Honesty** | [Known issues](docs/known-issues.md) • [Roadmap](ROADMAP.md) |
| **Deferred agenda (design only)** | [Runtime](docs/runtime/) • [Full-stack](docs/full-stack/) • [Distributed](docs/distributed/) • [AI governance](docs/ai/) • [Platform](docs/platform/) |
| **Open source** | [Contributing](CONTRIBUTING.md) • [Contributor Roadmap](docs/open-source/CONTRIBUTOR-ROADMAP.md) • [Issue Backlog](docs/open-source/ISSUE-BACKLOG.md) |

---

## Contributing

```bash
# Verify local changes before a PR
./tools/check-all.sh
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Constitution](docs/foundation/LANGUAGE-CONSTITUTION.md). Good first work
right now is in the frontend and the conformance suite — the areas that
are real. See [docs/known-issues.md](docs/known-issues.md) for concrete,
scoped problems.

---

## License & governance

Apache 2.0 ([LICENSE](LICENSE)). Governance in
[GOVERNANCE.md](GOVERNANCE.md); security reporting in
[SECURITY.md](SECURITY.md).
