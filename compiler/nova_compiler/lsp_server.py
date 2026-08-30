"""Language Server Protocol (LSP) server for NOVA (`nova lsp`).

JSON-RPC 2.0 over stdio. Implemented today:
- Diagnostics on didOpen / didChange (runs the real checker)
- Keyword / capability / core-type completion
- Document formatting (delegates to `nova fmt`)

Not implemented (the `initialize` response no longer advertises these):
- Hover with real type/effect information
- Go-to-definition, find-references
"""
from __future__ import annotations

import json
import sys
import os
from typing import Any

from .driver import NovaCompiler
from .fmt import format_code


KEYWORDS = [
    "fn", "let", "mut", "if", "else", "while", "for", "in",
    "match", "struct", "enum", "trait", "impl", "import",
    "widen", "capability", "pub", "self",
]

# The capabilities that actually exist (std/prelude.nova).
CAPABILITIES = ["Runtime", "Clock", "Filesystem", "Network"]

STDLIB_TYPES = ["Int", "Bool", "String", "Unit", "Option", "Result", "List"]


class NovaLSPServer:
    def __init__(self) -> None:
        self.documents: dict[str, str] = {}
        self.compiler = NovaCompiler()

    def run(self) -> None:
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                if line.startswith("Content-Length:"):
                    length = int(line.split(":")[1].strip())
                    # Read empty line
                    sys.stdin.readline()
                    body = sys.stdin.read(length)
                    msg = json.loads(body)
                    self.handle_message(msg)
            except Exception as ex:
                break

    def send_response(self, response: dict[str, Any]) -> None:
        body = json.dumps(response)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        sys.stdout.write(header + body)
        sys.stdout.flush()

    def handle_message(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            self.send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {
                        "textDocumentSync": 1,  # Full sync
                        "completionProvider": {"triggerCharacters": [".", ":", " "]},
                        "documentFormattingProvider": True,
                    }
                }
            })

        elif method == "textDocument/didOpen":
            doc = params["textDocument"]
            uri = doc["uri"]
            text = doc["text"]
            self.documents[uri] = text
            self.publish_diagnostics(uri, text)

        elif method == "textDocument/didChange":
            doc = params["textDocument"]
            uri = doc["uri"]
            changes = params["contentChanges"]
            if changes:
                text = changes[0]["text"]
                self.documents[uri] = text
                self.publish_diagnostics(uri, text)

        elif method == "textDocument/completion":
            items = []
            for kw in KEYWORDS:
                items.append({"label": kw, "kind": 14, "detail": "keyword"})
            for cap in CAPABILITIES:
                items.append({"label": cap, "kind": 7, "detail": "system capability"})
            for ty in STDLIB_TYPES:
                items.append({"label": ty, "kind": 7, "detail": "core type"})

            self.send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": items
            })

        elif method == "textDocument/formatting":
            doc = params["textDocument"]
            uri = doc["uri"]
            text = self.documents.get(uri, "")
            formatted = format_code(text)
            self.send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": [{
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": len(text.splitlines()) + 1, "character": 0}
                    },
                    "newText": formatted
                }]
            })

        elif method == "shutdown":
            self.send_response({"jsonrpc": "2.0", "id": msg_id, "result": None})

    def publish_diagnostics(self, uri: str, text: str) -> None:
        # Publish diagnostics back to client
        diagnostics = []
        path = uri.replace("file://", "")
        unit, err = self.compiler.check_file(path)
        if err:
            diagnostics.append({
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 10}
                },
                "severity": 1,
                "message": err,
                "source": "nova-verifier"
            })

        self.send_response({
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": uri,
                "diagnostics": diagnostics
            }
        })
