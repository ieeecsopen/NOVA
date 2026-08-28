# NOVA — Formal Threat Model & Isolation Boundaries

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
