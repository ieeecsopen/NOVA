# Module `structs-and-capabilities.nova`

*Source file: `examples/structs-and-capabilities.nova`*

---

## Structs

### `struct Handler`
```nova
struct Handler {
    rt: Runtime,
    c: Clock,
}
```

## Functions

### `fn wrap`
```nova
fn wrap(rt: Runtime, c: Clock) -> Handler
```

### `fn handle`
```nova
fn handle(h: Handler, msg: String) -> Int ! {Clock, Runtime}
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Clock, Runtime}
```
