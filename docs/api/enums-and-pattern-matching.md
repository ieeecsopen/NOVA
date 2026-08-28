# Module `enums-and-pattern-matching.nova`

*Source file: `examples/enums-and-pattern-matching.nova`*

---

## Enums

### `enum Shape`
```nova
enum Shape {
    Circle(Int),
    Rectangle(Int, Int),
    Triangle(Int, Int),
}
```

## Functions

### `fn area`
```nova
fn area(s: Shape) -> Int
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```
