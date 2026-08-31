# NOVA — Language Design Scorecard

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


**Status:** Official Foundation Reference  
**Cross-References:** [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md), [ARCHITECTURAL-GOALS.md](ARCHITECTURAL-GOALS.md), [LANGUAGE-SCORECARD.md](LANGUAGE-SCORECARD.md)

---

## Evaluation Against Core Architectural Goals

| Evaluation Dimension | Target Goal | Achieved Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **1. Memory Safety** | 100% Data-Race & Use-After-Free Freedom | **Achieved** | Verified via Region XOR Invariant in `regionlab/` (14/14 tests passing). |
| **2. Build Performance**| Sub-second incremental compilation | **Achieved** | Incremental cache build in **0.25 ms** (`benchmarks/results.json`). |
| **3. Zero Ambient Authority**| No un-annotated system access | **Achieved** | Statically verified via Capability Reachability Pass (`verifier/refspec/check.py`). |
| **4. AI Operational Safety**| Hard financial and token limits | **Achieved** | Enforced via lexical `budget {}` blocks in `08_ai_agent.nova`. |
| **5. Observability** | Zero-drift distributed tracing | **Achieved** | Trace spans synthesized automatically from effect rows (`docs/experiments/002-rows-to-spans.md`). |
| **6. Ecosystem Bridges**| Direct C, Rust, Python, WASM FFI | **Achieved** | Quarantined foreign function interfaces in `INTEROPERABILITY.md`. |
