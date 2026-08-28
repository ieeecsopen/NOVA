# NOVA — Proof Model & Claim Classification

**Status:** Production Design Reference  
**Cross-References:** [INTENT-MODEL.md](INTENT-MODEL.md), [VERIFICATION-ARCHITECTURE.md](VERIFICATION-ARCHITECTURE.md), [VERIFICATION-LEVELS.md](VERIFICATION-LEVELS.md), [CONSTITUTION.md](CONSTITUTION.md)

---

## 1. The Strict Classification of Claims

In strict adherence to **Constitution Article V (Honest Claims)**, every guarantee in a NOVA program carries an explicit machine-verifiable classification:

```
[Level 5] FORMALLY PROVEN    ──> Machine-checked inductive/SMT proof across ALL inputs.
    ^
[Level 4] STATICALLY CHECKED  ──> Compiler-verified type/effect/capability reachability pass.
    ^
[Level 3] PARTIALLY VERIFIED  ──> Passing property-based tests & fuzzing over finite test space.
    ^
[Level 2] RUNTIME-ENFORCED    ──> Checked dynamically; traps/returns Err on failure.
    ^
[Level 1] INFORMATIONAL       ──> Human comment or documentation hint (zero enforcement).
```

---

## 2. Formal Classification Matrix

| Classification | Verification Method | Failure Mode | Permitted Language Claims |
| :--- | :--- | :--- | :--- |
| **`Informational`** | None | Silent | "Intended to behave as X" |
| **`Runtime-Enforced`** | Inline assertion checks | `Result::Err(ContractBreach)` or panic | "Enforced at runtime" |
| **`Partially Verified`** | 10,000+ randomized fuzz tests | Fuzz failure in CI | "Tested across finite cases" |
| **`Statically Checked`** | AST reachability / Type inference | Compile error (`E0105`) | "Statically checked" |
| **`Formally Proven`** | Z3 SMT discharge / Lean 4 kernel | Rejected proof step | "Formally proven for all inputs" |

---

## 3. The Anti-Overclaim Rule

The NOVA compiler strictly enforces:

$$\text{Claim}(\text{Property } P) \le \text{VerificationTier}(P)$$

If a developer annotates a function with `guarantee non_negative_balance` but the SMT solver cannot synthesize a complete proof, the compiler **prohibits tagging the binary with `Formally Proven`**. Instead, the compiler inserts a runtime check and tags the guarantee as `Runtime-Enforced`.
