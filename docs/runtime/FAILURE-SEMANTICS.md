# NOVA — Distributed Failure Semantics

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
**Cross-References:** [DISTRIBUTED-MODEL.md](../distributed/DISTRIBUTED-MODEL.md), [REMOTE-EXECUTION.md](../distributed/REMOTE-EXECUTION.md), [ERROR-MODEL.md](../language/ERROR-MODEL.md)

---

## 1. The Cardinal Rule: Never Hide Network Failure

The fundamental flaw of past distributed architectures was attempting to conceal network latency and partial failure behind synchronous abstractions. 

In NOVA:

$$\forall \text{Remote Call } f, \quad \text{ReturnType}(f) = \text{Result}[T, \text{RemoteError}]$$

A program cannot invoke a remote service or send a network message without explicitly handling network error cases.

---

## 2. Modeling the Seven Distributed Failure Classes

```nova
enum RemoteError {
    Timeout(Int),                     // Milliseconds elapsed before response
    NetworkPartition(String),         // Connection dropped or host unreachable
    NodeCrash(NodeId),                // Remote worker terminated unexpectedly
    SerializationError(String),       // Type or schema version mismatch
    RateLimited(Int),                 // Backoff required (retry after ms)
    ConsistencyConflict(String),     // Optimistic concurrency / version conflict
    LeaseExpired(UUID),               // Distributed lock / lease token invalidated
}
```

---

## 3. Resilience & Supervision Architecture

### 3.1 Idempotency Tokens
All mutating remote requests carry a unique idempotency key to protect against network re-transmissions:

```nova
fn safe_charge(dist: Distributed, key: IdempotencyKey, amount: Int) -> Result[Receipt, RemoteError] ! {Distributed} {
    dist.call_with_key[Billing]("charge", key, amount)
}
```

### 3.2 Supervisor Trees (Erlang-Inspired)
Stateful distributed actors are supervised by hierarchical supervisor trees defining explicit restart strategies:

```nova
supervisor ClusterSupervisor {
    strategy: OneForOne,
    max_restarts: 5,
    within_seconds: 60,
    children: [SearchWorker, IndexWorker, CacheWorker],
}
```
* **`OneForOne`:** If `SearchWorker` crashes due to a node failure, only `SearchWorker` is restarted on a healthy cluster node.
* **`OneForAll`:** If a critical dependency crashes, all dependent workers are restarted cleanly.
