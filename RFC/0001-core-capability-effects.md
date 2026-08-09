# RFC 0001 — Capability-Derived Effects (NOVA Core v0.1)

- **Status:** Review
- **Created:** 2026-08-28
- **Depends on:** RFC 0000
- **Implements:** Constitution Articles III, IV, V

## 1. Summary

NOVA's core type system unifies two mechanisms that are normally separate:
**effect rows** (Koka) and **object capabilities** (E, Pony, Austral).

The unification is a collapse: **an effect label *is* a capability type.**
A function's effect row is not written by the programmer as independent
bookkeeping; it is *derived* from the capability values the function body
can reach — its parameters and its closure captures.

The claim under test:

> If authority is already a value in the type system, the effect row is
> redundant information that the compiler can compute. Effect annotations
> become a *checked summary* of what you were given, not a second artifact
> to maintain.

## 2. Problem

Take a plausible piece of production code — a retry helper:

```
// Rust-ish. What does this do?
pub fn with_retry<T>(f: impl Fn() -> Result<T>) -> Result<T> { ... }
```

The signature says nothing about whether `f` touches the network, writes
files, reads the clock, or spawns a process. Three real consequences:

1. **You cannot tell if retrying is safe.** Retrying a network read is
   fine. Retrying something that charges a credit card is not. The type
   is identical.
2. **You cannot sandbox it.** `with_retry` is a library function; the
   closure smuggled the authority in. Nothing at the call site or in the
   module system can restrict it.
3. **A dependency update can change what it does** without changing any
   signature anywhere in your program.

Now the capability-only version (Austral, Pony, or disciplined Rust):

```
fn with_retry<T>(f: impl Fn() -> Result<T>) -> Result<T>
```

Still identical. The capability was *captured* by the closure. Capability
discipline controls who can *obtain* authority; it does not make authority
visible once it has been closed over. This is the gap that makes
capability-safe languages hard to audit: authority leaks through closures,
struct fields, and trait objects, and the types stay silent.

Now the effect-only version (Koka):

```
fun with_retry(f : () -> <net,exn> a) : <net,exn> a
```

Visible — but `net` is an ambient label. Any code anywhere may perform
`net` if a `net` operation is in scope; the effect row records that it
happened but does not control who may do it. And the row is authored by
hand, so it drifts.

Neither mechanism alone gives you both **"who is permitted"** and
**"what happened, including through closures."**

## 3. Prior art

| System | Authority | Effect visibility | Row maintained by |
|---|---|---|---|
| Koka | ambient | yes, rows | inference + annotation |
| Frank / Eff | ambient | yes | inference |
| Unison | ambient | yes, abilities | inference |
| Haskell `IO` | ambient | coarse (one bit) | inference |
| Rust | ambient | none | — |
| Pony | capabilities (reference caps, aliasing) | none for IO | — |
| E / Joe-E / Caja | capabilities | none | — |
| Austral | linear capabilities | via linear types, partial | manual |
| WASI | capabilities at module boundary | none inside module | — |
| Java `SecurityManager` | stack inspection | none | — (and withdrawn: JEP 411) |
| **Effekt** | **capabilities (second-class)** | **yes — the capability *is* the effect** | contextual, implicit |
| OCaml 5 | ambient (`Stdlib`) | **none — handlers are untyped** | — |
| OCaml + Eio | `Stdenv.t` passed to `main`, by convention | none | — |
| Zig | allocators passed explicitly | none | — |
| F\* | ambient | yes, user-definable effect lattice | annotated |

### 3.1 The closest prior art

- **Effekt** — Brachthäuser, Schuster & Ostermann, *Effects as
  Capabilities: Effect Handlers and Lightweight Effect Polymorphism*
  (OOPSLA 2020), and *Effects, Capabilities, and Boxes* (OOPSLA 2022).
  Effekt already identifies effects with capabilities. Its capabilities
  are **second-class**: they cannot be captured, stored, or returned,
  which yields contextual effect polymorphism with no row variables. The
  2022 paper adds *boxes*, which make a capability first-class at the
  cost of an explicit annotation — and the box's type records the
  captured capability set.
- **Austral** makes authority linear and explicit, and gets partway to
  effect visibility because a linear capability cannot be silently
  captured. NOVA does not require linearity for visibility.
