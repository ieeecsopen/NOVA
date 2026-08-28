# NOVA — Cost Model & Resource Semirings

**Status:** Production Design Reference  
**Cross-References:** [RESOURCE-MODEL.md](RESOURCE-MODEL.md), [RESOURCE-ANALYSIS.md](RESOURCE-ANALYSIS.md), [docs/experiments/003-graded-rows.md](docs/experiments/003-graded-rows.md), [TYPE-SYSTEM.md](TYPE-SYSTEM.md)

---

## 1. The Algebraic Semiring of Computation Cost

NOVA formalizes cost propagation across program ASTs using a **Resource Semiring** $(\mathcal{R}, \oplus, \otimes, \mathbf{0}, \mathbf{1})$:

* **$\mathcal{R}$:** Vector of quantified resources $\langle \text{Memory}, \text{Latency}, \text{Tokens}, \text{Cost} \rangle$.
* **Sequential Composition ($\otimes$):** Addition of sequential costs:
$$\text{Cost}(e_1 ; e_2) = \text{Cost}(e_1) \otimes \text{Cost}(e_2) = c_1 + c_2$$
* **Branching Join ($\oplus$):** Maximum worst-case bound across conditional paths:
$$\text{Cost}(\text{if } b \text{ then } e_1 \text{ else } e_2) = \text{Cost}(e_1) \oplus \text{Cost}(e_2) = \max(c_1, c_2)$$
* **Identity Elements:** $\mathbf{0} = \langle 0, 0, 0, 0 \rangle$ (pure, zero-cost computation).

---

## 2. Syntactic Budget Blocks

Developers specify resource boundaries using lexical `budget` blocks:

```nova
fn run_ai_agent(ai: AI, prompt: String) -> Result[String, ResourceError] ! {AI} {
    budget {
        tokens < 10000,
        cost < 0.05,      // $0.05 max expenditure
        latency < 30000,  // 30 seconds max timeout
    } in {
        let embedding = ai.embed(prompt)?;
        let response = ai.complete(embedding)?;
        Ok(response)
    }
}
```

### Compile-Time vs. Runtime Enforcement
1. If the compiler can prove statically that `embed + complete < 10000 tokens`, the budget is verified at compile time with zero runtime overhead.
2. If dynamic token generation cannot be statically bounded, the compiler inserts a **linear resource token counter** that halts execution gracefully if the budget is reached.

---

## 3. Propagation Across Boundaries

Resource costs propagate transitively across all architectural boundaries:

```
[Agent Request: Budget $0.05]
       │
       ▼
[Service Gateway: Deducts $0.001 routing cost]
       │
       ▼
[AI Model Call: Consumes 2,500 tokens = $0.005]
       │
       ▼
[Database Log: Consumes 1 IOPS = $0.0001]
       │
       ▼
[Remaining Envelope: $0.0439 returned to caller]
```

* **Function Calls:** Callee's graded row is unified into caller's effect row.
* **Remote Calls:** Budget headers are serialized into RPC network envelopes.
* **Dependencies:** External packages must adhere to the consumer's declared budget ceiling (`package-manager/README.md`).
