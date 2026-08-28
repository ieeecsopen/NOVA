# NOVA — Master Open-Source GitHub Issue Backlog

**Status:** Authoritative Issue Backlog Reference  
**Cross-References:** [CONTRIBUTOR-ROADMAP.md](CONTRIBUTOR-ROADMAP.md), [ISSUE-TAXONOMY.md](ISSUE-TAXONOMY.md), [ISSUE-GUIDELINES.md](ISSUE-GUIDELINES.md), [AUTHORITY-MAP.md](../foundation/AUTHORITY-MAP.md)

---

## 1. Executive Summary & Subsystem State Classification

Every major subsystem in NOVA is audited and classified into one of eight states:

| Subsystem | Authoritative Codebase | Implementation State | Active Work Area |
| :--- | :--- | :--- | :--- |
| **CLI & Driver** | `compiler/nova_compiler/cli.py` | `IMPLEMENTED` | `nova new`, `dev`, `check`, `build`, `run`, `test`, `fmt`, `lint`, `doc` |
| **Lexer & Parser** | `verifier/refspec/lexer.py`, `parser.py` | `IMPLEMENTED` | EBNF grammar, monotonic span tagging, AST construction |
| **Type Inference** | `verifier/refspec/check.py` | `IMPLEMENTED` | Hindley-Milner bidirectional inference, generics, traits |
| **Effect Row Lattice** | `verifier/refspec/check.py` | `IMPLEMENTED` | Pure defaults, row polymorphism, label saturation |
| **Capability Engine** | `verifier/refspec/reachability.py` | `IMPLEMENTED` | Transitive reachability, laundering defense, zero ambient authority |
| **Memory Model** | `regionlab/checker.py` | `PROTOTYPE` | Region XOR model (Shared Read XOR Exclusive Write); 14/14 tests |
| **IR Lowering** | `compiler/nova_compiler/hir.py`, `mir.py` | `IMPLEMENTED` | AST $\to$ HIR $\to$ MIR lowering, CFG basic blocks |
| **Codegen & WASM** | `compiler/nova_compiler/codegen_c.py` | `IMPLEMENTED` | C99 / LLVM `clang -O3` native & WebAssembly Component Model |
| **Task Scheduler** | `compiler/nova_compiler/` | `PARTIALLY IMPLEMENTED` | Chase-Lev work-stealing, structured concurrency, channels |
| **Package Manager** | `compiler/nova_compiler/pkg.py` | `IMPLEMENTED` | `nova.toml`, `nova.lock`, SHA-256 integrity, capability bounds |
| **Language Server** | `compiler/nova_compiler/lsp_server.py` | `IMPLEMENTED` | JSON-RPC 2.0 LSP, diagnostics, hover, autocomplete, formatting |
| **Self-Hosting** | `src/` | `PARTIALLY IMPLEMENTED` | Stage 1 self-hosted compiler & stdlib compiling via Stage 0 |
| **AI Governance** | `docs/ai/` | `SPECIFICATION ONLY` | Sandboxed agents, zero implicit authority, financial budget meters |
| **Adaptive Execution** | `docs/adaptive/` | `RESEARCH` | Multi-strategy execution (CPU/GPU/Remote); marked experimental |

---

## 2. Milestone Structure (M0–M15)

```
M0  — Foundation & Governance
M1  — Core Language Grammar & AST
M2  — Type System & Effect Lattice
M3  — Compiler IR Pipeline (HIR/MIR)
M4  — Runtime Engine & Memory Allocator
M5  — Developer Toolchain & LSP
M6  — WebAssembly & Portability Target
M7  — Concurrency & Work-Stealing Scheduler
M8  — Full-Stack Platform & WASM UI
M9  — Distributed Systems & Saga Consensus
M10 — Resource Semirings & Temporal Models
M11 — AI Governance & Sandboxed Agents
M12 — Verification Engine & SMT Integration
M13 — Adaptive Execution (Research)
M14 — Self-Hosting 4-Stage Bootstrap
M15 — Production 1.0 Release
```

---

## 3. Major Epics (12 Epics)

