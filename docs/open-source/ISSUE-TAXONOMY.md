# NOVA — GitHub Issue & Label Taxonomy

**Status:** Official Label & Taxonomy Reference  
**Cross-References:** [CONTRIBUTING.md](../../CONTRIBUTING.md), [GOVERNANCE.md](../../GOVERNANCE.md)

---

## 1. Area Labels (`area:*`)

Used to route issues and pull requests to specific domain working groups:

* `area:language` — Syntax, grammar, keywords, language evolution
* `area:type-system` — Type inference, unification, generics, traits
* `area:effects` — Effect rows, pure defaults, effect polymorphism
* `area:capabilities` — Object capabilities, reachability analysis, unforgeable tokens
* `area:memory` — Region XOR memory model, borrowing, lifetimes, drop elaboration
* `area:compiler` — AST, HIR, MIR, optimizations, C99/LLVM codegen
* `area:runtime` — Task scheduler, memory frames, execution engine, observability
* `area:concurrency` — Tasks, work-stealing, message channels, structured sync
* `area:wasm` — WebAssembly target, WASI preview2, Component Model
* `area:full-stack` — Reactive VNodes, client/server boundaries, shared data entities
* `area:distributed` — RPC, node discovery, replication sagas, failure semantics
* `area:ai` — AI primitive integration, autonomous agent sandboxes, budget envelopes
* `area:verification` — Intent contracts (`requires`, `ensures`), SMT proofs, fuzzing
* `area:tooling` — CLI (`nova`), LSP server, formatter, linter, VS Code extension
* `area:package-manager` — Manifest (`nova.toml`), lockfile, dependency resolution
* `area:stdlib` — Standard prelude, collections, I/O, core library types
* `area:security` — Security audits, threat modeling, vulnerability assessments
* `area:benchmarks` — Challenge benchmark suite, performance telemetry, profiling
* `area:documentation` — Architecture specifications, guides, tutorials, API docs

---

## 2. Type Labels (`type:*`)

* `type:feature` — New capabilities or architectural implementations
* `type:bug` — Unexpected failure, compiler crash, or spec divergence
* `type:refactor` — Code cleanup or IR restructuring without behavior changes
* `type:test` — Conformance, property, fuzz, or regression test additions
* `type:research` — Exploratory investigation producing empirical reports or RFCs
* `type:rfc` — Language design proposal requiring community discussion
* `type:security` — Security vulnerability or sandboxing flaw
* `type:tooling` — Developer CLI, LSP, or CI infrastructure enhancements

---

## 3. Priority Labels (`priority:*`)

* `priority:critical` — Blocks core compilation, sound verification, or security integrity
* `priority:high` — Blocks an active milestone or major production feature
* `priority:medium` — Standard scheduled enhancement or defect fix
* `priority:low` — Minor ergonomic improvement or cosmetic polish

---

## 4. Status Labels (`status:*`)

* `status:good-first-issue` — Beginner-friendly task with isolated scope
* `status:help-wanted` — Well-specified task ready for community contribution
* `status:ready` — Fully specified task unblocked and ready for immediate work
* `status:in-progress` — An active contributor is currently developing this
* `status:blocked` — Blocked by an unresolved dependency or upstream RFC
* `status:needs-design` — Requires architectural discussion before implementation

---

## 5. Complexity Labels (`size:*`)

* `size:small` — Can be completed in < 1 day (~50–150 LOC)
* `size:medium` — Multi-day task (~150–500 LOC)
* `size:large` — Multi-week subsystem (~500–2,000 LOC)
* `size:research` — Open-ended investigation requiring proof or prototype
