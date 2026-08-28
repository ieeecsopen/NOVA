# Module `http-like.nova`

*Source file: `examples/http-like.nova`*

---

## Structs

### `struct Request`
```nova
struct Request {
    method: Method,
    path: String,
}
```

### `struct Response`
```nova
struct Response {
    status: Int,
    body: String,
}
```

## Enums

### `enum Method`
```nova
enum Method {
    Get,
    Post,
}
```

## Functions

### `fn route`
```nova
fn route(req: Request) -> Response
```

### `fn log_response`
```nova
fn log_response(rt: Runtime, resp: Response) -> Int ! {Runtime}
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```
