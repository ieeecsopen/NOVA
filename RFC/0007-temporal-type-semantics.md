# RFC 0007 — Temporal Type Semantics & Clock Freshness Guarantees

- **Status:** Draft
- **Created:** 2026-09-15
- **Supersedes:** —

## Summary

This RFC proposes first-class temporal type annotations (`T @ fresh(D)`) that
allow NOVA programs to encode data freshness constraints directly in the type
system. Cached or distributed reads that violate freshness SLAs are caught at
compile time, preventing stale data from silently propagating through a
capability-safe pipeline.

## Problem

Consider a distributed trading system that caches price quotes:

```nova
fn execute_trade(net: Network, quote: PriceQuote) -> Result[TradeReceipt, Error] ! {Network} {
    // BUG: `quote` may be 30 minutes old — the type system says nothing
    // about its temporal validity. A stale price causes financial loss.
    net.post("/trades", quote)
}
```

Today, `PriceQuote` carries no freshness metadata. The programmer must manually
track staleness with ad-hoc `Instant` fields and runtime checks. This is:

1. **Error-prone:** forgetting a check silently admits stale data.
2. **Non-composable:** each service re-invents its own TTL logic.
3. **Unverifiable:** the compiler cannot reason about data age.

## Prior Art

| System | Approach | Limitations |
| :--- | :--- | :--- |
| **Rust** | No temporal types. `Instant`-based guards are manual and untracked. | Compiler cannot enforce freshness. |
| **Koka** | Row-based effects track *what* happens, not *when* data was produced. | No temporal dimension. |
| **TLA+ / Alloy** | Temporal logic over state transitions, but not embedded in a programming language type system. | Specification-only; not enforceable at compile time in application code. |
| **CRDTs (Riak, Automerge)** | Convergent replicated types with vector clocks. | Convergence ≠ freshness; a converged value may still be arbitrarily old. |
| **HTTP `Cache-Control`** | `max-age`, `stale-while-revalidate` headers. | Runtime-only; not type-checked; limited to HTTP layer. |

## Design

### Syntax

A temporal annotation attaches a freshness bound to any type:

```
Type @ fresh(Duration)
```

Where `Duration` is a compile-time constant expressed as a literal with a time
unit suffix:

```nova
fn execute_trade(net: Network, quote: PriceQuote @ fresh(5s))
    -> Result[TradeReceipt, Error] ! {Network}
{
    net.post("/trades", quote.unwrap())
}
```

### Static Semantics

#### Type Formation

$$
\frac{\Gamma \vdash T : \text{Type} \quad d \in \text{Duration}}
     {\Gamma \vdash T\ @\ \text{fresh}(d) : \text{Type}}
$$

#### Subtyping (Monotonic Decay)

A value with a tighter freshness bound is a subtype of one with a looser bound:

$$
\frac{d_1 \leq d_2}
     {T\ @\ \text{fresh}(d_1) <: T\ @\ \text{fresh}(d_2)}
$$

#### Staleness Transition

A `T @ fresh(d)` value that escapes its TTL window degrades to `Stale[T]`:

$$
\frac{\Gamma \vdash v : T\ @\ \text{fresh}(d) \quad \text{elapsed}(v) > d}
     {\Gamma \vdash v : \text{Stale}[T]}
$$

At compile time, the checker conservatively marks any `T @ fresh(d)` value as
potentially stale if it crosses an effectful boundary (e.g., a network call or
suspension point) whose latency is not statically bounded.

#### Refresh Rule

A `Stale[T]` value can be promoted back to `T @ fresh(d)` only by invoking a
refresh capability:

$$
\frac{\Gamma \vdash s : \text{Stale}[T] \quad \Gamma \vdash \text{refresh} : (C, T) \rightarrow T\ @\ \text{fresh}(d)\ !\ \{C\}}
     {\Gamma \vdash \text{refresh}(c, s.\text{unwrap}()) : T\ @\ \text{fresh}(d)\ !\ \{C\}}
