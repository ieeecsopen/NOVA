# NOVA — AI as a Controlled Computational Primitive

**Status:** Production Design Reference  
**Cross-References:** [AGENT-MODEL.md](AGENT-MODEL.md), [AI-SECURITY.md](AI-SECURITY.md), [MODEL-PROVENANCE.md](MODEL-PROVENANCE.md), [AI-REPRODUCIBILITY.md](AI-REPRODUCIBILITY.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

---

## 1. The Core Doctrine

> **AI is NOT the identity of NOVA.**  
> AI is simply an uncalibrated, stochastic external computational service.

In NOVA, AI models do not bypass the language's safety systems. They must strictly obey NOVA's existing:
* **Type System:** Structured outputs parse directly into nominal NOVA types with contract validation.
* **Effect System:** Model invocations require the explicit `ai: AI` capability and register the `! {AI}` effect.
* **Resource Budgets:** Every call executes under strictly bounded token, time, and financial ceilings.
* **Failure Semantics:** Model hallucinations, timeouts, and rate limits return `Result[T, AIError]`.

---

## 2. Core AI Primitives

```nova
// 1. Model Handle with explicit version pinning
struct Model {
    provider: String,
    name: String,
    version_hash: String,
    temperature: Float,
}

// 2. Structured Typed Generation
fn extract_user_intent[T](ai: AI, model: Model, prompt: String) -> Result[T, AIError] ! {AI} {
    // Generates output guaranteed to deserialize into nominal type T
    ai.structured_complete[T](model, prompt)
}
```

---

## 3. Structured Outputs & Contract Validation

Raw unconstrained text generation is restricted to unstructured chat endpoints. When structured data is required, the compiler pairs LLM generation with **automatic contract invariant verification**:

```nova
struct ExtractedInvoice {
    vendor: String,
    total_cents: Int,
    due_date: String,
}
invariant total_cents > 0;

fn parse_invoice_pdf(ai: AI, pdf_bytes: List[Int]) -> Result[ExtractedInvoice, ParseError] ! {AI} {
    // 1. Structured decoding
    let invoice = ai.structured_complete[ExtractedInvoice](Model::default(), pdf_bytes)?;
    
    // 2. Contract verification is run automatically:
    // If total_cents <= 0, returns Err(ParseError::ContractBreach("total_cents > 0"))
    Result::Ok(invoice)
}
```
