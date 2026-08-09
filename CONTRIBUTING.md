# Contributing to NOVA

## Read first

- [`CONSTITUTION.md`](CONSTITUTION.md) — the design rules. Article III
  (priority order) and Article VI (the feature bar) decide most arguments
  before they start.
- [`RFC/0000-rfc-process.md`](RFC/0000-rfc-process.md) — when a design
  document is required.
- [`RFC/0001-core-capability-effects.md`](RFC/0001-core-capability-effects.md)
  — what the language currently is.

## Getting set up

The reference semantics needs only Python 3.11+. No dependencies.

```sh
python3 -m verifier.refspec check examples/hello.nova
python3 -m verifier.refspec run   examples/hello.nova
python3 tests/run_conformance.py
```

The Rust compiler is not yet started; it needs a stable Rust toolchain.

## What is most useful right now

In rough order:

1. **Attacking RFC 0001.** The design is in Review. A counterexample — a
   program that should be expressible and is not, or a way to launder
   authority past the derivation rule — is worth more than a feature.
2. **Answering RFC 0001 open question §11.1** (does effect derivation
   survive abstraction?). This gates Milestone 0.
3. **Conformance tests.** Especially rejection tests: programs that must
   *fail*, with the exact diagnostic.
4. **The Rust front end**, once someone with a toolchain starts it. It
   must agree with the reference semantics, not the other way round.

## What is not useful right now

- Syntax preferences. The surface syntax is provisional and will change;
  arguing about it before the semantics settle wastes everyone's time.
- Features from the Vision that have no RFC (distribution, AI, budgets).
  Constitution Article VIII.
- Performance work on the reference semantics. It is a specification, not
  a compiler; it is allowed to be slow.

## Tests

Conformance tests are the shared arbiter between implementations. Each is
a `.nova` file with an expectation header:

```
//! expect: ok
//! type: Int ! {Clock}
```
```
//! expect: error E0201
```

A test that only exercises the reference semantics is not a conformance
test; put it in the implementation's own suite.

## Pull requests

- One logical change per PR.
- A semantic change without a corresponding test will not be merged.
- If your change makes a diagnostic worse, say so in the PR. Article X
  treats diagnostics as semantics.
- Commits should explain *why*. The diff already says what.
