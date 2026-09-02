# src/ — self-hosting sketch

**Status: ~90 lines of illustrative NOVA. Not a compiler.**

`src/compiler/*.nova`, `src/std/*.nova` and `src/tools/fmt.nova` are short
NOVA programs that *name* the stages of a self-hosted compiler. They
parse and type-check under the reference toolchain (that is the point —
they are valid NOVA), but they do no actual work: `main.nova` prints
"Lexing source stream..." and returns 0.

They exist as a target shape for a real self-hosting effort, which is a
**late** milestone — it needs a complete, stable language, a real native
backend, and a standard library first. See
[docs/platform/SELF-HOSTING.md](../docs/platform/SELF-HOSTING.md) for the
intent and [ROADMAP.md](../ROADMAP.md) for the ordering.

The authoritative compiler is the Python reference implementation in
[`verifier/refspec/`](../verifier/refspec/) and
[`compiler/nova_compiler/`](../compiler/nova_compiler/).
