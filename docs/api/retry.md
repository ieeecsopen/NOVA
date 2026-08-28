# Module `retry.nova`

*Source file: `examples/retry.nova`*

---

## Functions

### `fn with_retry`
```nova
fn with_retry(attempts: Int, f: TFunExpr(span=Span(start=765, end=778), params=[], ret=TName(span=Span(start=771, end=774), name='Int', args=[]), eff=RowExpr(span=Span(start=777, end=778), labels=[], tail='r'))) -> Int
```

### `fn timed_read`
```nova
fn timed_read(c: Clock) -> Int ! {Clock}
```

### `fn pure_compute`
```nova
fn pure_compute() -> Int
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Clock, Runtime}
```
