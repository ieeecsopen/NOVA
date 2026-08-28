# RFC 0002 — Structs, Tuples, Enums, and Pattern Matching

- **Status:** Implemented
- **Created:** 2026-08-28
- **Depends on:** RFC 0001
- **Resolves:** RFC 0001 §11 open question 3 ("what is the row of a
  stored capability?")
- **Tier:** Optional language feature ([DESIGN-PRINCIPLES.md](../docs/foundation/DESIGN-PRINCIPLES.md))

## 1. Summary

NOVA gains product types (structs, the sole *structural* exception:
tuples) and sum types (enums), plus pattern matching to consume them,
with **exhaustiveness checked** for enum matches. This is Phase 2's
entry into Milestone 2 ("Abstraction").

The central technical result: **no new effect-system rule is needed.**
RFC 0001 §11.3 asked what happens when a capability is stored in a
struct field. The answer, established by construction rather than by a
new typing rule: a struct's field types are ordinary, always-inspectable
structural information — unlike a closure's captured environment, there
is no "capture" step that could hide a field's type. `FieldAccess` is
ordinary structural projection; when its resolved type happens to be a
capability type, RFC 0001's existing `MethodCall` capability-use rule
fires exactly as if the value had been a bare parameter. See §3.

## 2. Problem

Concretely, before this RFC, NOVA could not express a request handler
that bundles its dependencies:

```nova
fn handle(rt: Runtime, c: Clock, db: Database, req: String) -> Int ! {Runtime, Clock, Database} {
    ...
}
```

Every capability a function needs must be a separate parameter, because
there is no way to group them. Real programs bundle dependencies into a
"handler" or "context" struct precisely to avoid this. RFC 0001 deferred
this (implicitly, by having no product types at all) because it raised a
real question: if a struct *could* hold a capability, would storing one
inside it silently launder authority past the row, the way an early
closure design could (RFC 0001 §5.4)?

## 3. Design: why structs cannot launder authority

Compare the two "hiding" mechanisms directly.

**A closure's free variables are not part of its declared type.**
`|| c.now()` has type `() -> Int`, and nothing in that written type says
it captured `c`. RFC 0001 §4.3 had to add a rule — the row moves into the
arrow at closure-formation — specifically because the alternative (no
rule) would make the type lie.

**A struct's fields are always part of its declared type.**

```nova
struct Handler { c: Clock }
```

Every value of type `Handler` is known, from the declaration alone
(inspectable by any tool, with no runtime information needed), to carry
a `Clock`. There is no "capture" step — `Handler { c: c }` is an ordinary
expression whose type (`Handler`) already, fully, statically describes
what it contains. A reader does not need to see the constructor call to
know a `Handler` holds a `Clock`; the type says so.

Consequently:

> **Rule (Field projection).** `e.field` is ordinary structural type
> lookup: if `e : Handler` and `Handler` declares `c: Clock`, then
> `e.c : Clock`. No effect is introduced by the projection itself.

And RFC 0001's existing rule for capability use — `(CapUse)`, generalized
in this RFC to `MethodCall`'s capability branch — requires no change:

```nova
fn run(h: Handler) -> Int ! {Clock} {
    h.c.now()
}
```

`h.c` has type `Clock` (Rule (Field projection)); `.now()` on a `Clock`
is `MethodCall`'s existing capability-op branch, contributing `{Clock}`
to the row, exactly as if `c` had arrived as a bare parameter. **Nothing
in the checker special-cases this** — `verifier/refspec/check.py`'s
`FieldAccess` case does plain structural lookup, and `MethodCall`
dispatches on the *resolved type* of its receiver, whatever expression
produced that receiver.

**Constructing** a struct that holds a capability is pure, by the same
reasoning that closure-formation is pure (RFC 0001 rule (Abs)): forming
a value performs nothing; only *using* what it holds does.

```nova
fn wrap(c: Clock) -> Handler { Handler { c: c } }   // : Handler, row {}
```

## 4. Design: the types

### 4.1 Structs — nominal

```nova
struct Point { x: Int, y: Int }
struct Meters { x: Int, y: Int }   // a DIFFERENT type from Point
```

Two structs with identical fields remain distinct types. See
TYPE-SYSTEM.md, "Nominal vs structural," for the full argument; in
short, structural typing for named product types makes accidental
substitution silent (TypeScript's structural typing is explicitly
critiqued for this in
[COMPETITIVE-ANALYSIS.md](../research/COMPETITIVE-ANALYSIS.md)), and NOVA's
priority order (Constitution Article III) puts explicit semantics above
the convenience structural typing buys.

Construction: `Point { x: 1, y: 2 }`. Every field must be given exactly
once; missing or extra fields are `E0117`.

Field access: `p.x`. Field access is **not** a call — no parentheses —
which is how it is distinguished from a method call on the same
receiver, both syntactically (a `MethodCall` always has `(...)`, even
empty) and in the checker (§6).

### 4.2 Tuples — the one structural type

```nova
fn swap(p: (Int, Bool)) -> (Bool, Int) { (p.1, p.0) }
```

Tuples need no declaration and no name; `.0`, `.1`, ... project by
position. This is NOVA's single deliberate exception to nominal typing,
because an anonymous product needs no identity beyond its shape — see
TYPE-SYSTEM.md for why this does not weaken the nominal-typing argument
for everything else.

### 4.3 Enums — nominal tagged unions

```nova
enum Option[T] { Some(T), None }
enum Result[T, E] { Ok(T), Err(E) }
```

Variants carry **positional** fields only in v0.2 (no struct-like
variants — Constitution Article VI: smallest version that captures the
value; struct-variants are a plausible future extension, not a design
gap being hidden). Construction: `Option::Some(5)`, `Option::None`.

### 4.4 Recursive types, for free

```nova
enum List[T] { Cons(T, List[T]), Nil }
```

An enum may refer to itself (or to a struct not yet finished parsing) in
its own field types, because declaration collection happens in two
passes (`Checker.collect`): every nominal name is registered before any
field or variant type is resolved. This is what makes `std/list.nova`'s
persistent list — written entirely in ordinary NOVA, no compiler
special-casing — possible at all.

## 5. Design: pattern matching

```nova
match o {
    Option::Some(n) => n,
    Option::None => 0,
}
```

Patterns: literals (`0`, `"s"`, `true`), `_` (wildcard), a bare
identifier (binds), tuple patterns `(a, b)`, and variant patterns
`Name::Variant(sub, ...)`, nested arbitrarily.

### 5.1 Exhaustiveness

> **Rule (Exhaustiveness).** A `match` over an enum-typed scrutinee must
> cover every variant, or include a wildcard/binding arm. A `match` over
> any other scrutinee type (`Int`, `Bool`, `String`, a tuple) must
> include a wildcard/binding arm — NOVA does not attempt exhaustiveness
> over non-enum shapes in v0.2.

Diagnostic `E0220`. This is checked, not advisory — a non-exhaustive
match over an enum is a compile error, not a runtime panic waiting to
happen. Enum-only exhaustiveness (rather than general refinement-based
exhaustiveness, e.g. proving `if`/`else` chains over integers are
complete) is the smallest version that captures the main value: the
overwhelming majority of exhaustiveness bugs are "forgot a variant," not
"forgot an integer."

## 6. Method-call syntax, unified

RFC 0003 (generics and traits) needs method-call syntax
(`recv.method(args)`) for trait dispatch. Rather than invent a second
call syntax alongside RFC 0001's capability-operation syntax
(`recv.op(args)`), **the two are the same syntax**, disambiguated by the
receiver's *resolved type*, not by anything at the call site:

- receiver type is a capability type → RFC 0001's rule: the row gains
  the capability's label.
- receiver type is a struct/enum/ground type with a matching trait
  `impl` → ordinary method dispatch, contributing nothing to the row.

The AST node RFC 0001 called `CapUse` is renamed `MethodCall` and kept
as `CapUse = MethodCall` for any code still spelling the old name. This
is Constitution Article VI question 7 ("can this be simpler?") answered
concretely: one syntax, one AST node, a receiver-type-driven checker
branch — not two parallel mechanisms that happen to look alike.

## 7. Examples

### 7.1 Accepted — the motivating case

```nova
struct Handler { c: Clock }
fn run(h: Handler) -> Int ! {Clock} { h.c.now() }
```

### 7.2 Rejected — under-declaring through a field, exactly as through a parameter

```nova
fn run(h: Handler) -> Int { h.c.now() }
```
```
error[E0201]: function performs undeclared effects {Clock}
```

### 7.3 Rejected — field mismatch

```nova
struct Point { x: Int, y: Int }
fn bad() -> Point { Point { x: 1 } }
```
```
error[E0117]: `Point` field mismatch: missing y
```

### 7.4 Rejected — non-exhaustive match

```nova
enum Option[T] { Some(T), None }
fn bad(o: Option[Int]) -> Int { match o { Option::Some(n) => n } }
```
```
error[E0220]: non-exhaustive match: missing `None`
```

## 8. Alternatives

**A. Structural product types (row-typed records, TypeScript-style).**
Rejected: silent substitutability between differently-intended types is
exactly the failure mode NOVA's priority order (explicitness over
ergonomics) rules out. See TYPE-SYSTEM.md.

