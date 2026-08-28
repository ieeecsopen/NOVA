# Module `combined-request-handler.nova`

*Source file: `examples/combined-request-handler.nova`*

---

## Structs

### `struct Context`
```nova
struct Context {
    rt: Runtime,
    c: Clock,
}
```

### `struct Request`
```nova
struct Request {
    path: String,
    amount: Int,
}
```

## Enums

### `enum List`
```nova
enum List {
    Cons(T, List[T]),
    Nil,
}
```

### `enum Result`
```nova
enum Result {
    Ok(T),
    Err(E),
}
```

## Traits

### `trait Summarize`
```nova
trait Summarize {
    fn summarize(self) -> String;
}
```

## Functions

### `fn validate`
```nova
fn validate(req: Request) -> Result
```

### `fn handle`
```nova
fn handle(ctx: Context, req: Request) -> Int ! {Runtime}
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

### `fn unwrap_or`
```nova
fn unwrap_or(r: Result, default: T) -> T
```

### `fn is_ok`
```nova
fn is_ok(r: Result) -> Bool
```
