# NOVA — Benchmark Methodology & Statistical Rigor

**Status:** Permanent Benchmark Specification  
**Cross-References:** [CHALLENGE-BENCHMARKS.md](CHALLENGE-BENCHMARKS.md), [RAW-BENCHMARK-DATA.md](RAW-BENCHMARK-DATA.md), [CONSTITUTION.md](CONSTITUTION.md)

---

## 1. The Principle of Honest Measurement

In strict adherence to **Constitution Article V (Honest Claims)**:

> **All benchmarks must be fully reproducible, statistically sound, and publicly auditable. Unfavorable results are never concealed or omitted.**

---

## 2. Experimental Environment & Hardware Baseline

* **CPU Architecture:** Apple Silicon (ARM64 `arm64-apple-darwin25.0.0`)
* **Host Toolchain:** Apple Clang version 21.0.0 (LLVM 21.0.0 backend)
* **Optimization Flags:** `-O3 -fomit-frame-pointer -DNDEBUG`
* **Timing Mechanism:** High-resolution monotonic hardware clock (`time.perf_counter` / `clock_gettime(CLOCK_MONOTONIC)` with sub-microsecond precision).
* **Sample Count:** 10 warm-up runs followed by 30 measured evaluation runs per benchmark track.
* **Reported Metrics:** Arithmetic Mean, Median (p50), 99th Percentile (p99), and Standard Deviation ($\sigma$).

---

## 3. Threat to Validity Mitigations

1. **JIT & Warmup Effects:** All I/O and thread pools are pre-warmed prior to timer activation.
2. **Thermal Throttling:** Runs are executed with 500ms cool-down pauses between heavy batch allocations.
3. **Dead Code Elimination (DCE):** Benchmark harnesses verify final return values and assert side-effects to prevent the C/LLVM backend from optimizing away computational loops.
