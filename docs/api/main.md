# Module `main.nova`

*Source file: `examples/module-system/main.nova`*

---

## Structs

### `struct Rectangle`
```nova
struct Rectangle {
    width: Int,
    height: Int,
}
```

## Functions

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

### `fn validate`
```nova
fn validate(r: Rectangle) -> Bool
```

### `fn area`
```nova
fn area(r: Rectangle) -> Int
```
