# NOVA — Resource-Aware Programming Model

**Status:** Production Design Reference  
**Cross-References:** [COST-MODEL.md](COST-MODEL.md), [RESOURCE-ANALYSIS.md](RESOURCE-ANALYSIS.md), [docs/experiments/003-graded-rows.md](docs/experiments/003-graded-rows.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

---

## 1. Resources as Quantified Capabilities

In traditional software, operational resources (memory, dollars, tokens, time, energy) are completely invisible to the type system. A function that consumes \$1,000 of LLM inference or allocates 16GB of GPU VRAM has the exact same type signature as one that computes in 10 microseconds.

NOVA unifies resource accounting with capability-typed effects:

$$\text{Resource Requirement} \equiv \text{Quantified / Graded Capability}$$

A function does not just declare *that* it accesses a capability (`! {AI}`); it declares its **resource envelope** (`! {AI[tokens < 5000, cost < $0.02]}`).

---

## 2. Resource Taxonomy

NOVA defines first-class tracking for physical, cloud, and operational resource dimensions:

| Resource Dimension | Unit of Measurement | Tracking Mechanism | Hard Constraint Strategy |
| :--- | :--- | :--- | :--- |
| **Memory** | Bytes (`KB`, `MB`, `GB`) | Region frame allocation size | Region abort on overflow |
| **CPU Time** | Milliseconds (`ms`, `s`) | Thread execution quantum | Preemptive task yield |
| **GPU / NPU VRAM** | VRAM Bytes / FLOPs | Tensor buffer allocation handle | Device memory trap |
| **Network Bandwidth**| Bytes transferred / Packets | Socket capability meter | Rate limiting / Throttling |
| **Storage I/O** | Read/Write IOPS, Bytes | Storage capability counter | Disk quota enforcement |
| **Energy** | Joules / Milliwatt-hours | Battery / Hardware energy meter | Low-power task deferral |
| **Financial Cost** | Dollars / Cents (`$0.05`) | Ledger account capability | Immediate transaction abort |
| **AI Tokens** | Prompt / Completion Tokens | Tokenizer parser counter | Context window truncation |
| **API Rate Quota** | Calls per minute / Tokens | Token bucket algorithm | `Result::Err(RateLimited)` |

---

## 3. The Four Assurance Levels

In strict adherence to Constitution Article V (Honest Claims), the compiler distinguishes four explicit assurance tiers:

```
[Level 4] GUARANTEED  ──> SMT/Inductive proof: Cannot exceed budget under ANY input.
    ^
[Level 3] BOUNDED     ──> Static semiring algebra: Worst-case execution bound.
    ^
[Level 2] TRACKED     ──> Runtime metering: Monitored live; traps/yields on breach.
    ^
[Level 1] ESTIMATED   ──> Profile/Heuristic: Informational hint; no runtime trap.
```

| Level | Formal Semantics | Compile Invariant | Fallback / Enforcement |
| :--- | :--- | :--- | :--- |
| **1. Estimated** | Statistical average based on profiler benchmarks | Non-binding metadata | Logging / Telemetry only |
| **2. Tracked** | Dynamic hardware/runtime token consumption | Checked at loop/call boundaries | Traps with `ResourceExhausted` |
| **3. Bounded** | Formal closed-form upper bound $O(f(N))$ | Static type verification | Rejects code if bound > limit |
| **4. Guaranteed** | Machine-checked proof of finite bound | Discharged via Z3 / Lean | Compile error on unproven paths |

The compiler **never** upgrades an `Estimated` or `Tracked` metric to a `Guaranteed` claim.