- **Koka** supplies the row machinery. NOVA's row algebra is Koka's
  (Leijen 2005, *Extensible Records with Scoped Labels*).
- **Coeffects** — Petricek, Orchard & Mycroft (ICFP 2014) — give the
  right vocabulary for §4.3. Capabilities in scope are a *coeffect* (a
  requirement on the calling context); the derived row is the induced
  *effect*. NOVA's "derivation rule" is an effect computed from a
  coeffect, which is a studied relationship.

### 3.2 The novelty claim, struck

An earlier draft of this RFC claimed:

> *no existing system derives the effect row from the set of capability
> values reachable from a function body, such that closure capture of
> authority is forced into the closure's type.*

**This claim is withdrawn.** Effekt's boxes (2022) record a captured
capability set in the type of a first-class capability value, which is
substantially the same mechanism. Under §3's own stated rule and
Constitution Article V, the novelty claim is struck and this RFC is
downgraded to an **engineering RFC**: it adopts a known design and argues
for a particular set of trade-offs within it.

What remains unclaimed by any system found in the Phase 0 review is
narrower, and is offered as a *design* proposition rather than a research
contribution:

> Effect rows checked for **equality** rather than subsumption, over
> **uniformly first-class** capabilities, with a single syntactically
> greppable widening construct (§4.5).

Effekt reaches capture-visibility by *restricting* capabilities
(second-class by default, boxed by exception). NOVA reaches it by
*typing* them (first-class always, row always). Which is better is an
empirical question about programmer burden, not a theoretical one, and
§12's success criteria are the experiment.

Reviewers are invited to defeat the narrower claim as well.

## 4. Design

### 4.1 Capabilities

A capability declaration introduces **both** a type and an effect label of
the same name.

```nova
capability Net {
    connect(host: String, port: Int) -> Socket
    resolve(host: String) -> Ip
}

capability Clock {
    now() -> Instant
}
```

There is no way to construct a `Net` in NOVA source. Capability values
originate only from the runtime, at the entry point, and from
*attenuation* (§4.6). This is Constitution Article IV: no ambient
authority.

### 4.2 Effect rows

An effect row is a set of capability type names, with optional row
variable:

```
ε ::= {}                 empty (pure)
    | {C₁, …, Cₙ}        closed
    | {C₁, …, Cₙ | ρ}    open, ρ a row variable
```

Rows are unordered, duplicate-free sets. Row unification is Leijen's
scoped-label algorithm restricted to the duplicate-free case; because
labels here are nominal type names, the simplification is safe.

Function types carry a row:

```
(T₁, …, Tₙ) -> U ! ε
```

`! {}` is written by omission. `(Int) -> Int` is pure, and this is
enforced, not documented.

### 4.3 The derivation rule

This is the core of the RFC.

For a function body `e`, define `caps(e)` = the set of capability types of
every value reachable from `e`'s free variables — that is, its parameters
and its captured environment — that is *used* in `e`.

> **Rule (Capability Derivation).** A function's inferred effect row is
> exactly `caps(body) ∪ (rows of all functions it calls, minus rows
> discharged locally)`. A declared row is checked for equality with the
> inferred row, not subsumption.

Two consequences worth stating plainly:

- **Equality, not subsumption.** Declaring `! {Net, Clock}` on a function
  that only uses `Net` is an *error*, not an over-approximation. Widening
  is available explicitly (§4.5) so that it is visible where it happens.
  Rationale: Article III(2) — a signature that over-claims is as
  misleading as one that under-claims, and silent widening is how effect
  rows rot in practice.

- **Capture is not an escape hatch.** A closure that captures a `Net`
  gets `Net` in its type:

  ```nova
  fn make_fetcher(n: Net, url: String) -> (() -> Bytes ! {Net}) {
      || n.connect(url, 443).read_all()
  }
  ```

  The returned closure's type says `! {Net}`. The `with_retry` problem
  from §2 disappears: `with_retry` must be row-polymorphic, and its row
  variable is instantiated at the call site with the caller's row, which is
  visible.

### 4.4 Row polymorphism

```nova
fn with_retry[T, ρ](attempts: Int, f: () -> Result[T] ! ρ) -> Result[T] ! ρ
```

