# NOVA — Distributed Tracing & Continuous Profiling

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
**Cross-References:** [OBSERVABILITY.md](OBSERVABILITY.md), [RUNTIME-DIAGNOSTICS.md](RUNTIME-DIAGNOSTICS.md), [DISTRIBUTED-MODEL.md](../distributed/DISTRIBUTED-MODEL.md), [SCHEDULER-DESIGN.md](SCHEDULER-DESIGN.md)

---

## 1. Span Graphs from Lexical Concurrency

Structured concurrency trees in NOVA map 1-to-1 with OpenTelemetry-compatible span graphs:

```
[Span: HTTP POST /api/checkout] (Parent Root)
  │
  ├── [Span: parallel branch 1: fetch_user] ! {Database} (Duration: 2.1ms)
  │      └── [Event: Database.query] "SELECT * FROM users WHERE id = ?"
  │
  ├── [Span: parallel branch 2: reserve_items] ! {Database} (Duration: 3.4ms)
  │      └── [Event: Database.execute] "UPDATE inventory SET stock = stock - 1"
  │
  └── [Span: process_payment] ! {Network, Secret} (Duration: 85.0ms)
         └── [Event: Network.post] "https://api.stripe.com/v1/charges"
```

---

## 2. Distributed Context Propagation

Distributed network calls automatically inject standard W3C `traceparent` and `tracestate` headers into RPC payloads:

```
W3C Header: traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

When a remote worker receives a task via `dist.dispatch`, it extracts the `TraceContext` and attaches all downstream child spans to the caller's trace tree without manual context passing.

---

## 3. Continuous Low-Overhead Profiling

The NOVA runtime embeds a statistical sampling profiler inside the M:N work-stealing scheduler:
* **Overhead:** **< 0.8% CPU**, making it safe for continuous 24/7 production profiling.
* **Effect Partitioning:** Profiling samples record both the CPU instruction pointer and the **active effect row**, allowing instant separation of computational hotspots from I/O wait states.
* **Flame Graph Export:** Outputs standard `pprof` and Speedscope formats natively (`nova profile --export flamegraph.svg`).
