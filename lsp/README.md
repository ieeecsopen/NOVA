# NOVA Language Server

A minimal LSP server. The implementation lives in
[`compiler/nova_compiler/lsp_server.py`](../compiler/nova_compiler/lsp_server.py);
`lsp/server.py` here is a thin `python3 -m lsp.server` entry point that
delegates to it.

## Implemented today

* **Diagnostics** on `didOpen` / `didChange` — runs the real checker and
  reports the rendered error.
* **Completion** — keywords, the four prelude capabilities (`Runtime`,
  `Clock`, `Filesystem`, `Network`), and core type names.
* **Formatting** — `textDocument/formatting`, delegates to `nova fmt`.

## Not implemented

* Hover with real type / effect-row information.
* Go-to-definition, find-references, rename.
* Incremental sync (the server takes full-document sync only).

These are straightforward follow-ups against the existing checker, and
are good contributor tasks.

## Running

```bash
nova lsp                 # via the toolchain
python3 -m lsp.server    # directly
```

See [`editors/vscode/`](../editors/vscode/) for the VS Code extension
(syntax grammar + a client that launches `nova lsp`).
