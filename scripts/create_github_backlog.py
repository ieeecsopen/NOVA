#!/usr/bin/env python3
"""Script to initialize GitHub labels, milestones, and issue backlog for NOVA.
Uses GitHub CLI (`gh`).
"""
import json
import subprocess
import sys
import time

REPO = "ieeecsopen/NOVA"

LABELS = [
    # Area Labels
    ("area:language", "0075ca", "Syntax, grammar, keywords, language evolution"),
    ("area:lexer", "0e8a16", "Lexical analysis and tokenization"),
    ("area:parser", "1d76db", "Grammar parsing and AST construction"),
    ("area:type-system", "5319e7", "Type inference, unification, generics, traits"),
    ("area:memory", "d93f0b", "Region XOR memory model, borrowing, drop elaboration"),
    ("area:ownership", "e99695", "Linear affine types & borrow semantics"),
    ("area:effects", "bfd4f2", "Effect rows, pure defaults, effect polymorphism"),
    ("area:capabilities", "b60205", "Object capabilities, reachability, unforgeable tokens"),
    ("area:errors", "d4c5f9", "Result/Option algebraic error handling"),
    ("area:contracts", "0052cc", "Design-by-Contract (requires, ensures, invariants)"),
    ("area:verification", "1d76db", "Static verification, SMT solver proofs, fuzzing"),
    ("area:compiler", "fbca04", "AST, HIR, MIR, optimizations, C99/LLVM codegen"),
    ("area:ir", "fef2c0", "Intermediate representations (HIR, MIR)"),
    ("area:backend", "c2e0c6", "Code emission (C99, LLVM, machine code)"),
    ("area:runtime", "0e8a16", "Task scheduler, memory frames, execution engine"),
    ("area:concurrency", "1d76db", "Tasks, work-stealing, message channels, sync"),
    ("area:wasm", "6f42c1", "WebAssembly target, WASI preview2, Component Model"),
    ("area:distributed", "006b75", "RPC, node discovery, replication sagas, failure"),
    ("area:resources", "d4c5f9", "Resource semirings, token/cost budgets, metering"),
    ("area:temporal", "fef2c0", "Freshness, staleness, deadlines, monotonic clocks"),
    ("area:uncertainty", "e11d48", "Epistemic certainty & prediction states"),
    ("area:ai", "7c3aed", "AI computational primitives & model integrations"),
    ("area:agents", "a855f7", "Autonomous agent governance & sandbox budgets"),
    ("area:frontend", "38bdf8", "Reactive WASM frontend components & VNodes"),
    ("area:backend-platform", "0284c7", "Type-safe RPC gateways & HTTP services"),
    ("area:data", "059669", "Persistent entities & ACID transactions"),
    ("area:full-stack", "10b981", "Unified client-server-database architecture"),
    ("area:tooling", "f59e0b", "Developer CLI (nova), LSP, formatter, linter"),
    ("area:lsp", "d97706", "Language Server Protocol implementation"),
    ("area:package-manager", "b45309", "Package manifest (nova.toml), lockfile, dependency resolution"),
    ("area:stdlib", "84cc16", "Standard prelude, collections, I/O, core library"),
    ("area:security", "dc2626", "Security audits, threat modeling, vulnerability assessments"),
    ("area:observability", "6366f1", "Distributed telemetry, tracing & OpenTelemetry spans"),
    ("area:self-hosting", "4f46e5", "4-Stage self-hosting compiler & bootstrap ladder"),
    ("area:benchmarks", "8b5cf6", "Challenge benchmark suite & performance telemetry"),
    ("area:documentation", "0075ca", "Architecture specifications, guides, tutorials, API docs"),
    ("area:infrastructure", "475569", "CI/CD pipelines, workflows, build automation"),

    # Type Labels
    ("type:feature", "a2eeef", "New capabilities or architectural implementations"),
    ("type:bug", "d73a4a", "Unexpected failure, compiler crash, or spec divergence"),
    ("type:refactor", "e4e669", "Code cleanup or IR restructuring without behavior changes"),
    ("type:test", "c5def5", "Conformance, property, fuzz, or regression test additions"),
    ("type:documentation", "0075ca", "Improvements or additions to documentation"),
    ("type:research", "7057ff", "Exploratory investigation producing empirical reports or RFCs"),
    ("type:rfc", "d876e3", "Language design proposal requiring community discussion"),
    ("type:benchmark", "fef2c0", "Performance measurement or benchmark harness"),
    ("type:security", "b60205", "Security vulnerability or sandboxing flaw"),
    ("type:tooling", "fbca04", "Developer CLI, LSP, or CI infrastructure enhancements"),

    # Priority Labels
    ("priority:critical", "b60205", "Blocks core compilation, sound verification, or security integrity"),
    ("priority:high", "d93f0b", "Blocks an active milestone or major production feature"),
    ("priority:medium", "fbca04", "Standard scheduled enhancement or defect fix"),
    ("priority:low", "0e8a16", "Minor ergonomic improvement or cosmetic polish"),

    # Status Labels
    ("status:good-first-issue", "7057ff", "Beginner-friendly task with isolated scope"),
    ("status:help-wanted", "008672", "Well-specified task ready for community contribution"),
    ("status:research", "7c3aed", "Research investigation in progress"),
    ("status:discussion", "d876e3", "Requires community consensus before proceeding"),
    ("status:needs-design", "f59e0b", "Requires architectural RFC before implementation"),
    ("status:blocked", "b60205", "Blocked by an unresolved dependency or upstream RFC"),
    ("status:ready", "0e8a16", "Fully specified task unblocked and ready for immediate work"),

    # Size Labels
    ("size:small", "c2e0c6", "Small task (< 1 day, ~50-150 LOC)"),
    ("size:medium", "fef2c0", "Medium task (multi-day, ~150-500 LOC)"),
    ("size:large", "e99695", "Large subsystem (multi-week, ~500-2000 LOC)"),
    ("size:research", "d4c5f9", "Research investigation producing report/prototype"),
]

