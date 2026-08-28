# Module `generic-box-and-trait.nova`

*Source file: `examples/generic-box-and-trait.nova`*

---

## Structs

### `struct Box`
```nova
struct Box {
    value: T,
}
```

## Traits

### `trait Labeled`
```nova
trait Labeled {
    fn label(self) -> String;
}
```

## Functions

### `fn describe_box`
```nova
fn describe_box(rt: Runtime, b: Box) -> Int ! {Runtime}
```

### `fn main`
```nova
fn main(rt: Runtime) -> Int ! {Runtime}
```
