# NOVA — Work-Stealing Scheduler Architecture

**Status:** Production Design Reference  
**Cross-References:** [CONCURRENCY-MODEL.md](CONCURRENCY-MODEL.md), [MEMORY-MODEL.md](../language/MEMORY-MODEL.md), [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 1. M:N Work-Stealing Architecture

NOVA multiplexes $M$ lightweight user-space tasks over $N$ operating system worker threads (where $N = \text{CPU cores}$).

```
                     +---------------------------------+
                     |     Global Injection Queue      |
                     +----------------+----------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+------------------------+                                +------------------------+
|  Worker Thread 0       |  <======= Work Stealing =====> |  Worker Thread N-1     |
|  +------------------+  |                                |  +------------------+  |
|  | Local Task Deque |  |                                |  | Local Task Deque |  |
|  +------------------+  |                                |  +------------------+  |
|  | Event Poller (kqueue|                                |  | Event Poller (kqueue|
|  | / io_uring)      |  |                                |  | / io_uring)      |  |
+------------------------+                                +------------------------+
```

---

## 2. Task Lifecycle & State Transitions

Each task in NOVA transitions through explicit, deterministic states:

```
[Spawned] ──> [Ready] ──> [Running] ──> [Completed]
                ^            │
                │            ▼
                └─── [Blocked (I/O / Channel)]
```

* **`Spawned`:** Allocated within its parent structured concurrency frame (~2KB initial stack frame).
* **`Ready`:** Placed into the worker's local deque for execution.
* **`Running`:** Executing on an OS worker core.
* **`Blocked`:** Suspended waiting for non-blocking I/O event (`kqueue` / `io_uring`) or channel message; worker thread immediately switches to another ready task without blocking the OS thread.
* **`Cancelled`:** Task token revoked; cleans up local region and unwinds.

---

## 3. Work-Stealing Algorithm (Chase-Lev Deque)

1. **LIFO Local Execution:** A worker pushes and pops child tasks from the *bottom* of its local deque (data cache locality).
2. **FIFO Work Stealing:** When a worker runs out of tasks, it attempts to steal tasks from the *top* of another random worker's deque, minimizing lock contention.
3. **Capability-Prioritized Scheduling:** Tasks carrying real-time or user-facing effect rows (e.g. `! {DOM}`) are prioritized over background compute tasks (`! {Database, AI}`).

---

## 4. Performance & Memory Characteristics

| Metric | Traditional OS Threads | Go Goroutines | NOVA Structured Tasks |
| :--- | :--- | :--- | :--- |
| **Stack Memory Overhead** | ~1 MB – 8 MB | ~2 KB (dynamic growth) | **~2 KB (lexical region scoped)** |
| **Context Switch Latency**| ~1.5 µs – 3.0 µs | ~150 ns | **~40 ns – 80 ns** |
| **Orphan Task Risk** | High | High (Unscoped) | **Zero (Compiler-enforced tree)** |
| **Data Race Freedom** | Manual / Unsafe | Data race prone | **Guaranteed by Region XOR** |
