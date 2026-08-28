# NOVA — Runtime Diagnostics & Live Introspection

**Status:** Production Design Reference  
**Cross-References:** [OBSERVABILITY.md](OBSERVABILITY.md), [TRACING-MODEL.md](TRACING-MODEL.md), [ERROR-MODEL.md](ERROR-MODEL.md), [RESOURCE-MODEL.md](RESOURCE-MODEL.md)

---

## 1. The Six Diagnostic Questions Answered

NOVA's runtime diagnostics engine answers the six fundamental questions every developer and site reliability engineer asks during production incidents:

```
+---------------------------------------------------------------------------------------+
|                              NOVA RUNTIME DIAGNOSTIC DASHBOARD                        |
+---------------------------------------------------------------------------------------+
|  [1] WHAT IS IT DOING?     ──> Task Tree: `HTTP::Serve -> fetch_orders -> db.query`  |
|  [2] WHY IS IT SLOW?       ──> Bottleneck: `db.query` blocked on lock (45.2ms, 82%)  |
|  [3] RESOURCE CONSUMPTION  ──> Region: 4.2MB / 64MB | AI Tokens: 4,120 / 10,000       |
|  [4] CAPABILITIES USED     ──> Active Handles: `[Database, Network]`                  |
|  [5] AI INVOCATIONS        ──> `Model::Reasoning` (Prompt: 1.2k tok, Cost: $0.012)    |
|  [6] WHY DID IT FAIL?      ──> `Err(RemoteError::Timeout)` at `orders.nova:42`       |
+---------------------------------------------------------------------------------------+
```

---

## 2. Deep Dive: Diagnostic Mechanics

### 2.1 "What is this program doing?"
The runtime maintains a **live hierarchical task tree** of all active structured concurrency frames (`parallel {}`, `race {}`), showing the exact function, line, and active effect row being evaluated.

### 2.2 "Why is it slow?"
Continuous low-overhead sampling profilers generate **flame graphs partitioned by effect rows**. Developers can instantly see whether latency is caused by CPU computation, database disk I/O, network latency, or AI generation.

### 2.3 "What resource is it consuming?"
Memory is tracked at the lexical region level; CPU cycles, bandwidth, and AI tokens are metered in real time against the function's declared `budget {}` envelope.

### 2.4 "What capability did it use?"
Every capability method invocation is logged with caller identity, timestamp, and arguments.

### 2.5 "What AI call occurred?"
Emits an immutable `InferenceCertificate` capturing prompt hashes, token count, financial expenditure, and model version.

### 2.6 "Why did this operation fail?"
Errors carry **structured causal chains** (not plain string messages), linking the exact root cause across distributed service boundaries.

---

## 3. Time-Travel Debugging & Deterministic Replay

Because pure functions and capability-bounded tasks have zero ambient dependencies, recorded execution traces can be **replayed backward and forward inside the debugger** (`nova debug --replay trace.log`):

```bash
nova debug --replay incident-trace-2026-08-28.log
# (nova-dbg) step-back
# (nova-dbg) print acc.balance  # => 50
# (nova-dbg) print amount       # => 100
# (nova-dbg) where              # => banking.nova:42 (invariant breach)
```
