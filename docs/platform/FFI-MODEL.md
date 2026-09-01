# NOVA — Foreign Function Interface (FFI) Model

<!-- STATUS-BANNER -->
> **Status note (added in the 0.2 honesty pass).** This document is part
> of NOVA's *design record*. It was written in the aspirational voice of
> a finished 1.0 platform. **NOVA is a 0.2 research preview.** What is
> actually built and tested is a frontend type/effect/capability checker,
> a reference interpreter, a first-order native C backend, and the
> `regionlab` memory-model prototype. Everything here about a distributed
> runtime, a WASM UI layer, AI-agent governance, a package registry,
> self-hosting, or cross-language performance is **design, not
> implementation**. See [`README.md`](../../README.md),
> [`ROADMAP.md`](../../ROADMAP.md) and
> [`docs/known-issues.md`](../known-issues.md) for the real state.


**Status:** Production Design Reference  
**Cross-References:** [INTEROPERABILITY.md](INTEROPERABILITY.md), [WASM-COMPONENT-MODEL.md](WASM-COMPONENT-MODEL.md), [MEMORY-MODEL.md](../language/MEMORY-MODEL.md), [SAFETY-GUARANTEES.md](../../research/SAFETY-GUARANTEES.md)

---

## 1. Direct C ABI Compatibility

NOVA structs annotated with `#[repr(C)]` adhere strictly to platform C ABI layout rules (System V AMD64 and ARM64 AAPCS):

```nova
#[repr(C)]
struct EpollEvent {
    events: Int,
    data: Int,
}

extern "C" {
    fn epoll_create1(flags: Int) -> Int;
    fn epoll_ctl(epfd: Int, op: Int, fd: Int, event: *const EpollEvent) -> Int;
    fn epoll_wait(epfd: Int, events: *mut EpollEvent, maxevents: Int, timeout: Int) -> Int;
}
```

---

## 2. Memory Ownership Across the FFI Boundary

Passing memory across the FFI boundary requires explicit ownership contracts:

1. **Non-Owning Borrowing:** Passing pointers (`*const T`, `*mut T`) into C functions that execute synchronously within the lexical scope is guaranteed safe by the enclosing Region lock.
2. **Foreign Ownership Transfer:** When transferring heap data to a C/Rust library, NOVA provides an explicit `into_raw()` destructor that relinquishes linear tracking:

```nova
fn handoff_to_c_library(u: Unsafe, buffer: LinearBuffer) -> *mut Int ! {Unsafe} {
    // Consumes linear buffer, returning raw untracked C pointer
    buffer.into_raw(u)
}
```

3. **Reclaiming Foreign Memory:** Foreign pointers returned from C must be wrapped into a managing linear region with an explicit finalizer (`c_free`):

```nova
fn reclaim_c_buffer(u: Unsafe, ptr: *mut Int, len: Int) -> LinearBuffer ! {Unsafe} {
    LinearBuffer::from_raw(u, ptr, len, || libc_free(ptr))
}
```
