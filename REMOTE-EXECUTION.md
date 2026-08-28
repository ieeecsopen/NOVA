# NOVA — Location-Independent Remote Execution

**Status:** Production Design Reference  
**Cross-References:** [DISTRIBUTED-MODEL.md](DISTRIBUTED-MODEL.md), [FAILURE-SEMANTICS.md](FAILURE-SEMANTICS.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md)

---

## 1. The Location Independence Invariant

In conventional languages, functions cannot be safely moved across machines because they implicitly depend on ambient machine state (global variables, local filesystems, memory addresses, and specific OS architectures).

In NOVA, a function whose effect row is strictly constrained carries **zero ambient dependencies**. Consequently:

> **A pure or capability-bounded NOVA computation executes identically across Local CPU, Remote Cloud, Edge WASM, or GPU without semantic deviation.**

$$\text{Semantics}(\text{Task}_{\text{Local}}) \equiv \text{Semantics}(\text{Task}_{\text{Remote}}) \equiv \text{Semantics}(\text{Task}_{\text{WASM}})$$

---

## 2. Supported Execution Targets

```nova
enum ExecutionTarget {
    LocalCPU,
    RemoteNode(NodeHandle),
    EdgeWorker(RegionId),
    GPUDevice(Int),
    WASMSandbox,
}
```

```nova
// A pure compute task
fn compute_mandelbrot(width: Int, height: Int) -> List[Int] {
    // Pure algorithmic calculation
    ...
}

// Dispatched identically to GPU or Remote Worker
fn run_analysis(dist: Distributed) -> Result<List[Int], RemoteError> ! {Distributed} {
    // Shipped to GPU accelerator
    let gpu_result = dist.dispatch(ExecutionTarget::GPUDevice(0), || compute_mandelbrot(1920, 1080))?;
    
    // Shipped to remote cloud worker
    let cloud_result = dist.dispatch(ExecutionTarget::RemoteNode(dist.cluster().worker(1)), || compute_mandelbrot(1920, 1080))?;
    
    Result::Ok(cloud_result)
}
```

---

## 3. Code Mobility via WebAssembly Component Model

1. **Content-Addressed Hashing:** Computations are hashed by their AST structure and bytecode representation (inspired by Unison). If a remote worker already possesses the bytecode hash, only input arguments are transferred over the wire.
2. **WASM Sandboxing:** Tasks dispatched to untrusted remote or edge nodes are executed inside an isolated WebAssembly sandbox with zero ambient capabilities.
3. **Capability Re-hydration:** If a task requires `Filesystem`, the destination worker re-hydrates the task with an attenuated local `Filesystem` handle scoped strictly to a sandboxed directory.
