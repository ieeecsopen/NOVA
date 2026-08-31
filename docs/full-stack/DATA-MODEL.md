# NOVA — Data & Persistence Model

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
**Cross-References:** [FULL-STACK-MODEL.md](FULL-STACK-MODEL.md), [SERVICE-MODEL.md](SERVICE-MODEL.md), [ERROR-MODEL.md](../language/ERROR-MODEL.md)

---

## 1. Schema Derivation from Pure Types

NOVA rejects the separation between in-memory types and database schemas. A database entity is declared using standard NOVA struct syntax:

```nova
struct Order {
    id: UUID,
    customer_id: UUID,
    total_cents: Int,
    status: OrderStatus,
    created_at: Int,
}
invariant total_cents >= 0;
```

### Compiler DDL Generation
From the struct declaration above, the NOVA compiler automatically derives the corresponding SQL migration:

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customers(id),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    status VARCHAR(50) NOT NULL,
    created_at BIGINT NOT NULL
);
```

---

## 2. Compile-Time Query Safety

Queries are statically type-checked against the declared entity schemas at compile time:

```nova
fn find_recent_orders(db: Database, customer_id: UUID) -> Result[List[Order], DbError] ! {Database} {
    // Statically validated query: column names, parameter types, and return shape
    db.query[Order](
        "SELECT id, customer_id, total_cents, status, created_at FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
        customer_id
    )
}
```

---

## 3. Linear ACID Transactions

Transactions are modeled as **linear exclusive capabilities**. Holding a transaction token `tx: &mut Transaction` guarantees atomicity:

```nova
fn transfer_funds(db: Database, from: UUID, to: UUID, amount: Int) -> Result<(), TransferError> ! {Database} {
    let mut tx = db.begin_transaction()?;
    
    tx.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", amount, from)?;
    tx.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", amount, to)?;
    
    // Commit consumes the linear transaction handle
    tx.commit()
    // If scope exits without commit, the linear destructor rolls back automatically!
}
```
