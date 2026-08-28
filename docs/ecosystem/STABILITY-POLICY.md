# NOVA — Language Stability & Compatibility Policy

**Status:** Official Policy Reference  
**Cross-References:** [NOVA-1.0-SPECIFICATION.md](../language/NOVA-1.0-SPECIFICATION.md), [RELEASE-PROCESS.md](RELEASE-PROCESS.md), [GOVERNANCE.md](../../GOVERNANCE.md)

---

## 1. The 1.0 Backward Compatibility Guarantee

NOVA adheres strictly to **Semantic Versioning 2.0.0 (SemVer)**:

> **A valid, compiling NOVA 1.0 program will compile without errors and execute with identical semantics across every minor (1.x.y) release.**

We will never break user code casually. Breaking changes are prohibited outside of explicit major version boundaries (e.g. NOVA 2.0).

---

## 2. Feature Stability Tiers

To allow rapid innovation without compromising core stability, language features are partitioned into three explicit tiers:

| Stability Tier | Guarantee Level | Evolution Policy | Example Features |
| :--- | :--- | :--- | :--- |
| **Tier 1: Stable (1.0 Core)** | **Guaranteed Backward Compatible** | No breaking changes in 1.x | EBNF Grammar, Type System, Region XOR, Capability Model, CLI Toolchain |
| **Tier 2: Beta** | **High Stability** | Minor syntax tweaks with deprecation warnings | Graded Effect Rows (`grading.py`), SMT Contract Verification |
| **Tier 3: Experimental** | **Research Prototype** | Opt-in via feature flag (`--enable-experimental`) | Adaptive Multi-Strategy Execution (`ADAPTIVE-EXECUTION.md`) |

---

## 3. Deprecation Lifecycle

If a standard library function or syntax construct is superseded:
1. **Phase 1 (Deprecation Warning):** The compiler emits a lint warning (`warning[W0201]`) with automated migration suggestions across at least two minor releases (e.g. 1.2 through 1.4).
2. **Phase 2 (Automated Migration):** Running `nova fix` automatically rewrites the deprecated construct to the modern replacement.
3. **Phase 3 (Removal):** The construct is only removed at the next major version boundary (NOVA 2.0).
