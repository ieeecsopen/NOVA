# NOVA — Multi-Stage Verification Architecture

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


**Status:** Production Design Reference  
**Cross-References:** [INTENT-MODEL.md](INTENT-MODEL.md), [PROOF-MODEL.md](PROOF-MODEL.md), [VERIFICATION-LEVELS.md](../language/VERIFICATION-LEVELS.md), [CONTRACT-MODEL.md](../language/CONTRACT-MODEL.md)

---

## 1. The 8-Stage Verification Pipeline

NOVA integrates formal verification directly into the continuous compilation lifecycle. A program progresses through eight rigorous verification gates:

```
[1] Type Checking           ──> Hindley-Milner + nominal structs + traits
         │
         ▼
[2] Effect Checking         ──> Row typing + graded effect row unification
         │
         ▼
[3] Capability Checking     ──> Object capability reachability analysis (XOR property)
         │
         ▼
[4] Resource Analysis       ──> Cost semiring solving (tokens, cost, memory, latency)
         │
         ▼
[5] Property-Based Testing  ──> Automated generation of randomized edge-case inputs
         │
         ▼
[6] Coverage-Guided Fuzzing ──> Mutation-based invariant stress testing (LibFuzzer)
         │
         ▼
[7] SMT / Model Checking    ──> Z3 / CVC5 automated arithmetic & contract proofs
         │
         ▼
[8] Formal Proof Export     ──> Lean 4 / Coq machine-checked deductive proof certificates
```

---

## 2. Incremental Proof Caching

Formal verification can be computationally intensive. NOVA employs **Proof Artifact Caching**:
* Each function's AST, type signatures, contracts, and lemma dependencies are hashed into a cryptographic proof key (`.nova_cache/proofs/<sha256>.cert`).
* If a function and its dependencies are unchanged, the compiler re-uses the cached proof certificate in **< 0.1 ms**.

---

## 3. Actionable Counterexample Generation

When an SMT solver or property check discovers an invariant violation, the compiler produces concrete counterexamples:

```text
error[V0301]: contract 'non_negative_balance' violated in function 'withdraw'
  --> src/banking.nova:42:5
   |
42 |     acc.balance = acc.balance - amount;
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   = counterexample found by SMT solver:
       initial acc.balance = 50
       amount              = 100
       resulting balance   = -50  (violates invariant `balance >= 0`)
   = help: add precondition `requires amount <= acc.balance`
```
