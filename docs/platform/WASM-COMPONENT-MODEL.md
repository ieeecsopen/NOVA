# NOVA — WebAssembly Component Model & WIT Integration

**Status:** Production Design Reference  
**Cross-References:** [INTEROPERABILITY.md](INTEROPERABILITY.md), [ECOSYSTEM-BRIDGES.md](ECOSYSTEM-BRIDGES.md), [APPLICATION-MODEL.md](../full-stack/APPLICATION-MODEL.md)

---

## 1. WebAssembly Interface Types (WIT) Integration

NOVA natively supports the W3C WebAssembly Component Model. Every NOVA package can export and import standard `.wit` interface definitions:

```wit
// WIT Interface: search.wit
package nova:search;

interface engine {
    record search-request {
        query: string,
        limit: u32,
    }

    record search-result {
        id: string,
        score: float32,
    }

    query-index: func(req: search-request) -> list<search-result>;
}
```

---

## 2. Compiling NOVA to WASM Components

The NOVA compiler produces standard WASM components directly:

```bash
nova build src/engine.nova --target wasm32-wasi-component -o search_engine.wasm
```

```nova
// Implementing the WIT interface in NOVA:
export search.engine {
    fn query_index(req: SearchRequest) -> List[SearchResult] {
        // Pure implementation compiled to sandboxed WebAssembly component
        execute_search(req.query, req.limit)
    }
}
```

---

## 3. Polyglot Component Composition

Because NOVA components adhere to the canonical WASM Component Model ABI, they compose seamlessly with components written in other languages:

```
+-------------------------------------------------------------+
|                  Wasmtime / Edge Runtime Sandbox            |
|                                                             |
|  +---------------------+        +------------------------+  |
|  | NOVA Business Logic | <----> | Rust Cryptography Core |  |
|  +---------------------+        +------------------------+  |
|            │                                                |
|            ▼                                                |
|  +---------------------+                                    |
|  | Python ML Predictor |                                    |
|  +---------------------+                                    |
+-------------------------------------------------------------+
```

* Zero native C FFI security vulnerabilities.
* Memory isolation enforced by WebAssembly linear memory sandboxes.
* Standardized binary serialization over the Canonical ABI.
