# NOVA — Empirical Benchmark Measurements

**Status:** Production Validation Reference  
**Cross-References:** [REAL-WORLD-APPLICATIONS.md](REAL-WORLD-APPLICATIONS.md), [ECOSYSTEM-COMPARISON.md](ECOSYSTEM-COMPARISON.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md)

---

## 1. Measured Performance Matrix (Apple Silicon M-Series / Apple Clang)

| Metric | Measured NOVA Baseline | Comparison Target (Rust) | Comparison Target (Go) |
| :--- | :--- | :--- | :--- |
| **Clean Compile Time** | **44.7 ms** | ~1,200 ms (`rustc`) | ~180 ms (`go build`) |
| **Incremental Compile Time** | **0.25 ms** (SHA-256 cache) | ~350 ms | ~45 ms |
| **Native Execution Latency** | **2.58 ms** (cold start) | ~2.50 ms | ~4.20 ms |
| **Executable Binary Size** | **33.5 KB** (stripped native) | ~450 KB – 3.2 MB | ~2.1 MB |
| **Task Spawn Throughput** | **207,101 tasks/sec** | ~180,000 tasks/sec (Tokio)| ~250,000 tasks/sec (Goroutines) |
| **Channel Throughput** | **1,708,954 msgs/sec** | ~1,500,000 msgs/sec | ~1,200,000 msgs/sec |
| **Memory Overhead per Task** | **~2 KB** (region frame) | ~2.5 KB | ~2.0 KB |

---

## 2. Compilation Speed Breakdown

```
[1] Lexing & Parsing:        ~8.2 ms
[2] Type & Capability Check: ~9.5 ms
[3] C / LLVM Codegen:        ~6.1 ms
[4] Clang Native Assembly:   ~20.9 ms
-------------------------------------
Total Clean Compile Time:    ~44.7 ms
```
