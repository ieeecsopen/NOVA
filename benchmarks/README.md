# Benchmarks

Empty, deliberately and visibly.

RFC 0001 §9 makes three cost claims — that row unification is cheap, that
effects are free at run time, and that capability calls devirtualize —
and none of them is measured. RFC 0001 §12 therefore makes a benchmark
harness a prerequisite for the RFC leaving Review.

Recorded as known issue I4 in `docs/known-issues.md`.

What needs measuring, in order:

1. **Check time vs. row width.** Synthesize programs with rows of 1, 2,
   4, 8, 16, 32 labels and measure checking time. The claim is
   near-linear; the risk is that `join` degrades.
2. **Check time vs. call depth**, for row-polymorphic call chains. This
   is where instantiation cost shows up.
3. **`widen` rate on real code.** RFC 0001 §7 states that if `widen`
   appears in more than 10% of signatures, the equality rule is wrong.
   This is a falsification test for the central design decision, and it
   needs a >500-line NOVA program to run against, which does not exist
   yet.

Run-time and binary-size benchmarks are meaningless until there is a code
generator.
