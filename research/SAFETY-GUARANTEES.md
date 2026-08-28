# NOVA — Safety Guarantees

Milestone 1. A precise statement of what
[OWNERSHIP-MODEL.md](../docs/language/OWNERSHIP-MODEL.md)'s mechanism claims, at the
[Guarantee-ladder](../docs/foundation/LANGUAGE-CONSTITUTION.md#principle-7--verification-strength-must-be-explicit)
strength each claim actually occupies — level 3 ("checked by
`regionlab`'s prototype checker") for the mechanism itself, not level 4
("independently proven") for anything, and not silently promoted to a
claim about the eventual production compiler, which does not exist yet.

Every row below names the exact test in
[`regionlab/tests/`](../regionlab/tests) that exercises it. This document
is deliberately built to be checked against those tests, not read as
prose on its own — the honest-claims discipline this project has held
to since Phase 0 (Constitution Article V) applies to safety claims
exactly as it applies to novelty claims.

---

## 1. The five required properties, claim by claim

### 1.1 Use-after-free

> **Claim.** A well-typed NOVA program cannot read or write a value
> after the region owning it has closed.

**Mechanism.** Every region-allocated value's type carries its region's
identity (`InRegion[T]`, [OWNERSHIP-MODEL.md §3](../docs/language/OWNERSHIP-MODEL.md#3-regions-are-capabilities--syntax-and-typing)).
Every use checks the region is still open
(`Checker._check_live`, [`regionlab/checker.py`](../regionlab/checker.py)).

**Tested by:** [`regionlab/tests/003-use-after-free-rejected.rlab`](../regionlab/tests/003-use-after-free-rejected.rlab)
(`R1002`) — reading data from an explicitly closed region.

**Strength: level 3 (checked by the prototype).** Not level 4: no
independent proof exists that `regionlab`'s rule set is complete against
every program shape, only that the stated test cases are rejected. A
production implementation inherits this obligation, not this proof.

### 1.2 Double-free

> **Claim.** A region cannot be deallocated twice.

**Mechanism.** In NOVA's actual design ([OWNERSHIP-MODEL.md §5](../docs/language/OWNERSHIP-MODEL.md#5-what-the-checker-verifies)
item 3), there is **no syntax to deallocate a region explicitly at
all** — closing is a consequence of a lexical scope ending, which
happens exactly once by construction, the same way a Python `with`
block or a Rust drop cannot run twice for one binding. This makes
double-free unrepresentable, not merely rejected.

`regionlab` additionally provides an explicit `close(r)` statement, kept
specifically so double-free has a *directly testable* shape — closing an
already-closed region is checked and rejected (`R1003`) — rather than
relying solely on "there is no syntax for it," which would be true but
untestable.

**Tested by:** [`regionlab/tests/005-double-close-rejected.rlab`](../regionlab/tests/005-double-close-rejected.rlab).

**Strength: level 3 for the explicit-`close` case (checked); the
scope-based case in NOVA's real design is stronger — level "vacuous by
construction," the same status Constitutional Principle 1 currently
holds for v0.2's total absence of pointers.**

### 1.3 Invalid memory access

> **Claim.** A reference cannot be used to access memory outside the
> region it was typed against.

**Mechanism.** In this design, "invalid access" and "use-after-free"
collapse into **the same checked rule**: a region-tagged type can only
be read or written while its own region is open, and there is no
mechanism (no raw pointer, no pointer arithmetic, no reinterpret-cast) by
which a value could acquire a *different* region's tag than the one it
was allocated with. This is a genuine simplification regions provide
over a raw-pointer model, worth stating plainly rather than treating as
a separate guarantee needing a separate mechanism.

**Tested by:** the same test as §1.1 — there is no separate test because
there is no separate mechanism.

### 1.4 Dangling references

> **Claim.** A reference into a region's data cannot escape past the
> region's own closing.

**Mechanism.** A region block's own tail expression is checked: if its
type is tagged with the region about to close, this is rejected before
the region is allowed to close (`RegionBlock` handling,
[`regionlab/checker.py`](../regionlab/checker.py)).

**Tested by:** [`regionlab/tests/004-dangling-reference-rejected.rlab`](../regionlab/tests/004-dangling-reference-rejected.rlab)
(`R1001`).

**Strength: level 3, and narrower than the full claim might suggest** —
see §3.1 below for exactly what is *not* covered by this prototype's
escape check (function-return escapes, not just block-tail escapes).

### 1.5 Data races where the model promises race freedom

> **Claim.** Two holders of write access — or a writer and a reader —
> to the same region can never coexist.

**Mechanism.** [OWNERSHIP-MODEL.md §2](../docs/language/OWNERSHIP-MODEL.md#2-the-core-claim-stated-as-a-typing-discipline)'s
central rule, enforced as a region-level reader/writer exclusion: minting
an exclusive capability requires zero live shared capabilities and no
already-live exclusive one (`Exclusive` handling,
[`regionlab/checker.py`](../regionlab/checker.py)).

**Tested by:**
[`regionlab/tests/006-simultaneous-exclusive-rejected.rlab`](../regionlab/tests/006-simultaneous-exclusive-rejected.rlab)
(`R1005`, two writers) and
[`regionlab/tests/007-exclusive-while-shared-live-rejected.rlab`](../regionlab/tests/007-exclusive-while-shared-live-rejected.rlab)
(`R1005`, a writer and a reader).

**Strength: level 3, and explicitly conditional.** This is a claim about
what the *type system* prevents, checked on a program with no actual
concurrent execution (Milestone 4 does not exist yet). The claim is:
*if* concurrent tasks are later added on top of this mechanism (per
[OWNERSHIP-MODEL.md §6](../docs/language/OWNERSHIP-MODEL.md#6-interaction-with-phase-2s-type-system)'s
Send/Share derivation), *then* this rule is what prevents them from
racing on a region. It is not, and cannot yet be, a claim about NOVA
concurrency, because NOVA concurrency does not exist.

---

## 2. Send/Share, verified rather than merely argued

[OWNERSHIP-MODEL.md §6](../docs/language/OWNERSHIP-MODEL.md#6-interaction-with-phase-2s-type-system)
claims Send/Share fall out of the shared/exclusive distinction with no
separate trait mechanism. Tested directly, not just asserted:

- **The exclusive capability cannot be duplicated** (the `Send`-safety
  argument depends on this: moving it must genuinely transfer sole
  access, not create a second holder) —
  [`regionlab/tests/010-copy-exclusive-rejected.rlab`](../regionlab/tests/010-copy-exclusive-rejected.rlab)
  (`R1007`).
- **The shared capability can be duplicated freely** (the `Share`-safety
  argument depends on this being unrestricted, exactly like any other
  RFC 0001 capability) —
  [`regionlab/tests/011-copy-shared-accepted.rlab`](../regionlab/tests/011-copy-shared-accepted.rlab).

## 3. What is explicitly not guaranteed

Constitution Article XII (versioning honesty) and
[SECURITY.md](../SECURITY.md)'s existing practice both require this section
to exist and to be specific, not a general disclaimer.

### 3.1 The prototype's escape check is narrower than the full claim

`regionlab`'s dangling-reference check (§1.4) covers a value escaping as
a **region block's own tail expression**. It does **not** cover a value
escaping through a **function return** — `regionlab`'s functions are
restricted to `Int` parameters and return types entirely
([OWNERSHIP-MODEL.md §7](../docs/language/OWNERSHIP-MODEL.md#7-open-questions) item 3),
specifically so this gap does not have to be closed to validate the
core mechanism. A production implementation must extend the escape
check to function boundaries before this guarantee can be claimed at
level 3 for the whole language, not just for block-scoped code.

### 3.2 Field-level exclusivity is coarser than Rust's

[OWNERSHIP-MODEL.md §4.1](../docs/language/OWNERSHIP-MODEL.md#41-why-this-and-not-rusts-borrow-checker)
and §8 already state this directly: two disjoint fields of one region
cannot be exclusively borrowed independently. A program that needs this
must use two regions. Not tested as a negative case (there is nothing to
reject — it is a missing capability, not an unsound acceptance), but
recorded here so it is not mistaken for an oversight later.

### 3.3 No claim about the FFI/`Unsafe` boundary

[MEMORY-MODEL.md §7](../docs/language/MEMORY-MODEL.md#7-the-design-and-how-it-resolves-theme-b)
and [SECURITY.md](../SECURITY.md) already establish that any escape hatch
(FFI, a future `Unsafe` capability) is outside what the type system can
check by definition — a foreign region's internal aliasing is never
verified by NOVA, only the checked hand-off at the boundary is
(Vale's "Fearless FFI" framing, MEMORY-MODEL.md §3.7). This document
makes no claim beyond that already-stated one.

### 3.4 No claim about the eventual production compiler

`regionlab` is a small, standalone prototype (Constitution Article IX's
"two implementations" requirement does not yet apply to it — it is the
*first* implementation of this specific mechanism, not a second
independent one). Every claim in this document is a claim about
`regionlab`'s checked behavior on its own test suite, not a claim about
`verifier/refspec/` (unmodified by this phase) or a future Rust compiler
implementing the same design. Closing that gap is Milestone 3's
obligation, not this document's.

### 3.5 No claim about regions and generics, resizing, or non-lexical inference

[OWNERSHIP-MODEL.md §7](../docs/language/OWNERSHIP-MODEL.md#7-open-questions) lists these
as open questions, not as solved-but-untested. This document makes no
safety claim about any of them.

---

## 4. How to falsify a claim in this document

Every claim above names an exact test file. To check whether the claim
still holds after a future change to `regionlab/checker.py`:

```sh
python3 regionlab/tests/run.py
```

A claim is falsified the moment its named test's `# expect:` directive
stops matching the checker's actual output. This is the same discipline
[VISION.md](../VISION.md#what-would-falsify-it) already applies to the
project's thesis — a safety claim with no test that could falsify it is
not a claim this project makes.
