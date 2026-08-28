# NOVA — Data & Persistence Model

**Status:** Production Design Reference  
**Cross-References:** [FULL-STACK-MODEL.md](FULL-STACK-MODEL.md), [SERVICE-MODEL.md](SERVICE-MODEL.md), [ERROR-MODEL.md](ERROR-MODEL.md)

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
