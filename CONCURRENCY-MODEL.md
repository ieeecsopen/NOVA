# NOVA — Concurrency Model Specification

**Status:** Production Design Reference  
**Cross-References:** [SCHEDULER-DESIGN.md](SCHEDULER-DESIGN.md), [MEMORY-MODEL.md](MEMORY-MODEL.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [SAFETY-GUARANTEES.md](SAFETY-GUARANTEES.md)

---

## 1. The Fragmentation Problem in Modern Concurrency

Mainstream languages fragment concurrency across mutually incompatible paradigms:
* **Threads & Locks** (Java, C++): Prone to data races, deadlocks, and high memory overhead per thread (~1MB stack).
* **Async/Await & Futures** (JavaScript, Rust, C#): Causes the "Function Color" problem where synchronous and asynchronous functions cannot cleanly compose without infecting entire call graphs.
* **Unscoped Background Tasks** (Go `go func()`, Python): Orphan tasks leak memory, continue executing after HTTP requests terminate, and swallow unhandled panics silently.

NOVA replaces this fragmented landscape with a single foundation:

> **Structured Concurrency governed by Linear Capabilities and Effect Rows.**

---

## 2. Core Concurrency Primitives

NOVA unifies concurrency into three primary structured blocks:

### 2.1 Parallel Join (`parallel { ... }`)
Executes all branches concurrently and waits for all of them to complete. If any branch yields an error or panics, sibling branches are **cancelled immediately**:

```nova
fn fetch_dashboard(net: Network, user_id: UUID) -> Result[Dashboard, Error] ! {Network} {
    parallel {
        let user = fetch_user(net, user_id)?;
        let orders = fetch_orders(net, user_id)?;
        let notifications = fetch_notifications(net, user_id)?;
    }
    Ok(Dashboard { user: user, orders: orders, notifications: notifications })
}
```

### 2.2 Speculative Race (`race { ... }`)
Executes branches concurrently and yields the result of the **first branch to complete**, cancelling all slower branches:

```nova
fn query_fastest_replica(net: Network, query: String) -> Result[Data, Error] ! {Network} {
    race {
        query_node(net, "replica-east.internal", query),
        query_node(net, "replica-west.internal", query),
    }
}
```

### 2.3 Isolated Message-Passing Actors
Actors maintain isolated heaps and communicate exclusively by transferring ownership of `Send` messages over typed channels:

```nova
struct WorkerMsg { payload: String, reply_to: Channel[Int] }

fn start_worker(inbox: Channel[WorkerMsg]) -> () ! {Concurrent} {
    while let Some(msg) = inbox.recv() {
        let result = compute(msg.payload);
        msg.reply_to.send(result);
    }
}
```

---

## 3. Data-Race Freedom by Construction

NOVA guarantees data-race freedom without requiring a runtime global interpreter lock (GIL):

1. **The Region XOR Invariant:** Multiple concurrent tasks may hold shared read references (`&Region`) to immutable data. A mutable region (`&mut Region`) is **linear** and can never be shared across tasks.
2. **`Send` and `Share` Invariants:** A value can only cross a task or channel boundary if it holds no non-global linear capability handles.
3. **Effect Row Tracking:** Any function spawning concurrent work carries the `! {Concurrent}` effect, ensuring callers are aware of asynchronous scheduling.

---

## 4. Failure Propagation & Cooperative Cancellation

* **Hierarchical Tree Lifetimes:** Every task has a parent. A parent scope cannot complete until all child tasks finish.
* **Deterministic Cancellation:** When a task scope is cancelled (due to timeout or error), cancellation tokens are propagated down the task tree.
* **No Swallowed Panics:** A panic in a background task triggers cancellation of its sibling tasks and propagates up the structured scope to the enclosing supervisor.
