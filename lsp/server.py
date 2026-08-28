"""NOVA Language Server Protocol entrypoint."""
import sys
from compiler.nova_compiler.lsp_server import NovaLSPServer

if __name__ == "__main__":
    server = NovaLSPServer()
    server.run()
