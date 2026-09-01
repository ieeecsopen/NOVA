# NOVA — Static Resource Analysis & Governance

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
**Cross-References:** [RESOURCE-MODEL.md](RESOURCE-MODEL.md), [COST-MODEL.md](COST-MODEL.md), [docs/experiments/003-graded-rows.md](../experiments/003-graded-rows.md), [ERROR-MODEL.md](../language/ERROR-MODEL.md)

---

## 1. Static Resource Analysis Engine

The NOVA compiler analyzes resource demands during the **Graded Row Pass** (`verifier/refspec/grading.py`):

```
AST Body
   │
   ▼
Cost Equation Generation (Recurrence relations & basic block cost)
   │
   ▼
Semiring Solver (Evaluates sequential ⊗ and branch ⊕ max joins)
   │
   ▼
Static Closed-Form Bound or Dynamic Meter Injection
```

### 1.1 First-Order Functions (Closed-Form Bounds)
For linear and non-recursive code, the analysis computes exact closed-form consumption:

$$\text{Cost}(f) = \sum_{s \in \text{stmts}} \text{Cost}(s)$$

### 1.2 Loops and Recursion (Bounded vs. Tracked)
* If loop bounds are statically fixed (`for x in 0..10`), the compiler multiplies the body cost by 10.
* If a loop or recursion depends on unbounded runtime input, the compiler emits a `Tracked` annotation and inserts an inline capability meter.

---

## 2. Autonomous AI Agent Governance

In modern multi-agent systems, runaway agents can rapidly incur thousands of dollars in unintended API expenses or infinite loop reasoning steps.

NOVA provides native type-level guardrails for agent workflows:

```nova
struct AgentSession {
    ai: AI,
    vault: Secret,
}

fn execute_autonomous_research(agent: AgentSession, prompt: String) -> Result[Report, ResourceError] ! {AI} {
    // Hard financial and operational constraints
    budget {
        tokens < 50000,
        cost < 1.00,       // Max $1.00 USD total expenditure
        time < 120000,     // Max 2 minutes
        iterations < 10,   // Max 10 tool calls
    } in {
        let mut context = prompt;
        let mut steps = 0;
        
        while steps < 10 {
            let next_step = agent.ai.complete(context)?;
            if is_terminal(next_step) {
                return Ok(format_report(next_step));
            }
            context = append_step(context, next_step);
            steps = steps + 1;
        }
        
        Err(ResourceError::MaxIterationsReached)
    }
}
```

---

## 3. Dynamic Metering & Graceful Degradation

When a tracked resource budget approaches depletion:
1. **Soft Warning Threshold (80% Budget):** The task receives a `ResourceWarning` event, allowing it to switch to a lightweight fallback model (e.g. switching from an expensive reasoning model to a fast local model).
2. **Hard Ceiling (100% Budget):** Execution halts immediately within the structured task frame, unwinding local memory without corrupting shared state, and returning `Result::Err(ResourceError::BudgetExceeded)`.
