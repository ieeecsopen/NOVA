# NOVA — Release Process & Release Train

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


**Status:** Official Policy Reference  
**Cross-References:** [NOVA-1.0-SPECIFICATION.md](../language/NOVA-1.0-SPECIFICATION.md), [STABILITY-POLICY.md](STABILITY-POLICY.md), [SECURITY-PROCESS.md](SECURITY-PROCESS.md)

---

## 1. The 6-Week Release Train

NOVA follows a predictable six-week release cadence across three channels:

```
[Nightly Channel] ──(6 Weeks Testing)──> [Beta Channel] ──(6 Weeks Stabilization)──> [Stable Channel (1.x)]
   (Daily builds)                           (Feature Freeze)                                (Production Ready)
```

1. **Nightly Channel:** Built daily from `main`. Incorporates active experimental RFC work.
2. **Beta Channel:** Released every 6 weeks with a feature freeze. Undergoes exhaustive regression testing across all 12 real-world reference applications.
3. **Stable Channel:** Released every 6 weeks for production usage with guaranteed backward compatibility.

---

## 2. Release Gate Invariants

A release candidate cannot be promoted to **Stable** unless it passes all required quality gates:

- [x] **Zero Regressions:** 100% pass rate across the conformance test suite (`tests/`).
- [x] **Documentation Link Verification:** Zero broken internal links (`tools/check-links.py`).
- [x] **Benchmark Baseline:** No performance regression > 2% on the Challenge Benchmark Suite (`benchmarks/challenge_suite.py`).
- [x] **Cryptographic Signing:** Release binaries signed with official release keys and SLSA Level 4 provenance attestations.
- [x] **Diverse Double-Compiling:** Self-hosted bootstrap fixed-point verified.
