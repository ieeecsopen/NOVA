# NOVA — Formal Threat Model & Isolation Boundaries

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


**Status:** Authoritative Security Reference  
**Cross-References:** [SECURITY-AUDIT.md](SECURITY-AUDIT.md), [CAPABILITY-MODEL.md](../language/CAPABILITY-MODEL.md), [AI-SECURITY.md](../ai/AI-SECURITY.md)

---

## 1. STRIDE Threat Classification

```
+---------------------------------------------------------------------------------------+
|                                STRIDE THREAT DEFENSE MATRIX                           |
+---------------------------------------------------------------------------------------+
|  [S] Spoofing Identity   ──> Unforgeable `AuthToken` capability handles.              |
|  [T] Tampering with Data ──> Region XOR prevents concurrent race mutation.            |
|  [R] Repudiation         ──> OpenTelemetry trace spans automatically emitted.         |
|  [I] Info Disclosure     ──> Zero ambient authority; explicit capability manifests.   |
|  [D] Denial of Service   ──> Strict lexical budget limits on CPU, memory, AI tokens.  |
|  [E] Elevation of Privs  ──> Pure code by default; no implicit privilege escalation.  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Trust Boundaries & Isolation Rings

```
 [Ring 0: Host OS Kernel & Unsafe Hardware]
    ▲
    │ (Strict FFI Boundary with `! {Unsafe}`)
 [Ring 1: NOVA Native Runtime Engine]
    ▲
    │ (Region XOR & Memory Frames)
 [Ring 2: Capability-Guarded Application Code]
    ▲
    │ (WASM Sandboxing & WIT Interfaces)
 [Ring 3: Guest WebAssembly Components & Third-Party Dependencies]
    ▲
    │ (Hard Lexical Budgets & Zero Ambient Authority)
 [Ring 4: Autonomous AI Reasoning Agents]
```

Every tier boundary requires explicit, statically verified capability delegation. No inner ring authority is ever inherited implicitly.
