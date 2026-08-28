# RFC 0005 — Local Mutability and Loops

- **Status:** Implemented
- **Created:** 2026-08-28
- **Depends on:** RFC 0001
- **Tier:** Optional language feature ([DESIGN-PRINCIPLES.md](../docs/foundation/DESIGN-PRINCIPLES.md))

## 1. Summary

`let mut x = ...;` introduces a **frame-local, non-escaping** rebindable
variable; `x = expr;` rebinds it; `while` and `for` loop over it. This
is added *without* a memory model, and without waiting for one, because
it is provably alias-free: NOVA v0.2 has no reference or pointer type at
all, so nothing can hold a second handle to a local slot — the one
exception (a closure capturing a `mut` local) is caught and rejected by
the checker (§4), closing the only path by which this feature could
otherwise violate Constitution Article XI.

## 2. Problem

Milestone 1 (memory discipline) is undesigned. Without this RFC, NOVA
has no loop and no reassignment at all — every accumulation must be
written as recursion:

```nova
fn sum_to(n: Int) -> Int {
    fn go(i: Int, acc: Int) -> Int {
        if i >= n { acc } else { go(i + 1, acc + i) }
    }
    go(0, 0)
}
```

Correct, but unlike what "ordinary programming" (this phase's own
success criterion) looks like in any mainstream language, and a poor fit
for the CLI-program and HTTP-handler style examples this phase asks for.
The question this RFC answers: can *some* form of mutation be added
*before* Milestone 1, without contradicting it?

## 3. Design: why this is safe without a memory model

Constitution Article XI forbids the core from assuming unrestricted
aliasing. The risk with any mutable variable is exactly aliasing: if two
things can observe or write the same mutable slot, and one is not aware
of the other, that is the class of bug ownership systems exist to
prevent.

> **Claim.** A local variable that (a) cannot be referenced — there is no
> `&`, no pointer, no reference type in NOVA v0.2 at all — and (b) cannot
> be captured by an escaping closure, has **at most one live handle to
> it, always**. No aliasing is possible, because nothing exists in the
> language to construct a second handle.

(a) is true simply because NOVA v0.2 has not designed references yet —
this is a fact about the language's current poverty, and this RFC does
not change it. (b) requires an explicit rule, because a closure *can*
mention an enclosing variable by name (RFC 0001 already has captures);
without a rule, `let mut x = 0; let f = || x; ...; x = 1; f()` would let
the returned/stored closure and the enclosing scope both mutate `x`
after the closure has, conceptually, "left" — two live handles.

### 3.1 The rule

> **Rule (No mutable capture).** A lambda may not mention, in its body, a
> name that is bound `mut` in any enclosing scope.

Diagnostic `E0130`, in `check.py`'s `_check_no_mut_capture`, invoked
whenever a `Lambda` is checked. This is the one addition that makes §3's
claim actually hold, rather than merely usually holding.

### 3.2 Runtime representation, and why it is sound given §3.1

The reference evaluator (`eval.py`) represents every local binding as a
one-element list (a cell): `env[name] = [value]`. A nested scope's
`dict(env)` copy shares the *same* cell objects, so a write through a
loop body's nested block is visible after the loop — this is what makes
`while`/`for` correctly accumulate across iterations.

This would be **unsound in general** — sharing a mutable cell across two
independently-escaping references is aliasing — except that §3.1 already
guarantees the only things that ever share a cell are nested scopes
*within a single, still-executing call*. No `Closure` object is ever
built over a `mut` cell (the checker forbids the program that would
attempt it), so no cell is ever reachable from two places that can
outlive each other. The runtime implementation is simple *because* the
static rule already did the hard work.

### 3.3 What is deliberately not here