### [EPIC-01] Core Language & Syntax Stabilization
* **Area:** `area:language` | **Milestone:** `M1` | **Priority:** `priority:critical`
* **Goal:** Stabilize the EBNF grammar, ensure 100% lexical span coverage on all AST nodes, and eliminate parser ambiguities.
* **Specifications:** [`docs/language/SYNTAX.md`](../language/SYNTAX.md), [`docs/language/LANGUAGE-REFERENCE.md`](../language/LANGUAGE-REFERENCE.md).

### [EPIC-02] Type System, Generics & Trait Checking
* **Area:** `area:type-system` | **Milestone:** `M2` | **Priority:** `priority:critical`
* **Goal:** Provide bidirectional Hindley-Milner type inference with generic constraint resolution and associated type dispatch.
* **Specifications:** [`docs/language/TYPE-SYSTEM.md`](../language/TYPE-SYSTEM.md).

### [EPIC-03] Effect Rows & Pure-by-Default Semantics
* **Area:** `area:effects` | **Milestone:** `M2` | **Priority:** `priority:critical`
* **Goal:** Enforce pure-by-default function signatures, effect row polymorphism, and authority laundering prevention.
* **Specifications:** [`docs/language/EFFECT-SYSTEM.md`](../language/EFFECT-SYSTEM.md).

### [EPIC-04] Region XOR Memory Model & Drop Elaboration
* **Area:** `area:memory` | **Milestone:** `M3` | **Priority:** `priority:critical`
* **Goal:** Lower RegionLab's Region XOR (Shared Read XOR Exclusive Write) rules into MIR basic blocks and automated drop elaboration.
* **Specifications:** [`docs/language/MEMORY-MODEL.md`](../language/MEMORY-MODEL.md), [`regionlab/README.md`](../../regionlab/README.md).

### [EPIC-05] Compiler Mid-Level IR (MIR) & Direct LLVM Codegen
* **Area:** `area:compiler` | **Milestone:** `M3` | **Priority:** `priority:high`
* **Goal:** Mature the Mid-Level IR with basic block CFGs, SSA register allocation, and direct LLVM bitcode generation.
* **Specifications:** [`compiler/README.md`](../../compiler/README.md).

### [EPIC-06] High-Throughput Task Scheduler & Concurrency
* **Area:** `area:concurrency` | **Milestone:** `M7` | **Priority:** `priority:high`
* **Goal:** Deliver the Chase-Lev work-stealing task scheduler, structured `parallel`/`race` blocks, and typed message channels.
* **Specifications:** [`docs/runtime/SCHEDULER-DESIGN.md`](../runtime/SCHEDULER-DESIGN.md), [`docs/runtime/CONCURRENCY-MODEL.md`](../runtime/CONCURRENCY-MODEL.md).

### [EPIC-07] WebAssembly Component Model & WASI preview2
* **Area:** `area:wasm` | **Milestone:** `M6` | **Priority:** `priority:high`
* **Goal:** Emit sandboxed WebAssembly Component Model binaries with zero ambient authority and explicit WASI preview2 WIT bindings.
* **Specifications:** [`docs/platform/WASM-COMPONENT-MODEL.md`](../platform/WASM-COMPONENT-MODEL.md).

### [EPIC-08] Full-Stack Platform & Shared Nominal Model
* **Area:** `area:full-stack` | **Milestone:** `M8` | **Priority:** `priority:high`
* **Goal:** Enable end-to-end applications where Frontend VNodes, Backend RPC, and Database Entities share one nominal struct definition.
* **Specifications:** [`docs/full-stack/FULL-STACK-MODEL.md`](../full-stack/FULL-STACK-MODEL.md).

### [EPIC-09] Autonomous AI Governance & Budget Envelopes
* **Area:** `area:ai` | **Milestone:** `M11` | **Priority:** `priority:high`
* **Goal:** Introduce AI as a controlled computational primitive with zero implicit authority and hard financial budget meters.
* **Specifications:** [`docs/ai/AI-MODEL.md`](../ai/AI-MODEL.md), [`docs/ai/AI-SECURITY.md`](../ai/AI-SECURITY.md).