MILESTONES = [
    ("M0 — Foundation", "Repository architecture, governance, license, RFC process, CI matrix."),
    ("M1 — Core Language", "Grammar stabilization, AST node span attribution, parser precedence."),
    ("M2 — Type System & Safety", "Hindley-Milner inference, row-typed effect join lattice, Region XOR invariant."),
    ("M3 — Compiler & IR", "AST -> HIR -> MIR lowering, basic block CFG constructor, drop elaboration."),
    ("M4 — Runtime", "Memory frames, Region XOR allocator, error propagation, OpenTelemetry spans."),
    ("M5 — Toolchain", "nova CLI (new, dev, check, build, run, test, fmt, lint, doc, lsp)."),
    ("M6 — WASM", "WebAssembly Component Model backend, WASI preview2 capability bindings."),
    ("M7 — Concurrency", "Chase-Lev work-stealing scheduler, structured parallel/race, channels."),
    ("M8 — Full-Stack", "Shared nominal entities, reactive WASM VNode UI, type-safe RPC gateways."),
    ("M9 — Distributed", "Saga coordinators, consensus replicas, explicit network failure semantics."),
    ("M10 — Resources / Time / Uncertainty", "4-tier resource semirings, clock freshness, epistemic uncertainty."),
    ("M11 — AI", "Sandboxed autonomous agents, zero implicit authority, financial budget ceilings."),
    ("M12 — Verification", "Design-by-Contract (requires/ensures), SMT solver integration, Lean 4 proofs."),
    ("M13 — Adaptive Execution", "Research-grade multi-strategy dispatch (CPU, GPU, WASM, Remote Cluster)."),
    ("M14 — Self-Hosting", "4-stage bootstrap ladder (Stage 0 Host -> Stage 3 Bit-Identical Binary)."),
    ("M15 — Production / 1.0", "SemVer 2.0.0 stability guarantees, security audit sign-off, public challenge suite."),
]


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout + res.stderr


def sync_labels():
    print("Syncing labels...")
    for name, color, desc in LABELS:
        code, out = run_cmd(["gh", "label", "create", name, "--repo", REPO, "--color", color, "--description", desc, "--force"])
        if code == 0:
            print(f"  ✓ Label: {name}")
        else:
            print(f"  ✗ Failed label {name}: {out.strip()}")


def sync_milestones() -> dict[str, int]:
    print("Syncing milestones...")
    milestone_map = {}
    
    # Check existing milestones
    code, out = run_cmd(["gh", "api", f"repos/{REPO}/milestones"])
    if code == 0 and out.strip():
        try:
            existing = json.loads(out)
            for m in existing:
                milestone_map[m["title"]] = m["number"]
        except Exception:
            pass

    for title, desc in MILESTONES:
        if title in milestone_map:
            print(f"  ✓ Milestone exists: {title} (#{milestone_map[title]})")
            continue
        code, out = run_cmd(["gh", "api", f"repos/{REPO}/milestones", "-X", "POST", "-f", f"title={title}", "-f", f"description={desc}"])
        if code == 0:
            try:
                data = json.loads(out)
                num = data["number"]
                milestone_map[title] = num
                print(f"  ✓ Created milestone: {title} (#{num})")
            except Exception:
                print(f"  ✓ Created milestone: {title}")
        else:
            print(f"  ✗ Failed milestone {title}: {out.strip()}")
    return milestone_map


if __name__ == "__main__":
    sync_labels()
    m_map = sync_milestones()
    print("Milestone map:", m_map)
