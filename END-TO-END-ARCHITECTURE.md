# NOVA — End-to-End Application Architecture

**Status:** Production Design Reference  
**Cross-References:** [PLATFORM-MODEL.md](PLATFORM-MODEL.md), [UNIFIED-APPLICATION-SPEC.md](UNIFIED-APPLICATION-SPEC.md), [OBSERVABILITY.md](OBSERVABILITY.md), [SAFETY-GUARANTEES.md](SAFETY-GUARANTEES.md)

---

## 1. The Complete Data Lifecycle

Here is the exact journey of a request through a unified NOVA application:

```
[1] User clicks "Register for Event" in WASM Browser Client
         │
         ▼
[2] Client-Side Contract Validation (`enrolled < capacity` checked in UI)
         │
         ▼
[3] Type-Safe Binary RPC Serialization over WebSocket/HTTP
         │
         ▼
[4] Gateway Authentication produces unforgeable `caller: AuthToken`
         │
         ▼
[5] Backend Service executes `register_student()` ! {Database, Clock}
         │ (Requires verified `caller` capability and `db: Database`)
         ▼
[6] Linear ACID Transaction atomically updates enrollment count
         │
         ▼
[7] AI Assistant generates confirmation summary within `< 500 token` budget
         │
         ▼
[8] Effect rows automatically emit OpenTelemetry trace spans and metrics
```

---

## 2. Security and Correctness Across the Lifecycle

* **Zero Injection Attacks:** Queries use nominal entity structures; SQL injection is mathematically impossible.
* **Zero Privilege Escalation:** Unforgeable capability tokens prevent forged administrative mutations.
* **Zero Supply-Chain Leaks:** Dependencies operate under strict capability manifests declared in `nova.toml`.
* **Zero Drift Observability:** Distributed trace IDs and span metrics are synthesized directly from AST effect rows without manual log statements.
