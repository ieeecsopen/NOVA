# NOVA Package Manager (`nova add` / `nova remove`)

The capability-aware package management system for the NOVA ecosystem.

---

## 1. Principles

* **Explicit Authority Boundaries:** Dependencies must declare all required capabilities in `nova.toml`.
* **Zero Ambient Access:** A library cannot access system resources unless passed capabilities by the consumer.
* **Semantic Manifest Diffing:** Updates that request new capabilities are flagged as security events (`tools/manifest-diff.py`).

---

## 2. CLI Usage

### Add a Dependency
```bash
nova add analytics --caps Network
```

### Remove a Dependency
```bash
nova remove analytics
```

### Audit Package Capabilities
```bash
nova manifest diff package-v1/ package-v2/
```
