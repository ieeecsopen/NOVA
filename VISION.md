# NOVA — Vision

## The problem

Modern software carries obligations that the languages it is written in
cannot express.

A typical service knows, somewhere, that:

- this function must not touch the network
- this handler must complete in 50ms
- this code path must never see unredacted PII
- this dependency should not be able to read the filesystem
- this budget is 200MB of memory and 3 database round-trips
- this value is an estimate, not a measurement

None of that is in the type system. It lives in review comments, runbooks,
linter configs, service meshes, admission controllers, and the memory of
whoever wrote it. It is checked late, at deploy time or not at all, by
tools that do not understand the program.

The result is a class of failure that is structural, not accidental:
a transitive dependency reads `~/.ssh` because nothing said it could not;
a retry loop amplifies an outage because nothing bounded it; a log line
leaks a token because nothing tracked the taint.

## The thesis *(adopted 2026-08-28, after Phase 0)*

Phase 0 ranked five candidate theses
([DESIGN-OPPORTUNITIES.md §8](research/DESIGN-OPPORTUNITIES.md#8-five-candidate-theses-ranked)).
Two are adopted, as a pair:

> **T1 — the obligation row.** Every non-functional obligation a program is
> under — authority, effects, cost, retry policy, instrumentation — is
> carried by *one* row on function types, derived from context rather than
> authored, and checked compositionally.
>
> **T2 — capability-safe components.** NOVA is the language for building
> systems out of mutually distrusting parts: no ambient authority,
> capability requirements published as part of every interface, compiled
> to WebAssembly components so it can be adopted one module at a time.

They are not alternatives. **The row is the mechanism; capability-safe
components are the product.** T1 is why T2 is sound; T2 is what T1 looks
like to someone who has to ship something.

This pairing is chosen because T1 alone is unadoptable ("better types for
obligations" moves nobody) and T2 alone is unprincipled (capability
passing without effect tracking loses authority at every closure).

### What would falsify it

Recorded before the work, so it cannot be quietly redefined later. Three
of the five have now been tested:

| Falsifier | Experiment | Result |
|---|---|---|
| Grades that do not compose across branches or higher-order code | [003](docs/experiments/003-graded-rows.md) | **Partially confirmed.** Sequential/branch composition works; a syntactic pass collapses to "no bound" the moment row polymorphism (`with_retry`) is involved. Not fatal to T1, but it means grading must live in the type system, not a bolt-on pass — Milestone 5 is corrected accordingly. |
| Instrumentation derived from rows that nobody would use | [002](docs/experiments/002-rows-to-spans.md) | **Not falsified, refined.** Rows give the *shape* of execution (which capabilities, in what order, with what arguments) with a structural drift-freedom guarantee, at zero extra mechanism. They do not give *semantic* labeling (span names, sampling, redaction) — that needs a separate, undesigned layer. |
| Capability manifests that churn so much they are ignored | [001](docs/experiments/001-capability-manifests.md) | **Not falsified.** Detects a real supply-chain-shaped authority increase with zero new mechanism and no false positives on two controls. Churn rate is an ecosystem question that needs Milestone 2's module system to even ask. |
| A `widen` rate above 10% of signatures | *(needs a real codebase; not yet run)* | — |
| Capability-passing proving intolerable | *(needs a real codebase; not yet run)* | — |

The two remaining falsifiers need more NOVA code to exist than currently
does — they are Milestone 2+ questions, not Phase 0 ones.

## The claim

NOVA's thesis is that these obligations are *type-level* information that
languages have declined to carry, mostly for historical reasons, and that
carrying them is now affordable.

Two of them cannot be added later, so NOVA starts with them:

**Effects.** What a function does — not just what it returns — is part of
its type. `read_config` and `pure_parse` are different types, and the
difference is checked.

**Authority.** The ability to act on the outside world is a *value* that
must be passed, not an ambient power available to any code that can import
a module. Code that was never handed a network capability cannot open a
socket, no matter what it imports.

Everything else NOVA hopes to express — resource budgets, contracts,
uncertainty, deployment topology — is a refinement of those two ideas, and
none of it ships until it has a semantics.

## What NOVA is not

- Not a Rust replacement. Rust's ownership model is better developed than
  anything NOVA has; NOVA has not yet designed its memory discipline.
- Not a research toy. The goal is a language people ship production
  services in.
- Not a framework. NOVA is a language and a compiler. "Full-stack" means
  the type system can describe a boundary, not that NOVA ships a router.
- Not novel by assertion. See Constitution, Article V.

## The honest state of things

NOVA today is a specification for a small core calculus and a compiler
front end. It compiles a language with functions, effects, and
capabilities, and nothing else. It has no memory model, no generics, no
concurrency, and no code generation.

The near-term question NOVA is trying to answer is narrow and testable:

> Can effect rows and capability values be combined in one type system such
> that the effect row is *derivable* from the capabilities in scope, rather
> than being a second thing the programmer must maintain?

If the answer is yes, effect annotations stop being bookkeeping and become
a consequence of what you were given. If the answer is no, NOVA has learned
something and the design changes.

Everything downstream — distribution, budgets, agents — is contingent on
that question, and is not being built until it is answered.

## Direction, in order

1. **Core calculus.** Effects + capabilities, specified and checked.
2. **Memory discipline.** The largest open question. Affine by default is
   the leading candidate; alternatives are on the table.
3. **Abstraction.** Generics, traits/protocols, modules.
4. **Concurrency.** Structured, effect-typed, race-free by construction.
5. **Compilation.** Native and WebAssembly, via a documented IR.
6. **Resources.** Budgets as a checked effect, not a runtime limiter.
7. **Contracts and verification.** Opt-in, layered, machine-checked.
8. **The distributed and adaptive layers.** Only after 1–7.

Each step must survive the Constitution's feature bar before the next
begins.

## Non-negotiables

- The specification is the product; implementations follow it.
- No feature ships without an executable reference semantics.
- No claim of novelty without a citation.
- Breakage before 1.0 is expected and will be documented.
