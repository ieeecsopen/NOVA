# NOVA — Verification Levels & Decidability Framework

**Status:** Production Design Reference  
**Cross-References:** [CONTRACT-MODEL.md](CONTRACT-MODEL.md), [ERROR-MODEL.md](ERROR-MODEL.md), [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md), [TYPE-SYSTEM.md](TYPE-SYSTEM.md)

---

## 1. The Verification Ladder

NOVA rejects the claim that a single verification tool can automatically prove all program correctness properties. Per Rice’s Theorem and the Halting Problem, non-trivial semantic properties are undecidable in the general case.

NOVA structures verification into a **five-tier progressive ladder**, allowing developers and security auditors to select the appropriate level of rigor for each component:

```
[Level 5] Formally Proven Property (Interactive Theorem Provers: Lean/Coq)
    ^
[Level 4] SMT-Checked Property (Automated Refinement Solving: Z3/CVC5)
    ^
[Level 3] Statically Checked Property (Type System, Rows, Exhaustiveness)
    ^
[Level 2] Testable Property (Property-Based Testing & QuickCheck Fuzzing)
    ^
[Level 1] Runtime Assertion (Checked Preconditions & Invariants at Runtime)
```

---

## 2. Comprehensive Comparison Matrix

| Level | Description | Automation | Compile Cost | Decidability | Example Application |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **L1: Runtime Assertion** | `assert(cond)` checks executed at runtime; traps on breach. | Automatic | Zero | Decidable (Dynamic) | Defensive runtime bounds checks |
| **L2: Testable Property** | QuickCheck-style randomized test generation for $\forall x.\, P(x)$. | Automatic | Low | Finite Search | Algorithmic invariant validation |
| **L3: Statically Checked** | Type system, effect row reachability, exhaustiveness (`E0101`–`E0130`). | Automatic | Very Low ($O(N)$) | Fully Decidable | Capability anti-laundering, purity |
| **L4: SMT-Checked** | Linear integer arithmetic & array bounds dispatched to Z3/CVC5. | Automatic | Moderate ($O(e^N)$) | Semi-Decidable | Array index safety, overflow proof |
| **L5: Formally Proven** | Machine-checked inductive proof certificates (e.g. Lean 4, Coq). | Manual | High | Undecidable without human guidance | Crypto primitives, microkernel isolation |

---

## 3. Decidability Boundaries and Honest Engineering

In adherence to Constitution Article V (Honest Claims):
1. **No Magic Automatic Proofs:** NOVA never claims that arbitrary user-written contracts (`requires`, `ensures`) will be fully discharged at compile time without SMT timeouts or manual proof hints.
2. **Graceful Fallback:** If an SMT solver fails to prove an L4 contract within a bounded budget (e.g., 500ms), the compiler emits a compile warning and automatically lowers the contract to an **L1 Runtime Assertion**, guaranteeing that security invariants are never silently bypassed.
3. **Soundness of L3:** The core type and capability-reachability engine (L3) is strictly decidable and linear-time, ensuring instant IDE feedback and fast compiler builds.
