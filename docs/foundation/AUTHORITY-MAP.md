# NOVA — Authoritative Implementation Map & Consolidation Strategy

**Status:** Authoritative Architectural Mapping  
**Cross-References:** [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md), [COMPILER-AUDIT-REPORT.md](COMPILER-AUDIT-REPORT.md), [ARCHITECTURE.md](../runtime/ARCHITECTURE.md)

---

## 1. Subsystem Authority Classification

This document formally establishes which codebase is authoritative for every major subsystem to prevent contributor confusion and eliminate duplicate parallel implementations.

| Subsystem | Authoritative Codebase | Secondary / Migration Status | Purpose & Role |
| :--- | :--- | :--- | :--- |
| **CLI & Driver** | [`compiler/nova_compiler/cli.py`](../../compiler/nova_compiler/cli.py) | Authoritative (v1.0) | Single entrypoint for `nova new`, `dev`, `check`, `build`, `run`, `test`, `fmt`, `lint`, `doc`, `add`, `remove`, `update`, `publish`, `deploy`, `lsp`, `bench`. |
| **Frontend & Verifier** | [`verifier/refspec/`](../../verifier/refspec/) | Authoritative (v1.0) | Reference Hindley-Milner type inference, row-typed effect lattice, and transitive capability reachability analysis. |
| **Intermediate Representations** | [`compiler/nova_compiler/hir.py`](../../compiler/nova_compiler/hir.py) & [`mir.py`](../../compiler/nova_compiler/mir.py) | Authoritative (v1.0) | High-Level IR (pattern tree desugaring) and Mid-Level IR (CFG basic blocks, drop elaboration). |
| **Backend Codegen** | [`compiler/nova_compiler/codegen_c.py`](../../compiler/nova_compiler/codegen_c.py) | Authoritative (v1.0) | Optimized C99 / LLVM `clang -O3` native binary and WebAssembly Component Model emission. |
| **Memory Model** | [`regionlab/`](../../regionlab/) | Authoritative Prototype | Operational semantics & test harness for Region XOR (Shared Read XOR Exclusive Write) memory safety. |
| **Self-Hosted Sources** | [`src/`](../../src/) | Stage 1 Migration Target | Self-hosted compiler and standard library written in pure NOVA (`.nova`), compiling via Stage 0. |
| **Standard Library** | [`std/`](../../std/) | Authoritative Prelude | Pure standard prelude (`prelude.nova`, `option.nova`, `result.nova`, `list.nova`). |
| **Language Server** | [`compiler/nova_compiler/lsp_server.py`](../../compiler/nova_compiler/lsp_server.py) | Authoritative (v1.0) | JSON-RPC 2.0 LSP server. Legacy [`lsp/server.py`](../../lsp/server.py) is marked for deprecation. |

---

## 2. Consolidation & Deprecation Action Items

1. **LSP Consolidation:** All IDE extensions must invoke `nova lsp` which routes to [`compiler/nova_compiler/lsp_server.py`](../../compiler/nova_compiler/lsp_server.py).
2. **Self-Hosting Bootstrap Chain:** [`src/compiler/`](../../src/compiler/) mirrors the AST and type checking logic in pure NOVA, verified against [`verifier/refspec/`](../../verifier/refspec/) test vectors.
3. **Memory Model Integration:** The RegionLab checker rules (`regionlab/checker.py`) serve as the formal specification for lowering lifetime scopes into MIR drop flags.
