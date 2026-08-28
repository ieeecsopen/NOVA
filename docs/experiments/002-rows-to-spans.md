# Experiment 002 — Instrumentation derived from rows

Tests [P21](../../research/PROBLEM-SPACE.md#p21--observability-is-bolted-on-and-drifts):
can trace spans be *generated* from a function's capability uses, so that
instrumentation cannot drift out of sync with the code the way hand-placed
logging does?

**Implementation:** [`verifier/refspec/tracing.py`](../../verifier/refspec/tracing.py) —
a subclass of the reference `Interpreter` that intercepts every `CapUse`
node during evaluation and records it. It adds no new mechanism; it reads
information the type checker already has.

**Demonstration:** [`tests/tracing/drift-demo/`](../../tests/tracing/drift-demo/),
run via `python3 tests/tracing/run.py`.

## Method

Generating a span from a capability call is not the interesting part —
it is a few dozen lines, shown below. The interesting question is whether
doing it this way **avoids the drift bug** that makes hand-written
instrumentation unreliable: a human adds a call site and forgets the
matching log line, and the gap is invisible until an incident needs the
missing trace.

The test: two versions of a small request handler. `v2` adds a latency
measurement — a genuinely new capability use (`Clock`) — around existing
logging. The tracer itself is not touched between the two runs.

```
$ python3 tests/tracing/run.py
v1 trace: ['Runtime.print']
v2 trace: ['Runtime.clock', 'Clock.now', 'Runtime.print', 'Clock.now']
ok: v2's new capability use (Clock.now, x2) appears in the trace with
ZERO changes to tracing.py
```

## Result: the drift property holds, structurally

A hand-instrumented equivalent of `v2` would need a matching edit —
someone has to remember to add `log("clock read")` next to the new
`c.now()` calls. The derived tracer needs no such edit, and structurally
*cannot* need one: it does not mention `Clock` or `Runtime` by name
anywhere in its own code (`tracing.py` has zero references to any
concrete capability). It reacts to the `CapUse` node the checker already
proved is there. This is a stronger claim than "it happened to catch this
example" — it is that the mechanism has no code path by which it *could*
miss a capability use, because it never enumerates capabilities in the
first place.

This is the same reasoning as RFC 0001 §4.3's capture rule: the row is
authoritative because it is computed, not maintained, and both the
manifest experiment (001) and this one are downstream of that one
decision.

## Result: the honest limitation — granularity

The trace `Runtime.print("GET /health")` tells you a print happened. It
does **not** tell you *why* — that this was a health-check request, that
it came from a load balancer, that it should be sampled at 1%. A
domain-meaningful trace needs domain-meaningful values, and those come
from the arguments at the call site (which this experiment does capture
and render, e.g. `Runtime.print("GET /health")`), not from the capability
name alone.

So the accurate claim is narrower than "instrumentation is unnecessary":

> A derived trace gives, for free and without drift, the **shape** of
> what a function did — which capabilities, in what order, with what
> arguments. It does not give **semantic labeling** — span names, sampling
> decisions, which fields are PII and must be redacted before export.
> Those remain a human decision layered on top, most naturally as
> metadata *on the capability declaration itself* (e.g. an attenuated
> `Metrics` capability whose ops carry a stated sampling rate), not as
> hand-placed calls in function bodies.

That refinement — instrumentation metadata living on the capability
declaration — is a plausible design and is **not implemented**; it is a
finding for a future RFC, not a claim this experiment tested.

## Verdict against the falsification criteria

VISION.md named "instrumentation derived from rows that nobody would
actually use" as a falsifier. This experiment cannot test *want* on real
code — there is no real NOVA codebase — but it demonstrates the
structural property that would make it wanted: no drift, for the shape of
execution, at zero implementation cost beyond what the checker already
computes.

**Does not falsify T1.** The result is positive but narrower than the
strongest version of the claim: rows give shape-instrumentation for free;
they do not by themselves give semantic instrumentation. That is a
refinement of the thesis, worth recording precisely rather than
overclaiming.