`with_retry` is pure in itself; it performs whatever `f` performs. The
caller's row is now legible at the call site:

```nova
let r = with_retry(3, || svc.fetch(n, url))   // : Result[Bytes] ! {Net}
```

A reviewer asking "is this retry safe?" reads `{Net}` and knows there is
no `Payments` in the row.

### 4.5 Explicit widening

```nova
fn handler(n: Net) -> Unit ! {Net, Clock} = widen { ... }
```

`widen` marks a deliberate over-approximation — used when a signature must
be stable across versions or must match an interface. It is a syntactic
marker so that `grep widen` finds every place the row is not tight.

### 4.6 Attenuation

A capability may be wrapped to produce a weaker one. Attenuation is the
only in-language source of capability values:

```nova
capability ReadOnlyFs {
    read(path: Path) -> Bytes
}

attenuate ReadOnlyFs from (fs: Fs) {
    read(path) = fs.read(path)
}
```

The attenuated value has effect label `ReadOnlyFs`, **not** `Fs`. This is
deliberate and is the point of attenuation: a function handed a
`ReadOnlyFs` has row `{ReadOnlyFs}`, and an auditor reading the row learns
the strongest thing that is true.

The soundness obligation this creates: the attenuating body may use `Fs`,
so `attenuate` is the one construct where a row is *dropped*. It is
therefore checked specially — the attenuation body is the trusted boundary,
and `nova check` reports every `attenuate` site in an audit listing.

This is the same shape as Joe-E's "taming" and E's facets, and carries the
same trust obligation.

### 4.7 The entry point

```nova
fn main(rt: Runtime) -> Exit ! {Runtime}
```

`Runtime` is the root capability. Every other capability descends from it
by attenuation. There is no `import std.net; net.connect(...)` — the
import gives you the *type*, never a value.

### 4.8 Typing rules (core fragment)

Judgement: `Γ ⊢ e : T ! ε`

```
                     x : T ∈ Γ
(Var)          ─────────────────────
                  Γ ⊢ x : T ! {}


              Γ ⊢ e : C ! ε      op ∈ ops(C)
              Γ ⊢ aᵢ : Tᵢ ! εᵢ
(CapUse)     ──────────────────────────────────────
              Γ ⊢ e.op(a⃗) : U ! ε ∪ ⋃εᵢ ∪ {C}


              Γ, x⃗:T⃗ ⊢ e : U ! ε
(Abs)        ────────────────────────────────
              Γ ⊢ λx⃗. e : (T⃗) -> U ! ε  ! {}


              Γ ⊢ f : (T⃗) -> U ! ε_f   Γ ⊢ aᵢ : Tᵢ ! εᵢ
(App)        ───────────────────────────────────────────
              Γ ⊢ f(a⃗) : U ! ε_f ∪ ⋃εᵢ
```

Note (Abs): forming a closure is pure; the captured row moves *into the
arrow*. That single placement is what makes capture visible, and it is
where NOVA differs from a capability-only language.

## 5. Examples

### 5.1 Accepted

```nova
capability Clock { now() -> Instant }

fn elapsed(c: Clock, f: () -> Unit ! ρ) -> Duration ! {Clock | ρ} {
    let t0 = c.now();
    f();
    c.now() - t0
}
```

### 5.2 Rejected — undeclared effect

```nova
fn log_time(c: Clock) -> Unit {
    print(c.now())
}
```

```
error[E0201]: function declares no effects but performs `Clock`
  --> timing.nova:2:11
   |
 1 | fn log_time(c: Clock) -> Unit {
   |             --------- capability `Clock` enters here
 2 |     print(c.now())
   |           ^^^^^^^ this use requires effect `Clock`
   |
   = note: inferred row is `{Clock}`, declared row is `{}`
help: declare the effect
   |
 1 | fn log_time(c: Clock) -> Unit ! {Clock} {
   |                               +++++++++
```

### 5.3 Rejected — over-declared effect

```nova
fn ping(n: Net) -> Bool ! {Net, Clock} {
    n.resolve("example.com"); true
}
```

