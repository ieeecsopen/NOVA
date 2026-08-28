#!/usr/bin/env python3
"""Script to populate the NOVA GitHub Issue Backlog directly into ieeecsopen/NOVA."""
import json
import subprocess
import sys
import time

REPO = "ieeecsopen/NOVA"

MILESTONE_MAP = {
    "M0": "M0 — Foundation",
    "M1": "M1 — Core Language",
    "M2": "M2 — Type System & Safety",
    "M3": "M3 — Compiler & IR",
    "M4": "M4 — Runtime",
    "M5": "M5 — Toolchain",
    "M6": "M6 — WASM",
    "M7": "M7 — Concurrency",
    "M8": "M8 — Full-Stack",
    "M9": "M9 — Distributed",
    "M10": "M10 — Resources / Time / Uncertainty",
    "M11": "M11 — AI",
    "M12": "M12 — Verification",
    "M13": "M13 — Adaptive Execution",
    "M14": "M14 — Self-Hosting",
    "M15": "M15 — Production / 1.0",
}

ISSUES = [
    # -------------------------------------------------------------
    # 0. AUTHORITATIVE MAP
    # -------------------------------------------------------------
    {
        "title": "[Architecture] Establish Authoritative Subsystem Implementation Map",
        "labels": ["type:refactor", "priority:critical", "status:ready", "area:compiler", "size:small"],
        "milestone": "M0",
        "body": """## Summary
Establish and document the single authoritative codebase for each language and compiler subsystem to prevent duplicate parallel implementations.

## Current State
- `compiler/nova_compiler/`: Authoritative developer toolchain CLI, IR lowering (HIR/MIR), and C99/LLVM native/WASM backend.
- `verifier/refspec/`: Authoritative Hindley-Milner type inference, effect rows, and capability reachability analysis.
- `regionlab/`: Authoritative reference prototype for Region XOR memory safety.
- `src/compiler/`: Pure NOVA self-hosted compiler stage 1 source.

## Relevant Specification
- `docs/foundation/AUTHORITY-MAP.md`
- `docs/foundation/COMPILER-AUDIT-REPORT.md`

## Acceptance Criteria
- [ ] `docs/foundation/AUTHORITY-MAP.md` ratified as source of truth.
- [ ] Deprecated duplicate prototypes marked in repository READMEs.
- [ ] Subsystem routing documented for all incoming open-source PRs.
"""
    },

    # -------------------------------------------------------------
    # 1. EPICS (12 Major Epics)
    # -------------------------------------------------------------
    {
        "title": "[Epic] Core Language & Syntax Stabilization",
        "labels": ["type:feature", "priority:critical", "status:in-progress", "area:language", "size:large"],
        "milestone": "M1",
        "body": """## Goal
Stabilize the core NOVA EBNF grammar, ensure 100% lexical span coverage across all AST nodes, and eliminate parser ambiguities.

## Relevant Specifications
- `docs/language/SYNTAX.md`
- `docs/language/LANGUAGE-REFERENCE.md`

## Major Workstreams
1. Parser precedence climbing for binary operators.
2. Full lexical Span tracking on all expressions, types, and declarations.
3. Pattern match syntax expansion (nested tuples, enum payloads, wildcard guards).

## Definition of Done
- [ ] Core grammar frozen for 1.0.
- [ ] All 45 conformance tests pass with 0 syntax warnings.
- [ ] Comprehensive syntax reference documentation verified.
"""
    },
    {
        "title": "[Epic] Type System, Generics & Trait Checking",
        "labels": ["type:feature", "priority:critical", "status:in-progress", "area:type-system", "size:large"],
        "milestone": "M2",
        "body": """## Goal
Provide bidirectional Hindley-Milner type inference with generic constraint resolution, nominal structs, algebraic enums, and trait method dispatch.

## Relevant Specifications
- `docs/language/TYPE-SYSTEM.md`
- `RFC/0003-generics-traits-enums.md`

## Major Workstreams
1. Bidirectional type unification for generic call-sites.
2. Trait constraint solving and orphan rule checking.
3. Exhaustive algebraic pattern matching verification.

## Definition of Done
- [ ] Zero unhandled type mismatches or unsoundness leaks.
- [ ] Trait method dispatch lowering verified in HIR.
"""
    },
    {
        "title": "[Epic] Effect Rows & Pure-by-Default Semantics",
        "labels": ["type:feature", "priority:critical", "status:in-progress", "area:effects", "size:large"],
        "milestone": "M2",
        "body": """## Goal
Enforce pure-by-default function signatures, effect row polymorphism, and authority laundering prevention across higher-order closures.

## Relevant Specifications
- `docs/language/EFFECT-SYSTEM.md`
- `RFC/0001-core-capability-effects.md`

## Major Workstreams
1. Row typing lattice with label saturation.
2. Effect row propagation through closure captures and function arguments.
3. Static authority laundering detection in `reachability.py`.

## Definition of Done
- [ ] Pure functions execute with zero side-effects.
- [ ] Unannotated side-effects rejected with clear ASCII diagnostics.
"""
    },
    {
        "title": "[Epic] Region XOR Memory Model & Drop Elaboration",
        "labels": ["type:feature", "priority:critical", "status:in-progress", "area:memory", "size:large"],
        "milestone": "M3",
        "body": """## Goal
Lower RegionLab's Region XOR (Shared Read XOR Exclusive Write) rules into MIR basic blocks with automated drop elaboration and zero-GC memory frames.

## Relevant Specifications
- `docs/language/MEMORY-MODEL.md`
- `regionlab/README.md`

## Major Workstreams
1. Region frame allocation on thread stacks.
2. Lexical scope exit drop elaboration in Mid-Level IR.
3. Prevention of use-after-free and double-close across async regions.

## Definition of Done
- [ ] All 14 RegionLab operational semantics tests integrated into compiler MIR pipeline.
- [ ] Zero memory leaks or dangling pointers in generated binaries.
"""
    },
    {
        "title": "[Epic] Compiler Mid-Level IR (MIR) & Direct LLVM Codegen",
        "labels": ["type:feature", "priority:high", "status:in-progress", "area:compiler", "size:large"],
        "milestone": "M3",
        "body": """## Goal
Mature the Mid-Level IR (MIR) with basic block CFGs, SSA register allocation, and direct LLVM bitcode generation alongside the optimized C99 backend.

## Relevant Specifications
- `compiler/README.md`
- `docs/foundation/COMPILER-AUDIT-REPORT.md`

## Major Workstreams
1. High-Level IR (HIR) pattern tree desugaring.
2. Mid-Level IR (MIR) Control Flow Graph basic blocks and terminators.
3. LLVM C-API direct bitcode emission.

## Definition of Done
- [ ] `--emit-hir` and `--emit-mir` produce verified, valid IR representations.
- [ ] Clean build time remains < 50ms for standard applications.
"""
    },
    {
        "title": "[Epic] High-Throughput Task Scheduler & Concurrency",
        "labels": ["type:feature", "priority:high", "status:ready", "area:concurrency", "size:large"],
        "milestone": "M7",
        "body": """## Goal
Deliver the Chase-Lev work-stealing task scheduler, structured `parallel`/`race` blocks, and typed message channels.

## Relevant Specifications
- `docs/runtime/SCHEDULER-DESIGN.md`
- `docs/runtime/CONCURRENCY-MODEL.md`

## Major Workstreams
1. Lock-free Chase-Lev work-stealing deque implementation.
2. Cooperative task suspension and cancellation bubbling.
3. Multi-producer multi-consumer typed channels.

## Definition of Done
- [ ] Task spawn throughput exceeds 250,000 tasks/sec.
- [ ] Channel throughput exceeds 1,500,000 msgs/sec.
"""
    },
    {
        "title": "[Epic] WebAssembly Component Model & WASI preview2",
        "labels": ["type:feature", "priority:high", "status:ready", "area:wasm", "size:large"],
        "milestone": "M6",
        "body": """## Goal
Emit sandboxed WebAssembly Component Model binaries with zero ambient authority and explicit WASI preview2 WIT bindings.

## Relevant Specifications
- `docs/platform/WASM-COMPONENT-MODEL.md`
- `docs/runtime/RUNTIME-REPORT.md`

## Major Workstreams
1. `nova build --target wasm` WIT interface extraction.
2. Linear memory capability isolation in WASM host runtimes.
3. Standard library preview2 bindings.

## Definition of Done
- [ ] Standalone `.wasm` component executes cleanly in Wasmtime with zero ambient permissions.
"""
    },
    {
        "title": "[Epic] Full-Stack Platform & Shared Nominal Model",
        "labels": ["type:feature", "priority:high", "status:ready", "area:full-stack", "size:large"],
        "milestone": "M8",
        "body": """## Goal
Enable end-to-end applications where Frontend VNodes, Backend RPC, and Database Entities share one nominal struct definition without serialization drift.

## Relevant Specifications
- `docs/full-stack/FULL-STACK-MODEL.md`
- `docs/full-stack/PLATFORM-REPORT.md`

## Major Workstreams
1. Reactive WASM VNode UI component rendering.
2. Type-safe RPC router and unforgeable `AuthToken` capability tokens.
3. Persistent entity ACID transaction coordinator.

## Definition of Done
- [ ] `examples/enterprise-platform.nova` compiles and runs across all tiers with zero serialization drift.
"""
    },
    {
        "title": "[Epic] Autonomous AI Governance & Budget Envelopes",
        "labels": ["type:feature", "priority:high", "status:ready", "area:ai", "size:large"],
        "milestone": "M11",
        "body": """## Goal
Introduce AI as a controlled computational primitive with zero implicit authority, lexical capability bounds, and hard financial budget meters.

## Relevant Specifications
- `docs/ai/AI-MODEL.md`
- `docs/ai/AI-SECURITY.md`

## Major Workstreams
1. Lexical capability sandboxing for AI agent tool execution.
2. Dynamic token counters and financial cost ceiling enforcement.
3. Context replay and model provenance auditing.

## Definition of Done
- [ ] Agent execution halts deterministically upon budget ceiling exhaustion.
- [ ] Unauthorized tool execution blocked at compile time.
"""
    },
    {
        "title": "[Epic] Layered Verification & SMT Contract Proofs",
        "labels": ["type:feature", "priority:high", "status:ready", "area:verification", "size:large"],
        "milestone": "M12",
        "body": """## Goal
Verify design contracts (`requires`, `ensures`) through SMT solver discharge (Z3/CVC5) alongside runtime dynamic checks.

## Relevant Specifications
- `docs/verification/INTENT-MODEL.md`
- `docs/verification/VERIFICATION-ARCHITECTURE.md`

## Major Workstreams
1. Intent and contract syntax lowering into verification conditions.
2. SMT-LIB2 format translation for linear arithmetic.
3. Fallback runtime contract assertion injection.

## Definition of Done
- [ ] Statically proven invariants eliminate redundant runtime assertions.
- [ ] 5-tier verification status reported accurately to developers.
"""
    },
    {
        "title": "[Epic] 4-Stage Self-Hosting Bootstrap Pipeline",
        "labels": ["type:feature", "priority:medium", "status:in-progress", "area:self-hosting", "size:large"],
        "milestone": "M14",
        "body": """## Goal
Compile the NOVA compiler written in pure NOVA (`src/compiler/`) through Stage 1, Stage 2, and bit-identical Stage 3.

## Relevant Specifications
- `docs/platform/BOOTSTRAP.md`
- `docs/platform/SELF-HOSTING.md`

## Major Workstreams
1. Port AST, Lexer, Parser, and Typechecker to pure NOVA in `src/compiler/`.
2. Verify Stage 1 compiler binary emission via Stage 0.
3. Prove bit-identical fixed point: `SHA256(Stage 2) == SHA256(Stage 3)`.

## Definition of Done
- [ ] Diverse Double-Compiling audit completed.
- [ ] Pure NOVA self-hosted toolchain capable of compiling full test suite.
"""
    },
    {
        "title": "[Epic] Developer Toolchain, LSP & Ecosystem",
        "labels": ["type:feature", "priority:high", "status:in-progress", "area:tooling", "size:large"],
        "milestone": "M5",
        "body": """## Goal
Provide production-grade developer tooling (`nova` CLI, LSP server, formatter, linter, package manager, and VS Code extension).

## Relevant Specifications
- `docs/ecosystem/DEVELOPER-EXPERIENCE.md`
- `docs/runtime/RUNTIME-REPORT.md`

## Major Workstreams
1. JSON-RPC 2.0 Language Server Protocol (`nova lsp`) with go-to-definition and autocomplete.
2. Canonical code formatting (`nova fmt`) and lint rules (`nova lint`).
3. Cryptographic package lockfile validation (`nova update`, `nova.lock`).

## Definition of Done
- [ ] VS Code extension provides live diagnostics, semantic hover, and formatting on save.
- [ ] `nova new myapp && cd myapp && nova run` executes seamlessly.
"""
    },

    # -------------------------------------------------------------
    # 2. GOOD FIRST ISSUES (15 Issues)
    # -------------------------------------------------------------
    {
        "title": "[GFI] Add syntax cheatsheet to Getting Started guide",
        "labels": ["type:documentation", "priority:low", "status:good-first-issue", "area:documentation", "size:small"],
        "milestone": "M0",
        "body": """## Summary
Create a concise, one-page syntax cheatsheet in `docs/language/` highlighting variables, functions, effect rows, structs, enums, pattern matching, and capabilities.

## Relevant Specification
- `docs/language/SYNTAX.md`
- `docs/language/LANGUAGE-REFERENCE.md`

## Acceptance Criteria
- [ ] One-page cheatsheet markdown file created.
- [ ] All code snippets verified with `./nova check`.
- [ ] Linked from main repository `README.md`.
"""
    },
    {
        "title": "[GFI] Add parser regression test for empty tuple literals",
        "labels": ["type:test", "priority:low", "status:good-first-issue", "area:parser", "size:small"],
        "milestone": "M1",
        "body": """## Summary
Add a dedicated conformance test verifying that empty tuple literals `()` are correctly parsed as `Unit` and pass type inference.

## Relevant Specification
- `docs/language/TYPE-SYSTEM.md`
- `tests/conformance/039-tuples.nova`

## Acceptance Criteria
- [ ] Add `tests/conformance/047-unit-tuple-literals.nova`.
- [ ] `./tools/check-all.sh` passes with 46 conformance tests.
"""
    },
    {
        "title": "[GFI] Improve help descriptions for nova dev and nova build",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:tooling", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Enhance the CLI argument parser descriptions in `compiler/nova_compiler/cli.py` to include clear usage examples for `nova dev`, `nova build --target wasm`, and `nova check --emit-hir`.

## Implementation File
- `compiler/nova_compiler/cli.py`

## Acceptance Criteria
- [ ] `./nova --help` displays clean, descriptive examples.
- [ ] No regressions in argument parsing.
"""
    },
    {
        "title": "[GFI] Improve span underline pointer formatting in error diagnostics",
        "labels": ["type:compiler", "priority:low", "status:good-first-issue", "area:compiler", "size:small"],
        "milestone": "M1",
        "body": """## Summary
Refine multiline ASCII error diagnostic rendering in `verifier/refspec/diagnostics.py` to ensure consistent column alignment when source lines contain tab characters or unicode glyphs.

## Implementation File
- `verifier/refspec/diagnostics.py`

## Acceptance Criteria
- [ ] Multiline error pointers accurately align with token boundaries.
- [ ] Conformance tests in `tests/` pass.
"""
    },
    {
        "title": "[GFI] Add string trimming and split utilities to standard library",
        "labels": ["type:feature", "priority:medium", "status:good-first-issue", "area:stdlib", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Implement pure string manipulation functions (`trim`, `split`, `starts_with`, `ends_with`) in `std/prelude.nova` with zero ambient authority.

## Implementation File
- `std/prelude.nova`

## Acceptance Criteria
- [ ] Functions added to `std/prelude.nova` with pure effect signatures `! {}`.
- [ ] Unit tests added in `tests/conformance/`.
"""
    },
    {
        "title": "[GFI] Ensure trailing comma preservation in multi-line struct instantiations in formatter",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:tooling", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Update formatting logic in `compiler/nova_compiler/fmt.py` to preserve trailing commas on multi-line struct field instantiations.

## Implementation File
- `compiler/nova_compiler/fmt.py`

## Acceptance Criteria
- [ ] Trailing commas preserved when struct fields span multiple lines.
- [ ] `./nova fmt --check` succeeds on all `examples/`.
"""
    },
    {
        "title": "[GFI] Add linter warning for unused let-bound variables",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:tooling", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Add a quality lint rule in `compiler/nova_compiler/lint.py` that emits an advisory warning when a local immutable `let` binding is never referenced in subsequent expressions.

## Implementation File
- `compiler/nova_compiler/lint.py`

## Acceptance Criteria
- [ ] Unused variables flagged with warning code `W0201`.
- [ ] Variables prefixed with `_` ignored.
"""
    },
    {
        "title": "[GFI] Add recursive Fibonacci example with timing benchmark",
        "labels": ["type:benchmark", "priority:low", "status:good-first-issue", "area:benchmarks", "size:small"],
        "milestone": "M1",
        "body": """## Summary
Create `examples/fibonacci.nova` demonstrating pure recursive function evaluation and monotonic elapsed time measurement via `Clock.now`.

## Implementation File
- `examples/fibonacci.nova`

## Acceptance Criteria
- [ ] Example compiles and executes with `./nova run examples/fibonacci.nova`.
- [ ] Output prints calculated Fibonacci numbers and nanosecond timing.
"""
    },
    {
        "title": "[GFI] Add autocomplete trigger for standard library prelude types in LSP",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:lsp", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Expand completion items in `compiler/nova_compiler/lsp_server.py` to provide rich autocomplete suggestions for standard library types (`Option`, `Result`, `List`, `Runtime`, `Clock`).

## Implementation File
- `compiler/nova_compiler/lsp_server.py`

## Acceptance Criteria
- [ ] LSP completion returns type descriptions and docstrings.
"""
    },
    {
        "title": "[GFI] Add conformance test for nested struct field access",
        "labels": ["type:test", "priority:low", "status:good-first-issue", "area:type-system", "size:small"],
        "milestone": "M2",
        "body": """## Summary
Add a conformance test in `tests/conformance/` verifying that deep field access chains (e.g. `user.profile.address.city`) typecheck and lower cleanly into C99/WASM.

## Implementation File
- `tests/conformance/048-nested-struct-fields.nova`

## Acceptance Criteria
- [ ] Test added and verified with `./tools/check-all.sh`.
"""
    },
    {
        "title": "[GFI] Validate SemVer format in nova add package command",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:package-manager", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Add strict Semantic Versioning (SemVer 2.0.0) regex validation in `compiler/nova_compiler/pkg.py` when running `nova add <pkg> --version <ver>`.

## Implementation File
- `compiler/nova_compiler/pkg.py`

## Acceptance Criteria
- [ ] Invalid version strings (e.g. `v1`, `alpha`) rejected with a helpful diagnostic.
"""
    },
    {
        "title": "[GFI] Document return capability laundering defense in CAPABILITY-MODEL.md",
        "labels": ["type:documentation", "priority:low", "status:good-first-issue", "area:documentation", "size:small"],
        "milestone": "M2",
        "body": """## Summary
Add an explanatory section in `docs/language/CAPABILITY-MODEL.md` analyzing attack vector 21 (`021-attack-return-capability-value.nova`) and how the transitive reachability engine blocks it.

## Relevant File
- `docs/language/CAPABILITY-MODEL.md`
- `tests/conformance/021-attack-return-capability-value.nova`

## Acceptance Criteria
- [ ] Section added with diagrams and type lattice rules.
"""
    },
    {
        "title": "[GFI] Add GitHub Actions status badge to repository README.md",
        "labels": ["type:documentation", "priority:low", "status:good-first-issue", "area:infrastructure", "size:small"],
        "milestone": "M0",
        "body": """## Summary
Embed a live GitHub Actions CI workflow status badge at the top of the repository `README.md`.

## Relevant File
- `README.md`
- `.github/workflows/ci.yml`

## Acceptance Criteria
- [ ] Badge displays passing build status on `origin/main`.
"""
    },
    {
        "title": "[GFI] Add syntax highlighting for intent, requires, and ensures in VS Code extension",
        "labels": ["type:tooling", "priority:low", "status:good-first-issue", "area:tooling", "size:small"],
        "milestone": "M5",
        "body": """## Summary
Update the TextMate syntax grammar in `editors/vscode/syntaxes/nova.tmLanguage.json` to highlight verification keywords `intent`, `requires`, and `ensures`.

## Implementation File
- `editors/vscode/syntaxes/nova.tmLanguage.json`

## Acceptance Criteria
- [ ] Contract keywords highlighted as control keywords in VS Code.
"""
    },
    {
        "title": "[GFI] Add memory allocation benchmark harness for list operations",
        "labels": ["type:benchmark", "priority:low", "status:good-first-issue", "area:benchmarks", "size:small"],
        "milestone": "M4",
        "body": """## Summary
Expand `benchmarks/challenge_suite.py` to record total heap allocation bytes and allocation counts during large list transformations.

## Implementation File
- `benchmarks/challenge_suite.py`

## Acceptance Criteria
- [ ] List allocation metrics emitted to `benchmarks/results.json`.
"""
    },

    # -------------------------------------------------------------
    # 3. SECURITY & THREAT MODELING ISSUES (10 Issues)
    # -------------------------------------------------------------
    {
        "title": "[Security] Audit transitive capability reachability across higher-order closures",
        "labels": ["type:security", "priority:critical", "status:help-wanted", "area:security", "size:medium"],
        "milestone": "M2",
        "body": """## Summary
Conduct formal verification that captured capability handles inside deeply nested closures cannot escape their lexical scope or be laundered through pure wrapper functions.

## Relevant Specification
- `docs/verification/SECURITY-AUDIT.md`
- `verifier/refspec/reachability.py`

## Acceptance Criteria
- [ ] Adversarial test suite with 10 laundering vectors added in `tests/conformance/`.
- [ ] Reachability checker proves zero authority leak.
"""
    },
    {
        "title": "[Security] Implement cryptographic SHA-256 package lockfile verification",
        "labels": ["type:security", "priority:high", "status:help-wanted", "area:package-manager", "size:medium"],
        "milestone": "M5",
        "body": """## Summary
Enforce strict SHA-256 integrity digest verification during `nova build` to prevent supply-chain tampering of third-party package tarballs.

## Implementation File
- `compiler/nova_compiler/pkg.py`

## Acceptance Criteria
- [ ] Packages with modified tarball digests rejected immediately.
- [ ] `nova.lock` format validated cryptographically.
"""
    },
    {
        "title": "[Security] Prevent ambient filesystem access in WebAssembly guests",
        "labels": ["type:security", "priority:critical", "status:help-wanted", "area:wasm", "size:medium"],
        "milestone": "M6",
        "body": """## Summary
Audit the WASI preview2 compilation pipeline to ensure guest WASM modules receive zero preopened directory descriptors unless explicitly declared in `nova.toml`.

## Relevant Specification
- `docs/platform/WASM-COMPONENT-MODEL.md`
- `compiler/nova_compiler/codegen_c.py`

## Acceptance Criteria
- [ ] Guest WASM binary cannot read host filesystem without explicit capability token.
"""
    },
    {
        "title": "[Security] Enforce zero implicit authority on autonomous AI agent invocations",
        "labels": ["type:security", "priority:critical", "status:help-wanted", "area:ai", "size:medium"],
        "milestone": "M11",
        "body": """## Summary
Verify that autonomous AI reasoning loops cannot access system primitives (network, disk, subprocesses) without explicit lexical capability delegation.

## Relevant Specification
- `docs/ai/AI-SECURITY.md`
- `docs/ai/AI-MODEL.md`

## Acceptance Criteria
- [ ] Agent sandbox blocks unauthorized ambient tool execution.
"""
    },
    {
        "title": "[Security] Implement zero-copy secure memory clearing for Secret types",
        "labels": ["type:security", "priority:high", "status:help-wanted", "area:security", "size:medium"],
        "milestone": "M4",
        "body": """## Summary
Implement automated memory zeroing (`explicit_bzero`) upon scope exit for structs carrying the `Secret` capability to prevent memory dumps and cold-boot attacks.

## Implementation File
- `compiler/nova_compiler/codegen_c.py`

## Acceptance Criteria
- [ ] Secret memory wiped immediately upon region drop elaboration.
"""
    },
    {
        "title": "[Security] Add adversarial fuzz testing for malformed AST serialization",
        "labels": ["type:security", "priority:medium", "status:help-wanted", "area:verification", "size:medium"],
        "milestone": "M12",
        "body": """## Summary
Integrate continuous libFuzzer / AFL++ test harnesses against the lexer, parser, and AST deserializer to detect buffer overflows and parser hangs.

## Implementation File
- `verifier/refspec/parser.py`

## Acceptance Criteria
- [ ] 24-hour fuzz run completes with 0 panics or memory crashes.
"""
    },
    {
        "title": "[Security] Verify Region XOR invariant under concurrent task preemption",
        "labels": ["type:security", "priority:critical", "status:help-wanted", "area:memory", "size:medium"],
        "milestone": "M7",
        "body": """## Summary
Prove that the Region XOR Invariant (Shared Read XOR Exclusive Write) is preserved when task frames are stolen across worker threads in the work-stealing scheduler.

## Relevant Specification
- `docs/language/MEMORY-MODEL.md`
- `regionlab/checker.py`

## Acceptance Criteria
- [ ] ThreadSanitizer (TSan) test suite runs with zero data race reports.
"""
    },
    {
        "title": "[Security] Audit FFI boundary for unquarantined raw pointers",
        "labels": ["type:security", "priority:high", "status:help-wanted", "area:security", "size:medium"],
        "milestone": "M4",
        "body": """## Summary
Enforce that all foreign C function invocations are strictly quarantined within explicit `! {Unsafe}` effect blocks.

## Relevant Specification
- `docs/platform/FFI-MODEL.md`
- `verifier/refspec/check.py`

## Acceptance Criteria
- [ ] Calling FFI functions without `! {Unsafe}` rejected at compile time (`E0130`).
"""
    },
    {
        "title": "[Security] Test prompt injection resistance in AI tool calling layer",
        "labels": ["type:security", "priority:high", "status:help-wanted", "area:ai", "size:medium"],
        "milestone": "M11",
        "body": """## Summary
Construct an adversarial test suite simulating prompt injection attacks attempting to force AI agents to execute unauthorized tools or exceed token budgets.

## Relevant Specification
- `docs/ai/AI-SECURITY.md`

## Acceptance Criteria
- [ ] Injection attempts blocked deterministically by schema validator.
"""
    },
    {
        "title": "[Security] Add automated vulnerability scanning to release pipeline",
        "labels": ["type:security", "priority:medium", "status:help-wanted", "area:infrastructure", "size:small"],
        "milestone": "M15",
        "body": """## Summary
Integrate GitHub CodeQL static analysis and dependency vulnerability scanning into `.github/workflows/ci.yml`.

## Implementation File
- `.github/workflows/ci.yml`

## Acceptance Criteria
- [ ] CodeQL security scans run on every pull request.
"""
    },

    # -------------------------------------------------------------
    # 4. RESEARCH & RFC ISSUES (8 Issues)
    # -------------------------------------------------------------
    {
        "title": "[Research] Epistemic Uncertainty Type Representation in Linear Programs",
        "labels": ["type:research", "priority:medium", "status:research", "area:uncertainty", "size:research"],
        "milestone": "M10",
        "body": """## Research Question
How should epistemic certainty bounds and probability distributions be represented in NOVA's static type system without introducing runtime GC overhead?

## Context & Prior Art
Survey probabilistic programming languages (Stan, Pyro, Anglican) and affine type systems.

## Expected Deliverable
A research report in `docs/runtime/UNCERTAINTY-MODEL.md` and prototype in `prototypes/uncertainty/`.
"""
    },
    {
        "title": "[Research] Adaptive Execution Multi-Strategy Dispatch Cost Solver",
        "labels": ["type:research", "priority:medium", "status:research", "area:runtime", "size:research"],
        "milestone": "M13",
        "body": """## Research Question
What constraint solving heuristic optimally balances latency, financial cost ($), and memory when dynamically selecting between Local CPU, GPU, WASM, and Remote Cluster execution?

## Context & Prior Art
Investigate autotuning compilers and runtime strategy selectors.

## Expected Deliverable
A benchmark report comparing solver decision times against static dispatch.
"""
    },
    {
        "title": "[Research] Automated Intent-to-Contract SMT Synthesis",
        "labels": ["type:research", "priority:medium", "status:research", "area:verification", "size:research"],
        "milestone": "M12",
        "body": """## Research Question
Can high-level declarative `intent` goals be automatically synthesized into sound `requires`/`ensures` verification conditions for SMT solvers?

## Expected Deliverable
A prototype in `prototypes/contracts/` discharging verification conditions to Z3.
"""
    },
    {
        "title": "[RFC] Ownership & Borrowing Syntax Refinement",
        "labels": ["type:rfc", "priority:high", "status:discussion", "area:ownership", "size:medium"],
        "milestone": "M2",
        "body": """## Summary
Propose syntax and semantic refinements for explicit reference borrowing (`&T` vs `&mut T`) to complement Region XOR memory frames.

## Relevant Specification
- `docs/language/OWNERSHIP-MODEL.md`
- `RFC/0002-memory-and-borrowing.md`

## Expected Deliverable
RFC document submitted to `RFC/0006-ownership-borrowing-refinement.md`.
"""
    },
    {
        "title": "[RFC] Temporal Type Semantics & Clock Freshness Guarantees",
        "labels": ["type:rfc", "priority:medium", "status:discussion", "area:temporal", "size:medium"],
        "milestone": "M10",
        "body": """## Summary
Propose first-class temporal type annotations (`T @ fresh(100ms)`) ensuring cached distributed reads do not violate freshness SLAs.

## Relevant Specification
- `docs/runtime/TEMPORAL-MODEL.md`

## Expected Deliverable
Draft RFC in `RFC/` with typing rules and operational semantics.
"""
    },
    {
        "title": "[RFC] AI Agent Context Provenance & Audit Ledger Format",
        "labels": ["type:rfc", "priority:medium", "status:discussion", "area:ai", "size:medium"],
        "milestone": "M11",
        "body": """## Summary
Standardize the binary serialization format for AI agent execution ledgers, tracking prompt inputs, model versions, tool invocations, and cryptographic signatures.

## Relevant Specification
- `docs/ai/MODEL-PROVENANCE.md`
- `docs/ai/AI-REPRODUCIBILITY.md`
"""
    },
    {
        "title": "[RFC] Distributed Location Transparency & Remote Sagas",
        "labels": ["type:rfc", "priority:high", "status:discussion", "area:distributed", "size:medium"],
        "milestone": "M9",
        "body": """## Summary
Define the language-level semantics for content-addressed remote execution and consensus rollback coordinators.

## Relevant Specification
- `docs/distributed/DISTRIBUTED-MODEL.md`
- `docs/distributed/REMOTE-EXECUTION.md`
"""
    },
    {
        "title": "[Research] WASI preview2 Capability Bridges for System Clocks & Cryptography",
        "labels": ["type:research", "priority:medium", "status:research", "area:wasm", "size:research"],
        "milestone": "M6",
        "body": """## Research Question
What is the optimal WIT interface mapping between NOVA capability handles (`Clock`, `Random`) and WASI preview2 component imports?

## Expected Deliverable
Working prototype in `prototypes/` demonstrating zero-overhead clock calls in WASM.
"""
    },
]


def create_all_issues():
    print(f"Creating {len(ISSUES)} issues in {REPO}...")
    for idx, item in enumerate(ISSUES, 1):
        title = item["title"]
        labels = ",".join(item["labels"])
        m_key = item.get("milestone", "M0")
        milestone = MILESTONE_MAP.get(m_key, "M0 — Foundation")
        body = item["body"]

        cmd = [
            "gh", "issue", "create",
            "--repo", REPO,
            "--title", title,
            "--label", labels,
            "--milestone", milestone,
            "--body", body
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            url = res.stdout.strip()
            print(f"[{idx:02d}/{len(ISSUES):02d}] ✓ Created: {title} -> {url}")
        else:
            print(f"[{idx:02d}/{len(ISSUES):02d}] ✗ Failed: {title}\n  Error: {res.stderr.strip()}")
        time.sleep(0.5)


if __name__ == "__main__":
    create_all_issues()
