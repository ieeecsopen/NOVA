# NOVA — Security Model & Threat Analysis

**Status:** Production Design Reference  
**Cross-References:** [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md), [RFC 0001](../../RFC/0001-core-capability-effects.md)

---

## 1. Threat Model & Trust Boundaries

NOVA is architected for adversarial multi-tenant environments and modern open-source supply chains.

```
+-------------------------------------------------------------+
|                     Application Main                        |
|   (Holds Root Authority `rt: Runtime` from Operating System)|
+------------------------------+------------------------------+
                               | Explicit Attenuated Caps
                               v
+------------------------------+------------------------------+
|                     Third-Party Crates                      |
| (Zero ambient authority; can ONLY act on passed capability) |
+-------------------------------------------------------------+
```

### Trust Assumptions:
1. **Operating System & Runtime Core:** The root runner (`verifier/refspec/driver.py` / native runtime) securely injects the root `Runtime` capability into `main()`.
2. **Type Verifier Soundness:** The NOVA type checker, reachability verifier, and row-unification engine are trusted to accept only well-typed programs.
3. **Third-Party Code is Untrusted:** All third-party libraries and transitive dependencies are treated as potentially malicious or compromised.

---

## 2. Attack Vectors and Formal Defenses

### 2.1 Attack: Closure Authority Laundering
* **Attack Scenario:** An attacker writes a function returning a closure that captures the `Network` capability, claiming in the signature that the returned closure is pure (`() -> Int ! {}`).
* **NOVA Defense:** **Rejected statically (`E0105`, `tests/conformance/004`, `022`).** The reachability analyzer detects free capability variables in closure ASTs and forces them into the closure's effect row.

### 2.2 Attack: Dependency Authority Creep (Supply Chain Attack)
* **Attack Scenario:** A minor version bump of an image-processing library (`1.0.0` -> `1.0.1`) injects telemetry sending private image data to an external server via `Network`.
* **NOVA Defense:** **Prevented by construction.** The image processing function only accepts a pure byte slice. Because it has no `Network` capability parameter, it physically cannot initiate network I/O, regardless of what dependencies it imports. Furthermore, `tools/manifest-diff.py` flags capability requirement diffs during build time (`tests/manifest/logging-lib/`).

### 2.3 Attack: Capability Forgery
* **Attack Scenario:** An attacker attempts to forge a capability by casting an integer/string or instantiating a raw struct holding simulated capability handles.
* **NOVA Defense:** **Rejected statically (`E0112`, `tests/conformance/012`, `021`).** Capability types have private internal constructors accessible only to the runtime or designated attenuation methods.

### 2.4 Attack: Branch Effect Laundering
* **Attack Scenario:** A function performs a side effect in one conditional branch (e.g. `if condition { net.send(...) }`) but attempts to omit the effect from the function signature because the branch might not always execute.
* **NOVA Defense:** **Rejected statically (`tests/conformance/023`).** The effect row of an `if-else` or `match` block is the **formal join ($\cup$)** of all branch rows.

---

## 3. Security Verification Matrix

| Vulnerability Class | Traditional Language Status | NOVA Invariant & Status | Proven By |
| :--- | :--- | :--- | :--- |
| **Ambient Exfiltration** | Vulnerable (`import os; os.system(...)`) | **Eliminated by design** (No ambient imports) | RFC 0001 §4 |
| **Closure Smuggling** | Vulnerable (Closures hide captures) | **Statically Prevented** (Reachability pass) | `tests/conformance/004` |
| **Capability Forgery** | Vulnerable (Pointer casting) | **Statically Prevented** (`E0112`) | `tests/conformance/012` |
| **Supply Chain Hijacking**| Vulnerable (Silent ambient I/O) | **Statically Prevented** (Manifest diffing) | `tests/manifest/` |
| **Memory-Corruption Escape**| Vulnerable (Use-after-free, races) | **Statically Prevented** (Linear regions) | `regionlab/tests/` |
| **Unhandled Effect Drifts**| Vulnerable (Manual trace logging) | **Eliminated by design** (Row derivation) | `tests/tracing/` |
