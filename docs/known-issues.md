# NOVA — Known issues

Recorded honestly, per Constitution Article XII. Each entry says whether
it is a *specification* gap (the RFC does not say what should happen), an
*implementation* gap (the RFC says, the code does not do it), or a
*diagnostic* gap (both are correct, the error message is poor).

## C1 — Native C backend covers only the first-order subset *(implementation)*

`compiler/nova_compiler/codegen_c.py` lowers top-level `fn`s over `Int` /
`Bool` / `String` / `Unit` / `struct`, with `Runtime` and `Clock`, to a
real native binary. Enums, `match`, closures, generics, traits, `List`,
`for` and tuples are **not lowered** — `nova build` detects this before
emitting any C, prints `Backend: interpreter-backed runner`, and produces
a runnable artifact that executes the program through the reference
interpreter instead. The program runs and returns the right value; it is
just not a standalone machine binary. The interpreter
(`verifier/refspec/eval.py`) is the authoritative execution engine
regardless. Extending the backend is Milestone 3 work.

## C2 — HIR/MIR are informational, not a real IR *(implementation)*

`hir.py` and `mir.py` are surfaced by `--emit-hir` / `--emit-mir` and
run as a validation pass, but they are not on the execution path and do
not yet desugar pattern matches, monomorphize generics, or elaborate
drops. The names are aspirational; the substance is Milestone 3.

## C3 — No string operations *(specification, deliberate for v0.2)*

`String` supports only `==` / `!=` and pattern matching. There is no
concatenation, length, slicing or formatting — adding a fragment of a
string library would contradict the same v0.2 discipline that makes
collections persistent-only (`std/list.nova`). A `String` operation set
needs its own RFC alongside the memory model (Milestone 1), because a
growable string is a mutable heap value.

## C4 — `attenuate` still not implemented *(implementation)*

Unchanged from I5 below. `Filesystem` and `Network` now exist in the
prelude (minted from `Runtime`, each use visible in the row), but there
is still no way to hand out a *reduced* capability — only the whole
token. RFC 0001 §4.6 defines `attenuate`; it is deferred to Milestone 2.

## D1 — Let-bound closures blame the wrong expression *(diagnostic)*

```nova
fn launder(c: Clock) -> (() -> Int) {
    let f = || c.now();
    f
}
```

Correctly rejected, but with `E0206` (generic effect mismatch) instead of
`E0203` (closure hides authority). The blamed expression is the variable
`f`, so the checker cannot see that it names a lambda and cannot report
the capture. Fixing it needs the checker to track which bindings came
from lambdas. Covered by `tests/conformance/022-attack-let-bound-closure.nova`,
which currently asserts the *wrong* code so that fixing it fails the test
loudly.

## S1 — Rows of stored capabilities are unspecified *(specification)*

RFC 0001 §11.3. A struct field holding a capability would be a laundering
channel exactly as closures were, and v0.1 has no structs precisely
because this is unanswered. **This blocks any RFC that introduces product
types.**

## S2 — Effect derivation under abstraction is unanswered *(specification)*

RFC 0001 §11.1, and the open question most likely to sink the design.
When a capability is behind a generic parameter or an interface, the
concrete label is unknown. Milestone 0 does not exit until this has an
answer.

## I1 — One row variable per function *(implementation, and probably specification)*

`E0205`. Joining two rows with distinct rigid tails is rejected. This is
sound but restrictive; a function polymorphic in two independent rows
cannot be written. Whether it *should* be expressible is not yet decided —
see RFC 0001 §7.

## I2 — Reachability under-approximates *(implementation, by design)*

`verifier/refspec/reachability.py` tracks capabilities through annotated
bindings and direct aliases only. A capability obtained from a call
(`let c = rt.clock();`) does not appear in the `audit` listing, though the
checker still gets the row right. Visible as the difference between the
two sections of `python3 -m verifier.refspec audit examples/retry.nova`.
The pass is advisory; the checker is authoritative.

