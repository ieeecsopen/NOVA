# NOVA Native Compiler (`nova`)

The production native compiler for the NOVA programming language.

---

## 1. Compiler Architecture Pipeline

```
Source (.nova)
     │
     ▼
Lexer (Tokenizer with span tracking)
     │
     ▼
Parser (Recursive-descent producing AST)
     │
     ▼
AST (Spans, Node IDs, Type Expressions)
     │
     ▼
Name Resolution & Module Resolution (std.* + relative imports)
     │
     ▼
Type Checking & Effect Inference
     │
     ▼
Capability Reachability Analysis (Transitive closure capture validation)
     │
     ▼
High-Level Intermediate Representation (HIR)
     │ (Desugars pattern matches, monomorphizes generics, explicit captures)
     ▼
Mid-Level Intermediate Representation (MIR)
     │ (Control Flow Graph, Basic Blocks, SSA, Linear Drop Elaboration)
     ▼
C / LLVM Native Backend (`clang -O3`)
     │ (Generates machine code, links capability runtime)
     ▼
Native Executable (arm64 / x86_64 ELF/Mach-O)
```

---

## 2. Compiler Toolchain Commands

The `nova` binary provides the complete developer toolchain:

### Type Check & Verify
```bash
nova check <file.nova>
```
Validates syntax, type unification, and static capability reachability without code generation.

### Build Native Executable
```bash
nova build <file.nova> [-o output_binary] [--clean]
```
Compiles source into an optimized native machine binary with incremental SHA-256 caching (`.nova_cache/`).

### Run Program
```bash
nova run <file.nova> [args...]
```
Compiles and executes the native binary with zero developer friction.

### Benchmark Compilation & Runtime
```bash
nova bench <file.nova>
```
Measures clean compile time, incremental compile time, binary size, and native execution latency.

---

## 3. Benchmark Snapshot

On Apple Silicon (M-series / Apple Clang):
* **Clean Compile Time:** ~40–60 ms
* **Incremental (Cached) Build:** ~0.25 ms
* **Native Execution Time:** ~1.5–3.0 ms
* **Binary Size:** ~33 KB (stripped standalone native executable)

---

## 4. Diagnostics Engine

Errors pinpoint exact source spans and emit actionable diagnostics with structural components:
* **What:** Exact invariant breached (e.g. `E0105: closure captures un-annotated capability`).
* **Where:** Source file, line, and column span pointer.
* **Why:** The capability reference reached inside the function body.
* **Fix:** Add the required effect label to the function signature or remove the capability capture.