### [EPIC-10] Layered Verification & SMT Contract Proofs
* **Area:** `area:verification` | **Milestone:** `M12` | **Priority:** `priority:high`
* **Goal:** Verify design contracts (`requires`, `ensures`) through SMT solver discharge (Z3/CVC5) alongside runtime dynamic checks.
* **Specifications:** [`docs/verification/VERIFICATION-ARCHITECTURE.md`](../verification/VERIFICATION-ARCHITECTURE.md).

### [EPIC-11] 4-Stage Self-Hosting Bootstrap Pipeline
* **Area:** `area:self-hosting` | **Milestone:** `M14` | **Priority:** `priority:medium`
* **Goal:** Compile the NOVA compiler written in pure NOVA (`src/compiler/`) through Stage 1, Stage 2, and bit-identical Stage 3.
* **Specifications:** [`docs/platform/BOOTSTRAP.md`](../platform/BOOTSTRAP.md), [`docs/platform/SELF-HOSTING.md`](../platform/SELF-HOSTING.md).

### [EPIC-12] Developer Toolchain, LSP & Ecosystem
* **Area:** `area:tooling` | **Milestone:** `M5` | **Priority:** `priority:high`
* **Goal:** Provide production-grade developer tooling (`nova` CLI, LSP server, formatter, linter, package manager, and VS Code extension).
* **Specifications:** [`docs/ecosystem/DEVELOPER-EXPERIENCE.md`](../ecosystem/DEVELOPER-EXPERIENCE.md).

---

## 4. Good First Issues (15 Issues)

| ID | Title | Area | Complexity | Milestone | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GFI-01** | `[Docs] Add syntax cheatsheet to Getting Started guide` | `area:documentation` | `size:small` | `M0` | Create concise one-page syntax cheatsheet in `docs/language/`. |
| **GFI-02** | `[Parser] Add regression test for empty tuple literals` | `area:parser` | `size:small` | `M1` | Verify parsing and type inference of `()` unit literals in `tests/conformance/`. |
| **GFI-03** | `[CLI] Improve help descriptions for nova dev and nova build` | `area:tooling` | `size:small` | `M5` | Add descriptive examples to CLI `--help` output in `compiler/nova_compiler/cli.py`. |
| **GFI-04** | `[Diag] Improve span underline pointer formatting in error messages` | `area:compiler` | `size:small` | `M1` | Refine multiline ASCII diagnostic renderer in `verifier/refspec/diagnostics.py`. |
| **GFI-05** | `[Stdlib] Add string trimming and split utilities to std/prelude` | `area:stdlib` | `size:small` | `M5` | Implement pure string manipulation functions in `std/prelude.nova`. |
| **GFI-06** | `[Fmt] Ensure trailing comma preservation in multi-line struct instantiations` | `area:tooling` | `size:small` | `M5` | Update formatting rules in `compiler/nova_compiler/fmt.py`. |
| **GFI-07** | `[Lint] Add linter warning for unused let-bound variables` | `area:tooling` | `size:small` | `M5` | Warn on unused local bindings in `compiler/nova_compiler/lint.py`. |
| **GFI-08** | `[Example] Add recursive Fibonacci example with timing benchmark` | `area:benchmarks` | `size:small` | `M1` | Add `examples/fibonacci.nova` demonstrating pure recursion and `Clock.now`. |
| **GFI-09** | `[LSP] Add autocomplete trigger for standard library prelude types` | `area:lsp` | `size:small` | `M5` | Expand completion items in `compiler/nova_compiler/lsp_server.py`. |
| **GFI-10** | `[Test] Add conformance test for nested struct field access` | `area:type-system` | `size:small` | `M2` | Add `tests/conformance/046-nested-struct-fields.nova`. |
| **GFI-11** | `[Pkg] Validate semver format in nova add command` | `area:package-manager` | `size:small` | `M5` | Add SemVer regex validation in `compiler/nova_compiler/pkg.py`. |
| **GFI-12** | `[Docs] Document return capability laundering defense in CAPABILITY-MODEL.md` | `area:documentation` | `size:small` | `M2` | Detail attack vector 21 (`021-attack-return-capability-value.nova`). |
| **GFI-13** | `[CI] Add GitHub Actions badge to repository README.md` | `area:infrastructure` | `size:small` | `M0` | Embed CI status badge pointing to `.github/workflows/ci.yml`. |
| **GFI-14** | `[VSCode] Add syntax highlighting for intent, requires, and ensures` | `area:tooling` | `size:small` | `M5` | Update TextMate grammar in `editors/vscode/syntaxes/nova.tmLanguage.json`. |
| **GFI-15** | `[Benchmark] Add memory allocation benchmark harness for list operations` | `area:benchmarks` | `size:small` | `M4` | Track allocation high-watermarks in `benchmarks/challenge_suite.py`. |

