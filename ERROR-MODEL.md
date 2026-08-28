# NOVA — Error & Failure Model

**Status:** Production Design Reference  
**Cross-References:** [CONTRACT-MODEL.md](CONTRACT-MODEL.md), [VERIFICATION-LEVELS.md](VERIFICATION-LEVELS.md), [EFFECT-SYSTEM.md](EFFECT-SYSTEM.md), [SECURITY-MODEL.md](SECURITY-MODEL.md)

---

## 1. Philosophical Principle: Errors are Domain Values

NOVA rejects untyped ambient exceptions (`throw` / `try-catch`). Exceptions violate capability isolation by allowing non-local control flow to jump across lexical boundaries without capability permission or type-level representation.

In NOVA:
* **Recoverable domain errors** are first-class algebraic values (`Result<T, E>`).
* **Unrecoverable failures** (bug, corruption, invariant breach) abort the fault domain deterministically without unwinding arbitrary user state.

---

## 2. The Nine Failure Categories

NOVA formally partitions failures into nine distinct semantic classes:

| Failure Category | Nature | Representation / Mechanism | Handling Strategy |
| :--- | :--- | :--- | :--- |
| **1. Expected Failure** | Valid domain outcome (e.g., key not found) | `Option<T>` | Pattern matching, `.unwrap_or()` |
| **2. Recoverable Failure** | Operational I/O or network failure | `Result<T, E>` | `?` operator, `.map_err()`, retry loops |
| **3. Unrecoverable Failure** | Logic bug, memory corruption, out of bounds | `panic!(msg)` / Trap | Fault isolation, process restart |
| **4. Timeout** | Operation exceeded allocated time deadline | `Result<T, TimeoutError>` | `Clock` capability deadline checking |
| **5. Cancellation** | Caller revoked execution request | `CancelToken` check | Explicit cooperative cancellation |
| **6. Resource Exhaustion** | Out of memory / file descriptors | `Result<T, ResourceError>` / Region abort | Bulk region reclaim, fallback allocation |
| **7. Security Violation** | Attempt to perform unheld capability effect | Compile-time rejection (`E0102`) | Statically blocked before execution |
| **8. Contract Violation** | Precondition or postcondition breached | Contract Fault / Panic | Blame assignment to caller or callee |
| **9. Remote Failure** | Downstream node / RPC crash | `Result<T, RemoteError>` | Circuit breaking, fallback values |

---

## 3. The `Result<T, E>` Type and Propagation

`Result<T, E>` is defined in the standard library (`std.result`):

```nova
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

### Propagation Ergonomics
The `?` operator unwraps `Ok(v)` or early-returns `Err(e)` with automatic error coercion:

```nova
fn read_config(fs: Filesystem, path: String) -> Result<Config, ConfigError> ! {Filesystem} {
    let raw = fs.read(path).map_err(|e| ConfigError::Io(e))?;
    let parsed = parse_json(raw).map_err(|e| ConfigError::Parse(e))?;
    Ok(parsed)
}
```

---

## 4. Failure Metadata and Context

Errors in NOVA can carry causal traces and structural metadata without ambient heap allocations:

```nova
struct ErrorContext<E> {
    error: E,
    operation: String,
    timestamp: Int,
    cause: Option<Box<ErrorContext<E>>>,
}

impl<E> ErrorContext<E> {
    fn wrap(err: E, op: String, c: Clock) -> ErrorContext<E> ! {Clock} {
        ErrorContext {
            error: err,
            operation: op,
            timestamp: c.now(),
            cause: Option::None,
        }
    }
}
```

---

## 5. Fault Domains & Process Boundaries

When an unrecoverable failure (`panic`) occurs:
1. **No Ambient Exception Catching:** User-level code cannot catch a panic within the same lexical region.
2. **Region Teardown:** The containing region is deallocated immediately in bulk, preventing memory leaks and data corruption.
3. **Actor / Process Isolation:** Unrecoverable failures propagate only to the supervising actor/process boundary via message passing.
