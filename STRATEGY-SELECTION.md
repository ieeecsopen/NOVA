# NOVA — Runtime Strategy Selection & Explainability

**Status:** Research Reference (Post-v1 Exploratory)  
**Cross-References:** [ADAPTIVE-EXECUTION.md](ADAPTIVE-EXECUTION.md), [RUNTIME-OPTIMIZATION.md](RUNTIME-OPTIMIZATION.md), [OBSERVABILITY.md](OBSERVABILITY.md)

---

## 1. Runtime Signals Monitored

The runtime selection engine samples dynamic system state to evaluate the optimal execution strategy:

| Dynamic Signal | Source | Evaluated Metric | Impact on Strategy Selection |
| :--- | :--- | :--- | :--- |
| **Hardware Topology** | OS / Driver | GPU/NPU cores available | Disqualifies GPU variant if device is busy/absent. |
| **Memory Pressure** | Memory Region | Available heap space | Selects low-memory stream variant over batch cache. |
| **Energy / Battery** | Power Manager | Battery level % | Prioritizes CPU efficiency over high-power GPU kernels. |
| **Network Latency** | Event Poller | RTT to cloud worker | Rejects remote execution if RTT > 50ms. |
| **Budget Envelope** | Resource Meter | Remaining \$ / tokens | Prevents expensive cloud API dispatch. |

---

## 2. Transparent Explainability Architecture

To prevent "magic" non-deterministic debugging nightmares, every adaptive selection produces an **Explainability Trace Record**:

```text
[NOVA Adaptive Execution Trace]
  Operation:          SearchIndex
  Selected Strategy:  ParallelCPUSearch
  Rationale:          GPU device was busy with higher-priority shader task (queue depth: 4);
                      Local CPU load is low (18%);
                      Estimated latency: 4.8ms.
  Rejected Variants:
    - GPUVectorSearch:       REJECTED (Device busy, queue delay > 12ms)
    - RemoteClusterSearch:   REJECTED (Network RTT 48ms exceeds budget latency < 10ms)
    - SequentialCPUSearch:   REJECTED (Sub-optimal throughput vs. ParallelCPU)
```

Developers can inspect these decisions live in the debugger or query aggregated strategy metrics in production traces.