```
error[E0202]: declared effect `Clock` is never performed
  --> net.nova:1:32
   |
 1 | fn ping(n: Net) -> Bool ! {Net, Clock} {
   |                                ^^^^^ not in inferred row `{Net}`
   |
   = note: NOVA checks effect rows for equality, not subsumption
help: remove it, or mark the widening as deliberate
   |
 1 | fn ping(n: Net) -> Bool ! {Net, Clock} = widen {
```

### 5.4 Rejected — laundering authority through a closure

```nova
fn sneaky(n: Net) -> (() -> Bytes) {
    || n.connect("x", 80).read_all()
}
```

```
error[E0203]: closure captures capability `Net` but its type is pure
  --> sneaky.nova:2:5
   |
 2 |     || n.connect("x", 80).read_all()
   |     ^^ ─ captures `n: Net`
   |
   = note: closure type is `() -> Bytes ! {Net}`
   = note: returning it as `() -> Bytes` would hide authority from callers
```

This is the diagnostic that justifies the whole RFC.

## 6. Alternatives

**A. Do nothing — capabilities only, no rows.** Simpler, and Austral shows
it is workable. Rejected because §2's closure-capture case stays invisible,
and NOVA's downstream goals (budgets, contracts, distribution) all need to
read a function's effects from its type.

**B. Effect rows only, ambient operations (Koka).** Rejected on
Constitution Article III(4): ambient authority is a security property NOVA
ranks above ergonomics. Also, hand-maintained rows drift.

**C. Keep them separate — capabilities *and* an independent effect row.**
The obvious design. Rejected as the worse version of this RFC: two
artifacts to keep in sync, and the interesting question (can one be derived
from the other?) goes unanswered. This is the fallback if §3's claim fails.

**D. Linear capabilities (Austral).** Would give capture-visibility for
free. Rejected *for now* under Article XI: NOVA has no memory discipline
yet, and adopting linearity here would pre-decide RFC-0004 by accident.
Revisit once the memory model exists.

**E. Effect handlers in v0.1 (Koka/Unison/OCaml 5).** Deferred. Handlers
are the natural way to discharge rows and NOVA will likely want them, but
they interact with the memory model and with non-local control flow.
v0.1 discharges effects only at the entry point.

## 7. Tradeoffs

- **Equality checking is strict and will annoy people.** Adding a log line
  to a pure function changes its signature and every declared row above it.
  This is the intended pressure, but it is real friction, and `widen` is
  the escape valve. If `widen` appears in >10% of signatures in practice,
  the rule is wrong.
- **Rows grow.** A deep call stack accumulates labels. Mitigation:
  capability *bundles* (a later RFC), not implicit truncation.
- **Nominal labels hurt reuse.** Two libraries defining their own `Clock`
  produce incompatible rows. This is a module-system problem and is not
  solved here.
- **Attenuation is trusted code.** §4.6 introduces the one row-dropping
  construct. It is a real hole and is mitigated by auditing, not by types.
- **Inference cost.** Row unification is near-linear in practice but the
  derivation rule requires whole-body capture analysis before a signature
  is known, which constrains separate compilation (see §9).

## 8. What this forecloses

- **Subsumption-based effect widening** becomes unavailable as a default;
  changing to it later would silently loosen every existing signature.
- **Ambient standard-library IO** is permanently off the table. `std` can
  never grow a free `print`. This is intended and is the largest single
  ergonomic cost NOVA is accepting.
- **Effect labels as structural, not nominal** — switching later would
  break every capability declaration.

## 9. Costs

- **Compile time.** One extra pass (capability reachability) plus row
  unification during inference. Rows are small sets of interned nominal
  ids; expected cost is low, but *unmeasured* — a benchmark is a
  prerequisite for Accepted status.
- **Run time.** Zero for the effect system: rows are erased. Capabilities
  are ordinary values; a capability call is an indirect call unless
  devirtualized. Attenuation allocates one wrapper unless inlined.
- **Binary size.** Capability vtables. Unmeasured.
- **Reader cost.** Non-trivial. Every signature grows. The bet is that the
  information is worth the width.

## 10. Staging

**v0.1 (this RFC, implementable now):** capability declarations, effect
rows, the derivation rule, equality checking, closures, row polymorphism,
`main(rt: Runtime)`. Interpreted reference semantics only.

**Deferred, each needing its own RFC:**
- attenuation (§4.6) — specified here for coherence, *not* implemented in
  v0.1
