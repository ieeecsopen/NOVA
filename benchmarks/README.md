# Benchmarks

## What this measures

```bash
python3 benchmarks/challenge_suite.py          # human-readable
python3 benchmarks/challenge_suite.py --json    # machine-readable
```

`challenge_suite.py` times the operations the toolchain actually performs
today, on the real example programs:

| Measurement | What it covers |
| :--- | :--- |
| `nova check` median | lex + parse + type / effect / capability checking |
| `nova run` median | the above + execution via the reference interpreter |
| `nova build hello.nova` (clean) | + native C codegen + `clang` link |
| `nova build hello.nova` (cached) | SHA-256 cache hit in `.nova_cache/` |

Results are written to `results.json`.

## What this is NOT

**There is no cross-language comparison here, and any earlier table
pitting NOVA against Rust / Go / C++ has been removed.** Such a comparison
would need NOVA to have a native code path for the things being compared
(tasks, channels, compiled loops, real I/O). It does not
([docs/known-issues.md](../docs/known-issues.md) C1, I4). Publishing a
comparison before then would be misleading.

`concurrency_bench.py` is a stub. It used to benchmark Python's own
threading primitives and label the numbers "NOVA"; it no longer does
anything. NOVA has no concurrency runtime yet (ROADMAP Milestone 4).

## Methodology

- Wall-clock, `time.perf_counter()`, median of N runs per operation.
- Single machine, no isolation from other load — treat the numbers as
  order-of-magnitude, not precise.
- The interpreter is CPython-bound; these are not the numbers a
  production NOVA implementation would post, and are not claimed to be.
