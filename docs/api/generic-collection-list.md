# Module `generic-collection-list.nova`

*Source file: `examples/generic-collection-list.nova`*

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

### `fn double_all`
```nova
fn double_all(xs: List) -> List
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
