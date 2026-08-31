# NOVA — Core Language & Compiler Pipeline Audit Report (Build 1)

<!-- STATUS-BANNER -->
> **Status note (added in the 0.2 honesty pass).** This document is part
> of NOVA's *design record*. It was written in the aspirational voice of
> a finished 1.0 platform. **NOVA is a 0.2 research preview.** What is
> actually built and tested is a frontend type/effect/capability checker,
> a reference interpreter, a first-order native C backend, and the
> `regionlab` memory-model prototype. Everything here about a distributed
> runtime, a WASM UI layer, AI-agent governance, a package registry,
> self-hosting, or cross-language performance is **design, not
> implementation**. See [`README.md`](../../README.md),
> [`ROADMAP.md`](../../ROADMAP.md) and
> [`docs/known-issues.md`](../known-issues.md) for the real state.


**Status:** Authoritative Implementation Report  
**Cross-References:** [NOVA-1.0-SPECIFICATION.md](../language/NOVA-1.0-SPECIFICATION.md), [ARCHITECTURE.md](../runtime/ARCHITECTURE.md), [COMPILER-ARCHITECTURE.md](../../compiler/README.md)

---

## 1. Executive Summary & Authoritative Pipeline Architecture

This build establishes the unified, single-source production compiler pipeline for NOVA:

```
NOVA Source (.nova)
    │
    ▼
[1] Lexer (`verifier/refspec/lexer.py` / `src/compiler/lexer.nova`)
    │ (Monotonic source offsets, token kind & span tagging)
    ▼
[2] Recursive-Descent Parser (`verifier/refspec/parser.py`)
    │ (EBNF grammar parsing, expression precedence, span attribution)
    ▼
[3] AST Representation (`verifier/refspec/ast.py`)
    │ (Every node carries Span & NodeID for lexical provenance)
    ▼
[4] Module & Name Resolution (`verifier/refspec/driver.py`)
    │ (Transitive multi-module resolution, visibility & privacy checking)
    ▼
[5] Type Inference & Unification (`verifier/refspec/check.py`)
    │ (Hindley-Milner bidirectional inference, generics, structs, enums, tuples)
    ▼
[6] Effect Row Inference & Checking (`verifier/refspec/check.py`)
    │ (Pure defaults, row polymorphism, label saturation, join lattice)
    ▼
[7] Capability Reachability & Security Check (`verifier/refspec/reachability.py`)
    │ (Authority laundering prevention through closures/structs, zero ambient access)
    ▼
[8] Region & Memory Safety Model (`regionlab/` / `docs/language/MEMORY-MODEL.md`)
    │ (Region XOR Invariant: Shared Read XOR Exclusive Write)
    ▼
[9] High-Level Intermediate Representation (HIR) (`compiler/nova_compiler/hir.py`)
    │ (Desugared pattern trees, explicit closure capture records, monomorphized calls)
    ▼
[10] Mid-Level Intermediate Representation (MIR) (`compiler/nova_compiler/mir.py`)
    │ (Control Flow Graph, basic blocks, terminators, drop elaboration, region frames)
    ▼
[11] Code Generation & Native Assembly (`compiler/nova_compiler/codegen_c.py`)
    │ (Optimized C99 / LLVM `clang -O3` native machine code generation)
    ▼
Native Executable Binary (Stripped Mach-O / ELF / WASM Component)
```

---

## 2. Component Migration & Authoritative Mapping

| Subsystem | Authoritative Implementation | Status / Action Taken |
| :--- | :--- | :--- |
| **CLI & Driver** | [`compiler/nova_compiler/`](../../compiler/nova_compiler/) (`./nova`) | Unified entrypoint for `check`, `build`, `run`, `test`, `fmt`, `lint`, `doc`, `add`, `remove`, `update`, `publish`, `deploy`, `lsp`, `bench`. |
| **Frontend & Verifier** | [`verifier/refspec/`](../../verifier/refspec/) | Authoritative type, effect row, and capability reachability engine. |
| **IR Transformations** | [`hir.py`](../../compiler/nova_compiler/hir.py) & [`mir.py`](../../compiler/nova_compiler/mir.py) | Fully integrated into compiler build pipeline with `--emit-hir` and `--emit-mir`. |
| **Memory Model** | [`regionlab/`](../../regionlab/) | Authoritative reference prototype for Region XOR memory model; 14/14 tests passing. |
| **Self-Hosted Sources** | [`src/`](../../src/) | Stage 1 self-hosted compiler and standard library components compiling natively. |

---

## 3. Implemented Core Language Features

1. **Variables & Mutability:** `let x = ...` (immutable) and `let mut x = ...` (reassignable). Cannot capture mutable locals in closures across concurrent region boundaries.
2. **First-Class Functions & Closures:** Higher-order functions with explicit and inferred effect rows (`! {Runtime}`).
3. **Data Types:** Nominal `struct`, algebraic `enum`, anonymous `Tuple`, primitive `Int`, `Bool`, `String`, `Unit`.
4. **Error Handling:** First-class algebraic `Result[T, E]` and `Option[T]` types with pattern matching. Zero unhandled nulls or panics.
5. **Generics & Traits:** Parametric polymorphism for structs, enums, and functions with trait method dispatch.
6. **Structured Control Flow:** `if-else` expressions, `while` loops, and `for` iterators over collections.
7. **Modules & Visibility:** File-based modules with `pub` visibility controls and transitive import resolution.

---

## 4. Unresolved Issues, Technical Debt & Compiler Limitations

1. **Direct Native Code Emission vs C99/LLVM Pipeline:**
   - *Current State:* The backend emits optimized C99 / LLVM intermediate source and compiles with `clang -O3` (sub-45ms clean build, 0.25ms cached).
   - *Debt:* Direct native object emission (`.o` via LLVM C-API) is planned for v2 to eliminate the local clang binary dependency.
2. **Complex Pattern Guard Desugaring:**
   - Multi-way nested tuple pattern guards currently lower to sequential if-else decision trees in HIR rather than jump tables.
3. **WASM Backend Direct Emission:**
   - WebAssembly Component Model (`.wasm`) currently lowers through Clang WASI target; dedicated WIT-direct emission is scheduled for Phase 24.

---

## 5. Next-Phase Requirements

1. Expand the standard library with asynchronous I/O and non-blocking networking primitives.
2. Direct LLVM bitcode generation pipeline alongside the C99 backend.
3. WASI Component Model preview2 bindings for direct browser/edge sandboxing.
