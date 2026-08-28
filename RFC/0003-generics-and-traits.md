# RFC 0003 — Generics and Traits

- **Status:** Implemented
- **Created:** 2026-08-28
- **Depends on:** RFC 0001, RFC 0002
- **Tier:** Optional language feature ([DESIGN-PRINCIPLES.md](../docs/foundation/DESIGN-PRINCIPLES.md))

## 1. Summary

Parametric polymorphism (`fn identity[T](x: T) -> T`) and structural
trait bounds (`fn describe[T: Show](x: T) -> String`), checked by
extending RFC 0001's row-variable substitution machinery to ordinary type
variables — the same rigid/flexible discipline, the same `Subst` object,
one additional case in `unify_types`.

## 2. Problem

Without generics, RFC 0001 §2's `with_retry` is the *only* function that
can be written once and reused across types — because it is polymorphic
in its *row*, not in any ordinary type, and rows already had variables.
Every other reusable function (`identity`, a generic `List`, a `max`)
needed either duplication per type or (worse) an unsound escape hatch.

## 3. Design: type variables are row variables' twin

RFC 0001 already has: a rigid row variable, bound by an enclosing
`fn f[r](...)`; a flexible row variable, freshened at each call site
and solved by unification (`RowSubst`, now `Subst`, in `types.py`).

RFC 0003 adds exactly the same structure for ordinary types:

```
TVar("T")     -- rigid inside the function that declares [T]
TVar("?T1")   -- flexible, fresh, created at instantiation
```

`instantiate()` (RFC 0001, extended here) freshens **both** kinds of
rigid variable in one traversal, so a function that is simultaneously
row-polymorphic and type-polymorphic — `with_retry[T, r]`, if written
generically over its value type too — is instantiated in a single pass.
`unify_types` gained the corresponding case: a flexible type variable
binds to whatever it meets, exactly as a flexible row variable already
did (see §3.1 for the one subtlety this raised).

### 3.1 One subtlety found during implementation

A rigid type variable and a flexible one can share a *name* by
coincidence — e.g. `prepend[T](x: T, xs: List[T])` calling
`List::Cons(x, xs)`, where `List`'s own declared type parameter is also
named `T`. `unify_types`'s first implementation checked "is the LEFT
side a `TVar`?" and returned early in every branch of that check,
including when the left side was rigid and the right was a *different*,
flexible variable — so a rigid `T` meeting a fresh `?T1` (standing for
`List`'s own `T`, about to be solved to whatever `prepend`'s `T`
resolves to) was wrongly rejected as a mismatch.

The fix (now in `types.py`): check "is *either* side a flexible
variable?" **before** checking "is the left side rigid?". A flexible
variable binds to whatever it meets, in either position; only two
*rigid* variables (or a rigid variable and a concrete type) can fail to
unify. This is recorded here because it is exactly the kind of bug this
project's own conformance suites exist to catch, and it was caught by
`tests/manifest`-style construction (a real, non-contrived program — a
generic `prepend` calling a generic constructor) rather than by a
hand-written adversarial test, which is itself a small piece of evidence
for writing real code early.

## 4. Design: instantiation, entirely by argument-type inference

```nova
fn identity[T](x: T) -> T { x }
let five = identity(5);   // T solved to Int by unifying x's type against 5
```

**No explicit type-argument syntax** (`identity[Int](5)`) is supported in
v0.2. This is a deliberate, smaller scope (Article VI: smallest version
that captures 80% of the value) — every case in this RFC's examples and
in the 20+ programs in `examples/` is solved by ordinary argument-type
unification, the same mechanism RFC 0001 already used for row variables.
Explicit instantiation is deferred, not designed against.

## 5. Design: traits

```nova
trait Show { fn show(self) -> String; }
impl Show for Point { fn show(self) -> String { "a point" } }
```

- Trait method signatures exclude the implicit `self`; `self`'s type is
  literally `Self`, resolved (inside an `impl` body only) to that impl's
  concrete target type.
- **No default method bodies** in v0.2 — every `impl` must provide every
  method. Simpler; defaults are a plausible future extension.
- **No trait objects, no `dyn Trait`, no dynamic dispatch as a
  first-class value.** A generic bound `[T: Show]` is resolved
  statically: either `T` is a rigid type variable carrying the bound (its
  methods are looked up directly from the trait, inside a generic
  function body), or `T` has been unified to a concrete type, and the
  method is looked up from that type's `impl`.
- **Traits themselves are not generic** (`trait Container[T]` is not
  supported) — kept out to avoid a second, nested instantiation problem
  inside impl-lookup. A real, stated limitation, not an oversight.
