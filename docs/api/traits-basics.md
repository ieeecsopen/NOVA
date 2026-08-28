# Module `traits-basics.nova`

*Source file: `examples/traits-basics.nova`*

---

## Structs

### `struct Point`
```nova
struct Point {
    x: Int,
    y: Int,
}
```

### `struct Circle`
```nova
struct Circle {
    radius: Int,
}
```

## Traits

### `trait Describe`
```nova
trait Describe {
    fn describe(self) -> String;
}
```

## Functions

### `fn announce`
```nova
fn announce(rt: Runtime, x: T) -> Int ! {Runtime}
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```
