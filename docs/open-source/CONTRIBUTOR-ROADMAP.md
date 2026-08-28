# NOVA — Open-Source Contributor Roadmap & Milestones

**Status:** Authoritative Milestone Reference  
**Cross-References:** [GOVERNANCE.md](../../GOVERNANCE.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [ROADMAP.md](../../ROADMAP.md)

---

## 1. Release Milestones & Dependency Ladder

The NOVA engineering lifecycle is organized into sixteen strictly ordered milestones:

```
[M0 Foundation] ──> [M1 Core Language] ──> [M2 Type System & Safety] ──> [M3 Compiler]
                                                                               │
                                                                               ▼
[M7 Concurrency] <── [M6 WASM] <── [M5 Toolchain] <── [M4 Runtime Architecture]
       │
       ▼
[M8 Full-Stack] ──> [M9 Distributed] ──> [M10 Resources/Time] ──> [M11 AI Runtime]
                                                                        │
                                                                        ▼
[M15 Production 1.0] <── [M14 Self-Hosting] <── [M13 Adaptive] <── [M12 Verification]
```

---

## 2. Milestone Descriptions & Deliverables

| Milestone | Title | Focus Area & Key Technical Deliverables |
| :--- | :--- | :--- |
| **M0** | **Foundation** | Repository architecture, governance, license, RFC process, CI matrix. |
| **M1** | **Core Language** | Grammar stabilization, AST node span attribution, parser precedence. |
| **M2** | **Type System & Safety** | Hindley-Milner inference, row-typed effect join lattice, Region XOR invariant. |
| **M3** | **Compiler & IR** | AST $\to$ HIR $\to$ MIR lowering, basic block CFG constructor, drop elaboration. |
| **M4** | **Runtime Engine** | Memory frames, Region XOR allocator, error propagation, OpenTelemetry spans. |
| **M5** | **Toolchain & DX** | `nova` CLI (`new`, `dev`, `check`, `build`, `run`, `test`, `fmt`, `lint`, `doc`). |
| **M6** | **WASM & Portability** | WebAssembly Component Model backend, WASI preview2 capability bindings. |
| **M7** | **Concurrency** | Chase-Lev work-stealing scheduler, structured `parallel`/`race`, channels. |
| **M8** | **Full-Stack Platform** | Shared nominal entities, reactive WASM VNode UI, type-safe RPC gateways. |
| **M9** | **Distributed Systems** | Saga coordinators, consensus replicas, explicit network failure semantics. |
| **M10** | **Resources & Time** | 4-tier resource semirings, clock freshness, epistemic uncertainty modeling. |
| **M11** | **AI Governance** | Sandboxed autonomous agents, zero implicit authority, financial budget ceilings. |
| **M12** | **Verification Engine** | Design-by-Contract (`requires`/`ensures`), SMT solver integration, Lean 4 proofs. |
| **M13** | **Adaptive Execution** | Research-grade multi-strategy dispatch (CPU, GPU, WASM, Remote Cluster). |
| **M14** | **Self-Hosting** | 4-stage bootstrap ladder (Stage 0 Host $\to$ Stage 3 Bit-Identical Binary). |
| **M15** | **Production 1.0** | SemVer 2.0.0 stability guarantees, security audit sign-off, public challenge suite. |
