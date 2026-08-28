# NOVA — AI Model & Data Provenance

**Status:** Production Design Reference  
**Cross-References:** [AI-MODEL.md](AI-MODEL.md), [PROVENANCE-MODEL.md](../runtime/PROVENANCE-MODEL.md), [AI-SECURITY.md](AI-SECURITY.md)

---

## 1. Cryptographic Model Version Pinning

To guarantee reproducibility and prevent silent behavioral shifts when upstream providers update weights, NOVA mandates **cryptographic model digest pinning**:

```nova
struct PinnedModel {
    name: String,
    weights_sha256: String,
    tokenizer_version: String,
    context_window: Int,
}

// Example pinned reasoning model
const CLAUDE_SONNET: PinnedModel = PinnedModel {
    name: "claude-3-7-sonnet",
    weights_sha256: "sha256:8f4c2e...b3a1",
    tokenizer_version: "v3.2",
    context_window: 200000,
};
```

---

## 2. The Inference Provenance Certificate

Every model generation in NOVA produces an immutable **Inference Certificate**:

$$\text{Certificate} = \langle \text{ModelDigest}, \text{PromptHash}, \text{Seed}, \text{Temp}, \text{OutputHash}, \text{TokensUsed} \rangle$$

```nova
struct InferenceCertificate[T] {
    result: T,
    model: PinnedModel,
    prompt_hash: String,
    seed: Int,
    tokens_consumed: Int,
    cost_incurred: Float,
    timestamp: Int,
}
```

This certificate enables complete, post-hoc security audits and regulatory compliance verification without recording sensitive user prompt content in plaintext.
