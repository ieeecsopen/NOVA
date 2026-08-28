# NOVA — Full-Stack Application Model

**Status:** Production Design Reference  
**Cross-References:** [UI-MODEL.md](UI-MODEL.md), [SERVICE-MODEL.md](SERVICE-MODEL.md), [DATA-MODEL.md](DATA-MODEL.md), [APPLICATION-MODEL.md](APPLICATION-MODEL.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

---

## 1. The Core Vision: Unified Semantic Model

Contemporary full-stack architectures suffer from the **Triple Representation Problem**:
1. **Frontend:** TypeScript interfaces, React component state, Zod validators.
2. **Backend:** Rust/Go structs, GraphQL/REST DTOs, manual auth middleware.
3. **Database:** SQL schemas, ORM models, migration scripts.

A simple change (e.g. adding `email_verified: Bool` to a user) requires editing 5–7 disparate files across 3 languages and runtime boundaries.

NOVA eliminates this duplication through a single principle:

> **One nominal definition projects into all application layers at compile time.**

```
                           +----------------------+
                           |   struct User { ... }|
                           |   (Single Definition)|
                           +----------+-----------+
                                      |
         +----------------+-----------+-----------+----------------+
         |                |                       |                |
         v                v                       v                v
    [Frontend]          [API]                 [Backend]       [Database]
  Reactive WASM      OpenAPI/RPC            Business Logic     Postgres DDL
  View Component     Wire Schema             Domain Model      SQL Queries
```

---

## 2. Shared Semantic Projections

A single nominal type definition in NOVA carries its schema, validation rules, serialization, and storage layout:

```nova
struct User {
    id: UUID,
    name: String,
    email: String,
    created_at: Int,
}
invariant is_valid_email(email);
```

### Compiler-Generated Projections (Zero Code Duplication):
1. **Frontend (WASM/UI):** Emits typed view-model with reactive binding and client-side form validation matching `invariant is_valid_email(email)`.
2. **API Layer:** Emits binary / JSON serialization serializers and OpenAPI/TypeBox specifications.
3. **Backend Service:** Emits type-safe service handlers with static capability constraints.
4. **Database Storage:** Emits relational table DDL (`CREATE TABLE users (...)`) and parameterized SQL query builders.
5. **Documentation:** Emits human-readable API and schema documentation (`nova doc`).

---

## 3. Capabilities Across the Tier Boundary

NOVA's capability discipline strictly partitions what frontend and backend code can access:

| Tier | Available Capabilities | Prohibited Capabilities |
| :--- | :--- | :--- |
| **Frontend (Client / WASM)** | `dom: DOM`, `fetch: Fetch`, `storage: LocalStorage`, `history: History` | `Database`, `Filesystem`, `Process`, `Vault` |
| **Backend (Server / Node)** | `db: Database`, `fs: Filesystem`, `net: Network`, `vault: Secret`, `proc: Process` | Direct `DOM` manipulation |

The compiler statically prevents client components from invoking server capabilities (`E0102`), ensuring absolute architectural security without runtime proxy leaks.
