# NOVA

<div align="center">

[![CI](https://github.com/ieeecsopen/NOVA/actions/workflows/ci.yml/badge.svg)](https://github.com/ieeecsopen/NOVA/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-1.0_%22Genesis%22-7c3aed.svg)](https://github.com/ieeecsopen/NOVA/releases/tag/v1.0.0)
[![Conformance](https://img.shields.io/badge/Conformance-45%2F45_Passed-0e8a16.svg)](tests/)
[![RegionLab](https://img.shields.io/badge/RegionLab-14%2F14_Passed-0e8a16.svg)](regionlab/)
[![Links](https://img.shields.io/badge/Links-738%2F738_Verified-brightgreen.svg)](tools/check-links.py)

**A Constraint-Native Programming Language & Unified Application Platform**

*Unifying Types, Effect Rows, Capability Security, Zero-GC Memory Frames, Distributed Sagas, and Autonomous AI Governance.*

[**Quickstart**](#-quickstart) • [**Why NOVA?**](#-the-idea) • [**Architecture**](#-unified-platform-architecture) • [**Benchmarks**](#-performance--benchmarks) • [**Documentation**](#-documentation-sitemap) • [**Contributing**](#-contributing)

</div>

---

## 💡 The Idea

Programs carry critical real-world obligations that contemporary languages cannot express:
* *This dependency must not touch the network.*
* *This closure must not secretly launder filesystem authority.*
* *This autonomous AI agent must not exceed a $0.05 budget ceiling.*
* *This database entity must share identical typing across browser WASM and backend RPC.*

Today, these obligations live in disconnected code review comments, linter configs, API schemas, and runtime sandboxes — checked late by tools that do not understand whole-program semantics.

**NOVA unifies these obligations directly into the type system:**
1. **Pure Defaults & Effect Rows:** What a function *does* is an explicit part of its signature (`! {Runtime, Clock}`).
2. **Object Capabilities:** The authority to act on the outside world is an *unforgeable lexical token* you must be handed, not an ambient power any `import` confers.
3. **Region XOR Memory Safety:** Zero garbage collection pauses via lexical region frames (*Shared Read XOR Exclusive Write*).
4. **Controlled AI Primitives:** Autonomous reasoning loops execute under strict lexical capability bounds and hard financial budget meters.

```nova
// An effect label is a capability type.
// Purity is the default; authority is unforgeable.
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("Hello from NOVA!");
    0
}
```

---

## ⚡ The Diagnostic That Justifies NOVA

Capability-safe languages control who can *obtain* authority, but lose track of it once captured in a closure. Effect-typed languages track what happened, but allow arbitrary code to perform ambient effects. **NOVA prevents authority laundering statically at compile time:**

```nova
fn sneaky(c: Clock) -> (() -> Int) {
    || c.now()
}
```

```text
error[E0203]: closure captures capability `Clock` but its expected type does not declare it
 --> sneaky.nova:2:5
  |
2 |     || c.now()
  |     ^^^^^^^^^^ this closure has type `() -> Int ! {Clock}`
  = note: captures `c: Clock`
  = note: expected `() -> Int`
  = note: passing it here would hide the effect `Clock` from callers
```

---

## 🚀 Quickstart

NOVA includes a unified, production-grade compiler and developer toolchain:

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/ieeecsopen/NOVA.git
cd NOVA

# Run verification suite (Requires Python 3.11+ and Clang)
./tools/check-all.sh
```

### 2. Developer Inner Loop
```bash
# Scaffold a new production project
./nova new my_service
cd my_service

# Instant execution / development mode
../nova dev

# Typecheck and verify capability invariants without code generation
../nova check

# Run unified conformance and unit test suites
../nova test

# Compile to an optimized native machine binary (Mach-O / ELF)
../nova build

# Compile to a sandboxed WebAssembly Component Model artifact (.wasm)
../nova build --target wasm -o bin/service.wasm
```

---

## 🏗️ Unified Platform Architecture

NOVA is not merely a syntax — it is a single mathematical foundation spanning every tier of modern computation:

```text
                              ┌─────────────────────────────┐
                              │  Shared Nominal Definition  │
                              │  (Types, Invariants, DBC)   │
                              └──────────────┬──────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             │                               │                               │
             ▼                               ▼                               ▼
    [1. FRONTEND TIER]              [2. BACKEND & DATA]              [3. AI GOVERNOR]
 • Reactive VNode WASM           • Type-Safe RPC Handlers         • Sandboxed Autonomous Agent
 • Zero-overhead rendering       • Linear DB Transactions         • Lexical Capability Bounds
 • Event dispatcher              • Unforgeable Auth Tokens        • Hard Financial Envelope ($)
             │                               │                               │
             └───────────────────────────────┼───────────────────────────────┘
                                             │
                                             ▼
                               [4. DISTRIBUTED EXECUTION]
                            • Explicit Network Latency/Retries
                            • 3-Replica Saga Consensus
                            • OpenTelemetry Trace Spans
```

---

## ⚙️ Compiler & IR Pipeline

```text
NOVA Source (.nova)
    │
    ▼
[1] Lexer (Token kind tagging, monotonic span tracking)
    │
    ▼
[2] Parser (Recursive-descent, EBNF grammar, precedence climbing)
    │
    ▼
[3] AST (Spans & lexical NodeIDs on every node)
    │
    ▼
[4] Name Resolution (Multi-module transitive resolution, privacy & visibility)
    │
    ▼
[5] Type Inference & Unification (Hindley-Milner bidirectional inference)
    │
    ▼
[6] Effect Checking (Row typing lattice, pure default, effect polymorphism)
    │
    ▼
[7] Capability Reachability (Zero ambient authority, laundering prevention)
    │
    ▼
[8] Region & Memory Checking (Region XOR Invariant: Shared Read XOR Exclusive Write)
    │
    ▼
[9] High-Level IR (HIR) (Pattern tree desugaring, explicit closure environments)
    │
    ▼
[10] Mid-Level IR (MIR) (CFG basic blocks, drop elaboration, region frames)
    │
    ▼
[11] Code Generation (Optimized C99 / LLVM `clang -O3` native machine code)
    │
    ▼
Native Executable Binary (Mach-O / ELF / WASM Component)
```

Inspect compiler representations at any time:
```bash
./nova check examples/hello.nova --emit-hir --emit-mir
```

---

## 📊 Performance & Benchmarks

Empirically measured on Apple Silicon using the [Public Challenge Benchmark Suite](docs/validation/CHALLENGE-BENCHMARKS.md):

| Metric | NOVA 1.0 Baseline | Rust (Tokio) | Go | C++ (Clang) |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Build Time** | **44.7 ms** | ~1,200 ms | ~180 ms | ~850 ms |
| **Incremental Cached Build** | **0.25 ms** | ~150 ms | ~45 ms | ~120 ms |
| **Task Creation Throughput** | **251,923 tasks/s** | ~180,000 tasks/s | ~250,000 tasks/s | ~140,000 tasks/s |
| **Message Channel Throughput**| **1,708,954 msg/s** | ~1,500,000 msg/s | ~1,200,000 msg/s | ~1,100,000 msg/s |
| **Native Binary Footprint** | **33.5 KB** | ~350 KB | ~1,800 KB | ~65 KB |
| **Memory Management Model** | **Zero-GC Regions**| Lifetime Borrowing | Tracing GC | Manual / RAII |

---

## 📚 Documentation Sitemap

| Category | Primary Documents |
| :--- | :--- |
| **Foundation** | [Constitution](docs/foundation/LANGUAGE-CONSTITUTION.md) • [Philosophy](docs/foundation/LANGUAGE-PHILOSOPHY.md) • [Program Model](docs/foundation/PROGRAM-MODEL.md) • [Non-Goals](docs/foundation/NON-GOALS.md) • [Decision Log](docs/foundation/DECISION-LOG.md) |
| **Language Specs** | [Syntax & Grammar](docs/language/SYNTAX.md) • [Type System](docs/language/TYPE-SYSTEM.md) • [Effect System](docs/language/EFFECT-SYSTEM.md) • [Capabilities](docs/language/CAPABILITY-MODEL.md) • [Memory Model](docs/language/MEMORY-MODEL.md) • [Language Reference](docs/language/LANGUAGE-REFERENCE.md) |
| **Runtime & Concurrency** | [Architecture](docs/runtime/ARCHITECTURE.md) • [Scheduler Design](docs/runtime/SCHEDULER-DESIGN.md) • [Concurrency Model](docs/runtime/CONCURRENCY-MODEL.md) • [Resource Semirings](docs/runtime/RESOURCE-MODEL.md) • [Observability](docs/runtime/OBSERVABILITY.md) |
| **Full-Stack & Distributed** | [Full-Stack Model](docs/full-stack/FULL-STACK-MODEL.md) • [UI WASM Model](docs/full-stack/UI-MODEL.md) • [Distributed Sagas](docs/distributed/DISTRIBUTED-MODEL.md) • [Remote Compute](docs/distributed/REMOTE-EXECUTION.md) |
| **AI Governance** | [AI Computational Primitive](docs/ai/AI-MODEL.md) • [Autonomous Agents](docs/ai/AGENT-MODEL.md) • [AI Security & Sandboxing](docs/ai/AI-SECURITY.md) • [Provenance & Lineage](docs/ai/MODEL-PROVENANCE.md) |
| **Verification & Security** | [Verification Architecture](docs/verification/VERIFICATION-ARCHITECTURE.md) • [Intent & Contracts](docs/verification/INTENT-MODEL.md) • [Security Audit](docs/verification/SECURITY-AUDIT.md) • [Threat Model](docs/verification/THREAT-MODEL.md) |
| **Platform & Portability** | [WASM Component Model](docs/platform/WASM-COMPONENT-MODEL.md) • [FFI Bridges](docs/platform/FFI-MODEL.md) • [4-Stage Bootstrap](docs/platform/BOOTSTRAP.md) • [Self-Hosting](docs/platform/SELF-HOSTING.md) |
| **Open Source** | [Contributor Roadmap](docs/open-source/CONTRIBUTOR-ROADMAP.md) • [Issue Backlog](docs/open-source/ISSUE-BACKLOG.md) • [Issue Taxonomy](docs/open-source/ISSUE-TAXONOMY.md) • [Contribution Path](docs/open-source/CONTRIBUTION-PATH.md) |

---

## 🤝 Contributing

We welcome contributors of all experience levels! NOVA uses an open, structured milestone ladder and curated starter tasks.

* 📖 Read our [**Contributing Guide**](CONTRIBUTING.md) and [**Language Constitution**](docs/foundation/LANGUAGE-CONSTITUTION.md).
* 🎯 Start with an issue labeled [`status:good-first-issue`](https://github.com/ieeecsopen/NOVA/labels/status%3Agood-first-issue).
* 🗺️ Explore the [**Contributor Roadmap (M0–M15)**](docs/open-source/CONTRIBUTOR-ROADMAP.md) and [**Architecture Workstreams**](docs/open-source/ARCHITECTURE-WORKSTREAMS.md).

```bash
# Verify your local changes before submitting a PR
./tools/check-all.sh
```

---

## ⚖️ License & Governance

NOVA is open-source software licensed under the [**Apache License 2.0**](LICENSE).  
Project governance is documented in [**GOVERNANCE.md**](GOVERNANCE.md) and security reporting procedures are in [**SECURITY.md**](SECURITY.md).
