# Module `option-basics.nova`

*Source file: `examples/option-basics.nova`*

---

## Enums

### `enum Option`
```nova
enum Option {
    Some(T),
    None,
}
```

## Functions

### `fn find`
```nova
fn find(target: Int, a: Int, b: Int, c: Int) -> Option
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

### `fn unwrap_or`
```nova
fn unwrap_or(o: Option, default: T) -> T
```

### `fn is_some`
```nova
fn is_some(o: Option) -> Bool
```
