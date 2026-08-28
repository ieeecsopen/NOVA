# NOVA — Architecture

## Two implementations, on purpose

Constitution Article IX requires every semantic rule to exist in two
places. NOVA satisfies this with two deliberately *different*
implementations of the same specification:

| | `verifier/refspec` | `compiler/` |
|---|---|---|
| Language | Python 3.11+ | Rust |
| Purpose | executable specification | production compiler |
| Optimized for | readability, direct correspondence to RFC typing rules | speed, diagnostics, incrementality |
| Speed | irrelevant | matters |
| Status | **implemented** | not started (needs toolchain) |

They are written in different languages so that a shared bug is less
likely. When they disagree, the specification is ambiguous — that is a bug
in the RFC, and is fixed there first.

The conformance suite in `tests/` is the arbiter. Both implementations run
it.

## Pipeline

```
source (.nova)
   │
   ├─ lex ────────────► tokens          (spans preserved throughout)
   │
   ├─ parse ──────────► CST ──► AST
   │
   ├─ resolve ────────► names bound, capability decls registered
   │
   ├─ CAPABILITY REACHABILITY  ◄── the NOVA-specific pass (RFC 0001 §4.3)
   │     computes caps(body) for every function and closure
   │
   ├─ typecheck ──────► types + effect rows, unification
   │     declared row  ==  inferred row     (equality, not subsumption)
   │
   ├─ [reference semantics stops here and evaluates]
   │
   ├─ lower ──────────► NOVA IR           (not designed — RFC pending)
   │
   ├─ optimize
   │
   └─ codegen ────────► native | wasm     (not designed)
```

Everything from `lower` onward is unbuilt and undesigned. Saying so is
Article XII.

## Why capability reachability is its own pass

It is tempting to fold effect derivation into type checking. It is kept
separate because:

1. It is the pass most likely to be wrong, and it is easier to test in
   isolation.
2. Its output — the set of capabilities reachable from each function body,
   including through closure captures — is independently useful. It is what
   an audit tool needs, and it is what the eventual budget and contract
   layers will consume.
3. It has no dependency on unification, so it can run before types are
   solved and give better errors when it fails.

## Repository layout

```
compiler/          Rust compiler (front end first). Not started.
runtime/           Native runtime + root capability implementation. Not started.
std/               Standard library, in NOVA. Not started.
verifier/refspec/  Executable reference semantics (Python). IMPLEMENTED.
tools/             CLI, formatter, audit tooling. Not started.
lsp/               Language server. Not started.
package-manager/   Not started.
tests/             Conformance suite — the shared arbiter. IMPLEMENTED.
examples/          Programs in NOVA Core.
benchmarks/        Empty; required before RFC 0001 can be Accepted.
docs/              Specification and notes.
RFC/               Design record.
playground/        Not started.
```

## Design constraints on the compiler (for when it is written)

These are decided now because they are hard to retrofit:

- **Spans everywhere.** Every AST node carries a byte range. Diagnostics
  are a feature (Article X), and a compiler that adds spans later never
  gets them right.
- **Queries, not phases, at the top level.** Incrementality (a stated
  priority) means the driver should be demand-driven, like `rustc`'s query
  system or Salsa. Retrofitting this is a rewrite.
- **No panics on malformed input.** The parser recovers and produces a
  partial tree; the LSP depends on this.
- **Interned capability ids.** Effect rows are sets of interned nominal
  ids, so row operations are small-integer set ops.
- **The reference semantics is not a fallback.** It is never shipped as
  the compiler. It exists to disagree.

## Open architectural questions

- The IR. Nothing is decided. LLVM, Cranelift, MLIR, and a bespoke SSA IR
  are all live options, and the choice interacts with the WASM Component
  Model target. No RFC yet.
- Separate compilation of row-polymorphic functions (RFC 0001 §11.5).
- Whether `std` can be written in NOVA Core before generics exist. It
  probably cannot, which means generics (RFC 0003) blocks `std`.
