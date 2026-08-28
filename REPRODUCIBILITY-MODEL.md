# NOVA — Hermetic & Reproducible Build Model

**Status:** Production Design Reference  
**Cross-References:** [ECOSYSTEM-DESIGN.md](ECOSYSTEM-DESIGN.md), [DEPLOYMENT-MODEL.md](DEPLOYMENT-MODEL.md), [SECURITY-MODEL.md](SECURITY-MODEL.md)

---

## 1. The Hermetic Build Invariant

In NOVA, software builds must be deterministic and bit-for-bit reproducible across different machines, continuous integration runners, and developer workstations:

$$\text{Source} + \text{nova.lock} + \text{CompilerDigest} + \text{TargetEnv} \implies \text{Exact Bit-for-Bit Machine Binary}$$

If two developers compile the same Git commit with the same toolchain version, the resulting executable binary has the exact same SHA-256 cryptographic digest.

---

## 2. Eliminating Sources of Non-Determinism

The NOVA native compiler eliminates all common causes of build variance:

| Variance Source | Traditional Behavior | NOVA Hermetic Solution |
| :--- | :--- | :--- |
| **Local File Paths** | Embedded absolute developer paths | Stripped via deterministic relative path remapping |
| **Build Timestamps** | `__DATE__` and `__TIME__` macros | Fixed to Git commit epoch (`SOURCE_DATE_EPOCH`) |
| **Symbol Ordering** | Non-deterministic hash map iteration | Canonical lexicographical AST sorting |
| **Floating Point Math** | Architecture-specific FMA instructions | IEEE 754 deterministic math mode |
| **Transitive Dependencies**| Floating semver ranges | Strict cryptographic checksum pinning in `nova.lock` |

---

## 3. Cryptographic Build Attestation (SLSA Level 4)

Upon completing a build, `nova build` can emit an in-toto / SLSA provenance attestation:

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "subject": [{ "name": "app_binary", "digest": { "sha256": "3e4b7c..." } }],
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "builder": { "id": "nova-compiler-v0.2.0" },
    "invocation": { "parameters": { "opt_level": "-O3" } }
  }
}
```
