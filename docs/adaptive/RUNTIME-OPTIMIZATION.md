# NOVA — Runtime Optimization & Autotuning

**Status:** Research Reference (Post-v1 Exploratory)  
**Cross-References:** [ADAPTIVE-EXECUTION.md](ADAPTIVE-EXECUTION.md), [STRATEGY-SELECTION.md](STRATEGY-SELECTION.md), [SCHEDULER-DESIGN.md](../runtime/SCHEDULER-DESIGN.md)

---

## 1. Multi-Tier Optimization Spectrum

NOVA structures code optimization along a four-tier compilation lifecycle:

```
[Tier 1] Static AOT Native Compilation (`clang -O3` machine binary)
   │
   ▼
[Tier 2] Profile-Guided Re-Optimization (Branch probabilities & cache layouts)
   │
   ▼
[Tier 3] Partial Evaluation & Constant Specialization (Futamura projections)
   │
   ▼
[Tier 4] Dynamic JIT & Superoptimization (Hot vector kernels & hardware synthesis)
```

---

## 2. Capability Specialization via Partial Evaluation

When a function takes a capability handle configured with fixed parameters (e.g. `fs: Filesystem` scoped to a static read-only directory), the runtime **partially evaluates and specializes the binary code**:

$$\text{SpecializedFunction} = \text{PartialEval}(f, \text{CapabilityHandle}_{\text{Static}})$$

This inlines directory path checks and constant capability access rules, reducing capability overhead to zero machine instructions.

---

## 3. De-Optimization & Reversion Safety

If dynamic system invariants change (e.g., an SMT constraint is challenged or memory pressure spikes):
1. **On-Stack Replacement (OSR):** The runtime transitions active stack frames to the baseline verified interpreter or conservative variant without dropping task state.
2. **Safe Rollback:** Execution continues seamlessly using the conservative baseline algorithm without memory corruption.
