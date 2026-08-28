# NOVA — Data Provenance & Lineage Model

**Status:** Production Design Reference  
**Cross-References:** [UNCERTAINTY-MODEL.md](UNCERTAINTY-MODEL.md), [TEMPORAL-MODEL.md](TEMPORAL-MODEL.md), [SECURITY-MODEL.md](SECURITY-MODEL.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

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
