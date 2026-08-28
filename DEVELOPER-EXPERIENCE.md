# NOVA — Developer Experience (DX) & Toolchain Evaluation

**Status:** Production Design Reference  
**Cross-References:** [ARCHITECTURE.md](ARCHITECTURE.md), [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md), [SECURITY-MODEL.md](SECURITY-MODEL.md)

---

## 1. Toolchain Philosophy

A modern programming language cannot succeed as a bare compiler alone. A language is an ecosystem consisting of:

$$\text{Language} = \text{Core Syntax} + \text{Compiler} + \text{Runtime} + \text{Toolchain} + \text{Ecosystem}$$

NOVA ships with a unified toolchain CLI (`nova`) providing first-class formatting, linting, testing, documentation generation, package management, and Language Server Protocol integration out of the box.

---

## 2. DX Evaluation Across Core Dimensions

| Dimension | Evaluation & Architectural Decision | Developer Impact |
| :--- | :--- | :--- |
| **1. Learning Curve** | **Low.** Purity is the default; authority arrives as normal argument values. No named lifetime syntax (`'a`) or ambient global state to memorize. | Developers productive on Day 1 with familiar Rust/TypeScript-like syntax. |
| **2. Error Quality** | **Exemplary.** Compiler diagnostics state *What*, *Why*, *Where*, and *Possible Fixes* with exact ASCII span pointers. | Eliminates guesswork; errors suggest exact effect row annotations. |
| **3. Autocomplete Quality** | **Context-Aware.** The LSP knows which capabilities are reachable in current scope and autocompletes only valid capability methods. | Prevents writing code that attempts unheld capability effects. |
| **4. Formatting Consistency** | **Deterministic (`nova fmt`).** Single canonical formatter with zero configurable stylistic flags. | Eliminates code review formatting debates across teams. |
| **5. Build Speed** | **Fast.** Clean compile in ~40ms; incremental SHA-256 cached builds in < 1ms (`.nova_cache/`). | Sub-millisecond edit-compile-test inner loop. |
| **6. Dependency Management** | **Secure & Explicit (`nova add`).** Dependencies must declare required capabilities in `nova.toml`. | Supply-chain attacks statically prevented before compilation. |
| **7. Debugging Integration** | **Traceable & Drift-Free.** Effect rows derive execution spans without hand-written manual log drift (`docs/experiments/002-rows-to-spans.md`). | Clean execution traces and deterministic replay. |

---

## 3. Unified Toolchain Reference Table

| Command | Subsystem | Description |
| :--- | :--- | :--- |
| **`nova check <file>`** | Verifier | Static type checking, row unification, and capability reachability pass. |
| **`nova build <file>`** | Compiler | Compiles source to optimized native binary via C/LLVM backend (`clang -O3`). |
| **`nova run <file>`** | Runner | Compiles and executes a native NOVA program with zero friction. |
| **`nova test [pattern]`** | Test Runner | Discovers and executes conformance, unit, and security test suites. |
| **`nova fmt [files...]`** | Formatter | Canonical code formatting with automatic indentation and effect row normalization. |
| **`nova lint [files...]`** | Linter | Static analysis for naming conventions, style, and unused variables. |
| **`nova doc [path]`** | DocGen | Extracts types, docstrings, and capability signatures into Markdown API docs. |
| **`nova add <pkg>`** | Package Mgr | Declares dependency with explicit required capability bounds in `nova.toml`. |
| **`nova remove <pkg>`**| Package Mgr | Removes dependency from `nova.toml`. |
| **`nova lsp`** | LSP Server | Runs Language Server Protocol server over JSON-RPC 2.0 stdio. |
| **`nova bench <file>`** | Benchmark | Measures clean vs incremental compile times, binary size, and native execution latency. |