$$

### Dynamic Semantics (Runtime Behavior)

At runtime, temporal values carry a timestamp of their creation. The runtime
checks freshness at unwrap boundaries:

1. **`unwrap()` on `T @ fresh(d)`**: succeeds if `now - created_at < d`; panics
   or returns `Err` otherwise.
2. **Pattern matching on temporal types**: the `fresh` arm only matches if the
   value is still within its TTL.

```nova
match timed_quote {
    fresh(q) => execute_trade(net, q),
    stale(q) => refresh_and_trade(net, clock, q),
}
```

### Interaction with Capabilities

Temporal types compose naturally with the capability model:
- Constructing a `T @ fresh(d)` requires the `Clock` capability (to timestamp).
- Refreshing a stale value requires whichever capability sources the data
  (e.g., `Network`).

## Examples

### Accepted: Fresh data flows through

```nova
fn fetch_quote(net: Network, c: Clock, symbol: String)
    -> PriceQuote @ fresh(5s) ! {Network, Clock}
{
    let raw = net.get("/quotes/" + symbol)?;
    c.stamp(parse_quote(raw))   // stamp attaches current time
}
```

### Rejected: Stale data in fresh slot

```nova
fn bad_trade(net: Network, cached: Stale[PriceQuote])
    -> Result[TradeReceipt, Error] ! {Network}
{
    execute_trade(net, cached)
    //                 ^^^^^^
    // E0401: expected `PriceQuote @ fresh(5s)`, found `Stale[PriceQuote]`
    // help: call a refresh function to obtain a fresh value
}
```

## Alternatives

1. **Do nothing.** Freshness remains a runtime concern with manual `Instant`
   comparisons. This is the status quo and is error-prone.
2. **Library-only `Fresh<T>` wrapper.** A newtype that carries a timestamp but
   has no compiler enforcement. Better than nothing, but the compiler cannot
   reject stale-to-fresh coercions.
3. **Effect-row encoding.** Encode freshness as an effect (e.g., `! {Fresh(5s)}`).
   Overloads the effect system with temporal concerns that are orthogonal to
   capability safety.

## Tradeoffs

- **Annotation burden:** Developers must annotate temporal parameters. Mitigated
  by inference: a function returning `c.stamp(x)` automatically infers the
  `@ fresh(d)` annotation.
- **Compile-time complexity:** Subtyping checks on durations add a (small)
  constant factor to type checking.
- **Runtime overhead:** Each temporal value carries an 8-byte timestamp. For
  hot inner loops over primitive data this may be undesirable; the `@ static`
  escape hatch opts out.

## What This Forecloses

- Fully dependent temporal types (e.g., `T @ fresh(f(x))` where `f` is a
  runtime function). This RFC limits durations to compile-time constants. A
  future RFC could lift this restriction.

## Costs

| Dimension | Impact |
| :--- | :--- |
| Compile time | +~2% for programs using temporal annotations |
| Runtime | 8 bytes per temporal value (timestamp) |
| Binary size | Negligible |
| Reader effort | One new annotation syntax (`@ fresh(D)`) |

## Staging

1. **Phase 1 (this RFC):** `T @ fresh(D)` with compile-time constant `D`,
   `Stale[T]`, and `Expired[T]`. Conservative staleness inference at effectful
   boundaries.
2. **Phase 2 (future RFC):** `Before[T, Time]`, `After[T, Time]`, and
   `Eventually[T]` for distributed causality (see [TEMPORAL-MODEL.md](../docs/runtime/TEMPORAL-MODEL.md)).
3. **Phase 3 (future RFC):** Duration inference from capability latency bounds.

## Open Questions

1. Should `@ fresh(D)` be sugar for a more general `@ valid(Predicate)` system?
2. How should temporal values interact with serialization / deserialization
   across process boundaries?
3. Should the `Clock` capability be required for *checking* freshness (read),
   or only for *stamping* freshness (write)?

