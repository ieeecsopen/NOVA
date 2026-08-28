# NOVA Benchmarks Suite

Official performance benchmarks for the NOVA compiler, runtime, and concurrency scheduler.

---

## 1. Concurrency & Scheduler Benchmarks

Run via:
```bash
python3 benchmarks/concurrency_bench.py
```

### Measured Snapshot (Apple Silicon M-series):
* **Task Spawn & Join Throughput:** > 200,000 tasks/second (0.48s for 100,000 tasks).
* **Channel Message Throughput:** > 1,700,000 messages/second.
* **Structured Cancellation Latency:** ~1.4 ms for multi-branch tree propagation.

---

## 2. Compiler Performance Benchmarks

Run via:
```bash
nova bench examples/hello.nova
```

* **Clean Compile Time:** ~44 ms (Parsing, Type-check, Reachability, Clang -O3 codegen)
* **Incremental Compile Time:** ~0.25 ms (SHA-256 cache hits in `.nova_cache/`)
* **Binary Size:** 33,544 bytes (native stripped arm64 binary)
* **Native Execution Time:** ~2.5 ms