- effect handlers
- capability bundles / row abbreviations
- separate compilation of row-polymorphic functions
- generics beyond row variables

## 11. Open questions

1. **Does derivation survive abstraction?** When a capability is behind a
   generic parameter or an interface, the concrete label is unknown. Does
   the row become a variable, and does that variable stay legible? This is
   the question most likely to sink the design.
2. **Equality vs. subsumption at interface boundaries.** An interface
   method must fix a row. Implementors with *smaller* rows are then
   rejected under equality. Options: subsumption only at interface
   implementation sites, or implicit `widen`. Unresolved.
3. ~~**What is the row of a stored capability?**~~ **Resolved by
   [RFC 0002 §3](0002-structs-tuples-enums-pattern-matching.md#3-design-why-structs-cannot-launder-authority).**
   No new rule was needed: a struct's field types are always part of its
   declared, inspectable type — unlike a closure's free variables, there
   is no capture step that could hide them — so field access is ordinary
   structural lookup and the existing capability-use rule fires
   unmodified on whatever type it resolves to.
4. **Recursive functions** need row fixpoints. Standard, but the
   diagnostics for an inference failure will be poor.
5. Is `widen` a hole big enough to make the equality rule pointless?
6. ~~**Does the derivation rule survive the memory model?**~~ **Resolved
   by [MEMORY-MODEL.md §7](../MEMORY-MODEL.md#7-the-design-and-how-it-resolves-theme-b)
   and [OWNERSHIP-MODEL.md](../OWNERSHIP-MODEL.md).** Capabilities did
   not need to become second-class after all — Theme B's forced choice
   had a third option: keep every capability first-class (no revision to
   this RFC) and apply *linearity*, not second-classness, to exactly one
   axis — the capability granting exclusive, mutating access to a
   region. This RFC's derivation rule is therefore unmodified by
   Milestone 1; the memory model is layered on top of it, not through a
   redesign of it. This RFC is no longer provisional.
7. Should the row be **graded** rather than a plain set?
   [DESIGN-OPPORTUNITIES.md](../DESIGN-OPPORTUNITIES.md) Theme A argues
   that budgets, deadlines, retry policy, instrumentation and package
   manifests are all the same row with something attached to each label.
   v0.1 deliberately ships the ungraded case; the question is whether the
   ungraded design forecloses grading later. Preliminary answer: no, a set
   is the unit-graded case — but this needs checking before v0.1 freezes.

## 12. Success criteria

This RFC is Accepted only when:

- [ ] the reference interpreter and the checker agree on the full test
      suite (Constitution Article IX)
- [ ] every example in §5 produces the diagnostic shown
- [ ] a non-trivial program (>500 lines) is written in the core and the
      `widen` rate is measured
- [ ] open question 1 has an answer, or a documented plan

## 13. Revisions

**2026-08-28 — Phase 0 research review.**

- Prior-art table extended with Effekt, OCaml 5 / Eio, Zig and F\*.
- §3.1 added: Effekt is the nearest prior art, and the coeffect framing
  (Petricek, Orchard & Mycroft 2014) names what §4.3 is doing.
- §3.2 added: **the novelty claim is withdrawn** and this RFC is
  downgraded to an engineering RFC. A narrower design proposition
  replaces it.
- §11 gained open questions 6 (memory model may force second-class
  capabilities) and 7 (graded rows).

No normative change to the syntax, typing rules, or checked behaviour;
the conformance suite is unaffected.

**2026-08-28 — Phase 2 (RFC 0002).**

- §11 open question 3 (row of a stored capability) resolved: no new
  rule needed; see RFC 0002 §3.

**2026-08-28 — Phase 3, Milestone 1 (MEMORY-MODEL.md, OWNERSHIP-MODEL.md).**

- §11 open question 6 resolved: capabilities remain uniformly
  first-class. Linearity is applied to one axis of the capability system
  (exclusive region access) rather than to capabilities as a whole,
  which is the third option Theme B did not originally consider. No
  revision to §4's derivation rule was needed.
- This RFC's provisional status (imposed by open question 6) is lifted.

No normative change to this RFC's syntax, typing rules, or checked
behaviour in either revision; `verifier/refspec/`'s 45 conformance tests
remain unmodified and passing.
