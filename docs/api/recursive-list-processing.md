# Module `recursive-list-processing.nova`

*Source file: `examples/recursive-list-processing.nova`*

---

## Enums

### `enum List`
```nova
enum List {
    Cons(T, List[T]),
    Nil,
}
```

## Functions

### `fn count_even`
```nova
fn count_even(xs: List) -> Int
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```

### `fn empty`
```nova
fn empty() -> List
```

### `fn prepend`
```nova
fn prepend(x: T, xs: List) -> List
```

### `fn len`
```nova
fn len(xs: List) -> Int
```

### `fn append`
```nova
fn append(xs: List, x: T) -> List
```

### `fn sum`
```nova
fn sum(xs: List) -> Int
```
