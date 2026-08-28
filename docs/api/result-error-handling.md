# Module `result-error-handling.nova`

*Source file: `examples/result-error-handling.nova`*

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

### `fn safe_div`
```nova
fn safe_div(a: Int, b: Int) -> Result
```

### `fn describe`
```nova
fn describe(r: Result) -> String
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
