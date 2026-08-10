# NOVA — Language Reference (v0.2)

Phase 2 output. A complete, example-driven walkthrough of NOVA v0.2,
covering everything RFC 0001–0005 add. This is the document to read
top to bottom to learn the language; [SYNTAX.md](SYNTAX.md) is the
grammar and its principles, [TYPE-SYSTEM.md](TYPE-SYSTEM.md) is the type
system and its research decisions. Every example below is a real file
under [`examples/`](examples/), checked and run in CI
(`tools/check-all.sh`) — nothing here is aspirational prose.

```sh
python3 -m verifier.refspec check examples/hello.nova
python3 -m verifier.refspec run   examples/hello.nova
```

---

## 1. The execution model

A NOVA program is a computation with one distinguished entry point that
receives the **root capability** and returns an exit value
([LANGUAGE-PHILOSOPHY.md entry 3](LANGUAGE-PHILOSOPHY.md#3-program)):

```nova
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("hello from NOVA");
    0
}
```
— [`examples/hello.nova`](examples/hello.nova)

There is no `import std.io` and no free `print`. The authority to write
to the console arrived as `rt`, and `! {Runtime}` is the compiler
stating, checked, that it was used (RFC 0001).

## 2. Capabilities and effects

**Capabilities are the only source of authority** (RFC 0001 §4.1).
Obtaining a narrower capability from a broader one is itself an effect —
asking for power is a use of power:

```nova
fn measure(rt: Runtime) -> Int ! {Clock, Runtime} {
    let c = rt.clock();          // performs `Runtime`
    let start = c.now();         // performs `Clock`
    let end = c.now();
    end - start
}
```
— [`examples/timing.nova`](examples/timing.nova)

**A function's declared row is checked for equality, not subsumption**
(RFC 0001 §4.3) — over-declaring is an error exactly like
under-declaring. `= widen` is the one deliberate, greppable escape:

```nova
fn ping(c: Clock, rt: Runtime) -> Bool ! {Clock, Runtime} = widen {
    c.now();
    true
}
```
— [`examples/widen-and-audit.nova`](examples/widen-and-audit.nova); run
`nova audit` on it to see every widened signature listed.

**Row-polymorphic functions** are reusable across every effect, once:

```nova
fn with_retry[r](attempts: Int, f: () -> Int ! r) -> Int ! r {
    if attempts <= 1 { f() } else { with_retry(attempts - 1, f) }
}
```
— [`examples/retry.nova`](examples/retry.nova)

## 3. Functions, expressions, statements

```nova
fn add(a: Int, b: Int) -> Int { a + b }        // expression body, no `;`

fn f(x: Int) -> Int {
    let y = x + 1;      // statement, ends in `;`
    y * 2                // tail expression: the block's value
}
```

`if`/`while`/`for`/`match`/`{ }` are expressions; they need a trailing
`;` as a statement only when *not* the last thing in a block
(SYNTAX.md §5.4):

```nova
fn max(a: Int, b: Int) -> Int {
    if a > b { a } else { b }        // no `;` needed: this is the tail
}
```

## 4. Structs

Nominal product types (RFC 0002 §4.1) — two structs with identical
fields remain different types (TYPE-SYSTEM.md §2):

```nova
struct Point { x: Int, y: Int }

fn manhattan(p: Point) -> Int { p.x + p.y }

fn translate(p: Point, dx: Int, dy: Int) -> Point {
    Point { x: p.x + dx, y: p.y + dy }
}
```
— [`examples/structs-basic.nova`](examples/structs-basic.nova)

**A struct can bundle capabilities** — this is the example RFC 0002
exists to justify (its §3 resolves RFC 0001's open question about the
row of a stored capability: nothing new is needed; field access is
ordinary structural lookup, and the existing capability-use rule fires
on whatever type it resolves to):

```nova
struct Handler { rt: Runtime, c: Clock }

fn wrap(rt: Runtime, c: Clock) -> Handler {
    Handler { rt: rt, c: c }              // pure: forming a value performs nothing
}

fn handle(h: Handler, msg: String) -> Int ! {Clock, Runtime} {
    h.rt.print(msg);                       // performs `Runtime`, via a field
    h.c.now()                              // performs `Clock`, via a field
}
```
— [`examples/structs-and-capabilities.nova`](examples/structs-and-capabilities.nova)

## 5. Tuples

The one *structural* type (RFC 0002 §4.2, TYPE-SYSTEM.md §2) — no
declaration needed, `.0`/`.1`/... project by position:

```nova
fn swap(p: (Int, Bool)) -> (Bool, Int) { (p.1, p.0) }
fn divmod(a: Int, b: Int) -> (Int, Int) { (a / b, a - (a / b) * b) }
```
— [`examples/tuples.nova`](examples/tuples.nova). There is no
pattern-destructuring `let` in v0.2 — only `match` arms take patterns.

## 6. Enums and pattern matching

```nova
enum Shape { Circle(Int), Rectangle(Int, Int), Triangle(Int, Int) }

fn area(s: Shape) -> Int {
    match s {
        Shape::Circle(r) => 3 * r * r,
        Shape::Rectangle(w, h) => w * h,
        Shape::Triangle(base, height) => (base * height) / 2,
    }
}
```
— [`examples/enums-and-pattern-matching.nova`](examples/enums-and-pattern-matching.nova)

**Exhaustiveness is checked** (RFC 0002 §5.1) — delete an arm above and
`nova check` reports `E0220`, listing the missing variant by name. A
wildcard `_` (or a plain binding) satisfies exhaustiveness for any
scrutinee type, including non-enum ones.

## 7. Error handling: Option and Result

Both are **ordinary enums**, in `std/`, using nothing but what §6
already gave you (LANGUAGE-PHILOSOPHY.md entry 10's Guarantee ladder;
Constitutional Principle 3, "failure must have explicit semantics," met
by composition rather than by a new mechanism):

```nova
import std.option;

fn find(target: Int, a: Int, b: Int, c: Int) -> Option[Int] {
    if target == a { Option::Some(a) }
    else if target == b { Option::Some(b) }
    else if target == c { Option::Some(c) }
    else { Option::None }
}
```
— [`examples/option-basics.nova`](examples/option-basics.nova)

```nova
import std.result;

fn safe_div(a: Int, b: Int) -> Result[Int, String] {
    if b == 0 { Result::Err("division by zero") } else { Result::Ok(a / b) }
}

fn describe(r: Result[Int, String]) -> String {
    match r {
        Result::Ok(v) => "ok",
        Result::Err(e) => e,
    }
}
```
— [`examples/result-error-handling.nova`](examples/result-error-handling.nova)

## 8. Generics

Instantiation is always inferred from argument types (RFC 0003 §4) —
there is no `identity[Int](5)` syntax in v0.2:

```nova
fn identity[T](x: T) -> T { x }
fn pair[A, B](a: A, b: B) -> (A, B) { (a, b) }
```
— [`examples/generics-basics.nova`](examples/generics-basics.nova)

## 9. Traits

Method-call syntax is **the same syntax** as a capability operation
(RFC 0002 §6) — `.describe()` below, `.now()` in §2 — disambiguated
entirely by the receiver's type:

```nova
struct Point { x: Int, y: Int }
struct Circle { radius: Int }
trait Describe { fn describe(self) -> String; }

impl Describe for Point { fn describe(self) -> String { "a point" } }
impl Describe for Circle { fn describe(self) -> String { "a circle" } }

fn announce[T: Describe](rt: Runtime, x: T) -> Int ! {Runtime} {
    rt.print(x.describe());
    0
}
```
— [`examples/traits-basics.nova`](examples/traits-basics.nova)

**A generic struct with a generic impl** — a real v0.2 limitation shown
honestly in the same example: the impl is unconditional (no
`where T: Trait`), so it cannot itself require anything of the inner
type (RFC 0003 §5):

```nova
struct Box[T] { value: T }
trait Labeled { fn label(self) -> String; }
impl[T] Labeled for Box[T] { fn label(self) -> String { "a box" } }
```
— [`examples/generic-box-and-trait.nova`](examples/generic-box-and-trait.nova)

## 10. A generic collection, written in ordinary NOVA

`List[T]` (`std/list.nova`) is a persistent singly linked list — no
compiler special-casing at all (DESIGN-PRINCIPLES.md, Standard Library
tier). `for` walks its `Cons`/`Nil` shape directly:

```nova
import std.list;

fn double_all(xs: List[Int]) -> List[Int] {
    match xs {
        List::Cons(x, rest) => List::Cons(x * 2, double_all(rest)),
        List::Nil => List::Nil,
    }
}
```
— [`examples/generic-collection-list.nova`](examples/generic-collection-list.nova),
and user code can extend it the same way the standard library itself is
written — see
[`examples/recursive-list-processing.nova`](examples/recursive-list-processing.nova).

## 11. Local mutability and loops

`let mut` locals never escape their frame — there are no references in
NOVA v0.2 — so this needs no memory model (RFC 0005 §3, Constitution
Article XI):

```nova
fn sum_to(n: Int) -> Int {
    let mut total = 0;
    let mut i = 0;
    while i < n {
        total = total + i;
        i = i + 1;
    }
    total
}
```
— [`examples/mutability-and-loops.nova`](examples/mutability-and-loops.nova)

A closure may **not** capture a `mut` local (`E0130`) — the one rule
that makes the "no aliasing" claim actually hold, not merely usually
hold (RFC 0005 §3.1); see [`examples/rejected-programs.nova`](examples/rejected-programs.nova)
for the exact diagnostic.

## 12. Modules

A module is a file; `pub` marks what importers may see (RFC 0004):

```nova
// geometry.nova
pub struct Rectangle { width: Int, height: Int }
fn validate(r: Rectangle) -> Bool { r.width > 0 && r.height > 0 }   // private
pub fn area(r: Rectangle) -> Int { if validate(r) { r.width * r.height } else { 0 } }
```
```nova
// main.nova
import geometry;
fn main(rt: Runtime) -> Int ! {Runtime} {
    let r = Rectangle { width: 4, height: 5 };
    rt.print("computed an area");
    area(r)
}
```
— [`examples/module-system/`](examples/module-system/); its
`rejected.nova` shows what calling the private `validate` from outside
looks like (`E0120`), without being part of the checked example suite
itself.

**There is no qualified-name syntax** (RFC 0004 §2) — `import` controls
visibility, not namespacing; every name lives in one flat, globally
unique space. `import std.list;` makes `prepend`, `empty`, `len`, and
`List` itself available by their bare names, not as `list.prepend`.

## 13. A "CLI program"

NOVA v0.2 has no real argv/stdin capability yet — this simulates a fixed
command list rather than claiming real input handling exists, and says
so in the file:

```nova
enum Command { Add(Int, Int), Greet(String) }

fn run(rt: Runtime, cmd: Command) -> Int ! {Runtime} {
    match cmd {
        Command::Add(a, b) => { rt.print("add"); a + b },
        Command::Greet(name) => { rt.print(name); 0 },
    }
}
```
— [`examples/cli-program.nova`](examples/cli-program.nova)

## 14. A "small HTTP-like" example

Likewise, no real network capability exists yet; this shows the *shape*
such a program takes — structs, an enum, pattern-matched routing:

```nova
struct Request { method: Method, path: String }
struct Response { status: Int, body: String }
enum Method { Get, Post }

fn route(req: Request) -> Response {
    match req.method {
        Method::Get => match req.path {
            "/health" => Response { status: 200, body: "ok" },
            "/" => Response { status: 200, body: "welcome" },
            _ => Response { status: 404, body: "not found" },
        },
        Method::Post => Response { status: 405, body: "method not allowed" },
    }
}
```
— [`examples/http-like.nova`](examples/http-like.nova)

## 15. A capstone: all of it together

[`examples/combined-request-handler.nova`](examples/combined-request-handler.nova)
combines a capability-bundling struct, a `Result`-based validation step,
a trait, a module import, and a mutable accumulator over an imported
`List`, in one realistic-feeling program — and demonstrates RFC 0001's
strictness in the process: an earlier draft of this exact file declared
`! {Clock, Runtime}` on its handler, because the handler's `Context`
struct carries a `Clock`. The checker correctly rejected it — the
`Clock` is stored but never *used* (no `.now()` call anywhere), so the
true row is `{Runtime}` alone. Row-equality checking caught a real,
plausible over-declaration in the process of writing this reference,
which is the strongest demonstration available that RFC 0001 §4.3 is
being enforced, not just claimed.

## 16. Diagnostics reference

See [docs/diagnostics.md](docs/diagnostics.md) for the full index. New
in this phase: `E0111`–`E0130` (structs, enums, generics, traits,
modules, mutability) and `E0220` (non-exhaustive match).

## 17. What is not in v0.2

See [NON-GOALS.md](NON-GOALS.md) and TYPE-SYSTEM.md §10 for the full,
reasoned list. Concretely absent from every example above: explicit
generic instantiation syntax, conditional trait impls, trait objects,
default trait methods, mutable fields, general lvalues, qualified
import paths, floats, string formatting/interpolation, and a real
network or filesystem capability. Each is named, not hidden.
