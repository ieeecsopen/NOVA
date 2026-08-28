# Module `failure-lifecycle.nova`

*Source file: `examples/failure-lifecycle.nova`*

---

## Enums

### `enum Result`
```nova
enum Result {
    Ok(T),
    Err(E),
}
```

## Functions

### `fn try_operation`
```nova
fn try_operation(attempt: Int) -> Result
```

### `fn retry_operation`
```nova
fn retry_operation(rt: Runtime, attempt: Int, max_retries: Int) -> Result ! {Runtime}
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

### `fn unwrap_or`
```nova
fn unwrap_or(r: Result, default: T) -> T
```

### `fn is_ok`
```nova
fn is_ok(r: Result) -> Bool
```
