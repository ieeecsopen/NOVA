# Module `structs-basic.nova`

*Source file: `examples/structs-basic.nova`*

---

## Structs

### `struct Point`
```nova
struct Point {
    x: Int,
    y: Int,
}
```

## Functions

### `fn manhattan`
```nova
fn manhattan(p: Point) -> Int
```

### `fn translate`
```nova
fn translate(p: Point, dx: Int, dy: Int) -> Point
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```
