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

# Semantic hover information for keywords, capabilities, and types.
HOVER_INFO: dict[str, str] = {
    # Keywords
    "fn": "**`fn`** — Declare a function.\n\n```nova\nfn name(params) -> ReturnType ! {Effects} { body }\n```",
    "let": "**`let`** — Bind a value (immutable by default).\n\n```nova\nlet x = 42;\nlet mut y = 0;  // mutable binding\n```",
    "mut": "**`mut`** — Mark a binding or parameter as mutable.",
    "if": "**`if`** — Conditional expression.\n\n```nova\nif condition { then_branch } else { else_branch }\n```",
    "else": "**`else`** — Alternative branch of an `if` expression.",
    "while": "**`while`** — Loop while a condition is true.\n\n```nova\nwhile condition { body }\n```",
    "for": "**`for`** — Iterate over a collection.\n\n```nova\nfor item in collection { body }\n```",
    "in": "**`in`** — Used with `for` loops to specify the collection to iterate.",
    "match": "**`match`** — Pattern matching expression.\n\n```nova\nmatch value {\n    Pattern1 => expr1,\n    Pattern2 => expr2,\n}\n```",
    "struct": "**`struct`** — Define a product type (record).\n\n```nova\nstruct Point { x: Int, y: Int }\n```",
    "enum": "**`enum`** — Define a sum type (tagged union).\n\n```nova\nenum Option[T] { Some(T), None }\n```",
    "trait": "**`trait`** — Define a trait (interface).",
    "impl": "**`impl`** — Implement a trait for a type.",
    "import": "**`import`** — Import a module.\n\n```nova\nimport std.list;\n```",
    "capability": "**`capability`** — Declare a capability type.\n\nCapabilities represent authority to perform effects (I/O, time, etc.).",
    "pub": "**`pub`** — Mark an item as publicly visible outside its module.",
    "self": "**`self`** — Reference to the current instance in trait implementations.",
    "widen": "**`widen`** — Explicitly widen an effect row to include additional capabilities.",
    "intent": "**`intent`** — Declare the behavioral intent (contract) of a function.",
    "requires": "**`requires`** — Specify a precondition that must hold at function entry.",
    "ensures": "**`ensures`** — Specify a postcondition that must hold at function exit.",
    # Capabilities
    "Runtime": "**`Runtime`** — Root capability.\n\nProvides access to all system capabilities. Passed to `main()` as the single ambient authority.",
    "Clock": "**`Clock`** — Time capability.\n\nGrants the ability to read the current time. Effect: `! {Clock}`.",
    "Filesystem": "**`Filesystem`** — File I/O capability.\n\nGrants read/write access to the filesystem. Effect: `! {Filesystem}`.",
    "Network": "**`Network`** — Network capability.\n\nGrants the ability to make network requests. Effect: `! {Network}`.",
    # Core types
    "Int": "**`Int`** — Signed integer type (arbitrary precision).",
    "Bool": "**`Bool`** — Boolean type (`true` or `false`).",
    "String": "**`String`** — UTF-8 string type.",
    "Unit": "**`Unit`** — The unit type, equivalent to `()`. Used for functions with no meaningful return value.",
    "Option": "**`Option[T]`** — Optional value.\n\n```nova\nenum Option[T] { Some(T), None }\n```",
    "Result": "**`Result[T, E]`** — Result of an operation that may fail.\n\n```nova\nenum Result[T, E] { Ok(T), Err(E) }\n```",
    "List": "**`List[T]`** — Singly-linked list.\n\n```nova\nenum List[T] { Cons(T, List[T]), Nil }\n```",
}


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
        body = json.dumps(response).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        sys.stdout.buffer.write(header + body)
        sys.stdout.buffer.flush()

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
                        "hoverProvider": True,
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

        elif method == "textDocument/hover":
            doc = params["textDocument"]
            uri = doc["uri"]
            pos = params["position"]
            text = self.documents.get(uri, "")
            lines = text.splitlines()
            line_idx = pos["line"]
            char_idx = pos["character"]
            word = self._word_at(lines, line_idx, char_idx)
            hover_text = HOVER_INFO.get(word) if word else None
            if hover_text:
                self.send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": {"kind": "markdown", "value": hover_text}
                    }
                })
            else:
                self.send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": None
                })

        elif method == "shutdown":
            self.send_response({"jsonrpc": "2.0", "id": msg_id, "result": None})

    @staticmethod
    def _word_at(lines: list[str], line: int, char: int) -> str | None:
        """Extract the word (identifier) at the given (line, char) position."""
        if line < 0 or line >= len(lines):
            return None
        text = lines[line]
        if char < 0 or char >= len(text):
            return None
        if not (text[char].isalnum() or text[char] == '_'):
            return None
        # Walk left
        start = char
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
            start -= 1
        # Walk right
        end = char
        while end < len(text) - 1 and (text[end + 1].isalnum() or text[end + 1] == '_'):
            end += 1
        return text[start:end + 1]

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
