# NOVA — The One-Page Architecture Model

**Status:** Official Foundation Reference  
**Cross-References:** [LANGUAGE-CONSTITUTION.md](LANGUAGE-CONSTITUTION.md), [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md), [PROGRAM-MODEL.md](PROGRAM-MODEL.md)

---

```
+---------------------------------------------------------------------------------------+
|                                    NOVA AT A GLANCE                                   |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  1. LANGUAGE = CAPABILITIES + EFFECTS + REGIONS                                       |
|  • Pure code by default; functions declare what authority they need (`rt: Runtime`).  |
|  • Effects are typed rows: `fn query() -> Result[User, Error] ! {Database}`.          |
|  • Memory is governed by Region XOR: Shared Read XOR Exclusive Write.                 |
|                                                                                       |
|  2. COMPILER & RUNTIME = FAST & HERMETIC                                              |
|  • Native C99/LLVM native backend (`clang -O3`) & WebAssembly target.                 |
|  • Clean compile in ~44ms; sub-millisecond incremental cache (< 1ms).                 |
|  • Native binaries ~33 KB; structured diagnostics with actionable error pointers.     |
|                                                                                       |
|  3. FULL-STACK UNIFICATION                                                            |
|  • One nominal definition projects to Frontend WASM, API, Backend, and Database SQL.  |
|  • Zero code duplication across architectural tiers.                                  |
|                                                                                       |
|  4. CONCURRENCY & AI GOVERNANCE                                                       |
|  • Structured concurrency (`parallel {}`, `race {}`) prevents orphan background tasks. |
|  • AI agents operate under hard lexical budget envelopes (`cost < $0.10`).            |
|                                                                                       |
|  5. LANGUAGE-NATIVE OBSERVABILITY                                                     |
|  • Effect rows automatically synthesize OpenTelemetry trace spans with zero drift.   |
|                                                                                       |
+---------------------------------------------------------------------------------------+
```
