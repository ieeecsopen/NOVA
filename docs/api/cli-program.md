# Module `cli-program.nova`

*Source file: `examples/cli-program.nova`*

---

## Enums

### `enum Command`
```nova
enum Command {
    Add(Int, Int),
    Greet(String),
}
```

### `enum List`
```nova
enum List {
    Cons(T, List[T]),
    Nil,
}
```

## Functions

### `fn run`
```nova
fn run(rt: Runtime, cmd: Command) -> Int ! {Runtime}
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