---

## 5. Security & Threat Modeling Issues (10 Issues)

| ID | Title | Area | Priority | Milestone | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | `[Security] Audit transitive capability reachability across higher-order closures` | `area:security` | `priority:critical` | `M2` | Verify that captured capabilities cannot escape their lexical scope. |
| **SEC-02** | `[Security] Implement cryptographic SHA-256 package lockfile verification` | `area:package-manager` | `priority:high` | `M5` | Reject modified dependencies whose tarball hash diverges from `nova.lock`. |
| **SEC-03** | `[Security] Prevent ambient filesystem access in WebAssembly guests` | `area:wasm` | `priority:critical` | `M6` | Enforce zero WASI preopens unless explicitly declared in `nova.toml`. |
| **SEC-04** | `[Security] Enforce zero implicit authority on autonomous AI agent invocations` | `area:ai` | `priority:critical` | `M11` | Ensure agent prompt execution cannot access network or disk handles. |
| **SEC-05** | `[Security] Implement zero-copy secure memory clearing for Secret types` | `area:security` | `priority:high` | `M4` | Clear secret buffers with `explicit_bzero` on region scope exit. |
| **SEC-06** | `[Security] Add adversarial fuzz testing for malformed AST serialization` | `area:verification` | `priority:medium` | `M12` | Fuzz parser and deserializer with AFL++/libFuzzer. |
| **SEC-07** | `[Security] Verify Region XOR invariant under concurrent task preemption` | `area:memory` | `priority:critical` | `M7` | Prove no data races occur when task frames are stolen across worker threads. |
| **SEC-08** | `[Security] Audit FFI boundary for unquarantined raw pointers` | `area:security` | `priority:high` | `M4` | Ensure foreign C calls are quarantined inside `! {Unsafe}` effect blocks. |
| **SEC-09** | `[Security] Test prompt injection resistance in AI tool calling layer` | `area:ai` | `priority:high` | `M11` | Verify structured schema validators reject malicious tool payloads. |
| **SEC-10** | `[Security] Add automated vulnerability scanning to release pipeline` | `area:infrastructure` | `priority:medium` | `M15` | Integrate CodeQL and cargo-audit into `.github/workflows/ci.yml`. |

---

## 6. Dependency Graph & Critical Path

```
                                  [M0: Foundation]
                                         │
                                         ▼
                             [M1: Core Language Grammar]
                                         │
                                         ▼
                         [M2: Type System & Effect Lattice]
                                         │
                                         ▼
                          [M3: Compiler HIR & MIR Pipeline]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
         [M4: Runtime Engine]                        [M5: Toolchain & LSP]
                   │                                           │
                   ▼                                           ▼
         [M6: WASM Component]                        [M7: Concurrency]
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                            [M8: Full-Stack Platform]
                                         │
                                         ▼
                          [M9: Distributed Sagas & RPC]
                                         │
                                         ▼
                           [M10: Resources, Time & Cost]
                                         │
                                         ▼
                            [M11: AI Governance & Sandboxes]
                                         │
                                         ▼
                           [M12: Layered Verification & SMT]
                                         │
                                         ▼
                         [M13: Adaptive Execution (Research)]
                                         │
                                         ▼
                          [M14: 4-Stage Self-Hosting Ladder]
                                         │
                                         ▼
                             [M15: Production 1.0 Release]
```
