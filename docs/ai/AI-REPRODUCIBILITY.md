# NOVA — AI Reproducibility & Evaluation Framework

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
**Cross-References:** [AI-MODEL.md](AI-MODEL.md), [MODEL-PROVENANCE.md](MODEL-PROVENANCE.md), [AI-SECURITY.md](AI-SECURITY.md)

---

## 1. The Reproducibility Challenge

LLM outputs are naturally stochastic. To achieve deterministic software engineering standards, NOVA provides **reproducible evaluation harnesses and transcript replay**:

$$\text{Deterministic Output} = f(\text{Prompt}, \text{ModelDigest}, \text{Seed}, \text{Temp} = 0)$$

---

## 2. Deterministic Inference Replay

```nova
struct ReplayHarness {
    transcript_log: String,
    mode: ReplayMode, // Live | MockFromTranscript | Record
}

fn execute_with_replay[T](harness: ReplayHarness, task: () -> Result[T, Error] ! {AI}) -> Result[T, Error] {
    match harness.mode {
        ReplayMode::MockFromTranscript => {
            // Replays exact recorded model response without making live network calls
            harness.load_cached_response()
        },
        ReplayMode::Live => task(),
        ReplayMode::Record => {
            let res = task()?;
            harness.record_transcript(res);
            Result::Ok(res)
        }
    }
}
```

---

## 3. Continuous Evaluation & Drift Detection

NOVA integrates evaluation test suites into `nova test`:

```nova
evaluation SemanticExtractionEval {
    dataset: "tests/eval/invoices.jsonl",
    target_accuracy: 0.98,
    metrics: [ExactMatch, F1Score, ContractPassRate],
}
```

If an upstream LLM update alters output formatting or drops accuracy below 98%, `nova test` flags the regression during continuous integration.
