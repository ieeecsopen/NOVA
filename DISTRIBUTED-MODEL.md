# NOVA — Distributed Programming Model

**Status:** Production Design Reference  
**Cross-References:** [REMOTE-EXECUTION.md](REMOTE-EXECUTION.md), [FAILURE-SEMANTICS.md](FAILURE-SEMANTICS.md), [CONCURRENCY-MODEL.md](CONCURRENCY-MODEL.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

---

## 1. The Fallacies of Distributed Computing, Resolved

Mainstream distributed abstractions (e.g. Java RMI, CORBA, transparent RPC) failed because they attempted to make remote network calls look syntactically identical to local in-memory function calls.

NOVA strictly rejects transparent RPC. In NOVA:
1. **Network calls are explicit:** Remote execution requires the `dist: Distributed` or `net: Network` capability.
2. **Failure is a typed return value:** Every remote operation returns `Result[T, RemoteError]`.
3. **No Distributed Shared Memory:** Nodes communicate exclusively by message passing over typed channels or content-addressed task dispatch.

---

## 2. Core Distributed Primitives

| Primitive | Representation | Semantic Responsibility |
| :--- | :--- | :--- |
| **`Node`** | `node: NodeHandle` | Represents an authenticated remote execution machine or cluster container. |
| **`Service`** | `service Name { ... }` | Replicated service declaration with explicit capability constraints and replica count. |
| **`Channel[T]`** | `ch: DistributedChannel[T]` | Type-safe, ordered network stream transferring serialized `Send` payloads. |
| **`Actor`** | `actor Name { ... }` | Isolated stateful entity running on a specific node, processing incoming inbox messages sequentially. |
| **`CRDT[T]`** | `state: CRDT[T]` | Conflict-free replicated data types ensuring convergent eventual consistency. |

---

## 3. Consistency Models as Type-Level Contracts

NOVA supports explicit consistency semantics parameterized over data storage:

```nova
// Strong consistency: Linearizable read/write through consensus (Raft/Paxos)
struct StrongBankLedger {
    balance: Int,
}
consistency Linearizable;

// Eventual consistency: Replicated shopping cart with PN-Counter / LWW-Set CRDT
struct ShoppingCart {
    items: LWWSet[String],
}
consistency Eventual[CRDT];
```

---

## 4. Distributed Transactions & Sagas

Because distributed transactions cannot safely hold locks across physical network partitions, long-running workflows use **Linear Saga Capabilities**:

```nova
struct OrderSaga {
    order_id: UUID,
    step: Int,
}

fn execute_order_saga(dist: Distributed, saga: OrderSaga) -> Result<(), SagaError> ! {Distributed} {
    // Step 1: Authorize Payment
    let payment = dist.call[PaymentService]("authorize", saga.order_id)?;
    
    // Step 2: Reserve Inventory
    match dist.call[InventoryService]("reserve", saga.order_id) {
        Result::Ok(_) => Result::Ok(()),
        Result::Err(err) => {
            // Automatic compensating transaction
            dist.call[PaymentService]("refund", payment.tx_id)?;
            Result::Err(SagaError::InventoryUnavailable)
        }
    }
}
```