No mutable struct fields, no mutable collection elements, no assignment
through any lvalue more complex than a bare local name (RFC 0002's
`FieldAccess` is read-only; there is no `s.field = x`). Every one of
these would reintroduce exactly the aliasing question §3 answers only
for the bare-local case — a mutable field is reachable from every copy
of a struct value, which is not (in general) confined to one call frame.
This is why NOVA's collections (`std/list.nova`) are **persistent**
(functional/immutable), not mutable — see TYPE-SYSTEM.md and
[LANGUAGE-PHILOSOPHY.md entry 6](../docs/foundation/LANGUAGE-PHILOSOPHY.md#6-resource)
for why this is a deliberate design, not an oversight.

## 4. Design: loops

```nova
while cond { body }
for x in xs { body }
```

`for` requires its iterable to have type `List[T]` (checked exactly:
`check.py`'s `For` case requires a `TEnum` named `List`) — not a general
iterator protocol or trait. The reference evaluator walks the
`Cons`/`Nil` runtime representation directly (`eval.py`'s `For` case),
which works for *any* value of that shape, including one built entirely
by user code re-using `std/list.nova`'s enum, because nothing about `for`
is specific to the standard library's own functions.

Both `if`/`while`/`for`/`match` may appear as statements with no
trailing `;`, exactly when they are not the last expression in a block —
Rust's rule, adopted for the same reason: `while cond { x = x + 1; }
next_thing();` reads naturally with no forced semicolon after `}`.

## 5. Examples

### 5.1 Accepted

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

### 5.2 Rejected — assigning an immutable binding

```nova
fn f() -> Int { let x = 0; x = 1; x }
```
```
error[E0126]: cannot assign to `x`: not declared `mut`
```

### 5.3 Rejected — the case this RFC exists to prevent

```nova
fn bad() -> (() -> Int) {
    let mut x = 0;
    || x
}
```
```
error[E0130]: closure captures `mut` local `x`
```

## 6. Alternatives

**A. Wait for Milestone 1 and design references/mutation together.**
Rejected as unnecessarily conservative: §3's argument shows frame-local
mutation is independently safe *without* deciding anything about
references, regions, or aliasing in general. Waiting would cost every
program written before Milestone 1 an ordinary loop, for no soundness
benefit.

**B. Mutable function parameters (`fn f(mut x: Int)`).** Deferred, not
designed against: no example in this phase needed it, and it raises a
question (can a mutated parameter be observed by the caller? — no, by
value semantics, but is that obvious enough?) worth its own small RFC
rather than folding in here.

**C. General lvalues (`s.field = x`, `xs[i] = x`).** Rejected for the
reason in §3.3: both reintroduce the aliasing question this RFC
specifically avoids by restricting itself to bare locals.

## 7. Tradeoffs

- Accumulator-style code needs `mut`; everything else stays immutable by
  default, which is the intended bias (Constitution Article III ranks
  explicitness above ergonomics).
- `for` is coupled to one specific enum shape (`List`), not a general
  protocol — a real, named limitation, not a hidden one.

## 8. What this forecloses

Nothing: §3.3's exclusions are not implemented, so nothing has been
built that a future references/regions RFC would need to unbuild. This
is the reason the claim in §3 is safe to make now rather than waiting.

## 9. Costs

Zero additional runtime cost per binding beyond one extra list
indirection per read/write in the reference evaluator (irrelevant to a
future compiled backend, which can allocate a stack slot exactly as any
other local). Zero cost to programs that use no `mut` binding at all
(Constitutional Principle 10) — `let` without `mut` behaves exactly as
before this RFC.

## 10. Staging

Implemented: `let mut`, `Assign`, `while`, `for` over `List[T]`, the
no-mutable-capture check. Not implemented: mutable parameters, mutable
fields, mutable collection elements, general lvalues, iterator
protocols beyond `List[T]`.

## 11. Success criteria

- [x] Conformance tests 040–042 (mutation, illegal assignment, forbidden
      capture) pass.
- [x] `for` over `std/list.nova`'s `List[T]` works with no special
      casing beyond the `Cons`/`Nil` shape (conformance 044).
- [x] The soundness argument in §3 has an enforced, tested counterpart
      (`E0130`) rather than being merely asserted in prose.
