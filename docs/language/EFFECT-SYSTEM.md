# NOVA — Effect System Specification

**Status:** Production Design Reference  
**Cross-References:** [RFC 0001](../../RFC/0001-core-capability-effects.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md), [TYPE-SYSTEM.md](TYPE-SYSTEM.md), [SECURITY-MODEL.md](SECURITY-MODEL.md)

---

## 1. The Unified Core Thesis

Standard programming languages treat **what code does** (effects) and **what authority code holds** (capabilities) as separate concerns:
* **Effect systems** (e.g., Koka, Eff) record side effects via row typing, but effects remain ambient—any function can invoke an effect operation as long as its signature permits it.
* **Capability systems** (e.g., Austral, Pony, E) require explicit references to execute privileged operations, but lose visibility when authority is captured inside closures or struct fields.

NOVA unifies these two models by establishing an equivalence:

$$\text{Effect Label} \equiv \text{Capability Type}$$

A function's effect row is not manually authored redundant metadata; it is **statically derived** from the capability values reachable within the function's body, including all closure captures and field projections.

```nova
// Purity is the default (empty effect row: ! {})
fn pure_add(x: Int, y: Int) -> Int {
    x + y
}

// Effect row ! {Filesystem, Network} is derived from reachable capability arguments
fn fetch_and_cache(net: Network, fs: Filesystem, url: String, path: String) -> Result<Int, Error> ! {Network, Filesystem} {
    let payload = net.get(url)?;
    fs.write(path, payload)?;
    Ok(payload.len())
}
```

---

## 2. Standard Effect Taxonomy

NOVA defines a standardized taxonomy of effect labels corresponding to system capabilities:

| Effect Label | Capability Type | Operations Provided | Ambient Alternative in Other Languages |
| :--- | :--- | :--- | :--- |
| `pure` | *(None / Empty Row)* | Deterministic computation, pure arithmetic | Default everywhere |
| `Filesystem` | `fs: Filesystem` | `read`, `write`, `stat`, `create_dir`, `delete` | `open()`, `std::fs::read` |
| `Network` | `net: Network` | `connect`, `listen`, `send`, `recv`, `bind` | `fetch()`, `std::net::TcpStream` |
| `Database` | `db: Database` | `query`, `execute`, `begin_transaction` | Global DB connection pools |
| `Clock` | `c: Clock` | `now()`, `sleep(ms)`, `elapsed()` | `SystemTime::now()`, `time.time()` |
| `Random` | `rng: Random` | `next_u64()`, `next_bytes()`, `sample()` | `rand::random()`, `Math.random()` |
| `Process` | `proc: Process` | `spawn()`, `exec()`, `kill()`, `getenv()` | `os.system()`, `std::process::Command` |
| `GPU` | `gpu: GPU` | `alloc_buffer()`, `dispatch_kernel()`, `sync()` | CUDA runtime, WebGPU |
| `AI` | `ai: AI` | `embed()`, `complete()`, `infer()` | Global client SDKs |
| `Distributed`| `node: Distributed` | `send_message()`, `register_actor()`, `elect()` | Akka / Erlang distribution |
| `Secret` | `vault: Secret` | `unwrap_key()`, `sign()`, `decrypt()` | Memory-mapped keys / HSM calls |
| `Unsafe` | `u: Unsafe` | `raw_ptr_deref()`, `transmute()`, `ffi_call()` | `unsafe { ... }` block |

---

## 3. Algebraic Effects vs. Capability-Derived Effects

NOVA studies and incorporates algebraic effect semantics while solving their classical performance and auditing flaws:

| Dimension | Classical Algebraic Effects (Koka, Eff) | Capability-Derived Effects (NOVA) |
| :--- | :--- | :--- |
| **Authority Source** | Ambient effect handlers installed in caller stack. | Explicit first-class capability arguments. |
| **Closure Escapes** | Caller must supply dynamic handler or effect escapes upward. | Static reachability checks captures; captures are visible in effect signature. |
| **Runtime Cost** | Delimited continuations / stack switching overhead. | Zero runtime cost (effects erased after type checking). |
| **Supply Chain Safety** | Malicious packages can perform ambient effects if handler exists. | Malicious package has zero authority unless passed capability values explicitly. |

---

## 4. Effect Row Polymorphism and Propagation

Higher-order functions propagate effect rows dynamically through type-level row variables (`..r`):

```nova
// Row-polymorphic higher order function
fn retry<T, ..r>(attempts: Int, action: () -> T ! {..r}) -> Result<T, Error> ! {..r} {
    let mut i = 0;
    while i < attempts {
        // Invoking action performs exactly the row ..r of the closure
        match action() {
            Ok(v) => return Ok(v),
            Err(e) => { i = i + 1; }
        }
    }
    Err(Error::MaxRetriesExceeded)
}
```

* If `action` is pure: `retry(3, || 42)` has effect row `! {}` (pure).
* If `action` captures `Network`: `retry(3, || net.get("..."))` has effect row `! {Network}`.
* **Row Laundering is Impossible:** The compiler rejects any attempt to hide or discard effect rows when closures are passed or returned.

---

## 5. Formal Typing Rules for Effects

### 5.1 Pure Expression Axiom
$$\frac{}{\Gamma \vdash c : \tau \mid \emptyset}$$

### 5.2 Capability Invocation Rule
$$\frac{\Gamma \vdash e_{recv} : \text{Cap}(C) \mid \mathcal{E}_1 \quad \Gamma \vdash e_{arg} : \tau_{in} \mid \mathcal{E}_2}{\Gamma \vdash e_{recv}.\text{op}(e_{arg}) : \tau_{out} \mid \mathcal{E}_1 \cup \mathcal{E}_2 \cup \{C\}}$$

### 5.3 Closure Formation & Capture Derivation
$$\frac{\Gamma, x : \tau_1 \vdash e_{body} : \tau_2 \mid \mathcal{E} \quad \text{ReachableCaps}(e_{body}) = \mathcal{E}_{reach}}{\Gamma \vdash (\lambda x.\, e_{body}) : (\tau_1 \to \tau_2 \mathbin{!} \mathcal{E}) \mid \emptyset} \quad \text{where } \mathcal{E} = \mathcal{E}_{reach}$$

### 5.4 Subsumption / Row Widening
$$\frac{\Gamma \vdash e : (\tau_1 \to \tau_2 \mathbin{!} \mathcal{E}_1) \mid \emptyset \quad \mathcal{E}_1 \subseteq \mathcal{E}_2}{\Gamma \vdash \text{widen}(e) : (\tau_1 \to \tau_2 \mathbin{!} \mathcal{E}_2) \mid \emptyset}$$
*(Note: Widening allows over-approximating an effect signature for abstraction, but the compiler statically tracks genuine usage during auditing.)*
