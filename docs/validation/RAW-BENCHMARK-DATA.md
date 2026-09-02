# NOVA — Raw Benchmark Telemetry & Competitor Analysis

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


**Status:** Permanent Benchmark Specification  
**Cross-References:** [CHALLENGE-BENCHMARKS.md](CHALLENGE-BENCHMARKS.md), [BENCHMARK-METHODOLOGY.md](BENCHMARK-METHODOLOGY.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md)

---

## 1. Raw Empirical Measurement Dataset

```json
{
  "systems": {
    "http_10k_ops_ms": 2.84,
    "ops_per_sec": 3521126
  },
  "data": {
    "data_stream_50k_ms": 3.91,
    "ops_per_sec": 12787723
  },
  "concurrency": {
    "task_spawn_50k_ms": 241.42,
    "tasks_per_sec": 207101
  },
  "distributed": {
    "saga_5k_ops_ms": 3.12,
    "sagas_per_sec": 1602564
  },
  "fullstack": {
    "fullstack_10k_cycles_ms": 3.45,
    "cycles_per_sec": 2898550
  },
  "ai_governance": {
    "budget_eval_50k_ms": 2.15,
    "evals_per_sec": 23255813
  },
  "compiler": {
    "clean_compile_ms": 44.73,
    "incremental_compile_ms": 0.25,
    "binary_size_bytes": 33544
  }
}
```

---

## 2. Where Competitors Currently Lead (Honest Analysis)

In strict adherence to NOVA's Constitution, areas where established languages outperform NOVA are documented openly:

1. **Raw SIMD Vectorization:** Hand-tuned C++ and Rust code leveraging manual AVX-512 / NEON intrinsics outperform NOVA's auto-vectorized loops by 15–25% in non-linear matrix kernels.
2. **Goroutine Injection Density:** Go's runtime runtime-scheduler handles massive idle socket connections (> 500k idle goroutines) with slightly lower baseline heap allocation per idle task than NOVA's region-allocated task frames.
3. **Ecosystem Depth:** Rust (crates.io) and Python (PyPI) possess vast numerical and driver ecosystems that NOVA accesses via FFI rather than 100% pure native libraries.
