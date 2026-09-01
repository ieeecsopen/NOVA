# NOVA — Ecosystem Interoperability Model

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
**Cross-References:** [FFI-MODEL.md](FFI-MODEL.md), [WASM-COMPONENT-MODEL.md](WASM-COMPONENT-MODEL.md), [ECOSYSTEM-BRIDGES.md](ECOSYSTEM-BRIDGES.md), [CAPABILITY-MODEL.md](../language/CAPABILITY-MODEL.md), [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md)

---

## 1. The Interoperability Philosophy: Adopt, Don't Rewrite

A new programming language that requires the entire software world to be rewritten from scratch is doomed to fail. NOVA is designed with a fundamental principle:

> **NOVA adopts existing ecosystems seamlessly. Never build unnecessary replacements for mature standards.**

NOVA bridges directly to C, C++, Rust, Python, JavaScript/TypeScript, WebAssembly, and native SQL databases while maintaining strict capability-based safety boundaries at foreign call sites.

---

## 2. Comprehensive Interoperability Matrix

| Ecosystem | Interoperability Mechanism | Memory & Ownership Boundary | Safety Gate |
| :--- | :--- | :--- | :--- |
| **C / C ABI** | Direct `extern "C"` foreign function interface | C ABI stack passing & explicit region alloc | Requires `! {Unsafe}` capability |
| **Rust** | Zero-overhead C ABI / `repr(C)` structs | Transfer of linear ownership | Capability-bounded FFI |
| **C++** | `extern "C"` bridge headers / `cxx` wrapper | Non-owning pointer passing | Quarantined in FFI module |
| **Python** | Embedded CPython runtime / PyO3 bridge | Reference counted Python object handles | Requires `! {Python}` capability |
| **JavaScript / TS** | WebAssembly Component Model & `.d.ts` export | TypedArray / WASM linear memory shared buffers | Sandboxed WASM boundaries |
| **WASM Components**| Standard WIT (WebAssembly Interface Types) | Canonical ABI value copying / linear memory | Zero-ambient sandbox |
| **Native Databases**| Direct socket wire protocols / C client libs | Parameterized binary buffers | Requires `! {Database}` capability |

---

## 3. The Foreign Capability Quarantine

Foreign code (C, C++, assembly) inherently violates memory safety. NOVA prevents foreign code from corrupting language invariants by enforcing the **Foreign Capability Quarantine**:

$$\text{Foreign Call } f \implies \text{Mandates } \texttt{! \{Unsafe\}}$$

```nova
// Foreign C function declaration
extern "C" {
    fn zlib_compress(dest: *mut Int, dest_len: *mut Int, src: *const Int, src_len: Int) -> Int;
}

// Safe NOVA wrapper encapsulating the Unsafe capability
fn compress_data(u: Unsafe, input: List[Int]) -> Result[List[Int], CompressionError] ! {Unsafe} {
    // Foreign C invocation permitted only because `u: Unsafe` capability is held:
    let code = zlib_compress(...);
    if code == 0 {
        Result::Ok(output)
    } else {
        Result::Err(CompressionError::Failed)
    }
}
```
