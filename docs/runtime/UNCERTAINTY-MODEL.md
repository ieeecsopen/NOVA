# NOVA — Epistemic Uncertainty Model

**Status:** Production Design Reference  
**Cross-References:** [TEMPORAL-MODEL.md](TEMPORAL-MODEL.md), [PROVENANCE-MODEL.md](PROVENANCE-MODEL.md), [LANGUAGE-PHILOSOPHY.md](../foundation/LANGUAGE-PHILOSOPHY.md), [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md)

---

## 1. The Epistemic Invariant: Truth vs. Prediction

In modern software integrating machine learning and LLMs, treating model outputs as ordinary certain values leads directly to security vulnerabilities, hallucinations, and unhandled failure modes.

NOVA strictly partitions values into **four distinct epistemic states**:

```
[Certain[T]]       ──> Ground-truth, deterministic invariant (e.g. database read, pure math).
     │
[Calibrated[T, P]] ──> Statistically calibrated probability (e.g. conformal prediction coverage).
     │
[Prediction[T, S]] ──> Heuristic model score / softmax confidence (NOT true probability).
     │
[Unknown[Reason]]  ──> Explicit missing or unobserved data with causal rationale.
```

---

## 2. The Cardinal Prohibition: Confidence $\neq$ Probability

In adherence to Constitution Article V (Honest Claims):

$$\text{Model Confidence Score } (S) \not\equiv \text{True Probability } (P)$$

Softmax outputs and LLM self-reported confidence are uncalibrated heuristics. The NOVA type system **prohibits casting `Prediction[T, Score]` to `Calibrated[T, Probability]`** without passing through a verified statistical calibration gate:

```nova
// An uncalibrated AI model prediction
struct Classification {
    label: String,
    score: Float, // e.g. 0.95
}

// Conformal calibration function converting heuristic score to rigorous coverage probability
fn calibrate[T](pred: Prediction[T, Float], cal: ConformalCalibrator) -> Result[Calibrated[T, Float], CalibrationError] {
    if cal.is_valid_sample(pred) {
        let p = cal.compute_p_value(pred.score);
        Result::Ok(Calibrated { value: pred.value, probability: p })
    } else {
        Result::Err(CalibrationError::DistributionShift)
    }
}
```

---

## 3. High-Stakes Type-Level Guardrails

High-integrity functions mandate `Certain[T]` or `Calibrated[T, P > 0.99]`, statically preventing unverified AI predictions from executing privileged mutations:

```nova
struct MedicalDosage {
    patient_id: UUID,
    milligrams: Int,
}

// Statically requires verified certain dosage
fn administer_dosage(vault: Secret, dosage: Certain[MedicalDosage]) -> Result<(), Error> ! {Secret} {
    // Safe to administer
    ...
}

// Attempting to pass an AI prediction directly is rejected at compile time:
// administer_dosage(vault, ai_suggested_dosage); // ERROR: expected Certain[MedicalDosage], found Prediction[MedicalDosage]
```
