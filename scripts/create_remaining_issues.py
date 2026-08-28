#!/usr/bin/env python3
"""Create remaining Epics and Issues with corrected labels."""
import subprocess
import time

REPO = "ieeecsopen/NOVA"

# 1. Ensure status:in-progress label exists
subprocess.run(["gh", "label", "create", "status:in-progress", "--repo", REPO, "--color", "38bdf8", "--description", "Work is currently in progress", "--force"])

REMAINING_ISSUES = [
    {
        "title": "[Epic] Core Language & Syntax Stabilization",
        "labels": ["type:feature", "priority:critical", "status:in-progress", "area:language", "size:large"],
        "milestone": "M1 — Core Language",
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
        "milestone": "M2 — Type System & Safety",
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
        "milestone": "M2 — Type System & Safety",
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
        "milestone": "M3 — Compiler & IR",
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
        "milestone": "M3 — Compiler & IR",
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
        "title": "[Epic] 4-Stage Self-Hosting Bootstrap Pipeline",
        "labels": ["type:feature", "priority:medium", "status:in-progress", "area:self-hosting", "size:large"],
        "milestone": "M14 — Self-Hosting",
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
        "milestone": "M5 — Toolchain",
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
    {
        "title": "[GFI] Improve span underline pointer formatting in error diagnostics",
        "labels": ["type:refactor", "priority:low", "status:good-first-issue", "area:compiler", "size:small"],
        "milestone": "M1 — Core Language",
        "body": """## Summary
Refine multiline ASCII error diagnostic rendering in `verifier/refspec/diagnostics.py` to ensure consistent column alignment when source lines contain tab characters or unicode glyphs.

## Implementation File
- `verifier/refspec/diagnostics.py`

## Acceptance Criteria
- [ ] Multiline error pointers accurately align with token boundaries.
- [ ] Conformance tests in `tests/` pass.
"""
    },
]

for idx, item in enumerate(REMAINING_ISSUES, 1):
    title = item["title"]
    labels = ",".join(item["labels"])
    milestone = item["milestone"]
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
        print(f"[{idx}/8] ✓ Created: {title} -> {res.stdout.strip()}")
    else:
        print(f"[{idx}/8] ✗ Failed: {title}\n  Error: {res.stderr.strip()}")
    time.sleep(0.5)
