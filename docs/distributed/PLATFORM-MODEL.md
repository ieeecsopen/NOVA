# NOVA — Unified Application Platform Model

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
**Cross-References:** [UNIFIED-APPLICATION-SPEC.md](../full-stack/UNIFIED-APPLICATION-SPEC.md), [END-TO-END-ARCHITECTURE.md](../full-stack/END-TO-END-ARCHITECTURE.md), [FULL-STACK-MODEL.md](../full-stack/FULL-STACK-MODEL.md), [APPLICATION-MODEL.md](../full-stack/APPLICATION-MODEL.md), [AI-MODEL.md](../ai/AI-MODEL.md)

---

## 1. The Glued Framework Antipattern, Solved

Contemporary cloud applications resemble an unstable patchwork of disconnected frameworks:
* **Frontend:** React + Next.js + TypeScript + Tailwind
* **Backend:** Node / Go / Rust + Express / Axum
* **API Wire:** GraphQL / OpenAPI / tRPC
* **Database:** PostgreSQL + Prisma / Diesel + Flyway migrations
* **AI:** LangChain / LlamaIndex + unmetered API calls
* **Infra:** Docker + Kubernetes manifests + Helm charts + Terraform

NOVA unifies this entire software lifecycle into **one coherent semantic model**:

> **A single language, compiler, runtime, and capability graph orchestrates the entire application topology.**

```
+---------------------------------------------------------------------------------------+
|                                  APPLICATION TOPOLOGY                                 |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   [FRONTEND (WASM/DOM)]                               [AI AGENTS (Bounded Budget)]     |
|   Reactive View Model                                  Researcher / Assistant         |
|   Caps: `[DOM, Fetch, Storage]`                        Budget: `< 20k tok, < $0.10`   |
|            │                                                    │                     |
|            ▼                                                    ▼                     |
|   +-------------------------------------------------------------------------------+   |
|   |                         BACKEND SERVICES (RPC / JOBS)                         |   |
|   |   API Gateway  •  Background Queue  •  Auth & Auditing                        |   |
|   |   Caps: `[Database, Secret, Network, Clock]`                                  |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           │                                           |
|                                           ▼                                           |
|                                [DATABASE & PERSISTENCE]                               |
|                                PostgreSQL / Linear ACID                               |
|                                Verified Entity Contracts                              |
+---------------------------------------------------------------------------------------+
```

---

## 2. Shared Semantic Projections Across the Whole Application

A single definition in NOVA projects into all application tiers without manual code duplication:

| Dimension | Compiler Projection from Single Definition |
| :--- | :--- |
| **Types & Validation** | Shared across client forms, wire payloads, backend handlers, and DB tables. |
| **Contracts & DbC** | Pre/post-conditions (`requires`, `ensures`) verified statically and at runtime. |
| **Permissions & Auth** | Unforgeable capability tokens (`AuthToken`) enforce role-based access. |
| **AI Governance** | Autonomous agents operate under strict lexical capability and financial envelopes. |
| **Observability** | Effect rows automatically synthesize OpenTelemetry trace spans and metrics. |
| **Deployment** | Topology compiles directly to OCI Containers, Edge WASM, or Native Monoliths. |
