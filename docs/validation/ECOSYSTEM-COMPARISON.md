# NOVA — Objective Ecosystem Comparison

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


**Status:** Production Validation Reference  
**Cross-References:** [BENCHMARK-RESULTS.md](BENCHMARK-RESULTS.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md), [MEMORY-MODEL.md](../language/MEMORY-MODEL.md)

---

## 1. Multi-Language Comparison Matrix

| Evaluation Dimension | NOVA | Rust | Go | Zig | C++ | TypeScript | Python | Swift |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Runtime Speed** | **Near C/Rust** | Top | High | Top | Top | Moderate | Low | High |
| **2. Memory Model** | **Region XOR** | Borrow checker| GC (Paging) | Manual | Manual | GC (V8) | Reference Count| ARC |
| **3. Memory Safety** | **Guaranteed** | Guaranteed | Guaranteed | Unsafe | Unsafe | Safe | Safe | Safe |
| **4. Compile Time** | **Fast (~45ms)**| Slow (~1.2s)| Fast (~180ms)| Fast (~80ms)| Slow (~2.5s)| Fast (Node/TS) | None (Interp) | Moderate |
| **5. Incremental Build**| **< 1ms** | Moderate | Fast | Fast | Slow | Fast | Instant | Moderate |
| **6. Binary Size** | **~33 KB** | ~450 KB – 3MB | ~2.1 MB | ~40 KB | ~80 KB | N/A (Bundle) | N/A (Script) | ~5 MB |
| **7. Startup Latency** | **~2.5 ms** | ~2.5 ms | ~4.2 ms | ~2.2 ms | ~2.1 ms | ~45 ms | ~35 ms | ~8 ms |
| **8. Developer Effort**| **Low** | High (`'a` syntax)| Low | Moderate | High | Low | Very Low | Low |
| **9. Security Model** | **Capability-Native**| Ambient | Ambient | Ambient | Ambient | Ambient | Ambient | Ambient |
| **10. AI Governance** | **Native ($ ceiling)**| None | None | None | None | None | None | None |
| **11. Full-Stack Model**| **Unified Single Def**| Disconnected| Disconnected | None | None | TS-Only | None | Swift-Only |
