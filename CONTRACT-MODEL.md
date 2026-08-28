# NOVA — Contract & Specification Model

**Status:** Production Design Reference  
**Cross-References:** [ERROR-MODEL.md](ERROR-MODEL.md), [VERIFICATION-LEVELS.md](VERIFICATION-LEVELS.md), [TYPE-SYSTEM.md](TYPE-SYSTEM.md), [SAFETY-GUARANTEES.md](SAFETY-GUARANTEES.md)

---

## 1. Design by Contract (DbC) in NOVA

NOVA integrates **Design by Contract** directly into function signatures and type definitions. Contracts define binding behavioral specifications that can be verified at multiple levels (runtime check, fuzzing, SMT solving, or formal proof).

---

## 2. Contract Clauses and Keywords

NOVA supports six formal contract primitives:

| Keyword | Target | Scope & Timing | Responsibility / Blame |
| :--- | :--- | :--- | :--- |
| **`requires`** | Precondition | Evaluated at function entry | **Caller's Obligation:** If breached, blame caller. |
| **`ensures`** | Postcondition | Evaluated at function return | **Callee's Guarantee:** If breached, blame function body. |
| **`invariant`** | Struct / Loop | Checked across method calls / loop steps | **State Owner:** Invariant holds before and after public mutations. |
| **`assert`** | Statement | Point-in-time evaluation | **Local Context:** Statically proved or dynamically trapped. |
| **`guarantee`** | Module / Interface | Boundary security invariant | **Subsystem:** Invariant enforced across module boundaries. |
| **`property`** | Test / Theorem | Quantified specification ($\forall x$) | **Verification Engine:** Property-based testing or SMT solver. |

---

## 3. Strict Purity Rule for Contracts

A critical invariant of NOVA’s contract system is:

$$\forall c \in \text{Contracts}(f), \quad \text{EffectRow}(c) = \emptyset \quad (\text{Strictly Pure})$$

Contract expressions:
1. **Cannot perform side effects:** Cannot access `Network`, `Filesystem`, `Database`, or mutate program state.
2. **Cannot allocate unbounded memory:** Must be deterministic, terminating pure boolean expressions.
3. **Cannot observe or alter capabilities:** Cannot launder or consume capability values.

---

## 4. Contract Example: Bank Account Domain

```nova
struct Account {
    balance: Int,
    is_active: Bool,
}
invariant balance >= 0;

fn withdraw(account: &mut Account, amount: Int) -> Result<Int, Error>
    requires amount > 0
    requires account.is_active
    ensures account.balance >= 0
{
    if account.balance < amount {
        return Err(Error::InsufficientFunds);
    }
    account.balance = account.balance - amount;
    Ok(account.balance)
}
```

### Blame Assignment
* If a caller invokes `withdraw(acc, -50)`: **Caller is blamed** for breaching `requires amount > 0`.
* If `withdraw` erroneously decrements balance below zero without error: **Callee is blamed** for breaching `ensures account.balance >= 0`.
