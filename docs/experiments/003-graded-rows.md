# Experiment 003 — Graded rows

Tests RFC 0001 [open question 7](../../RFC/0001-core-capability-effects.md#11-open-questions)
and the core claim of thesis T1
([DESIGN-OPPORTUNITIES.md §2](../../DESIGN-OPPORTUNITIES.md#2-theme-a--obligations-are-one-mechanism)):
that budgets, retry policy and instrumentation are the *same* effect row
with a grade attached to each label, and that the ungraded row does not
foreclose the graded one.

**Implementation:** [`verifier/refspec/grading.py`](../../verifier/refspec/grading.py).
**Tests:** [`tests/grading/`](../../tests/grading/), run via
`python3 tests/grading/run.py`.

## Method

A separate syntactic pass over the already-checked AST computes, for each
function, an upper bound on how many times each capability in its row is
used. The lattice is naturals-with-top: sequential composition adds,
branching takes the max (a may-analysis), recursion saturates to `*`.

Deliberately *not* built by extending the type checker — the question was
whether occurrence-counting is even coherent before paying for the bigger
change of putting grades in the type system.

## Result: it works for the first-order, non-recursive core

```
$ python3 -m verifier.refspec grade examples/timing.nova
  measure: {Clock: 2, Runtime: 1}
  report: {Clock: 1, Runtime: 1}
  main: {Clock: 3, Runtime: 3}
```

`measure` calls `rt.clock()` once and the resulting `c.now()` twice — the
bound is exact. Sequential composition adding and branches joining both
behave as predicted (`tests/grading/002`, `003`). Recursion correctly
saturates only the labels actually reachable, not the whole row
(`tests/grading/004`) — a real function like `count_down` is bounded as
`{Clock: *}`, not "no bound at all", which is a meaningfully weaker and
more honest statement than either extreme.

## Result: it fails, soundly, at row polymorphism — this is the finding

```
$ python3 -m verifier.refspec grade examples/retry.nova
  with_retry: ? (no sound bound)   [higher-order call]
  timed_read: ? (no sound bound)
  pure_compute: ? (no sound bound)
  main: ? (no sound bound)
```

`pure_compute` is checked **pure** by RFC 0001 — its row is `{}`,
verified by `nova check`. But `pure_compute` calls `with_retry(3, || 42)`,
and grading cannot see through that call: `with_retry`'s `f` parameter is
a *value*, not a name the syntactic pass can look up, so the pass cannot
rule out `f` performing anything. The honest answer is "no sound bound",
propagated to every caller.

This was worth getting right rather than papering over. An earlier
version of this pass returned `{}` for `with_retry` (saturating an empty
dict does nothing), which is **unsound** — it silently claims a function
is free when it is actually unknown. Fixed by distinguishing two states
that are easy to conflate: `{}` (a proven bound of zero) and `UNKNOWN`
(no bound could be established) — see the module docstring and
`tests/grading/006`–`007`.

## What this means for RFC 0001 §11.7

The naive approach — grade the *type checker's output* with a separate
syntactic pass, after the fact — does not survive row polymorphism, which
is exactly the mechanism RFC 0001 uses to make `with_retry` reusable in
the first place (§4.4). The two goals are in tension: the more
polymorphic a function is over effects, the less a syntactic afterthought
pass can say about its cost.

The wall is precise enough to state as a requirement on any future
design: **grading cannot be bolted on beside the row; it has to be
carried on the row itself, including on row *variables***. Concretely,
`with_retry[r]` would need a type like

```
fn with_retry[r](attempts: Int, f: () -> Int ! r@1) -> Int ! r@attempts
```

where `r@n` means "the capabilities in `r`, each grade multiplied by
`n`" — i.e. grades attach to the row variable and are resolved at
instantiation, the same moment the label set itself is resolved. That is
a change to the *type system* (a real RFC, changing unification), not a
pass that runs after it.

## Verdict against the falsification criteria

[VISION.md](../../VISION.md#what-would-falsify-it) named "grades that do
not compose across branches or higher-order code" as a falsifier of T1.

- **Sequential and branching composition: survives.** Addition and join
  are the right operations and behave correctly (`tests/grading/001-003`).
- **Higher-order / polymorphic composition: does not survive**, in the
  syntactic-pass form tested here. This is a real, load-bearing limit, not
  a minor gap — `with_retry` is RFC 0001's own motivating example
  (§2), and it is precisely the case that breaks.

**This does not falsify T1**, because the failure is specific to *where*
grading was implemented (a bolt-on pass) rather than to the *idea* that
one row can carry both effect and grade. It does mean the "no design
needed, just count occurrences" version of Milestone 5 (RFC 0001 §10) is
wrong, and Milestone 5 must instead extend row unification itself before
grading can be trusted on any row-polymorphic code — which is most
interesting code. That is a real, load-bearing correction to the roadmap,
produced for the cost of one afternoon's implementation, which was the
point of running this experiment before Milestone 5 rather than during
it.
