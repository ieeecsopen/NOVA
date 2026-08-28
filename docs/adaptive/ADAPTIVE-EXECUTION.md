# NOVA — Adaptive Multi-Strategy Execution

**Status:** Research Reference (Post-v1 Exploratory)  
**Cross-References:** [STRATEGY-SELECTION.md](STRATEGY-SELECTION.md), [RUNTIME-OPTIMIZATION.md](RUNTIME-OPTIMIZATION.md), [INTENT-MODEL.md](../verification/INTENT-MODEL.md), [RESOURCE-MODEL.md](../runtime/RESOURCE-MODEL.md)

---

## 1. The Multi-Variant Semantic Principle

Traditional programming languages force the developer to hardcode a single algorithm (e.g. choosing between an in-memory hash table, an on-disk B-tree, a GPU shader, or a remote RPC service).

In NOVA, the developer specifies the **semantic goal, invariants, and constraints**, while the compiler and runtime choose among multiple valid implementation strategies based on dynamic hardware and operational context:

$$\text{Operation} = \text{Semantic Goal} + \{ \text{Variant}_1, \text{Variant}_2, \dots, \text{Variant}_n \}$$

```nova
strategy SearchIndex[T](query: Query) -> List[SearchResult] {
    // Contract all variants must satisfy:
    ensures result.len() <= query.limit;
    
    variant GPUVectorSearch {
        requires_capabilities: [GPU],
        optimizes: Latency,
        cost_profile: HighEnergy,
        impl: || gpu_search(query)
    }

    variant ParallelCPUSearch {
        requires_capabilities: [Concurrent],
        optimizes: Throughput,
        cost_profile: ModerateCPU,
        impl: || cpu_parallel_search(query)
    }

    variant RemoteClusterSearch {
        requires_capabilities: [Network, Distributed],
        optimizes: LargeScaleDataset,
        cost_profile: NetworkLatency,
        impl: || cluster_dispatch(query)
    }
}
```

---

## 2. The Cardinal Safety Invariant

In strict adherence to NOVA safety guarantees:

> **Adaptive strategy switching must NEVER silently violate declared contracts, effect rows, or capability boundaries.**

1. **Equivalence of Contracts:** Every variant must satisfy the exact same `requires`, `ensures`, and intent `guarantees`.
2. **Capability Containment:** A variant cannot be selected if its required capabilities (e.g. `GPU`) are not available in the caller's active scope.
3. **Budget Compliance:** A variant is immediately disqualified if its estimated cost exceeds the caller's `budget {}` envelope.