- **One `impl` per `(trait, concrete type head)` pair.** `impl Show for
  Option[T]` is one impl covering every instantiation of `Option`, not a
  family conditioned on `T`'s own properties (no `where T: Show` — v0.2
  cannot express "an `Option[T]` is `Show` only if `T` is"). A real
  limitation; the impl registry key is `(trait_name, head_name)` and has
  no room for a condition on the impl's own type parameters.

### 5.1 Soundness: the impl must match the trait's contract

A caller's `MethodCall` is checked against the **trait's** declared
signature (`TraitInfo.methods`), never against whatever an individual
`impl` happens to have written. Nothing stops an `impl` block from being
internally inconsistent with its trait *unless it is checked separately*
— found and closed during implementation (`_check_impl_signature` in
`check.py`, diagnostic `E0127`): without it, an `impl` could declare
`fn show(self) -> Int` for a trait requiring `-> String`, its own body
would typecheck against its own (wrong) signature, and every caller —
checked against the trait's `-> String` — would be silently unsound at
runtime. This is exactly the kind of gap RFC 0001 §9's "two
implementations" discipline exists to catch, applied here within a
single implementation via deliberate adversarial testing
(conformance 037) rather than a second implementation, because a second
NOVA implementation does not yet exist (known issue I3).

### 5.2 Runtime dispatch is dynamic; static checking is not

The reference evaluator (`eval.py`) resolves a non-capability
`MethodCall` by inspecting the *runtime value's* head type tag
(`_runtime_head`) and searching the impl registry — a legitimate
reference-semantics simplification, not a claim about what a real
compiler must do. NOVA v0.2 has no trait objects, so dispatch is always
statically resolvable in principle; the interpreter is dynamically
typed throughout (Python values), and this is one more place that is
already true, not a new source of dynamism.

## 6. Examples

### 6.1 Accepted — generic function, inferred instantiation

```nova
fn identity[T](x: T) -> T { x }
fn main(rt: Runtime) -> Int ! {Runtime} {
    rt.print("ok");
    identity(5)
}
```

### 6.2 Accepted — trait method call

```nova
struct Point { x: Int, y: Int }
trait Show { fn show(self) -> String; }
impl Show for Point { fn show(self) -> String { "point" } }
fn describe(p: Point) -> String { p.show() }
```

### 6.3 Rejected — impl signature disagrees with its trait

```nova
impl Show for Point { fn show(self) -> Int { 0 } }
```
```
error[E0127]: `show` does not match trait `Show`'s declared signature
```

### 6.4 Rejected — incomplete impl

```nova
impl Show for Point { }
```
```
error[E0115]: missing implementation for `show`
```

## 7. Alternatives

**A. Trait objects / dynamic dispatch from the start.** Rejected for
v0.2: adds a second dispatch mechanism (vtables or an equivalent) before
static, monomorphizable dispatch is even validated. Revisit once real
programs show a need for heterogeneous collections of trait values.

**B. Explicit-only instantiation (`identity[Int](5)` required).**
Rejected: strictly more ceremony for zero examples in this phase that
need it. Argument-type inference already exists for row variables; not
reusing it for type variables would be the asymmetric choice.

**C. Conditional impls (`impl[T] Show for Option[T] where T: Show`).**
Rejected for v0.2 as the harder, second half of a generics-and-traits
system; recorded as a real limitation (§5) rather than solved partially.

## 8. Tradeoffs

- No conditional impls, no trait objects, no default methods, no
  explicit instantiation syntax — four real limitations, each named
  rather than hidden.
- Traits with colliding method names across multiple `impl`s for the
  same concrete type would be resolved by whichever the registry
  iteration finds first (`check.py`'s `MethodCall` lookup takes
  `found[0]`) — an ambiguity the checker does not currently detect or
  reject. Recorded as a known gap (see `docs/known-issues.md`).

## 9. What this forecloses

Choosing "traits are not generic" (§5) forecloses `Container[T]`-style
trait families without a follow-up RFC; choosing "one impl per
(trait, head)" forecloses conditional impls the same way.

## 10. Costs

Instantiation is one substitution pass per call site, the same
asymptotic cost RFC 0001 already paid for row-polymorphic calls.
Unmeasured, per `benchmarks/README.md`.

## 11. Staging

Implemented: generic functions, generic structs/enums, argument-inferred
instantiation, non-generic traits, single (non-conditional) impls,
static-only dispatch. Not implemented: explicit instantiation, default
methods, conditional impls, trait objects, generic traits.

## 12. Success criteria

- [x] `identity`, generic `List`/`Option`/`Result`, and trait dispatch
      all typecheck and run (conformance 034–038, `std/list.nova`,
      `std/option.nova`, `std/result.nova`).
- [x] The impl/trait signature-mismatch hole is closed and tested
      (conformance 037).
- [x] The rigid/flexible unification bug (§3.1) is fixed and would be
      caught by regression if reintroduced (any generic recursive
      function reusing a type-parameter name exercises it).
