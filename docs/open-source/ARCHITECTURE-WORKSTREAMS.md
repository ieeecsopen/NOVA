# NOVA — Architecture Workstreams & Working Groups

**Status:** Official Working Group Reference  
**Cross-References:** [GOVERNANCE.md](../../GOVERNANCE.md), [AUTHORITY-MAP.md](../foundation/AUTHORITY-MAP.md)

---

## 1. Domain Working Groups (WGs)

| Working Group | Scope & Responsibilities | Key Specifications | Primary Codebase |
| :--- | :--- | :--- | :--- |
| **WG-Language** | Syntax, EBNF grammar, language evolution, RFC reviews | `docs/language/` | `verifier/refspec/ast.py`, `parser.py` |
| **WG-TypeSystem** | Hindley-Milner inference, row-typed effect join lattice | `docs/language/TYPE-SYSTEM.md` | `verifier/refspec/check.py` |
| **WG-Compiler** | HIR/MIR lowering, CFG basic blocks, C99/LLVM codegen | `compiler/README.md` | `compiler/nova_compiler/` |
| **WG-Runtime** | Task scheduler, Region XOR allocator, WASM runtime | `docs/runtime/` | `compiler/nova_compiler/codegen_c.py` |
| **WG-FullStack** | Reactive WASM VNodes, RPC services, shared entities | `docs/full-stack/` | `examples/`, `docs/full-stack/` |
| **WG-AI-Gov** | Agent sandboxing, token meters, budget ceilings | `docs/ai/` | `docs/ai/AI-SECURITY.md` |
| **WG-Tooling** | CLI (`nova`), LSP server, VS Code extension, package manager | `package-manager/` | `compiler/nova_compiler/`, `editors/` |
| **WG-Security** | Threat modeling, sandboxing audit, vulnerability triage | `docs/verification/` | `verifier/refspec/reachability.py` |

---

## 2. GitHub Project Board Workflow

Issues move across seven Kanban columns:

```
[1. BACKLOG] ──> [2. NEEDS DESIGN] ──> [3. READY] ──> [4. IN PROGRESS]
                                                             │
                                                             ▼
[7. DONE (Merged)] <── [6. CI / TESTING] <── [5. REVIEW (PR Open)]
```