**B. General (non-enum) exhaustiveness checking, e.g. integer range
analysis.** Rejected for v0.2 as disproportionate: the value is
concentrated in enum coverage, and general refinement-based
exhaustiveness is Milestone 6 territory (SMT-backed), not a v0.2 pattern
match.

**C. A distinct method-call syntax from capability-operation syntax.**
Rejected in §6: one syntax, receiver-type-driven, is simpler and the
existing mechanism already generalizes.

## 9. Tradeoffs

- **No struct-variants.** `enum Shape { Circle { radius: Int } }` is not
  supported; only `Circle(Int)`. A real limitation, deferred.
- **Reachability (`reachability.py`) under-approximates through field
  projection** — it does not track *which* field of a struct holds a
  capability, only whole-variable bindings (documented in the module's
  own comments). This is sound (the pass is advisory; §3's rule is
  enforced by the checker, not by this pass) but means the `audit`
  tool's output is less precise for capabilities reached through a
  struct than for bare parameters.
- **Match arms must agree on a single result type.** No arm-by-arm
  subtyping or coercion; this follows from NOVA having no subtyping at
  all (TYPE-SYSTEM.md).

## 10. What this forecloses

Choosing nominal struct/enum types forecloses later adopting structural
typing for them without breaking every program that relies on nominal
distinctness (Constitution Article IV's retrofitting test, applied here
by choice rather than necessity — nominal was chosen deliberately, but
the foreclosure is real and worth naming).

## 11. Costs

- **Compile time:** two-pass declaration collection is linear in
  declaration count; substitution (`substitute()`, `types.py`) is linear
  in type size. Unmeasured against Milestone 0's cost claims (still
  outstanding per `benchmarks/README.md`).
- **Reader cost:** a struct-typed function signature is exactly as wide
  as its fields suggest — no hidden cost for readers who don't use
  generics or traits (Constitutional Principle 10).

## 12. Staging

Implemented in `verifier/refspec/{ast,parser,check,eval,reachability}.py`.
Struct-variants, refinement-based exhaustiveness, and pattern guards
(`Some(n) if n > 0 => ...`) are not implemented and not designed.

## 13. Success criteria

- [x] `verifier/refspec/*.py` implements structs, tuples, enums, match,
      exhaustiveness.
- [x] Conformance tests 026–033 (structs, field-through-capability,
      enums, exhaustiveness) pass.
- [x] `std/list.nova`, `std/option.nova`, `std/result.nova` are written
      in ordinary NOVA using exactly this RFC's mechanisms, with no
      compiler special-casing.
- [x] RFC 0001 §11 open question 3 is answered (this document, §3).
