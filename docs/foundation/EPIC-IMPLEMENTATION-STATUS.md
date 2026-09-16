# NOVA Epic Implementation Status

**Status:** Ratified implementation boundary (2026-09-10)

This document records what is executable in the repository and what remains
design-only for the open full-stack, AI, adaptive-execution, provenance, and
compiler-backend issues. It prevents examples and design reports from being
mistaken for shipped runtime subsystems.

The current shipped implementation is the Python reference frontend and
interpreter in [`verifier/refspec/`](../../verifier/refspec/), the developer
CLI and first-order native C backend in
[`compiler/nova_compiler/`](../../compiler/nova_compiler/), and the standalone
Region XOR prototype in [`regionlab/`](../../regionlab/). See the ratified
[authority map](AUTHORITY-MAP.md) for ownership and PR routing.

## Status matrix

| Issue | Executable evidence | Current boundary | Smallest next implementation |
| :--- | :--- | :--- | :--- |
| #4 Full-stack platform | [`examples/enterprise-platform.nova`](../../examples/enterprise-platform.nova) checks and runs through the reference interpreter. | VNode, RPC, database, distributed transaction, serialization, and telemetry behavior are simulated by nominal structs and `Runtime.print`; no tier runtime exists. | Define one shared serialization contract and implement one end-to-end projection before claiming cross-tier execution. |
| #5 AI governance | [`examples/real-world/08_ai_agent.nova`](../../examples/real-world/08_ai_agent.nova) checks and runs as ordinary NOVA code. | No AI model primitive, tool executor, lexical AI capability, token meter, financial meter, or deterministic budget runtime exists. | Specify and implement one capability-gated budgeted primitive with an executable host boundary. |
| #29 Prompt-injection security | Generic conformance and interpreter security tests exist. | There is no AI tool-calling layer or schema validator to attack, so an injection-resistance claim cannot yet be tested end to end. | Land the AI tool-call contract first, then add adversarial fixtures for unauthorized tools, schema confusion, and budget escape. |
| #32 Adaptive dispatch solver | Research references live under [`docs/adaptive/`](../adaptive/). | No strategy selector, cost model, hardware sampler, remote dispatcher, or benchmarked solver exists. | Implement a deterministic pure decision function over an explicit cost/signal record, then benchmark it. |
| #36 Provenance ledger | Design documents exist under [`docs/ai/`](../ai/). | No ledger serializer, cryptographic signature path, replay harness, or model execution integration exists. | Freeze a versioned record schema and add round-trip/signature verification before integrating model calls. |
| #43 MIR and LLVM | [`hir.py`](../../compiler/nova_compiler/hir.py) and [`mir.py`](../../compiler/nova_compiler/mir.py) expose informational lowering classes. | HIR/MIR are not on the execution path; MIR lowering is partial, direct LLVM/bitcode emission is absent, and unsupported builds use the reference interpreter or fail closed for WASM/WASI. | Add verified HIR/MIR fixtures for the supported subset, then expand CFG lowering before direct LLVM emission. |

## Reproducible checks

From the repository root:

```text
python -m verifier.refspec check examples/enterprise-platform.nova
python -m verifier.refspec run examples/enterprise-platform.nova
python -m verifier.refspec check examples/real-world/08_ai_agent.nova
python -m verifier.refspec run examples/real-world/08_ai_agent.nova
python -m compiler.nova_compiler.cli build examples/enterprise-platform.nova -o /tmp/enterprise-platform
```

The first four commands prove frontend/interpreter behavior only. Their output
contains simulated tier messages; it is not evidence of a WASM renderer, RPC
transport, database coordinator, model invocation, or budget meter. The build
command reports an interpreter-backed runner for constructs outside the native
C subset.

For compiler work, `--emit-hir` and `--emit-mir` are diagnostic lowerings. They
must not be described as direct LLVM, production MIR, or a native full-stack
backend until the corresponding execution path and tests exist.

## PR routing

These issues should not be implemented as one cross-cutting patch:

- #4, #5, #29, #32, and #36 each require a new runtime contract and focused
  tests before their definitions of done can be claimed.
- #43 owns the compiler IR/backend path and should proceed in stages: verified
  HIR/MIR fixtures, complete CFG lowering, then direct LLVM/bitcode emission.
- A PR may update this status document when evidence changes, but it must not
  promote a design document or printed example output to an implementation
  claim.
