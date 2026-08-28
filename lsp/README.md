# NOVA Language Server Protocol (LSP)

The official Language Server Protocol implementation for the NOVA programming language.

---

## 1. Capabilities Supported

* **Diagnostics:** Inline compiler error reporting on open/edit/save with span underlines (`textDocument/publishDiagnostics`).
* **Autocomplete:** Context-aware completion for keywords, capability identifiers (`Clock`, `Filesystem`, `Network`), types, and stdlib helpers (`textDocument/completion`).
* **Hover:** Type signature and inferred effect row inspection (`textDocument/hover`).
* **Formatting:** Canonical 4-space indentation and effect row formatting (`textDocument/formatting`).
* **Go-to-Definition & References:** Symbol navigation (`textDocument/definition`).

---

## 2. Running the LSP Server

```bash
nova lsp
```
or directly via Python:
```bash
python3 -m lsp.server
```

---

## 3. Editor Integration

See `editors/vscode/` for the complete VS Code extension manifest, syntax grammar, and language configuration.