## I3 — No second implementation *(implementation)*

Constitution Article IX requires two. There is one. The Rust compiler is
not started, so nothing currently disagrees with the reference semantics,
which means the specification has not actually been tested for ambiguity.

## I4 — Benchmarks measure the toolchain, not the language *(implementation)*

RFC 0001 §9 makes cost claims that remain largely unmeasured. What
`benchmarks/` now contains is a wall-clock harness for the *toolchain*
(`nova build` / `nova run` timings via `challenge_suite.py`) plus a
Python micro-benchmark of the host's threading primitives
(`concurrency_bench.py`) — the latter is **not** a measurement of NOVA
and is labelled as such in `benchmarks/README.md`. There is no
cross-language comparison, and there should not be one until there is a
native code path for the constructs being compared. §12's "benchmarks
before Accepted" bar is not met.

## I5 — Attenuation is specified but not implemented *(implementation)*

RFC 0001 §4.6 defines `attenuate`; v0.1 does not implement it (§10 defers
it). Until it exists, the only capabilities are the prelude's, and the
"audit every row-dropping site" story is untested.

## E1 — Graded rows do not survive row polymorphism *(specification, expected)*

Experiment 003 (`docs/experiments/003-graded-rows.md`). A syntactic pass
that counts capability occurrences after checking gives sound, useful
bounds for first-order, non-recursive code, and gives up entirely
(`UNKNOWN`, not an unsound guess) the moment a row-polymorphic
higher-order function like `with_retry` is involved — which is most of
the code RFC 0001 makes idiomatic. Grading needs to be carried on row
*variables* inside unification itself; this is now a stated precondition
for Milestone 5, not a detail to fill in during it.

## P1 — No conditional trait impls *(specification, stated limitation)*

RFC 0003 §5. `impl[T] Show for Option[T] where T: Show` is not
expressible — an `impl` is unconditional and cannot itself require a
property of its own type parameters. `examples/generic-box-and-trait.nova`
is written to stay inside this limit rather than pretend it does not
exist.

## P2 — No trait-name disambiguation *(implementation, stated limitation)*

If two `impl`s for the same concrete type provided methods of the same
name from two different traits, `check.py`'s `MethodCall` lookup takes
whichever the impl registry iterates to first, with no ambiguity error.
Not currently reachable by any example or conformance test, but not
rejected either. RFC 0003 §8.

## P3 — No qualified import paths *(specification, deliberate)*

RFC 0004 §2. `import a.b;` makes `b`'s `pub` items visible by their bare
names, not as `b.name`. Names are globally unique across the whole
program as a consequence. This is deliberate — a real qualified-path
system needs a package manager to define what a "package" is, and none
exists yet (Milestone 2) — but it is a real, load-bearing scope
decision, not a placeholder.

## P4 — No pattern-destructuring `let` *(specification, stated limitation)*

`let (a, b) = pair;` is not supported; only `match` arms take patterns.
`examples/tuples.nova`'s own comments note this directly, having been
written against it once and corrected. A small, plausible future
addition (RFC 0002 §9 does not currently list it, but should be updated
alongside any RFC that adds it).

## P5 — `reachability.py` under-approximates through field projection
*(implementation, by design, extended from I2)*

RFC 0002 §9. The advisory reachability pass does not track *which*
field of a struct holds a capability — only whole-variable bindings, as
it already did for closures before this phase. Soundness rests entirely
on the checker (`MethodCall`'s receiver-type dispatch), not on this
pass; see RFC 0002 §3 for why that is sufficient.

## P6 — No mutable fields, collection elements, or general lvalues
*(specification, deliberate, argued in RFC 0005 §3.3)*

Only a bare local name may appear on the left of `=`. Extending
mutability to fields or collection elements would reintroduce the
aliasing question RFC 0005 specifically avoided by restricting itself to
frame-local variables with no possible second reference.
