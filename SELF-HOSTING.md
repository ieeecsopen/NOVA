# NOVA — Self-Hosted Compiler Architecture

**Status:** Production Design Reference  
**Cross-References:** [BOOTSTRAP.md](BOOTSTRAP.md), [compiler/README.md](compiler/README.md), [DEVELOPER-EXPERIENCE.md](DEVELOPER-EXPERIENCE.md)

---

## 1. Directory Structure of Self-Hosted Source (`src/`)

```
src/
├── std/
│   ├── collections.nova       # Core collections & data structure helpers
│   └── io.nova                # Capability-guarded I/O primitives
├── compiler/
│   ├── ast.nova               # Typed AST data node definitions
│   ├── lexer.nova             # Tokenizer with source span tracking
│   ├── parser.nova            # Recursive-descent parser
│   ├── typecheck.nova         # Type, effect, and capability verifier
│   └── main.nova              # Self-hosted compiler entrypoint
└── tools/
    └── fmt.nova               # Self-hosted canonical source code formatter
```

---

## 2. Bootstrapping Commands

```bash
# 1. Compile Stage 1 self-hosted compiler using Stage 0 native toolchain
./nova build src/compiler/main.nova -o bin/nova_stage1

# 2. Stage 1 compiles itself to produce Stage 2 binary
./bin/nova_stage1 src/compiler/main.nova -o bin/nova_stage2

# 3. Verify cryptographic fixed point
diff <(shasum -a 256 bin/nova_stage1) <(shasum -a 256 bin/nova_stage2)
```
