# NOVA Syntax Cheatsheet

This is a concise reference for the v0.2 surface syntax. For the full grammar and rationale, see [SYNTAX.md](SYNTAX.md) and [LANGUAGE-REFERENCE.md](LANGUAGE-REFERENCE.md).

## 1. Variables and control flow

```nova
let x = 42;
let y = x + 1;

mut count = 0;
count = count + 1;

if count > 10 {
    count = 0;
} else {
    count = count + 1;
}

while count < 3 {
    count = count + 1;
}
```

- `let` binds immutable values.
- `mut` marks a variable that can be reassigned.
- `if`, `else`, `while`, `for`, and `match` are block-form expressions.
- `;` ends statements; a block's final expression does not need a trailing `;`.

## 2. Functions and effect rows

```nova
fn add(a: Int, b: Int) -> Int {
    a + b
}

fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("hello from NOVA");
    0
}

fn with_retry[r](attempts: Int, f: () -> Int ! r) -> Int ! r {
    if attempts <= 1 { f() } else { with_retry(attempts - 1, f) }
}
```

- Function signatures use `->` and optional effect rows after `!`.
- Effect rows are written like `{Runtime}`, `{Clock, Runtime}`, or a row variable such as `r`.
- `= widen` allows a deliberate widening annotation:

```nova
fn ping(c: Clock, rt: Runtime) -> Bool ! {Clock, Runtime} = widen {
    c.now();
    true
}
```

## 3. Capabilities and authority

```nova
capability Clock {
    fn now(self) -> Int;
}

fn measure(rt: Runtime, c: Clock) -> Int ! {Clock, Runtime} {
    let start = c.now();
    let end = c.now();
    end - start
}
```

- Capabilities are authority handles, not plain values.
- A function's effect row records every capability it uses.
- A closure captures authority in its type; it cannot hide it behind a pure-looking signature.

## 4. Structs, tuples, and enums

```nova
struct Point { x: Int, y: Int }

fn origin() -> Point {
    Point { x: 0, y: 0 }
}

fn manhattan(p: Point) -> Int {
    p.x + p.y
}

fn swap(pair: (Int, Bool)) -> (Bool, Int) {
    (pair.1, pair.0)
}

enum Shape {
    Circle(Int),
    Rectangle(Int, Int),
    Triangle(Int, Int),
}
```

- Structs are nominal product types.
- Tuples are structural and use `.0`, `.1`, ... for field projection.
- Enums define named variants with payloads.

## 5. Pattern matching

```nova
fn area(s: Shape) -> Int {
    match s {
        Shape::Circle(r) => 3 * r * r,
        Shape::Rectangle(w, h) => w * h,
        Shape::Triangle(base, height) => (base * height) / 2,
    }
}

fn describe(opt: Option[Int]) -> String {
    match opt {
        Option::Some(v) => "some",
        Option::None => "none",
    }
}
```

- Match arms use `=>`.
- Exhaustiveness is checked; missing cases produce an error.
- `_` or a plain binding can act as a wildcard catch-all.

## 6. Traits and generics

```nova
trait Show { fn show(self) -> String; }

impl Show for Point {
    fn show(self) -> String {
        "(" + self.x.to_string() + ", " + self.y.to_string() + ")"
    }
}

fn identity[T](x: T) -> T { x }

fn pair[A, B](a: A, b: B) -> (A, B) {
    (a, b)
}
```

- Generic parameters use a single `[...]` binder on declarations.
- Traits define method requirements; `impl` provides implementations.
- Type inference fills generic arguments automatically.

## 7. Common rules to remember

- Use `fn name(params) -> Type [! Row]` for function signatures.
- Use `struct Name { field: Type, ... }` for records.
- Use `enum Name { Variant[(Type, ...)], ... }` for tagged unions.
- Use `match` for data-driven control flow and exhaustiveness checks.
- Capability operations are tracked in the effect row, not hidden by wrappers.

For the authoritative behavior and examples, check the real conformance files under [tests/conformance/](../../tests/conformance/) and the checked examples under [examples/](../../examples/).
