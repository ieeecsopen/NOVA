# NOVA — Temporal Types & Freshness Model

**Status:** Production Design Reference  
**Cross-References:** [UNCERTAINTY-MODEL.md](UNCERTAINTY-MODEL.md), [PROVENANCE-MODEL.md](PROVENANCE-MODEL.md), [EFFECT-SYSTEM.md](../language/EFFECT-SYSTEM.md), [LANGUAGE-PHILOSOPHY.md](../foundation/LANGUAGE-PHILOSOPHY.md)

---

## 1. The Temporal Gap in Conventional Type Systems

Conventional type systems are static: a `User` or `ExchangeRate` value is typed identically whether it was fetched 10 milliseconds ago or 3 weeks ago.

In modern distributed, cache-heavy, and reactive systems, **time and freshness are core semantic properties of data**.

NOVA introduces **Temporal Wrapper Types** that make data decay and validity explicit:

$$\text{Value} = \text{Data Payload} + \text{Temporal Validity Envelope}$$

---

## 2. Temporal Type Taxonomy

| Type Constructor | Semantic Invariant | Degradation / Decay Behavior |
| :--- | :--- | :--- |
| **`Fresh[T, TTL]`** | Guaranteed valid within duration `TTL` | Automatically transitions to `Stale[T]` after TTL expires. |
| **`Stale[T]`** | Read permitted for cached fallback | Cannot be used in operations requiring `Fresh[T]`. |
| **`Expired[T]`** | Invalid data payload | Cannot be unwrapped without invoking a refresh capability. |
| **`Before[T, Time]`** | Generated strictly prior to logical timestamp | Validates distributed ordering / Lamport clock precedence. |
| **`After[T, Time]`** | Generated strictly after logical timestamp | Enforces causality and linearizable read ordering. |
| **`Eventually[T]`** | Asynchronous convergence value | Resolves when background replication reaches quorum. |

---

## 3. Freshness Verification & Cache Invalidation

Reading data with strict freshness requirements forces the developer to provide a refresh path:

```nova
struct PriceQuote {
    symbol: String,
    price_cents: Int,
}

// Handler requires a fresh quote (< 5 seconds old)
fn execute_trade(net: Network, quote: Fresh[PriceQuote, 5s]) -> Result[TradeReceipt, Error] ! {Network} {
    // Valid to execute
    net.post("/trades", quote.unwrap())
}

// Fallback logic when quote is stale
fn handle_cached_quote(net: Network, c: Clock, quote: Stale[PriceQuote]) -> Result[TradeReceipt, Error] ! {Clock, Network} {
    // Stale quote cannot be passed to execute_trade directly
    // Must re-fetch using Network capability:
    let fresh_quote = fetch_quote(net, c, quote.unwrap().symbol)?;
    execute_trade(net, fresh_quote)
}
```

---

## 4. Logical Clocks & Distributed Causality

For distributed systems without synchronized physical clocks, NOVA provides **Causal Vector Types**:

```nova
struct CausalEvent[T] {
    data: T,
    clock: VectorClock,
}

fn merge_events[T](e1: CausalEvent[T], e2: CausalEvent[T]) -> MergeResult[T] {
    if e1.clock.precedes(e2.clock) {
        MergeResult::Ordered(e1, e2)
    } else if e2.clock.precedes(e1.clock) {
        MergeResult::Ordered(e2, e1)
    } else {
        MergeResult::ConcurrentConflict(e1, e2)
    }
}
```
