# NOVA — Ecosystem Bridges (Python, JS/TS, Databases)

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
**Cross-References:** [INTEROPERABILITY.md](INTEROPERABILITY.md), [FFI-MODEL.md](FFI-MODEL.md), [WASM-COMPONENT-MODEL.md](WASM-COMPONENT-MODEL.md), [DATA-MODEL.md](../full-stack/DATA-MODEL.md)

---

## 1. Python Ecosystem Bridge (PyTorch, NumPy, Pandas)

NOVA integrates with the Python data science and machine learning ecosystem via an embedded CPython bridge requiring the `py: Python` capability:

```nova
fn run_pytorch_model(py: Python, weights_path: String, input_tensor: List[Float]) -> Result[List[Float], PyError] ! {Python} {
    // 1. Import Python module dynamically
    let torch = py.import_module("torch")?;
    
    // 2. Load model and execute tensor inference
    let model = torch.call("load", weights_path)?;
    let tensor = torch.call("tensor", input_tensor)?;
    let output = model.call("forward", tensor)?;
    
    Result::Ok(output.to_list())
}
```

---

## 2. JavaScript & TypeScript Bridge

NOVA generates first-class TypeScript declaration files (`.d.ts`) and npm package wrappers automatically during compilation:

```bash
nova build src/lib.nova --target npm -o dist/
```

### Generated TypeScript Interface (`dist/index.d.ts`):
```typescript
export interface UserProfile {
    id: string;
    name: string;
    email: string;
}

export declare class NovaEngine {
    constructor();
    processUser(user: UserProfile): Promise<boolean>;
}
```

---

## 3. Database Wire Protocol Bridges

NOVA connects directly to production databases using standard wire protocols:
* **PostgreSQL:** Binary frontend/backend wire protocol over TCP (`! {Database}`).
* **MySQL:** Standard client handshake protocol.
* **Redis:** RESP3 binary protocol for in-memory caching.
* **SQLite:** Embedded C library bridge linked natively (`libsqlite3`).
