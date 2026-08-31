# NOVA — Whole-Application Topology Model

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
**Cross-References:** [FULL-STACK-MODEL.md](FULL-STACK-MODEL.md), [UI-MODEL.md](UI-MODEL.md), [SERVICE-MODEL.md](SERVICE-MODEL.md), [DATA-MODEL.md](DATA-MODEL.md)

---

## 1. Declarative Application Topology

NOVA allows an entire distributed system to be declared within a unified application topology block:

```nova
application CampusPortal {
    // Client entrypoint compiled to WASM & SSR HTML
    frontend Web {
        entry: pages.Home,
        allowed_capabilities: [DOM, Fetch, LocalStorage],
    }

    // Backend microservices and API gateways
    services {
        API {
            routes: api.Routes,
            requires: [Database, Secret],
        }

        Worker {
            tasks: jobs.BackgroundQueue,
            requires: [Database, Network],
        }
    }

    // Database cluster configuration
    database Postgres {
        schema: [User, Order, Course, Registration],
        pool_size: 20,
    }
}
```

---

## 2. Multi-Target Compilation

A single `application` topology definition can be compiled into multiple deployment formats without changing application source code:

1. **Single Monolith Native Executable:** Frontend WASM assets embedded in binary; services run in in-process threads communicating via zero-copy channels.
2. **Containerized Microservices:** Emits individual container images for `API` and `Worker` with isolated capability manifests.
3. **Serverless Edge WASM:** Emits lightweight WASM workers for edge routing and SSR rendering.

---

## 3. End-to-End Boundary Verification

Before generating any deployment artifact, the NOVA compiler statically verifies:
* **No Capability Leaks:** The `frontend Web` tier cannot transitively reference `Database` or `Secret` capabilities.
* **Schema Consistency:** All queries in `API` match the exact columns declared in the `database Postgres` entities.
* **Type-Safe RPCs:** All network payloads exchanged between `Web` and `API` share verified serialization schemas.
