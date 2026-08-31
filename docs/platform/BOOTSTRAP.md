# NOVA — Self-Hosting & Compiler Bootstrap Model

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
**Cross-References:** [SELF-HOSTING.md](SELF-HOSTING.md), [REPRODUCIBILITY-MODEL.md](REPRODUCIBILITY-MODEL.md), [COMPILER-ARCHITECTURE.md](../../compiler/README.md)

---

## 1. The 4-Stage Bootstrap Lifecycle

NOVA achieves complete self-hosting through a four-stage bootstrap sequence:

```
+---------------------------------------------------------------------------------------+
|                                 THE BOOTSTRAP LADDER                                  |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  [STAGE 0] Host Bootstrap Compiler                                                    |
|  • Reference verifier & native C/LLVM backend.                                         |
|  • Compiles the initial self-hosted compiler subset (`src/compiler/`).                 |
|                                │                                                      |
|                                ▼                                                      |
|  [STAGE 1] Self-Hosted Compiler (Stage 1 Binary)                                      |
|  • Written in NOVA (`src/compiler/*.nova`).                                           |
|  • Compiled into native machine code by Stage 0.                                       |
|  • Possesses complete language capability for lexing, parsing, and type checking.     |
|                                │                                                      |
|                                ▼                                                      |
|  [STAGE 2] Self-Recompilation & Fixed-Point Verification                              |
|  • Stage 1 compiler compiles `src/compiler/*.nova` to produce Stage 2 binary.          |
|  • Cryptographic verification: $\text{Digest}(\text{Stage 2}) \equiv \text{Digest}(\text{Stage 3})$.|
|                                │                                                      |
|                                ▼                                                      |
|  [STAGE 3] Self-Hosted Developer Toolchain                                             |
|  • Formatter (`src/tools/fmt.nova`), linter, docgen, test runner, and package manager  |
|    written natively in NOVA and compiled by the self-hosted Stage 2 compiler.          |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

---

## 2. Ken Thompson "Trusting Trust" Mitigation

To eliminate the risk of hidden backdoors in host compilers:
1. **Diverse Double-Compiling (DDC):** The self-hosted compiler source is compiled by two distinct compiler toolchains (Clang/LLVM and GCC backend pipelines).
2. **Fixed-Point Bit Identicality:** Stage 2 and Stage 3 native binaries must match bit-for-bit:
$$\text{SHA256}(\text{Binary}_{\text{Stage 2}}) \equiv \text{SHA256}(\text{Binary}_{\text{Stage 3}})$$
