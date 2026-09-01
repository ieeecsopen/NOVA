# NOVA — Data Provenance & Lineage Model

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
**Cross-References:** [UNCERTAINTY-MODEL.md](UNCERTAINTY-MODEL.md), [TEMPORAL-MODEL.md](TEMPORAL-MODEL.md), [SECURITY-MODEL.md](../language/SECURITY-MODEL.md), [CAPABILITY-MODEL.md](../language/CAPABILITY-MODEL.md)

---

## 1. Provenance as a First-Class Invariant

In modern applications, security and data integrity require knowing **who produced data, when it was generated, and how it was transformed**.

NOVA introduces **Provenance-Tracked Types** that carry cryptographic lineage without manual log parsing:

$$\text{Tracked Value} = \text{Data Payload } (T) + \text{Lineage Certificate}$$

```nova
struct Provenance[T] {
    data: T,
    origin: OriginType,
    created_at: Int,
    transformation_chain: List[Hash],
    signature: Option[Signature],
}
```

---

## 2. Origin Taxonomy

| Origin Category | Nature | Trust Level | Example Source |
| :--- | :--- | :--- | :--- |
| **`Origin::GroundTruth`** | Trusted internal database or hardware sensor | **High** | Internal Postgres, Secure Enclave |
| **`Origin::AuthenticatedUser`** | Verified user input via authenticated session | **Medium-High** | Signed JWT request |
| **`Origin::ExternalUntrusted`** | Third-party web webhook or public input | **Low (Tainted)** | Unauthenticated HTTP POST |
| **`Origin::SyntheticModel`** | AI model generation / LLM synthesis | **Probabilistic** | LLM completion output |

---

## 3. Security Applications

### 3.1 Prompt Injection Defense
Untrusted user inputs are typed as `Provenance[String, Origin::ExternalUntrusted]`. LLM prompt templates reject raw untrusted strings, forcing developers to sanitize or escape them explicitly:

```nova
fn build_safe_prompt(user_input: Provenance[String, Origin::ExternalUntrusted]) -> SafePrompt {
    let sanitized = sanitize_delimiters(user_input.data);
    SafePrompt::new(sanitized)
}
```

### 3.2 PII Redaction Verification
Functions returning data to public logs mandate the `Redacted[T]` proof type:

```nova
struct UserRecord {
    name: String,
    ssn: String,
}

fn redact_for_logs(record: UserRecord) -> Redacted[UserRecord] {
    Redacted {
        name: record.name,
        ssn: "***-**-****"
    }
}
```
