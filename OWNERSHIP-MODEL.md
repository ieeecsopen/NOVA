# NOVA — Ownership Model

Milestone 1. The concrete mechanism decided in
[MEMORY-MODEL.md §7](MEMORY-MODEL.md#7-the-design-and-how-it-resolves-theme-b):
regions as the unit of ownership, with linearity applied to one specific
axis of the capability system rather than to capabilities as a whole.

This document defines the mechanism precisely enough to implement twice
(Constitution Article IX) and states, for every rule, what it forecloses
and what it costs — the same discipline [RFC 0001](RFC/0001-core-capability-effects.md)
already held itself to.

---

## 1. Vocabulary

Extends [LANGUAGE-PHILOSOPHY.md](LANGUAGE-PHILOSOPHY.md); new terms:

- **Region.** A contiguous lifetime scope that owns a set of heap
  values. A region is opened, used, and closed exactly once; closing a
  region deallocates everything in it in one operation. A region *is a
  capability* (§3) — [LANGUAGE-PHILOSOPHY.md entry 7](LANGUAGE-PHILOSOPHY.md#7-capability)'s
  definition applies unmodified.
- **Owning reference.** A value that determines when its region closes
  — when the owning reference goes out of scope (ordinary lexical
  scoping, exactly as RFC 0005's `mut` locals already use), the region
  closes.
- **Shared region capability** (`&Region`). Grants read access to every
  value in a region. Freely copyable — many holders may coexist, exactly
  like any other RFC 0001 capability.
- **Exclusive region capability** (`&mut Region`). Grants read *and
  write* access, and is **linear** (§4): it has exactly one holder at
  any point in the program, and using it (passing it to a function)
  *moves* it, exactly as a linear value moves in Austral.
- **Affine value.** An ordinary NOVA value (Int, a struct, an enum) used
  at most once without an explicit `.clone()` — Rust's `Copy`/`Clone`
  split, unmodified, because §2 of MEMORY-MODEL.md found no reason to
  redesign it.

## 2. The core claim, stated as a typing discipline

> **A region's data may be read by any number of holders of its shared
> capability, or written by exactly one holder of its exclusive
> capability, never both at once.** Both capabilities are ordinary,
> first-class RFC 0001 values; only the *exclusive* one is linear.

This single sentence is the whole mechanism. Everything below is this
sentence made precise enough to check.

## 3. Regions are capabilities — syntax and typing

```nova
region r {
    let owner: Region = r;
    // `owner` is the single owning reference; the region closes
    // when `r`'s scope ends, exactly like a `let mut` local's frame
    // (RFC 0005 §3) -- no named lifetime, no annotation beyond the
    // block itself.
}
```

A region block introduces a fresh `Region` capability, scoped to the
block, exactly as `main`'s `Runtime` is scoped to the whole program
(RFC 0001 §4.7) — a region is simply a *narrower*, block-scoped root
capability, obtained the same way any other capability is narrowed
(RFC 0001 §4.6, attenuation): `region { ... }` is sugar for "attenuate a
fresh memory-management capability from whatever encloses this scope,
valid for exactly this block."

**Allocating into a region:**

```nova
fn alloc[T](r: Region, value: T) -> InRegion[T] { ... }
```

`InRegion[T]` is a value's region-tagged type — a value allocated in
region `r` has type `InRegion[T]` tagged with `r`'s identity, so the
checker can verify a reference never escapes past its region's closing
(§5).

## 4. Exclusive access is linear — the resolution of Theme B in full

RFC 0001's capabilities are copyable, first-class values with no
restriction on how many places may hold one. That is exactly wrong for
mutation: if two holders of "permission to mutate this region" could
coexist, two writers could race, or a reader could observe a
half-written value — precisely the property §2 promises never happens.

**The fix is not to make capabilities second-class** (Effekt's route,
which [DESIGN-OPPORTUNITIES.md Theme B](DESIGN-OPPORTUNITIES.md#3-theme-b--ownership-scope-and-lifetime-are-one-mechanism)
worried NOVA would be forced into). It is to add exactly one refinement
to exactly one *kind* of capability:

> **Rule (Linear exclusivity).** A value of type `&mut Region` cannot be
> copied. Passing it to a function moves it: the caller loses access,
> the callee gains it. It must be used along every control-flow path
> (returned, passed onward, or the region closed) — dropping it
> silently is a checked error, exactly as Austral's linear values
> require an explicit consuming use (MEMORY-MODEL.md §3.6).

Every *other* capability — `Runtime`, `Clock`, a user-declared
`capability`, and `&Region` (the shared, read-only form) — is completely
unaffected: still first-class, still freely copyable, still exactly
what RFC 0001 §4.1 defined. **RFC 0001 needed no revision.** Its
Revisions section records this outcome plainly.

### 4.1 Why this, and not Rust's borrow checker

Rust enforces the same exclusivity rule (`&mut T` vs `&T`) but does it
*per value*, with a lifetime parameter tracking exactly how long each
individual borrow lasts, checked against every other borrow of the same
or overlapping data. NOVA enforces it *per region*: the question is
never "does this reference's lifetime overlap that one's" (Rust), only
"is the region's exclusive capability currently moved away or not"
(NOVA) — a strictly coarser, and strictly simpler, question. This is
[MEMORY-MODEL.md §2](MEMORY-MODEL.md#2-rust-evaluated-honestly-before-anything-is-proposed)'s
"mental overhead" cost addressed directly, at the cost of some
precision: two disjoint fields of the same region cannot be
mutably-borrowed independently in NOVA the way Rust's field-level borrow
splitting allows (§8, a named limitation, not a hidden one).

### 4.2 No named lifetimes, anywhere

Because exclusivity is tracked at the region level and a region's
lifetime is exactly its lexical scope (§3), there is no construct in
NOVA source that names a lifetime. "How long is this borrow valid"
is always answered by "until this region's block ends," which is
visible in the program text without a separate annotation language —
directly satisfying the brief's instruction not to add lifetime syntax
because Rust has it.

## 5. What the checker verifies

Three checked properties, each mapped to [MEMORY-MODEL.md §1](MEMORY-MODEL.md#1-what-must-be-prevented-made-precise)'s
table:

1. **No reference to `InRegion[T]` data escapes its region's scope.**
   (Prevents use-after-free, dangling references.) Checked the same way
   RFC 0005's `_check_no_mut_capture` already checks that a closure
   cannot capture a `mut` local: a value tagged with region `r` may not
   be returned from, or captured by a closure escaping, `r`'s own block
   — see [`regionlab/checker.py`](regionlab/checker.py) `check_escape`.
2. **`&mut Region` is never duplicated.** (Prevents data races and
   invalid concurrent mutation.) Checked exactly as any linear value:
   a use consumes it; a second use without a fresh acquisition is
   `E1002`.
3. **A region is closed exactly once**, at scope exit, never by
   explicit call. (Prevents double-free — there is no `free`/`drop`
   function to call twice.) This is not a checked rule so much as a
   consequence of there being no syntax for it: closing is a side
   effect of a block ending, full stop.

## 6. Interaction with Phase 2's type system

**Structs and enums need no region annotation on their own declaration.**
This mirrors RFC 0002 §3's resolution for capabilities exactly: a
struct's *fields* may be region-tagged (a field of type `InRegion[T]`),
but the struct type itself carries no special marker — region-safety is
a property of *values*, checked at the point a value is constructed,
read, or allowed to escape, not a property baked into every type
declaration. The same "no new rule needed, existing structural checking
generalizes" argument RFC 0002 made for capabilities applies here.

**Generics interact with regions at the value level, not the type
level**, for the same reason: `fn identity[T](x: T) -> T` already works
unmodified whether `T` happens to be region-tagged or not, because
region-tagging is carried on the concrete type substituted for `T`,
exactly as RFC 0003's existing substitution machinery (`substitute()`,
`types.py`) already carries any other property of a concrete type
through instantiation.

**Send/Share are derived properties, not a second trait mechanism.**
Rust needs `Send`/`Sync` as a separate, auto-derived unsafe-trait layer
on top of ownership (MEMORY-MODEL.md §2.5's mutability-polymorphism gap
is a symptom of the same "bolted on separately" pattern). NOVA derives
both directly from §2's rule:

- a region whose *exclusive* capability is held is safely **movable**
  across a task boundary (`Send`-equivalent) by construction — moving
  `&mut Region` is just an ordinary linear move, and the region's old
  holder loses access, so there is nothing left behind to race with;
- a region accessed only through its **shared** capability is safely
  **concurrently readable** (`Share`-equivalent) by construction — every
  holder of `&Region` has read-only access, so concurrent holders never
  conflict.

No new marker traits, no auto-derivation machinery: the existing
capability distinction (shared vs. exclusive, §2) already *is* the
Send/Share distinction, one level down. This is verified, not merely
argued, in [`regionlab/`](regionlab/)'s test suite (§9).

## 7. Open questions

Recorded rather than silently resolved, per this project's standing
practice (RFC 0001 §11 as the precedent):

1. **Field-level exclusivity splitting.** Rust allows mutably borrowing
   two disjoint fields of the same struct independently; NOVA's
   region-granularity model (§4.1) does not, in v1 of this design. A
   program that needs this must split the two fields into two regions.
   Whether that is an acceptable cost in practice, or needs a future
   refinement, is unanswered.
2. **Region resizing/growth.** This design assumes a region's contents
   are fixed once allocated (bump-allocate, never resize in place).
   Whether a growable region needs its own rule, or whether "close and
   reopen a larger region" suffices, is unanswered.
3. **Generic code parameterized over region-ness itself** (a function
   generic over "does my argument own its region or borrow it") is not
   designed. Every example and prototype test in this phase is
   monomorphic in this respect.
4. **Interaction with effect-row grading** ([RFC 0001 §11.7](RFC/0001-core-capability-effects.md#11-open-questions),
   still itself unresolved per
   [Experiment 003](docs/experiments/003-graded-rows.md)): does a
   region's allocation count belong in the same graded row as
   capability-use counts? Plausible, not designed.
5. **Whether region inference can ever be non-lexical** (ML-Kit-style,
   rather than tied strictly to a `region { }` block). This design
   commits only to the lexical case; a more flexible inference is a
   future RFC, not a promise made here.

## 8. Tradeoffs, named directly

- **Coarser than Rust at the granularity of a single struct's fields**
  (§4.1) — a real, accepted cost for a large mental-overhead reduction.
- **A region is an all-or-nothing deallocation unit.** A region holding
  one long-lived value and a thousand short-lived ones wastes memory
  until the whole region closes — the classic region-based-memory cost,
  named in [MEMORY-MODEL.md §3.7](MEMORY-MODEL.md#37-region-based-memory-cyclone-ml-kittofte-talpin-vale-verona)
  and not hidden here.
- **Linear values need explicit handling on every path, including
  error paths** — the one place this design pays linear-typing's
  ergonomic cost (MEMORY-MODEL.md §3.6), accepted because it applies
  only to `&mut Region`, not to ordinary data.

## 9. Validation

[`regionlab/`](regionlab/) is a small, standalone prototype checker
(not merged into `verifier/refspec/` — Phase 2's shipped v0.2 language
and its 45 conformance tests are unmodified by this phase) implementing
exactly §3–§6's rules on a minimal calculus, with negative tests for
every property in [MEMORY-MODEL.md §1](MEMORY-MODEL.md#1-what-must-be-prevented-made-precise).
See [SAFETY-GUARANTEES.md](SAFETY-GUARANTEES.md) for the claims this
validates and `regionlab/tests/` for the individual cases.
