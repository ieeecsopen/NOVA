# NOVA — Language-Native Observability

**Status:** Production Design Reference  
**Cross-References:** [RUNTIME-DIAGNOSTICS.md](RUNTIME-DIAGNOSTICS.md), [TRACING-MODEL.md](TRACING-MODEL.md), [docs/experiments/002-rows-to-spans.md](../experiments/002-rows-to-spans.md), [EFFECT-SYSTEM.md](../language/EFFECT-SYSTEM.md), [CAPABILITY-MODEL.md](../language/CAPABILITY-MODEL.md)

---

## 1. The Death of Manual Logging Drift

In conventional languages, observability is an afterthought added via scattered `logger.info(...)` statements and decorator annotations (`@trace`, `@metric`). This creates two major pathologies:
1. **Telemetry Drift:** Code evolves, but log messages and metric names remain unchanged, misinforming on-call engineers.
2. **Missing Spans:** Developers forget to instrument new endpoints, creating blind spots in production traces.

NOVA replaces manual telemetry with **Language-Native Semantic Observability**:

> **Effect Rows and Capability Invocations automatically derive drift-free OpenTelemetry spans at compile time with ZERO manual annotations.**

```
                               +-----------------------------+
                               | fn fetch_user(id) ! {Database} |
                               +--------------+--------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
           [Static Type Check]                              [Language Runtime]
      Guarantees only Database used               Emits Span: `service.user.fetch`
                                                  Logs: `Database.query` (latency: 1.2ms)
```

---

## 2. Why Annotations Are Insufficient

| Telemetry Approach | Maintenance Burden | Drift Risk | Coverage |
| :--- | :--- | :--- | :--- |
| **Manual Logging (`log.info`)** | High (Hand-written strings) | **Extreme** (Outdated within months) | Fragmented / Inconsistent |
| **Decorator Annotations (`@trace`)**| Medium (Must annotate every fn) | **High** (Developer forgets new fns) | Partial / Opt-in |
| **NOVA Effect-Derived Spans** | **Zero (Compiler-synthesized)** | **Zero (Statically linked to AST)** | **100% Exhaustive & Sound** |

---

## 3. Capability-Driven Auditing

Because every I/O, database, network, and AI operation requires an explicit capability handle, the runtime automatically generates an unforgeable, cryptographically signed audit trail:

```nova
fn handle_checkout(db: Database, vault: Secret, net: Network, cart: Cart) -> Result[Receipt, Error] ! {Database, Secret, Network} {
    // Every call below emits structured telemetry automatically:
    let payment_key = vault.unwrap_key("stripe_token");  // Audited: Secret.unwrap_key
    let charge = net.post("/v1/charges", payment_key);     // Audited: Network.post (lat: 84ms)
    db.execute("INSERT INTO orders ...", charge.id);       // Audited: Database.execute (lat: 2ms)
    Result::Ok(Receipt::new(charge.id))
}
```

* Zero manual log formatting.
* Automatic propagation of distributed trace IDs (`W3C TraceContext`).
* Complete auditability for SOC2, HIPAA, and financial compliance out of the box.
