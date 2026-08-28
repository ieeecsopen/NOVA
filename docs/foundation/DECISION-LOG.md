# NOVA — Architectural Decision Log (ADL)

**Status:** Official Foundation Reference  
**Cross-References:** [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md), [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md), [ARCHITECTURAL-GOALS.md](ARCHITECTURAL-GOALS.md)

---

## Decision Record Summary

| ADR # | Decision Title | Status | Rationale | Alternatives Rejected |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-001** | **Capability-Effect Unification** | **Accepted** | Unifies dynamic authority tokens with static effect typing rows into one algebraic foundation. | Ambient global functions, dynamic permissions checks. |
| **ADR-002** | **Region XOR Memory Model** | **Accepted** | Eliminates data races and memory corruption without garbage collection or complex named lifetimes (`'a`). | Tracing GC, pure ARC, full Rust-style borrow checker. |
| **ADR-003** | **Zero Ambient Authority** | **Accepted** | Statically prevents supply-chain attacks by requiring explicit capability passing for all I/O and network operations. | Ambient environment access (standard in Node/Python/Go). |
| **ADR-004** | **Structured Concurrency as Default** | **Accepted** | Guarantees all concurrent branches join before scope exit, eliminating orphan threads. | Unscoped `go func()`, raw thread handles, async function coloring. |
| **ADR-005** | **Honest Claims Classification** | **Accepted** | Mandates 5 explicit verification tiers to prohibit overclaiming mathematical guarantees. | Binary "verified" vs "unverified" labels. |
