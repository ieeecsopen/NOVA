#!/usr/bin/env python3
"""Smoke test: `nova lsp` speaks enough LSP for the VS Code client.

Runs `nova lsp`, sends `initialize`, `didOpen` (a program the checker
rejects), and `completion`, and asserts the server answers each. Exits
non-zero on any missing response.

Usage:  python3 editors/vscode/test/lsp_smoke.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
NOVA = os.path.join(REPO_ROOT, "nova")
NOVA_COMMAND = ([sys.executable, "-m", "compiler.nova_compiler.cli", "lsp"]
                if os.name == "nt" else [NOVA, "lsp"])

BAD_PROGRAM = "fn f(c: Clock) -> Int ! {} {\n    c.now()\n}\n"


def frame(obj: dict) -> bytes:
    body = json.dumps(obj).encode()
    return b"Content-Length: %d\r\n\r\n%s" % (len(body), body)


def parse_frames(data: bytes) -> list[dict]:
    out: list[dict] = []
    i = 0
    marker = b"Content-Length:"
    while True:
        h = data.find(marker, i)
        if h == -1:
            break
        nl = data.find(b"\r\n\r\n", h)
        if nl == -1:
            break
        length = int(data[h + len(marker):nl].strip().split(b"\r\n")[0])
        start = nl + 4
        body = data[start:start + length]
        try:
            out.append(json.loads(body))
        except json.JSONDecodeError:
            pass
        i = start + length
    return out


def main() -> int:
    with tempfile.NamedTemporaryFile(suffix=".nova", delete=False, mode="w") as tf:
        tf.write(BAD_PROGRAM)
        bad_path = tf.name

    try:
        proc = subprocess.Popen(
            NOVA_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=REPO_ROOT)
        msgs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"capabilities": {}}},
            {"jsonrpc": "2.0", "method": "textDocument/didOpen",
             "params": {"textDocument": {
                 "uri": "file://" + bad_path, "languageId": "nova",
                 "version": 1, "text": BAD_PROGRAM}}},
            {"jsonrpc": "2.0", "id": 2, "method": "textDocument/completion",
             "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": {}},
        ]
        stdout, stderr = proc.communicate(
            b"".join(frame(m) for m in msgs), timeout=15)
    finally:
        os.unlink(bad_path)

    frames = parse_frames(stdout)
    init = any(f.get("id") == 1 and "capabilities" in f.get("result", {})
               for f in frames)
    comp = any(f.get("id") == 2 and isinstance(f.get("result"), list)
               and len(f["result"]) > 0 for f in frames)
    completion_items = next((f["result"] for f in frames if f.get("id") == 2 and isinstance(f.get("result"), list)), [])
    option_entries = [item for item in completion_items if item.get("label") == "Option"]
    rich_meta = bool(option_entries and option_entries[0].get("detail") and option_entries[0].get("documentation"))
    diag = any(f.get("method") == "textDocument/publishDiagnostics"
               and f.get("params", {}).get("diagnostics")
               for f in frames)

    print(f"frames received:            {len(frames)}")
    print(f"initialize response:        {'OK' if init else 'MISSING'}")
    print(f"completion response:        {'OK' if comp else 'MISSING'}")
    print(f"rich completion metadata:    {'OK' if rich_meta else 'MISSING'}")
    print(f"diagnostics for bad program:{'OK' if diag else 'MISSING'}")
    if not stdout:
        print("stderr:", stderr.decode(errors="replace")[:500])

    ok = init and comp and rich_meta and diag
    print("\nPASS" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
