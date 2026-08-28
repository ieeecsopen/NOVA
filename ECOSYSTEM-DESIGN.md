# NOVA — Package Ecosystem & Registry Architecture

**Status:** Production Design Reference  
**Cross-References:** [REPRODUCIBILITY-MODEL.md](REPRODUCIBILITY-MODEL.md), [DEPLOYMENT-MODEL.md](DEPLOYMENT-MODEL.md), [SECURITY-MODEL.md](SECURITY-MODEL.md), [package-manager/README.md](package-manager/README.md)

---

## 1. Zero-Ambient Package Security

In traditional package ecosystems (npm, PyPI, Cargo), a third-party dependency possesses identical ambient authority to the root application. A compromised transitive dependency can silently read `~/.ssh/id_rsa`, spawn child processes, or exfiltrate environment variables.

NOVA eliminates supply-chain exfiltration through **Capability-Bounded Manifests**:

> **A package can NEVER use a capability that has not been explicitly granted by the consumer in `nova.toml`.**

---

## 2. Rich Package Manifest (`nova.toml`)

```toml
[package]
name = "nova-http"
version = "1.2.0"
edition = "2026"
license = "Apache-2.0"
repository = "https://github.com/ieeecsopen/nova-http"

# Explicit capability requirements
[capabilities]
requires = ["Network", "Clock"]
prohibits = ["Filesystem", "Process", "Secret"]

# Resource envelopes for package operations
[resources]
max_memory = "32MB"
max_latency = "500ms"

# Compilation targets
[targets]
supported = ["native-arm64", "native-x86_64", "wasm32-wasi"]

[dependencies]
nova-tls = { version = "0.8.1", capabilities = ["Network"], integrity = "sha256:4a2f8b..." }
```

---

## 3. Semantic Manifest Diffing & Audits

When a package update requests new capabilities (e.g. version 1.2.1 adds `Filesystem.write`), the update is **flagged as a high-severity security event** during `nova update` and blocked until explicitly approved by the developer (`tools/manifest-diff.py`).
