# NOVA — Backend Service Model

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
**Cross-References:** [FULL-STACK-MODEL.md](FULL-STACK-MODEL.md), [DATA-MODEL.md](DATA-MODEL.md), [SECURITY-MODEL.md](../language/SECURITY-MODEL.md)

---

## 1. Services as Capability-Bounded Interfaces

A backend service in NOVA is a typed specification of operations, where each endpoint declares the precise capabilities required to fulfill requests:

```nova
struct UserService {
    db: Database,
    vault: Secret,
}

impl UserService {
    fn get_user(self, id: UUID) -> Result[User, ServiceError] ! {Database} {
        self.db.query_one("SELECT * FROM users WHERE id = ?", id)
    }

    fn update_password(self, id: UUID, new_hash: String) -> Result<(), ServiceError> ! {Database, Secret} {
        let key = self.vault.unwrap_key("auth_pepper");
        let salted = hash_with_pepper(new_hash, key);
        self.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", salted, id)
    }
}
```

---

## 2. Authentication as an Unforgeable Capability

Rather than relying on ambient request headers or mutable session middleware, authentication produces an **unforgeable session capability**:

```nova
struct AuthToken {
    user_id: UUID,
    roles: List[String],
}

// Handler strictly requires an authenticated caller capability
fn delete_user_account(svc: UserService, caller: AuthToken, target_id: UUID) -> Result<(), Error> ! {Database} {
    if caller.user_id != target_id && !caller.roles.contains("admin") {
        return Result::Err(Error::Unauthorized);
    }
    svc.db.execute("DELETE FROM users WHERE id = ?", target_id)
}
```

---

## 3. Structured Concurrency and Background Workers

Background jobs operate under strict structured concurrency lifetimes:
* **No Orphan Background Tasks:** Sub-tasks are spawned within lexical task scopes and are cancelled cooperatively if the parent request scope terminates.
* **Bounded Resource Queues:** Workers receive attenuated database and network capabilities preventing resource exhaustion.
