# NOVA — Architectural Red Team & Adversarial Analysis

**Status:** Official Foundation Reference  
**Cross-References:** [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md), [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md), [DECISION-LOG.md](DECISION-LOG.md)

---

## 1. Adversarial Challenges & Red Team Attacks

The NOVA architecture was subjected to explicit adversarial critique during design:

### Challenge 1: "Capability passing is too verbose for scripting."
* **Red Team Critique:** Developers will reject a language where simple `print` requires passing `rt: Runtime`.
* **Resolution:** Module-level entrypoint sugar and inferred effect rows preserve full static soundness while reducing manual boilerplate for simple CLI utilities.

### Challenge 2: "Region XOR cannot express arbitrary cyclic graphs without GC."
* **Red Team Critique:** Complex graph data structures cannot be modeled with pure hierarchical regions.
* **Resolution:** Dedicated arena graph indexes (index-based references) and linear capability-tracked nodes handle cyclic topologies safely without requiring tracing GC pauses.

### Challenge 3: "AI models will find prompt injection bypasses."
* **Red Team Critique:** Attackers can hijack LLMs to execute destructive operations.
* **Resolution:** In NOVA, an agent possesses zero implicit authority. Even if an LLM is hijacked, it physically cannot initiate filesystem or network calls unless the capability handle is explicitly present in its scope.
